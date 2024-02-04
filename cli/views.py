import json
from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes, renderer_classes, api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from cli.tasks import add_command as add_command_task
# Create your views here.


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def add_command(request):
    body = json.loads(request.body)
    command, description, url, input, output = body["command"], body["description"], body["url"], body["input"], body["output"]
    add_command_task.delay(command, description, url, input, output)


    return Response({'message': 'Done'})

