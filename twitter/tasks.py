from datetime import datetime

from PIL import ImageFont
from pytz import utc

from backend.celery import app
from client.exception import UnknownClientAccount
from client.models import ClientAccount
from tweetpik.tweetpik import TweetPik
from twitter.models import TwitterAccount, Tweet
from twitter.service import refresh_twitter_account, get_twitter_account, unfollow_account, update_twitter_accounts_user_is_following, \
    update_users_following_twitter_account
from twitter_api.twitter_api import TwitterAPI
from unfollow.models import UnfollowRequest

FONT_USER_INFO = ImageFont.truetype("arial.ttf", 90, encoding="utf-8")
FONT_TEXT = ImageFont.truetype("arial.ttf", 110, encoding="utf-8")
WIDTH = 2376
HEIGHT = 2024
COLOR_BG = 'white'
COLOR_NAME = 'black'
COLOR_TAG = (64, 64, 64)
COLOR_TEXT = 'black'
COORD_PHOTO = (250, 170)
COORD_NAME = (600, 185)
COORD_TAG = (600, 305)
COORD_TEXT = (250, 510)
LINE_MARGIN = 15


@app.task(name="populate_user_by_id")
def populate_user_data_from_twitter_id(twitter_id, client_account_id=None):
    current_user = get_twitter_account(twitter_id, client_account_id)
    refresh_twitter_account(twitter_id, client_account_id)
    if client_account_id:
        get_users_following_for_client_account.delay(client_account_id)
        get_followers_for_client_account.delay(client_account_id)
        current_user.last_checked = utc.localize(datetime.now())
        current_user.save()


@app.task(name="get_tweet_info")
def lookup_tweet(tweet_id, client_account_id=None):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        tweet = twitter_api.lookup_tweet(tweet_id, token=client_account.token)
    else:
        tweet = twitter_api.lookup_tweet_as_admin(tweet_id)
    tweet_object = Tweet.objects.filter(tweet_id=tweet_id).first()
    tweet_object.message = tweet.text
    author = TwitterAccount.objects.filter(twitter_id=tweet.author_id)
    if not author:
        author = TwitterAccount()
        author.twitter_id = tweet.author_id
        author.save()
        populate_user_data_from_twitter_id.delay(tweet.author_id, client_account_id)
    tweet_object.author = author
    tweet_object.tweet_created_at = tweet.created_at


@app.task(name="user_engagement")
def fetch_user_engagement(twitter_id, client_account_id):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        tweets = twitter_api.get_recent_tweets(twitter_id=twitter_id, token=client_account.token)
    else:
        tweets = twitter_api.get_recent_tweets_as_admin(twitter_id=twitter_id)

    for tweet in tweets:
        saved_tweet = Tweet.objects.filter(tweet_id=tweet.id).first()
        if not saved_tweet:
            saved_tweet = Tweet()
            saved_tweet.tweet_id = tweet.id
            saved_tweet.message = tweet.text
            saved_tweet.tweet_created_at = tweet.created_at


@app.task(name="create_screenshot_from_tweet")
def create_screenshot(tweet_id):
    tweet_pik = TweetPik()
    tweet_pik.create_image(tweet_id=tweet_id)


@app.task(name="get_followers_for_client_account")
def get_followers_for_client_account(client_account_id):
    client_account = ClientAccount.objects.get(id=client_account_id)
    update_twitter_accounts_user_is_following(twitter_id=client_account.twitter_account.twitter_id,
                                              client_account_id=client_account_id)


@app.task(name="get_users_following_client_account")
def get_users_following_for_client_account(client_account_id):
    client_account = ClientAccount.objects.get(id=client_account_id)
    update_users_following_twitter_account(twitter_id=client_account.twitter_account.twitter_id,
                                           client_account_id=client_account_id)


@app.task(name="get_followers_for_twitter_account")
def get_followers_for_twitter_account(twitter_id):
    twitter_api = TwitterAPI()
    current_user = TwitterAccount.objects.get(twitter_id=twitter_id)
    if not current_user:
        current_user = TwitterAccount()
        current_user.twitter_id = twitter_id
    followers = twitter_api.get_following_for_user(twitter_id=twitter_id)

    for user in followers:
        twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=user.id, twitter_username=user.username,
                                             twitter_name=user.name
                                             )
            twitter_account.save()
        relationship = TwitterAccount.objects.filter(twitter_id=current_user.twitter_id,
                                                     following__twitter_id=twitter_account.twitter_id).first()
        if not relationship:
            current_user.following.add(twitter_account)


@app.task(name="get_users_following_twitter_account")
def get_users_following(twitter_id):
    twitter_api = TwitterAPI()
    current_user = get_twitter_account(twitter_id)
    followers = twitter_api.get_users_following_account_as_admin(client_account_id=client_account_id)

    for user in followers:
        twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
        if not twitter_account:
            twitter_account = TwitterAccount(twitter_id=user.id, twitter_username=user.username,
                                             twitter_name=user.name
                                             )
            twitter_account.save()
        relationship = TwitterAccount.objects.filter(twitter_id=twitter_account.twitter_id,
                                                     following__twitter_id=current_user.twitter_id).first()
        if not relationship:
            twitter_account.following.add(current_user)


@app.task(name="set_user_follows_account")
def make_user_follow_account(user_id, follows_id):
    relationship = TwitterAccount.objects.filter(twitter_id=user_id,
                                                 following__twitter_id=follows_id).first()
    if not relationship:
        current_user = TwitterAccount.objects.filter(twitter_id=user_id).first()
        twitter_account = TwitterAccount.objects.filter(twitter_id=follows_id).first()
        current_user.following.add(twitter_account)
        current_user.save()

@app.task(name="unfollow_user")
def unfollow_user_for_client_account(client_account_id, twitter_id_to_unfollow, request_id):
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    print(f"Unfollowing {twitter_id_to_unfollow}")
    unfollow_account(client_account_id, twitter_id_to_unfollow)
    current_user = TwitterAccount.objects.filter(twitter_id=client_account.twitter_account.twitter_id).first()
    user_to_unfollow = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    current_user.following.remove(user_to_unfollow)
    if (request_id):
        request = UnfollowRequest.objects.get(id=request_id)
        request.unfollowed = utc.localize(datetime.now())
        request.save()
