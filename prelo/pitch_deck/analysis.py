import json

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.models import PitchDeck, PitchDeckAnalysis
from prelo.prompts.functions import functions
from prelo.prompts.prompts import CLEANING_PROMPT, ANALYSIS_PROMPT, EXTRA_ANALYSIS_PROMPT


def clean_data(data):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(CLEANING_PROMPT)
    chain = prompt | model.bind(function_call={"name": "extract_promo_info"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke(
        {"raw_info": "\n".join([f"Page: {slide['path']}\n{slide['response']}" for slide in data])})
    print(f"After data has been cleaned: {response}")
    return response


def initial_analysis(data):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "extract_company_info"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="results")
    response = chain.invoke({"data": data})
    print(f"After data has been analyzed: {response}")
    return response


def extra_analysis(data, summary):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(EXTRA_ANALYSIS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": data, "summary": summary})
    print(f"After extra analysis: {response}")
    return response


def analyze_deck(pitch_deck_analysis: PitchDeckAnalysis):
    initial_analysis_data = initial_analysis(pitch_deck_analysis.compiled_slides)
    pitch_deck_analysis.initial_analysis = json.dumps(initial_analysis_data)
    pitch_deck_analysis.save()
    print("Initial analysis complete, starting extra analysis")
    extra_analysis_data = extra_analysis(pitch_deck_analysis.compiled_slides, initial_analysis_data)
    pitch_deck_analysis.extra_analysis = extra_analysis_data
    pitch_deck_analysis.save()
    print("Extra analysis complete, writing report")
    pitch_deck_analysis.deck.status = PitchDeck.READY_FOR_REPORTING
    pitch_deck_analysis.deck.save()
