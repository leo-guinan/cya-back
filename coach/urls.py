from django.urls import path

from coach.views import chat, add_user

urlpatterns = [
    path('chat/', chat),
    path('add_user/', add_user),
]