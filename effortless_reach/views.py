import json

from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework_api_key.permissions import HasAPIKey

from effortless_reach.models import RssFeed
from rss.service import parse_feed


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def parse_rss_feed(request):
    body = json.loads(request.body)
    url = body['url']
    existing_feed = RssFeed.objects.filter(url=url).first()
    if not existing_feed:
        feed = RssFeed(url=url)
        feed.save()
    entries = parse_feed(url)