from django.urls import path

from payments.views import create_checkout_session

urlpatterns = [
    path('create_checkout_session/', create_checkout_session),
    ]