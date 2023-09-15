import json

import pinecone
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from experiments.models import UploadedFile, ExperimentMessage
from experiments.service import version_one, version_two, version_three, s3_upload, s3_download


# Create your views here.


@csrf_exempt
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def run_requests(request):
    pinecone.init(
        api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
        environment=config("PINECONE_ENV"),  # next to api key in console
    )
    body = json.loads(request.body)
    message = body['message']
    upload_file = UploadedFile.objects.latest('created_at')
    s3_download(upload_file.key)
    experiment_message = ExperimentMessage(uploaded_file=upload_file, message=message)
    experiment_message.save()
    v1 = version_one(upload_file.key, experiment_message)
    v2 = version_two(experiment_message)
    v3 = version_three(experiment_message, upload_file.bucket, upload_file.key)

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
