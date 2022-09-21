from django.db import models


# Create your models here.

class AnalysisReport(models.Model):
    account = models.ForeignKey("twitter.TwitterAccount", related_name="analysis_reports", on_delete=models.CASCADE)
    dormant_count = models.IntegerField("number of accounts followed that are dormant")
    following_count = models.IntegerField("number of accounts followed")
    date_of_report = models.DateField("Date report was created", auto_now_add=True)


class Analysis(models.Model):
    class AnalysisState(models.TextChoices):
        REQUESTED = 'RE', ('Requested')
        IN_PROGRESS = 'IP', ('In progress')
        COMPLETE = 'CP', ('Complete')
        ERROR = 'ER', ('Error')

    state = models.CharField(
        max_length=2,
        choices=AnalysisState.choices,
        default=AnalysisState.REQUESTED,
    )
    account = models.OneToOneField("twitter.TwitterAccount", related_name="analysis", on_delete=models.CASCADE,
                                   unique=True)
    created = models.DateTimeField("Date created", auto_now_add=True)
    updated = models.DateTimeField("Date updated", auto_now=True)
    dormant_count = models.IntegerField("number of accounts followed that are dormant", default=0)
    following_count = models.IntegerField("number of accounts followed", default=0)


class AccountCheck(models.Model):
    class CheckStatus(models.TextChoices):
        REQUESTED = 'RE', ('Requested')
        IN_PROGRESS = 'IP', ('In progress')
        COMPLETE = 'CP', ('Complete')
        ERROR = 'ER', ('Error')

    status = models.CharField(
        max_length=2,
        choices=CheckStatus.choices,
        default=CheckStatus.REQUESTED,
    )
    account = models.OneToOneField("twitter.TwitterAccount", related_name="account_check", on_delete=models.CASCADE,
                                   unique=True)
    requests = models.ManyToManyField("client.ClientAccount", related_name="accounts_to_analyze")
    last_requested = models.DateTimeField("last time requested", auto_now=True)
    last_analyzed = models.DateTimeField("last time analyzed", null=True)
    error = models.CharField("Error encountered", max_length=1024, null=True, blank=True)



class UnfollowRequest(models.Model):
    requesting_account = models.ForeignKey("client.ClientAccount", related_name="requested_unfollows",
                                           on_delete=models.CASCADE)
    account_to_unfollow = models.ForeignKey("twitter.TwitterAccount", related_name="unfollow_requests", on_delete=models.CASCADE, null=True)
    unfollowed = models.DateTimeField("the time the account was unfollowed", null=True)


