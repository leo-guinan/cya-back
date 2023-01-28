from django.urls import path

from effortless_reach.views import parse_rss_feed

urlpatterns = [
    path('parse/', parse_rss_feed),
]