import json
import uuid

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from coach.models import User
from coach.tasks import add_user_email

# Create your views here.


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def chat(request):
    pass
    # body = json.loads(request.body)
    # message = body['message']
    # user_id = body['user_id']
    # session_id = body.get('session_id', str(uuid.uuid4()))
    #
    # return Response({'message': response, 'session_id': session_id})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def add_user(request):
    body = json.loads(request.body)
    email = body['email']
    name = body['name']
    preferred_name = body['preferred_name']
    initial_session_id = str(uuid.uuid4())
    user = User(name=name, email=email, preferred_name=preferred_name, initial_session_id=initial_session_id)
    user.save()
    add_user_email.delay(email, preferred_name)
    return Response({'user_id': user.id, 'session_id': initial_session_id})
