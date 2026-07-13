"""Conference Finder UI — Gradio frontend.

Calls the FastAPI backend (`backend/app.py`) over HTTP per API_CONTRACT.md.
Date filtering happens client-side (the backend contract has no date
params) over the results a field/query search already returned.

Run the backend first (`uvicorn app:app --port 8000` from backend/), then
`python app.py` here.
"""
import html

import gradio as gr
import requests

BASE_URL = "http://localhost:8000"
ANY_FIELD = "(Any field)"
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
    choices = [ANY_FIELD] + resp.json()["fields"]
    return gr.update(choices=choices, value=ANY_FIELD)


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


def _bubble_card(result: dict, index: int) -> str:
    c1, c2 = PALETTE[index % len(PALETTE)]
    name = html.escape(result["name"])
    field = html.escape(result["field"])
    location = html.escape(result["location"])
    url = html.escape(result["url"], quote=True)
    score_pct = round(result["score"] * 100)
    delay = min(index * 0.05, 0.5)

    return f"""
    <div class="result-bubble" style="animation-delay:{delay}s">
      <div class="score-bubble" style="background: linear-gradient(135deg, {c1}, {c2});">
        {score_pct}%
      </div>
      <div class="result-main">
        <a class="result-title" href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>
        <span class="chip-tag" style="background: linear-gradient(135deg, {c1}22, {c2}22); color:{c1};">{field}</span>
      </div>
      <div class="result-side">
        <div class="side-line">📍 {location}</div>
        <div class="side-line">🗓️ {result['start_date']} – {result['end_date']}</div>
        <div class="side-line side-deadline">⏳ submit by {result['submission_deadline']}</div>
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


def run_search(field: str, query: str, date_from, date_to):
    params = {}
    if field and field != ANY_FIELD:
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
    return ANY_FIELD, None, None


BUBBLE_CSS = """
@keyframes float {
  0%   { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(20px, -40px) scale(1.08); }
  66%  { transform: translate(-25px, 25px) scale(0.94); }
  100% { transform: translate(0, 0) scale(1); }
}
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

