import os

from decouple import config
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain.agents import create_csv_agent
import boto3
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import pinecone
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import Pinecone


# initialize pinecone


def version_one(message):
    agent = create_csv_agent(
        OpenAI(temperature=0, openai_api_key=config("OPENAI_API_KEY")),
        "FinancialSample.csv",
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    )
    response = agent.run(message)
    return response


def version_two(message):
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pinecone.Index("langchain-demo")
    vectorstore = Pinecone(index, embeddings.embed_query, "text")
    retriever = vectorstore.as_retriever()
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI()
    chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
    )
    return chain.invoke(message)


def version_three(message):
    return "version 3"

def load_xlsx_to_pinecone(s3_bucket, s3_key, index_name):
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    # download file from s3 bucket
    # s3 = boto3.client('s3')
    # with open('data.xlsx', 'wb') as f:
    #     s3.download_fileobj(s3_bucket, s3_key, f)
    loader = UnstructuredExcelLoader('Financial Sample.xlsx', mode="elements")
    docs = loader.load_and_split()
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )

    index_name = "excel-index"

    # First, check if our index already exists. If it doesn't, we create it
    if index_name not in pinecone.list_indexes():
        # we create a new index
        pinecone.create_index(
            name=index_name,
            metric='cosine',
            dimension=1536
        )
    # The OpenAI embedding model `text-embedding-ada-002 uses 1536 dimensions`
    Pinecone.from_documents(docs, embeddings, index_name=index_name)

