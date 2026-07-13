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
```
backend/   FastAPI app + matching logic (Search Engine module)
frontend/  Gradio UI (Python)
data/      Static seed dataset used as the "database" for the MVP
```

## Quickstart

Backend (start first, listens on port 8000):
```
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Frontend (Gradio, calls the backend over HTTP):
```
cd frontend
pip install -r requirements.txt
python app.py
```
