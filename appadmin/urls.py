from django.urls import path

from appadmin.views import lookup_client_account, refresh_client_account, fetch_users, add_rss_feed_effortless_reach

urlpatterns = [
    path('lookup_user/', lookup_client_account),
    path('refresh_user/', refresh_client_account),
    path('fetch_users/', fetch_users),
    path('process_rss_feed/', add_rss_feed_effortless_reach)

]
