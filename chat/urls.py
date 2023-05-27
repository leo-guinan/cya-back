from django.urls import path

from chat.views import chat, add_client

urlpatterns = [
    path('add/', add_client),
    path('<str:client>/', chat),
]
