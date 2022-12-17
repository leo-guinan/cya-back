from django.db import models

# Create your models here.
class Podcast(models.Model):
    title = models.CharField(max_length=255)
    transcript = models.TextField()
    summary = models.TextField(null=True)
    key_points = models.TextField(null=True)
    links_to_include = models.TextField(null=True)
    linkedin_post = models.TextField(null=True)
    twitter_thread = models.TextField(null= True)
    transcript_embeddings = models.TextField(null=True)
    show_notes = models.TextField(null=True)


