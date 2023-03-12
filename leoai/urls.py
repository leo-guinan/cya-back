from django.urls import path

from leoai.views import search

urlpatterns = [
    path('search/', search),
]