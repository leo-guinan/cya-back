import json
from datetime import datetime

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

from prelo.models import PitchDeck, PitchDeckAnalysis
from prelo.prompts.prompts import WRITE_REPORT_PROMPT


def combine_into_report(pitch_deck_analysis: PitchDeckAnalysis):
    report = create_report(pitch_deck_analysis.initial_analysis, pitch_deck_analysis.extra_analysis)
    print("Report written")
    update_document(pitch_deck_analysis.deck.uuid, report)
    pitch_deck_analysis.report = report
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.COMPLETE
    pitch_deck_analysis.deck.save()
    return report



def update_document(doc_uuid, content):
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.prelo

    existing_doc = db.documents.find_one({"uuid": doc_uuid})
    if not existing_doc:
        print("Warning: Document not found in database, creating new document")
        return db.documents.insert_one({
            "content": content,
            "uuid": doc_uuid,
            "createdAt": datetime.now()
        })

    else:
        return db.documents.update_one({"uuid": doc_uuid}, {
            "$set": {"content": content, "updatedAt": datetime.now()}})


def create_report(basic_analysis, extra_analysis):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(WRITE_REPORT_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"basic_analysis": json.dumps(basic_analysis), "extra_analysis": extra_analysis})
    print(f"After report has been written: {response}")
    return response
