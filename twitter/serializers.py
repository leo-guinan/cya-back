from rest_framework import serializers

from twitter.models import TwitterAccount, Tweet


class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAccount
        fields = [
            'twitter_id',
            'twitter_username',
            'twitter_name',
            'twitter_bio',
            'twitter_profile_picture_url',
            'most_recent_tweet',
            'last_tweet_date',
        ]


class TwitterAccountSerializer(serializers.ModelSerializer):
    follows = FollowerSerializer(many=True, read_only=True)
    class Meta:
        model = TwitterAccount
        fields = [
            'twitter_id',
            'twitter_username',
            'twitter_name',
            'twitter_bio',
            'twitter_profile_picture_url',
            'follows',
            'last_tweet_date',
        ]


class TweetSerializer(serializers.ModelSerializer):
    author = TwitterAccountSerializer(many=False, read_only=True)

    class Meta:
        model = Tweet
        fields = [
            "tweet_id",
            "tweet_created_at",
            "message",
            "author",
            "in_response_to",
        ]
