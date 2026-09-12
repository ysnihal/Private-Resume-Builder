"""
The exact JSON shapes the AI is allowed to return.

Gemini is constrained to produce JSON matching one of these exactly (see
backend/providers/gemini_provider.py) and every field is validated before
the rest of the app ever sees it.
"""

from pydantic import BaseModel


class ResumeBullets(BaseModel):
    """One work-experience entry's worth of bullet points, for
    Resume.html's entry `notes` field (one bullet per array item)."""

    bullets: list[str]


class CoverLetterParagraph(BaseModel):
    """Matches the {id, text} shape CoverLetter.html already uses for each
    paragraph card. `id` is either an existing paragraph's id (replace it)
    or left blank for a new paragraph."""

    id: str
    text: str


class CoverLetterParagraphs(BaseModel):
    paragraphs: list[CoverLetterParagraph]


class ResumeSummary(BaseModel):
    """A single generated Professional Summary paragraph."""

    summary: str


class ResumeSkills(BaseModel):
    """A generated Core Competencies list - Resume.html's skills field
    stores these joined by commas/newlines (see splitCompetencies in
    Resume.html), so the frontend joins this list itself."""

    skills: list[str]
