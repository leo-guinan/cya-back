import os
import uuid

import boto3
import pandas as pd
import pinecone
from decouple import config
from langchain.agents import create_csv_agent
from langchain.agents.agent_types import AgentType
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.retrievers import SelfQueryRetriever
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import Pinecone

from experiments.models import UploadedFile, ExperimentResponse


# initialize pinecone


def version_one(file_path, experiment_message):
    message = experiment_message.message
    xls = pd.ExcelFile(file_path)
    # Loop over each sheet
    for sheet in xls.sheet_names:
        # Read the sheet to pandas dataframe
        df = pd.read_excel(xls, sheet)

        # Write the dataframe to csv
        csv_file_name = f"{sheet}.csv"
        df.to_csv(csv_file_name, index=False)
        print(f"{csv_file_name} has been created.")

    # Get all the csv files in the directory
    csv_files = [f for f in os.listdir(os.curdir) if f.endswith('.csv')]
    responses = []
    for csv_file in csv_files:

        agent = create_csv_agent(
            OpenAI(temperature=0, openai_api_key=config("SECONDARY_OPENAI_API_KEY")),
            csv_file,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        )
        response = agent.run(message)
        responses.append(response)
        os.remove(csv_file)
    response = "\n".join(responses)

    experiment_response = ExperimentResponse(uploaded_file=experiment_message.uploaded_file, response=response, variant="version_one", message=experiment_message)
    experiment_response.save()
    return response

def version_two(experiment_message):
    message = experiment_message.message
    embeddings = OpenAIEmbeddings(openai_api_key=config("SECONDARY_OPENAI_API_KEY"))

    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))

    vectorstore = Pinecone(index,
                           embeddings.embed_query,
                           "text",
                           namespace="excel-experiment")
    retriever = vectorstore.as_retriever()
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI(openai_api_key=config("SECONDARY_OPENAI_API_KEY"), model_name="gpt-4-32k")
    chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
    )
    response = chain.invoke(message)
    experiment_response = ExperimentResponse(uploaded_file=experiment_message.uploaded_file, response=response, variant="version_two", message=experiment_message)
    experiment_response.save()
    return response


def version_three(experiment_message, s3_bucket, s3_key):
    message = experiment_message.message
    embeddings = OpenAIEmbeddings(openai_api_key=config("SECONDARY_OPENAI_API_KEY"))
    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))

    vectorstore = Pinecone(index,
                           embeddings.embed_query,
                           "text",
                           namespace="excel-experiment")
    metadata_field_info = [
        AttributeInfo(
            name="s3_bucket",
            description="The s3 bucket where the file is stored",
            type="string or list[string]",
        ),
        AttributeInfo(
            name="s3_key",
            description="The s3 key where the file is stored",
            type="integer",
        ),
        AttributeInfo(
            name="description",
            description="What this file contains",
            type="string",
        ),

    ]
    document_content_description = "a spreadsheet containing financial data for an account"
    llm = OpenAI(temperature=0, openai_api_key=config("SECONDARY_OPENAI_API_KEY"))
    retriever = SelfQueryRetriever.from_llm(
        llm, vectorstore, document_content_description, metadata_field_info, verbose=True
    )
    template = f"""Answer the question based only on the following context:
        {{context}}
        
        The location of the file is: {s3_bucket}/{s3_key}

        Question: {{question}}
        """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI(openai_api_key=config("SECONDARY_OPENAI_API_KEY"), model_name="gpt-4-32k")
    chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
    )
    response = chain.invoke(message)
    experiment_response = ExperimentResponse(uploaded_file=experiment_message.uploaded_file, response=response, variant="version_three", message=experiment_message)
    experiment_response.save()
    return response


def load_xlsx_to_pinecone(s3_bucket, s3_key):
    embeddings = OpenAIEmbeddings(openai_api_key=config("SECONDARY_OPENAI_API_KEY"))

    # download file from s3 bucket
    s3 = boto3.client('s3')
    with open('data.xlsx', 'wb') as f:
        s3.download_fileobj(s3_bucket, s3_key, f)
    loader = UnstructuredExcelLoader('data.xlsx', mode="elements")
    docs = loader.load_and_split()
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )

    index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))


    vectorstore = Pinecone(index,
                           embeddings.embed_query,
                           "text",
                           namespace="excel-experiment")
    texts = []
    metadatas = []
    ids = []
    for doc in docs:
        texts.append(doc.page_content)
        metadatas.append({
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        })
        ids.append(str(uuid.uuid4()))

    vectorstore.add_texts(texts, metadatas=metadatas, ids=ids, namespace="excel-experiment")
    os.remove('data.xlsx')


def s3_upload(file):
    s3_client = boto3.client('s3',
                             aws_access_key_id=config('AWS_ACCESS_KEY'),
                             aws_secret_access_key=config('AWS_SECRET_KEY')
                             )

    try:
        s3_client.upload_fileobj(file, config('EXPERIMENT_AWS_BUCKET_NAME'), file.name)
        print("File uploaded successfully")
        uploaded = UploadedFile(bucket=config('EXPERIMENT_AWS_BUCKET_NAME'), key=file.name)
        uploaded.save()
        print("file saved to db")
        load_xlsx_to_pinecone(config('EXPERIMENT_AWS_BUCKET_NAME'), file.name)
        print("file loaded to pinecone")
        return True
    except Exception as e:
        print(e)
        return False

def s3_download(file):
    s3_client = boto3.client('s3',
                             aws_access_key_id=config('AWS_ACCESS_KEY'),
                             aws_secret_access_key=config('AWS_SECRET_KEY')
                             )


    try:
        s3_client.download_file(config('EXPERIMENT_AWS_BUCKET_NAME'), file, file)
        return True
    except Exception as e:
        print(e)
        return False