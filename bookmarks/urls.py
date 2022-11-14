from django.urls import path

from bookmarks.views import get_bookmarks_for_user

urlpatterns = [
    path('fetch/', get_bookmarks_for_user),
]
