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
    account = models.OneToOneField("twitter.TwitterAccount", related_name="analysis", on_delete=models.CASCADE, unique=True)
    created = models.DateTimeField("Date created", auto_now_add=True)
    updated = models.DateTimeField("Date updated", auto_now=True)
    dormant_count = models.IntegerField("number of accounts followed that are dormant", default=0)
    following_count = models.IntegerField("number of accounts followed", default=0)


