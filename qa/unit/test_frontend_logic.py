"""Tests frontend/app.py's pure logic (fetch_fields, run_search, show_more,
clear_filters, date filtering, card rendering) with `requests` mocked out —
no backend server, no browser.

Loaded by file path under a private module name (not sys.path + `import
app`) because frontend/app.py and backend/app.py share a filename, and
frontend/app.py imports gradio at module scope, which this dev environment
doesn't have installed. A minimal fake `gradio` module is injected into
sys.modules before loading so the module-level `gr.Blocks(...)` UI
construction in frontend/app.py succeeds without the real dependency.
"""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

FRONTEND_APP_PATH = Path(__file__).parent.parent.parent / "frontend" / "app.py"


@pytest.fixture
def frontend_app(monkeypatch):
    fake_gradio = MagicMock()
    fake_gradio.update.side_effect = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "gradio", fake_gradio)

    spec = importlib.util.spec_from_file_location("frontend_app_under_test", FRONTEND_APP_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json_data


def _conference(**overrides):
    base = {
        "id": "c1", "name": "Example Conf", "field": "Chemistry",
        "topics": "catalysis", "location": "Boston",
        "start_date": "2026-03-01", "end_date": "2026-03-03",
        "submission_deadline": "2026-01-01", "url": "https://example.org",
        "score": 0.8231,
    }
    base.update(overrides)
    return base


# --- fetch_fields ----------------------------------------------------------

def test_fetch_fields_prepends_any_field_option(frontend_app, monkeypatch):
    monkeypatch.setattr(
        frontend_app.requests, "get",
        lambda *a, **kw: FakeResponse({"fields": ["Chemistry", "Neuroscience"]}),
    )
    result = frontend_app.fetch_fields()
    assert result["choices"] == ["(Any field)", "Chemistry", "Neuroscience"]
    assert result["value"] == "(Any field)"


# --- _filter_by_date ---------------------------------------------------------

def test_filter_by_date_no_bounds_returns_all(frontend_app):
    results = [_conference(start_date="2026-01-01"), _conference(start_date="2026-06-01")]
    assert frontend_app._filter_by_date(results, None, None) == results


def test_filter_by_date_applies_lower_and_upper_bound(frontend_app):
    results = [
        _conference(id="early", start_date="2026-01-01"),
        _conference(id="mid", start_date="2026-03-15"),
        _conference(id="late", start_date="2026-08-01"),
    ]
    filtered = frontend_app._filter_by_date(results, "2026-02-01", "2026-06-01")
    assert [r["id"] for r in filtered] == ["mid"]


# --- card / status rendering -------------------------------------------------

def test_render_cards_empty_shows_friendly_message(frontend_app):
    html = frontend_app._render_cards([])
    assert "No matching conferences found" in html


def test_render_cards_includes_result_details(frontend_app):
    html = frontend_app._render_cards([_conference(score=0.8231)])
    assert "Example Conf" in html
    assert "Boston" in html
    assert "https://example.org" in html
    assert "Chemistry" in html
    assert "82%" in html  # round(0.8231 * 100)


def test_status_text_empty_when_no_total(frontend_app):
    assert frontend_app._status_text(0, 0) == ""


def test_status_text_reports_shown_and_total(frontend_app):
    assert "Showing 3 of 10" in frontend_app._status_text(3, 10)


# --- run_search: request building -------------------------------------------

def test_run_search_omits_field_param_when_any_field_selected(frontend_app, monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params or {})
        return FakeResponse({"results": []})

    monkeypatch.setattr(frontend_app.requests, "get", fake_get)
    frontend_app.run_search("(Any field)", "protein folding", None, None)
    assert "field" not in captured
    assert captured["query"] == "protein folding"


def test_run_search_omits_query_param_when_blank(frontend_app, monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured.update(params or {})
        return FakeResponse({"results": []})

    monkeypatch.setattr(frontend_app.requests, "get", fake_get)
    frontend_app.run_search("Chemistry", "", None, None)
    assert captured == {"field": "Chemistry"}


# --- run_search: pagination & result shape -----------------------------------

def test_run_search_paginates_to_page_size(frontend_app, monkeypatch):
    fifteen_results = [_conference(id=str(i)) for i in range(15)]
    monkeypatch.setattr(
        frontend_app.requests, "get",
        lambda *a, **kw: FakeResponse({"results": fifteen_results}),
    )
    results, shown, status_html, cards_html, load_more_update = frontend_app.run_search(
        "(Any field)", "", None, None
    )
    assert len(results) == 15
    assert shown == frontend_app.PAGE_SIZE == 10
    assert "Showing 10 of 15" in status_html
    assert load_more_update == {"visible": True}


def test_run_search_hides_load_more_when_all_results_shown(frontend_app, monkeypatch):
    three_results = [_conference(id=str(i)) for i in range(3)]
    monkeypatch.setattr(
        frontend_app.requests, "get",
        lambda *a, **kw: FakeResponse({"results": three_results}),
    )
    _, shown, _, _, load_more_update = frontend_app.run_search("(Any field)", "", None, None)
    assert shown == 3
    assert load_more_update == {"visible": False}


def test_run_search_applies_date_filter_before_paginating(frontend_app, monkeypatch):
    results = [
        _conference(id="early", start_date="2026-01-01"),
        _conference(id="late", start_date="2026-08-01"),
    ]
    monkeypatch.setattr(
        frontend_app.requests, "get",
        lambda *a, **kw: FakeResponse({"results": results}),
    )
    filtered, shown, status_html, _, _ = frontend_app.run_search(
        "(Any field)", "", "2026-06-01", None
    )
    assert [r["id"] for r in filtered] == ["late"]
    assert shown == 1
    assert "Showing 1 of 1" in status_html


def test_run_search_network_error_returns_empty_state(frontend_app, monkeypatch):
    import requests

    def raise_error(*a, **kw):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(frontend_app.requests, "get", raise_error)
    results, shown, status_html, cards_html, load_more_update = frontend_app.run_search(
        "(Any field)", "catalysis", None, None
    )
    assert results == []
    assert shown == 0
    assert status_html == ""
    assert "Error contacting backend" in cards_html
    assert "connection refused" in cards_html
    assert load_more_update == {"visible": False}


# --- show_more ---------------------------------------------------------------

def test_show_more_advances_by_page_size(frontend_app):
    results = [_conference(id=str(i)) for i in range(25)]
    new_shown, status_html, cards_html, load_more_update = frontend_app.show_more(results, 10)
    assert new_shown == 20
    assert "Showing 20 of 25" in status_html
    assert load_more_update == {"visible": True}


def test_show_more_caps_at_total_results(frontend_app):
    results = [_conference(id=str(i)) for i in range(25)]
    new_shown, status_html, cards_html, load_more_update = frontend_app.show_more(results, 20)
    assert new_shown == 25
    assert load_more_update == {"visible": False}


# --- clear_filters -------------------------------------------------------------

def test_clear_filters_resets_field_and_dates(frontend_app):
    assert frontend_app.clear_filters() == (frontend_app.ANY_FIELD, None, None)