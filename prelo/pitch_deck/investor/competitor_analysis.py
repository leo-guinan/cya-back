import json
from typing import Dict, List, Literal

from bs4 import BeautifulSoup
import requests
from prelo.events import record_prelo_event
from prelo.models import Company, Competitor, PitchDeck
from decouple import config
from langchain_core.prompts import ChatPromptTemplate
from prelo.pitch_deck.analysis import initial_analysis
from submind.llms.submind import SubmindModelFactory
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

JINA_READER_PREFIX = "https://r.jina.ai/"
ANALYSIS_TYPE = Literal["funding", "benefit", "price", "market_share"]

functions = [
    {
        "name": "get_details_from_deck",
        "description": "Get details from the deck",
        "parameters": {
            "type": "object",
            "properties": {
                "solution": {"type": "string"},
                "problem": {"type": "string"},
                "target_market": {"type": "string"},
                "unique_value_proposition": {"type": "string"},
            },
        },
    },
    {
        "name": "extract_competitor_info",
        "description": "Extract competitor information from the provided content.",
        "parameters": {
            "type": "object",
            "properties": {
                "competitors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "funding": {"type": "string"},
                            "features": {"type": "array", "items": {"type": "string"}},
                            "prices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "price": {"type": "string"},
                                        "plan_information": {"type": "string"},
                                    },
                                },
                            },
                            "market_share": {"type": "string"},
                        },
                    },
                }
            },
        },
    },
    {
        "name": "create_feature_matrix",
        "description": "Create a feature matrix for the provided companies.",
        "parameters": {
            "type": "object",
            "properties": {
                "feature_matrix": {"type": "string"},
            },
        },
    },
    {
        "name": "get_company_features_from_deck",
        "description": "Extract company features from the deck.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_features": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
]


def get_competitor_analysis(deck: PitchDeck, analysis_type: ANALYSIS_TYPE):
    print("Starting competitor analysis...")
    competitors = deck.competitors.all()
    if not competitors:
        print("No competitors found in deck, fetching competitors...")
        competitors = get_competitors(deck)
    else:
        print("Competitors found in deck, using existing data.")
    
    if analysis_type == "funding":
        print("Performing funding analysis...")
        return "\n".join(list(map(lambda x: f"{x.name}: {x.funding_report}", competitors)))
    elif analysis_type == "benefit":
        return create_feature_matrix(deck)
    elif analysis_type == "price":
        print("Performing price analysis...")
        return "\n".join(list(map(lambda x: f"{x.name}: {x.price_report}", competitors)))
    elif analysis_type == "market_share":
        print("Performing market share analysis...")
        return "\n".join(list(map(lambda x: f"{x.name}: {x.market_share_report}", competitors)))


def get_competitors(deck: PitchDeck):
    print("Generating search terms...")
    search_terms = generate_search_terms(deck)
    search_results = []
    competitor_lists = []

    for term in search_terms:
        print(f"Performing Google search for term: {term}")
        try:
            results = perform_google_search(term)
            for result in results['items']:
                competitor_lists.append(f"{result['title']}\n{result['link']}")
        except Exception as e:
            print(f"Error during Google search for query '{term}': {e}")
            continue

    combined = "\n".join(competitor_lists)
    print("Extracting competitor information from combined search results...")
    competitor_info = extract_competitor_info_for_all(deck, combined)
    print("Consolidating competitor information...")
    competitors = consolidate_competitors(deck, competitor_info)
    return competitors


def generate_search_terms(deck: PitchDeck) -> List[str]:
    print("Extracting information from deck to generate search terms...")
    info = get_info_from_deck(deck)
    solution = info["solution"]
    unique_value_proposition = info["unique_value_proposition"]
    problem = info["problem"]
    target_market = info["target_market"]
    terms = []
    terms.append(f"{solution} for {target_market}")
    terms.append(f"{unique_value_proposition}")
    terms.append(f"{problem} {solution}")
    terms.append(f"Competitive alternatives to {solution}")
    terms.append(f"Top {target_market} {solution}")

    unique_terms = list(dict.fromkeys(terms))[:5]
    print(f"Generated search terms: {unique_terms}")
    return unique_terms


def perform_google_search(query: str, num_results: int = 5) -> List[Dict]:
    print(f"Performing Google search for query: {query}")
    api_key = config("CUSTOM_SEARCH_API_KEY")
    cse_id = config("CUSTOM_SEARCH_ENGINE_ID")
    try:
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": num_results,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        print(f"Google search successful for query: {query}")
        return response.json()

    except Exception as e:
        print(f"Error during Google search for query '{query}': {e}")
        return []


def scrape_webpage(url: str) -> str:
    print(f"Scraping webpage: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(JINA_READER_PREFIX + url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Successfully scraped webpage: {url}")
        return response.content
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""


