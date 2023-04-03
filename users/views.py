import json

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from users.models import User


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add_user(request):
    body = json.loads(request.body)
    email = body['email']
    user = User.objects.filter(email=email).first()
    if user is None:
        user = User(email=email)
        user.save()
    return Response({'user_id': user.id})

# Create your views here.
