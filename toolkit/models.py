from django.db import models

# Create your models here.

class YoutubeVideo(models.Model):
    url = models.CharField(max_length=255, unique=True)
    transcript = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    outline = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class IdeaColliderOutput(models.Model):
    first_video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name='first_video')
    second_video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name='second_video')
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # create unique constraint on first_video and second_video
    class Meta:
        unique_together = ('first_video', 'second_video')

    def __str__(self):
        return self.result