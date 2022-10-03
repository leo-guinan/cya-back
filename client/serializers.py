from rest_framework import serializers

from client.models import ClientAccount
from twitter.serializers import TwitterAccountSerializer


class ClientAccountSerializer(serializers.ModelSerializer):
    twitter_account = TwitterAccountSerializer(many=False, read_only=True)

    class Meta:
        model = ClientAccount
        fields = [
            'id',
            'email',
            'twitter_account',
        ]

