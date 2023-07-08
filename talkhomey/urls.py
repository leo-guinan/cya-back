from django.urls import path

from talkhomey.views import add

urlpatterns = [
    path('add/', add),
]