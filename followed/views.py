import json

from django.shortcuts import render
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount, Client
from followed.config import CLIENT_NAME
from followed.models import Subscriber, FollowerReport
from followed.serializers import FollowerReportSerializer
from followed.tasks import refresh_followers
from twitter.models import TwitterAccount


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def subscribe(request):
    # Subscribe to a Twitter account - get current followers and create record.

    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    client_account_id = body['client_account_id']

    client_account = ClientAccount.objects.filter(id=client_account_id, client__name=CLIENT_NAME).first()
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not twitter_account:
        twitter_account = TwitterAccount()
        twitter_account.twitter_id = twitter_id
        twitter_account.save()
    if not client_account:
        client_account = ClientAccount()
        client_account.twitter_account = twitter_account
        client = Client.objects.filter(name=CLIENT_NAME).first()
        client_account.client = client
        client_account.save()
    if not client_account.twitter_account:
        client_account.twitter_account = twitter_account
        client_account.save()
    subscriber = Subscriber.objects.filter(client_account=client_account).first()
    if not subscriber:
        subscriber = Subscriber()
        subscriber.client_account = client_account
        subscriber.save()
        refresh_followers.delay(subscriber.id)
    return Response({"subscriber_id": subscriber.id})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def latest(request):
    body = json.loads(request.body)
    subscription_id = body['subscription_id']
    print(subscription_id)
    report = FollowerReport.objects.filter(subscriber_id=subscription_id).first()

    return Response({"date": report.date, "total_followers": report.followers.count()})