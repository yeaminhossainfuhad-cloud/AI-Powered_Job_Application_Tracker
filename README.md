# JobTrackAI — AI-Powered Job Application Tracker

A Django web application for managing and tracking job applications from a single
dashboard, with an AI-powered job description analyzer built on the Anthropic API
(Claude).

## Features

- **User Authentication** — registration, login, logout, per-user data isolation
- **Job Application Management** — create, list, view, edit, delete applications
  (title, company, description, location, salary, URL, application date, status, notes)
- **Application Status Pipeline** — Wishlist → Applied → Screening → Interview →
  Selected / Rejected, with a visual progress bar
- **Search & Filtering** — search by job title/company, filter by status,
  category, and location
- **Categories & Tags** — assign a category and free-form tags to each application
- **Interview Management** — schedule interviews with date/time, type, meeting
  link, interviewer name, and notes; upcoming interviews surface on the dashboard
- **AI Features (Anthropic / Claude API)**
  - **AI Job Description Analyzer** — generates a summary, required skills,
    required experience, important technologies, and interview preparation
    suggestions from a pasted job description
  - **AI Job Match Analysis** (optional/bonus) — compares your profile/resume
    summary against the job description and returns a match score, strengths,
    gaps, and a recommendation
- **Dashboard** — total applications, applications by status, recent applications,
  upcoming interviews

## Tech Stack

- Python 3.11+, Django 5
- SQLite (default, zero-config)
- Anthropic Python SDK (`anthropic`) for AI features
- Server-rendered Django templates + vanilla CSS (no frontend build step required)

## Project Structure

```
job_tracker/
├── manage.py
├── requirements.txt
├── .env.example
├── job_tracker/          # project settings, urls, wsgi/asgi
├── accounts/              # registration, login, logout
│   └── templates/accounts/
├── jobs/                  # applications, interviews, AI analysis
│   ├── models.py          # JobApplication, Interview, Tag, AIAnalysis
│   ├── forms.py
│   ├── views.py
│   ├── ai_service.py      # Anthropic API integration
│   ├── management/commands/seed_demo_data.py
│   └── templates/jobs/
├── templates/base.html
└── static/css/style.css
```

## Setup Instructions

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/yeaminhossainfuhad-cloud/AI-Powered_Job_Application_Tracker.git
cd job_tracker
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
SECRET_KEY=replace-with-a-random-secret-key
DEBUG=True
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

Get an Anthropic API key at https://console.anthropic.com/. The AI features
(Job Description Analyzer, Job Match Analysis) will show a friendly error
message if this key is missing — the rest of the app works fine without it.

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create an admin user (optional, for /admin access)

```bash
python manage.py createsuperuser
```

### 6. (Optional) Seed demo data

Creates a demo user (`demo` / `demo12345` by default) with a few sample
applications so you can see the app populated immediately:

```bash
python manage.py seed_demo_data
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ — you'll be redirected to the login page.
Register a new account, or log in with the seeded demo user.

## AI Feature Details

`jobs/ai_service.py` wraps two calls to the Anthropic Messages API
(`model="claude-sonnet-4-6"`):

- `analyze_job_description(...)` — the required **AI Job Description Analyzer**.
  Sends the job title, company, and description, and asks Claude to return
  structured JSON with: `summary`, `required_skills`, `required_experience`,
  `important_technologies`, `interview_prep_suggestions`. The result is cached
  in the `AIAnalysis` model (one-to-one with `JobApplication`) and can be
  regenerated on demand.
- `analyze_job_match(...)` — the optional **AI Job Match Analysis**. Compares
  a free-text candidate profile against the job description and returns a
  `match_score` (0–100), `strengths`, `gaps`, and a `recommendation`.

Both functions raise `AIServiceError` on any failure (missing API key, network
error, malformed response), which the views catch and surface as a friendly
message via Django's messages framework — the app never crashes if the AI
service is unavailable.

## Key URLs

| Page                     | URL                                       |
|---------------------------|--------------------------------------------|
| Register                 | `/accounts/register/`                     |
| Login                     | `/accounts/login/`                        |
| Dashboard                | `/`                                        |
| Application list          | `/applications/`                          |
| Application detail        | `/applications/<id>/`                     |
| Create application        | `/applications/new/`                      |
| Edit application          | `/applications/<id>/edit/`                |
| AI Analysis               | `/applications/<id>/ai-analysis/`         |
| Django Admin              | `/admin/`                                 |

## Notes on Design Decisions

- Applications, interviews, tags, and AI analyses are all scoped to
  `request.user`; every queryset in `jobs/views.py` filters on `user=request.user`
  (or via the related application) so users can only ever see their own data.
- `Interview` has a `ForeignKey` to `JobApplication` (one application can have
  multiple interview rounds). Scheduling an interview automatically advances
  an application's status to "Interview" if it hasn't progressed that far yet.
- `AIAnalysis` is a `OneToOneField` on `JobApplication` — re-running the
  analyzer updates the existing record via `update_or_create` rather than
  creating duplicates.
- `Tag` is per-user (`unique_together = (name, owner)`) so two users can both
  have a "Remote" tag without collisions.

## Running Tests / Checking the Project

```bash
python manage.py check
python manage.py test
```

# Author

**Md. Yeamin Hossain Fuhad**

- Diploma in Engineering in Computer Science & Technology
- B.Sc. in Computer Science & Engineering, World University of Bangladesh
- IT Support, Popular Diagnostic Centre
- Aspiring Python Django Developer & Software Quality Assurance (SQA) Engineer