def extract_competitor_info_for_all(deck: PitchDeck, content: str) -> List[Dict]:
    print("Extracting competitor information using GPT-4...")
    model = SubmindModelFactory.get_mini(f"competitor_analysis_{deck.uuid}", "extract_competitor_info", temperature=0.0)
    prompt = ChatPromptTemplate.from_template(
        """
You are an analyst tasked with extracting company information from the provided content. 
Please identify the companies mentioned and provide the following details for each:

1. Name
2. Description
3. Company Funding
4. Features
5. Prices
6. Market Share

Here's the content:
{content}

    """
    )
    chain = (
        prompt
        | model.bind(
            function_call={"name": "extract_competitor_info"}, functions=functions
        )
        | JsonOutputFunctionsParser()
    )
    response = chain.invoke({"content": content})
    print("Competitors extracted: ", response)
    return response
    


def consolidate_competitors(
    deck: PitchDeck,
    competitor_lists: Dict,
) -> List[Competitor]:
    print("Consolidating competitor lists into unique list...")
    unique = {}
    for comp in competitor_lists['competitors']:
        if comp['name'] and comp['name'].lower() not in unique:
            unique[comp['name'].lower()] = comp

    all_competitors = list(unique.values())
    competitors = []
    for competitor in all_competitors:
        print(f"Creating Competitor model for: {competitor['name']}")
        competitor_model = Competitor.objects.create(
            name=competitor['name'],
            description=competitor['description'],
            price_report="\n".join(map(lambda x: f'{x["price"]}: {x["plan_information"]}', competitor['prices'])),
            benefit_report="\n".join(competitor['features']),
            market_share_report=competitor['market_share'],
            funding_report=competitor['funding'],
            deck=deck,
        )
        competitors.append(competitor_model)
    print("Competitor consolidation complete.")
    return competitors


def get_info_from_deck(deck: PitchDeck) -> Dict:
    print("Extracting information from deck using GPT-4...")
    template = """
You are an analyst tasked with extracting information about the company from the provided information in their pitch deck. 
Please identify the following details:

1. Solution
2. Problem
3. Target Market
4. Unique Value Proposition

Here's the deck content:
{content}

    """
    model = SubmindModelFactory.get_mini(f"competitor_analysis_{deck.uuid}", "get_info_from_deck", temperature=0.0)
    prompt = ChatPromptTemplate.from_template(template)
    chain = (
        prompt
        | model.bind(
            function_call={"name": "get_details_from_deck"}, functions=functions
        )
        | JsonOutputFunctionsParser()
    )
    response = chain.invoke({"content": deck.analysis.compiled_slides})
    print("Information extracted from deck: ", response)
    return response


def create_feature_matrix(deck: PitchDeck):
    if deck.feature_matrix:
        return deck.feature_matrix
    competitors = deck.competitors.all()
    if len(competitors) == 0:
        competitors = get_competitors(deck)
    
    
    print("Creating feature matrix for competitors...")
    model = SubmindModelFactory.get_mini(f"competitor_analysis_{deck.uuid}", "create_feature_matrix", temperature=0.0)
    company = Company.objects.filter(deck_uuid=deck.uuid).first()
    if not company:
        print("Company not found, creating company...")
        record_prelo_event({
            "event": "competitor_analysis",
            "type": "missing_company",
            "deck_uuid": deck.uuid,
            "action": "Creating a new company for the deck and populating it."
        })
        # I guess we need to process the deck again to get the company info?
        company = Company.objects.create(deck_uuid=deck.uuid)
        company = initial_analysis(deck.analysis.id, company.id)
    prompt = ChatPromptTemplate.from_template(
        """
You are an analyst tasked with creating a feature matrix for the provided company and their competitors. 
If features are similar, combine them into a single type. Create a matrix with as few rows as possible given the options available.
In the first column, list the features.
For the header row, list the company names.
In the second column, list the main company. Then list the competitors in the subsequent columns.
Use well-formatted markdown to create a nice display. Center align all values.

Here is the company:
{company}

Here are the features of the company:
{company_features}

Here is the list of competitors:
{competitors}
    """
    )
    chain = (
        prompt
        | model.bind(
            function_call={"name": "create_feature_matrix"}, functions=functions
        )
        | JsonOutputFunctionsParser()
    )
    response = chain.invoke({"company": company.name, "company_features": deck.company_features, "competitors": "\n".join(list(map(lambda x: f"{x.name}: {x.benefit_report}", competitors)))})
    print("Feature matrix created: ", response)
    deck.feature_matrix = response['feature_matrix']
    deck.save()
    return deck.feature_matrix

def get_company_features_from_deck(deck: PitchDeck):
    print("Extracting company features from deck using GPT-4...")
    template = """
You are an analyst tasked with extracting information about the company's features from the provided information in their pitch deck. 

Here is the deck content:
{content}
    """
    model = SubmindModelFactory.get_mini(f"competitor_analysis_{deck.uuid}", "get_company_features_from_deck", temperature=0.0)
    prompt = ChatPromptTemplate.from_template(template)
    chain = (
        prompt
        | model.bind(
            function_call={"name": "get_company_features_from_deck"}, functions=functions
        )
        | JsonOutputFunctionsParser()
    )
    response = chain.invoke({"content": deck.analysis.compiled_slides})
    print("Company features extracted from deck: ", response)
    deck.company_features = response['company_features']
    deck.save()
    return deck.company_features
