from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import JobApplication


class JobApplicationCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="testpass123")
        self.other_user = User.objects.create_user(username="bob", password="testpass123")
        self.client.login(username="alice", password="testpass123")

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("jobs:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_create_application(self):
        response = self.client.post(
            reverse("jobs:application_create"),
            {
                "job_title": "Backend Engineer",
                "company_name": "Acme Corp",
                "job_description": "Build APIs with Django.",
                "location": "Remote",
                "salary": "$100k",
                "job_url": "",
                "application_date": "2026-01-01",
                "status": JobApplication.STATUS_APPLIED,
                "category": "software",
                "notes": "",
                "tags_input": "Remote, Dream Job",
            },
        )
        self.assertEqual(response.status_code, 302)
        app = JobApplication.objects.get(job_title="Backend Engineer")
        self.assertEqual(app.user, self.user)
        self.assertEqual(app.tags.count(), 2)

    def test_users_only_see_their_own_applications(self):
        JobApplication.objects.create(
            user=self.other_user, job_title="Designer", company_name="Other Co"
        )
        response = self.client.get(reverse("jobs:application_list"))
        self.assertNotContains(response, "Designer")

    def test_application_detail_404_for_other_users_application(self):
        app = JobApplication.objects.create(
            user=self.other_user, job_title="Designer", company_name="Other Co"
        )
        response = self.client.get(reverse("jobs:application_detail", args=[app.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_application(self):
        app = JobApplication.objects.create(
            user=self.user, job_title="QA Engineer", company_name="TestCo"
        )
        response = self.client.post(reverse("jobs:application_delete", args=[app.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(JobApplication.objects.filter(pk=app.pk).exists())

    def test_status_progress_percent(self):
        app = JobApplication.objects.create(
            user=self.user,
            job_title="X",
            company_name="Y",
            status=JobApplication.STATUS_WISHLIST,
        )
        self.assertEqual(app.status_progress_percent, 0)
        app.status = JobApplication.STATUS_SELECTED
        self.assertEqual(app.status_progress_percent, 100)


class AuthTests(TestCase):
    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "Str0ngPassword!23",
                "password2": "Str0ngPassword!23",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
