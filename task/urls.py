from django.urls import path

from task.views import add

urlpatterns = [
    path('add/', add),
]