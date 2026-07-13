"""Search Engine matching logic. Owner: feature/matching-logic branch.

Skills 3-5 from SKILLS.md live here:
  3. Keyword/Field Filter
  4. Semantic Text Matcher (TF-IDF + cosine similarity)
  5. Result Ranker/Merger
"""
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = Path(__file__).parent.parent / "data" / "conferences.json"


def load_conferences() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


def filter_by_field(conferences: list[dict], field: str | None) -> list[dict]:
    """Skill 3: exact-match filter on `field`. Empty/None field = no filter."""
    if not field:
        return conferences
    return [c for c in conferences if c["field"] == field]


def rank_by_query(conferences: list[dict], query: str | None) -> list[dict]:
    """Skill 4: TF-IDF + cosine similarity of `query` against each
    conference's `topics` text. Attach a `score` in [0, 1] to each result.
    Empty/None query = score 1.0 for all (no ranking signal)."""
    if not query or not conferences:
        return [{**c, "score": 1.0} for c in conferences]

    corpus = [c["topics"] for c in conferences] + [query]
    tfidf = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    similarities = cosine_similarity(tfidf[-1], tfidf[:-1])[0]
    return [
        {**c, "score": float(score)}
        for c, score in zip(conferences, similarities)
    ]


def search_conferences(field: str | None, query: str | None) -> list[dict]:
    """Skill 5: combine the field filter and semantic score into one
    ranked list, sorted by `score` descending, per API_CONTRACT.md."""
    filtered = filter_by_field(load_conferences(), field)
    ranked = rank_by_query(filtered, query)
    results = [r for r in ranked if r["score"] > 0.0]
    return sorted(results, key=lambda r: r["score"], reverse=True)
