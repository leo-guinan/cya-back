import datetime

from backend.celery import app
from client.exception import UnknownClient
from client.models import Client
from friendcontent.models import TriggerTweet
from twitter.models import Tweet, TwitterAccount
from twitter_api.twitter_api import TwitterAPI


@app.task(name="handle_tweet")
def handle_tweet():
    twitter_api = TwitterAPI()
    client = Client.objects.filter(name="FRIENDCONTENT").first()
    if not client:
        raise UnknownClient()
    try:
        latest = TriggerTweet.objects.latest('added')
        mentions = twitter_api.get_latest_mentions(client.id, since=latest.tweet.tweet_id)

    except:
        latest = None
        mentions = twitter_api.get_latest_mentions(client.id, since=None)
    #if conversation_id === tweet_id, new thread started, no child. Else, should have a parent trigger with conversation id as trigger
    if mentions:
        for mention in mentions:
            print(mention.conversation_id)
            tweet = Tweet.objects.filter(tweet_id=mention.id).first()
            if not tweet:
                tweet = Tweet()
                tweet.tweet_id = mention.id
                author = TwitterAccount.objects.filter(twitter_id=mention.author_id).first()
                if not author:
                    author = TwitterAccount()
                    author.twitter_id = mention.author_id
                    author.save()
                tweet.author = author
                tweet.message = mention.text
                tweet.tweet_created_at = mention.created_at
                tweet.save()
            trigger = TriggerTweet()
            trigger.tweet = tweet
            if 'add' in mention.text.lower():
                trigger.action = "ADD"
            elif 'podcast' in mention.text.lower():
                trigger.action = 'PODCAST'
            else:
                trigger.action = "unknown"
            trigger.save()


@app.task(name="process_tweets")
def process_tweets():
    twitter_api = TwitterAPI()
    triggers_to_process = TriggerTweet.objects.filter(taken=False).all()
    client = Client.objects.filter(name="FRIENDCONTENT").first()

    for trigger in triggers_to_process:
        if 'blog' in trigger.action:
            pass
        if 'podcast' in trigger.action:
            twitter_api.send_tweet_as_client_in_response(client_id=client.id, tweet_to_respond_to=trigger.tweet.tweet_id, message="Your friend @LobowSpark has a podcast: https://lobow.buzzsprout.com/")
            trigger.taken=True
            trigger.save()
        if 'add' in trigger.action:
            response = twitter_api.send_tweet_as_client_in_response(client_id=client.id, tweet_to_respond_to=trigger.tweet.tweet_id, message=f"what kind of media would you like to add? Currently supported types: podcast")
            new_tweet = Tweet()
            new_tweet.tweet_id = response.id
            new_tweet.message = response.text
            new_tweet.author = client.twitter_account
            new_tweet.tweet_created_at = datetime.datetime.utcnow()
            new_tweet.save()
            print(response)
            new_trigger = TriggerTweet()
            new_trigger.tweet = new_tweet


            trigger.taken = True
            trigger.save()
