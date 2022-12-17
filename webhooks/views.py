import base64
import hashlib
import hmac
import json
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from mail.service import send_email
from webhooks.activity import Activity


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
        print(request.body)
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
    print(len(message))
    send_email(from_email, "We have received your transcript.", "Thanks!")
    return Response({'status': 'ok'}, status=200)
