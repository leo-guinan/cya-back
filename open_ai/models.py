from django.db import models
from django.utils import timezone


# Create your models here.

class OpenAICall(models.Model):
    tokens_used = models.IntegerField()
    source = models.CharField(max_length=255)
    request_id = models.CharField(max_length=255)
    request_type = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    parent_id = models.CharField(max_length=255, null=True)


    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(OpenAICall, self).save(*args, **kwargs)
