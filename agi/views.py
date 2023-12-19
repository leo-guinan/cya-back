import json

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from agi.models import OutgoingRequest
from agi.tasks import respond_to_agi_message, respond_to_webhook


# Create your views here.


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def salesforce_list_meetings(request):
    pass


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def person(request):
    body = json.loads(request.body)
    print(body)
    respond_to_agi_message.delay(body.get("message", ""), None, None)
    return Response({'message': 'Hello, world!'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def respond(request):
    body = json.loads(request.body)
    print(body)
    if body.get("respond_to", ""):
        respond_to_webhook.delay(body.get("respond_to", ""), body.get("message", ""), None, None)
    return Response({'message': 'You should help people with the stuff you are good at.'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
def webhook(request, uuid):
    print(uuid)
    body = json.loads(request.body)
    print(body)
    # look up webhook response.
    original_request = OutgoingRequest.objects.get(uuid=uuid)
    original_request.processed = True
    original_request.save()
    return Response({'message': 'Hello, world!'})
