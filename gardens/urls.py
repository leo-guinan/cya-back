from django.urls import path

from gardens.views import add_feed, get_feeds, get_content_for_feed

urlpatterns = [
    path('add_feed/', add_feed),
    path('feeds/', get_feeds),
    path('get_content/', get_content_for_feed),

]
