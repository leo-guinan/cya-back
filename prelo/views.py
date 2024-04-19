import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


# Create your views here.
@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def ask(request):
    body = json.loads(request.body)
    print(body)
    return Response({'message': 'Hello, World!'})

@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def details(request):
    body = json.loads(request.body)
    print(body)
    return Response({'message': 'Hello, World!'})