from django.urls import path

from spark.views import search

urlpatterns = [
    path('search/', search),
]