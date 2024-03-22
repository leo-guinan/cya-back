from django.db import models

# Create your models here.
class Task(models.Model):
    PRIVATE = "PR"
    PUBLIC = "PB"
    LIMITED = "LM"
    SCOPE_CHOICES = [
        (PRIVATE, "Private"),
        (PUBLIC, "Public"),
        (LIMITED, "Limited"),
    ]
    scope = models.CharField(
        max_length=2,
        choices=SCOPE_CHOICES,
        default=PRIVATE,
    )


    task = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(unique=True, max_length=255)
    description = models.TextField()
    taskFor = models.TextField()
    complete = models.BooleanField(default=False)
    completedAt = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey("self", models.DO_NOTHING, null=True, blank=True, db_column='parent',
                               related_name="children")
    user_id = models.TextField()
    priority = models.IntegerField(default=0)
    external_model_id = models.TextField(null=True, blank=True)
    external_object_uuid = models.TextField(null=True, blank=True)


    class Source(models.Model):
        name = models.CharField(max_length=1024)
        url = models.TextField()
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
