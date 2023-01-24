from django.urls import path

from search.views import search_creator_content, search_curated_content

urlpatterns = [
    path('search/', search_creator_content),
    path('curated/', search_curated_content),

]