from django.db import models

from chat.enums import SpeakerTypes


# Create your models here.
class ClientApp(models.Model):
    name = models.TextField(unique=True)
    api_key = models.TextField(unique=True)
    initial_message = models.TextField(default="How can I help you today?")
    default_slug = models.TextField(default="global")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    client = models.ForeignKey('client.Client', related_name='apps', on_delete=models.CASCADE, null=True, blank=True)
    metasearch_engine = models.OneToOneField('decisions.MetaSearchEngine', related_name='app', on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name

class Source(models.Model):
    app = models.ForeignKey(ClientApp, related_name='sources', on_delete=models.CASCADE)
    url = models.TextField()
    title = models.TextField()
    metasearch_engine = models.ForeignKey('decisions.MetaSearchEngine', related_name='sources', on_delete=models.CASCADE, null=True, blank=True)

class Use(models.Model):
    messages = models.ManyToManyField('Message', related_name='uses')
    source = models.ForeignKey(Source, related_name='uses', on_delete=models.CASCADE)
    index = models.IntegerField(default=0)

class Message(models.Model):
    previous_message = models.ForeignKey('self', related_name='next_messages', on_delete=models.CASCADE, null=True, blank=True)
    speaker = models.IntegerField(choices=SpeakerTypes.choices(), default=SpeakerTypes.HUMAN)
    content = models.TextField()


