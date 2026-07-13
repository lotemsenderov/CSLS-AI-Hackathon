import json
from datetime import date

import scraper


def _entry(**overrides):
    base = {
        "title": "ExampleConf",
        "year": 2026,
        "id": "exampleconf26",
        "link": "https://example.org/exampleconf26",
        "deadline": "2026-01-01 23:59:59",
        "place": "Remote",
        "start": date(2026, 3, 1),
        "end": date(2026, 3, 3),
        "sub": "ML",
    }
    base.update(overrides)
    return base


def test_normalize_maps_all_fields():
    result = scraper.normalize(_entry())
    assert result == {
        "id": "scraped-exampleconf26",
        "name": "ExampleConf 2026",
        "field": "Machine Learning",
        "topics": "ExampleConf, machine learning",
        "location": "Remote",
        "start_date": "2026-03-01",
        "end_date": "2026-03-03",
        "submission_deadline": "2026-01-01",
        "url": "https://example.org/exampleconf26",
    }


def test_normalize_handles_list_of_sub_areas():
    result = scraper.normalize(_entry(sub=["ML", "CV"]))
    assert "machine learning" in result["topics"]
    assert "computer vision" in result["topics"]


def test_normalize_falls_back_to_lowercased_title_when_id_missing():
    result = scraper.normalize(_entry(id=None))
    assert result["id"] == "scraped-exampleconf"


def test_normalize_strips_html_and_unescapes_note():
    result = scraper.normalize(_entry(note="See <a href='x'>details</a> &amp; more"))
    assert "<a" not in result["topics"]
    assert "See details & more" in result["topics"]


def test_normalize_returns_none_when_required_field_missing():
    for missing in ["start", "end", "deadline", "place", "link"]:
        assert scraper.normalize(_entry(**{missing: None})) is None


def test_merge_into_dataset_dedupes_by_id(tmp_path, monkeypatch):
    data_path = tmp_path / "conferences.json"
    data_path.write_text(json.dumps([{"id": "existing-1", "field": "Chemistry"}]))
    monkeypatch.setattr(scraper, "DATA_PATH", data_path)

    added = scraper.merge_into_dataset([
        {"id": "existing-1", "field": "Chemistry"},  # duplicate, should be skipped
        {"id": "scraped-new-1", "field": "Machine Learning"},
    ])

    assert added == 1
    result = json.loads(data_path.read_text())
    assert [c["id"] for c in result] == ["existing-1", "scraped-new-1"]
