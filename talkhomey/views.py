import json

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from talkhomey.models import Resource


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add(request):
    body = json.loads(request.body)
    name = body.get('name', None)
    url = body.get('url', None)
    description = body.get('description', None)
    if name is None or url is None or description is None:
        return Response({'message': 'Missing required fields'}, status=400)
    resource = Resource.objects.create(name=name, url=url, description=description)
    return Response({'resource': resource.id,})
