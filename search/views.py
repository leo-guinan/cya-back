import json

from decouple import config
from django.shortcuts import render
from rest_framework.decorators import permission_classes, api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.llms.openai import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain.utilities import BingSearchAPIWrapper

from search.add import add_recommended_link
from users.models import User


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    query = body['query']


    search = BingSearchAPIWrapper(bing_subscription_key=config('BING_SUBSCRIPTION_KEY'), bing_search_url=config('BING_SEARCH_URL'))
    results = search.results(query, 5)

    return Response({'response': results})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add(request):
    body = json.loads(request.body)
    url = body['url']
    title = body['title']
    user_id = body['user_id']
    user = User.objects.filter(id=user_id).first()
    if user is None:
        return Response({'status': 'failure'})
    recommendation = body['recommendation']
    add_recommended_link(url, title, user, recommendation, None)
    return Response({'response': 'success'})