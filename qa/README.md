# qa/ — test & evaluation suite

Tests every module in the project (`backend/fields.py`, `search.py`,
`app.py`, `frontend/app.py`, `data/conferences.json`) from outside
`backend/` and `frontend/`, plus scores search relevance and dataset
integrity with plots on an HTML dashboard.

```
qa/
  unit/         pytest — correctness per module (pass/fail)
  evaluation/   scoring logic — relevance, data quality (returns metrics, not just pass/fail)
  report/       renders unit + evaluation results into one HTML dashboard
  reports/      generated output (index.html, junit.xml) — overwritten on every run
```

## Run it

```bash
pip install -r qa/requirements.txt -r backend/requirements.txt
python qa/run_all.py            # writes qa/reports/index.html
python qa/run_all.py --open     # also opens it in a browser
```

Or just the pytest suite, without the dashboard:

```bash
pytest qa/unit
```

## What's being tested

- **`unit/test_fields.py`** — the field taxonomy is well-formed and matches
  what's actually used in the dataset.
- **`unit/test_data_integrity.py`** — every conference has the required
  keys, valid/ordered dates, an http(s) url, non-empty topics.
- **`unit/test_api.py`** — `backend/app.py`'s `/fields` and `/search`
  endpoints, in-process via FastAPI's `TestClient` (no server needed),
  against `API_CONTRACT.md`.
- **`unit/test_frontend_logic.py`** — `frontend/app.py`'s pure logic
  (`fetch_fields`, `run_search`, `show_more`, `clear_filters`, date
  filtering, card rendering) with `requests` mocked out. Loaded by file
  path under a private module name, with a fake `gradio` injected into
  `sys.modules`, because `frontend/app.py` and `backend/app.py` share a
  filename and this dev environment doesn't have `gradio` installed.

## What's being scored (the "smart" part)

Pass/fail isn't enough for the ranking logic — a search engine can be
"passing" and still be mediocre. `evaluation/relevance_eval.py` scores
`backend/search.py`'s TF-IDF ranker against a hand-labeled gold set
(`evaluation/gold_queries.py`): realistic research-description paraphrases
mapped to an expected field, run through the *unfiltered* search so the
ranker has to surface the right conferences out of the whole dataset on
lexical signal alone.

The dataset is heavily skewed toward Machine Learning (the scraper only
covers ML/AI — see `backend/scraper.py`), so field-match accuracy on an ML
query is cheap to get right by base rate alone. To keep the score honest:

- **Rare-field queries** (Biophysics, Chemistry, Neuroscience, Computational
  Biology) are scored on **precision@5** and **MRR** — a strong signal,
  since those fields are a small minority of the dataset.
- **ML subfield queries** (computer vision, robotics, NLP, ...) are scored
  on **top-1 keyword hit rate** against the conference's own subfield tag,
  since field-match precision there is inflated by the base rate.
- **Score discrimination** — the gap between the top result's score and the
  rest — sanity-checks that the ranker is actually differentiating, not
  returning near-uniform scores.

`evaluation/data_quality_eval.py` scores the dataset itself: field-balance
skew, invalid/out-of-order dates, malformed urls, duplicate ids, and the
distribution of topics-text length (a near-empty `topics` field silently
kills TF-IDF matching for that conference).

Both are surfaced on the dashboard as stat tiles + bar charts / histograms,
not just a pass/fail line — the point is to see *where* it's weak, not just
*whether* it's weak.