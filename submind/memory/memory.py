from datetime import datetime

import uuid
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

from submind.llms.submind import SubmindModelFactory
from submind.models import Submind
from submind.prompts.prompts import LEARNING_PROMPT


# client will allow same submind to be used by multiple users
def remember(submind: Submind, client_id=None):
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    if client_id:

        existing_doc = db.documents.find_one({"uuid": submind.mindUUID, "client_id": client_id})
        if not existing_doc:
            db.documents.insert_one({
                "content": "",
                "uuid": submind.mindUUID,
                "createdAt": datetime.now(),
                "client_id": client_id
            })
            existing_doc = db.documents.find_one({"uuid": submind.mindUUID, "client_id": client_id})
    else:
        existing_doc = db.documents.find_one({"uuid": submind.mindUUID})
        if not existing_doc:
            db.documents.insert_one({
                "content": "",
                "uuid": submind.mindUUID,
                "createdAt": datetime.now()
            })
            existing_doc = db.documents.find_one({"uuid": submind.mindUUID})
    return existing_doc['content']


def learn(learning: dict, submind: Submind):
    print("Beginning learning process")
    mind = remember(submind)
    model = SubmindModelFactory.get_model(submind.uuid, "learn")
    prompt = ChatPromptTemplate.from_template(LEARNING_PROMPT)
    output_parser = StrOutputParser()
    chain = prompt | model | output_parser
    new_mind = chain.invoke({
        "description": submind.description,
        "mind": mind,
        "question": learning['question'],
        "answer": learning['answer']
    })

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
        "$set": {"content": new_mind, "previousVersion": historical_uuid, "updatedAt": datetime.now()}}, upsert=True)
