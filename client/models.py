from django.db import models

# Create your models here.
class Client(models.Model):
    name = models.TextField(unique=True)
    api_key = models.ForeignKey("rest_framework_api_key.APIKey", on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()

    def __str__(self):
        return self.name