"""
Turns the raw "My Info" profile object - exactly as stored in the
browser's resumeBuilderProfileV1 (see index.html) - into one readable
text block for AI prompts. Centralized here so resume and cover-letter
generation format it the same way.

Field names below (jobTitle, employer, startDate, endDate, school,
degree, fieldOfStudy, ...) match index.html's own normalizeProfile()
exactly - verified against index.html:2006-2028, not guessed.

Note: this ignores each field's individual "include" toggle
(includeFields) and includes everything present. Those toggles control
what a NEW resume/letter gets prefilled with, not necessarily what the AI
should be allowed to know about - a reasonable first-pass choice, not a
verified requirement. Worth revisiting if it ever surfaces something you
specifically excluded.
"""


def _format_date_range(start: str, end: str, current: bool = False) -> str:
    if current:
        end = "Present"
    return " - ".join(part for part in [start, end] if part)


def format_candidate_background(profile: dict | None) -> str:
    profile = profile or {}
    lines: list[str] = []

    work_experience = profile.get("workExperience") or []
    if work_experience:
        lines.append("WORK EXPERIENCE:")
        for job in work_experience:
            title = job.get("jobTitle", "")
            employer = job.get("employer", "")
            dates = _format_date_range(job.get("startDate", ""), job.get("endDate", ""), job.get("current", False))
            header = " at ".join(part for part in [title, employer] if part)
            if dates:
                header = f"{header} ({dates})" if header else dates
            lines.append(f"* {header or 'Untitled role'}")
            notes = job.get("notes", "")
            if notes:
                lines.append(f"  {notes}")

    education = profile.get("education") or []
    if education:
        lines.append("EDUCATION:")
        for item in education:
            degree = item.get("degree", "")
            field = item.get("fieldOfStudy", "")
            school = item.get("school", "")
            dates = _format_date_range(item.get("startDate", ""), item.get("endDate", ""))
            degree_field = " in ".join(part for part in [degree, field] if part)
            header = " - ".join(part for part in [degree_field, school] if part)
            if dates:
                header = f"{header} ({dates})" if header else dates
            if header:
                lines.append(f"* {header}")

    achievements = profile.get("achievements") or ""
    if achievements:
        lines.append("ACHIEVEMENTS:")
        lines.append(achievements)

    hobbies = profile.get("hobbies") or ""
    if hobbies:
        lines.append("HOBBIES / INTERESTS:")
        lines.append(hobbies)

    return "\n".join(lines) if lines else "(no profile information provided)"
