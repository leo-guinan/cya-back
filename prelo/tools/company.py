import uuid
import requests
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable
from pinecone import Pinecone
from pyairtable import Api
from django.db import models, transaction

from submind.prompts.prompts import TOOL_RESULT_PROMPT


def get_fundraises():
    pass


def get_industry():
    pass


# can we turn a plaintext query into a structured airtable query? Maybe for now, just create a fulltext field and dump in pinecone?
schema = {

}


def get_airtable_schema(base_id, api_key):
    url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# Function to map Airtable field types to Django field types
def map_field_type(airtable_type):
    mapping = {
        'singleLineText': 'models.CharField(max_length=255)',
        'multilineText': 'models.TextField()',
        'richText': 'models.TextField()',
        'number': 'models.FloatField()',
        'checkbox': 'models.BooleanField()',
        'date': 'models.DateField()',
        'dateTime': 'models.DateTimeField()',
        'currency': 'models.DecimalField(max_digits=10, decimal_places=2)',
        'percent': 'models.FloatField()',
        'singleSelect': 'models.CharField(max_length=255)',
        'multipleSelects': 'models.JSONField()',
        'attachment': 'models.JSONField()',
        'formula': 'models.CharField(max_length=255)',
        'rollup': 'models.CharField(max_length=255)',
        'createdTime': 'models.DateTimeField(auto_now_add=True)',
        'lastModifiedTime': 'models.DateTimeField(auto_now=True)',
        'autoNumber': 'models.AutoField()',
    }
    return mapping.get(airtable_type, 'models.CharField(max_length=255)')


# Function to generate Django model
def generate_django_model(table):
    model_name = table['name'].replace(' ', '')
    fields = table['fields']

    model = f'class {model_name}(models.Model):\n'
    for field in fields:
        field_name = field['name'].replace(' ', '_').lower()
        field_type = map_field_type(field['type'])
        model += f'    {field_name} = {field_type}\n'

    return model


# Function to fetch data from Airtable
def fetch_airtable_data(table_name, base_id, api_key):
    url = f"{config('AIRTABLE_API_URL')}/{base_id}/{table_name}"
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['records']


# Function to populate Django database
def populate_django_db(table_name, model, base_id, api_key):
    data = fetch_airtable_data(table_name, base_id, api_key)
    ModelClass = globals()[model]
    with transaction.atomic():
        for record in data:
            fields = record['fields']
            model_instance = ModelClass()
            for field_name, value in fields.items():
                django_field_name = field_name.replace(' ', '_').lower()
                setattr(model_instance, django_field_name, value)
            model_instance.save()

def get_all_records():
    api = Api(config('PRELO_AIRTABLE_API_KEY'))
    table = api.table(config('PRELO_BASE_ID'), config('PRELO_TABLE_ID'))
    records = table.all()
    return records


def format_records(records):
    formatted_strings = []
    for record in records:
        formatted_record = ", ".join(f"{key}: {value}" for key, value in record.items())
        formatted_strings.append(formatted_record)
    return formatted_strings


def load_records_into_pinecone(records):
    pc = Pinecone(api_key=config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    metadatas = []
    ids = []
    chunks_to_save = []
    for record in records:
        formatted_record = ", ".join(f"{key}: {value}" for key, value in record['fields'].items())
        id = str(uuid.uuid4())
        metadata = {
            "airtable_id": record['id'],
            "created_at": record['createdTime'],
            "founders": record['fields'].get("Founders", ""),
            "stage": record['fields'].get("Funding Stage", ""),
            "industry": record['fields'].get("Industry", ""),
            "funding_amount": record['fields'].get("Last Funding (USD)", ""),
        }

        chunks_to_save.append(formatted_record)
        metadatas.append(metadata)
        ids.append(id)

    vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=config('PINECONE_IPRELO_NAMESPACE'))

def load_angel_investor_records_into_pinecone(records):
    pc = Pinecone(api_key=config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    metadatas = []
    ids = []
    chunks_to_save = []
    for record in records:
        formatted_record = ", ".join(f"{key}: {value}" for key, value in record['fields'].items())
        id = str(uuid.uuid4())
        metadata = {
            "airtable_id": record['id'],
            "created_at": record['createdTime'],
            "investor": record['fields'].get("Investor (VC or Angel)", ""),
            "contact_name": record['fields'].get("Contact Name", ""),
            "industry": record['fields'].get("Preferred Sectors", ""),
            "funding_stage": record['fields'].get("Preferred Investment Size", ""),
            "funding_amount": record['fields'].get("Last Funding (USD)", ""),
        }

        chunks_to_save.append(formatted_record)
        metadatas.append(metadata)
        ids.append(id)

    vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=config('PINECONE_INVESTOR_PRELO_NAMESPACE'))

def load_no_warm_intro_investor_records_into_pinecone(records):

    pc = Pinecone(api_key=config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    metadatas = []
    ids = []
    chunks_to_save = []
    for record in records:
        formatted_record = ", ".join(f"{key}: {value}" for key, value in record['fields'].items())
        id = str(uuid.uuid4())
        metadata = {
            "airtable_id": record['id'],
            "created_at": record['createdTime'],
            "investor": record['fields'].get("Investor (VC or Angel)", ""),
            "contact_name": record['fields'].get("Contact Name", ""),
            "industry": record['fields'].get("Industry", ""),
            "check_size": record['fields'].get("Check Size $", ""),
            "funding_stage": record['fields'].get("Funding Stage", ""),
            "geography": record['fields'].get("Geography", ""),
        }

        chunks_to_save.append(formatted_record)
        metadatas.append(metadata)
        ids.append(id)

    vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=config('PINECONE_INVESTOR_PRELO_NAMESPACE'))


TOOL_DESCRIPTION = "This tool allows you to get information about startups, their founders, and their fundraising efforts"


@traceable
def query_records(query, previous_results=None):
    pc = Pinecone(api_key=config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    matched = vectorstore.similarity_search_with_score(query, k=5, namespace=config('PINECONE_PRELO_NAMESPACE'))
    docs = "\n\n".join(doc[0].page_content for doc in matched)
    model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(TOOL_RESULT_PROMPT)
    chain = prompt | model | StrOutputParser()
    combined_query = f"{previous_results}\n\n{query}" if previous_results else query
    response = chain.invoke({
        "query": combined_query,
        "tool_description": TOOL_DESCRIPTION,
        "tool_output": docs
    })
    print(response)
    return response

INVESTOR_LOOKUP_PROMPT = """

Given this message, 

"""

def lookup_investors(query):
    pc = Pinecone(api_key=config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    matched = vectorstore.similarity_search_with_score(query, k=5, namespace=config('PINECONE_INVESTOR_PRELO_NAMESPACE'))
    docs = "\n\n".join(doc[0].page_content for doc in matched)
    model = ChatOpenAI(model="gpt-4o", openai_api_key=config("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_template(TOOL_RESULT_PROMPT)
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({
        "query": query,
        "tool_description": TOOL_DESCRIPTION,
        "tool_output": docs
    })
    print(response)
    return response

# records = get_all_records()
# # Using the function to format the records
# formatted_data = format_records(records)
# for data in formatted_data:
#     print(data)
