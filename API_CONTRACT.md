# API Contract

Backend: `http://localhost:8000` (FastAPI, CORS enabled for
`http://localhost:5173`).

## `GET /fields`
Returns the dropdown taxonomy. No params.

**Response 200**
```json
{
  "fields": ["Biophysics", "Machine Learning", "Chemistry", "Neuroscience", "..."]
}
```

## `GET /search`
**Query params**
| name | type | required | notes |
|------|------|----------|-------|
| `field` | string | no | must be one of the values from `/fields`; omit or empty = no field filter |
| `query` | string | no | free-text research description; omit or empty = skip semantic ranking, field filter only |

**Response 200**
```json
{
  "results": [
    {
      "id": "conf-001",
      "name": "International Conference on Biophysics",
      "field": "Biophysics",
      "location": "Boston, MA, USA",
      "start_date": "2026-09-14",
      "end_date": "2026-09-17",
      "submission_deadline": "2026-06-01",
      "url": "https://example.org/icb2026",
      "score": 0.87
    }
  ]
}
```
- `results` is already sorted by `score` descending (highest relevance
  first). The frontend does NOT need to re-rank, only optionally re-sort by
  date/location per the Filter & Sort Controls skill.
- `score` is a float in `[0, 1]`; if `query` was empty, `score` reflects
  field-match only (1.0 if field matched or no field filter, 0.0 if it
  didn't match — results with 0.0 are excluded).

## Error shape
```json
{ "detail": "human-readable message" }
```
