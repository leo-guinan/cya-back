from django.urls import path

from task.views import add, list, prioritize

urlpatterns = [
    path('add/', add),
    path('list/', list),
    path('prioritize/', prioritize),
]