from django.db import models


CREATED = "CR"
PROCESSING = "PR"
ERROR = "ER"
COMPLETE = "CP"
STATUS_CHOICES = [
    (CREATED, "Created"),
    (PROCESSING, "Processing"),
    (COMPLETE, "Complete"),
    (ERROR, "Error"),
]

# Create your models here.

class YoutubeVideo(models.Model):
    url = models.CharField(max_length=255, unique=True)
    transcript = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class BlogPost(models.Model):
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=CREATED,
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    outline = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class IdeaColliderOutput(models.Model):

    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=CREATED,
    )
    first_video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name='first_video')
    second_video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name='second_video')
    result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=100, unique=True)

    # create unique constraint on first_video and second_video
    class Meta:
        unique_together = ('first_video', 'second_video')

    def __str__(self):
        return self.result


class PdfDocument(models.Model):
    name = models.CharField(max_length=255)
    s3_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=100, unique=True)
    indexed = models.BooleanField(default=False)
