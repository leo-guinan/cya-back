from django.urls import path

from client.views import new_client

urlpatterns = [
    path('new/', new_client),
]