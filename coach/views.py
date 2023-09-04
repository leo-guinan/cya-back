import json
import uuid
from datetime import datetime

from decouple import config
from langchain.memory import MongoDBChatMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from coach.models import User, ChatSession, CHAT_TYPE_MAPPING
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


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_chat(request):
    body = json.loads(request.body)
    print(body)
    session_id = body['session_id']
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    print(session_id)

    chat = ChatSession.objects.filter(session_id=session_id, user=user).first()
    if not chat:
        chat = ChatSession(session_id=session_id, user=user)
        chat.save()
        return Response({'name': chat.name, 'session_id': chat.session_id, 'messages': [
            {
                'message': 'What can I help you with?',
                'type': 'ai'

            }
        ]})
    # get chat session from Mongo
    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
    )

    messages = [{
        'message': message.content,
        'type': message.type,
    } for message in message_history.messages]


    if not messages:
        messages = [{
            'message': 'What can I help you with?',
            'type': 'ai'

        }]

    return Response({'name': chat.name, 'session_id': chat.session_id, 'messages': messages})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def start_daily_checkin(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    chat_type = body['chat_type']
    user = User.objects.get(id=user_id)
    mapped_type = CHAT_TYPE_MAPPING[chat_type]
    chat_session = ChatSession()
    chat_session.user = user
    chat_session.session_id = str(uuid.uuid4())
    chat_session.name = f"Daily Check-in {str(datetime.today().strftime('%m/%d/%y'))}"
    chat_session.chat_type = mapped_type
    chat_session.save()

    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=chat_session.session_id
    )
    if(mapped_type == ChatSession.DAILY_GREAT):
        message = "Glad to hear you are doing great! What's going well?"
    elif(mapped_type == ChatSession.DAILY_BAD):
        message = "Sorry to hear you are doing bad. What's going on?"
    elif(mapped_type == ChatSession.DAILY_OK):
        message = "Most days are only ok! That's ok. Anything you are excited for?"
    else:
        message = "What can I help you with?"
    message_history.add_ai_message(message)

    return Response({'session_id': chat_session.session_id})

