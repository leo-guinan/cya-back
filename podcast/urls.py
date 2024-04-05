from django.urls import path, re_path

from podcast.views import clip, find_podcast_episodes, get_query_result

urlpatterns = [
    path('clip/', clip),
    path('find/', find_podcast_episodes),
    path('query/', get_query_result)
]