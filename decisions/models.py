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
    url = models.OneToOneField(Link, related_name="fulltext", on_delete=models.CASCADE)
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
    snippet = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.text

class SearchEngine(models.Model):
    slug = models.TextField(unique=True)
    url = models.TextField()
    title = models.TextField( null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uuid = models.TextField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.slug

class SearchEngineSearchEngine(models.Model):
    search_engines = models.ManyToManyField(SearchEngine, related_name='parents', symmetrical=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.TextField()
    slug = models.TextField(unique=True)
    uuid = models.TextField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.name




class SearchableLink(models.Model):
    url = models.ForeignKey(Link, related_name='searchable_links', on_delete=models.CASCADE)
    search_engine = models.ForeignKey(SearchEngine, related_name='searchable_links', on_delete=models.CASCADE)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uuid = models.TextField(null=True, blank=True, unique=True)
    image = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.url
