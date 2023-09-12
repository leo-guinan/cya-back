from django.urls import path, re_path

from experiments.views import run_requests

urlpatterns = [
    path('test/', run_requests)
]