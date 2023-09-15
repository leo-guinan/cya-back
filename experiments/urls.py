from django.urls import path, re_path

from experiments.views import run_requests, upload_file

urlpatterns = [
    path('test/', run_requests),
    path('test/upload/', upload_file)
]