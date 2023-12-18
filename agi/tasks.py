# respond_to_agi_message.delay(message, text_data_json['user_id'], self.session)
import uuid

import pinecone
import requests
from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

from agi.agent import Agent
from agi.models import Tool, Person
from backend.celery import app


@app.task(name="agi.tasks.respond_to_agi_message")
def respond_to_agi_message(message, user_id, session):
    session_id = str(uuid.uuid4())
    agent = Agent(session_id)
    result = agent.determine_action(message)
    print(result)


@app.task(name="agi.tasks.update_tool_embeddings")
def update_tool_embeddings():
    tools = Tool.objects.all()
    people = Person.objects.all()
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))


    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
    tool_index = Pinecone(index, embeddings, "text", namespace="agi_tools")
    people_index = Pinecone(index, embeddings, "text", namespace="agi_people")
    tool_index.delete(delete_all=True)
    people_index.delete(delete_all=True)
    tool_texts= []
    tool_ids = []
    tool_metadatas = []
    for tool in tools:
        temp_uuid = str(uuid.uuid4())
        tool_texts.append(f'{tool.name} {tool.description}')
        tool_ids.append(temp_uuid)
        tool_metadatas.append({"tool_id": tool.id})
        tool.pinecone_id = temp_uuid
        tool.save()

    tool_index.add_texts(tool_texts, tool_metadatas, tool_ids)
    people_texts = []
    people_ids = []
    people_metadatas = []
    for person in people:
        temp_uuid = str(uuid.uuid4())
        people_texts.append(f'{person.name} {person.description}')
        people_ids.append(temp_uuid)
        people_metadatas.append({"person_id": person.id})
        person.pinecone_id = temp_uuid
        person.save()
    people_index.add_texts(people_texts, people_metadatas, people_ids)

@app.task(name="agi.tasks.respond_to_webhook")
def respond_to_webhook(respond_to, message, user_id, session):
    requests.post(respond_to, json={"message": "You should start by talking to the people around you about what you know"})


@app.task(name="agi.tasks.resume_conversation")
def resume_conversation(session_id, message):
    pass



