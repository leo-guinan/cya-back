from django.db import models

# Create your models here.
class Message(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.message

class Request(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.message