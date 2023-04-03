from django.db import models

# Create your models here.
class Link(models.Model):
    url = models.TextField()
    title = models.TextField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    children = models.ManyToManyField('self', related_name='parents', symmetrical=False)
    def __str__(self):
        return self.url

class Fulltext(models.Model):
    url = models.ForeignKey(Link, related_name="fulltexts", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.text

class Section(models.Model):
    fulltext = models.ForeignKey(Fulltext, related_name='sections', on_delete=models.CASCADE)
    text = models.TextField()
    embedding_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    embeddings_saved = models.BooleanField(default=False)
    def __str__(self):
        return self.text

class Recommendation(models.Model):
    url = models.ForeignKey(Link, related_name='recommendations', on_delete=models.CASCADE)
    text = models.TextField()
    author = models.ForeignKey('users.User', related_name='recommendations', on_delete=models.CASCADE)
    affiliate_link = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.text