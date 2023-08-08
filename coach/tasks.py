import json
import logging

import pinecone
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
from langchain.vectorstores import Pinecone

from backend.celery import app
from coach.models import User, ChatSession, ChatError, ChatCredit
from coach.tools.background import BackgroundTool
from coach.tools.coaching import CoachingTool
from coach.tools.lookup import LookupTool
from coach.tools.needed import WhatsNeededTool
from content.crawler import Crawler
from content.scraper import Scraper

logger = logging.getLogger(__name__)


@app.task(name="coach.tasks.respond_to_chat_message")
def respond_to_chat_message(message, user_id, session_id):
    channel_layer = get_channel_layer()
    user = User.objects.get(id=user_id)
    session = ChatSession.objects.filter(session_id=session_id).first()
    if session is None:
        session = ChatSession(user=user, session_id=session_id)
        session.save()
    try:
        extract_user_info.delay(user_id, message, session_id)

        # has user answered initial questions? If not, find first un-answered question and return that as response.
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )

        memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history)

        # System prompt for chatbot
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")

        coach_tool = CoachingTool(memory=memory)
        whats_needed_tool = WhatsNeededTool()
        background_tool = BackgroundTool()

        docs = background_tool.get_relevant_docs(message)

        # determine what's needed to answer the query
        raw_ans = whats_needed_tool.process_question(message)
        print(raw_ans)

        questions = json.loads(raw_ans)['questions']
        answers = []
        for question in questions:
            answers.append({

                "question": question['question'],
                "answer": background_tool.answer_question(docs, question)

            })

        print(answers)

        # if not, ask clarifying questions

        # see if any sources can provide extra support to answer the question

        # create a response

        # tools = [coach_tool.get_tool(), whats_needed_tool.get_tool()]
        # agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        #
        # response = agent.run(message)
        #
        # # You are Alix, the Build In Public Coach.
        # #
        # #
        # #
        # #
        # #  {human_input}.
        # #
        # # Here is the feedback from your team: {response}
        # #
        # # Your job is to take their response and convert it to a useful response for your client in your voice.
        # #
        # # You are in a real time chat, so keep your responses short and feel free to ask small, clarifying questions.  You don't want to overwhelm the client with
        # #
        # #
        # #
        # #
        # # your response
        #
        response = "\n".join([f"Question: {answer['question']}: {answer['answer']}" for answer in answers])
        lookup_tool = LookupTool()
        document = lookup_tool.lookup(message)
        print(document)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
            You are Alix, the Build In Public Coach. You are friendly, informal, and tech-savvy.

            You believe that building in public is a great way to empower people to build their own businesses.

            You are supportive, encouraging, and helpful.

            Your team has researched the following question from your client: {message}
            They've looked up the information they have on your client and came up with the following questions and answers
            from their database.
            {response}
            
            You looked up the question in your research library and found the following answer:
            {document['result']}
            

            Your job is to take their response and convert it to a useful response for your client in your voice.
            If you need more information, feel free to ask small, clarifying questions.  You don't want to overwhelm the client with
            too large a response.
            """),
            # The persistent system prompt
            MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
            HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
        ])

        alix_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,
                                               chat_memory=message_history)

        chat_llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=alix_memory,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        alix_response = chat_llm_chain.predict(
            human_input=message,
        )

        # record chat credit used
        chat_credit = ChatCredit(user=user, session=session)
        chat_credit.save()
        # print(alix_response)

        source_markdown = "\n".join(
            [f"""[{source.metadata['title']}]({source.metadata['url']})""" for source in document['source_documents']])

        composite_response = f"""
        {alix_response}
        
        Sources:
        {source_markdown}
        """

        print(composite_response)
        # need to send message to websocket
        async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": composite_response})
    except Exception as e:
        error = str(e)
        print(f'Error: ${e}')
        chat_error = ChatError(error=error, session=session)
        chat_error.save()
        async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message",
                                                             "message": "Sorry, there was an error processing your request. Please try again."})


@app.task(name="coach.tasks.crawl_and_scrape")
def crawl_and_scrape(url):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    # db = Chroma("test", embeddings)
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = Pinecone(index, embeddings.embed_query, "text")

    scraper = Scraper(vectorstore)
    crawler = Crawler(scraper)
    crawler.crawl(url)


@app.task(name="coach.extract_user_info")
def extract_user_info(user_id, message, session_id):
    llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")

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
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    # db = Chroma("test", embeddings)
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    vectorstore = Pinecone(index, embeddings.embed_query, "text")
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
