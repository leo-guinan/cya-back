import json
import time
from datetime import datetime

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

from prelo.models import PitchDeck, PitchDeckAnalysis, InvestorReport
from prelo.prompts.prompts import WRITE_REPORT_PROMPT, TOP_CONCERN_PROMPT, OBJECTIONS_PROMPT, \
    DERISKING_PROMPT, UPDATED_TOP_CONCERN_PROMPT, UPDATED_OBJECTIONS_PROMPT, UPDATED_DERISKING_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


def combine_into_report(pitch_deck_analysis: PitchDeckAnalysis, investor_report: InvestorReport):
    start_time = time.perf_counter()
    analysis_score = combine_scores(pitch_deck_analysis)
    report = create_report(pitch_deck_analysis.initial_analysis, pitch_deck_analysis.extra_analysis, analysis_score,
                           pitch_deck_analysis.deck.uuid, investor_report)
    print("Report written")
    update_document(pitch_deck_analysis.deck.uuid, report)
    pitch_deck_analysis.report = report
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.COMPLETE
    pitch_deck_analysis.deck.save()
    end_time = time.perf_counter()
    pitch_deck_analysis.report_time = end_time - start_time
    pitch_deck_analysis.save()
    return report


def get_top_objection(pitch_deck_analysis: PitchDeckAnalysis, submind_document):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "top_concerns")
    prompt = ChatPromptTemplate.from_template(TOP_CONCERN_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "deck": pitch_deck_analysis.compiled_slides,
        "analysis": pitch_deck_analysis.extra_analysis,
    })
    return response

def get_updated_top_objection(pitch_deck_analysis:PitchDeckAnalysis, submind_document, deck_changes, thoughts, previous_concern):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "updated_top_concerns")
    prompt = ChatPromptTemplate.from_template(UPDATED_TOP_CONCERN_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "changes": deck_changes,
        "thoughts": thoughts,
        "top_concern": previous_concern,
    })
    return response

def get_investor_objections(pitch_deck_analysis: PitchDeckAnalysis, submind_document):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "objections")
    prompt = ChatPromptTemplate.from_template(OBJECTIONS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "deck": pitch_deck_analysis.compiled_slides,
        "analysis": pitch_deck_analysis.extra_analysis,
    })
    return response

def get_updated_investor_objections(pitch_deck_analysis: PitchDeckAnalysis, submind_document, deck_changes, thoughts, previous_objections):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "updated_objections")
    prompt = ChatPromptTemplate.from_template(UPDATED_OBJECTIONS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "changes": deck_changes,
        "thoughts": thoughts,
        "objections": previous_objections,
    })
    return response


def get_de_risking_strategies(pitch_deck_analysis: PitchDeckAnalysis, submind_document):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "de_risking")
    prompt = ChatPromptTemplate.from_template(DERISKING_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "deck": pitch_deck_analysis.compiled_slides,
        "analysis": pitch_deck_analysis.extra_analysis,
    })
    return response

def get_updated_de_risking_strategies(pitch_deck_analysis: PitchDeckAnalysis, submind_document, deck_changes, thoughts, previous_derisking):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "updated_de_risking")
    prompt = ChatPromptTemplate.from_template(UPDATED_DERISKING_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "mind": submind_document,
        "changes": deck_changes,
        "thoughts": thoughts,
        "derisking": previous_derisking,
    })
    return response

def create_risk_report(pitch_deck_analysis: PitchDeckAnalysis):
    start_time = time.perf_counter()
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)

    top_concern = get_top_objection(pitch_deck_analysis, submind_document)
    objections = get_investor_objections(pitch_deck_analysis, submind_document)
    derisking = get_de_risking_strategies(pitch_deck_analysis, submind_document)
    print(f"Top Concern: {top_concern}")
    print(f"Objections: {objections}")
    print(f"De-risking: {derisking}")
    end_time = time.perf_counter()
    pitch_deck_analysis.top_concern = top_concern
    pitch_deck_analysis.objections = objections
    pitch_deck_analysis.how_to_overcome = derisking
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.COMPLETE
    pitch_deck_analysis.report_time = end_time - start_time
    pitch_deck_analysis.deck.save()
    return top_concern, objections, derisking

