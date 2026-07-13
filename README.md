# Conference Finder

A tool to help researchers find relevant academic conferences, matching a
broad scientific field (dropdown) and/or a free-text description of their
research against a set of conferences.

Start here:

- [PLAN.md](PLAN.md) — architecture, tech stack, database design, timeline.
- [SKILLS.md](SKILLS.md) — modular skills, one per teammate/branch.
- [API_CONTRACT.md](API_CONTRACT.md) — the request/response shapes shared
  between the frontend and backend.

## Layout

```text
backend/   FastAPI app + matching logic (Search Engine module)
frontend/  Gradio UI (Python)
data/      Static seed dataset used as the "database" for the MVP
```

## Quickstart

Requires **Python 3.10+** (the backend uses `str | None` / `list[dict]`
type-hint syntax, which is a hard requirement on older interpreters —
check with `python3 --version` before you start, especially on Windows
where the default install can be older).

Backend (start first, listens on port 8000):

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Frontend (Gradio, calls the backend over HTTP):

```bash
cd frontend
pip install -r requirements.txt
python app.py
```

Run the tests:

```bash
cd backend
pytest
```

Pull in more real conferences (currently ML/AI only, from the public
`paperswithcode/ai-deadlines` dataset — see `backend/scraper.py` for
caveats):

```bash
cd backend
python scraper.py
```
