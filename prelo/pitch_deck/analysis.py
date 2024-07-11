import json
import time
from statistics import mean

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser, JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.models import PitchDeck, PitchDeckAnalysis, Company, Team, TeamMember, CompanyScores, GoToMarketStrategy, \
    CompetitorStrategy
from prelo.pitch_deck.investor.believe import believe_analysis
from prelo.pitch_deck.investor.concerns import concerns_analysis, updated_concerns_analysis
from prelo.pitch_deck.investor.memo import write_memo
from prelo.pitch_deck.investor.recommendation import recommendation_analysis, recommended_next_steps
from prelo.pitch_deck.investor.summary import summarize_deck, summarize_investor_report
from prelo.pitch_deck.investor.traction import traction_analysis
from prelo.pitch_deck.reporting import create_updated_risk_report
from prelo.prompts.functions import functions
from prelo.prompts.prompts import CLEANING_PROMPT, ANALYSIS_PROMPT, EXTRA_ANALYSIS_PROMPT, INVESTMENT_SCORE_PROMPT, \
    IDENTIFY_UPDATES_PROMPT, DID_FOUNDER_ADDRESS_CONCERNS_PROMPT, UPDATE_INVESTMENT_SCORE_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


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


def gtm_strategy(pitch_deck_analysis_id, company_id):
    COMPETITOR_ANALYSIS = """You are a powerful submind for a top early-stage investor.

    Here's what you know about early-stage investing: {mind}

    You are reviewing a pitch deck.

    Here's the deck: {deck}

    Based on this, identify what types of competitors we should look for when doing competitive analysis.
    """
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    company = Company.objects.get(id=company_id)
    deck = pitch_deck_analysis.deck
    submind = Submind.objects.get(id=config('PRELO_SUBMIND_ID'))
    submind_document = remember(submind)
    model = SubmindModelFactory.get_model(submind.uuid, "competitor_analysis")

    prompt = ChatPromptTemplate.from_template(COMPETITOR_ANALYSIS)
    chain = prompt | model | StrOutputParser()

    competitors = chain.invoke(
        {"mind": submind_document,
         "deck": pitch_deck_analysis.compiled_slides,
         })


    COMPETITOR_SELECTION = """
    You are a powerful submind for a top early-stage investor.
    
    Here's what you know about early-stage investing: {mind}
    
    Here's your analysis of a company that submitted a pitch deck: {company}
    
    Here's the competitive analysis you created: {competitors}
    
    Based on that, select 5 companies that are the primary competitors, analyze their go to market strategies, and recommend a go to market strategy for the company you are working with. 
    """
    model = SubmindModelFactory.get_model(submind.uuid, "competitor_analysis")


    prompt = ChatPromptTemplate.from_template(COMPETITOR_SELECTION)
    chain = prompt | model.bind(function_call={"name": "create_gtm_strategy"},
                                functions=functions) | JsonOutputFunctionsParser()

    gtm_strategy = chain.invoke(
            {"mind": submind_document,
             "company": deck.analysis.how_to_overcome,
             "competitors":competitors,
            })
    strategy = GoToMarketStrategy()
    strategy.company = company
    strategy.strategy = json.dumps(gtm_strategy['strategy'])
    strategy.save()
    for competitor in gtm_strategy['competitors']:
        competitor_strategy = CompetitorStrategy()
        competitor_strategy.company_name = competitor['name']
        competitor_strategy.strategy = competitor['strategy']
        competitor_strategy.gtm = strategy
        competitor_strategy.save()


def initial_analysis(pitch_deck_analysis_id, company_id):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    company = Company.objects.get(id=company_id)
    data = pitch_deck_analysis.compiled_slides
    model = SubmindModelFactory.get_model(company.deck_uuid, "initial_analysis", 0.0)
    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "extract_company_info"}, functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke({"data": data})
    print(f"After data has been analyzed: {response}")

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
    company.save()


def extra_analysis(data, deck_uuid):
    model = SubmindModelFactory.get_model(deck_uuid, "extra_analysis", 0.0)
    prompt = ChatPromptTemplate.from_template(EXTRA_ANALYSIS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": data})
    return response


def analyze_deck(pitch_deck_analysis: PitchDeckAnalysis):
    start_time = time.perf_counter()

    print("Initial analysis complete, starting extra analysis")
    extra_analysis_data = extra_analysis(pitch_deck_analysis.compiled_slides,
                                         pitch_deck_analysis.deck.uuid)
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


def analyze_deck_changes(new_deck, old_deck):
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)

    model = SubmindModelFactory.get_model(submind.uuid, "identify_updates")

    prompt = ChatPromptTemplate.from_template(IDENTIFY_UPDATES_PROMPT)
    chain = prompt | model | StrOutputParser()

    response = chain.invoke(
        {"mind": submind_document,
         "earlier_deck": old_deck,
         "newer_deck": new_deck
         })
    return response


