from django.urls import path

from leoai.views import  chat

urlpatterns = [
    path('chat/', chat),

]