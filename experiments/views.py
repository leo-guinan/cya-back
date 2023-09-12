import json

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from experiments.service import version_one, version_two, version_three


# Create your views here.


@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def run_requests(request):
    body = json.loads(request.body)
    message = body['message']
    v1 = version_one(message)
    v2 = version_two(message)
    v3 = version_three(message)

    return Response({'version_one': v1, 'version_two': v2, 'version_three': v3})
