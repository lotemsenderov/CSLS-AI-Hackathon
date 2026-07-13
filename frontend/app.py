"""Conference Finder UI — Gradio frontend.

Calls the FastAPI backend (`backend/app.py`) over HTTP per API_CONTRACT.md.
Date filtering happens client-side (the backend contract has no date
params) over the results a field/query search already returned.

Run the backend first (`uvicorn app:app --port 8000` from backend/), then
`python app.py` here.
"""
import html
from difflib import SequenceMatcher

import gradio as gr
import requests

BASE_URL = "http://localhost:8000"
PAGE_SIZE = 10

# A rotating palette for the score bubbles / field chips — purely decorative.
PALETTE = [
    ("#6366f1", "#8b5cf6"),  # indigo -> violet
    ("#ec4899", "#f472b6"),  # pink
    ("#06b6d4", "#3b82f6"),  # cyan -> blue
    ("#f59e0b", "#f97316"),  # amber -> orange
    ("#10b981", "#22c55e"),  # emerald -> green
]


def fetch_fields():
    resp = requests.get(f"{BASE_URL}/fields", timeout=5)
    resp.raise_for_status()
    return gr.update(choices=resp.json()["fields"], value=None)


def _as_date_str(value) -> str | None:
    """gr.DateTime(type='string') returns 'YYYY-MM-DD[ HH:MM:SS]' or None."""
    if not value:
        return None
    return value[:10]


def _filter_by_date(results: list[dict], date_from, date_to) -> list[dict]:
    lo = _as_date_str(date_from)
    hi = _as_date_str(date_to)
    if not lo and not hi:
        return results
    out = []
    for r in results:
        start = r.get("start_date", "")
        if lo and start < lo:
            continue
        if hi and start > hi:
            continue
        out.append(r)
    return out


def _word_matches(query_word: str, speaker_word: str) -> bool:
    """Loose match: substring either way, or close enough to tolerate typos."""
    if query_word in speaker_word or speaker_word in query_word:
        return True
    return SequenceMatcher(None, query_word, speaker_word).ratio() >= 0.75


def _filter_by_keynote(results: list[dict], keynote_query: str) -> list[dict]:
    query_words = (keynote_query or "").strip().lower().split()
    if not query_words:
        return results
    out = []
    for r in results:
        speakers = r.get("keynote_speakers") or []
        speaker_words = " ".join(speakers).lower().split()
        if all(any(_word_matches(qw, sw) for sw in speaker_words) for qw in query_words):
            out.append(r)
    return out


def _bubble_card(result: dict, index: int) -> str:
    c1, c2 = PALETTE[index % len(PALETTE)]
    name = html.escape(result["name"])
    field = html.escape(result["field"])
    location = html.escape(result["location"])
    url = html.escape(result["url"], quote=True)
    score_pct = round(result["score"] * 100)
    delay = min(index * 0.05, 0.5)

    description_html = ""
    description = (result.get("description") or "").strip()
    if description:
        if len(description) > 220:
            description = description[:220].rsplit(" ", 1)[0] + "…"
        description_html = f'<div class="result-desc">{html.escape(description)}</div>'

    keynote_html = ""
    speakers = [s for s in (result.get("keynote_speakers") or []) if s]
    if speakers:
        speakers_text = html.escape(", ".join(speakers))
        keynote_html = f'<div class="side-line">🎤 {speakers_text}</div>'

    return f"""
    <div class="result-bubble" style="animation-delay:{delay}s">
      <div class="result-main">
        <a class="result-title" href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>
        <span class="chip-tag" style="background: linear-gradient(135deg, {c1}22, {c2}22); color:{c1};">{field}</span>
        {description_html}
      </div>
      <div class="result-side">
        <div class="side-line">📍 {location}</div>
        <div class="side-line">🗓️ {result['start_date']} – {result['end_date']}</div>
        <div class="side-line side-deadline">⏳ submit by {result['submission_deadline']}</div>
        {keynote_html}
      </div>
      <div class="score-meter" title="Relevance score">
        <div class="score-track"><div class="score-fill" style="width:{score_pct}%; background: linear-gradient(90deg, {c1}, {c2});"></div></div>
        <span class="score-label" style="color:{c1};">{score_pct}%</span>
      </div>
    </div>
    """


