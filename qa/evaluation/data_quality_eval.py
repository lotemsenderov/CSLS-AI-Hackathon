"""Structural / integrity checks on data/conferences.json — the "database".

Not about ranking quality (see relevance_eval.py); this is about whether the
dataset itself is well-formed enough for search.py to trust: valid dates,
unique ids, non-degenerate topics text, and (given the scraper is ML-only,
see backend/scraper.py) how skewed the field distribution has become.
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
for extra_dir in (ROOT / "backend", Path(__file__).parent):
    p = str(extra_dir)
    if p not in sys.path:
        sys.path.insert(0, p)

import search  # noqa: E402
from fields import FIELDS  # noqa: E402

REQUIRED_KEYS = {
    "id", "name", "field", "topics", "location",
    "start_date", "end_date", "submission_deadline", "url",
}
SPARSE_TOPIC_WORD_THRESHOLD = 2
IMBALANCE_WARNING_SHARE = 0.6


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def run() -> dict:
    conferences = search.load_conferences()
    total = len(conferences)

    ids = [c.get("id") for c in conferences]
    duplicate_ids = total - len(set(ids))

    missing_keys = [c["id"] for c in conferences if not REQUIRED_KEYS <= c.keys()]
    unknown_field = [c["id"] for c in conferences if c.get("field") not in FIELDS]

    invalid_dates, invalid_urls, sparse_topics = [], [], []
    topic_word_counts = []
    field_counts: dict[str, int] = {f: 0 for f in FIELDS}

    for c in conferences:
        field_counts[c.get("field")] = field_counts.get(c.get("field"), 0) + 1

        start, end, deadline = (
            _parse_date(c.get("start_date")),
            _parse_date(c.get("end_date")),
            _parse_date(c.get("submission_deadline")),
        )
        if not all([start, end, deadline]) or start > end or deadline > end:
            invalid_dates.append(c["id"])

        url = c.get("url", "")
        if not (url.startswith("http://") or url.startswith("https://")):
            invalid_urls.append(c["id"])

        word_count = len(c.get("topics", "").split())
        topic_word_counts.append(word_count)
        if word_count < SPARSE_TOPIC_WORD_THRESHOLD:
            sparse_topics.append(c["id"])

    largest_field, largest_count = max(field_counts.items(), key=lambda kv: kv[1])
    largest_share = largest_count / total if total else 0.0

    integrity_score = 1.0 - (
        (duplicate_ids + len(missing_keys) + len(unknown_field) + len(invalid_dates) + len(invalid_urls))
        / max(total, 1)
    )

    return {
        "total_conferences": total,
        "duplicate_ids": duplicate_ids,
        "missing_keys_count": len(missing_keys),
        "unknown_field_count": len(unknown_field),
        "invalid_dates_count": len(invalid_dates),
        "invalid_dates_ids": invalid_dates,
        "invalid_urls_count": len(invalid_urls),
        "sparse_topics_count": len(sparse_topics),
        "field_counts": field_counts,
        "largest_field": largest_field,
        "largest_field_share": largest_share,
        "imbalance_warning": largest_share >= IMBALANCE_WARNING_SHARE,
        "topic_word_counts": topic_word_counts,
        "integrity_score": max(0.0, integrity_score),
    }


if __name__ == "__main__":
    import json

    result = run()
    print(json.dumps({k: v for k, v in result.items() if k != "topic_word_counts"}, indent=2))