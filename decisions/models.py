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
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uuid = models.TextField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug


class MetaSearchEngine(models.Model):
    search_engines = models.ManyToManyField(SearchEngine, related_name='parents', symmetrical=False)
    children = models.ManyToManyField('self', related_name='parents', symmetrical=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.TextField()
    slug = models.TextField(unique=True)
    uuid = models.TextField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.name


class SearchEngineCategory(models.Model):
    search_engine = models.ForeignKey(SearchEngine, related_name='categories', on_delete=models.CASCADE)
    category = models.TextField()
    client_app = models.ForeignKey('chat.ClientApp', related_name='search_engine_categories', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category


class SearchEngineCategoryPrompt(models.Model):
    client_app = models.ForeignKey('chat.ClientApp', related_name='search_engine_category_prompt', on_delete=models.CASCADE)
    search_engine_category = models.ForeignKey(SearchEngineCategory, related_name='prompts', on_delete=models.CASCADE)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.prompt
