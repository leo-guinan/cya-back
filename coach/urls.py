from django.urls import path

from coach.views import add_user, list_chats

urlpatterns = [
    path('add_user/', add_user),
    path('chats/', list_chats),
]