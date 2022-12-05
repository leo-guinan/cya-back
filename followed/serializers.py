from django.db.models import QuerySet, Count
from rest_framework import serializers

from followed.models import FollowerReport


class FollowerReportSerializer(serializers.ModelSerializer):
    total_followers = serializers.IntegerField()

    class Meta:
        model = FollowerReport
        fields = [
            'date',
            'total_followers',
        ]

    def __new__(cls, *args, **kwargs):
        if args and isinstance(args[0], QuerySet):
            queryset = cls._build_queryset(args[0])
            args = (queryset,) + args[1:]
        return super().__new__(cls, *args, **kwargs)

    @classmethod
    def _build_queryset(cls, queryset):
        # modify the queryset here
        return queryset.annotate(
            total_followers=Count('followers'),
        )