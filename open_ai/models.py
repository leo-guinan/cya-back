from django.db import models

# Create your models here.

class OpenAICall(models.Model):
    tokens_used = models.IntegerField()