def _render_cards(results: list[dict]) -> str:
    if not results:
        return '<div class="empty-bubble">🔍 No matching conferences found. Try loosening a filter.</div>'
    cards = "".join(_bubble_card(r, i) for i, r in enumerate(results))
    return f'<div class="results-wrap">{cards}</div>'


def _status_text(shown: int, total: int) -> str:
    if total == 0:
        return ""
    return f'<div class="status-text">Showing {shown} of {total} matching conferences</div>'


def run_search(field: str, query: str, date_from, date_to, keynote_query: str):
    params = {}
    if field:
        params["field"] = field
    if query:
        params["query"] = query

    try:
        resp = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        error_html = f'<div class="empty-bubble">⚠️ Error contacting backend: {html.escape(str(e))}</div>'
        return [], 0, "", error_html, gr.update(visible=False)

    results = _filter_by_date(resp.json()["results"], date_from, date_to)
    results = _filter_by_keynote(results, keynote_query)
    shown = min(PAGE_SIZE, len(results))
    return (
        results,
        shown,
        _status_text(shown, len(results)),
        _render_cards(results[:shown]),
        gr.update(visible=shown < len(results)),
    )


def show_more(results: list[dict], shown: int):
    new_shown = min(shown + PAGE_SIZE, len(results))
    return (
        new_shown,
        _status_text(new_shown, len(results)),
        _render_cards(results[:new_shown]),
        gr.update(visible=new_shown < len(results)),
    )


def clear_filters():
    return None, None, None, ""


