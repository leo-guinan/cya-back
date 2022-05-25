from datetime import datetime, timedelta

from pytz import utc

from backend.celery import app
from twitter_api.twitter_api import TwitterAPI
from unfollow.models import TwitterAccount, FollowingRelationship


@app.task(name="lookup_twitter_user")
def lookup_twitter_user(token, twitter_id_to_check):
    twitter_api = TwitterAPI()
    current_user = TwitterAccount.objects.filter(twitter_id=twitter_id_to_check).first()
    if not current_user:
        user_data = twitter_api.lookup_user(twitter_id=twitter_id_to_check)
        if not user_data:
            return None
        current_user = TwitterAccount(twitter_id=twitter_id_to_check, twitter_username=user_data.username,
                                      twitter_name=user_data.name)
        print(current_user)
        current_user.save()
    followers = twitter_api.get_following_for_user(twitter_id=twitter_id_to_check, token=token)
    for user in followers:
        twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=user.id, twitter_username=user.username,
                                             twitter_name=user.name
                                             )
            twitter_account.save()
        user_follows_account.delay(twitter_id_to_check, user.id)
        get_most_recent_tweet_for_account.delay(token, user.id)


@app.task(name="get_most_recent_tweet")
def get_most_recent_tweet_for_account(token, account_id):
    twitter_api = TwitterAPI()
    twitter_account = TwitterAccount.objects.filter(twitter_id=account_id).first()
    if (twitter_account.last_tweet_date and twitter_account.last_tweet_date > (
    utc.localize(datetime.now() - timedelta(days=90)))):
        return
    most_recent_tweet = twitter_api.get_most_recent_tweet_for_user(account_id, token=token)
    if most_recent_tweet is not None:
        twitter_account.last_tweet_date = most_recent_tweet.created_at
        twitter_account.save()
    else:
        # when no tweet, just set last tweet date to 5 years ago
        twitter_account.last_tweet_date = utc.localize(datetime.now() - timedelta(weeks=52 * 5))
        twitter_account.save()


@app.task(name="user_follows_account")
def user_follows_account(user_id, follows_id):
    relationship = FollowingRelationship.objects.filter(twitter_user__twitter_id=user_id,
                                                        follows__twitter_id=follows_id).first()
    if not relationship:
        current_user = TwitterAccount.objects.filter(twitter_id=user_id).first()
        twitter_account = TwitterAccount.objects.filter(twitter_id=follows_id).first()
        relationship = FollowingRelationship(twitter_user=current_user, follows=twitter_account)
        relationship.save()
