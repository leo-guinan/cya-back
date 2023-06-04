from django.urls import path

from chat.views import chat, add_client_app

urlpatterns = [
    path('add/', add_client_app),
    path('<str:client>/', chat),
]
