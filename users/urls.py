from django.urls import path

from users.views import add_user

urlpatterns = [
    path('add/', add_user),
]
