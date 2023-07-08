from django.db import models


# Create your models here.

class Resource(models.Model):
    url = models.CharField(max_length=512)
    title = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    children = models.ManyToManyField('self', symmetrical=False, related_name='parents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ResourceChunk(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='chunks')
    chunk = models.TextField()
    uuid = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
