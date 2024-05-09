import uuid

from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable
from pinecone import Pinecone
from pyairtable import Api

from submind.prompts.prompts import TOOL_RESULT_PROMPT


def get_fundraises():
    pass


def get_industry():
    pass


# can we turn a plaintext query into a structured airtable query? Maybe for now, just create a fulltext field and dump in pinecone?
schema = {

}


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

    vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=config('PINECONE_PRELO_NAMESPACE'))


TOOL_DESCRIPTION = "This tool allows you to get information about startups, their founders, and their fundraising efforts"


@traceable
def query_records(query, data_to_send, previous_results=None):
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

# records = get_all_records()
# # Using the function to format the records
# formatted_data = format_records(records)
# for data in formatted_data:
#     print(data)
