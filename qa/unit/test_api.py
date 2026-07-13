"""Tests backend/app.py (the FastAPI layer) in-process via TestClient, per
API_CONTRACT.md. No server needs to be running."""
import pytest
from fastapi.testclient import TestClient

import app as app_module
from fields import FIELDS

client = TestClient(app_module.app)


def test_get_fields_returns_the_taxonomy():
    resp = client.get("/fields")
    assert resp.status_code == 200
    assert resp.json() == {"fields": FIELDS}


def test_search_no_params_returns_all_conferences_neutral_score():
    resp = client.get("/search")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert all(r["score"] == 1.0 for r in results)


def test_search_field_filters_results():
    resp = client.get("/search", params={"field": "Chemistry"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert all(r["field"] == "Chemistry" for r in results)


def test_search_unknown_field_returns_empty_list():
    resp = client.get("/search", params={"field": "Astrology"})
    assert resp.status_code == 200
    assert resp.json() == {"results": []}


def test_search_query_ranks_results_descending_by_score():
    resp = client.get("/search", params={"query": "deep learning generative models"})
    assert resp.status_code == 200
    scores = [r["score"] for r in resp.json()["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_result_shape_matches_api_contract():
    resp = client.get("/search", params={"query": "battery electrochemistry"})
    results = resp.json()["results"]
    assert len(results) > 0
    required = {
        "id", "name", "field", "topics", "location",
        "start_date", "end_date", "submission_deadline", "url", "score",
    }
    for r in results:
        assert required <= r.keys()


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_search_rejects_non_get_methods(method):
    resp = getattr(client, method)("/search")
    assert resp.status_code == 405


def test_cors_header_present_for_allowed_origin():
    resp = client.get("/fields", headers={"Origin": "http://localhost:5173"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"