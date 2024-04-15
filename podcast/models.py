from django.db import models

# Create your models here.


class Podcast(models.Model):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=255, unique=True)
    podcast_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PodcastEpisode(models.Model):
    name = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transcript_guid = models.CharField(max_length=255, unique=True)
    transcript = models.TextField()
    episode_url = models.TextField(null=True, blank=True)
    episode_audio_url = models.TextField()
    embeddings_generated = models.BooleanField(default=False)
    description = models.TextField(null=True)


    def __str__(self):
        return self.name


class PodcastQuery(models.Model):
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    podcast_episodes = models.ManyToManyField(PodcastEpisode)
    snippets = models.ManyToManyField('PodcastEpisodeSnippet')
    completed = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.query


class PodcastEpisodeSnippet(models.Model):
    podcast_episode = models.ForeignKey(PodcastEpisode, on_delete=models.CASCADE)
    snippet = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=255, unique=True)
    score = models.FloatField(default=0.0)


    def __str__(self):
        return self.snippet