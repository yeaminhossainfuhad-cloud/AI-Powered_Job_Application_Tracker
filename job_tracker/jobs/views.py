from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import ai_service
from .forms import (
    ApplicationSearchForm,
    CandidateMatchForm,
    InterviewForm,
    JobApplicationForm,
)
from .models import AIAnalysis, Interview, JobApplication


def _user_applications(user):
    return JobApplication.objects.filter(user=user)


@login_required
def dashboard(request):
    applications = _user_applications(request.user)

    total_applications = applications.count()
    status_counts = [
        {"key": key, "label": label, "count": applications.filter(status=key).count()}
        for key, label in JobApplication.STATUS_CHOICES
    ]
    recent_applications = applications.order_by("-created_at")[:5]
    upcoming_interviews = (
        Interview.objects.filter(application__user=request.user, interview_datetime__gte=timezone.now())
        .select_related("application")
        .order_by("interview_datetime")[:5]
    )

    context = {
        "total_applications": total_applications,
        "status_counts": status_counts,
        "recent_applications": recent_applications,
        "upcoming_interviews": upcoming_interviews,
    }
    return render(request, "jobs/dashboard.html", context)


@login_required
def application_list(request):
    applications = _user_applications(request.user)
    form = ApplicationSearchForm(request.GET or None)

    if form.is_valid():
        q = form.cleaned_data.get("q")
        status = form.cleaned_data.get("status")
        category = form.cleaned_data.get("category")
        location = form.cleaned_data.get("location")

        if q:
            applications = applications.filter(
                Q(job_title__icontains=q) | Q(company_name__icontains=q)
            )
        if status:
            applications = applications.filter(status=status)
        if category:
            applications = applications.filter(category=category)
        if location:
            applications = applications.filter(location__icontains=location)

    paginator = Paginator(applications, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "form": form,
        "page_obj": page_obj,
        "applications": page_obj.object_list,
    }
    return render(request, "jobs/application_list.html", context)


@login_required
def application_detail(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    interviews = application.interviews.all()
    ai_analysis = getattr(application, "ai_analysis", None)
    return render(
        request,
        "jobs/application_detail.html",
        {
            "application": application,
            "interviews": interviews,
            "ai_analysis": ai_analysis,
            "interview_form": InterviewForm(),
        },
    )


@login_required
def application_create(request):
    if request.method == "POST":
        form = JobApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save()
            messages.success(request, f"Added application for {application.job_title}.")
            return redirect("jobs:application_detail", pk=application.pk)
    else:
        form = JobApplicationForm(user=request.user)

    return render(request, "jobs/application_form.html", {"form": form, "is_edit": False})


@login_required
def application_edit(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == "POST":
        form = JobApplicationForm(request.POST, instance=application, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Application updated.")
            return redirect("jobs:application_detail", pk=application.pk)
    else:
        form = JobApplicationForm(instance=application, user=request.user)

    return render(
        request, "jobs/application_form.html", {"form": form, "is_edit": True, "application": application}
    )


@login_required
def application_delete(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == "POST":
        title = application.job_title
        application.delete()
        messages.success(request, f"Deleted application for {title}.")
        return redirect("jobs:application_list")
    return render(request, "jobs/application_confirm_delete.html", {"application": application})


@login_required
def interview_create(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == "POST":
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()
            if application.status in (JobApplication.STATUS_WISHLIST, JobApplication.STATUS_APPLIED, JobApplication.STATUS_SCREENING):
                application.status = JobApplication.STATUS_INTERVIEW
                application.save(update_fields=["status", "updated_at"])
            messages.success(request, "Interview scheduled.")
        else:
            messages.error(request, "Could not schedule interview. Please check the form.")
    return redirect("jobs:application_detail", pk=application.pk)


@login_required
def interview_delete(request, pk, interview_pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    interview = get_object_or_404(Interview, pk=interview_pk, application=application)
    if request.method == "POST":
        interview.delete()
        messages.success(request, "Interview removed.")
    return redirect("jobs:application_detail", pk=application.pk)


@login_required
def ai_analysis_view(request, pk):
    """AI Job Description Analyzer: generates (or re-generates) an AI analysis
    for the application's job description and displays it."""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)

    if request.method == "POST" and request.POST.get("action") == "generate":
        try:
            result = ai_service.analyze_job_description(
                application.job_title, application.company_name, application.job_description
            )
            AIAnalysis.objects.update_or_create(
                application=application,
                defaults={
                    "summary": result["summary"],
                    "required_skills": result["required_skills"],
                    "required_experience": result["required_experience"],
                    "important_technologies": result["important_technologies"],
                    "interview_prep_suggestions": result["interview_prep_suggestions"],
                    "raw_response": result["raw_response"],
                },
            )
            messages.success(request, "AI analysis generated.")
        except ai_service.AIServiceError as exc:
            messages.error(request, str(exc))
        return redirect("jobs:ai_analysis", pk=application.pk)

    ai_analysis = getattr(application, "ai_analysis", None)
    match_form = CandidateMatchForm()
    return render(
        request,
        "jobs/ai_analysis.html",
        {"application": application, "ai_analysis": ai_analysis, "match_form": match_form},
    )


@login_required
def ai_match_view(request, pk):
    """Optional AI feature: AI Job Match Analysis against a candidate profile."""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    match_result = None
    match_form = CandidateMatchForm(request.POST or None)

    if request.method == "POST" and match_form.is_valid():
        try:
            match_result = ai_service.analyze_job_match(
                application.job_title,
                application.company_name,
                application.job_description,
                match_form.cleaned_data["candidate_profile"],
            )
        except ai_service.AIServiceError as exc:
            messages.error(request, str(exc))

    ai_analysis = getattr(application, "ai_analysis", None)
    return render(
        request,
        "jobs/ai_analysis.html",
        {
            "application": application,
            "ai_analysis": ai_analysis,
            "match_form": match_form,
            "match_result": match_result,
        },
    )
