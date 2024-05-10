from decouple import config
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.investor.prompts.llm import functions, THESIS_MATCH
from prelo.models import PitchDeckAnalysis, InvestorReport
from submind.llms.submind import SubmindModelFactory


def check_deck_against_thesis(pitch_deck_analysis: PitchDeckAnalysis, investor):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "check_deck_against_thesis", temperature=0.0)
    prompt = ChatPromptTemplate.from_template(THESIS_MATCH)
    chain = prompt | model.bind(function_call={"name": "match_thesis"},
                                functions=functions) | JsonOutputFunctionsParser()
    response = chain.invoke({"thesis": investor.thesis, "deck": pitch_deck_analysis.compiled_slides})
    print(f"After checking deck against thesis: {response}")
    investor_report = InvestorReport()
    investor_report.investor = investor
    investor_report.matches_thesis = response['matches']
    investor_report.thesis_reasons = response['reason']
    investor_report.thesis_match_score = response['score']
    investor_report.company = pitch_deck_analysis.deck.company
    investor_report.save()
    return investor_report

