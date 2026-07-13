"""Live Scraper (Skill 7 - stretch/future). Owner: feature/scraper branch.

Pulls real ML/AI conferences from the paperswithcode/ai-deadlines dataset
(a public, structured YAML CFP tracker) and merges them into
data/conferences.json, normalized to our schema.

Note: this source was last updated Sept 2024, so its conferences are
dated 2020-2025 -- real data, but not "upcoming" relative to today. Swap
SOURCE_URL for a fresher feed if/when one is available; normalize() is
the seam to adapt to a different source's raw shape.
"""
import html
import json
import re
from pathlib import Path

import requests
import yaml

SOURCE_URL = "https://raw.githubusercontent.com/paperswithcode/ai-deadlines/gh-pages/_data/conferences.yml"
DATA_PATH = Path(__file__).parent.parent / "data" / "conferences.json"
FIELD = "Machine Learning"

SUB_AREA_LABELS = {
    "ML": "machine learning",
    "CV": "computer vision",
    "NLP": "natural language processing",
    "DM": "data mining",
    "RO": "robotics",
    "SP": "signal processing",
    "KR": "knowledge representation and reasoning",
    "CG": "computational geometry",
    "AP": "applications",
    "HCI": "human-computer interaction",
}


def fetch_source() -> list[dict]:
    resp = requests.get(
        SOURCE_URL,
        headers={"User-Agent": "conference-finder-hackathon-scraper/1.0"},
        timeout=10,
    )
    resp.raise_for_status()
    return yaml.safe_load(resp.text)


def _topics_for(entry: dict) -> str:
    sub = entry.get("sub", [])
    subs = sub if isinstance(sub, list) else [sub]
    labels = [SUB_AREA_LABELS.get(s, str(s).lower()) for s in subs if s]
    note = html.unescape(re.sub("<[^>]+>", "", entry.get("note") or ""))
    return ", ".join(part for part in [entry.get("title", ""), *labels, note] if part)


def normalize(entry: dict) -> dict | None:
    """Map one raw ai-deadlines entry to our schema, or None if it's
    missing fields we require (some entries in the source are incomplete)."""
    start, end, deadline = entry.get("start"), entry.get("end"), entry.get("deadline")
    if not (start and end and deadline and entry.get("place") and entry.get("link")):
        return None
    return {
        "id": f"scraped-{entry.get('id') or entry['title'].lower()}",
        "name": f"{entry['title']} {entry.get('year', '')}".strip(),
        "field": FIELD,
        "topics": _topics_for(entry),
        "location": entry["place"],
        "start_date": str(start),
        "end_date": str(end),
        "submission_deadline": str(deadline).split(" ")[0],
        "url": entry["link"],
    }


def scrape() -> list[dict]:
    return [n for e in fetch_source() if (n := normalize(e)) is not None]


def merge_into_dataset(scraped: list[dict]) -> int:
    """Append new scraped entries into data/conferences.json, deduped by
    id against what's already there. Returns the number actually added."""
    with open(DATA_PATH, encoding="utf-8") as f:
        existing = json.load(f)
    existing_ids = {c["id"] for c in existing}
    new = [c for c in scraped if c["id"] not in existing_ids]
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing + new, f, indent=2)
        f.write("\n")
    return len(new)


if __name__ == "__main__":
    scraped = scrape()
    added = merge_into_dataset(scraped)
    print(f"Fetched {len(scraped)} usable conferences, added {added} new entries to {DATA_PATH}")
