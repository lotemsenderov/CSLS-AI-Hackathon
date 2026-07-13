"""Entry point: runs the qa/unit pytest suite, scores search relevance and
data integrity, and writes a self-contained HTML dashboard.

    python qa/run_all.py

Opens nothing automatically — the dashboard is written to
qa/reports/index.html; open it in a browser once it's built.
"""
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "report"))

from build_report import build  # noqa: E402


def main() -> None:
    path = build()
    print(f"\nDashboard written to: {path}")
    if "--open" in sys.argv:
        webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    main()