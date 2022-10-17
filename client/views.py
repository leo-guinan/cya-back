import json

# Create your views here.
from django.utils import timezone
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.exception import UnknownClient, UnknownClientAccount
from client.models import Client, ClientAccount, AccountConfig
from twitter.models import TwitterAccount
from unfollow.tasks import lookup_twitter_user

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def client_account_login(request):
    print("client_account_login")
    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    client_name = body['client']
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
        account_config.client_account=client_account
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
def client_email_account_login(request):
    print("client_account_login")
    body = json.loads(request.body)
    client_name = body['client']
    email = body['email']
    client = Client.objects.filter(name=client_name).first()
    if not client:
        raise UnknownClient()
    client_account = ClientAccount.objects.filter(email=email, client=client).first()
    if not client_account:
        client_account = ClientAccount()
        client_account.client = client
        client_account.save()
        account_config = AccountConfig()
        account_config.notification_preference = AccountConfig.NotificationPreference.TWEET
        account_config.client_account=client_account
        account_config.save()
        client_account.config = account_config
    client_account.email = email
    client_account.refreshed = timezone.now()
    client_account.save()
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

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def update_client_account_preferences(request):
    body = json.loads(request.body)
    client_account_id = body['client_account_id']
    email = body['email']
    notification_preference = body['notification_preference']
    notification_requested = body['notification_requested']
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    config = client_account.config
    if not config:
        config = AccountConfig()
        config.client_account = client_account
    if notification_preference == 'email':
        config.notification_preference = AccountConfig.NotificationPreference.EMAIL
    elif notification_preference == "dm":
        config.notification_preference = AccountConfig.NotificationPreference.DIRECT_MESSAGE
    else:
        config.notification_preference = AccountConfig.NotificationPreference.TWEET
    config.notification_requested = notification_requested
    config.save()
    if email:
        client_account.email = email
    client_account.save()
    return Response({"refresh": "success"})
