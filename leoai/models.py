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


class Collection(models.Model):
    name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class Item(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.TextField()
    link = models.TextField()
    description = models.TextField()
    recommendation = models.TextField()
    uuid = models.TextField()
    def __str__(self):
        return self.name