"""Search Engine matching logic. Owner: feature/matching-logic branch.

Skills 3-5 from SKILLS.md live here:
  3. Keyword/Field Filter
  4. Semantic Text Matcher (TF-IDF + cosine similarity)
  5. Result Ranker/Merger
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "conferences.json"


def load_conferences() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


def filter_by_field(conferences: list[dict], field: str | None) -> list[dict]:
    """Skill 3: exact-match filter on `field`. Empty/None field = no filter."""
    # TODO: implement
    raise NotImplementedError


def rank_by_query(conferences: list[dict], query: str | None) -> list[dict]:
    """Skill 4: TF-IDF + cosine similarity of `query` against each
    conference's `topics` text. Attach a `score` in [0, 1] to each result.
    Empty/None query = score 1.0 for all (no ranking signal)."""
    # TODO: implement using sklearn.feature_extraction.text.TfidfVectorizer
    # and sklearn.metrics.pairwise.cosine_similarity
    raise NotImplementedError


def search_conferences(field: str | None, query: str | None) -> list[dict]:
    """Skill 5: combine the field filter and semantic score into one
    ranked list, sorted by `score` descending, per API_CONTRACT.md."""
    # TODO: implement — call filter_by_field then rank_by_query, sort by score
    raise NotImplementedError
