from django.urls import path

from leoai.views import search, add_to_collection

urlpatterns = [
    path('search/', search),
    path('add-to-collection/', add_to_collection),
]