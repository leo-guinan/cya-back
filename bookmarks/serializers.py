from rest_framework import serializers

from bookmarks.models import Bookmark
from twitter.serializers import TweetSerializer, TwitterAccountSerializer


class BookmarkSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer(many=False, read_only=True)
    owner = TwitterAccountSerializer(many=False, read_only=True)

    class Meta:
        model = Bookmark
        fields = ('tweet', 'owner', 'link', 'name')
