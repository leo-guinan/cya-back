from django.urls import path

from gardens.views import add_feed, get_feeds

urlpatterns = [
    path('add_feed/', add_feed),
    path('feeds/', get_feeds),
]
