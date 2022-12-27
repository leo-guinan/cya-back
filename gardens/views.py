import json
import logging

from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount
from gardens.models import ContentFeed, ContentSource, Content
from gardens.serializers import ContentFeedSerializer, ContentSerializer
from gardens.tasks import fetch_content_for_feed
logger = logging.getLogger(__name__)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add_feed(request):
    body = json.loads(request.body)
    feed_url = body['feed_url']
    client_account_id = body['client_account_id']
    # Need to think about this. The content type actually lives on the content, not the parent feed.
    # type = body['type']
    # content_type = None
    # if (type == 'YOUTUBE'):
    #     content_type = Content.ContentType.YOUTUBE
    # elif (type == 'PODCAST'):
    #     content_type = Content.ContentType.PODCAST
    # elif (type == 'VIDEO'):
    #     content_type = Content.ContentType.VIDEO
    # elif (type == 'BLOG'):
    #     content_type = Content.ContentType.BLOG
    # else:
    #     content_type = Content.ContentType.BLOG
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    feed = ContentFeed()
    source = ContentSource()
    source.feed_location = feed_url
    source.save()
    feed.source = source
    feed.owner = client_account
    feed.save()

    #get content for feed url
    logger.debug("fetching content for feed")
    fetch_content_for_feed.delay(feed_id=feed.id)
    return Response({"content_feed_id": feed.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_feeds(request):
    body = json.loads(request.body)
    feed_ids = body['feed_ids']
    logger.debug(feed_ids)
    feeds = ContentFeed.objects.filter(id__in=feed_ids).all()
    logger.debug(len(feeds))
    results = []
    for feed in feeds:
        serializer = ContentFeedSerializer(feed)
        results.append(serializer.data)
        logger.debug(serializer.data)
    return Response({"feeds": results})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_content_for_feed(request):
    body = json.loads(request.body)
    feed_id = body['feed_id']
    feed = ContentFeed.objects.filter(id=feed_id).first()
    content = Content.objects.filter(feed=feed).all()
    results = []
    for c in content:
        serializer = ContentSerializer(c)
        results.append(serializer.data)
    return Response({"content": results})