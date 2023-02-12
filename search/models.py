from django.db import models

# Create your models here.
class Content(models.Model):
    link = models.URLField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey('client.ClientAccount', related_name='created_items', on_delete=models.CASCADE)
    type = models.CharField(max_length=255, null=True, blank=True)
    fulltext = models.TextField(null=True, blank=True)


class ContentChunk(models.Model):
    content = models.ForeignKey('search.Content', related_name='chunks', on_delete=models.CASCADE)
    text = models.TextField()
    embeddings = models.JSONField(null=True, blank=True)
    embeddings_saved = models.BooleanField(default=False)
    chunk_id = models.CharField(max_length=255, unique=True)

class Curator(models.Model):
    client_account = models.OneToOneField('client.ClientAccount', related_name='curation', on_delete=models.CASCADE)
    podcasts = models.ManyToManyField('effortless_reach.Podcast', related_name='curators')
    podcast_episodes = models.ManyToManyField('effortless_reach.PodcastEpisode', related_name='curators')
