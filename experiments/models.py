from django.db import models

# Create your models here.
class UploadedFile(models.Model):
    bucket = models.CharField(max_length=255)
    key = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.file.name