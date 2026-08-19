from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Tag(models.Model):
    """A user-defined label used to categorize job applications
    (e.g. 'Remote', 'Dream Job', 'Startup')."""

    name = models.CharField(max_length=50)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags")

    class Meta:
        unique_together = ("name", "owner")
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobApplication(models.Model):
    STATUS_WISHLIST = "wishlist"
    STATUS_APPLIED = "applied"
    STATUS_SCREENING = "screening"
    STATUS_INTERVIEW = "interview"
    STATUS_SELECTED = "selected"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_WISHLIST, "Wishlist"),
        (STATUS_APPLIED, "Applied"),
        (STATUS_SCREENING, "Screening"),
        (STATUS_INTERVIEW, "Interview"),
        (STATUS_SELECTED, "Selected"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # Ordering used to render a status "pipeline" progress bar in the UI
    STATUS_ORDER = [
        STATUS_WISHLIST,
        STATUS_APPLIED,
        STATUS_SCREENING,
        STATUS_INTERVIEW,
        STATUS_SELECTED,
    ]

    CATEGORY_CHOICES = [
        ("software", "Software Engineering"),
        ("data", "Data / AI / ML"),
        ("design", "Design"),
        ("product", "Product Management"),
        ("marketing", "Marketing"),
        ("sales", "Sales"),
        ("operations", "Operations"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )

    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    job_description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    salary = models.CharField(
        max_length=100, blank=True, help_text="e.g. $90,000 - $110,000 or negotiable"
    )
    job_url = models.URLField(blank=True)
    application_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WISHLIST)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other", blank=True)
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="applications")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_title} @ {self.company_name}"

    def get_absolute_url(self):
        return reverse("jobs:application_detail", args=[self.pk])

    @property
    def status_progress_percent(self):
        """Used to render a simple pipeline progress bar. Rejected applications
        are shown as 100% (end of pipeline) but styled differently in the template."""
        if self.status == self.STATUS_REJECTED:
            return 100
        try:
            idx = self.STATUS_ORDER.index(self.status)
        except ValueError:
            return 0
        return int((idx / (len(self.STATUS_ORDER) - 1)) * 100)


class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ("phone", "Phone Screen"),
        ("video", "Video Call"),
        ("onsite", "Onsite / In-Person"),
        ("technical", "Technical / Coding"),
        ("hr", "HR Round"),
        ("final", "Final Round"),
        ("other", "Other"),
    ]

    application = models.ForeignKey(
        JobApplication, on_delete=models.CASCADE, related_name="interviews"
    )
    interview_datetime = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default="video")
    meeting_link = models.URLField(blank=True)
    interviewer_name = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["interview_datetime"]

    def __str__(self):
        return f"{self.get_interview_type_display()} on {self.interview_datetime:%Y-%m-%d %H:%M}"

    @property
    def is_upcoming(self):
        return self.interview_datetime >= timezone.now()


class AIAnalysis(models.Model):
    """Stores the result of running the AI Job Description Analyzer on a
    given application so it doesn't need to be re-generated on every view."""

    application = models.OneToOneField(
        JobApplication, on_delete=models.CASCADE, related_name="ai_analysis"
    )
    summary = models.TextField(blank=True)
    required_skills = models.TextField(blank=True, help_text="Comma-separated or newline list")
    required_experience = models.CharField(max_length=255, blank=True)
    important_technologies = models.TextField(blank=True)
    interview_prep_suggestions = models.TextField(blank=True)
    match_score = models.PositiveIntegerField(null=True, blank=True, help_text="0-100 match with user profile")
    raw_response = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI analysis for {self.application}"
