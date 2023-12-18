from django.urls import path, re_path

from podcast.views import clip
urlpatterns = [
    path('clip/', clip),
]