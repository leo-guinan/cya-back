import datetime
import json
import logging
import uuid

import pinecone
import requests
from channels.layers import get_channel_layer
from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.vectorstores import Pinecone

from backend.celery import app
from cofounder.agent.remember_agent import RememberAgent
from cofounder.chat.default import run_default_chat
from cofounder.cofounder.default import DefaultCofounder
from cofounder.models import User, ChatSession, Cofounder, BusinessProfile, FounderProfile
from cofounder.tools.chat_namer import ChatNamerTool
from cofounder.tools.fix_json import FixJSONTool
from content.crawler import Crawler
from content.scraper import Scraper

logger = logging.getLogger(__name__)


@app.task(name="cofounder.tasks.respond_to_chat_message")
def respond_to_cofounder_message(message, user_id, session_id):
    channel_layer = get_channel_layer()
    user = User.objects.get(id=user_id)
    session = ChatSession.objects.filter(session_id=session_id).first()

    fix_json_tool = FixJSONTool()
    if session is None:
        logger.info("No session found, creating new session")
        name_tool = ChatNamerTool()
        name_json = name_tool.name_chat(message)
        try:
            name = json.loads(name_json)['name']
        except Exception as e:
            # if json fails, try to fix it with gpt 4
            name_json = fix_json_tool.fix_json(name_json)
            name = json.loads(name_json)['name']
        print(f"Saving session: {session_id}")

        session = ChatSession(user=user, session_id=session_id, name=name, chat_type=ChatSession.DEFAULT)
        session.save()

    run_default_chat(session, message, user, channel_layer)
    # learn.delay(user_id, message, session_id)


@app.task(name="coach.tasks.crawl_and_scrape")
def crawl_and_scrape(url):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = Pinecone(index, embeddings.embed_query, "text")

    scraper = Scraper(vectorstore)
    crawler = Crawler(scraper)
    crawler.crawl(url)


@app.task(name="coach.extract_user_info")
def extract_user_info(user_id, message, session_id):
    llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                     openai_api_base=config('OPENAI_API_BASE'), headers={
            "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
        })

    extract_user_info_prompt_template = """
                You are an information extraction agent. Your job is to understand everything you can about a person and the business they are trying to build.
                Given a message, identify key information about the person or their business that will help their coach provide them the best coaching.
                Here's their message:
                {message}
                """

    extract_user_info_prompt = PromptTemplate(
        template=extract_user_info_prompt_template,
        input_variables=["message"]
    )

    user_info = LLMChain(
        llm=llm,
        verbose=True,
        prompt=extract_user_info_prompt,
    )

    response = user_info.predict(message=message)
    print(response)
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = Pinecone(index, embeddings.embed_query, "text", namespace="user_info")
    vectorstore.add_texts([response], metadatas=[{"user_id": user_id, "session_id": session_id}], namespace="user_info")


@app.task(name="coach.tasks.add_user_email")
def add_user_email(email, preferred_name):
    try:
        # send request with bearer token authentication
        headers = {
            "Authorization": f"Bearer {config('LOOPS_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "firstName": preferred_name,
            "userGroup": "Users",
            "source": "User Signup"
        }
        requests.post("https://app.loops.so/api/v1/contacts/create", headers=headers, data=json.dumps(data))

    except Exception as e:
        logger.error(e)


@app.task(name="coach.tasks.send_weekly_prompt")
def send_weekly_prompt(user_id):
    # get user
    user = User.objects.get(id=user_id)

    # create new chat session
    chat_session = ChatSession()
    chat_session.user = user
    chat_session.session_id = str(uuid.uuid4())
    chat_session.name = f"Weekly Prompt {datetime.today().strftime('%m/%d/%y')}"
    chat_session.save()

    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=chat_session.session_id
    )
    # seed with message
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,
                                      chat_memory=message_history)
    memory.chat_memory.add_ai_message("What are you planning on doing this week?")

    prompt_url = f"{config('COACHING_APP_BASE_URL')}{chat_session.session_id}/"

    # send email with link to chat session
    try:
        # send request with bearer token authentication
        headers = {
            "Authorization": f"Bearer {config('LOOPS_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "transactionalId": "cllmxwam300epl10p1rwnoyjv",
            "email": user.email,
            "dataVariables": {
                "prompt_url": prompt_url
            }
        }
        requests.post("https://app.loops.so/api/v1/transactional", headers=headers, data=json.dumps(data))

    except Exception as e:
        logger.error(e)


@app.task(name="coach.tasks.send_daily_checkin")
def send_daily_checkin(user_id):
    # get user
    user = User.objects.get(id=user_id)
    try:
        # send request with bearer token authentication
        headers = {
            "Authorization": f"Bearer {config('LOOPS_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "transactionalId": "clm25g6wg000vmk0os6wdrsaj",
            "email": user.email,
        }
        requests.post("https://app.loops.so/api/v1/transactional", headers=headers, data=json.dumps(data))

    except Exception as e:
        logger.error(e)


@app.task(name="cofounder.tasks.create_cofounder")
def create_cofounder(user_id):
    user = User.objects.get(id=user_id)
    business = BusinessProfile.objects.filter(user__id=user_id).first()
    founder = FounderProfile.objects.filter(user__id=user_id).first()

    url = "https://api.copy.ai/api/workflow/PKGW-1e1115f4-c997-47c9-8426-ace6b6abfe30/run"

    payload = {
        "startVariables": {
            "business_idea": business.profile,
            "founder_profile": founder.profile,
        },
        "metadata": {"api": True}
    }
    headers = {
        "Content-Type": "application/json",
        "x-copy-ai-api-key": config("COPYAI_API_KEY")
    }

    response = requests.post(url, json=payload, headers=headers)

    parsed = json.loads(response.text)
    details = json.loads(parsed['output']["Generate_Co-founder_Details"])
    cofounder = Cofounder()
    cofounder.user = user
    cofounder.profile = details["backstory"]
    cofounder.name = details['name']
    cofounder.save()


@app.task(name="cofounder.tasks.learn")
def learn(user_id, message, session_id):
    cofounder = DefaultCofounder(session_id, user_id)
    cofounder.learn_about_the_business(message)

@app.task(name="cofounder.tasks.learn_blog")
def learn_blog(user_id, url, title, description):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = Pinecone(index, embeddings.embed_query, "text")

    scraper = Scraper(vectorstore)
    scraper.scrape(url)

    pass

