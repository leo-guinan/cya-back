from backend.celery import app
from client.models import ClientAccount
from twitter.models import TwitterAccount, Tweet, Retweet, Like
from twitter_api.twitter_api import TwitterAPI


@app.task(name="populate_user_by_username")
def populate_user_data_from_twitter_username(username, client_account_id=None):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        user = twitter_api.lookup_user_by_username(username=username, token=client_account.token)
    else:
        user = twitter_api.lookup_user_by_username_as_admin(username=username)
    twitter_account = TwitterAccount.objects.filter(twitter_id=user.id).first()
    if not twitter_account:
        twitter_account = TwitterAccount()
        twitter_account.twitter_id = user.id
    twitter_account.twitter_bio = user.description
    twitter_account.twitter_name = user.name
    twitter_account.twitter_username = user.username
    twitter_account.twitter_profile_picture_url = user.profile_image_url
    twitter_account.save()


@app.task(name="populate_user_by_id")
def populate_user_data_from_twitter_id(twitter_id, client_account_id=None):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        user = twitter_api.lookup_user(twitter_id=twitter_id, client_account_id=client_account_id)
    else:
        user = twitter_api.lookup_user_as_admin(twitter_id=twitter_id)
    twitter_account = TwitterAccount.objects.filter(twitter_id=twitter_id).first()
    if not twitter_account:
        twitter_account = TwitterAccount()
        twitter_account.twitter_id = user.id
    twitter_account.twitter_bio = user.description
    twitter_account.twitter_name = user.name
    twitter_account.twitter_username = user.username
    twitter_account.twitter_profile_picture_url = user.profile_image_url
    twitter_account.save()


@app.task(name="get_liking_users")
def fetch_liking_users(tweet_id, client_account_id=None):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        users = twitter_api.get_likes(tweet_id, client_account.token)
    else:
        users = twitter_api.get_likes_as_admin(tweet_id)

    tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
    if not tweet:
        tweet = Tweet()
        tweet.tweet_id = tweet_id
        tweet.save()
        lookup_tweet.delay(tweet_id, client_account_id)
    if users:
        for user in users:
            twitter_account = TwitterAccount.objects.filter(twitter_id=user.id)
            if not twitter_account:
                twitter_account = TwitterAccount()
                twitter_account.twitter_id = user.id
                twitter_account.save()
                populate_user_data_from_twitter_id.delay(user.id, client_account_id)
            like = Like.objects.filter(liking_account=twitter_account, tweet=tweet)
            if not like:
                like = Like(liking_account=twitter_account, tweet=tweet)
                like.save()


@app.task(name="get_retweeting_users")
def fetch_retweeting_users(tweet_id, client_account_id=None):
    twitter_api = TwitterAPI()
    if client_account_id:
        client_account = ClientAccount.objects.filter(id=client_account_id).first()
        if not client_account:
            raise Exception("unable to find client account")
        users = twitter_api.get_retweets(tweet_id, client_account.token)
    else:
        users = twitter_api.get_retweets_as_admin(tweet_id)

    tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
    if not tweet:
        tweet = Tweet()
        tweet.tweet_id = tweet_id
        tweet.save()
        lookup_tweet.delay(tweet_id, client_account_id)
    if users:
        for user in users:
            twitter_account = TwitterAccount.objects.filter(twitter_id=user.id)
            if not twitter_account:
                twitter_account = TwitterAccount()
                twitter_account.twitter_id = user.id
                twitter_account.save()
                populate_user_data_from_twitter_id.delay(user.id, client_account_id)
            retweet = Retweet.objects.filter(retweeting_account=twitter_account, tweet=tweet)
            if not retweet:
                retweet = Retweet(retweeting_account=twitter_account, tweet=tweet)
                retweet.save()


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

