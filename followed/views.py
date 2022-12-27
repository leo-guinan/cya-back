import json
import logging

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount, Client
from followed.config import CLIENT_NAME
from followed.models import Subscriber, FollowerReport
from followed.tasks import refresh_followers_for_account
from twitter.models import TwitterAccount
logger = logging.getLogger(__name__)


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
        logger.debug(f'subscribed new twitter_account: {twitter_account.id}')
    logger.debug(f'subscription for twitter_account: {twitter_account.id}')

    if not client_account:
        client_account = ClientAccount()
        client_account.twitter_account = twitter_account
        client = Client.objects.filter(name=CLIENT_NAME).first()
        client_account.client = client
        client_account.save()
        logger.debug(f'subscribed new client_account: {client_account.id}')
    logger.debug(f'subscription for client_account: {client_account.id}')

    if not client_account.twitter_account:
        client_account.twitter_account = twitter_account
        client_account.save()
    subscriber = Subscriber.objects.filter(client_account=client_account).first()
    if not subscriber:
        subscriber = Subscriber()
        subscriber.client_account = client_account
        subscriber.save()
        refresh_followers_for_account.delay(subscriber.id)
        logger.debug(f'new subscriber record created: {subscriber.id}')
    logger.debug(f'subscriber record: {subscriber.id}')
    return Response({"subscriber_id": subscriber.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def latest(request):
    body = json.loads(request.body)
    subscription_id = body['subscription_id']
    report = FollowerReport.objects.filter(subscriber_id=subscription_id).first()
    if not report:
        return Response({"error": "No report found."})
    return Response({"date": report.date, "total_followers": report.followers.count()})
