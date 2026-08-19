"""Optional helper: python manage.py seed_demo_data --username demo --password demo1234
Creates a demo user (if needed) with a handful of sample job applications so
graders/reviewers can see the app populated without manual data entry."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Interview, JobApplication, Tag


class Command(BaseCommand):
    help = "Seed the database with a demo user and sample job applications."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="demo12345")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        user, created = User.objects.get_or_create(username=username, defaults={"email": "demo@example.com"})
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}' / '{password}'"))
        else:
            self.stdout.write(f"Using existing user '{username}'")

        remote_tag, _ = Tag.objects.get_or_create(owner=user, name="Remote")
        dream_tag, _ = Tag.objects.get_or_create(owner=user, name="Dream Job")

        sample_jobs = [
            {
                "job_title": "Backend Engineer",
                "company_name": "Acme Cloud",
                "job_description": (
                    "We're looking for a Backend Engineer with 3+ years of experience in Python "
                    "and Django to build scalable REST APIs. Experience with PostgreSQL, Docker, "
                    "AWS, and CI/CD pipelines is required. Bonus: experience with Celery and Redis."
                ),
                "location": "Remote",
                "salary": "$90,000 - $115,000",
                "status": JobApplication.STATUS_APPLIED,
                "category": "software",
                "tags": [remote_tag],
            },
            {
                "job_title": "Machine Learning Engineer",
                "company_name": "DataVantage",
                "job_description": (
                    "Seeking an ML Engineer to build and deploy NLP models. Requires strong Python, "
                    "PyTorch, and experience with LLM fine-tuning. 2+ years experience preferred."
                ),
                "location": "Dhaka, BD",
                "salary": "Negotiable",
                "status": JobApplication.STATUS_INTERVIEW,
                "category": "data",
                "tags": [dream_tag],
            },
            {
                "job_title": "Product Designer",
                "company_name": "Northwind Studio",
                "job_description": (
                    "Product Designer role focused on B2B SaaS dashboards. Figma expertise required, "
                    "3+ years of experience, portfolio required."
                ),
                "location": "Hybrid - Dhaka",
                "salary": "$50,000 - $65,000",
                "status": JobApplication.STATUS_WISHLIST,
                "category": "design",
                "tags": [],
            },
        ]

        for job in sample_jobs:
            tags = job.pop("tags")
            app, created = JobApplication.objects.get_or_create(
                user=user, job_title=job["job_title"], company_name=job["company_name"], defaults=job
            )
            if tags:
                app.tags.set(tags)
            if created and app.status in (JobApplication.STATUS_INTERVIEW,):
                Interview.objects.get_or_create(
                    application=app,
                    interview_datetime=timezone.now() + timedelta(days=3),
                    defaults={"interview_type": "video", "meeting_link": "https://zoom.us/example"},
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
