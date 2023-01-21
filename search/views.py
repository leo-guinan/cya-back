import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from search.service import search


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
@csrf_exempt
def search_creator_content(request):

    body = json.loads(request.body)
    search_term = body['search_term']
    creator = body['creator']
    title, link, description, chunk = search(search_term, creator)
    result = {
        'title': title,
        'link': link,
        'description': description,
        'chunk': chunk
    }
    return Response(result)
