from django.urls import path

from task.views import add, complete, generate, get, list, prioritize

urlpatterns = [
    path('add/', add),
    path('list/', list),
    path('prioritize/', prioritize),
    path('complete/', complete),
    path('generate/', generate),
    path('get/', get),
]