from django.urls import path

from search.views import chat, search, add, create_search_engine, list_links, get_queries

urlpatterns = [
    path('', search),
    path('add/', add),
    path('create/', create_search_engine),
    path('list/', list_links),
    path('queries/', get_queries),
    path('chat/', chat),
]