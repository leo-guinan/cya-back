from django.urls import path

from lobow.views import chat

urlpatterns = [
    path('chat/', chat)
]
