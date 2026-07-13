# Skills Breakdown

Each skill below is a self-contained unit of work: one person, one branch,
one clear file to own. Pick your skill, branch off `main` as
`feature/<skill-branch>`, and merge back once it works against
[API_CONTRACT.md](API_CONTRACT.md).

## Search Engine (Logic) module

| # | Skill | Owns | Branch |
|---|-------|------|--------|
| 1 | **Data Schema & Seed Data** — hand-write ~20-30 sample conferences matching the schema in [PLAN.md](PLAN.md#database-design). | `data/conferences.json` | `feature/data-seed` |
| 2 | **Field Taxonomy** — the fixed list of broad scientific fields for the dropdown; shared contract with the UI. | `backend/fields.py` | `feature/data-seed` |
| 3 | **Keyword/Field Filter** — exact-match filter on the chosen dropdown field. | `backend/search.py` | `feature/matching-logic` |
| 4 | **Semantic Text Matcher** — TF-IDF/cosine ranking of free text vs. each conference's `topics`. Upgrade path: swap in `sentence-transformers` or an LLM embeddings call later, same function signature. | `backend/search.py` | `feature/matching-logic` |
| 5 | **Result Ranker/Merger** — combines the field filter and the semantic score into one ranked list. | `backend/search.py` | `feature/matching-logic` |
| 6 | **API Layer** — FastAPI `/search` and `/fields` endpoints, request validation, CORS. | `backend/app.py` | `feature/api` |
| 7 | *(Stretch/future — not in the 1-hr MVP)* **Live Scraper** — a real scraper per conference-listing site, normalizing results into the schema above. | `backend/scraper.py` (not created yet) | `feature/scraper` |

Skills 1-2 and 3-5 are small enough that one person can usually cover both
in their pair (e.g. one person does data + taxonomy, another does the three
matching functions) — split further only if you have 4+ people.

## User Interface module

| # | Skill | Owns | Branch |
|---|-------|------|--------|
| 1 | **Search Input Form** — dropdown (bound to Field Taxonomy via `GET /fields`) + free-text box, submit handling. | `frontend/src/components/SearchForm.jsx` | `feature/frontend-ui` |
| 2 | **Results Display** — renders the conference list/cards returned by `/search`. | `frontend/src/components/ResultsList.jsx` | `feature/frontend-ui` |
| 3 | **Filter & Sort Controls** — client-side sort/filter of the already-fetched results by date and location. | `frontend/src/components/ResultsList.jsx` | `feature/frontend-ui` |
| 4 | **API Client** — fetch wrapper for `/fields` and `/search`, loading/error states. | `frontend/src/api.js` | `feature/frontend-ui` |
| 5 | **Styling/Layout** — page shell, basic responsive layout. Lowest priority under time pressure — do last if time allows. | `frontend/src/App.jsx`, CSS | `feature/frontend-ui` |

All 5 UI skills live on one branch (`feature/frontend-ui`) since they're
tightly coupled files in a small app — split into per-component branches
only if you have 2+ people free for frontend.

## Suggested assignment for a 4-person team
- **Person A:** Search skills 1-2 (Data Schema, Field Taxonomy)
- **Person B:** Search skills 3-5 (Filter, Matcher, Ranker)
- **Person C:** Search skill 6 (API Layer) — start once skills 3-5 have a
  stub function signature agreed, even before they're finished
- **Person D:** All UI skills (1-5), building against
  [API_CONTRACT.md](API_CONTRACT.md) mock responses until the real backend
  is ready to integrate
