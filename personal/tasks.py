from decouple import config
from pymongo import MongoClient

from backend.celery import app


@app.task(name="personal.tasks.look_for_new_messages")
def look_for_new_messages():
    mongo_client = MongoClient(config('PERSONAL_MONGODB_CONNECTION_STRING'))
    db = mongo_client.agi
    messages = db.messages.find({"processed": False})
    print(db.messages.count_documents({"processed": False}))

    for message in messages:
        print(message)
        message['processed'] = True
        db.messages.update_one({"_id": message['_id']}, {"$set": message})


@app.task(name="personal.tasks.process_message")
def process_message(message):
    print(message)
    # do I know locally? Answer