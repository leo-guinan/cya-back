from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prelo.models import PitchDeck
from prelo.prompts.functions import functions
from prelo.prompts.prompts import SLIDE_DECK_UUID_PROMPT, PITCH_DECK_QUESTION_PROMPT, \
    SLIDE_DECK_UUID_SLIDE_NUMBERS_PROMPT, PITCH_DECK_SLIDES_QUESTION_PROMPT
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser, JsonKeyOutputFunctionsParser


def answer_question_about_slide(message, input_data, previous_tool_results=None):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(SLIDE_DECK_UUID_SLIDE_NUMBERS_PROMPT)
    chain = prompt | model.bind(function_call={"name": "lookup_pitch_deck_uuid_and_slide_numbers"},
                                functions=functions) | JsonOutputFunctionsParser()
    uuid_with_slide_numbers = chain.invoke({
        "message": input_data,

    })
    deck_uuid = uuid_with_slide_numbers["uuid"]
    slide_numbers = uuid_with_slide_numbers["slide_numbers"]
    deck = PitchDeck.objects.filter(uuid=deck_uuid).first()
    slides = deck.slides.filter(order__in=slide_numbers).all()
    answer_prompt = ChatPromptTemplate.from_template(PITCH_DECK_SLIDES_QUESTION_PROMPT)
    answer_chain = answer_prompt | model | StrOutputParser()
    message_content = f"{previous_tool_results}\n{message} " if previous_tool_results else message
    if not deck:
        raise ValueError("Deck not found")
    deck_analysis = deck.analysis
    response = answer_chain.invoke({
        "deck_info": deck_analysis.compiled_slides,
        "slides": [slide.content for slide in slides],
        "request": message_content
    })
    print(response)
    return response


def answer_question_about_deck(message, input_data, previous_tool_results=None):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(SLIDE_DECK_UUID_PROMPT)
    chain = prompt | model.bind(function_call={"name": "lookup_pitch_deck_uuid"},
                                functions=functions) | JsonKeyOutputFunctionsParser(key_name="uuid")
    uuid_to_lookup = chain.invoke({
        "message": input_data,

    })
    print(f"UUID: {uuid_to_lookup}")
    deck = PitchDeck.objects.filter(uuid=uuid_to_lookup).first()
    answer_prompt = ChatPromptTemplate.from_template(PITCH_DECK_QUESTION_PROMPT)
    answer_chain = answer_prompt | model | StrOutputParser()
    message_content = f"{previous_tool_results}\n{message} " if previous_tool_results else message
    if not deck:
        raise ValueError("Deck not found")
    deck_analysis = deck.analysis
    response = answer_chain.invoke({
        "deck_info": deck_analysis.compiled_slides,
        "analysis": deck_analysis.extra_analysis,
        "request": message_content
    })
    print(response)
    return response

def answer_question_about_founder(message, input_data, previous_tool_results=None):
    return "Not implemented yet"

def answer_question_about_company(message, input_data, previous_tool_results=None):
    return "Not implemented yet"