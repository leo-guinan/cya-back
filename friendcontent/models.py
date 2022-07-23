from django.db import models


# Create your models here.

class Content(models.Model):
    class ContentType(models.TextChoices):
        BLOG = 'BL', ('Blog')
        PODCAST = 'PC', ('Podcast')
        YOUTUBE = 'YT', ('Youtube')
        TIKTOK = 'TT', ('TikTok')
        INSTAGRAM = 'IG', ('Instagram')
        HASHTAG = 'HT', ('Hashtag')

    owner = models.ForeignKey("twitter.TwitterAccount", related_name="external_content", on_delete=models.CASCADE)
    content_type = models.CharField(max_length=2, choices=ContentType.choices, default=ContentType.PODCAST)
    url = models.CharField("link to the content", max_length=1024)


class TriggerTweet(models.Model):
    tweet = models.ForeignKey("twitter.Tweet", related_name='triggers', on_delete=models.CASCADE)
    action = models.CharField("action to take", max_length=280, null=True, blank=True)
    taken = models.BooleanField("has it been completed", default=False)
    added = models.DateTimeField("time the record was added", auto_now_add=True)
    child = models.OneToOneField('self', related_name="parent", on_delete=models.SET_NULL, null=True)
