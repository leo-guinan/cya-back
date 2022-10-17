from rest_framework import serializers

from client.serializers import ClientAccountSerializer
from gardens.models import ContentFeed, ContentSource, Content


class ContentSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSource
        fields = [
            'name',
            'feed_location',
        ]


class ContentSerializer(serializers.ModelSerializer):
    owner = ClientAccountSerializer(many=False, read_only=True)

    class Meta:
        model = Content
        fields = [
            'id',
            'url',
            'title',
            'summary',
            'published',
            'type',
            'owner',
        ]


class ContentFeedSerializer(serializers.ModelSerializer):
    owner = ClientAccountSerializer(many=False, read_only=True)
    source = ContentSourceSerializer(many=False, read_only=True)
    content = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = ContentFeed
        fields = [
            'id',
            'source',
            'owner',
            'content',
        ]
