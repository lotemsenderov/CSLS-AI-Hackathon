"""Orchestrates qa/unit (via pytest + JUnit XML) and the qa/evaluation
scorers, then renders everything into one self-contained HTML dashboard at
qa/reports/index.html.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
QA_DIR = ROOT / "qa"
REPORTS_DIR = QA_DIR / "reports"
JUNIT_PATH = REPORTS_DIR / "junit.xml"

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(QA_DIR / "evaluation"))

import components as c  # noqa: E402
import data_quality_eval  # noqa: E402
import relevance_eval  # noqa: E402


def run_unit_tests() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pytest", str(QA_DIR / "unit"), "-q", f"--junitxml={JUNIT_PATH}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    tree = ET.parse(JUNIT_PATH)
    root = tree.getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")

    by_file, failures = {}, []
    for case in suite.iter("testcase"):
        filename = case.get("classname", "").rsplit(".", 1)[-1] or "unknown"
        stats = by_file.setdefault(filename, {"passed": 0, "failed": 0})
        failure_el = case.find("failure")
        if failure_el is None:
            failure_el = case.find("error")
        if failure_el is not None:
            stats["failed"] += 1
            failures.append({
                "test": f"{filename}::{case.get('name')}",
                "message": (failure_el.get("message") or "").splitlines()[0][:200],
            })
        else:
            stats["passed"] += 1

    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    return {
        "total": total,
        "passed": total - failed,
        "failed": failed,
        "pass_rate": (total - failed) / total if total else 1.0,
        "by_file": by_file,
        "failures": failures,
    }


def render_summary(unit, relevance, quality) -> str:
    overall = (unit["pass_rate"] + relevance["headline_score"] + quality["integrity_score"]) / 3
    tiles = [
        c.stat_tile("Overall score", f"{overall:.0%}", status_for_score(overall)),
        c.stat_tile("Unit tests", f"{unit['passed']}/{unit['total']}", status_for_score(unit["pass_rate"]),
                    "passed"),
        c.stat_tile("Relevance score", f"{relevance['headline_score']:.0%}",
                    status_for_score(relevance["headline_score"])),
        c.stat_tile("Data integrity", f"{quality['integrity_score']:.0%}",
                    status_for_score(quality["integrity_score"])),
    ]
    return c.stat_row(tiles)


def status_for_score(score: float) -> str:
    return c.status_for(score)


def render_unit_section(unit: dict) -> str:
    rows = [
        {"label": name, "value": stats["passed"] / (stats["passed"] + stats["failed"]),
         "color": "var(--good)" if stats["failed"] == 0 else "var(--critical)",
         "tooltip": f"{name}: {stats['passed']} passed, {stats['failed']} failed"}
        for name, stats in sorted(unit["by_file"].items())
    ]
    body = c.bar_chart(rows, value_fmt=lambda v: f"{v:.0%}")
    if unit["failures"]:
        body += "<h3 style='font-size:13px;color:var(--critical);margin:16px 0 8px;'>Failures</h3>"
        body += c.table(["Test", "Message"], [[f["test"], f["message"]] for f in unit["failures"]])
    return c.section(
        "Module correctness (pytest)",
        "backend/fields.py, search.py, app.py, and frontend/app.py logic — run via qa/unit/",
        body,
    )


def render_relevance_section(relevance: dict) -> str:
    tiles = c.stat_row([
        c.stat_tile("Rare-field precision@5", f"{relevance['rare_field_precision_at_5']:.0%}"),
        c.stat_tile("Rare-field MRR", f"{relevance['rare_field_mrr']:.2f}"),
        c.stat_tile("ML keyword hit rate", f"{relevance['ml_keyword_hit_rate']:.0%}"),
        c.stat_tile("Score discrimination", f"{relevance['mean_discrimination']:.2f}"),
    ])

    rare_rows = [
        {
            "label": r["query"][:40],
            "value": r["precision_at_k"],
            "color": c.field_color(r["expected_field"]),
            "tooltip": f"{r['query']} -> expects {r['expected_field']}; top1: {r['top1_name']} "
                       f"(precision@5={r['precision_at_k']:.1f}, MRR={r['reciprocal_rank']:.2f})",
        }
        for r in relevance["rare_field_results"]
    ]
    ml_rows = [
        {
            "label": r["query"][:40],
            "value": 1.0 if r["keyword_hit_top1"] else 0.0,
            "color": c.field_color("Machine Learning"),
            "tooltip": f"{r['query']} -> top1: {r['top1_name']} "
                       f"(keyword hit: {r['keyword_hit_top1']})",
        }
        for r in relevance["ml_subfield_results"]
    ]

    body = tiles
    body += "<h3 style='font-size:13px;color:var(--text-secondary);margin:16px 0 8px;'>" \
            "Rare-field queries (precision@5) &mdash; strong signal, base rate is low</h3>"
    body += c.bar_chart(rare_rows)
    body += "<h3 style='font-size:13px;color:var(--text-secondary);margin:16px 0 8px;'>" \
            "ML subfield queries (top-1 keyword hit) &mdash; field-match alone is a weak signal here</h3>"
    body += c.bar_chart(ml_rows, value_fmt=lambda v: "hit" if v else "miss")
    body += "<h3 style='font-size:13px;color:var(--text-secondary);margin:16px 0 8px;'>" \
            "TF-IDF score distribution across all gold queries</h3>"
    body += c.histogram(relevance["all_score_samples"], bins=10, x_min=0.0, x_max=1.0)

    return c.section(
        "Search relevance (backend/search.py)",
        "Scored against qa/evaluation/gold_queries.py — hand-written paraphrases, not literal substrings",
        body,
    )


def render_quality_section(quality: dict) -> str:
    tiles = c.stat_row([
        c.stat_tile("Total conferences", str(quality["total_conferences"])),
        c.stat_tile("Duplicate ids", str(quality["duplicate_ids"]),
                    "good" if quality["duplicate_ids"] == 0 else "critical"),
        c.stat_tile("Invalid dates", str(quality["invalid_dates_count"]),
                    "good" if quality["invalid_dates_count"] == 0 else "critical"),
        c.stat_tile("Invalid urls", str(quality["invalid_urls_count"]),
                    "good" if quality["invalid_urls_count"] == 0 else "critical"),
        c.stat_tile("Largest field share", f"{quality['largest_field_share']:.0%}",
                    "warning" if quality["imbalance_warning"] else "good", quality["largest_field"]),
    ])

    field_rows = [
        {"label": field, "value": count, "color": c.field_color(field)}
        for field, count in sorted(quality["field_counts"].items(), key=lambda kv: -kv[1])
    ]
    body = tiles
    body += "<h3 style='font-size:13px;color:var(--text-secondary);margin:16px 0 8px;'>Conferences per field</h3>"
    body += c.bar_chart(field_rows, value_fmt=lambda v: str(int(v)))
    body += "<h3 style='font-size:13px;color:var(--text-secondary);margin:16px 0 8px;'>Topics text length (words)</h3>"
    wc = quality["topic_word_counts"]
    body += c.histogram(wc, bins=8, x_min=0, x_max=max(wc) if wc else 1, color="var(--series-1)")

    if quality["invalid_dates_ids"]:
        body += "<h3 style='font-size:13px;color:var(--critical);margin:16px 0 8px;'>Conferences with invalid/out-of-order dates</h3>"
        body += c.table(["id"], [[i] for i in quality["invalid_dates_ids"]])

    return c.section(
        "Dataset integrity (data/conferences.json)",
        "Structural checks over the current dataset, plus the field-balance shape",
        body,
    )


def build() -> Path:
    unit = run_unit_tests()
    relevance = relevance_eval.run()
    quality = data_quality_eval.run()

    sections = [
        render_summary(unit, relevance, quality),
        render_unit_section(unit),
        render_relevance_section(relevance),
        render_quality_section(quality),
    ]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_doc = c.page("Conference Finder — QA Dashboard", generated_at, sections)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "index.html"
    out_path.write_text(html_doc, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = build()
    print(f"Report written to {path}")