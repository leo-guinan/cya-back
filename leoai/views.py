import json
import uuid

from django.shortcuts import render
from langchain.memory import ConversationBufferMemory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from leoai.agent import Agent
from leoai.models import Message, Request, Collection, Item
from leoai.tools import Tools


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
    tools.add_item_to_collection(collection.name,[text], [item.uuid], [{
        'name': item.name,
        'link': item.link,
    }])
    return Response({'response': "Added to collection."})