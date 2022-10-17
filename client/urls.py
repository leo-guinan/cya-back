from django.urls import path

from .views import client_account_login, refresh_account_token, update_client_account_preferences, \
    client_email_account_login

urlpatterns = [
    path('login/', client_account_login),
    path('email_login/', client_email_account_login),
    path('account/refresh/', refresh_account_token),
    path('account/preferences/', update_client_account_preferences),
]
