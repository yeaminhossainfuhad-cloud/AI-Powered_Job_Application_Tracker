from django.contrib import admin

from .models import AIAnalysis, Interview, JobApplication, Tag


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company_name", "user", "status", "category", "application_date")
    list_filter = ("status", "category")
    search_fields = ("job_title", "company_name", "user__username")
    inlines = [InterviewInline]


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "interview_datetime", "interview_type")
    list_filter = ("interview_type",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ("application", "generated_at")
