from datetime import date, datetime, timedelta
from pytz import utc

from backend.celery import app
from client.exception import UnknownClient
from client.models import Client
from friendcontent.models import TriggerTweet, Content
from friendcontent.service import respond_to_add, respond_to_add_podcast, add_podcast, respond_to_add_blog, \
    respond_to_add_youtube, respond_to_add_tiktok, add_blog, add_youtube, add_tiktok, respond_to_podcast, \
    respond_to_blog, respond_to_youtube, respond_to_tiktok, respond_with_help
from twitter.models import Tweet, TwitterAccount
from twitter.service import refresh_twitter_account, update_twitter_accounts_user_is_following, \
    update_users_following_twitter_account
from twitter.tasks import populate_user_data_from_twitter_id, get_users_following_for_client_account
from twitter_api.twitter_api import TwitterAPI

SUPPORTED_MEDIA = {
    'podcast': {

    },
    'blog': {

    },
    'youtube': {

    },
    'tiktok': {

    }
}


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
            print(mention.id)
            if mention.id == mention.conversation_id:
                print("parent response, new conversation")
                # this is a new request. Act accordingly.
                if 'add' in mention.text.lower():
                    respond_to_add(trigger, client)
                elif 'podcast' in mention.text.lower():
                    respond_to_podcast(author, trigger, client)
                elif 'blog' in mention.text.lower():
                    respond_to_blog(author, trigger, client)
                elif 'youtube' in mention.text.lower():
                    respond_to_youtube(author, trigger, client)
                elif 'tiktok' in mention.text.lower():
                    respond_to_tiktok(author, trigger, client)
                else:
                    trigger.action = "unknown"
                    respond_with_help(trigger, client)
                trigger.save()
            else:
                parent = TriggerTweet.objects.filter(tweet__tweet_id=mention.conversation_id).first()
                if not parent:
                    continue
                root = parent
                while parent.child:
                    #Get latest response
                    parent = parent.child
                print("child response")
                if 'podcast' in mention.text.lower():
                    trigger.action = 'PODCAST'
                elif 'blog' in mention.text.lower():
                    trigger.action = 'BLOG'
                elif 'youtube' in mention.text.lower():
                    trigger.action = 'YOUTUBE'
                elif 'tiktok' in mention.text.lower():
                    trigger.action = 'TIKTOK'
                else:
                    trigger.action = "unknown"
                trigger.taken = True
                trigger.save()
                parent.child = trigger
                parent.save()
                if parent.action == 'ADD':
                    if trigger.action == 'PODCAST':
                        respond_to_add_podcast(trigger, client)
                    elif trigger.action == 'BLOG':
                        respond_to_add_blog(trigger, client)
                    elif trigger.action == 'YOUTUBE':
                        respond_to_add_youtube(trigger, client)
                    elif trigger.action == 'TIKTOK':
                        respond_to_add_tiktok(trigger, client)
                if root.action == "ADD":
                    if parent.action == "PODCAST":
                        add_podcast(mention, author, trigger, client)
                    elif parent.action == 'BLOG':
                        add_blog(mention, author, trigger, client)
                    elif parent.action == 'YOUTUBE':
                        add_youtube(mention, author, trigger, client)
                    elif parent.action == 'TIKTOK':
                        add_tiktok(mention, author, trigger, client)




@app.task(name="process_tweets")
def process_tweets():
    twitter_api = TwitterAPI()
    triggers_to_process = TriggerTweet.objects.filter(taken=False).all()
    client = Client.objects.filter(name="FRIENDCONTENT").first()

    for trigger in triggers_to_process:
        if 'BLOG' in trigger.action:
            pass
        if 'PODCAST' in trigger.action:
            twitter_api.send_tweet_as_client_in_response(client_id=client.id, tweet_to_respond_to=trigger.tweet.tweet_id, message="Your friend @LobowSpark has a podcast: https://lobow.buzzsprout.com/")
            trigger.taken=True
            trigger.save()
        if 'ADD' in trigger.action:
            response = twitter_api.send_tweet_as_client_in_response(client_id=client.id, tweet_to_respond_to=trigger.tweet.tweet_id, message=f"@{trigger.tweet.author.twitter_username}: what kind of media would you like to add? Currently supported types: podcast")
            print(response)
            new_tweet = Tweet()
            new_tweet.tweet_id = response['id']
            new_tweet.message = response['text']
            new_tweet.author = client.twitter_account
            new_tweet.tweet_created_at = datetime.utcnow()
            new_tweet.save()
            new_trigger = TriggerTweet()
            new_trigger.tweet = new_tweet


            trigger.taken = True
            trigger.save()
