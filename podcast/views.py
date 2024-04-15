import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from podcast.models import PodcastQuery
from podcast.tasks import search


# Create your views here.
@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def clip(request):
    body = request.body

    print(body)
    return Response({'message': 'Hello, World!'})



@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def find_podcast_episodes(request):
    body = json.loads(request.body)
    query = body.get('query')
    if not query:
        return Response({'message': 'Query is required'}, status=400)

    podcast_query = PodcastQuery.objects.create(query=query)
    search.delay(podcast_query.id)

    print(body)
    return Response({'status': 'Queued', 'query_id': podcast_query.id})

@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_query_result(request):
    body = json.loads(request.body)
    query_id = body.get('query_id')
    if not query_id:
        return Response({'message': 'Query ID is required'}, status=400)

    query = PodcastQuery.objects.get(id=query_id)
    if (not query.completed):
        return Response({'status': 'Queued'},)

    snippets = query.snippets.all()
    print(f"Found {len(snippets)} snippets")
    results = []
    for snippet in snippets:
        results.append({
            'snippet': snippet.snippet,
            'score': snippet.score
        })
    return Response({'query': query.query, 'results': results, 'status': 'Completed'})

