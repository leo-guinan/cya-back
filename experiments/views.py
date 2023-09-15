import json

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from experiments.service import version_one, version_two, version_three, s3_upload


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

@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def upload_file(request):
    file = request.FILES['file']

    # Save file in S3.
    response = s3_upload(file)

    if response:
        return Response({"message": "Successful upload"})
    else:
        return Response({"message": "Upload could not be performed."}, status=400)
