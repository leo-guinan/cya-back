import json
import time
from statistics import mean

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.models import PitchDeck, PitchDeckAnalysis, Company, Team, TeamMember, CompanyScores
from prelo.prompts.functions import functions
from prelo.prompts.prompts import CLEANING_PROMPT, ANALYSIS_PROMPT, EXTRA_ANALYSIS_PROMPT, INVESTMENT_SCORE_PROMPT


def clean_data(data, deck_uuid):
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
    prompt = ChatPromptTemplate.from_template(CLEANING_PROMPT)
    chain = prompt | model.bind(function_call={"name": "extract_promo_info"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke(
        {"raw_info": "\n".join([f"Page: {slide['path']}\n{slide['response']}" for slide in data])})
    print(f"After data has been cleaned: {response}")
    return response


def initial_analysis(data, deck_id, deck_uuid):
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
    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "extract_company_info"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke({"data": data})
    print(f"After data has been analyzed: {response}")
    company = Company()
    company.save()
    team = Team.objects.create(company=company)
    for team_member in response.get('team', ''):
        member = TeamMember()
        member.team = team
        member.name = team_member.get('name', '')
        member.title = team_member.get('role', '')
        member.background = team_member.get('background', '')
        member.founder = team_member.get('founder', False)
        member.save()
    company.name = response.get('company_name', '')
    company.industry = response.get('industry', '')
    company.problem = response.get('problem', '')
    company.solution = response.get('solution', '')
    company.market = response.get('market_size', '')
    company.traction = response.get('traction', '')
    company.revenue = response.get('revenue', '')
    company.funding_round = response.get('funding_round', '')
    company.funding_amount = response.get('funding_amount', '')
    company.why_now = response.get('why_now', '')
    company.contact_info = response.get('contact_info', '')
    company.location = response.get('location', '')
    company.expertise = response.get('domain_expertise', '')
    company.competition = response.get('competition', '')
    company.partnerships = response.get('partnerships', '')
    company.founder_market_fit = response.get('founder_market_fit', '')
    company.deck_id = deck_id
    company.save()

    return response


def extra_analysis(data, summary, deck_uuid):
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
    prompt = ChatPromptTemplate.from_template(EXTRA_ANALYSIS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": data, "summary": summary})
    print(f"After extra analysis: {response}")
    return response


def analyze_deck(pitch_deck_analysis: PitchDeckAnalysis):
    start_time = time.perf_counter()
    initial_analysis_data = initial_analysis(pitch_deck_analysis.compiled_slides, pitch_deck_analysis.deck.id,
                                             pitch_deck_analysis.deck.uuid)
    pitch_deck_analysis.initial_analysis = json.dumps(initial_analysis_data)
    pitch_deck_analysis.save()
    # update the name of the deck with the name of the company
    pitch_deck_analysis.deck.name = pitch_deck_analysis.deck.company.name
    pitch_deck_analysis.deck.save()
    print("Initial analysis complete, starting extra analysis")
    extra_analysis_data = extra_analysis(pitch_deck_analysis.compiled_slides, initial_analysis_data, pitch_deck_analysis.deck.uuid)
    pitch_deck_analysis.extra_analysis = extra_analysis_data
    pitch_deck_analysis.save()
    scored_data = score_investment_potential(pitch_deck_analysis, pitch_deck_analysis.deck.uuid)
    print(scored_data)
    print("Extra analysis complete, writing report")
    pitch_deck_analysis.deck.status = PitchDeck.READY_FOR_REPORTING
    pitch_deck_analysis.deck.save()
    end_time = time.perf_counter()
    pitch_deck_analysis.analysis_time = end_time - start_time
    pitch_deck_analysis.save()


def score_investment_potential(pitch_deck_analysis: PitchDeckAnalysis, deck_uuid: str):
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
    prompt = ChatPromptTemplate.from_template(INVESTMENT_SCORE_PROMPT)
    chain = prompt | model.bind(function_call={"name": "calculate_company_score"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke(
        {"data": pitch_deck_analysis.initial_analysis, "analysis": pitch_deck_analysis.extra_analysis})
    print(f"Scored investment potential: {response}")
    scores = CompanyScores()
    scores.company = pitch_deck_analysis.deck.company
    market = response.get("market", {"score": 0, "reasoning": "missing"})
    scores.market_opportunity = market['score']
    scores.market_reasoning = market['reasoning']
    team = response.get("team", {"score": 0, "reasoning": "missing"})
    scores.team = team['score']
    scores.team_reasoning = team['reasoning']
    founder_market_fit = response.get("founder_market_fit", {"score": 0, "reasoning": "missing"})
    scores.founder_market_fit = founder_market_fit['score']
    scores.founder_market_reasoning = founder_market_fit['reasoning']
    product = response.get("product", {"score": 0, "reasoning": "missing"})
    scores.product = product['score']
    scores.product_reasoning = product['reasoning']
    traction = response.get("traction", {"score": 0, "reasoning": "missing"})
    scores.traction = traction['score']
    scores.traction_reasoning = traction['reasoning']
    scores.final_score = mean([market['score'], team['score'], product['score'], traction['score']])
    scores.save()
    pitch_deck_analysis.report = response
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.READY_FOR_REPORTING
    pitch_deck_analysis.deck.save()
    return response
