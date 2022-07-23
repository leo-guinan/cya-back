import json

# Create your views here.
from django.utils import timezone
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClient, UnknownClientAccount
from client.models import Client, ClientAccount
from twitter.models import TwitterAccount
from unfollow.tasks import lookup_twitter_user

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def client_account_login(request):
    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    client_name = body['client']
    email = body['email']
    token = body['token']
    refresh_token = body['refresh_token']
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
    client_account.email = email
    client_account.token = token
    client_account.refresh_token = refresh_token
    client_account.refreshed = timezone.now()
    client_account.save()
    lookup_twitter_user.delay(client_account_id=client_account.id)
    return Response({"client_account_id": client_account.id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def refresh_account_token(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    token = body['token']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
       raise UnknownClientAccount()
    client_account.token = token
    client_account.save()
    return Response({"refresh": "success"})