from django.urls import path, re_path

from cli.views import add_command, say_hi

urlpatterns = [
    path('add_command/', add_command),
    path('say_hi/', say_hi),
]