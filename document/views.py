import datetime
import json

from decouple import config
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from document.service import generate_document_from_prompt


# Create your views here.


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def generate_document(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    prompt = body['prompt']
    uuid = body['uuid']

    content = generate_document_from_prompt(prompt, uuid)
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.myaicofounder
    new_doc = {
        "userId": user_id,
        "content": content,
        "uuid": uuid,
        "createdAt": datetime.datetime.now()
    }

    db.documents.insert_one(new_doc)
    return Response({'status': 'success', 'uuid': uuid, 'content': content})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def get_document(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    uuid = body['uuid']
    print("user_id: ", user_id)
    print("uuid: ", uuid)
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.myaicofounder
    document = db.documents.find_one({"uuid": uuid, "userId": user_id})
    print(document)
    if not document:
        return Response({'status': 'error', 'message': 'Document not found'})
    return Response({'status': 'success', 'uuid': uuid, 'content': document['content']})


