from django.db import models

# Create your models here.
class Person(models.Model):
    name = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pinecone_id = models.TextField(null=True, blank=True)
    url = models.TextField()

    def __str__(self):
        return self.name

class Tool(models.Model):
    name = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url = models.TextField()
    pinecone_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class OutgoingRequest(models.Model):
    message = models.TextField()
    respond_to = models.TextField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.TextField(unique=True)
    webhook_url = models.TextField()
    session_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.message

class IncomingRequest(models.Model):
    message = models.TextField()
    respond_to = models.TextField()
    uuid = models.TextField(unique=True)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    webhook_url = models.TextField()

    def __str__(self):
        return self.message