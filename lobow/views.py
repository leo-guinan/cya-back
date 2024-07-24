import json
import time
import uuid

from decouple import config
from django.shortcuts import render
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from lobow.content import get_content_from_youtube
from lobow.prompts import LOBOW_SYSTEM_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride


def get_lobow_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("LOBOW_DATABASE_NAME"),
        collection_name=config("LOBOW_COLLECTION_NAME")
    )

# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def chat(request):
    body = json.loads(request.body)
    message = body.get('message')
    conversation_uuid = str(uuid.uuid4())
    context = get_content_from_youtube(message)

    answer_context = context[0]['text']
    print(f"Received message: {message}")
    print(f"Using context: {answer_context}")

    chat_model = SubmindModelFactory.get_mini(conversation_uuid, "lobow_chat")

    start_time = time.perf_counter()

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                LOBOW_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chat_runnable = chat_prompt | chat_model

    chat_with_message_history = RunnableWithMessageHistory(
        chat_runnable,
        get_lobow_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    answer = chat_with_message_history.invoke(
        {
            "input": message,
            "context": answer_context,
        },
        config={"configurable": {"session_id": f'leoai_{conversation_uuid}'}},

    )
    print(f"Answer: {answer.content}")
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    return Response({"context": answer.content,
                     "type": "youtube",
                     "url": f"https://www.youtube.com/watch?v={context[0]['metadata']['videoId']}"
                     })

