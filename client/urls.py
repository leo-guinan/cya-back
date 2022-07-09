from django.urls import path

from .views import client_account_login, refresh_account_token

urlpatterns = [
    path('login/', client_account_login),
    path('account/refresh/', refresh_account_token),
]
