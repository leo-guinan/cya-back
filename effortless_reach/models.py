from django.db import models

# Create your models here.
class RssFeed(models.Model):
    url = models.CharField(max_length=512)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('client.ClientAccount', on_delete=models.CASCADE, related_name="rss_feeds", null=True)


class Podcast(models.Model):
    title = models.CharField(max_length=512)
    link = models.CharField(max_length=512)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rss_feed = models.ForeignKey(RssFeed, on_delete=models.CASCADE)

class PodcastEpisode(models.Model):
    title = models.CharField(max_length=512)
    link = models.CharField(max_length=512)
    download_link = models.CharField(max_length=512, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField()
    podcast = models.ForeignKey(Podcast, related_name="episodes", on_delete=models.CASCADE)

class Transcript(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    episode = models.OneToOneField(PodcastEpisode, related_name="transcript", on_delete=models.CASCADE)

