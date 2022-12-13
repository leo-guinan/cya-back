import datetime

import requests
import tweepy
from decouple import config
from django.utils import timezone

from client.exception import UnknownClientAccount
from client.models import ClientAccount, Client, StaffAccount


class TwitterAPI:
    USER_FIELDS = "id,profile_image_url,name,description,protected"
    TWEET_FIELDS = "public_metrics,entities,created_at,author_id,conversation_id"

    def __init__(self, client=None):
        self.oauth_callback_url = config('TWITTER_OAUTH_CALLBACK_URL')
        if not client:
            self.api_key = config('TWITTER_API_KEY')
            self.api_secret = config('TWITTER_API_SECRET')
            self.client_id = config('TWITTER_CLIENT_ID')
            self.client_secret = config('TWITTER_CLIENT_SECRET')
            self.access_token = config('TWITTER_ACCESS_TOKEN')
            self.access_token_secret = config('TWITTER_ACCESS_SECRET')
            self.bearer_token = config('TWITTER_BEARER_TOKEN')
        else:
            self.api_key = client.consumer_key
            self.api_secret = client.consumer_secret
            self.client_id = client.client_id
            self.client_secret = client.client_secret
            self.access_token = client.access_token
            self.access_token_secret = client.access_secret
            self.bearer_token = client.bearer_token

    def get_all_bookmarks(self, access_token, access_token_secret):
        """Get all Twitter bookmarks for a given user"""
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

    def get_following_for_user(self, twitter_id, client_account_id):
        """Get the accounts a given Twitter user is following"""
        client, user_auth = self.get_client_for_account(client_account_id)
        results = client.get_users_following(id=twitter_id, max_results=1000, user_auth=user_auth)
        following = results.data
        next_token = results.meta.get("next_token", "")
        while next_token:
            added_following = client.get_users_following(id=twitter_id, max_results=1000, pagination_token=next_token,
                                                         user_auth=user_auth)
            following.extend(added_following.data)
            next_token = added_following.meta.get("next_token", "")

        print(f'found {len(following)} users that {twitter_id} is following')
        return following

    def get_users_following_account(self, twitter_id, client_account_id):
        """Get the users following a given Twitter account"""
        client, user_auth = self.get_client_for_account(client_account_id)

        results = client.get_users_followers(id=twitter_id, max_results=1000, user_auth=user_auth)
        followers = results.data
        next_token = results.meta.get("next_token", "")
        while next_token:
            added_following = client.get_users_followers(id=twitter_id, max_results=1000, pagination_token=next_token,
                                                         user_auth=user_auth)
            followers.extend(added_following.data)
            next_token = added_following.meta.get("next_token", "")

        print(f'found {len(followers)} users following {twitter_id}')
        return followers

    def get_most_recent_tweet_for_user(self, twitter_id, client_account_id=None, staff_account=False):
        """Get the most recent tweet for a given user."""
        client, user_auth = self.get_client_for_account(client_account_id, staff_account=staff_account)
        next_token = ''
        print(f'checking user: {twitter_id}')
        if client_account_id:
            print(f"for client account: {client_account_id}")
        results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                          user_fields=self.USER_FIELDS,
                                          expansions="author_id",
                                          max_results=5, user_auth=user_auth)
        while not results.data and results.meta.get(next_token, ""):
            print(f'rechecking user: {twitter_id}, results: {results}')
            results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                              user_fields=self.USER_FIELDS,
                                              expansions="author_id",
                                              max_results=5, pagination_token=next_token, user_auth=user_auth)
        if results.data and results.data[0]:
            print(f"{len(results.data)} results found")
            tweet = results.data[0]
            author = results.includes['users'][0] if results.includes["users"][0] else None
            return tweet, author
        print("No tweets found")
        return None, None

    def lookup_user(self, twitter_id, client_account_id=None, staff_account=False):
        """Get the account information for a given Twitter account"""
        client, user_auth = self.get_client_for_account(client_account_id, staff_account=staff_account)
        user = client.get_user(id=twitter_id, user_fields=self.USER_FIELDS, user_auth=user_auth)
        return user.data

    def get_number_of_accounts_followed_by_account(self, twitter_id):
        """Get a count of the number of accounts a given twitter account is following"""
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(id=twitter_id, user_fields="public_metrics")
        return user.data.public_metrics['following_count']

    def unfollow_user(self, client_account_id, twitter_id_to_unfollow):
        """For the specificied client account, unfollow the passed in twitter account."""
        client, user_auth = self.get_client_for_account(client_account_id)
        try:
            response = client.unfollow_user(twitter_id_to_unfollow, user_auth=user_auth)
            print(response)
        except Exception as e:
            print(e)
            raise e

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

    def send_tweet(self, message):
        client = tweepy.Client(consumer_key=self.api_key, consumer_secret=self.api_secret,
                               access_token=self.access_token,
                               access_token_secret=self.access_token_secret)
        response = client.create_tweet(text=message, user_auth=True)
        return response.data

    def send_tweet_as_client(self, app_client, message):
        client = tweepy.Client(consumer_key=app_client.consumer_key, consumer_secret=app_client.consumer_secret,
                               access_token=app_client.access_token,
                               access_token_secret=app_client.access_secret)
        response = client.create_tweet(text=message, user_auth=True)
        return response.data

    def send_tweet_as_client_in_response(self, client_id, tweet_to_respond_to, message):
        app_client = Client.objects.filter(id=client_id).first()
        client = tweepy.Client(consumer_key=app_client.consumer_key, consumer_secret=app_client.consumer_secret,
                               access_token=app_client.access_token,
                               access_token_secret=app_client.access_secret)
        response = client.create_tweet(text=message, in_reply_to_tweet_id=tweet_to_respond_to, user_auth=True)
        return response.data

    def send_dm_to_user(self, client_id, twitter_user_to_message, message):
        client = Client.objects.filter(id=client_id).first()
        auth = tweepy.OAuth1UserHandler(
            client.consumer_key, client.consumer_secret,
            client.access_token, client.access_secret
        )
        api = tweepy.API(auth)
        api.send_direct_message(twitter_user_to_message, text=message)

    def get_latest_mentions(self, client_id, since):
        app_client = Client.objects.filter(id=client_id).first()
        client = tweepy.Client(bearer_token=app_client.bearer_token)
        mentions = client.get_users_mentions(id=app_client.twitter_account.twitter_id,
                                             since_id=since,
                                             tweet_fields="author_id,created_at,conversation_id",
                                             max_results=50) if since else client.get_users_mentions(
            id=app_client.twitter_account.twitter_id, tweet_fields="author_id,created_at,conversation_id",
            max_results=50)
        return mentions.data if mentions.data else None

    def get_latest_tweets(self, twitter_id, since_tweet_id=None, client_account_id=None, staff_account=False):
        start_time = (datetime.datetime.now() - datetime.timedelta(days=7))
        client, user_auth = self.get_client_for_account(client_account_id, staff_account=staff_account)
        tweets = []
        raw_data = []
        if since_tweet_id:
            response = client.get_users_tweets(id=twitter_id,
                                               exclude="retweets,replies", since_id=since_tweet_id,
                                               expansions="attachments.media_keys",
                                               media_fields="media_key,type,url,height,width",
                                               tweet_fields=self.TWEET_FIELDS,
                                               max_results=100,
                                               start_time=start_time,
                                               user_auth=user_auth)
            tweets = response.data
            raw_data = [response]
            next_token = response.meta.get("next_token", "")
            while next_token:
                added_tweets = client.get_users_tweets(id=twitter_id,
                                                       exclude="retweets,replies",
                                                       since_id=since_tweet_id,
                                                       expansions="attachments.media_keys",
                                                       media_fields="media_key,type,url,height,width",
                                                       tweet_fields=self.TWEET_FIELDS,
                                                       user_auth=user_auth,
                                                       max_results=100,
                                                       start_time=start_time,
                                                       pagination_token=next_token)
                tweets.extend(added_tweets.data)
                raw_data.extend(added_tweets)
                next_token = added_tweets.meta.get("next_token", "")
        else:
            response = client.get_users_tweets(id=twitter_id,
                                               exclude="retweets,replies",
                                               tweet_fields=self.TWEET_FIELDS,
                                               expansions="attachments.media_keys",
                                               media_fields="media_key,type,url,height,width",
                                               max_results=100,
                                               start_time=start_time,
                                               user_auth=user_auth)
            tweets = response.data
            raw_data = [response]
            next_token = response.meta.get("next_token", "")
            while next_token:
                added_tweets = client.get_users_tweets(id=twitter_id,
                                                       exclude="retweets,replies",
                                                       tweet_fields=self.TWEET_FIELDS,
                                                       expansions="attachments.media_keys",
                                                       media_fields="media_key,type,url,height,width",
                                                       max_results=100,
                                                       start_time=start_time,
                                                       user_auth=user_auth,
                                                       pagination_token=next_token)
                tweets.extend(added_tweets.data)
                raw_data.extend(added_tweets)
                next_token = added_tweets.meta.get("next_token", "")
        return tweets, raw_data

    def get_bio_and_recent_tweets_for_account(self, twitter_id, number_of_tweets=25, exclude_fields="replies,retweets",
                                              client_account_id=None, staff_account=False, refresh=False):
        client, user_auth = self.get_client_for_account(client_account_id, staff_account=staff_account, refresh=refresh)
        try:
            response = client.get_users_tweets(id=twitter_id,
                                               exclude=exclude_fields,
                                               expansions="attachments.media_keys,author_id",
                                               media_fields="media_key,type,url,height,width",
                                               tweet_fields=self.TWEET_FIELDS,
                                               user_fields=self.USER_FIELDS,
                                               max_results=number_of_tweets,
                                               user_auth=user_auth)

            tweets = response.data if response.data else []
            user = response.includes['users'][0] if response.includes.get('users') else {}
            return tweets, user
        except Exception as e:
            print(e)
            print("Attempting token refresh")
            return self.get_bio_and_recent_tweets_for_account(twitter_id, number_of_tweets=number_of_tweets,
                                                              exclude_fields=exclude_fields,
                                                              client_account_id=client_account_id,
                                                              staff_account=staff_account, refresh=True)

    def get_tweet(self, tweet_id, client_account_id=None, staff_account=False):
        client, user_auth = self.get_client_for_account(client_account_id, staff_account=staff_account)
        response = client.get_tweet(id=tweet_id, tweet_fields=self.TWEET_FIELDS, user_auth=user_auth)
        return response.data

    def refresh_oauth2_token(self, client_account_id):
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        client = client_account.client
        url = 'https://api.twitter.com/2/oauth2/token'
        myobj = {
            'refresh_token': client_account.refresh_token,
            "grant_type": "refresh_token",
            "client_id": client.client_id
        }
        response = requests.post(url, data=myobj, auth=(client.client_id, client.client_secret))
        results = response.json()
        client_account.access_token = results['access_token']
        client_account.refresh_token = results['refresh_token']
        client_account.refreshed = timezone.now()
        client_account.save()
        return results['access_token']

    def get_client_for_account(self, client_account_id, staff_account=False, refresh=False):
        user_auth = False
        if not client_account_id:
            client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=False)
            return client, user_auth
        if not staff_account:
            client_account = ClientAccount.objects.filter(id=client_account_id).first()
        else:
            client_account = StaffAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise UnknownClientAccount()
        if client_account.client.auth_version == "V2":

            if refresh:
                token = self.refresh_oauth2_token(client_account_id)
            else:
                token = client_account.access_token
            client = tweepy.Client(token,
                                   wait_on_rate_limit=True)
        else:
            client = tweepy.Client(consumer_key=client_account.client.consumer_key,
                                   consumer_secret=client_account.client.consumer_secret,
                                   access_token=client_account.access_key,
                                   access_token_secret=client_account.secret_access_key, )
            print("Using V1 User auth client")

            user_auth = True
        return client, user_auth
