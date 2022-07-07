from django.db import models

# Create your models here.
class StartingAccount(models.Model):
    account = models.ForeignKey("twitter.TwitterAccount", related_name="crawls", on_delete=models.CASCADE)
    levels = models.IntegerField("how many levels deep to search", default=5)
    completed = models.BooleanField("has the crawler finished", default=False)


class CrawledAccount(models.Model):
    account = models.ForeignKey("twitter.TwitterAccount", related_name="crawled_on", on_delete=models.CASCADE)
    starting_account = models.ForeignKey("crawler.StartingAccount", related_name="crawled_from", on_delete=models.CASCADE)
    date_of_crawl = models.DateField(auto_now_add=True)

