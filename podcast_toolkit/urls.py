from django.urls import path

from podcast_toolkit.views import generate_shownotes

urlpatterns = [
    path('generate_shownotes/', generate_shownotes),

]