def check_against_concerns(deck_changes: str, previous_deck_analysis: PitchDeckAnalysis):
    submind = Submind.objects.get(id=config("PRELO_SUBMIND_ID"))
    submind_document = remember(submind)
    model = SubmindModelFactory.get_model(submind.uuid, "addressed_concerns")

    prompt = ChatPromptTemplate.from_template(DID_FOUNDER_ADDRESS_CONCERNS_PROMPT)
    chain = prompt | model | StrOutputParser()

    addressed = chain.invoke(
        {"mind": submind_document,
         "changes": deck_changes,
         "top_concern": previous_deck_analysis.top_concern,
         "concerns": previous_deck_analysis.objections,
         "derisking": previous_deck_analysis.how_to_overcome
         })
    return addressed


def compare_deck_to_previous_version(pitch_deck_analysis: PitchDeckAnalysis):
    previous_deck = PitchDeck.objects.filter(user_id=pitch_deck_analysis.deck.user_id,
                                             version=(pitch_deck_analysis.deck.version - 1)).first()
    print(f"Previous deck: {previous_deck}")
    if not previous_deck:
        raise "No previous deck found"
    previous_deck_analysis = previous_deck.analysis
    previous_scores = previous_deck_analysis.deck.scores
    deck_changes = analyze_deck_changes(pitch_deck_analysis.compiled_slides, previous_deck_analysis.compiled_slides)
    concerns_addressed = check_against_concerns(deck_changes, previous_deck_analysis)
    updated_scores = update_scores(pitch_deck_analysis, deck_changes, concerns_addressed, previous_deck_analysis.report)
    top_concern, objections, how_to_overcome = create_updated_risk_report(pitch_deck_analysis, deck_changes,
                                                                          concerns_addressed, previous_deck_analysis)
    print("Updated risk report created")

    updated_concerns = updated_concerns_analysis(pitch_deck_analysis,
                                                 deck_changes,
                                                 concerns_addressed,
                                                 previous_deck_analysis.concerns)

    print("Updated concerns analysis complete")
    return top_concern, objections, how_to_overcome, updated_concerns, previous_scores, updated_scores


def investor_analysis(pitch_deck_analysis: PitchDeckAnalysis):
    start_time = time.perf_counter()
    print("Initial analysis complete, starting extra analysis")
    summarize_deck(pitch_deck_analysis)
    print("Summary complete")
    traction_analysis(pitch_deck_analysis)
    print("Traction complete")
    concerns_analysis(pitch_deck_analysis)
    print("Concerns complete")
    recommendation_analysis(pitch_deck_analysis)
    print("Recommendation complete")


    summarize_investor_report(pitch_deck_analysis)
    recommended_next_steps(pitch_deck_analysis)
    end_time = time.perf_counter()
    pitch_deck_analysis.analysis_time = end_time - start_time
    pitch_deck_analysis.save()


def score_investment_potential(pitch_deck_analysis: PitchDeckAnalysis, deck_uuid: str):
    model = SubmindModelFactory.get_model(deck_uuid, "score_investment_potential", 0.0)
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
    scores.deck = pitch_deck_analysis.deck
    scores.save()
    pitch_deck_analysis.report = response
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.READY_FOR_REPORTING
    pitch_deck_analysis.deck.save()
    return response

def update_scores(pitch_deck_analysis: PitchDeckAnalysis, changes: str, thoughts:str, scores:str ):
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "update_score_investment_potential", 0.0)
    prompt = ChatPromptTemplate.from_template(UPDATE_INVESTMENT_SCORE_PROMPT)
    chain = prompt | model.bind(function_call={"name": "calculate_company_score"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke(
        {"changes": changes,
         "thoughts": thoughts,
         "scores": scores
        })
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
    scores.deck = pitch_deck_analysis.deck
    scores.save()
    pitch_deck_analysis.report = response
    pitch_deck_analysis.save()
    pitch_deck_analysis.deck.status = PitchDeck.READY_FOR_REPORTING

    pitch_deck_analysis.deck.save()
    return scores
