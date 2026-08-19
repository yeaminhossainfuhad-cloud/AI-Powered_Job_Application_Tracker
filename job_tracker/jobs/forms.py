from django import forms

from .models import AIAnalysis, Interview, JobApplication, Tag


class JobApplicationForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        label="Tags",
        help_text="Comma-separated, e.g. Remote, Dream Job, Startup",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Remote, Dream Job"}),
    )

    class Meta:
        model = JobApplication
        fields = [
            "job_title",
            "company_name",
            "job_description",
            "location",
            "salary",
            "job_url",
            "application_date",
            "status",
            "category",
            "notes",
        ]
        widgets = {
            "job_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Backend Engineer"}),
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Acme Corp"}),
            "job_description": forms.Textarea(
                attrs={"class": "form-control", "rows": 8, "placeholder": "Paste the full job description here…"}
            ),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Remote / Dhaka, BD"}),
            "salary": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. $90k - $110k"}),
            "job_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "application_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["tags_input"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None:
            instance.user = self.user
        if commit:
            instance.save()
            self._save_tags(instance)
        return instance

    def _save_tags(self, instance):
        raw = self.cleaned_data.get("tags_input", "")
        names = [n.strip() for n in raw.split(",") if n.strip()]
        tag_objs = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(owner=instance.user, name=name)
            tag_objs.append(tag)
        instance.tags.set(tag_objs)

    def save_m2m_tags(self, instance):
        # Kept for API symmetry when commit=False is used by a caller.
        self._save_tags(instance)


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            "interview_datetime",
            "interview_type",
            "meeting_link",
            "interviewer_name",
            "notes",
        ]
        widgets = {
            "interview_datetime": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "interview_type": forms.Select(attrs={"class": "form-select"}),
            "meeting_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://zoom.us/..."}),
            "interviewer_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Jane Doe, Engineering Manager"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class ApplicationSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search by job title or company…"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses")] + JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    category = forms.ChoiceField(
        required=False,
        choices=[("", "All categories")] + JobApplication.CATEGORY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Location contains…"}),
    )


class CandidateMatchForm(forms.Form):
    candidate_profile = forms.CharField(
        required=True,
        label="Your profile / resume summary",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Paste a short summary of your skills, experience, and background…",
            }
        ),
    )
