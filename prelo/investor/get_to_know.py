import uuid
from datetime import datetime

from decouple import config
from pymongo import MongoClient

from prelo.models import Investor
from submind.models import Submind
from toolkit.tools.person_search import learn_about_person


def learn_about_investor(investor_id):
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    investor = Investor.objects.get(id=investor_id)
    submind_uuid = str(uuid.uuid4())
    submind_mind_uuid = str(uuid.uuid4())
    submind = Submind.objects.create(uuid=submind_uuid, name=f"Investor Submind for {investor.name}", mindUUID=submind_mind_uuid, description="This is a submind that has learned about an investor and thinks about things the way they do.")
    db.documents.insert_one({
        "content": f"You want to learn how to think exactly like {investor.name}. Learn what you can about them and how they are different from the average early stage investor.",
        "uuid": submind.mindUUID,
        "createdAt": datetime.now()
    })
    learn_about_person(investor.name, submind_uuid, submind.id)

