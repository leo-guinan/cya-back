import base64
import hashlib
import hmac
import json
import logging

from decouple import config
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from client.models import ClientAccount, Client
from mail.service import send_email
from marketing.service import add_user_to_app_list
from podcast_toolkit.tasks import process_transcript_request
from search.tasks import save_content_task
from webhooks.activity import Activity
from webhooks.models import TranscriptRequestEmail
from webhooks.tasks import twitter_user_experiment
logger = logging.getLogger(__name__)


# Create your views here.
@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([])
@csrf_exempt
def twitter_webhook(request):
    if request.method == 'GET':
        # creates HMAC SHA-256 hash from incomming token and your consumer secret
        sha256_hash_digest = hmac.new(config('TWITTER_API_SECRET').encode('utf-8'),
                                      msg=request.GET['crc_token'].encode('utf-8'),
                                      digestmod=hashlib.sha256).digest()

        # construct response data with base64 encoded hash
        response = {
            'response_token': 'sha256=' + base64.b64encode(sha256_hash_digest).decode('utf-8')
        }

        # returns properly formatted json response
        return Response(response, status=200)
    elif request.method == 'POST':
        # do something with the request
        # TODO: do something with the event
        logger.debug(request.body)
        return Response({'status': 'ok'}, status=200)


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def list_twitter_webhook_environments(request):
    activity = Activity()
    return Response(activity.webhooks())


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def register_twitter_webhook(request):
    activity = Activity()
    activity.register_webhook(request.GET['callback_url'])
    return Response(activity.webhooks())


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def delete_twitter_webhook(request):
    activity = Activity()
    activity.delete(request.GET['id'])
    return Response(activity.webhooks())


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def subscribe_twitter_webhook(request):
    activity = Activity()
    activity.subscribe()
    return Response(activity.webhooks())


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def email_received(request):
    body = json.loads(request.body)
    from_email = body['from']
    message = body['text']
    title = body['title']
    client_account = ClientAccount.objects.filter(email=from_email, client__name="PODCAST_TOOLKIT").first()
    if not client_account:
        # add to marketing list and send invite to signup
        add_user_to_app_list(from_email, "PODCAST_TOOLKIT", ["new_user"])
        # should I create account with trial here? could also tag with user id in case of email switch

        client_account = ClientAccount()
        client_account.email = from_email
        client = Client.objects.get(name="PODCAST_TOOLKIT")
        client_account.client = client
        client_account.save()
    record = TranscriptRequestEmail.objects.filter(from_email=from_email, title=title, client_account=client_account).first()
    if record is None:
        record = TranscriptRequestEmail(from_email=from_email, title=title, transcript=message)
        record.save()
        process_transcript_request.delay(record.id)
    send_email('leo@definet.dev', f"new transcript received: {client_account.id}", "Transcript Alert!")
    return Response({'status': 'ok'}, status=200)


@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def content_received(request):
    body = json.loads(request.body)
    author_email = body['author_email']
    message = body['text']
    title = body['title']
    link = body['link']
    content_type = body['type']
    description = body['description']

    # link = models.URLField(unique=True)
    #     title = models.CharField(max_length=255)
    #     description = models.TextField()
    #     creator = models.ForeignKey('client.ClientAccount', related_name='created_items', on_delete=models.CASCADE)
    #     type = models.CharField(max_length=255, null=True, blank=True)
    client_account = ClientAccount.objects.filter(email=author_email, client__name="PODCAST_TOOLKIT").first()
    if not client_account:
        # add to marketing list and send invite to signup
        # add_user_to_app_list(from_email, "PODCAST_TOOLKIT", ["new_user"])
        # should I create account with trial here? could also tag with user id in case of email switch

        client_account = ClientAccount()
        client_account.email = author_email
        client = Client.objects.get(name="SEARCH")
        client_account.client = client
        client_account.save()

    save_content_task.delay(text=message, title=title, description=description, link=link, content_type=content_type, creator_id=client_account.id)
    return Response({'status': 'ok'}, status=200)

@api_view(('POST', 'GET'))
@renderer_classes((JSONRenderer,))
@authentication_classes([])
@permission_classes([HasAPIKey])
@csrf_exempt
def process_twitter_user(request):
    body = json.loads(request.body)
    twitter_username = body['twitter_username']
    for_author = body.get('for_author', None)
    twitter_user_experiment.delay(twitter_username, for_author)
    return Response({'status': 'ok'}, status=200)


