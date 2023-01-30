from django.urls import path

from effortless_reach.views import parse_rss_feed, get_podcast_episodes

urlpatterns = [
    path('parse/', parse_rss_feed),
    path('get_episodes/', get_podcast_episodes),
]