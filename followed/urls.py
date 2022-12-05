from django.urls import path

from followed.views import subscribe, latest

urlpatterns = [
    path('subscribe/', subscribe),
    path('latest/', latest),
]