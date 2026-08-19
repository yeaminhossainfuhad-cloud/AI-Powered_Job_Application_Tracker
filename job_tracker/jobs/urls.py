from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/new/", views.application_create, name="application_create"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/edit/", views.application_edit, name="application_edit"),
    path("applications/<int:pk>/delete/", views.application_delete, name="application_delete"),
    path("applications/<int:pk>/interviews/new/", views.interview_create, name="interview_create"),
    path(
        "applications/<int:pk>/interviews/<int:interview_pk>/delete/",
        views.interview_delete,
        name="interview_delete",
    ),
    path("applications/<int:pk>/ai-analysis/", views.ai_analysis_view, name="ai_analysis"),
    path("applications/<int:pk>/ai-match/", views.ai_match_view, name="ai_match"),
]
