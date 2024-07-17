from django.urls import path

from leoai.views import chat, chat_ev

urlpatterns = [
    path('chat/', chat),
    path('chat/ev/', chat_ev),

]