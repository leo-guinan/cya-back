import base64
import json
import os
import tempfile
from datetime import datetime

import fitz
from decouple import config
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

from prelo.aws.s3_utils import download_file_from_s3
from prelo.models import PitchDeck

CLEANING_PROMPT = """ 
        You are an expert at identifying promotional information from the description of images in a pitch deck.

        Identify the information related to the tool used to create the deck and return a clean version of the initial data without any of the promotional information.

        If there is a page dedicated to the tool in the slides, remove that entire page.

        Here is the information extracted from the pitch deck: {raw_info}.

"""

ANALYSIS_PROMPT = """ 
        You are an expert at reading company pitch decks for investors. Given the information from a pitch deck, extract the following information:

        Company Name
        Company Founder(s)/Team
        Industry
        Problem
        Solution
        Market Size
        Traction
        Why Now?
        Domain expertise of the team/founders
        Founder contact info
        When company was founded
        Funding Round
        Funding Amount
        Location


        Here's the pitch deck data: {data}

"""

EXTRA_ANALYSIS_PROMPT = """ 
        You are an expert investor who is especially skilled at identifying why a given company might succeed and what risks might kill the company.

        Given the raw data from the pitch deck and the summary of the information extracted, identify the biggest risks to the company, the biggest indicators of potential success, 
        and the questions you would want answered in order to de-risk the company.

        Here's the pitch deck data: {data}

        And the summarized data: {summary}

"""

WRITE_REPORT_PROMPT = """
    You are an analyst for a top investor who is looking to invest in a company. 
    You have been given a pitch deck to analyze and provide a report on.
    
    Here are the results of the analysis.
    
    Basic analysis from the pitch deck: {basic_analysis}
    
    Detailed analysis of risks, opportunities, and questions: {extra_analysis}
    
    Write a report that summarizes the key points of the pitch deck and provides a recommendation on whether to invest in the company or not.
    
    
"""

functions = [
    {
        "name": "extract_promo_info",
        "description": "identify and remove promotional material related to the tools used to create a pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "promotional_info": {
                            "type": "string",
                            "description": "The promotional information identified",
                        },
                        "clean_info": {
                            "type": "string",
                            "description": "The starting info without any of the promotional info"
                        }

                    }
                },
            },
            "required": ["results"],
        },
    },
    {
        "name": "extract_company_info",
        "description": "identify information about the company pitching the investor",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "the name of the company",
                        },
                        "founders": {
                            "type": "string",
                            "description": "The founders and/or team"
                        },
                        "industy": {
                            "type": "string",
                            "description": "The industry of the company"
                        },
                        "problem": {
                            "type": "string",
                            "description": "the problem the company is solving"
                        },
                        "solution": {
                            "type": "string",
                            "description": "the company's solution to the problem"
                        },
                        "market_size": {
                            "type": "string",
                            "description": "The estimated market size the company is targeting"
                        },
                        "traction": {
                            "type": "string",
                            "description": "the company's traction so far"
                        },
                        "why_now": {
                            "type": "string",
                            "description": "Why the company should exist now"
                        },
                        "domain_expertise": {
                            "type": "string",
                            "description": "what special expertise the founder/team have that will help them solve this problem"
                        },
                        "founder_contact": {
                            "type": "string",
                            "description": "Contact Info for the founder"
                        },
                        "founding_date": {
                            "type": "string",
                            "description": "The approximate date the company was founded"
                        },
                        "location": {
                            "type": "string",
                            "description": "where the company is based"
                        },
                        "funding_round": {
                            "type": "string",
                            "description": "The current funding round the company is raising"
                        },
                        "funding_amount": {
                            "type": "string",
                            "description": "The amount of money the company wants to raise"
                        },

                    }
                },
            },
            "required": ["results"],
        },
    },
]


def pdf_to_images(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # number of page
        pix = page.get_pixmap()
        output_path = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_path)


PITCH_DECK_SLIDE_PROMPT = """You are an expert pitch deck slide analyzer. This is a slide from a company's pitch deck for investors. What information does this slide contain?"""


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


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
    response = chain.invoke(
        {"data": data})
    print(f"After data has been analyzed: {response}")
    return response


def extra_analysis(data, summary):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(EXTRA_ANALYSIS_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"data": data, "summary": json.dumps(summary)})
    print(f"After extra analysis: {response}")
    return response


def create_report(basic_analysis, extra_analysis):
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(WRITE_REPORT_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"basic_analysis": json.dumps(basic_analysis), "extra_analysis": extra_analysis})
    print(f"After report has been written: {response}")
    return response


def analyze_pitch_deck(pitch_deck: PitchDeck):
    try:
        temp_file = download_file_from_s3(pitch_deck.s3_path)

        image_dir = tempfile.gettempdir()
        pdf_to_images(temp_file, image_dir)
        image_uris = sorted([os.path.join(image_dir, image_name) for image_name in os.listdir(image_dir) if
                             not os.path.isdir(image_name)])
        raw_slides = []
        for image_uri in image_uris:
            if not image_uri.endswith('.png'):
                continue
            print(f"Analyzing image: {image_uri}")
            base64_image = encode_image(image_uri)
            model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
            message = HumanMessage([
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "auto"
                    }
                }
            ])
            response = model.invoke([message])
            raw_slides.append({
                'path': image_uri,
                'response': response
            })
        print("All slides analyzed, cleaning data")
        # cleaned_data = clean_data(raw_slides)
        combined = "\n".join([f"Page: {slide['path']}\n{slide['response']}" for slide in raw_slides])
        print("Data cleaned, starting initial analysis")
        initial_analysis_data = initial_analysis(combined)
        print("Initial analysis complete, starting extra analysis")
        extra_analysis_data = extra_analysis(combined, initial_analysis_data)
        print("Extra analysis complete, writing report")
        report = create_report(initial_analysis_data, extra_analysis_data)
        print("Report written")
        update_document(pitch_deck.uuid, report)
        pitch_deck.status = PitchDeck.COMPLETE
        pitch_deck.save()
    except Exception as e:
        print(f"Error analyzing pitch deck: {e}")
        pitch_deck.status = PitchDeck.ERROR
        pitch_deck.save()


def cleanup_local_file(path):
    """
    Delete a file from the local filesystem.

    :param path: str, the path to the file to be deleted
    """
    if os.path.exists(path):
        os.remove(path)


def update_document(doc_uuid, content):
    mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
    db = mongo_client.prelo

    existing_doc = db.documents.find_one({"uuid": doc_uuid})
    if not existing_doc:
        print("Warning: Document not found in database, creating new document")
        db.documents.insert_one({
            "content": content,
            "uuid": doc_uuid,
            "createdAt": datetime.now()
        })

    else:
        db.documents.update_one({"uuid": doc_uuid}, {
            "$set": {"content": content, "updatedAt": datetime.now()}})
