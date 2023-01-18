from django.urls import path

from search.views import search_creator_content

urlpatterns = [
    path('search/', search_creator_content),

]