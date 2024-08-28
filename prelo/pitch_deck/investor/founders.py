import json

import requests
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.models import PitchDeckAnalysis, Company
from prelo.prompts.functions import functions
from prelo.prompts.prompts import FOUNDER_LINKEDIN_PROMPT, FOUNDER_TWITTER_PROMPT, FOUNDER_CONTACT_PROMPT
from submind.llms.submind import SubmindModelFactory


def google_search(query, num_results=5):
    api_key = config('CUSTOM_SEARCH_API_KEY')
    cse_id = config('CUSTOM_SEARCH_ENGINE_ID')
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num_results,
    }
    response = requests.get(url, params=params)
    return response.json()


def extract_founder_info(pitch_deck_analysis: PitchDeckAnalysis):
    company = Company.objects.filter(deck_uuid=pitch_deck_analysis.deck.uuid).first()
    team = company.team.first()
    model = SubmindModelFactory.get_model(pitch_deck_analysis.deck.uuid, "concerns")
    linkedin_prompt = ChatPromptTemplate.from_template(FOUNDER_LINKEDIN_PROMPT)
    twitter_prompt = ChatPromptTemplate.from_template(FOUNDER_TWITTER_PROMPT)
    contact_prompt = ChatPromptTemplate.from_template(FOUNDER_CONTACT_PROMPT)
    linkedin_chain = linkedin_prompt | model.bind(function_call={"name": "founder_linkedin_extraction"},
                                functions=functions) | JsonOutputFunctionsParser()
    twitter_chain = twitter_prompt | model.bind(function_call={"name": "founder_twitter_extraction"},
                                functions=functions) | JsonOutputFunctionsParser()
    founder_contact_chain = contact_prompt | model.bind(function_call={"name": "founder_contact_extraction"},
                                functions=functions) | JsonOutputFunctionsParser()
    contact_info = founder_contact_chain.invoke({
        "pitch_deck": pitch_deck_analysis.compiled_slides,
    })
    print(f"Contact info: {contact_info} for {company.name}")
    founders = []
    for member in team.members.all():
        if member.founder:
            linkedin_query = f"{member.name} founder {company.name} linkedin"
            twitter_query = f"{member.name} founder {company.name} twitter"
            linkedin_results = google_search(linkedin_query)
            twitter_results = google_search(twitter_query)
            print(twitter_results)

            linkedin_response = linkedin_chain.invoke({
                "founder": member.name,
                "company": company.name,
                "search_results": linkedin_results
            })
            twitter_response = twitter_chain.invoke({
                "founder": member.name,
                "company": company.name,
                "search_results": twitter_results
            })
            print(f"Linkedin: {linkedin_response}")
            print(f"Twitter: {twitter_response}")
            founders.append({
                "name": member.name,
                "linkedin": linkedin_response['results'].get('linkedin_url', ''),
                "twitter": twitter_response['results'].get('twitter_url', '')
            })
    pitch_deck_analysis.founder_summary = json.dumps(founders)
    pitch_deck_analysis.founder_contact_info = json.dumps(contact_info)
    pitch_deck_analysis.save()



