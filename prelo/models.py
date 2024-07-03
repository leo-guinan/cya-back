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
    target_audience = models.TextField(default="Founder")
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="decks", null=True)
    version = models.IntegerField(default=1, null=True)
    user_id = models.CharField(max_length=255, blank=True, null=True)

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


class UpdatedVersionAnalysis(models.Model):
    previous_deck = models.ForeignKey(PitchDeck, on_delete=models.CASCADE, related_name="previous_version")
    new_deck = models.ForeignKey(PitchDeck, on_delete=models.CASCADE, related_name="new_version")
    risks_addressed = models.TextField(blank=True, null=True)
    slides_changed = models.TextField(blank=True, null=True)
    questions_answered = models.TextField(blank=True, null=True)
    still_missing = models.TextField(blank=True, null=True)


class PitchDeckAnalysis(models.Model):
    deck = models.OneToOneField(PitchDeck, on_delete=models.CASCADE, related_name="analysis")
    compiled_slides = models.TextField()
    initial_analysis = models.TextField(blank=True, null=True)
    extra_analysis = models.TextField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)
    processing_time = models.FloatField(blank=True, null=True)
    analysis_time = models.FloatField(blank=True, null=True)
    report_time = models.FloatField(blank=True, null=True)
    top_concern = models.TextField(blank=True, null=True)
    objections = models.TextField(blank=True, null=True)
    how_to_overcome = models.TextField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    traction = models.TextField(blank=True, null=True)
    concerns = models.TextField(blank=True, null=True)
    believe = models.TextField(blank=True, null=True)
    investor_report = models.OneToOneField("InvestorReport", on_delete=models.CASCADE, related_name="analysis",
                                           null=True)
    memo = models.OneToOneField("DealMemo", on_delete=models.CASCADE, related_name="analysis", null=True)

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
    partnerships = models.TextField(blank=True, null=True)
    founder_market_fit = models.TextField(blank=True, null=True)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    deck_uuid = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        fields = [
            f"Name: {self.name or 'N/A'}",
            f"Industry: {self.industry or 'N/A'}",
            f"Founded: {self.founded or 'N/A'}",
            f"Problem: {self.problem or 'N/A'}",
            f"Solution: {self.solution or 'N/A'}",
            f"Market: {self.market or 'N/A'}",
            f"Revenue: {self.revenue or 'N/A'}",
            f"Funding Round: {self.funding_round or 'N/A'}",
            f"Traction: {self.traction or 'N/A'}",
            f"Why Now: {self.why_now or 'N/A'}",
            f"Contact Info: {self.contact_info or 'N/A'}",
            f"Funding Amount: {self.funding_amount or 'N/A'}",
            f"Location: {self.location or 'N/A'}",
            f"Expertise: {self.expertise or 'N/A'}",
            f"Competition: {self.competition or 'N/A'}",
            f"Partnerships: {self.partnerships or 'N/A'}",
            f"Founder Market Fit: {self.founder_market_fit or 'N/A'}"
        ]
        return "\n".join(fields)


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


class CompanyScores(models.Model):
    deck = models.OneToOneField(PitchDeck, on_delete=models.CASCADE, related_name="scores", null=True)
    market_opportunity = models.FloatField(default=0.0)
    market_reasoning = models.TextField(blank=True, null=True)
    team = models.FloatField(default=0.0)
    team_reasoning = models.TextField(blank=True, null=True)
    founder_market_fit = models.FloatField(default=0.0)
    founder_market_reasoning = models.TextField(blank=True, null=True)
    product = models.FloatField(default=0.0)
    product_reasoning = models.TextField(blank=True, null=True)
    traction = models.FloatField(default=0.0)
    traction_reasoning = models.TextField(blank=True, null=True)
    final_score = models.FloatField(default=0.0)
    final_reasoning = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.final_score} - {self.deck.name}"


class Investor(models.Model):
    thesis = models.TextField()
    location = models.TextField()
    website = models.TextField()
    name = models.TextField()
    personal_notes = models.TextField()  # anything about the investor as a person that might be relevant
    lookup_id = models.CharField(max_length=255, unique=True)


class InvestmentFirm(models.Model):
    name = models.TextField
    location = models.TextField
    website = models.TextField
    investors = models.ManyToManyField(Investor, related_name="firms")
    thesis = models.TextField()
    portfolio_companies = models.ManyToManyField(Company, related_name="investors")
    lookup_id = models.IntegerField(unique=True)


class InvestorReport(models.Model):
    matches_thesis = models.BooleanField()
    recommendation_reasons = models.TextField()
    investment_potential_score = models.IntegerField()
    firm = models.ForeignKey(InvestmentFirm, on_delete=models.CASCADE, related_name="reports")
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name="reports")


class DealMemo(models.Model):
    firm = models.ForeignKey(InvestmentFirm, on_delete=models.CASCADE, related_name="memos")
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name="memos")
    memo = models.TextField()


class GoToMarketStrategy(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="go_to_market")
    strategy = models.TextField()


class CompetitorStrategy(models.Model):
    company_name = models.TextField()
    strategy = models.TextField()
    gtm = models.ForeignKey(GoToMarketStrategy, on_delete=models.CASCADE, related_name="competitors")


class DeckReport(models.Model):
    deck = models.OneToOneField(PitchDeck, on_delete=models.CASCADE, related_name="report")
    s3_path = models.CharField(max_length=255)

