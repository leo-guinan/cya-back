from django.urls import path

from bookmarks.views import get_bookmarks_for_user, update_bookmark_name

urlpatterns = [
    path('fetch/', get_bookmarks_for_user),
    path('update_name/', update_bookmark_name),
]
