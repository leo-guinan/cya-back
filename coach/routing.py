from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"api/ws/chat/(?P<session_id>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})/$", consumers.ChatConsumer.as_asgi()),
]