from django.urls import path

from search.views import search_curated_content, create_curator, browse_podcasts, \
    curate_podcast, uncurate_podcast, curated_podcasts, search_content

urlpatterns = [
    path('search/', search_content),
    path('curated/', search_curated_content),
    path('create_curator/', create_curator),
    path('browse_podcasts/', browse_podcasts),
    path('curated_podcasts/', curated_podcasts),
    path('curate/', curate_podcast),
    path('uncurate/', uncurate_podcast),


]