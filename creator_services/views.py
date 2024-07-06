import time

from decouple import config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride

CREATOR_DEMO_PROMPT = """
You are a powerful submind for a creator. Here's everything you know about the creator you are representing: {mind}

Respond to the user from the perspective of the creator you represent. If you don't know anything about the 
referenced topic,
just tell the user. Ask the user for more information if you need them to clarify something so you can give them 
the best possible answer.
"""

BASIC_CREATOR_DEMO_PROMPT = """
You are a powerful submind for a creator.

Respond to the user from the perspective of the creator you represent. If you don't know anything about the 
referenced topic,
just tell the user. Ask the user for more information if you need them to clarify 
something so you can give them the best possible answer.
"""

def get_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('SUBMIND_UI_MONGODB_CONNECTION_STRING'),
        session_id=f'chat_{session_id}',
        database_name=config("SUBMIND_UI_DATABASE_NAME"),
        collection_name=config("SUBMIND_UI_COLLECTION_NAME")
    )

def get_message_history_basic_gpt4o(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('SUBMIND_UI_MONGODB_CONNECTION_STRING'),
        session_id=f'basic_gpt4o_{session_id}',
        database_name=config("SUBMIND_UI_DATABASE_NAME"),
        collection_name=config("SUBMIND_UI_COLLECTION_NAME")
    )

def get_message_history_basic_claude(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('SUBMIND_UI_MONGODB_CONNECTION_STRING'),
        session_id=f'basic_claude_{session_id}',
        database_name=config("SUBMIND_UI_DATABASE_NAME"),
        collection_name=config("SUBMIND_UI_COLLECTION_NAME")
    )



# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def send_demo_message(request):
    conversation_uuid = request.data.get('uuid')
    message = request.data.get('message')
    submind_id = request.data.get('submind_id')
    submind = Submind.objects.get(id=submind_id)

    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(conversation_uuid, "interview_chat", 0.0)
    model_claude = SubmindModelFactory.get_claude(conversation_uuid, "interview_chat")
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?

    basic_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                BASIC_CREATOR_DEMO_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    custom_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                CREATOR_DEMO_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    basic_runnable_gpt4o = basic_prompt | model
    basic_runnable_claude = basic_prompt | model_claude
    custom_runnable_claude = custom_prompt | model_claude

    basic_gpt40_with_message_history = RunnableWithMessageHistory(
        basic_runnable_gpt4o,
        get_message_history_basic_gpt4o,
        input_messages_key="input",
        history_messages_key="history",
    )
    basic_claude_with_message_history = RunnableWithMessageHistory(
        basic_runnable_claude,
        get_message_history_basic_claude,
        input_messages_key="input",
        history_messages_key="history",
    )
    custom_claude_with_message_history = RunnableWithMessageHistory(
        custom_runnable_claude,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    submind_document = remember(submind)
    custom_answer = custom_claude_with_message_history.invoke(
        {
            "input": message,
            "mind": submind_document,
        },
        config={"configurable": {"session_id": f'custom_claude_{conversation_uuid}'}},

    )
    basic_gpt40_answer = basic_gpt40_with_message_history.invoke(
        {
            "input": message,
        },
        config={"configurable": {"session_id": f'basic_gpt4o_{conversation_uuid}'}},

    )
    basic_claude_answer = basic_claude_with_message_history.invoke(
        {
            "input": message,
        },
        config={"configurable": {"session_id": f'basic_claude_{conversation_uuid}'}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")

    return Response({"custom_message": custom_answer.content, "gpt4o_message": basic_gpt40_answer.content,
                     "claude_message": basic_claude_answer.content})
