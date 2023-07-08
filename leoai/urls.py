from django.urls import path

from leoai.views import search, add_to_collection, get_collection, add_fact, get_facts, youtube_to_notion

urlpatterns = [
    path('search/', search),
    path('add-to-collection/', add_to_collection),
    path('add-fact/', add_fact),
    path('get-collection/', get_collection),
    path('get-facts/', get_facts),
    path('youtube/', youtube_to_notion),
]