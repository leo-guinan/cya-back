from django.db import models


# Create your models here.

class Subscription(models.Model):
    class SubscriptionCadence(models.TextChoices):
        DAILY = 'DL', ('Daily')
        WEEKLY = 'WK', ('Weekly')

    owner = models.ForeignKey("twitter.TwitterAccount", related_name="subscriptions", on_delete=models.CASCADE)
    group = models.ForeignKey("twitter.Group", related_name="subscriptions", on_delete=models.CASCADE)
    name = models.CharField("the name of the subscription", max_length=255)
    cadence = models.CharField(max_length=2, choices=SubscriptionCadence.choices, default=SubscriptionCadence.WEEKLY)

