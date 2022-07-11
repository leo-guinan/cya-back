from datetime import datetime, timedelta

import tweepy
from decouple import config
import requests
import logging
import base64

from pytz import utc

from client.exception import UnknownClientAccount
from client.models import ClientAccount


class TwitterAPI:
    USER_FIELDS = "id,profile_image_url,name,description"
    TWEET_FIELDS = "public_metrics,entities,created_at,author_id"

    def __init__(self):
        self.api_key = config('TWITTER_API_KEY')
        self.api_secret = config('TWITTER_API_SECRET')
        self.client_id = config('TWITTER_CLIENT_ID')
        self.client_secret = config('TWITTER_CLIENT_SECRET')
        self.access_token = config('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = config('TWITTER_ACCESS_SECRET')
        self.oauth_callback_url = config('TWITTER_OAUTH_CALLBACK_URL')
        self.bearer_token = config('TWITTER_BEARER_TOKEN')

    def twitter_login(self):
        oauth1_user_handler = tweepy.OAuthHandler(self.api_key, self.api_secret, callback=self.oauth_callback_url)
        url = oauth1_user_handler.get_authorization_url(signin_with_twitter=True)
        request_token = oauth1_user_handler.request_token["oauth_token"]
        request_secret = oauth1_user_handler.request_token["oauth_token_secret"]
        return url, request_token, request_secret

    def twitter_callback(self, oauth_verifier, oauth_token, oauth_token_secret):
        oauth1_user_handler = tweepy.OAuthHandler(self.api_key, self.api_secret, callback=self.oauth_callback_url)
        oauth1_user_handler.request_token = {
            'oauth_token': oauth_token,
            'oauth_token_secret': oauth_token_secret
        }
        access_token, access_token_secret = oauth1_user_handler.get_access_token(oauth_verifier)
        return access_token, access_token_secret

    def get_me(self, access_token, access_token_secret):
        try:
            client = tweepy.Client(consumer_key=self.api_key, consumer_secret=self.api_secret,
                                   access_token=access_token,
                                   access_token_secret=access_token_secret)
            info = client.get_me(user_auth=True, expansions='pinned_tweet_id')
            return info
        except Exception as e:
            print(e)
            return None

    def search_tweets_since_tweet(self, search_term, starting_tweet):
        try:
            client = tweepy.Client(bearer_token=self.bearer_token)
            if starting_tweet != '0':
                tweets = client.search_recent_tweets(query=search_term, since_id=starting_tweet,
                                                     tweet_fields="created_at,text,author_id,id",
                                                     user_fields="public_metrics",
                                                     expansions="author_id")
            else:
                tweets = client.search_recent_tweets(query=search_term,
                                                     tweet_fields="created_at,text,author_id,id",
                                                     user_fields="public_metrics",
                                                     expansions="author_id")
            if (tweets.data):
                return [tweets.data, tweets.includes['users']]
            return [[], []]
        except Exception as e:
            print(e)
            return None

    def get_all_bookmarks(self, access_token, access_token_secret):
        client = tweepy.Client(consumer_key=self.api_key, consumer_secret=self.api_secret,
                               access_token=access_token,
                               access_token_secret=access_token_secret)
        results = client.get_bookmarks(tweet_fields="created_at,text,author_id,id",
                                       user_fields="public_metrics",
                                       expansions="author_id")
        bookmarks = results.data
        next_token = results.meta.get("next_token", "")

        while next_token:
            added_results = client.get_bookmarks(tweet_fields="created_at,text,author_id,id",
                                                 user_fields="public_metrics",
                                                 expansions="author_id",
                                                 pagination_token=next_token
                                                 )
            bookmarks.extend(added_results.data)
            next_token = added_results.meta.get("next_token", "")

        return bookmarks

    def get_following_for_user(self, client_account_id):
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise UnknownClientAccount()
        twitter_id = client_account.twitter_account.twitter_id
        token = self.refresh_oauth2_token(client_account_id=client_account_id)
        client = tweepy.Client(token,
                               wait_on_rate_limit=True)
        results = client.get_users_following(id=twitter_id, max_results=1000)
        following = results.data
        next_token = results.meta.get("next_token", "")
        while next_token:
            added_following = client.get_users_following(id=twitter_id, max_results=1000, pagination_token=next_token)
            following.extend(added_following.data)
            next_token = added_following.meta.get("next_token", "")

        print(f'found {len(following)} users that {twitter_id} is following')
        return following

    def get_following_for_user_admin(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token,
                               wait_on_rate_limit=True)
        results = client.get_users_following(id=twitter_id, max_results=1000)
        following = results.data
        next_token = results.meta.get("next_token", "")
        while next_token:
            added_following = client.get_users_following(id=twitter_id, max_results=1000, pagination_token=next_token)
            following.extend(added_following.data)
            next_token = added_following.meta.get("next_token", "")

        print(f'found {len(following)} users that {twitter_id} is following')
        return following

    def get_followers_for_user_admin(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token,
                               wait_on_rate_limit=True)
        results = client.get_users_followers(id=twitter_id, max_results=1000)
        followers = results.data
        next_token = results.meta.get("next_token", "")
        while next_token:
            added_following = client.get_users_followers(id=twitter_id, max_results=1000, pagination_token=next_token)
            followers.extend(added_following.data)
            next_token = added_following.meta.get("next_token", "")

        print(f'found {len(followers)} users that follow {twitter_id}')
        return followers

    def get_most_recent_tweet_for_user(self, client_account_id, twitter_id):
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise UnknownClientAccount()
        token = self.refresh_oauth2_token(client_account_id=client_account_id)
        client = tweepy.Client(token, wait_on_rate_limit=False)
        next_token = ''
        print(f'checking user: {twitter_id}')
        results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                          max_results=10)
        while not results.data and results.meta.get(next_token, ""):
            print(f'rechecking user: {twitter_id}, results: {results}')
            results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                              max_results=10, pagination_token=next_token)

        return results.data[0] if results.data else None

    def get_most_recent_tweet_for_user_as_admin(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        next_token = ''
        print(f'checking user: {twitter_id}')
        results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                          max_results=10)
        while not results.data and results.meta.get(next_token, ""):
            print(f'rechecking user: {twitter_id}, results: {results}')
            results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                              max_results=10, pagination_token=next_token)

        return results.data[0] if results.data else None

    def lookup_user_as_admin(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(id=twitter_id, user_fields=self.USER_FIELDS)
        return user.data

    def lookup_user(self, twitter_id, client_account_id):
        token = self.refresh_oauth2_token(client_account_id=client_account_id)
        client = tweepy.Client(token)
        user = client.get_user(id=twitter_id, user_fields=self.USER_FIELDS)
        return user.data

    def lookup_user_by_username_as_admin(self, username):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(username=username, user_fields=self.USER_FIELDS)
        return user.data

    def lookup_user_by_username(self, username, token):
        client = tweepy.Client(token)
        user = client.get_user(username=username, user_fields=self.USER_FIELDS)
        return user.data

    def get_number_of_accounts_followed_by_account(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(id=twitter_id, user_fields="public_metrics")
        return user.data.public_metrics['following_count']

    def unfollow_user(self, client_account_id, twitter_id_to_unfollow):
        token = self.refresh_oauth2_token(client_account_id)
        client = tweepy.Client(token)
        client.unfollow_user(twitter_id_to_unfollow, user_auth=False)

    def get_responses_to_tweet(self, tweet_id, since_id=None):
        client = tweepy.Client(bearer_token=self.bearer_token)
        last_lookup = since_id
        if not last_lookup:
            last_lookup = tweet_id
        responses = client.search_recent_tweets(query=f'conversation_id:{tweet_id}',
                                                since_id=last_lookup,
                                                tweet_fields="author_id", max_results=100, expansions="author_id",
                                                user_fields=self.USER_FIELDS)
        return responses

    def get_responses_to_prompt_in_conversation(self, tweet_id, since_id=None):
        client = tweepy.Client(bearer_token=self.bearer_token)
        last_lookup = since_id
        if not last_lookup:
            last_lookup = tweet_id
        responses = client.search_recent_tweets(
            query=f'conversation_id:{tweet_id} to:feathercrm -from:feathercrm is:reply', since_id=last_lookup,
            tweet_fields="author_id", max_results=100)
        return responses

    def reply_to_tweet(self, message, tweet_id_to_reply_to):
        client = tweepy.Client(consumer_key=self.api_key, consumer_secret=self.api_secret,
                               access_token=self.access_token,
                               access_token_secret=self.access_token_secret)
        response = client.create_tweet(text=message, in_reply_to_tweet_id=tweet_id_to_reply_to, user_auth=True)
        return response.data

    def get_retweets(self, tweet_id, token):
        client = tweepy.Client(token)
        response = client.get_retweeters(id=tweet_id)
        return response.data

    def get_likes(self, tweet_id, token):
        client = tweepy.Client(token)
        response = client.get_liking_users(id=tweet_id)
        return response.data

    def get_retweets_as_admin(self, tweet_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        response = client.get_retweeters(id=tweet_id)
        return response.data

    def get_likes_as_admin(self, tweet_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        response = client.get_liking_users(id=tweet_id)
        return response.data

    def lookup_tweet(self, tweet_id, token):
        client = tweepy.Client(token)
        response = client.get_tweet(id=tweet_id, tweet_fields=["public_metrics", "entities", "created_at", "author_id"])
        return response.data

    def lookup_tweet_as_admin(self, tweet_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        response = client.get_tweet(id=tweet_id, tweet_fields=["public_metrics", "entities", "created_at", "author_id"])
        return response.data

    def get_recent_tweets_as_admin(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        response = client.search_recent_tweets(query=f"from:{twitter_id}", max_results=10,
                                               tweet_fields=self.TWEET_FIELDS)
        return response.data

    def get_recent_tweets(self, twitter_id, token):
        client = tweepy.Client(token)
        response = client.search_recent_tweets(query=f"from:{twitter_id}", max_results=10,
                                               tweet_fields=self.TWEET_FIELDS)
        return response.data

    def send_tweet(self, message):
        client = tweepy.Client(consumer_key=self.api_key, consumer_secret=self.api_secret,
                               access_token=self.access_token,
                               access_token_secret=self.access_token_secret)
        response = client.create_tweet(text=message, user_auth=True)
        return response.data

    def refresh_oauth2_token(self, client_account_id):
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        print(client_account.refreshed)
        print(utc.localize(datetime.now() - timedelta(minutes=90)))
        if client_account.refreshed >= utc.localize(datetime.now() - timedelta(minutes=90)):
            return client_account.token
        if not client_account:
            raise UnknownClientAccount()
        client = client_account.client
        url = 'https://api.twitter.com/2/oauth2/token'
        myobj = {
            'refresh_token': client_account.refresh_token,
            "grant_type": "refresh_token",
            "client_id": client.client_id
        }
        response = requests.post(url, data=myobj, auth=(client.client_id, client.client_secret))
        results = response.json()
        print(results)
        client_account.access_token = results['access_token']
        client_account.refresh_token = results['refresh_token']
        client_account.refreshed=datetime.now()
        client_account.save()
        return results["access_token"]


