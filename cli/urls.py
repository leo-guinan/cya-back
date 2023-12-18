from django.urls import path, re_path

from cli.views import command

urlpatterns = [
    path('command/', command),


]