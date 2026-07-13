"""Scores backend/search.py's ranking quality against qa/evaluation/gold_queries.py.

Runs each gold query through the *unfiltered* search (no field param) so the
TF-IDF ranker has to do the work of surfacing the right conferences out of
the full 205-conference pool on lexical signal alone. See gold_queries.py for
why rare-field and ML-subfield queries are scored differently.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
for extra_dir in (ROOT / "backend", Path(__file__).parent):
    p = str(extra_dir)
    if p not in sys.path:
        sys.path.insert(0, p)

import search  # noqa: E402

from gold_queries import ML_SUBFIELD_QUERIES, RARE_FIELD_QUERIES  # noqa: E402

TOP_K = 5


def _keyword_hit(keywords: list[str], conference: dict) -> bool:
    haystack = conference.get("topics", "").lower()
    return any(kw.lower() in haystack for kw in keywords)


def _score_query(item: dict) -> dict:
    results = search.search_conferences(None, item["query"])
    top_k = results[:TOP_K]

    field_hits = [r for r in top_k if r["field"] == item["expected_field"]]
    rank_of_first_hit = next(
        (i + 1 for i, r in enumerate(results) if r["field"] == item["expected_field"]),
        None,
    )
    top_scores = [r["score"] for r in top_k]
    rest_scores = [r["score"] for r in results[TOP_K:]]

    return {
        "query": item["query"],
        "expected_field": item["expected_field"],
        "top1_field_correct": top_k[0]["field"] == item["expected_field"] if top_k else False,
        "precision_at_k": len(field_hits) / TOP_K,
        "reciprocal_rank": (1.0 / rank_of_first_hit) if rank_of_first_hit else 0.0,
        "keyword_hit_top1": _keyword_hit(item["expected_keywords"], top_k[0]) if top_k else False,
        "top1_name": top_k[0]["name"] if top_k else None,
        "top1_score": top_k[0]["score"] if top_k else 0.0,
        "discrimination": (top_scores[0] - (sum(rest_scores) / len(rest_scores)))
        if top_k and rest_scores
        else 0.0,
        "all_scores": [r["score"] for r in results],
    }


def run() -> dict:
    rare = [_score_query(q) for q in RARE_FIELD_QUERIES]
    ml = [_score_query(q) for q in ML_SUBFIELD_QUERIES]

    rare_precision_at_k = sum(r["precision_at_k"] for r in rare) / len(rare)
    rare_mrr = sum(r["reciprocal_rank"] for r in rare) / len(rare)
    ml_keyword_hit_rate = sum(r["keyword_hit_top1"] for r in ml) / len(ml)
    mean_discrimination = sum(r["discrimination"] for r in rare + ml) / len(rare + ml)

    # Headline score: equal weight on "can it find the needle" (rare fields)
    # and "does it understand ML subfields" (keyword hit rate).
    headline = (rare_precision_at_k + rare_mrr + ml_keyword_hit_rate) / 3

    return {
        "headline_score": headline,
        "rare_field_precision_at_5": rare_precision_at_k,
        "rare_field_mrr": rare_mrr,
        "ml_keyword_hit_rate": ml_keyword_hit_rate,
        "mean_discrimination": mean_discrimination,
        "rare_field_results": rare,
        "ml_subfield_results": ml,
        "all_score_samples": [s for r in rare + ml for s in r["all_scores"]],
    }


if __name__ == "__main__":
    import json

    result = run()
    print(json.dumps({k: v for k, v in result.items() if k not in
                       ("rare_field_results", "ml_subfield_results", "all_score_samples")}, indent=2))