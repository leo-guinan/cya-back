import boto3
import pinecone
from decouple import config
from langchain.agents import create_csv_agent
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import Pinecone

from experiments.models import UploadedFile


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


def s3_upload(file):
    s3_client = boto3.client('s3',
                             aws_access_key_id=config('AWS_ACCESS_KEY'),
                             aws_secret_access_key=config('AWS_SECRET_KEY')
                             )

    try:
        s3_client.upload_fileobj(file, config('EXPERIMENT_AWS_BUCKET_NAME'), file.name)
        uploaded = UploadedFile(bucket=config('EXPERIMENT_AWS_BUCKET_NAME'), key=file.name)
        uploaded.save()
        return True
    except Exception as e:
        print(e)
        return False
