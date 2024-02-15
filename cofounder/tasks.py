import datetime
import json
import logging
import uuid

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.vectorstores import Pinecone as PineconeLC
from llama_index import StorageContext, VectorStoreIndex
from llama_index.vector_stores import MetadataFilters, MetadataFilter, FilterOperator, PineconeVectorStore
from pinecone import Pinecone

from backend.celery import app
from cofounder.cofounder.default import DefaultCofounder
from cofounder.command.classify import classify_command
from cofounder.command.identify_tasks import identify_tasks
from cofounder.command.transform import schema_to_body
from cofounder.models import User, ChatSession, Cofounder, BusinessProfile, FounderProfile, Command, Task, Answer
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

    answer = classify_command(message)
    if answer == "statement":
        save_info.delay(message, session_id, user_id)
    elif answer == "question":
        answer_question.delay(message, session_id, user_id)
    # elif answer == "command": # let's not support commands yet
    #     perform_command.delay(message, session.id)
    else:
        print(f'Answer: {answer}')

    # learn.delay(user_id, message, session_id)


@app.task(name="coach.tasks.crawl_and_scrape")
def crawl_and_scrape(url):
    pc = Pinecone(
        config("PINECONE_API_KEY"),  # find at app.pinecone.io
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = PineconeLC(index, embeddings.embed_query, "text")

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
    pc = Pinecone(
        config("PINECONE_API_KEY"),  # find at app.pinecone.io
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = PineconeLC(index, embeddings.embed_query, "text", namespace="user_info")
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
    pc = Pinecone(
        config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    # db = Chroma("test", embeddings)
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = PineconeLC(index, embeddings.embed_query, "text")

    scraper = Scraper(vectorstore)
    scraper.scrape(url)

    pass

def serialize_task(task_model):
    return {
        "id": task_model.id,
        "name": task_model.task,
        "details": task_model.details,
        "taskFor": task_model.taskFor
    }
@app.task(name="cofounder.tasks.save_info")
def save_info(message, session_id, user_id):
    pc = Pinecone(config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cofounder")

    texts = []
    ids = []
    metadatas = []

    texts.append(message)
    ids.append(str(uuid.uuid4()))
    metadatas.append({"source": "cli", "date": datetime.datetime.now().isoformat(), "userId": user_id})
    cli_index.add_texts(texts, metadatas, ids)
    channel_layer = get_channel_layer()
    print(session_id)

    tasks = identify_tasks(message)
    task_models = []
    for task in tasks:
        print(task)
        task_model = Task()
        task_model.session = ChatSession.objects.get(session_id=session_id)
        task_model.task = task['name']
        task_model.taskFor = task['taskFor']
        task_model.details = task['details']
        task_model.uuid = str(uuid.uuid4())
        task_model.save()
        task_models.append(task_model)


    async_to_sync(channel_layer.group_send)(session_id,
                                            {"type": "chat.message", "message": json.dumps(list(map(lambda t: serialize_task(t), task_models))), "id": "task"})


@app.task(name="cofounder.tasks.answer_question")
def answer_question(question, session_id, user_id):
    pc = Pinecone(config("PINECONE_API_KEY"))
    print(f'Looking up: {question} for user: {user_id}')
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))

    vector_store = PineconeVectorStore(
        pinecone_index=index, namespace="cofounder"
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, storage_context=storage_context)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="userId", operator=FilterOperator.EQ, value=user_id
            ),
        ]
    )
    retriever = index.as_retriever(filters=filters, verbose=True)
    answer = retriever.retrieve(question)

    clean_answer = answer[0].text if answer and answer[0] else None

    if not clean_answer:
        clean_answer = "I don't know, sorry"

    answer_model = Answer()
    answer_model.session = ChatSession.objects.get(session_id=session_id)
    answer_model.answer = clean_answer
    answer_model.uuid = str(uuid.uuid4())
    answer_model.question = question
    answer_model.save()

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(session_id,
                                            {"type": "chat.message", "message": clean_answer, "id": "answer"})


@app.task(name="cofounder.tasks.perform_command")
def perform_command(command, session_id):
    # pick best fitting command, if over a certain threshold.
    # turn command into an embedding
    # compare embedding to all commands
    # if over threshold, run command

    pc = Pinecone(
        config("PINECONE_API_KEY"),  # find at app.pinecone.io
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli_commands")
    # cli_index.delete(delete_all=True)
    # add_command("add_command", "Add a command to the knowledge base", "http://localhost:8000/api/cli/add_command",
    #             "(command, description, url, input, output)", "Command added")
    retriever = cli_index.as_retriever()
    query = command
    results = retriever.get_relevant_documents(query)
    print(results[0])
    print(results[0].metadata)
    retrieved = Command.objects.get(uuid=results[0].metadata['uuid'])
    req_url = retrieved.url if retrieved.url.endswith("/") else retrieved.url + "/"
    print(req_url)
    body = schema_to_body(command, retrieved.input_schema)
    parsed_body = json.loads(body.content)
    print(parsed_body)
    answer = requests.post(req_url, json=parsed_body)
    print(answer)


@app.task(name="cofounder.tasks.add_command")
def add_command(command, description, url, input_schema, output):
    print(f"adding command {command}")
    pc = Pinecone(
        config("PINECONE_API_KEY")
    )
    command_object = Command(command=command, description=description, url=url, input_schema=input_schema,
                             output_schema=output, uuid=str(uuid.uuid4()))
    command_object.save()
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli_commands")
    texts = []
    ids = []
    metadatas = []

    texts.append(f"""
    Command:
    {command}

    Description:
    {description}

    URL:
    {url}

    Input Schema:
    {input_schema}

    Output Schema:
    {output}
    """)
    ids.append(command_object.uuid)
    metadatas.append({"source": "cli", "date": datetime.datetime.now().isoformat(), "uuid": command_object.uuid})
    cli_index.add_texts(texts, metadatas, ids)
