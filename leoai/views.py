import json

from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from leoai.agent import Agent


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    search_term = body['search_term']
    agent = Agent()
    results = agent.run(search_term)
    return Response({'results': results})
