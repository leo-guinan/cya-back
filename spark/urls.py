from django.urls import path

from spark.views import search, add

urlpatterns = [
    path('search/', search),
    path('add/', add),
]