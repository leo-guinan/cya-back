from django.urls import path, re_path

from toolkit.views import video_to_blog

urlpatterns = [
    path('video_to_blog/', video_to_blog),
]