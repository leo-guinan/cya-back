import json
from datetime import datetime
from operator import itemgetter
from uuid import uuid4

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import format_document
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import get_buffer_string
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone as PineconeLC
from pinecone import Pinecone

from backend.celery import app
from cli.command.classify import classify_command
from cli.command.transform import schema_to_body
from cli.models import Command
from cli.service import get_state_for_session


@app.task(name="cli.tasks.run_command")
def run_command(command, session_id):
    current_state = get_state_for_session(session_id)
    answer = classify_command(command)
    if answer == "statement":
        save_info.delay(command, current_state.state, session_id)
    elif answer == "question":
        answer_question.delay(command, current_state.state, session_id)
    elif answer == "command":
        perform_command.delay(command, current_state.state, session_id)
    else:
        print(f'Answer: {answer}')


@app.task(name="cli.tasks.save_info")
def save_info(message, current_state, session_id):
    pc = Pinecone(config("PINECONE_API_KEY"))
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli")

    texts = []
    ids = []
    metadatas = []

    texts.append(message)
    ids.append(str(uuid4()))
    metadatas.append({"source": "cli", "date": datetime.now().isoformat()})
    cli_index.add_texts(texts, metadatas, ids)
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(session_id,
                                            {"type": "chat.message", "message": f'I know {message}', "id": "response"})


@app.task(name="cli.tasks.answer_question")
def answer_question(question, current_state, session_id):
    pc = Pinecone(config("PINECONE_API_KEY"))

    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))

    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli")

    retriever = cli_index.as_retriever()

    _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
    DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

    def _combine_documents(
            docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
    ):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)

    model = ChatOpenAI(api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
    _inputs = RunnableParallel(
        standalone_question=RunnablePassthrough.assign(
            chat_history=lambda x: get_buffer_string(x["chat_history"])
        )
                            | CONDENSE_QUESTION_PROMPT
                            | ChatOpenAI(temperature=0, api_key=config("OPENAI_API_KEY"), model_name="gpt-4-turbo")
                            | StrOutputParser(),
    )
    _context = {
        "context": itemgetter("standalone_question") | retriever | _combine_documents,
        "question": lambda x: x["standalone_question"],
    }
    conversational_qa_chain = _inputs | _context | ANSWER_PROMPT | ChatOpenAI(api_key=config("OPENAI_API_KEY"),
                                                                              model_name="gpt-4-turbo")
    answer = conversational_qa_chain.invoke(
        {
            "question": question,
            "chat_history": [],
        }
    )

    print(answer)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(session_id,
                                            {"type": "chat.message", "message": answer.content, "id": "state"})


@app.task(name="cli.tasks.perform_command")
def perform_command(command, current_state, session_id):
    # pick best fitting command, if over a certain threshold.
    # turn command into an embedding
    # compare embedding to all commands
    # if over threshold, run command
    channel_layer = get_channel_layer()

    pc = Pinecone(config("PINECONE_API_KEY"))

    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli_commands")
    # cli_index.delete(delete_all=True)
    # add_command("add_command", "Add a command to the knowledge base", "http://localhost:8000/api/cli/add_command",
    #             "(command, description, url, input, output)", "Command added")
    retriever = cli_index.as_retriever()
    query = command
    results = retriever.get_relevant_documents(query)
    if len(results) == 0:
        async_to_sync(channel_layer.group_send)(session_id,
                                                {"type": "chat.message",
                                                 "message": f'Command not found', "id": "state"})
        return
    retrieved = Command.objects.get(uuid=results[0].metadata['uuid'])
    req_url = retrieved.url if retrieved.url.endswith("/") else retrieved.url + "/"
    print(req_url)
    body = schema_to_body(command, retrieved.input_schema, session_id)
    parsed_body = json.loads(body)
    print(parsed_body)
    answer = requests.post(req_url, json=parsed_body)
    print(answer)
    # async_to_sync(channel_layer.group_send)(session_id,
    #                                         {"type": "chat.message", "message": f'Successfully executed command: {command}', "id": "state"})


@app.task(name="cli.tasks.add_command")
def add_command(command, description, url, input, output):
    print(f"adding command {command}")
    pc = Pinecone(config("PINECONE_API_KEY"))

    command_object = Command(command=command, description=description, url=url, input_schema=input,
                             output_schema=output, uuid=str(uuid4()))
    command_object.save()
    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"))
    cli_index = PineconeLC(index, embeddings, "text", namespace="cli_commands")
    retriever = cli_index.as_retriever()
    texts = []
    ids = []
    metadatas = []

    texts.append(f"""
    Command:
    {command}
    
    Description:
    {description}
    
    URL:
    {url}
    
    Input Schema:
    {input}
    
    Output Schema:
    {output}
    """)
    ids.append(command_object.uuid)
    metadatas.append({"source": "cli", "date": datetime.now().isoformat(), "uuid": command_object.uuid})
    cli_index.add_texts(texts, metadatas, ids)
