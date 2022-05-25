from django.urls import path
from .views import TwitterAccountList, TwitterAccountDetail, lookup_user, \
    get_followers_whose_last_tweet_was_more_than_3_months_ago, \
    get_number_of_followers_whose_last_tweet_was_more_than_3_months_ago, unfollow_user

urlpatterns = [
    path('', TwitterAccountList.as_view()),
    path('<int:pk>', TwitterAccountDetail.as_view()),
    path('lookup/', lookup_user),
    path('followers/dormant/', get_followers_whose_last_tweet_was_more_than_3_months_ago),
    path('followers/dormant/count/', get_number_of_followers_whose_last_tweet_was_more_than_3_months_ago),
    path('followers/dormant/unfollow/', unfollow_user),
]