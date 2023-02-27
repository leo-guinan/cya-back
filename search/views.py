import json

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClient
from client.models import Client, ClientAccount, AccountConfig
from effortless_reach.models import Podcast, PodcastEpisode
from effortless_reach.serializers import PodcastSerializer, PodcastEpisodeSerializer, SummarySerializer, \
    KeyPointSerializer
from search.models import Curator
from search.service import search, curated


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
@csrf_exempt
def search_content(request):

    body = json.loads(request.body)
    search_term = body['search_term']
    title, link, description, chunk = search(search_term)
    result = {
        'title': title,
        'link': link,
        'description': description,
        'chunk': chunk,
    }
    return Response(result)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
@csrf_exempt
def search_curated_content(request):

    body = json.loads(request.body)
    curator_id = body['curator_id']
    curator = Curator.objects.filter(id=curator_id).first()
    if not curator:
        return Response({'error': 'Curator not found'})
    search_term = body['search_term']
    title, link, description, chunk = curated(search_term, curator)
    result = {
        'title': title,
        'link': link,
        'description': description,
        'chunk': chunk,
    }
    return Response(result)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def create_curator(request):
    body = json.loads(request.body)
    email = body['email']
    client = Client.objects.filter(name='SEARCH').first()
    if not client:
        raise UnknownClient()
    client_account = ClientAccount.objects.filter(email=email, client=client).first()
    if not client_account:
        client_account = ClientAccount()
        client_account.client = client
        client_account.save()
        account_config = AccountConfig()
        account_config.notification_preference = AccountConfig.NotificationPreference.TWEET
        account_config.client_account = client_account
        account_config.save()
        client_account.config = account_config
    client_account.email = email
    client_account.refreshed = timezone.now()
    client_account.save()
    if not client_account.get_curator():
        curator = Curator()
        curator.client_account = client_account
        curator.save()
    else:
        curator = client_account.curation
    return Response({"client_account_id": client_account.id, "curator_id": curator.id})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def browse_podcasts(request):
    body = json.loads(request.body)
    curator_id = body['curator_id']
    podcasts = Podcast.objects.all()
    results = []
    for podcast in podcasts:
        serializer = PodcastSerializer(podcast)
        extended_podcast = serializer.data
        extended_podcast['curated'] = podcast.curators.filter(id=curator_id).exists()
        results.append(extended_podcast)

    return Response({"podcasts": results})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def curated_podcasts(request):
    body = json.loads(request.body)
    curator_id = body['curator_id']
    podcasts = Podcast.objects.filter(curators__id=curator_id)
    results = []
    for podcast in podcasts:
        serializer = PodcastSerializer(podcast)
        extended_podcast = serializer.data
        extended_podcast['curated'] = podcast.curators.filter(id=curator_id).exists()
        results.append(extended_podcast)

    return Response({"podcasts": results})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def curate_podcast(request):
    body = json.loads(request.body)
    curator_id = body['curator_id']
    podcast_id = body['podcast_id']
    curator = Curator.objects.filter(id=curator_id).first()
    if not curator:
        return Response({'error': 'Curator not found'})
    podcast = Podcast.objects.filter(id=podcast_id).first()
    if not podcast:
        return Response({'error': 'Podcast not found'})
    podcast.curators.add(curator)

    return Response({"status": "success"})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def uncurate_podcast(request):
    body = json.loads(request.body)
    curator_id = body['curator_id']
    podcast_id = body['podcast_id']
    curator = Curator.objects.filter(id=curator_id).first()
    if not curator:
        return Response({'error': 'Curator not found'})
    podcast = Podcast.objects.filter(id=podcast_id).first()
    if not podcast:
        return Response({'error': 'Podcast not found'})
    if podcast.curators.filter(id=curator_id).exists():
        podcast.curators.remove(curator)
    return Response({"status": "success"})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def browse_episodes(request):
    body = json.loads(request.body)
    podcast_id = body['podcast_id']
    podcast = Podcast.objects.filter(id=podcast_id).first()
    if not podcast:
        return Response({'error': 'Podcast not found'})
    results = []
    for episode in podcast.episodes.all():
        serializer = PodcastEpisodeSerializer(episode)
        results.append(serializer.data)
    return Response({"episodes": results})

