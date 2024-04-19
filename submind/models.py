from django.db import models


# Create your models here.


class Submind(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    subminds = models.ManyToManyField('self', symmetrical=False, related_name="superminds")
    mindUUID = models.CharField(max_length=100, unique=True)


class Goal(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.TextField()
    submind = models.ForeignKey(Submind, on_delete=models.CASCADE, related_name="goals")
    completed = models.BooleanField(default=False)
    results = models.TextField(null=True, blank=True)
    client = models.ForeignKey('SubmindClient', on_delete=models.CASCADE, related_name="goals", null=True)
    def is_complete(self):
        if all(question.is_complete() for question in self.questions.all()):
            self.completed = True
            self.save()
        return self.completed


class Question(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.TextField()
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="questions")
    submind = models.ForeignKey(Submind, on_delete=models.CASCADE, related_name="questions")

    # define being complete as having at least one thought as a response
    def is_complete(self):
        return len(self.thoughts.all()) > 0


class Thought(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="thoughts")
    submind = models.ForeignKey(Submind, on_delete=models.CASCADE, related_name="thoughts")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.content:
            # Trigger a completion check on the parent question
            if self.question.is_complete():
                # Trigger a completion check on the parent goal
                self.question.goal.is_complete()


# a client defines the root submind for something
class SubmindClient(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)

