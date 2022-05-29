import tweepy
from decouple import config
import json

class TwitterAPI:
    def __init__(self):
        self.api_key = config('TWITTER_API_KEY')
        self.api_secret = config('TWITTER_API_SECRET')
        self.client_id = config('TWITTER_CLIENT_ID')
        self.client_secret = config('TWITTER_CLIENT_SECRET')
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

    def get_following_for_user(self, twitter_id, token):
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

    def get_most_recent_tweet_for_user(self, twitter_id, token):
        client = tweepy.Client(token, wait_on_rate_limit=True)
        next_token = ''
        print(f'checking user: {twitter_id}')
        results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets", max_results=100)
        while not results.data and results.meta.get(next_token, ""):
            print(f'rechecking user: {twitter_id}, results: {results}')
            results = client.get_users_tweets(id=twitter_id, tweet_fields=["created_at"], exclude="replies,retweets",
                                              max_results=100, pagination_token=next_token)

        return results.data[0] if results.data else None

    def lookup_user(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(id=twitter_id)
        return user.data

    def get_number_of_accounts_followed_by_account(self, twitter_id):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=True)
        user = client.get_user(id=twitter_id, user_fields="public_metrics")
        return user.data.public_metrics['following_count']

    def unfollow_user(self, twitter_id_to_unfollow, token):
        client = tweepy.Client(token)
        client.unfollow_user(twitter_id_to_unfollow, user_auth=False)

