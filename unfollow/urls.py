from django.urls import path

from .views import TwitterAccountList, TwitterAccountDetail, \
    get_followers_whose_last_tweet_was_more_than_3_months_ago, \
    unfollow_user, \
    get_number_of_followers_processed, get_number_of_followers, protect_user, get_protected_users, unprotect_user, \
    get_account_analysis, get_number_of_accounts_left_to_analyze, bulk_unfollow_users, bulk_request_status

urlpatterns = [
    path('', TwitterAccountList.as_view()),
    path('<int:pk>', TwitterAccountDetail.as_view()),
    path('analyze/', get_account_analysis),
    path('status/', get_number_of_accounts_left_to_analyze),
    path('followers/', get_number_of_followers),
    path('followers/processed/', get_number_of_followers_processed),
    path('followers/dormant/', get_followers_whose_last_tweet_was_more_than_3_months_ago),
    path('followers/dormant/unfollow/', unfollow_user),
    path('followers/dormant/bulk_unfollow/', bulk_unfollow_users),
    path('followers/dormant/bulk_unfollow_status/', bulk_request_status),
    path('followers/dormant/protect/', protect_user),
    path('followers/dormant/unprotect/', unprotect_user),
    path('followers/protected/', get_protected_users),
]
