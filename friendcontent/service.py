import random
from datetime import date, datetime, timedelta
from pytz import utc

from client.models import Client
from friendcontent.models import TriggerTweet, Content
from friendcontent.util import extract_url_from_text
from twitter.models import Tweet, Relationship
from twitter.service import refresh_twitter_account, update_twitter_accounts_user_is_following
from twitter_api.twitter_api import TwitterAPI

CLIENT = Client.objects.filter(name="FRIENDCONTENT").first()

def respond_to_add(trigger, client):
    twitter_api = TwitterAPI()
    trigger.action = "ADD"
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"what kind of media would you like to add? Currently supported types: podcast, blog, tiktok, youtube. Please respond with a type.")
    _save_trigger(response, trigger, client)


def respond_to_add_podcast(trigger, client):
    twitter_api = TwitterAPI()
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"Awesome! What's the url of the podcast?")
    _save_trigger(response, trigger, client)


def respond_to_add_blog(trigger, client):
    twitter_api = TwitterAPI()
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"Awesome! What's the url of the podcast?")
    _save_trigger(response, trigger, client)


def respond_to_add_youtube(trigger, client):
    twitter_api = TwitterAPI()
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"Awesome! What's the url of the podcast?")
    _save_trigger(response, trigger, client)


def respond_to_add_tiktok(trigger, client):
    twitter_api = TwitterAPI()
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"Awesome! What's the url of the podcast?")
    _save_trigger(response, trigger, client)


def add_podcast(mention, author, trigger, client):
    twitter_api = TwitterAPI()
    content = Content()
    print(mention.text)
    url = extract_url_from_text(mention.text)
    content.url = url
    content.content_type = 'PC'
    content.owner = author
    content.save()
    twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                 tweet_to_respond_to=trigger.tweet.tweet_id,
                                                 message=f"Excellent! Your podcast has been saved!")


def add_blog(mention, author, trigger, client):
    twitter_api = TwitterAPI()
    content = Content()
    print(mention.text)
    url = extract_url_from_text(mention.text)
    content.url = url
    content.content_type = 'BL'
    content.owner = author
    content.save()
    twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                 tweet_to_respond_to=trigger.tweet.tweet_id,
                                                 message=f"Excellent! Your blog has been saved!")


def add_youtube(mention, author, trigger, client):
    twitter_api = TwitterAPI()
    content = Content()
    print(mention.text)
    url = extract_url_from_text(mention.text)
    content.url = url
    content.content_type = 'YT'
    content.owner = author
    content.save()
    twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                 tweet_to_respond_to=trigger.tweet.tweet_id,
                                                 message=f"Excellent! Your youtube has been saved!")


def add_tiktok(mention, author, trigger, client):
    twitter_api = TwitterAPI()
    content = Content()
    print(mention.text)
    url = extract_url_from_text(mention.text)
    content.url = url
    content.content_type = 'TT'
    content.owner = author
    content.save()
    twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                 tweet_to_respond_to=trigger.tweet.tweet_id,
                                                 message=f"Excellent! Your tiktok has been saved!")


def respond_to_podcast(author, trigger, client):
    _find_content_matching_type_in_network(author, 'PC', trigger, client)


def respond_to_blog(author, trigger, client):
    _find_content_matching_type_in_network(author, 'BL', trigger, client)


def respond_to_youtube(author, trigger, client):
    _find_content_matching_type_in_network(author, 'YT', trigger, client)


def respond_to_tiktok(author, trigger, client):
    _find_content_matching_type_in_network(author, 'TT', trigger, client)

def respond_with_help(trigger, client):
    twitter_api = TwitterAPI()
    response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                            tweet_to_respond_to=trigger.tweet.tweet_id,
                                                            message=f"""User Guide for @friend_content

To add content to our database, tweet '@friend_content add' and respond to the prompts. 

To request a content recommendation from your network, use '@friend_content $TYPE'. 

Current types supported: podcast, blog, tiktok, youtube""")
    _save_trigger(response, trigger, client)

def _save_trigger(response, trigger, client):
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


def _find_content_matching_type_in_network(author, content_type, trigger, client):
    # get all users in authors social network
    # get all content of type belonging to users in that network
    # pick random content from that group
    # send tweet
    twitter_api = TwitterAPI()
    if not author.last_checked or author.last_checked < (date.today() - timedelta(days=2)):
        # lookup user
        refresh_twitter_account(author.twitter_id)
        update_twitter_accounts_user_is_following(author.twitter_id, client=CLIENT)

        author.last_checked = utc.localize(datetime.now())
        author.save()
    following = Relationship.objects.filter(this_account=author).all()
    following_accounts = [follow.follows_this_account for follow in following]
    content_options = Content.objects.filter(content_type=content_type, owner__in=following_accounts).all()
    if len(content_options) > 0:
        item = random.choice(content_options)
        response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                                tweet_to_respond_to=trigger.tweet.tweet_id,
                                                                message=f"Here you go! From @{item.owner.twitter_username}: {item.url}")

    else:
        response = twitter_api.send_tweet_as_client_in_response(client_id=client.id,
                                                                tweet_to_respond_to=trigger.tweet.tweet_id,
                                                                message=f"Unfortunately, we don't have any content from anyone you are following. Spread the word and help people in your network find us!")
    _save_trigger(response, trigger, client)
