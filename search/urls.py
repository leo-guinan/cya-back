from django.urls import path

from search.views import search, add, create_search_engine, list_links

urlpatterns = [
    path('', search),
    path('add/', add),
    path('create/', create_search_engine),
    path('list/', list_links)
]