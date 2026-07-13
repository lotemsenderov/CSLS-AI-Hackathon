# Conference-Finder — Development Plan

## Context
We're building a tool that matches researchers to relevant academic
conferences, split into two modules: **Search Engine (Logic)** and
**User Interface**. Build budget: **~1 hour**, **3-4 people** working in
parallel via Git branches.

Decisions:
- Stack: **Python (FastAPI)** backend, **React (Vite)** frontend.
- Matching: hybrid — exact/keyword filter on a broad-field dropdown, then a
  **TF-IDF + cosine similarity** re-rank of free text against conference
  descriptions. This is the practical stand-in for "semantic" matching
  given the time budget (pure local compute via scikit-learn, no API keys,
  no network latency). Upgrade path: swap in `sentence-transformers` or an
  LLM embeddings call later without changing the interface.
- Data: a **static, pre-seeded sample dataset** (`data/conferences.json`),
  not live scraping. A real scraper is a documented stretch/future skill.

## Architecture

```
frontend/ (React + Vite)
  SearchForm → GET http://localhost:8000/search?field=..&query=..
  ResultsList (client-side sort/filter by date, location)
        |
        v  JSON over REST (CORS enabled)
backend/ (FastAPI)
  /fields   -> returns the dropdown taxonomy (shared contract with UI)
  /search   -> field filter + TF-IDF cosine rank over data/conferences.json
data/
  conferences.json  (~20-30 hand-seeded sample conferences)
```

## Database design
No real DB in the 1-hour MVP — `data/conferences.json` is the "database,"
shaped exactly like a future Postgres `conferences` table so it's a
drop-in upgrade later:

```json
{
  "id": "str",
  "name": "str",
  "field": "str (matches dropdown taxonomy)",
  "topics": "str (free text used for TF-IDF matching: description/CFP text)",
  "location": "str",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "submission_deadline": "YYYY-MM-DD",
  "url": "str"
}
```
Future: this becomes a Postgres table with the same columns (+ indexes on
`field`, `start_date`) once a real scraper populates it continuously.

## Connecting the modules
- REST JSON, FastAPI `CORSMiddleware` allowing the Vite dev origin
  (`http://localhost:5173`).
- The API contract is written down first (see [API_CONTRACT.md](API_CONTRACT.md))
  so frontend and backend can be built in parallel against an agreed shape
  instead of blocking on each other.

## Step-by-step plan (1 hour, 3-4 people)

1. **(0-5 min, together)** Skeleton + `API_CONTRACT.md` already created
   (this commit). Everyone reads it, then branches off `main`.
2. **(5-45 min, parallel branches)** — see [SKILLS.md](SKILLS.md) for the
   full skill/owner breakdown:
   - `feature/data-seed` — fill out `data/conferences.json`.
   - `feature/matching-logic` — implement `backend/search.py`.
   - `feature/api` — wire up `backend/app.py`.
   - `feature/frontend-ui` — build the React form + results UI against the
     mock response in `API_CONTRACT.md`.
3. **(45-55 min)** Merge branches, point frontend at the live backend, fix
   any contract mismatches.
4. **(55-60 min)** Smoke-test 2-3 demo queries end to end.

**Git note:** given the time pressure, favor short-lived branches merged
fast (even direct pushes with a heads-up in chat) over a full PR review
cycle — this is a hackathon-speed exception, not a general practice.

## Post-hackathon roadmap (not in scope now)
- Replace TF-IDF with real embeddings (sentence-transformers / LLM API).
- Add scraper sources for Biophysics/Chemistry/Neuroscience (currently
  `backend/scraper.py` only covers ML/AI, via `paperswithcode/ai-deadlines`)
  and run it on a schedule instead of on demand.
- Move `conferences.json` into Postgres.
- Pagination, auth, saved searches, deployment.
