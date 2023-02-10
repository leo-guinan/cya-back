import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from pytz import utc
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClientAccount, UnknownClient
from client.models import ClientAccount, Client, AccountConfig
from client.serializers import ClientAccountSerializer
from effortless_reach.models import RssFeed
from effortless_reach.tasks import process_rss_feed
from twitter.models import Relationship, TwitterAccount
from unfollow.models import AccountCheck
from unfollow.tasks import lookup_twitter_user
logger = logging.getLogger(__name__)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def lookup_client_account(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    # Number of accounts following
    # Number of accounts followed
    # Number of outstanding account lookup requests
    # Number of dormant accounts followed
    current_user = client_account.twitter_account
    following = Relationship.objects.filter(this_account=current_user).all()
    followers = Relationship.objects.filter(follows_this_account=current_user).all()
    following_count = len(following)
    follower_count = len(followers)
    dormant_count = 0
    date_to_compare_against = utc.localize(datetime.now() - timedelta(days=90))
    for relationship in following:
        if relationship and relationship.follows_this_account.last_tweet_date:
            if relationship.follows_this_account.last_tweet_date < date_to_compare_against:
                dormant_count += 1
    followers_to_analyze = client_account.accounts_to_analyze.filter(status__in=[AccountCheck.CheckStatus.REQUESTED, AccountCheck.CheckStatus.IN_PROGRESS]).count()
    result = {
        "following_count": following_count,
        "follower_count": follower_count,
        "dormant_count": dormant_count,
        "followers_to_analyze": followers_to_analyze,
        "last_analyzed": current_user.last_checked,
        "twitter_username": current_user.twitter_username,
        "twitter_name": current_user.twitter_name
    }
    return Response(result)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def refresh_client_account(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    lookup_twitter_user.delay(client_account_id=client_account_id, force=True)
    return Response({"success": True})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def create_client_account(request):
    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    client_name = body['client_name']
    email = body['email']
    access_key = body['access_key']
    secret_access_key = body['secret_access_key']
    client = Client.objects.filter(name=client_name).first()
    if not client:
        raise UnknownClient()
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not twitter_account:
        twitter_account = TwitterAccount()
        twitter_account.twitter_id = twitter_id
        twitter_account.save()
    client_account = ClientAccount.objects.filter(twitter_account=twitter_account, client=client).first()
    if not client_account:
        client_account = ClientAccount()
        client_account.client = client
        client_account.twitter_account = twitter_account
        client_account.save()
        account_config = AccountConfig()
        account_config.notification_preference = AccountConfig.NotificationPreference.TWEET
        account_config.client_account = client_account
        account_config.save()
        client_account.config = account_config
    client_account.email = email
    client_account.access_key = access_key
    client_account.secret_access_key = secret_access_key
    client_account.refreshed = timezone.now()
    client_account.save()
    lookup_twitter_user.delay(client_account_id=client_account.id)
    return Response({"client_account_id": client_account.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def fetch_users(request):
    logger.debug("Fetching users")
    body = json.loads(request.body)
    client_name = body['client']
    client = Client.objects.filter(name=client_name).first()
    accounts = ClientAccount.objects.filter(client=client).all()
    results = []
    for account in accounts:
        serializer = ClientAccountSerializer(account)
        results.append(serializer.data)
    return Response(results)


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
@csrf_exempt
def add_rss_feed_effortless_reach(request):
    body = json.loads(request.body)
    url = body['url'].trim()
    client = Client.objects.filter(name="EffortlessReach").first()
    client_account = ClientAccount.objects.filter(email='admin@effortlessreach.com', client=client).first()
    if not client_account:
        client_account = ClientAccount.objects.create(email='admin@effortlessreach.com', client=client)
        client_account.save()


    existing_feed = RssFeed.objects.filter(url=url).first()
    if not existing_feed:
        existing_feed = RssFeed(url=url, owner=client_account)
        existing_feed.save()
    process_rss_feed.delay(existing_feed.id)
    return Response({"feed_id": existing_feed.id, "client_account_id": client_account.id})
