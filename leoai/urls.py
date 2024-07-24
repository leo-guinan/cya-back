from django.urls import path

from leoai.views import chat, chat_ev, write_linkedin_post

urlpatterns = [
    path('chat/', chat),
    path('linkedin/', write_linkedin_post),

    path('chat/ev/', chat_ev),

]