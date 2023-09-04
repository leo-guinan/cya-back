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
from coach.chat.bad import run_daily_bad_chat
from coach.chat.default import run_default_chat
from coach.chat.great import run_daily_great_chat
from coach.chat.ok import run_daily_ok_chat
from coach.models import User, ChatSession, CHAT_TYPE_MAPPING
from coach.tools.chat_namer import ChatNamerTool
from coach.tools.fix_json import FixJSONTool
from content.crawler import Crawler
from content.scraper import Scraper

logger = logging.getLogger(__name__)


@app.task(name="coach.tasks.respond_to_chat_message")
def respond_to_chat_message(message, user_id, session_id):

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
    else:
        logger.info("Session found")
        logger.info(f'Chat type: {session.chat_type}')

    chat_type = session.chat_type
    logger.info(f"Chat type: {chat_type}")
    extract_user_info.delay(user_id, message, session_id)
    if chat_type == ChatSession.DAILY_GREAT:
        run_daily_great_chat(session, message, user, channel_layer)
    elif chat_type == ChatSession.DAILY_OK:
        run_daily_ok_chat(session, message, user, channel_layer)
    elif chat_type == ChatSession.DAILY_BAD:
        run_daily_bad_chat(session, message, user, channel_layer)
    else:
        run_default_chat(session, message, user, channel_layer)


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
    chat_session.name = "Weekly Prompt " + str(datetime.date)
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


@app.task(name="coach.tasks.send_weekly_prompts")
def send_weekly_prompts():
    users = User.objects.all()
    for user in users:
        send_weekly_prompt.delay(user.id)
