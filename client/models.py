import django.utils.timezone
from django.db import models


# Create your models here.
class Client(models.Model):
    class AuthVersion(models.TextChoices):
        AUTH_V1 = 'V1', ('Oauth V1')
        AUTH_V2 = 'V2', ('Oauth V2')

    name = models.CharField("name of the client", max_length=255, unique=True)
    api_key = models.ForeignKey("rest_framework_api_key.APIKey", on_delete=models.SET_NULL, null=True, blank=True)
    client_id = models.CharField("client id", max_length=255, null=True, blank=True)
    client_secret = models.CharField("client secret", max_length=255, null=True, blank=True)
    access_token = models.CharField("Access token", max_length=255, null=True, blank=True)
    access_secret = models.CharField("Access secret", max_length=255, null=True, blank=True)
    consumer_key = models.CharField("consumer key", max_length=255, null=True, blank=True)
    consumer_secret = models.CharField("consumer secret", max_length=255, null=True, blank=True)
    bearer_token = models.CharField("bearer token", max_length=255, null=True, blank=True)
    twitter_account = models.OneToOneField("twitter.TwitterAccount", related_name="client", on_delete=models.CASCADE,
                                           null=True)
    auth_version = models.CharField(
        max_length=2,
        choices=AuthVersion.choices,
        default=AuthVersion.AUTH_V1,
    )


class ClientAccount(models.Model):
    client = models.ForeignKey("client.Client", related_name="accounts", on_delete=models.CASCADE)
    token = models.CharField("twitter oauth2 token", max_length=255, default="", null=True, blank=True)
    refresh_token = models.CharField("twitter oauth2 refresh token", max_length=255, default="", null=True, blank=True)
    email = models.CharField("account email address", max_length=255, null=True, blank=True)
    twitter_account = models.ForeignKey("twitter.TwitterAccount", related_name="client_accounts",
                                        on_delete=models.CASCADE, null=True)
    refreshed = models.DateTimeField("time the token was refreshed", default=django.utils.timezone.now)
    access_key = models.CharField("oauth v1 access key", max_length=255, null=True, blank=True)
    secret_access_key = models.CharField("oauth v2 secret key", max_length=255, null=True, blank=True)
    stripe_customer_id = models.CharField("stripe customer id", max_length=255, null=True, blank=True)
    def get_curator(self):
        if hasattr(self, 'curation'):
            return self.curation
        return None


class StaffAccount(models.Model):
    client = models.ForeignKey("client.Client", related_name="staff", on_delete=models.CASCADE)
    token = models.CharField("twitter oauth2 token", max_length=255, default="", null=True, blank=True)
    refresh_token = models.CharField("twitter oauth2 refresh token", max_length=255, default="", null=True, blank=True)
    email = models.CharField("account email address", max_length=255, null=True, blank=True)
    twitter_account = models.ForeignKey("twitter.TwitterAccount", related_name="staff_accounts",
                                        on_delete=models.CASCADE)
    refreshed = models.DateTimeField("time the token was refreshed", default=django.utils.timezone.now)
    access_key = models.CharField("oauth v1 access key", max_length=255, null=True, blank=True)
    secret_access_key = models.CharField("oauth v2 secret key", max_length=255, null=True, blank=True)


class BetaAccount(models.Model):
    client_account = models.ForeignKey("client.ClientAccount", related_name="beta", on_delete=models.CASCADE)
    beta_code = models.CharField("beta access code", max_length=255)
    messaged = models.BooleanField("did we send the dm?", default=False)


class AccountConfig(models.Model):
    class NotificationPreference(models.TextChoices):
        TWEET = 'TW', ('Tweet')
        EMAIL = 'EM', ('Email')
        DIRECT_MESSAGE = "DM", ("Direct Message")

    client_account = models.OneToOneField("client.ClientAccount", related_name="config", on_delete=models.CASCADE)
    notification_preference = models.CharField(max_length=2, choices=NotificationPreference.choices,
                                               default=NotificationPreference.TWEET)
    notification_requested = models.BooleanField("Has the user requested notification?", default=False)
