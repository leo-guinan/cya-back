from django.db import models

# Create your models here.

class State(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    state = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Command(models.Model):
    command = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()
    url = models.URLField()
    input_schema = models.TextField()
    output_schema = models.TextField()
    uuid = models.CharField(unique=True, max_length=255)
