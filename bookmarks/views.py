import json
import tweepy
import pandas as pd
from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from bookmarks.models import Bookmark
from bookmarks.serializers import BookmarkSerializer
from twitter.models import TwitterAccount, AccountError, Tweet, IncludedLink
from twitter.service import get_twitter_account


def create_link(username, tweet_id):
    return f'https://twitter.com/{username}/status/{tweet_id}'



def save_tweet_to_database(raw_tweet, bookmarking_user_twitter_id):
    author = get_twitter_account(raw_tweet['author_id'])
    tweet = Tweet.objects.filter(tweet_id=raw_tweet['tweet_id']).first()
    if not tweet:

        tweet = Tweet()
        tweet.tweet_id = raw_tweet['tweet_id']
        tweet.tweet_created_at = raw_tweet['created_at']
        tweet.author = author
        tweet.message = raw_tweet['text']
        tweet.save()

        if raw_tweet['external_links']:
            for link in raw_tweet['external_links']:
                external_link = IncludedLink()
                external_link.includingTweet = tweet
                external_link.link = link['url']
                external_link.title = link['title']
                external_link.original_image_url = link['original_image']
                external_link.thumbnail_image_url = link['thumbnail_image']
                external_link.save()

    bookmarking_user = get_twitter_account(bookmarking_user_twitter_id)
    bookmark = Bookmark.objects.filter(tweet=tweet, owner=bookmarking_user).first()
    if not bookmark:
        bookmark = Bookmark()
        bookmark.tweet = tweet
        bookmark.link = raw_tweet['link']
        bookmark.owner = bookmarking_user
        bookmark.save()
    return bookmark


def has_external_link(row):
    entities = row['entities']
    urls = []
    if not entities:
        return
    for key,value in entities.items():
        if key == 'urls':
            for url in value:
                url_object = {
                    'url': url.get('expanded_url', ""),
                    'title': url.get('title', ""),
                    'original_image': url.get('images', [""])[0],
                    'thumbnail_image': url.get('images', ["", ""])[1]
                }
                urls.append(url_object)
    return urls


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_bookmarks_for_user(request):
    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    token = body['twitter_token']

    client = tweepy.Client(token)
    bookmarks = client.get_bookmarks(
        expansions='author_id',
        tweet_fields="id,text,author_id,created_at,referenced_tweets,source,public_metrics,entities,geo,context_annotations",
        user_fields="name,username,description"
    )
    results = []

    users = []


    for user in bookmarks.includes.get('users', []):
        user_data = {
            'twitter_id': user.id,
            'name': user.name,
            'username': user.username,
            'bio': user.description,
        }
        users.append(user_data)

    for tweet in bookmarks.data:
        tweet_data = {
            'author_id': tweet.author_id,
            'tweet_id': tweet.id,
            'created_at': tweet.created_at,
            'text': tweet.text,
            'source': tweet.source,
            'entities': tweet.entities,
            'context_annotations': tweet.context_annotations,
            'geo': tweet.geo,
            'public_metrics': tweet.public_metrics,
            'referenced_tweets': tweet.referenced_tweets,
        }
        tweet_data['link'] = create_link(next(item for item in users if item["twitter_id"] == tweet_data['author_id'])['username'], tweet_data['tweet_id'])
        tweet_data['external_links'] = has_external_link(tweet_data)
        bookmark = save_tweet_to_database(tweet_data, twitter_id)
        serializer = BookmarkSerializer(bookmark)
        results.append(serializer.data)

    return Response(results)

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def update_bookmark_name(request):
    body = json.loads(request.body)
    twitter_id = body['twitter_id']
    tweet_id = body['tweet_id']
    name = body['name']
    tweet = Tweet.objects.filter(tweet_id=tweet_id).first()
    if not tweet:
        return Response({'error': 'Tweet not found'})
    bookmarking_user = get_twitter_account(twitter_id)
    if not bookmarking_user:
        return Response({'error': 'User not found'})
    bookmark = Bookmark.objects.filter(tweet=tweet, owner=bookmarking_user).first()
    if not bookmark:
        return Response({'error': 'Bookmark not found'})
    bookmark.name = name
    bookmark.save()
    serializer = BookmarkSerializer(bookmark)
    return Response(serializer.data)
