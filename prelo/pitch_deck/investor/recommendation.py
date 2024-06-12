from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.investor.prompts.llm import functions
from prelo.models import PitchDeckAnalysis, InvestmentFirm, Investor, InvestorReport
from prelo.prompts.prompts import RECOMMENDATION_PROMPT
from submind.llms.submind import SubmindModelFactory


def recommendation_analysis(pitch_deck_analysis: PitchDeckAnalysis):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "concerns")
    prompt = ChatPromptTemplate.from_template(RECOMMENDATION_PROMPT)
    chain = prompt | model.bind(function_call={"name": "recommendation_analysis"},
                                functions=functions) | JsonOutputFunctionsParser()
    firm_id = pitch_deck_analysis.deck.s3_path.split("/")[-4]
    investor_id = pitch_deck_analysis.deck.s3_path.split("/")[-3]
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
    investor_report.save()
    pitch_deck_analysis.investor_report = investor_report
    pitch_deck_analysis.save()
    return response
