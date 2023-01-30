import json

from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount, Client
from effortless_reach.models import RssFeed, Podcast
from effortless_reach.serializers import PodcastSerializer
from effortless_reach.tasks import process_rss_feed


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def parse_rss_feed(request):
    body = json.loads(request.body)
    url = body['url']
    email = body['email']
    client = Client.objects.filter(name="EffortlessReach").first()
    client_account = ClientAccount.objects.filter(email=email, client=client).first()
    if not client_account:
        client_account = ClientAccount.objects.create(email=email, client=client)

    existing_feed = RssFeed.objects.filter(url=url).first()
    if not existing_feed:
        existing_feed = RssFeed(url=url, owner=client_account)
        existing_feed.save()
    process_rss_feed.delay(existing_feed.id)
    return Response({"feed_id": existing_feed.id, "client_account_id": client_account.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_podcast_episodes(request):
    body = json.loads(request.body)
    feed_id = body['feed_id']
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        return Response({'error': 'client account not found'})
    rss_feed = RssFeed.objects.filter(id=feed_id).first()
    if not rss_feed:
        return Response({'error': 'rss feed not found'})
    podcast = rss_feed.podcast
    if podcast.rss_feed.owner != client_account:
        return Response({'error': 'client account does not own podcast'})
    serializer = PodcastSerializer(podcast)
    return Response(serializer.data)