def create_updated_risk_report(pitch_deck_analysis: PitchDeckAnalysis, deck_changes, thoughts, previous_analysis):
    start_time = time.perf_counter()
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)

    top_concern = get_updated_top_objection(pitch_deck_analysis, submind_document, deck_changes, thoughts, previous_analysis.top_concern)
    objections = get_updated_investor_objections(pitch_deck_analysis, submind_document, deck_changes, thoughts, previous_analysis.objections)
    derisking = get_updated_de_risking_strategies(pitch_deck_analysis, submind_document, deck_changes, thoughts, previous_analysis.how_to_overcome)
    print(f"Top Concern: {top_concern}")
    print(f"Objections: {objections}")
    print(f"De-risking: {derisking}")
    end_time = time.perf_counter()
    pitch_deck_analysis.top_concern = top_concern
    pitch_deck_analysis.objections = objections
    pitch_deck_analysis.how_to_overcome = derisking
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.COMPLETE
    pitch_deck_analysis.report_time = end_time - start_time
    pitch_deck_analysis.deck.save()
    return top_concern, objections, derisking

def write_how_to_de_risk(pitch_deck_analysis, top_concern, objections, derisking):
    return f"""
# Top Investor Concerns 
{top_concern}

# Objections To Overcome
{objections}

# How to Address the Concerns
{derisking}        
    """.strip()


def combine_scores(pitch_deck_analysis: PitchDeckAnalysis):
    score_model = pitch_deck_analysis.deck.company.scores.first()
    scores_for_report = "Here are the company scores: \n"
    scores_for_report += f"Total Score: {score_model.final_score} \n"
    scores_for_report += f"Recommendation: {score_model.final_reasoning} \n"
    scores_for_report += f"Market Opportunity: {score_model.market_opportunity} \n"
    scores_for_report += f"Reason: {score_model.market_reasoning} \n"
    scores_for_report += f"Team: {score_model.team} \n"
    scores_for_report += f"Reason: {score_model.team_reasoning} \n"
    scores_for_report += f"Founder Market Fit: {score_model.founder_market_fit} \n"
    scores_for_report += f"Reason: {score_model.founder_market_reasoning} \n"
    scores_for_report += f"Product: {score_model.product} \n"
    scores_for_report += f"Reason: {score_model.product_reasoning} \n"
    scores_for_report += f"Traction: {score_model.traction} \n"
    scores_for_report += f"Reason: {score_model.traction_reasoning} \n"
    return scores_for_report


def update_document(doc_uuid, content):
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.prelo

    existing_doc = db.documents.find_one({"uuid": doc_uuid})
    if not existing_doc:
        print("Warning: Document not found in database, creating new document")
        return db.documents.insert_one({
            "content": content,
            "uuid": doc_uuid,
            "status": "complete",
            "createdAt": datetime.now()
        })

    else:
        return db.documents.update_one({"uuid": doc_uuid}, {
            "$set": {"content": content, "updatedAt": datetime.now(), "status": "complete"}})


def create_report(basic_analysis, extra_analysis, investment_score, deck_uuid, investor_report: InvestorReport):
    model = ChatOpenAI(
        model="gpt-4-turbo",
        openai_api_key=config("OPENAI_API_KEY"),
        model_kwargs={
            "extra_headers": {
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}",
                "Helicone-Property-UUID": deck_uuid
            }
        },
        openai_api_base="https://oai.hconeai.com/v1",
    )
    prompt = ChatPromptTemplate.from_template(WRITE_REPORT_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"basic_analysis": json.dumps(basic_analysis), "extra_analysis": extra_analysis,
                             "investment_score": investment_score,
                             "matches_thesis": investor_report.matches_thesis,
                             "thesis_reasons": investor_report.thesis_reasons})
    print(f"After report has been written: {response}")
    return response
