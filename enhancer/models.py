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


class EnhancedTweet(models.Model):
    class EnhancedTweetAnalysisStatus(models.TextChoices):
        OKAY = 'OK', ('Okay')
        ERROR = 'ER', ('Error')
    class EnhancedTweetSentiment(models.TextChoices):
        POSITIVE = 'PS', ('Positive')
        NEGATIVE = 'NG', ('Negative')
        NEUTRAL = 'NU', ('Neutral')

    tweet = models.ForeignKey('twitter.Tweet', on_delete=models.CASCADE)
    embeddings = models.JSONField(null=True, blank=True)
    enhancement_run_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=EnhancedTweetAnalysisStatus.choices, default=EnhancedTweetAnalysisStatus.OKAY)
    categories = models.CharField(max_length=255, null=True, blank=True)
    sentiment = models.CharField(max_length=2, choices=EnhancedTweetSentiment.choices, default=EnhancedTweetSentiment.NEUTRAL)


class EnhancedTweetsGroup(models.Model):
    class EnhancedTweetsGroupAnalysisStatus(models.TextChoices):
        OKAY = 'OK', ('Okay')
        ERROR = 'ER', ('Error')
    enhanced_tweets = models.ManyToManyField(EnhancedTweet, related_name='enhanced_tweets_groups')
    summary = models.TextField(null=True, blank=True)
    enhancement_run_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=EnhancedTweetsGroupAnalysisStatus.choices, default=EnhancedTweetsGroupAnalysisStatus.OKAY)

