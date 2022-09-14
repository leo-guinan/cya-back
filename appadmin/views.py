import json
from datetime import datetime, timedelta

from django.shortcuts import render

# Create your views here.
from pytz import utc
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClientAccount
from client.models import ClientAccount
from twitter.models import Relationship
from unfollow.tasks import lookup_twitter_user


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
    followers_to_analyze = client_account.accounts_to_analyze.filter(last_analyzed__isnull=True).count()
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
