from django.db import models

# Create your models here.
class Content(models.Model):
    class ContentType(models.TextChoices):
        BLOG = 'BL', ('Requested')
        YOUTUBE = 'YT', ('In progress')
        VIDEO = 'VD', ('Complete')
        PODCAST = 'PC', ('Error')

    type = models.CharField(
        max_length=2,
        choices=ContentType.choices,
        default=ContentType.BLOG,
    )

    owner = models.ForeignKey("client.ClientAccount", related_name="content_items", on_delete=models.CASCADE)
    url = models.CharField("link to the content", max_length=1024)
    feed = models.ForeignKey("gardens.ContentFeed", related_name="content", on_delete=models.CASCADE)
    title = models.CharField("title of the content", max_length=1024, null=True, blank=True)
    summary = models.CharField("summary of the content", max_length=4096, null=True, blank=True)
    published = models.DateTimeField("time the content was published", null=True, blank=True)




class ContentSource(models.Model):
    feed_location = models.CharField("location of the feed", max_length=1024)
    name = models.CharField("name of the feed", max_length=1024)


class ContentFeed(models.Model):
    owner = models.ForeignKey("client.ClientAccount", related_name="content_feeds", on_delete=models.CASCADE)
    url = models.CharField("link to the content", max_length=1024, null=True, blank=True)
    source = models.ForeignKey("gardens.ContentSource", related_name="content", on_delete=models.CASCADE)


