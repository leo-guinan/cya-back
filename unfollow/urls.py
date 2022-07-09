from django.urls import path
from .views import TwitterAccountList, TwitterAccountDetail, \
    get_followers_whose_last_tweet_was_more_than_3_months_ago, \
    get_number_of_followers_whose_last_tweet_was_more_than_3_months_ago, unfollow_user, \
    get_number_of_followers_processed, get_number_of_followers, protect_user, get_protected_users, unprotect_user, \
    analyze_self

urlpatterns = [
    path('', TwitterAccountList.as_view()),
    path('<int:pk>', TwitterAccountDetail.as_view()),
    path('lookup_self/', analyze_self),
    path('followers/', get_number_of_followers),
    path('followers/processed/', get_number_of_followers_processed),
    path('followers/dormant/', get_followers_whose_last_tweet_was_more_than_3_months_ago),
    path('followers/dormant/count/', get_number_of_followers_whose_last_tweet_was_more_than_3_months_ago),
    path('followers/dormant/unfollow/', unfollow_user),
    path('followers/dormant/protect/', protect_user),
    path('followers/dormant/unprotect/', unprotect_user),
    path('followers/protected/', get_protected_users),
]