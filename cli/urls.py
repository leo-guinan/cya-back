from django.urls import path, re_path

from cli.views import add_command

urlpatterns = [
    path('add_command/', add_command),
]