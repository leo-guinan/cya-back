from django.urls import path

from appadmin.views import lookup_client_account, refresh_client_account

urlpatterns = [
    path('lookup_user/', lookup_client_account),
    path('refresh_user/', refresh_client_account),

]