BUBBLE_CSS = """
@keyframes pop-in {
  from { opacity: 0; transform: translateY(14px) scale(0.94); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes title-glow {
  0%, 100% { filter: hue-rotate(0deg); }
  50%      { filter: hue-rotate(25deg); }
}

/* Force a consistent light palette regardless of system dark-mode so text
   never inherits a light theme-color onto our light backgrounds. */
:root, .dark {
  --body-text-color: #1f2937 !important;
  --body-text-color-subdued: #4b5563 !important;
  --background-fill-primary: #ffffff !important;
  --background-fill-secondary: #f6f5fb !important;
  --border-color-primary: #e5e0fa !important;
  --block-background-fill: #ffffff !important;
  --block-label-text-color: #4b5563 !important;
  --input-background-fill: #ffffff !important;
  --body-background-fill: transparent !important;
}

.gradio-container {
  background: radial-gradient(circle at 15% 10%, #eef2ff 0%, #f8f4ff 45%, #fdf2f8 100%) !important;
  color: #1f2937 !important;
  position: relative;
  overflow-x: hidden;
}

#app-title {
  text-align: center;
  font-size: 2.75rem;
  font-weight: 800;
  margin-bottom: 0 !important;
  background: linear-gradient(135deg, #6366f1, #ec4899, #f59e0b, #6366f1);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent !important;
  animation: title-glow 6s ease-in-out infinite;
}
#app-subtitle, #app-subtitle * { text-align: center; color: #4b5563 !important; margin-top: 0.2em !important; }

/* Filters panel */
.filters-panel {
  background: #ffffff !important;
  border-radius: 16px !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(99,102,241,.08);
  padding: 12px 16px !important;
  --layout-gap: 6px !important;
  --form-gap-width: 4px !important;
  gap: 6px !important;
}
#filters-title, #filters-title * { color: #312e81 !important; font-weight: 700 !important; font-size: 0.85rem !important; margin: 0 0 4px 0 !important; }
.filters-panel label span { color: #4b5563 !important; font-size: 0.82rem !important; }
.filters-panel .block { padding-top: 0 !important; padding-bottom: 0 !important; }

/* Field picker rendered as pill-shaped bubble chips */
.bubble-radio .wrap { display: flex !important; flex-wrap: wrap; gap: 6px; background: none !important; border: none !important; box-shadow: none !important; }
.bubble-radio label {
  border-radius: 999px !important;
  padding: 5px 14px !important;
  margin: 0 !important;
  border: 1.5px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #312e81 !important;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease, color .18s ease;
}
.bubble-radio label * { color: inherit !important; }
.bubble-radio label:hover { transform: translateY(-3px) scale(1.05); box-shadow: 0 8px 18px rgba(99,102,241,.22); }
.bubble-radio label:has(input:checked) {
  background: linear-gradient(135deg, #6366f1, #ec4899) !important;
  border-color: transparent !important;
  color: #ffffff !important;
  box-shadow: 0 8px 20px rgba(99,102,241,.35);
}
.bubble-radio input[type="radio"] { display: none !important; }

/* Rounded pill query box + date pickers */
.bubble-input textarea, .bubble-input input,
.bubble-date input {
  border-radius: 999px !important;
  padding: 8px 16px !important;
  border: 1.5px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #1f2937 !important;
  font-size: 0.88rem !important;
  transition: box-shadow .18s ease, border-color .18s ease;
}
.bubble-input textarea:focus, .bubble-input input:focus, .bubble-date input:focus {
  border-color: #a5b4fc !important;
  box-shadow: 0 0 0 3px rgba(139,92,246,.18) !important;
}

/* Round gradient search button */
#search-btn {
  border-radius: 999px !important;
  border: none !important;
  background: linear-gradient(135deg, #6366f1, #ec4899) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  padding: 8px 22px !important;
  font-size: 0.88rem !important;
  transition: transform .18s ease, box-shadow .18s ease;
  box-shadow: 0 6px 16px rgba(99,102,241,.25);
}
#search-btn:hover { transform: translateY(-2px) scale(1.03); box-shadow: 0 10px 22px rgba(99,102,241,.35); }

#clear-btn {
  border-radius: 999px !important;
  border: 1.5px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #4b5563 !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  padding: 6px 16px !important;
}
#clear-btn:hover { border-color: #c7b9f7 !important; color: #312e81 !important; }

#load-more-btn {
  border-radius: 999px !important;
  border: 2px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #6366f1 !important;
  font-weight: 700 !important;
  margin: 6px auto 0 auto !important;
  display: block !important;
}
#load-more-btn:hover { background: #f6f5fb !important; transform: translateY(-2px); }

.status-text { text-align: center; color: #6b7280 !important; font-size: 0.9rem; margin: 4px 0 2px 0; }

/* Result bubble cards */
.results-wrap { display: flex; flex-direction: column; gap: 14px; padding-top: 6px; }
.result-bubble {
  display: flex; align-items: center; gap: 18px;
  background: #ffffff; border-radius: 26px; padding: 16px 22px;
  box-shadow: 0 8px 24px rgba(99,102,241,.12);
  animation: pop-in .45s ease both;
  transition: transform .18s ease, box-shadow .18s ease;
}
.result-bubble:hover { transform: translateY(-4px); box-shadow: 0 14px 32px rgba(99,102,241,.2); }
.result-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.result-title { font-size: 1.15rem; font-weight: 700; text-decoration: none; color: #312e81; }
.result-title:hover { text-decoration: underline; }
.chip-tag { align-self: flex-start; border-radius: 999px; padding: 3px 12px; font-size: 0.8rem; font-weight: 700; }
.result-desc { font-size: 0.88rem; color: #4b5563; line-height: 1.45; }
.result-side {
  flex: 0 0 auto; text-align: right; padding-left: 18px;
  border-left: 2px solid #f1eefc; max-width: 240px;
  display: flex; flex-direction: column; gap: 4px;
}
.side-line { font-size: 0.85rem; color: #4b5563; white-space: normal; }
.side-deadline { color: #9333ea; font-weight: 600; }
.score-meter { flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; gap: 5px; width: 60px; }
.score-track { width: 100%; height: 6px; border-radius: 999px; background: #f1eefc; overflow: hidden; }
.score-fill { height: 100%; border-radius: 999px; transition: width .4s ease; }
.score-label { font-size: 0.78rem; font-weight: 700; }
.empty-bubble {
  text-align: center; padding: 30px; border-radius: 26px; background: #ffffff;
  box-shadow: 0 8px 24px rgba(99,102,241,.12); font-size: 1.05rem; color: #4b5563;
}

@media (max-width: 700px) {
  .result-bubble { flex-wrap: wrap; }
  .result-side { text-align: left; border-left: none; border-top: 2px solid #f1eefc; padding-left: 0; padding-top: 10px; width: 100%; }
}
"""

