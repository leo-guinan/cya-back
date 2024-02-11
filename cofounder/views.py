import json
import uuid
from datetime import datetime

from decouple import config
from langchain.memory import MongoDBChatMessageHistory
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from cofounder.cofounder.default import DefaultCofounder
from cofounder.models import User, ChatSession, CHAT_TYPE_MAPPING, UserPreferences, FounderProfile, BusinessProfile, \
    Answer, Task


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def add_user(request):
    body = json.loads(request.body)
    email = body['email']
    name = body['name']
    initial_session_id = str(uuid.uuid4())
    user = User(name=name, email=email, initial_session_id=initial_session_id)
    user.save()
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
def start_chat(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    chat_session = ChatSession()
    chat_session.user = user
    chat_session.session_id = str(uuid.uuid4())
    chat_session.chat_type = CHAT_TYPE_MAPPING["default"]
    chat_session.save()

    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=chat_session.session_id
    )
    # cofounder = DefaultCofounder(chat_session.session_id, user.id)

    # message_history.add_ai_message(cofounder.greet_founder())

    return Response({'session_id': chat_session.session_id})

@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_preferences(request, user_id):
    user_preferences = UserPreferences.objects.filter(user_id=user_id).first()
    if not user_preferences:
        user_preferences = UserPreferences()
        user_preferences.user_id = user_id
        user_preferences.save()
    return Response({'preferences': {
        'daily_checkin': user_preferences.daily_checkin,
    }})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def set_preferences(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    user.preferences.daily_checkin = body['preferences']['daily_checkin']
    user.preferences.save()
    return Response({"status": "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def set_profile(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    profile = FounderProfile.objects.filter(user=user).first()
    business_profile = BusinessProfile.objects.filter(user=user).first()
    if not profile:
        profile = FounderProfile()
        profile.user = user
    profile.profile = body['founder_profile']
    profile.save()

    if not business_profile:
        business_profile = BusinessProfile()
        business_profile.user = user
    business_profile.profile = body['business_profile']
    business_profile.name = body['business_name']
    business_profile.website = body['business_website']
    business_profile.save()
    return Response({"status": "success"})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def get_profile(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    profile = FounderProfile.objects.filter(user=user).first()
    business_profile = BusinessProfile.objects.filter(user=user).first()

    return Response({
        "founder_name": user.name,
        "business_name": business_profile.name if business_profile else "",
        "business_website": business_profile.website if business_profile else "",
        "founder_profile": profile.profile if profile else "",
        "business_profile": business_profile.profile if business_profile else "",
    })

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def teach_cofounder(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    user = User.objects.get(id=user_id)
    # content_type = body['content_type']
    # url = body['url']
    title = body['title']
    description = body['description']
    full_text = body['full_text']
    session_id = str(uuid.uuid4())
    cofounder = DefaultCofounder(session_id, user_id)
    cofounder.learn(title, description, full_text)
    return Response({"status": "success"})



def webhook():
    pass

def formatTask(task):
    return {
        "name": task.task,
        "details": task.details,
        "taskFor": task['for']
    }
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def tasks(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    session_id = body['session_id']
    session = ChatSession.objects.filter(session_id=session_id, user_id=user_id).first()
    tasks = Task.objects.filter(session=session).all()

    return Response({"tasks": map(lambda task: formatTask, tasks)})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def answers(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    session_id = body['session_id']
    session = ChatSession.objects.filter(session_id=session_id, user_id=user_id).first()
    answers = Answer.objects.filter(session=session).all()

    mapped_answers = map(lambda answer: answer.answer, answers)
    print(mapped_answers)
    return Response({"answers": mapped_answers})