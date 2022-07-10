from rest_framework import serializers

from twitter.serializers import TwitterAccountSerializer
from unfollow.models import Analysis


class AnalysisSerializer(serializers.ModelSerializer):
    account = TwitterAccountSerializer(many=False, read_only=True)

    class Meta:
        model = Analysis
        fields = ['dormant_count', 'following_count', 'state', 'account', 'created', 'updated']
