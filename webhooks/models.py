from django.db import models
from django.utils import timezone


# Create your models here.

class TranscriptRequestEmail(models.Model):
    class Meta:
        unique_together = (('from_email', 'title'),)

    from_email = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    transcript = models.TextField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    podcast = models.OneToOneField('podcast_toolkit.Podcast', related_name="request", on_delete=models.CASCADE, null=True)


    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(TranscriptRequestEmail, self).save(*args, **kwargs)
