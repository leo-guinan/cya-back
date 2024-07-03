import json
import uuid

from decouple import config
from django.shortcuts import render
from google.oauth2.credentials import Credentials
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from toolkit.tasks import youtube_to_blog, idea_collider, fetch_google_docs_data


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def video_to_blog(request):
    body = json.loads(request.body)
    youtube_url = body['youtube_url']
    audience = body['audience']
    result_uuid = str(uuid.uuid4())

    youtube_to_blog.delay(youtube_url, audience, result_uuid)
    return Response({'message': 'success', 'result_uuid': result_uuid})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def idea_collider(request):
    body = json.loads(request.body)
    video_url = body['youtube_url']
    other_youtube_video_url = body['other_youtube_url']
    intersection = body['intersection']
    audience = body['audience']
    result_uuid = str(uuid.uuid4())

    idea_collider.delay(video_url, other_youtube_video_url, intersection, audience, result_uuid)
    return Response({'message': 'success', 'result_uuid': result_uuid})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def blog_result(request, result_uuid):
    return Response({'message': 'success'})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def collider_result(request, result_uuid):
    return Response({'message': 'success'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def sync_google_docs(request):
    body = json.loads(request.body)
    tokens = body['tokens']
    user_id = body['user_id']


    print(tokens)

    fetch_google_docs_data.delay(tokens, user_id)


    return Response({'message': 'success'})


