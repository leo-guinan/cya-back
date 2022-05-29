from django.db import models

# Create your models here.
class TwitterAccount(models.Model):
    twitter_id = models.CharField("Twitter ID", max_length=512, unique=True)
    twitter_username = models.CharField("Twitter Username", max_length=255, null=True)
    twitter_name = models.CharField("Twitter Name", max_length=255, null=True)
    last_tweet_date = models.DateTimeField("date of last tweet", null=True)
    token = models.CharField("Token", max_length=100, null=True)


    def __str__(self):
        return f'{self.twitter_username}: {self.last_tweet_date}'

class FollowingRelationship(models.Model):
    twitter_user = models.ForeignKey('unfollow.TwitterAccount', related_name="main", on_delete=models.DO_NOTHING)
    follows = models.ForeignKey('unfollow.TwitterAccount', related_name="follows", on_delete=models.DO_NOTHING)

