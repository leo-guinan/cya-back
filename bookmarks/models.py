from django.db import models

# Create your models here.
class Bookmark(models.Model):
    tweet = models.ForeignKey('twitter.Tweet', related_name="containing_bookmarks", on_delete=models.CASCADE)
    link = models.CharField(max_length=1024)
    owner = models.ForeignKey('twitter.TwitterAccount', related_name="user_bookmarks", on_delete=models.CASCADE)
    name = models.CharField(max_length=1024, blank=True, null=True)
