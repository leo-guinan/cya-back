import json

from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey

from client.models import Client


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def new_client(request):
    body = json.loads(request.body)
    name = body.get('name', None)
    email = body.get('email', None)
    if name is None or email is None:
        return Response({'message': 'Missing required fields'}, status=400)
    api_key, key = APIKey.objects.create_key(name=name)
    Client.objects.create(name=name, email=email, api_key=api_key)
    return Response({'api_key': key, })