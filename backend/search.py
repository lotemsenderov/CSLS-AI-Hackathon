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
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def filter_by_field(conferences: list[dict], field: str | None) -> list[dict]:
    """Skill 3: exact-match filter on `field`. Empty/None field = no filter."""
    if not field:
        return list(conferences)
    return [c for c in conferences if c.get("field") == field]


def rank_by_query(conferences: list[dict], query: str | None) -> list[dict]:
    """Skill 4: TF-IDF + cosine similarity of `query` against each
    conference's `topics` text. Attach a `score` in [0, 1] to each result.
    Empty/None query = score 1.0 for all (no ranking signal)."""
    if not conferences:
        return []
    if not query:
        return [{**c, "score": 1.0} for c in conferences]

    corpus = [c.get("topics", "") for c in conferences]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus + [query])
    except ValueError:
        # Empty vocabulary (e.g. query/topics are all stop words) — no
        # lexical signal to rank on, so treat every candidate as equally
        # relevant rather than erroring out the whole search.
        return [{**c, "score": 1.0} for c in conferences]

    query_vec = tfidf_matrix[-1]
    corpus_matrix = tfidf_matrix[:-1]
    similarities = cosine_similarity(query_vec, corpus_matrix)[0]

    return [{**c, "score": float(score)} for c, score in zip(conferences, similarities)]


def search_conferences(field: str | None, query: str | None) -> list[dict]:
    """Skill 5: combine the field filter and semantic score into one
    ranked list, sorted by `score` descending, per API_CONTRACT.md."""
    conferences = load_conferences()
    filtered = filter_by_field(conferences, field)
    ranked = rank_by_query(filtered, query)
    return sorted(ranked, key=lambda c: c["score"], reverse=True)
