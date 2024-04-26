from django.db import models

# Create your models here.

class PitchDeck(models.Model):
    CREATED = "CR"
    UPLOADED = "UL"
    PROCESSING = "PR"
    READY_FOR_ANALYSIS = "RA"
    ANALYZING = "AN"
    READY_FOR_REPORTING = "RR"
    REPORTING = "RE"
    COMPLETE = "CP"
    ERROR = "ER"
    STATUS_CHOICES = [
        (CREATED, "Created"),
        (UPLOADED, "Uploaded"),
        (PROCESSING, "Processing"),
        (READY_FOR_ANALYSIS, "Ready for Analysis"),
        (ANALYZING, "Analyzing"),
        (READY_FOR_REPORTING, "Ready for Reporting"),
        (REPORTING, "Reporting"),
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
    error_message = models.TextField(blank=True, null=True)
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


class PitchDeckAnalysis(models.Model):
    deck = models.OneToOneField(PitchDeck, on_delete=models.CASCADE, related_name="analysis")
    compiled_slides = models.TextField()
    initial_analysis = models.TextField(blank=True, null=True)
    extra_analysis = models.TextField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)
    processing_time = models.FloatField(blank=True, null=True)
    analysis_time = models.FloatField(blank=True, null=True)
    report_time = models.FloatField(blank=True, null=True)
    def __str__(self):
        return self.deck.name


class Company(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    founded = models.DateField(blank=True, null=True)
    problem = models.TextField(blank=True, null=True)
    solution = models.TextField(blank=True, null=True)
    market = models.TextField(blank=True, null=True)
    revenue = models.TextField(blank=True, null=True)
    funding_round = models.TextField(blank=True, null=True)
    traction = models.TextField(blank=True, null=True)
    why_now = models.TextField(blank=True, null=True)
    contact_info = models.TextField(blank=True, null=True)
    funding_amount = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    expertise = models.TextField(blank=True, null=True)
    competition = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name


class Team(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="team")
    def __str__(self):
        return self.name

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    founder = models.BooleanField(default=False)
    background = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
