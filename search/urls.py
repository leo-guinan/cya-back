from django.urls import path

from search.views import search, add

urlpatterns = [
    path('', search),
    path('add/', add),
]