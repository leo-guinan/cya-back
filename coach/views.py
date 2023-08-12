import json
import uuid

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from coach.models import User, ChatSession
from coach.tasks import add_user_email


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


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def list_chats(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    chats = ChatSession.objects.filter(user=user).order_by("updated")
    chats_response = [{'name': chat.name, 'session_id': chat.session_id} for chat in chats]
    return Response({'chats': chats_response})