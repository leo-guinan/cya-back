from django.db import models


# Create your models here.
class EnhancedTwitterAccount(models.Model):
    class EnhancedTwitterAccountAnalysisStatus(models.TextChoices):
        OKAY = 'OK', ('Okay')
        ERROR = 'ER', ('Error')


    twitter_account = models.ForeignKey('twitter.TwitterAccount', on_delete=models.CASCADE)
    summary = models.TextField(null=True, blank=True)
    analysis = models.JSONField(null=True, blank=True)
    enhancement_run_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=EnhancedTwitterAccountAnalysisStatus.choices, default=EnhancedTwitterAccountAnalysisStatus.OKAY)
    likely_spam = models.BooleanField(default=False)
