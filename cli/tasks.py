from datetime import datetime
from operator import itemgetter

import pinecone
from decouple import config
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.pinecone import Pinecone
from uuid import uuid4

from langchain_core.messages import get_buffer_string
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import format_document

from backend.celery import app
from cli.command.classify import classify_command



@app.task(name="cli.tasks.run_command")
def run_command(command):
    answer = classify_command(command)
    if answer == "statement":
        save_info.delay(command)
    elif answer == "question":
        answer_question.delay(command)
    else:
        print(f'Answer: {answer}')


@app.task(name="cli.tasks.save_info")
def save_info(message):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = Pinecone(index, embeddings, "text", namespace="cli")

    texts = []
    ids = []
    metadatas = []

    texts.append(message)
    ids.append(str(uuid4()))
    metadatas.append({"source": "cli", "date": datetime.now().isoformat()})
    cli_index.add_texts(texts, metadatas, ids)


@app.task(name="cli.tasks.answer_question")
def answer_question(question):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = Pinecone(index, embeddings, "text", namespace="cli")

    retriever = cli_index.as_retriever()

    _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(
            docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
    ):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)

    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4")
    _inputs = RunnableParallel(
        standalone_question=RunnablePassthrough.assign(
            chat_history=lambda x: get_buffer_string(x["chat_history"])
        )
                            | CONDENSE_QUESTION_PROMPT
                            | ChatOpenAI(temperature=0, api_key=config("OPENAI_API_KEY"), model_name="gpt-4")
                            | StrOutputParser(),
    )
    _context = {
        "context": itemgetter("standalone_question") | retriever | _combine_documents,
        "question": lambda x: x["standalone_question"],
    }
    conversational_qa_chain = _inputs | _context | ANSWER_PROMPT | ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4")
    answer = conversational_qa_chain.invoke(
        {
            "question": question,
            "chat_history": [],
        }
    )

    print(answer)





