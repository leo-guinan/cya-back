import uuid
from datetime import datetime

from decouple import config
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pymongo import MongoClient

from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind

LEARNING_FROM_PDF_PROMPT = """
You are a new startup founder.

You want to learn about how to raise money for your startup.

Here's what you know so far: {submind}

You are reading a book called Raising Millions, written by Hustle Fund, and here's the next page: {page}

What did you learn from that page?

"""

COMBINE_KNOWLEDGE_PROMPT = """
You are a new startup founder.

You are learning how to raise money for your startup.

You are taking notes on what you learn. Here are your notes so far: {notes}

Here's what you learned: {learning}

Rewrite your notes to incorporate what you've learned and correct anything you've learned incorrectly.

"""


def learn_from_page(content: str, goal: str, submind: Submind):
    submind_document = remember(submind)
    # model = SubmindModelFactory.get_model(submind.uuid, "learning_from_webscraping")
    model_claude = ChatAnthropic(model_name="claude-3-haiku-20240307",
                                 anthropic_api_key=config("ANTHROPIC_API_KEY"),
                                 anthropic_api_url="https://anthropic.hconeai.com/",
                                 model_kwargs={
                                     "extra_headers": {
                                         "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                                         "Helicone-Property-Step": "Learning from PDF",
                                         "Helicone-Property-UUID": submind.uuid

                                     }
                                 }
                                 )
    prompt = ChatPromptTemplate.from_template(LEARNING_FROM_PDF_PROMPT)
    chain = prompt | model_claude | StrOutputParser()

    response = chain.invoke(
        {"submind": submind_document,
         "page": content,
         })
    print(response)

    combination_prompt = ChatPromptTemplate.from_template(COMBINE_KNOWLEDGE_PROMPT)
    combination_chain = combination_prompt | model_claude | StrOutputParser()
    combined_response = combination_chain.invoke(
        {"notes": submind_document,
         "learning": response,
         })
    print(f"After updating: {combined_response}")
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    historical_uuid = str(uuid.uuid4())

    previous_doc = db.documents.find_one({"uuid": submind.mindUUID})
    db.document_history.insert_one({
        "uuid": historical_uuid,
        "content": previous_doc["content"],
        "createdAt": previous_doc["createdAt"],
        "documentUUID": previous_doc["uuid"]
    })
    db.documents.update_one({"uuid": submind.mindUUID}, {
        "$set": {"content": combined_response, "previousVersion": historical_uuid, "updatedAt": datetime.now()}},
                            upsert=True)


def read_pdf(pdf_path, submind, goal, namespace, starting_page=0):
    loader = PyMuPDFLoader(pdf_path)
    data = loader.load()
    for index, page in enumerate(data):
        print(f"Reading page {index}")
        if index < starting_page:
            continue
        learn_from_page(page.page_content, goal, submind)


def learn_about_topic_from_pdf(topic):
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    submind_uuid = str(uuid.uuid4())
    submind_mind_uuid = str(uuid.uuid4())
    submind = Submind.objects.create(uuid=submind_uuid, name=f"Submind for {topic}",
                                     mindUUID=submind_mind_uuid,
                                     description="This is a submind that has learned about a topic.")
    print(f"Submind {submind.id} is learning about {topic}")
    db.documents.insert_one({
        "content": f"You are learning about {topic}",
        "uuid": submind.mindUUID,
        "createdAt": datetime.now()
    })
    read_pdf("./RaiseMillions.pdf", submind, topic, submind_uuid)
