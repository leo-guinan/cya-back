from django.db import models

# Create your models here.

class PitchDeck(models.Model):
    CREATED = "CR"
    UPLOADED = "UL"
    PROCESSING = "PR"
    COMPLETE = "CP"
    ERROR = "ER"
    STATUS_CHOICES = [
        (CREATED, "Created"),
        (UPLOADED, "Uploaded"),
        (PROCESSING, "Processing"),
        (COMPLETE, "Complete"),
        (ERROR, "Error"),
    ]
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=CREATED,
    )
    s3_path = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.s3_path


class PitchDeckSlide(models.Model):
    deck = models.ForeignKey(PitchDeck, on_delete=models.CASCADE, related_name="slides")
    content = models.TextField()
    order = models.IntegerField()
    s3_path = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    uuid = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return f"{self.deck.name} - {self.order}"