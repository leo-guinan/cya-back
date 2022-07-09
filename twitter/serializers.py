from rest_framework import serializers


class TwitterAccountSerializer(serializers.Serializer):
    twitter_id = serializers.CharField(max_length=512)
    twitter_username = serializers.CharField(max_length=255)
    twitter_name = serializers.CharField(max_length=255)
    last_tweet_date = serializers.DateTimeField()

