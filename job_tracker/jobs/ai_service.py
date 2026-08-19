"""
AI integration for the Job Application Tracker.

This module wraps calls to the Anthropic API (Claude) to implement the
required AI feature: analyzing a job description to extract a summary,
required skills, required experience, important technologies, and
interview preparation suggestions. It also offers an optional AI Job
Match Analysis against a short user profile.

The module is intentionally defensive: if no API key is configured, or the
API call fails for any reason, it raises AIServiceError with a friendly
message so the view can show it to the user instead of crashing.
"""
import json
import os

from django.conf import settings

try:
    import anthropic
except ImportError:  # pragma: no cover - handled at runtime with a friendly error
    anthropic = None

MODEL_NAME = "claude-sonnet-4-6"

ANALYZER_SYSTEM_PROMPT = (
    "You are an expert technical recruiter and career coach. You analyze job "
    "descriptions and return ONLY valid JSON (no markdown fences, no preamble, "
    "no commentary) matching exactly this schema:\n"
    "{\n"
    '  "summary": "2-4 sentence plain-English summary of the role",\n'
    '  "required_skills": ["skill 1", "skill 2", ...],\n'
    '  "required_experience": "short string describing years/level required",\n'
    '  "important_technologies": ["tech 1", "tech 2", ...],\n'
    '  "interview_prep_suggestions": ["suggestion 1", "suggestion 2", ...]\n'
    "}\n"
    "Keep each list to at most 8 concise items. If the job description does not "
    "clearly specify something, make a brief, reasonable inference and say so."
)

MATCH_SYSTEM_PROMPT = (
    "You are an expert technical recruiter. Compare a candidate profile against "
    "a job description and return ONLY valid JSON (no markdown fences) matching:\n"
    "{\n"
    '  "match_score": <integer 0-100>,\n'
    '  "strengths": ["..."],\n'
    '  "gaps": ["..."],\n'
    '  "recommendation": "one short paragraph of advice for this candidate"\n'
    "}"
)


class AIServiceError(Exception):
    """Raised when the AI feature cannot be completed."""


def _get_client():
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic is None:
        raise AIServiceError(
            "The 'anthropic' Python package is not installed. Run: pip install anthropic"
        )
    if not api_key:
        raise AIServiceError(
            "No ANTHROPIC_API_KEY is configured. Add it to your .env file to enable AI features."
        )
    return anthropic.Anthropic(api_key=api_key)


def _extract_json(text):
    """Claude is instructed to return raw JSON, but strip code fences defensively
    in case they slip in."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIServiceError(f"AI response was not valid JSON: {exc}") from exc


def analyze_job_description(job_title, company_name, job_description):
    """Calls Claude to analyze a job description. Returns a dict with keys:
    summary, required_skills, required_experience, important_technologies,
    interview_prep_suggestions, raw_response.
    """
    if not job_description or not job_description.strip():
        raise AIServiceError("This application has no job description to analyze yet.")

    client = _get_client()

    user_prompt = (
        f"Job Title: {job_title}\n"
        f"Company: {company_name}\n\n"
        f"Job Description:\n{job_description}\n\n"
        "Analyze this job description now and respond with the JSON schema only."
    )

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1500,
            system=ANALYZER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # noqa: BLE001 - surface any API error to the UI
        raise AIServiceError(f"AI request failed: {exc}") from exc

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    raw_text = "\n".join(text_blocks)
    data = _extract_json(raw_text)

    def join_list(value):
        if isinstance(value, list):
            return "\n".join(str(v) for v in value)
        return str(value) if value else ""

    return {
        "summary": data.get("summary", ""),
        "required_skills": join_list(data.get("required_skills")),
        "required_experience": data.get("required_experience", ""),
        "important_technologies": join_list(data.get("important_technologies")),
        "interview_prep_suggestions": join_list(data.get("interview_prep_suggestions")),
        "raw_response": raw_text,
    }


def analyze_job_match(job_title, company_name, job_description, candidate_profile):
    """Optional AI feature: compares a free-text candidate profile against the
    job description and returns a match score + strengths/gaps/recommendation."""
    if not job_description or not job_description.strip():
        raise AIServiceError("This application has no job description to analyze yet.")
    if not candidate_profile or not candidate_profile.strip():
        raise AIServiceError("Add a short profile/resume summary to run a match analysis.")

    client = _get_client()

    user_prompt = (
        f"Job Title: {job_title}\nCompany: {company_name}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Candidate Profile:\n{candidate_profile}\n\n"
        "Compare them now and respond with the JSON schema only."
    )

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            system=MATCH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        raise AIServiceError(f"AI request failed: {exc}") from exc

    text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    raw_text = "\n".join(text_blocks)
    data = _extract_json(raw_text)
    return {
        "match_score": data.get("match_score"),
        "strengths": data.get("strengths", []),
        "gaps": data.get("gaps", []),
        "recommendation": data.get("recommendation", ""),
        "raw_response": raw_text,
    }