/* Decorative floating bubbles, purely cosmetic, non-interactive */
.bubble-bg { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.bubble-bg span {
  position: absolute; border-radius: 50%; opacity: 0.28; filter: blur(1px);
  animation: float ease-in-out infinite;
  background: linear-gradient(135deg, var(--c1), var(--c2));
}
.bubble-bg span:nth-child(1) { width: 140px; height: 140px; left: 6%;  top: 12%; --c1:#6366f1; --c2:#8b5cf6; animation-duration: 16s; }
.bubble-bg span:nth-child(2) { width: 90px;  height: 90px;  left: 82%; top: 18%; --c1:#ec4899; --c2:#f472b6; animation-duration: 13s; animation-delay: -3s; }
.bubble-bg span:nth-child(3) { width: 60px;  height: 60px;  left: 70%; top: 68%; --c1:#06b6d4; --c2:#3b82f6; animation-duration: 11s; animation-delay: -6s; }
.bubble-bg span:nth-child(4) { width: 110px; height: 110px; left: 12%; top: 72%; --c1:#f59e0b; --c2:#f97316; animation-duration: 18s; animation-delay: -2s; }
.bubble-bg span:nth-child(5) { width: 45px;  height: 45px;  left: 45%; top: 8%;  --c1:#10b981; --c2:#22c55e; animation-duration: 9s;  animation-delay: -4s; }
.bubble-bg span:nth-child(6) { width: 75px;  height: 75px;  left: 35%; top: 85%; --c1:#8b5cf6; --c2:#ec4899; animation-duration: 14s; animation-delay: -7s; }

.gradio-container > .main, .gradio-container .contain { position: relative; z-index: 1; }

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
  border-radius: 26px !important;
  border: none !important;
  box-shadow: 0 8px 24px rgba(99,102,241,.10);
  padding: 20px 22px !important;
}
#filters-title, #filters-title * { color: #312e81 !important; font-weight: 700 !important; font-size: 1.05rem !important; margin: 0 0 10px 0 !important; }
.filters-panel label span { color: #4b5563 !important; }

/* Field picker rendered as pill-shaped bubble chips */
.bubble-radio .wrap { display: flex !important; flex-wrap: wrap; gap: 10px; background: none !important; border: none !important; box-shadow: none !important; }
.bubble-radio label {
  border-radius: 999px !important;
  padding: 9px 20px !important;
  margin: 0 !important;
  border: 2px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #312e81 !important;
  cursor: pointer;
  font-weight: 600;
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
  padding: 12px 22px !important;
  border: 2px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #1f2937 !important;
  transition: box-shadow .18s ease, border-color .18s ease;
}
.bubble-input textarea:focus, .bubble-input input:focus, .bubble-date input:focus {
  border-color: #a5b4fc !important;
  box-shadow: 0 0 0 4px rgba(139,92,246,.18) !important;
}

/* Round gradient search button */
#search-btn {
  border-radius: 999px !important;
  border: none !important;
  background: linear-gradient(135deg, #6366f1, #ec4899) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  padding: 12px 34px !important;
  transition: transform .18s ease, box-shadow .18s ease;
  box-shadow: 0 10px 24px rgba(99,102,241,.3);
}
#search-btn:hover { transform: translateY(-2px) scale(1.03); box-shadow: 0 14px 30px rgba(99,102,241,.4); }

#clear-btn {
  border-radius: 999px !important;
  border: 2px solid #e5e0fa !important;
  background: #ffffff !important;
  color: #4b5563 !important;
  font-weight: 600 !important;
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
.score-bubble {
  flex: 0 0 auto; width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #ffffff; font-weight: 800; font-size: 0.95rem;
  box-shadow: 0 6px 14px rgba(0,0,0,.15);
}
.result-main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.result-title { font-size: 1.15rem; font-weight: 700; text-decoration: none; color: #312e81; }
.result-title:hover { text-decoration: underline; }
.chip-tag { align-self: flex-start; border-radius: 999px; padding: 3px 12px; font-size: 0.8rem; font-weight: 700; }
.result-side {
  flex: 0 0 auto; text-align: right; padding-left: 18px;
  border-left: 2px solid #f1eefc; min-width: 190px;
  display: flex; flex-direction: column; gap: 4px;
}
.side-line { font-size: 0.85rem; color: #4b5563; white-space: nowrap; }
.side-deadline { color: #9333ea; font-weight: 600; }
.empty-bubble {
  text-align: center; padding: 30px; border-radius: 26px; background: #ffffff;
  box-shadow: 0 8px 24px rgba(99,102,241,.12); font-size: 1.05rem; color: #4b5563;
}

@media (max-width: 700px) {
  .result-bubble { flex-wrap: wrap; }
  .result-side { text-align: left; border-left: none; border-top: 2px solid #f1eefc; padding-left: 0; padding-top: 10px; width: 100%; }
}
"""

BUBBLE_BG_HTML = (
    '<div class="bubble-bg"><span></span><span></span><span></span>'
    "<span></span><span></span><span></span></div>"
)

# Prevent the browser's dark-mode preference from swapping in Gradio's dark
# theme colors, which otherwise clashes with our fixed light-themed CSS.
FORCE_LIGHT_JS = """
() => {
    document.body.classList.remove('dark');
    document.documentElement.classList.remove('dark');
}
"""

with gr.Blocks(title="Conference Finder") as demo:
    gr.HTML(BUBBLE_BG_HTML)
    gr.Markdown("# Conference Finder", elem_id="app-title")
    gr.Markdown(
        "Pick a broad scientific field and/or describe your research to "
        "find matching academic conferences.",
        elem_id="app-subtitle",
    )

    with gr.Group(elem_classes=["filters-panel"]):
        gr.Markdown("🔎 Filters", elem_id="filters-title")
        field_radio = gr.Radio(
            choices=[ANY_FIELD], value=ANY_FIELD, label="Field", elem_classes=["bubble-radio"]
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
        with gr.Row():
            clear_btn = gr.Button("Clear filters", elem_id="clear-btn", size="sm")
            search_btn = gr.Button("✨ Search", variant="primary", elem_id="search-btn")

    status_md = gr.HTML()
    results_html = gr.HTML()
    load_more_btn = gr.Button("Show 10 more ↓", elem_id="load-more-btn", visible=False)

    results_state = gr.State([])
    shown_state = gr.State(0)

    search_outputs = [results_state, shown_state, status_md, results_html, load_more_btn]
    search_inputs = [field_radio, query_box, date_from, date_to]

    demo.load(fn=fetch_fields, outputs=field_radio)
    search_btn.click(fn=run_search, inputs=search_inputs, outputs=search_outputs)
    query_box.submit(fn=run_search, inputs=search_inputs, outputs=search_outputs)
    load_more_btn.click(
        fn=show_more,
        inputs=[results_state, shown_state],
        outputs=[shown_state, status_md, results_html, load_more_btn],
    )
    clear_btn.click(
        fn=clear_filters, outputs=[field_radio, date_from, date_to]
    ).then(fn=run_search, inputs=search_inputs, outputs=search_outputs)

if __name__ == "__main__":
    demo.launch(css=BUBBLE_CSS, js=FORCE_LIGHT_JS)
