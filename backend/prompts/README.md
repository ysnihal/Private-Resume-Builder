# Prompts

Every `.txt` file in this folder is sent to the AI more or less as-is - you
can edit the wording, tone, or instructions in any of them and never touch
a `.py` file.

## Placeholders

A placeholder looks like `$this`. `backend/prompts.py` fills these in
before sending the text to the AI. If you rename or remove a placeholder
from a `.txt` file, update the matching Python call in `backend/main.py`
(or wherever that prompt is loaded) to match - the loader will raise an
error naming the missing value rather than silently sending `$this`
literally to the AI.

## Files

- `test_connectivity.txt` - the one-off "are you alive" check behind
  `/api/test-llm`. No placeholders.
- `resume_bullets.txt` - generates bullets for one work-experience entry.
  Wired to the real "Generate with AI" button next to "Add bullet" in
  Resume.html (POST /api/generate/resume-bullets).
- `resume_summary.txt` - generates the Professional Summary paragraph.
  Wired to "Generate with AI" in the field panel when Summary is selected
  (POST /api/generate/resume-field).
- `resume_skills.txt` - generates the Core Competencies list. Same
  endpoint as summary, different `field` value.
- `cover_letter_paragraphs.txt` - generates cover letter paragraphs.
  Wired to "Generate with AI" in CoverLetter.html
  (POST /api/generate/cover-letter-paragraphs).

## A note on one prompt that's NOT here

The "your JSON was invalid, try again" correction text in
`backend/structured.py` is deliberately kept in code, not as a template.
It's part of the retry mechanism's own logic (it always has to exist,
always has to say roughly that), not content you'd want to tune - so
moving it here seemed more likely to create a confusing hidden dependency
than to help. Say if you'd rather it lived here too.
