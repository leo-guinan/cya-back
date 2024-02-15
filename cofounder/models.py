from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=255)
    initial_session_id = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    daily_checkin = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class InitialQuestion(models.Model):
    question = models.CharField(max_length=255)
    index = models.IntegerField()
    prompt_variable = models.CharField(max_length=255)
    def __str__(self):
        return self.question

class UserAnswer(models.Model):
    answer = models.TextField()
    question = models.ForeignKey(InitialQuestion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.answer

class ChatCredit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credits')
    session = models.ForeignKey('ChatSession', on_delete=models.CASCADE, related_name='credits')
    def __str__(self):
        return self.user.name

class ChatSession(models.Model):
    DEFAULT = "DF"
    DAILY_GREAT = "DG"
    DAILY_OK = "DO"
    DAILY_BAD = "DB"
    CHAT_TYPE_CHOICES = [
        (DEFAULT, "Default"),
        (DAILY_GREAT, "Great"),
        (DAILY_OK, "Ok"),
        (DAILY_BAD, "Bad"),
    ]
    chat_type = models.CharField(
        max_length=2,
        choices=CHAT_TYPE_CHOICES,
        default=DEFAULT,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255)
    name = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.name



class ChatError(models.Model):
    error = models.TextField()
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)

    def __str__(self):
        return self.error

class ChatPrompt(models.Model):
    prompt = models.TextField()
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.prompt

class ChatPromptParameter(models.Model):
    prompt = models.ForeignKey(ChatPrompt, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Source(models.Model):
    name = models.CharField(max_length=255)
    rss_feed = models.CharField(blank=True, null=True, max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    fulltext_id = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sources', blank=True, null=True)
    PODCAST = "PC"
    YOUTUBE = "YT"
    BLOG = "BL"
    TEXT = "TX"
    CONTENT_TYPE_CHOICES = [
        (PODCAST, "Podcast"),
        (YOUTUBE, "Youtube"),
        (BLOG, "blog"),
        (TEXT, "text"),
    ]
    content_type = models.CharField(
        max_length=2,
        choices=CONTENT_TYPE_CHOICES,
        default=TEXT,
    )
    def __str__(self):
        return self.name

class SourceLink(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='links')
    url = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    fulltext_id = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.title

CHAT_TYPE_MAPPING = {
    "default": ChatSession.DEFAULT,
    "daily_great": ChatSession.DAILY_GREAT,
    "daily_ok": ChatSession.DAILY_OK,
    "daily_bad": ChatSession.DAILY_BAD,
}

class FounderProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='founders')
    profile = models.TextField()
    def __str__(self):
        return self.user.name

class BusinessProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    profile = models.TextField()
    business_id = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.name


class Cofounder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cofounders')
    name = models.CharField(max_length=255)
    profile = models.TextField()
    profile_image = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Command(models.Model):
    command = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField()
    url = models.URLField()
    input_schema = models.TextField()
    output_schema = models.TextField()
    uuid = models.CharField(unique=True, max_length=255)

class Answer(models.Model):
    answer = models.TextField()
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(unique=True, max_length=255)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)

class Task(models.Model):
    task = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.CharField(unique=True, max_length=255)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    details = models.TextField()
    taskFor = models.TextField()
    complete = models.BooleanField(default=False)