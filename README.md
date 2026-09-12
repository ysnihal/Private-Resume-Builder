# Career Studio

A browser-based app for building resumes and cover letters, saved to your browser's local storage — no account, ever. The core app (everything below except "AI Generation") needs nothing but a browser: open `index.html` directly and it works standalone, no server required.

AI-tailored bullets and cover letter paragraphs are optional and need a small local Python backend to run - see [Architecture](#architecture) and [Local Setup](#local-setup) below. Nothing else in the app depends on it.

## Features

**My Info**
- One place to save your personal, contact, and address details, plus work history and education.
- Choose which fields auto-fill into new resumes and cover letters (Include all / Exclude all).
- Back up or restore your info as a `.txt` file.
- Back up or restore your whole Career Studio library (My Info, resumes, and cover letters) as a `.json` file.

**Resumes**
- Dashboard of all your saved resumes with live thumbnail previews.
- Create, rename, duplicate, or delete resumes.
- Recover deleted resumes and cover letters from Trash, or permanently remove them when ready.
- Search and sort your resume list.
- Track each resume's status: Applied, Interview, Offer, or Rejected.
- Full resume editor: reorder/add/hide sections, pick an accent color, edit any entry inline, and set field-level defaults.
- Keyboard shortcuts for faster editing.
- Start a linked cover letter directly from a resume’s target job details.
- Export a resume as a PDF or as an editable HTML file.

**Cover Letter**
- Editor for writing and formatting a cover letter, paragraph by paragraph.
- Word/paragraph count with on-target length guidance (250–400 words).
- Pulls your details from My Info automatically.
- Linked letters retain their source resume so you can jump back to it from the dashboard.
- Export as PDF or editable HTML.

**AI Generation** (requires the local backend - see below)
- "Generate with AI" on a resume's work-experience entries, Professional Summary, and Core Competencies.
- "Generate with AI" for cover letter paragraphs.
- Every suggestion is shown for review before anything is saved - bullets append safely; Summary, Skills, and paragraphs open a review dialog with Insert/Discard so nothing you wrote is overwritten silently.
- Uses your saved My Info profile and that document's Job Info as context - never invents facts outside them by design (the AI can still make mistakes; review what it writes).

**General**
- Light and dark mode (auto-detects your system theme, or toggle manually).
- The core app saves automatically in your browser - no server, no sign-in, ever required for it.
- Changes made in another open dashboard tab refresh the current library safely.

## Architecture

Two independent halves:

**Frontend** - `index.html`, `Resume.html`, `CoverLetter.html`: plain HTML/CSS/JS, no build step, no framework. All your data (profile, resumes, cover letters) lives in the browser's `localStorage` - the backend never stores or sees it beyond a single request in flight.

**Backend** - `backend/`: a small FastAPI (Python) server, used only for AI generation and to serve the three HTML files above (so the browser and the API share an origin and CORS never comes up). It never touches `localStorage` directly; the frontend sends whatever context a request needs (profile, job info, existing content) in the request body.

Inside `backend/`:
- `main.py` - the FastAPI app: every route, in one file.
- `providers/` - one class per AI service (Gemini, Anthropic, OpenAI, Groq), all implementing the same `generate(prompt, schema=None)` shape (`providers/base.py`). Swapping which one runs is one setting - `LLM_PROVIDER` in `.env` - never a code change. **Only Gemini currently implements structured (schema) output** - the other three raise a clear error if asked for it, rather than silently returning free text.
- `prompts/*.txt` - the actual wording sent to the AI, kept out of Python entirely so it can be edited without touching code. See `prompts/README.md`.
- `schemas.py` - the exact JSON shapes the AI must return (Pydantic models), used to validate every response.
- `structured.py` - turns a plain text-in/text-out model call into a validated result, retrying once with a correction prompt if the first response isn't valid JSON.
- `errors.py` - turns raw provider exceptions (rate limits, timeouts, bad keys, network failures) into a short human message plus an HTTP status code.
- `usage_log.py` - appends token counts and estimated cost to `usage_log.jsonl` (gitignored) after every real call.
- `profile_format.py` - turns the raw My Info profile into readable text for prompts.

## Local Setup

1. Install Python 3.12+.
2. Create a virtual environment somewhere **outside** any cloud-synced folder (OneDrive, Dropbox, etc. sync every installed package file, which is slow and unnecessary) - e.g. `python -m venv C:\dev\venvs\career-studio`.
3. Install dependencies: `<path-to-venv>\Scripts\python.exe -m pip install -r backend\requirements.txt`.
4. Copy `backend\.env.example` to `backend\.env` and paste in a real [Gemini API key](https://aistudio.google.com/) (free tier) after `GEMINI_API_KEY=`.
5. Run the server from the project's root folder: `<path-to-venv>\Scripts\python.exe -m uvicorn backend.main:app --reload`.
6. Open `http://127.0.0.1:8000/index.html` in your browser - not by double-clicking the file, since the AI buttons need the same-origin backend to work.

Gemini's free tier is limited (as of writing, `gemini-3.6-flash` allows about 20 requests per day, per Google's own error responses - verify current limits at [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits), since free-tier terms change). Hitting it shows a clear in-app message rather than a crash; the rest of the app keeps working normally.

## Running Tests

```
<path-to-venv>\Scripts\python.exe -m pytest backend/tests
```

No API key is required - the tests that touch AI generation mock the provider entirely, so they run the same with or without a real key in `.env`.
