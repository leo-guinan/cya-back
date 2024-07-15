import json
import time
import uuid

from decouple import config
from django.views.decorators.csrf import csrf_exempt
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from leoai.agent import Agent
from leoai.content import find_content_for_query
from leoai.models import Message, Request, Collection, Item, Facts, FactItem
from leoai.prompts import LEOAI_SYSTEM_PROMPT
from leoai.serializers import CollectionSerializer, FactsSerializer
from leoai.tasks import transcribe_youtube_video
from leoai.tools import Tools
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


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    message = body['message']
    history = body.get('history', [])
    memory = ConversationBufferMemory()
    saved_message = Message()
    saved_message.message = message

    if history:
        saved_message.history = json.dumps(history)
        for item in history:
            memory.save_context({'input': item['user']}, {'output': item['bot']})
    saved_message.save()
    agent = Agent()
    response = agent.run(message, memory=memory)
    try:
        email = json.loads(response)['email_address']
        if (email):
            request = Request()
            request.message = saved_message
            request.email = email
            request.save()
            return Response({'response': "Thank you. Leo will be in touch soon."})
    except Exception as e:
        print(e)
        return Response({'response': response})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
@csrf_exempt
def add_to_collection(request):
    body = json.loads(request.body)
    collection = body['collection']
    collection = Collection.objects.filter(name=collection).first()
    if not collection:
        collection = Collection()
        collection.name = body['collection']
        collection.save()
    item = Item()
    item.collection = collection
    item.name = body['item']
    item.link = body['link']
    item.description = body['description']
    item.recommendation = body['recommendation']
    item.uuid = uuid.uuid4()
    item.save()
    tools = Tools()
    text = item.recommendation + "\n\n" + item.description + "\n\n" + item.link
    tools.add_item_to_collection(collection.name, [text], [str(item.uuid)], [{
        'name': item.name,
        'link': item.link,
    }])
    return Response({'status': "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add_fact(request):
    body = json.loads(request.body)
    facts = body['facts']
    facts = Facts.objects.filter(name=facts).first()
    if not facts:
        facts = Facts()
        facts.name = body['facts']
        facts.save()
    item = FactItem()
    item.fact = facts
    item.question = body['question']
    item.answer = body['answer']
    item.uuid = uuid.uuid4()
    item.save()
    tools = Tools()
    text = item.question + "\n\n" + item.answer
    tools.add_item_to_collection(facts.name, [text], [str(item.uuid)], [{
        'question': item.question,
        'answer': item.answer,
    }])
    return Response({'status': "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_collection(request):
    body = json.loads(request.body)
    collection = body['collection']
    collection = Collection.objects.filter(name=collection).first()
    if not collection:
        return Response({'response': "Collection not found."})
    collectionSerializer = CollectionSerializer(collection)
    response = collectionSerializer.data
    return Response({'response': response})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_facts(request):
    body = json.loads(request.body)
    facts = body['facts']
    facts = Facts.objects.filter(name=facts).first()
    if not facts:
        return Response({'response': "Facts not found."})
    factSerializer = FactsSerializer(facts)
    response = factSerializer.data
    return Response({'response': response})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def youtube_to_notion(request):
    body = json.loads(request.body)
    video_url = body['video_url']
    page = body['page']
    transcribe_youtube_video.delay(video_url, page)
    return Response({'status': "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def thread_webhook(request):
    pass

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def blog_webhook(request):
    body = json.loads(request.body)
    output = body['output']
    final_output = output['output']


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def chat(request):
    conversation_uuid = request.data.get('uuid')
    message = request.data.get('message')
    submind = Submind.objects.get(id=config("LEOAI_SUBMIND_ID"))

    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model_claude = SubmindModelFactory.get_claude(conversation_uuid, "leoai_chat")
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?
    answer, content = find_content_for_query(message)

    custom_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                LEOAI_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    custom_runnable_claude = custom_prompt | model_claude


    custom_claude_with_message_history = RunnableWithMessageHistory(
        custom_runnable_claude,
        get_leoai_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    submind_document = remember(submind)
    custom_answer = custom_claude_with_message_history.invoke(
        {
            "input": message,
            "submind": submind_document,
            "answer": answer
        },
        config={"configurable": {"session_id": f'custom_claude_{conversation_uuid}'}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    return Response({"message": custom_answer.content, "content": content})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def content_lookup(request):
    conversation_uuid = request.data.get('uuid')
    message = request.data.get('message')
    submind = Submind.objects.get(id=config("LEOAI_SUBMIND_ID"))

    start_time = time.perf_counter()
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model_claude = SubmindModelFactory.get_claude(conversation_uuid, "leoai_chat")
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?


    custom_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                LEOAI_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    custom_runnable_claude = custom_prompt | model_claude


    custom_claude_with_message_history = RunnableWithMessageHistory(
        custom_runnable_claude,
        get_leoai_message_history,
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
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    return Response({"message": custom_answer.content})
