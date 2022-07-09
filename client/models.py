from django.db import models

# Create your models here.
class Client(models.Model):
    name = models.CharField("name of the client", max_length=255, unique=True)
    api_key = models.ForeignKey("rest_framework_api_key.APIKey", on_delete=models.SET_NULL, null=True, blank=True)
    client_id = models.CharField("client id", max_length=255, null=True, blank=True)
    client_secret = models.CharField("client secret", max_length=255, null=True, blank=True)


class ClientAccount(models.Model):
    client = models.ForeignKey("client.Client", related_name="accounts", on_delete=models.CASCADE)
    token = models.CharField("twitter oauth2 token", max_length=255, default="")
    refresh_token = models.CharField("twitter oauth2 refresh token", max_length=255, default="")
    email = models.CharField("account email address", max_length=255, null=True, blank=True)
    twitter_account = models.ForeignKey("twitter.TwitterAccount", related_name="client_accounts", on_delete=models.CASCADE)

