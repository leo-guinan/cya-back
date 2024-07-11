import json
import uuid

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.investor.prompts.llm import functions
from prelo.models import PitchDeckAnalysis, InvestmentFirm, Investor, InvestorReport
from prelo.prompts.prompts import RECOMMENDATION_PROMPT, RECOMMEND_NEXT_STEPS_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


def recommendation_analysis(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "concerns")
    prompt = ChatPromptTemplate.from_template(RECOMMENDATION_PROMPT)
    chain = prompt | model.bind(function_call={"name": "recommendation_analysis"},
                                functions=functions) | JsonOutputFunctionsParser()
    firm_id = pitch_deck_analysis.deck.s3_path.split("/")[-3]
    print(f"Firm ID: {firm_id}")
    investor_id = pitch_deck_analysis.deck.s3_path.split("/")[-2]
    print(f"Investor ID: {investor_id}")
    firm = InvestmentFirm.objects.get(lookup_id=firm_id)
    investor = Investor.objects.get(lookup_id=investor_id)
    response = chain.invoke({
        "firm_thesis": firm.thesis,
        "investor_thesis": investor.thesis,
        "summary": pitch_deck_analysis.summary,
        "concerns": pitch_deck_analysis.concerns,
        "believe": pitch_deck_analysis.believe,
        "traction": pitch_deck_analysis.traction,
    })
    print(f"After data has been analyzed: {response}")
    investor_report = InvestorReport()
    investor_report.investor = investor
    investor_report.firm = firm
    investor_report.recommendation_reasons = response['reason']
    investor_report.investment_potential_score = response['score']
    investor_report.matches_thesis = response['matches']
    investor_report.uuid = str(uuid.uuid4())
    investor_report.save()
    pitch_deck_analysis.investor_report = investor_report
    pitch_deck_analysis.save()
    return response


def recommended_next_steps(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "concerns")
    prompt = ChatPromptTemplate.from_template(RECOMMEND_NEXT_STEPS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "recommended_next_step"}, functions=functions) | JsonOutputFunctionsParser()
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)
    response = chain.invoke({
        "mind": submind_document,
        "report": pitch_deck_analysis.investor_report.recommendation_reasons,
        "score": pitch_deck_analysis.investor_report.investment_potential_score,
    })

    print(f"Recommended next step: {json.dumps(response)}")
    pitch_deck_analysis.investor_report.recommended_next_steps = json.dumps(response)
    pitch_deck_analysis.investor_report.save()

