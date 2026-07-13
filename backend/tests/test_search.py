import pytest

import search

REQUIRED_KEYS = {
    "id", "name", "field", "topics", "location",
    "start_date", "end_date", "submission_deadline", "url",
}


@pytest.fixture
def sample_conferences():
    return [
        {
            "id": "a", "name": "A", "field": "Biophysics",
            "topics": "protein folding membrane dynamics single-molecule imaging",
            "location": "X", "start_date": "2026-01-01", "end_date": "2026-01-02",
            "submission_deadline": "2025-12-01", "url": "u1",
        },
        {
            "id": "b", "name": "B", "field": "Machine Learning",
            "topics": "deep learning neural networks transformers",
            "location": "Y", "start_date": "2026-02-01", "end_date": "2026-02-02",
            "submission_deadline": "2025-12-01", "url": "u2",
        },
        {
            "id": "c", "name": "C", "field": "Biophysics",
            "topics": "cryo electron microscopy structural biology",
            "location": "Z", "start_date": "2026-03-01", "end_date": "2026-03-02",
            "submission_deadline": "2025-12-01", "url": "u3",
        },
    ]


# --- filter_by_field ---------------------------------------------------

def test_filter_by_field_none_returns_all(sample_conferences):
    result = search.filter_by_field(sample_conferences, None)
    assert result == sample_conferences
    assert result is not sample_conferences  # returns a new list, doesn't mutate caller's


def test_filter_by_field_empty_string_returns_all(sample_conferences):
    assert search.filter_by_field(sample_conferences, "") == sample_conferences


def test_filter_by_field_matches_only_that_field(sample_conferences):
    result = search.filter_by_field(sample_conferences, "Biophysics")
    assert [c["id"] for c in result] == ["a", "c"]


def test_filter_by_field_unknown_field_returns_empty(sample_conferences):
    assert search.filter_by_field(sample_conferences, "Astrology") == []


def test_filter_by_field_empty_input_returns_empty():
    assert search.filter_by_field([], "Biophysics") == []


# --- rank_by_query -------------------------------------------------------

def test_rank_by_query_empty_conferences_returns_empty():
    assert search.rank_by_query([], "protein folding") == []


def test_rank_by_query_none_query_gives_neutral_score(sample_conferences):
    result = search.rank_by_query(sample_conferences, None)
    assert len(result) == len(sample_conferences)
    assert all(c["score"] == 1.0 for c in result)


def test_rank_by_query_empty_string_query_gives_neutral_score(sample_conferences):
    result = search.rank_by_query(sample_conferences, "")
    assert all(c["score"] == 1.0 for c in result)


def test_rank_by_query_does_not_mutate_input(sample_conferences):
    search.rank_by_query(sample_conferences, "protein folding")
    assert "score" not in sample_conferences[0]


def test_rank_by_query_scores_relevant_conference_highest(sample_conferences):
    result = search.rank_by_query(sample_conferences, "neural networks and transformers")
    best = max(result, key=lambda c: c["score"])
    assert best["id"] == "b"


def test_rank_by_query_scores_within_bounds(sample_conferences):
    result = search.rank_by_query(sample_conferences, "protein folding imaging")
    assert all(0.0 <= c["score"] <= 1.0 for c in result)


def test_rank_by_query_stopword_only_query_does_not_crash(sample_conferences):
    result = search.rank_by_query(sample_conferences, "the a an of")
    assert len(result) == len(sample_conferences)
    assert all(0.0 <= c["score"] <= 1.0 for c in result)


# --- search_conferences (integration, uses the real data/conferences.json) ----

def test_search_conferences_no_filters_returns_all_with_neutral_score():
    all_confs = search.load_conferences()
    result = search.search_conferences(None, None)
    assert len(result) == len(all_confs)
    assert all(c["score"] == 1.0 for c in result)


def test_search_conferences_unknown_field_returns_empty():
    assert search.search_conferences("Astrology", None) == []


def test_search_conferences_field_filter_only_matches_field():
    result = search.search_conferences("Machine Learning", None)
    assert len(result) > 0
    assert all(c["field"] == "Machine Learning" for c in result)


def test_search_conferences_is_sorted_descending_by_score():
    result = search.search_conferences(None, "deep learning generative models")
    scores = [c["score"] for c in result]
    assert scores == sorted(scores, reverse=True)


def test_search_conferences_results_have_contract_shape():
    result = search.search_conferences(None, "battery electrochemistry")
    assert len(result) > 0
    for c in result:
        assert REQUIRED_KEYS <= c.keys()
        assert isinstance(c["score"], float)
        assert 0.0 <= c["score"] <= 1.0


def test_search_conferences_field_and_query_combined_stays_within_field():
    result = search.search_conferences("Neuroscience", "memory and cognition")
    assert len(result) > 0
    assert all(c["field"] == "Neuroscience" for c in result)


# --- load_conferences / data integrity ----------------------------------

def test_load_conferences_schema_and_uniqueness():
    conferences = search.load_conferences()
    assert len(conferences) >= 1
    ids = [c["id"] for c in conferences]
    assert len(ids) == len(set(ids)), "duplicate conference ids in data file"
    for c in conferences:
        assert REQUIRED_KEYS <= c.keys()


def test_every_data_field_is_in_the_taxonomy():
    """A conference with a `field` value not in fields.FIELDS would be
    unreachable from the UI dropdown filter, since /fields only offers
    values from that list."""
    from fields import FIELDS

    conferences = search.load_conferences()
    used_fields = {c["field"] for c in conferences}
    assert used_fields <= set(FIELDS)
