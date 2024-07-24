import json
import time
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

from decouple import config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from leoai.content import find_content_for_query, find_ev_content
from leoai.prompts import LEOAI_SYSTEM_PROMPT, LEOAI_CHOOSE_PATH_PROMPT, LEOAI_CONTACT_PROMPT, functions, \
    EV_SYSTEM_PROMPT
from leoai.tools.contact_info import get_contact_info_for_leo
from leoai.tools.linkedin import write_linkedin_posts
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride


def get_leoai_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("LEOAI_DATABASE_NAME"),
        collection_name=config("LEOAI_COLLECTION_NAME")
    )


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def chat(request):
    conversation_uuid = request.data.get('uuid')
    message = request.data.get('message')
    submind = Submind.objects.get(id=config("LEOAI_SUBMIND_ID"))
    model = SubmindModelFactory.get_model(conversation_uuid, "leoai_chat")
    # chat_model = SubmindModelFactory.get_mini(conversation_uuid, "leoai_chat")
    chat_model = SubmindModelFactory.get_ollama(conversation_uuid, "leoai_chat")
    start_time = time.perf_counter()

    choose_path_prompt = ChatPromptTemplate.from_template(LEOAI_CHOOSE_PATH_PROMPT)

    path = choose_path_prompt | model.bind(function_call={"name": "choose_path"},
                                           functions=functions) | JsonOutputFunctionsParser()

    tools_available = """
        Id: 1, Name: Info about Leo, Description: Get information about Leo Guinan
        
        """

    path_response = path.invoke({
        "message": message,
        "tools": tools_available
    })

    chat_history = get_leoai_message_history(conversation_uuid)
    submind_document = remember(submind)

    if path_response['use_tool']:
        if path_response['tool_id'] == '1':
            contact_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        LEOAI_CONTACT_PROMPT
                    ),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}"),
                ]
            )

            chat_runnable = contact_prompt | model

            chat_with_message_history = RunnableWithMessageHistory(
                chat_runnable,
                get_leoai_message_history,
                input_messages_key="input",
                history_messages_key="history",
            )

            answer = chat_with_message_history.invoke(
                {
                    "input": message,
                    "submind": submind_document,
                    "contact_info": json.dumps(get_contact_info_for_leo())
                },
                config={"configurable": {"session_id": f'leoai_{conversation_uuid}'}},
            )

            end_time = time.perf_counter()
            print(f"Chat with lookup took {end_time - start_time} seconds")

            return Response({"message": answer.content, })

    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?
    context, content = find_content_for_query(message)
    print(f"Answer: {context}")

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                LEOAI_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chat_runnable = chat_prompt | chat_model

    chat_with_message_history = RunnableWithMessageHistory(
        chat_runnable,
        get_leoai_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    answer = chat_with_message_history.invoke(
        {
            "input": message,
            "submind": submind_document,
            "context": context
        },
        config={"configurable": {"session_id": f'leoai_{conversation_uuid}'}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    return Response({"message": answer.content, "content": content})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def chat_ev(request):
    conversation_uuid = request.data.get('uuid')
    message = request.data.get('message')
    submind = Submind.objects.get(id=config("EV_SUBMIND_ID"))
    model = SubmindModelFactory.get_model(conversation_uuid, "evai_chat")
    submind_document = remember(submind)
    start_time = time.perf_counter()

    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?
    context, content = find_ev_content(message)

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                EV_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chat_runnable = chat_prompt | model

    chat_with_message_history = RunnableWithMessageHistory(
        chat_runnable,
        get_leoai_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    answer = chat_with_message_history.invoke(
        {
            "input": message,
            "submind": submind_document,
            "context": context
        },
        config={"configurable": {"session_id": f'evyoutube{conversation_uuid}'}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    return Response({"message": answer.content, "content": content})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def write_linkedin_post(request):

    query = request.data.get('query')
    posts = write_linkedin_posts(query)

    return Response({"posts": posts})

