from datetime import datetime, timedelta

from pytz import utc

from client.models import ClientAccount
from twitter.models import TwitterAccount, Tweet, Relationship
from twitter_api.twitter_api import TwitterAPI
from unfollow.models import AccountCheck


def get_twitter_account(twitter_id, client_account_id=None):
    account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not account:
        account = refresh_twitter_account(twitter_id, client_account_id)
    return account


def refresh_twitter_account(twitter_id, client_account_id=None, staff_account=False):
    twitter_api = TwitterAPI()
    raw_user = twitter_api.lookup_user(twitter_id=twitter_id, client_account_id=client_account_id, staff_account=staff_account)
    account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if raw_user:
        return save_twitter_account_to_database(raw_user)
    else:
        if account:
            account.delete()
    return None


def update_users_following_twitter_account(twitter_id=None, client_account_id=None, client=None):
    twitter_api = TwitterAPI(client)
    followers = twitter_api.get_users_following_account(twitter_id=twitter_id, client_account_id=client_account_id)
    current_user = TwitterAccount.objects.get(twitter_id=twitter_id)
    followed_by = Relationship.objects.filter(follows_this_account=current_user).all()
    followed_by.delete()
    for user in followers:
        account_check_request(client_account_id, user.id)
        twitter_account = get_twitter_account(user.id, client_account_id)
        relationship = Relationship(this_account=twitter_account, follows_this_account=current_user)
        relationship.save()


def update_twitter_accounts_user_is_following(twitter_id, client_account_id=None, client=None):
    twitter_api = TwitterAPI(client)
    followers = twitter_api.get_following_for_user(twitter_id=twitter_id, client_account_id=client_account_id)
    current_user = get_twitter_account(twitter_id=twitter_id)
    following = Relationship.objects.filter(this_account=current_user).all()
    following.delete()
    for user in followers:
        account_check_request(client_account_id, user.id)
        twitter_account = get_twitter_account(user.id, client_account_id)
        relationship = Relationship(this_account=current_user, follows_this_account=twitter_account)
        relationship.save()


def account_check_request(client_account_id, twitter_id):
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
        if not twitter_account:
            twitter_account = TwitterAccount()
            twitter_account.twitter_id = twitter_id
            twitter_account.save()
        existing_check = AccountCheck.objects.filter(account=twitter_account).first()
        if not existing_check:
            existing_check = AccountCheck()
            existing_check.account = twitter_account
            existing_check.status = AccountCheck.CheckStatus.REQUESTED
            existing_check.save()
        existing_check.requests.add(client_account)
        existing_check.save()


def unfollow_account(client_account_id, twitter_id_to_unfollow):
    twitter_api = TwitterAPI()
    twitter_api.unfollow_user(client_account_id, twitter_id_to_unfollow)


def get_most_recent_tweet(client_account_id, twitter_id_to_lookup, staff_account=False):
    twitter_api = TwitterAPI()

    most_recent_tweet, author = twitter_api.get_most_recent_tweet_for_user(client_account_id=client_account_id,
                                                                           twitter_id=twitter_id_to_lookup,
                                                                           staff_account=staff_account)
    if author:
        save_twitter_account_to_database(author)
    update_twitter_account_with_most_recent_tweet(most_recent_tweet)
    return most_recent_tweet, author


def update_twitter_account_with_most_recent_tweet(most_recent_tweet):
    twitter_account = TwitterAccount.objects.filter(twitter_id=most_recent_tweet.author_id).first()

    if not twitter_account:
        raise Exception("Twitter account should exist here.")
    if most_recent_tweet is not None:
        twitter_account.last_tweet_date = most_recent_tweet.created_at
        twitter_account.save()
    else:
        # when no tweet, just set last tweet date to 5 years ago
        twitter_account.last_tweet_date = utc.localize(datetime.now() - timedelta(weeks=52 * 5))
        twitter_account.save()


def get_recent_tweets(client_account_id, twitter_id, staff_account=False):
    twitter_api = TwitterAPI()
    number_of_tweets = Tweet.objects.filter(author__twitter_id=twitter_id).count()
    if number_of_tweets > 0:
        latest_tweet = Tweet.objects.filter(author__twitter_id=twitter_id).latest('tweet_created_at')

        tweets = twitter_api.get_latest_tweets(twitter_id,
                                               since_tweet_id=latest_tweet.tweet_id if latest_tweet else None,
                                               client_account_id=client_account_id, staff_account=staff_account)
    else:
        tweets = twitter_api.get_latest_tweets(twitter_id,
                                               client_account_id=client_account_id, staff_account=staff_account)
    if not tweets or len(tweets) == 0:
        print("no tweets found for user...")
        return
    for tweet in tweets:
        save_tweet_to_database(tweet)


def save_tweet_to_database(raw_tweet):
    print(raw_tweet)
    author = get_twitter_account(raw_tweet.author_id)
    tweet = Tweet()
    tweet.tweet_id = raw_tweet.id
    tweet.tweet_created_at = raw_tweet.created_at
    tweet.author = author
    tweet.message = raw_tweet.text
    tweet.save()
    return tweet


def save_twitter_account_to_database(raw_user):
    twitter_account = TwitterAccount.objects.filter(twitter_id=raw_user.id).first()
    if not twitter_account:
        twitter_account = TwitterAccount()
        twitter_account.twitter_id = raw_user.id
        twitter_account.save()
    twitter_account.twitter_username = raw_user.username
    twitter_account.twitter_bio = raw_user.description
    twitter_account.twitter_name = raw_user.name
    twitter_account.twitter_profile_picture_url = raw_user.profile_image_url
    twitter_account.protected = raw_user.protected
    twitter_account.save()
    return twitter_account


def get_tweet(tweet_id):
    existing_tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
    if not existing_tweet:
        twitter_api = TwitterAPI()
        raw_tweet = twitter_api.get_tweet(tweet_id)
        existing_tweet = save_tweet_to_database(raw_tweet)
    return existing_tweet


def send_tweet(from_client, message):
    twitter_api = TwitterAPI()
    twitter_api.send_tweet_as_client(app_client=from_client, message=message)


def send_dm_to_account(from_client, to_twitter_id, message):
    twitter_api = TwitterAPI()
    twitter_api.send_dm_to_user(from_client.id, to_twitter_id, message)
