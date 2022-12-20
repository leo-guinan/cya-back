from datetime import datetime

from django.db import models

# Create your models here.
class Subscriber(models.Model):
    client_account = models.OneToOneField("client.ClientAccount",  related_name="followed_subscription", on_delete=models.CASCADE)
    subscription_end_date = models.DateTimeField('subscription end date', null=True, blank=True)
    beta = models.BooleanField("is this a beta account", default=False)



class FollowerReport(models.Model):

    subscriber = models.ForeignKey("followed.Subscriber", related_name="reports", on_delete=models.CASCADE)
    followers = models.ManyToManyField("twitter.TwitterAccount", related_name="subscribed_following")
    date = models.DateTimeField("date of report", auto_created=True)


class DifferenceReport(models.Model):
    newer_report = models.ForeignKey("followed.FollowerReport", related_name="newer_report", on_delete=models.CASCADE)
    older_report = models.ForeignKey("followed.FollowerReport", related_name="older_report", on_delete=models.CASCADE)
    new_followers = models.ManyToManyField("enhancer.EnhancedTwitterAccount", related_name="new_followers")
    lost_followers = models.ManyToManyField("twitter.TwitterAccount", related_name="stopped_following")
    date = models.DateTimeField("date of report", auto_created=True)
    subject = models.CharField("subject of email", max_length=255, null=True, blank=True)
    message = models.TextField("message of email", null=True, blank=True)
    sent = models.BooleanField("has this report been sent", default=False)


