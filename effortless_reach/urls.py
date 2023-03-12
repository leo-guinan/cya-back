from django.urls import path

from effortless_reach.views import parse_rss_feed, get_podcast_episodes, generate_summary, generate_keypoints, \
    save_notes

urlpatterns = [
    path('parse/', parse_rss_feed),
    path('get_episodes/', get_podcast_episodes),
    path('generate_summary/', generate_summary),
    path('generate_keypoints/', generate_keypoints),
    path('save_notes/', save_notes),
]