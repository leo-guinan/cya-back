import json
import time

from decouple import config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride
from submind.prompts.prompts import SUBMIND_CHAT_PROMPT


def get_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("SCORE_MY_DECK_DATABASE_NAME"),
        collection_name=config("SCORE_MY_DECK_COLLECTION_NAME")
    )


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_message(request, submind_id):
    body = json.loads(request.body)
    print(f"Received message for {submind_id}: ", body['message'])
    conversation_uuid = body["uuid"]
    message = body["message"]
    submind = Submind.objects.get(id=submind_id)
    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(conversation_uuid, "chat", 0.5)
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?


    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SUBMIND_CHAT_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model

    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    submind_document = remember(submind)
    answer = with_message_history.invoke(
        {
            "input": message,
            "mind": submind_document,
            "description": submind.description,
        },
        config={"configurable": {"session_id": conversation_uuid}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")

    print(answer.content)

    return Response({"message": answer.content})
