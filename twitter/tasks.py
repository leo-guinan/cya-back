from datetime import datetime

from PIL import ImageFont
from django.db.models import Q
from pytz import utc

from backend.celery import app
from client.exception import UnknownClientAccount
from client.models import ClientAccount, StaffAccount
from tweetpik.tweetpik import TweetPik
from twitter.models import TwitterAccount, Relationship
from twitter.service import refresh_twitter_account, get_twitter_account, unfollow_account, \
    update_twitter_accounts_user_is_following, \
    update_users_following_twitter_account, get_recent_tweets
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


@app.task(name="unfollow_user")
def unfollow_user_for_client_account(client_account_id, twitter_id_to_unfollow, request_id):
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    if not client_account:
        raise UnknownClientAccount()
    print(f"Unfollowing {twitter_id_to_unfollow}")
    unfollow_account(client_account_id, twitter_id_to_unfollow)
    current_user = TwitterAccount.objects.filter(twitter_id=client_account.twitter_account.twitter_id).first()
    user_to_unfollow = TwitterAccount.objects.filter(twitter_id=twitter_id_to_unfollow).first()
    relationship = Relationship.objects.filter(this_account=current_user, follows_this_account=user_to_unfollow).first()
    if relationship:
        relationship.delete()
    if request_id:
        request = UnfollowRequest.objects.get(id=request_id)
        request.unfollowed = utc.localize(datetime.now())
        request.save()


@app.task(name="get_latest_tweets")
def get_latest_tweets_for_account(client_account_id, twitter_id):
    client_account = ClientAccount.objects.filter(id=client_account_id).first()
    try:
        get_recent_tweets(client_account_id=client_account_id, twitter_id=twitter_id)
    except Exception as e:
        print(e)
        staff_accounts = StaffAccount.objects.filter(client=client_account.client).all()
        for staff_account in staff_accounts:
            try:
                get_recent_tweets(client_account_id=staff_account.id, twitter_id=twitter_id, staff_account=True)
                return
            except Exception as nested_e:
                print(nested_e)
                continue


@app.task(name="populate_account_data")
def lookup_accounts_that_are_missing_data():
    staff_accounts = StaffAccount.objects.all()
    current_staff_account = 0
    # limit on Twitter API is 900 requests per 15 minutes,
    # so target slightly less than that every 15 minutes for each of 5 staff accounts
    accounts = TwitterAccount.objects.filter(Q(twitter_username__isnull=True) | Q(twitter_bio__isnull=True)).all()[:4000]
    for account in accounts:
        try:
            refresh_twitter_account(account.twitter_id,
                                    client_account_id=staff_accounts[current_staff_account].id,
                                    staff_account=True)
        except:
            # move to next staff account
            if current_staff_account == len(staff_accounts) - 1:
                current_staff_account = 0
            else:
                current_staff_account += 1
            refresh_twitter_account(account.twitter_id,
                                    client_account_id=staff_accounts[current_staff_account].id,
                                    staff_account=True)