# Prevent the browser's dark-mode preference from swapping in Gradio's dark
# theme colors, which otherwise clashes with our fixed light-themed CSS.
FORCE_LIGHT_JS = """
() => {
    document.body.classList.remove('dark');
    document.documentElement.classList.remove('dark');
}
"""

with gr.Blocks(title="Conference Finder") as demo:
    gr.Markdown("# Conference Finder", elem_id="app-title")
    gr.Markdown(
        "Pick a broad scientific field and/or describe your research to "
        "find matching academic conferences.",
        elem_id="app-subtitle",
    )

    with gr.Group(elem_classes=["filters-panel"]):
        gr.Markdown("🔎 Filters", elem_id="filters-title")
        field_radio = gr.Radio(
            choices=[], value=None, label="Field", elem_classes=["bubble-radio"]
        )
        with gr.Row():
            date_from = gr.DateTime(
                label="Starting after",
                include_time=False,
                type="string",
                elem_classes=["bubble-date"],
            )
            date_to = gr.DateTime(
                label="Starting before",
                include_time=False,
                type="string",
                elem_classes=["bubble-date"],
            )
        query_box = gr.Textbox(
            label="Describe your research",
            placeholder="e.g. protein folding simulations",
            elem_classes=["bubble-input"],
        )
        keynote_box = gr.Textbox(
            label="Keynote speaker",
            placeholder="e.g. Yoshua Bengio",
            elem_classes=["bubble-input"],
        )
        with gr.Row():
            clear_btn = gr.Button("Clear filters", elem_id="clear-btn", size="sm")
            search_btn = gr.Button("✨ Search", variant="primary", elem_id="search-btn")

    status_md = gr.HTML()
    results_html = gr.HTML()
    load_more_btn = gr.Button("Show 10 more ↓", elem_id="load-more-btn", visible=False)

    results_state = gr.State([])
    shown_state = gr.State(0)

    search_outputs = [results_state, shown_state, status_md, results_html, load_more_btn]
    search_inputs = [field_radio, query_box, date_from, date_to, keynote_box]

    demo.load(fn=fetch_fields, outputs=field_radio)
    search_btn.click(fn=run_search, inputs=search_inputs, outputs=search_outputs)
    query_box.submit(fn=run_search, inputs=search_inputs, outputs=search_outputs)
    keynote_box.submit(fn=run_search, inputs=search_inputs, outputs=search_outputs)
    load_more_btn.click(
        fn=show_more,
        inputs=[results_state, shown_state],
        outputs=[shown_state, status_md, results_html, load_more_btn],
    )
    clear_btn.click(
        fn=clear_filters, outputs=[field_radio, date_from, date_to, keynote_box]
    ).then(fn=run_search, inputs=search_inputs, outputs=search_outputs)

if __name__ == "__main__":
    demo.launch(css=BUBBLE_CSS, js=FORCE_LIGHT_JS)
