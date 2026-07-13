"""Structural correctness checks on data/conferences.json as pytest
assertions. The richer scoring/distribution view of the same data lives in
qa/evaluation/data_quality_eval.py and shows up on the HTML dashboard."""
from datetime import date

import search

REQUIRED_KEYS = {
    "id", "name", "field", "topics", "location",
    "start_date", "end_date", "submission_deadline", "url",
}


def _conferences():
    return search.load_conferences()


def test_dataset_is_nonempty():
    assert len(_conferences()) > 0


def test_no_duplicate_ids():
    ids = [c["id"] for c in _conferences()]
    assert len(ids) == len(set(ids))


def test_every_conference_has_required_keys():
    for c in _conferences():
        missing = REQUIRED_KEYS - c.keys()
        assert not missing, f"{c.get('id')} missing keys: {missing}"


def test_every_conference_has_nonempty_topics():
    for c in _conferences():
        assert c.get("topics", "").strip(), f"{c['id']} has empty topics text"


def test_dates_are_valid_and_ordered():
    bad = []
    for c in _conferences():
        try:
            start = date.fromisoformat(c["start_date"])
            end = date.fromisoformat(c["end_date"])
            deadline = date.fromisoformat(c["submission_deadline"])
        except (KeyError, ValueError):
            bad.append(c["id"])
            continue
        if start > end or deadline > end:
            bad.append(c["id"])
    assert not bad, f"conferences with invalid/out-of-order dates: {bad}"


def test_urls_use_http_scheme():
    bad = [c["id"] for c in _conferences() if not c.get("url", "").startswith(("http://", "https://"))]
    assert not bad, f"conferences with non-http url: {bad}"