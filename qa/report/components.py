"""Small HTML/CSS chart & layout building blocks for the qa dashboard.

Deliberately not a JS charting library: the dashboard is a static file
regenerated on every run, so plain divs/tables keep it self-contained and
fast, at the cost of interactivity beyond native browser tooltips (the
`title` attribute on each bar). Colors follow the validated categorical /
status palette from the dataviz skill (references/palette.md) so light and
dark mode are both first-class, not an afterthought.
"""
import html

CATEGORICAL_LIGHT = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
CATEGORICAL_DARK = ["#3987e5", "#199e70", "#c98500", "#008300", "#9085e9", "#e66767", "#d55181", "#d95926"]

STATUS_HEX = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}

# Fixed field -> categorical slot assignment, consistent across every chart.
FIELD_SLOT = {
    "Biophysics": 0,
    "Computational Biology": 1,
    "Machine Learning": 2,
    "Chemistry": 3,
    "Neuroscience": 4,
}


def _esc(s) -> str:
    return html.escape(str(s))


def field_color(field: str) -> str:
    slot = FIELD_SLOT.get(field, len(FIELD_SLOT) % len(CATEGORICAL_LIGHT))
    return f"var(--series-{slot + 1})"


def status_for(score: float, good=0.9, warning=0.7) -> str:
    if score >= good:
        return "good"
    if score >= warning:
        return "warning"
    return "critical"


def stat_tile(label: str, value: str, status: str = "neutral", sublabel: str = "") -> str:
    status_class = f" stat-tile--{status}" if status != "neutral" else ""
    sub = f'<div class="stat-tile__sub">{_esc(sublabel)}</div>' if sublabel else ""
    return f"""
    <div class="stat-tile{status_class}">
      <div class="stat-tile__label">{_esc(label)}</div>
      <div class="stat-tile__value">{_esc(value)}</div>
      {sub}
    </div>"""


def stat_row(tiles_html: list) -> str:
    return f'<div class="stat-row">{"".join(tiles_html)}</div>'


def bar_chart(rows: list, value_fmt=lambda v: f"{v:.0%}", max_value: float = None, height_class: str = "") -> str:
    """rows: list of dicts {label, value, color (css value), tooltip (optional)}"""
    if not rows:
        return '<p class="muted">No data.</p>'
    mx = max_value if max_value is not None else max((r["value"] for r in rows), default=1) or 1
    bars = []
    for r in rows:
        pct = max(0.0, min(1.0, r["value"] / mx)) * 100
        tooltip = _esc(r.get("tooltip", f"{r['label']}: {value_fmt(r['value'])}"))
        bars.append(f"""
        <div class="bar-row" title="{tooltip}">
          <div class="bar-row__label">{_esc(r['label'])}</div>
          <div class="bar-row__track">
            <div class="bar-row__fill {height_class}" style="width:{pct:.2f}%; background:{r['color']};"></div>
          </div>
          <div class="bar-row__value">{_esc(value_fmt(r['value']))}</div>
        </div>""")
    return f'<div class="bar-chart">{"".join(bars)}</div>'


def histogram(values: list, bins: int = 8, x_min: float = 0.0, x_max: float = 1.0, color: str = "var(--series-1)") -> str:
    if not values:
        return '<p class="muted">No data.</p>'
    width = (x_max - x_min) / bins
    counts = [0] * bins
    for v in values:
        idx = int((v - x_min) / width) if width else 0
        idx = min(max(idx, 0), bins - 1)
        counts[idx] += 1
    rows = [
        {
            "label": f"{x_min + i * width:.2f}–{x_min + (i + 1) * width:.2f}",
            "value": c,
            "color": color,
            "tooltip": f"score {x_min + i * width:.2f}–{x_min + (i + 1) * width:.2f}: {c} conference(s)",
        }
        for i, c in enumerate(counts)
    ]
    return bar_chart(rows, value_fmt=lambda v: str(int(v)))


def table(headers: list, rows: list) -> str:
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def section(title: str, subtitle: str, body_html: str) -> str:
    sub = f'<p class="section__subtitle">{_esc(subtitle)}</p>' if subtitle else ""
    return f"""
    <section class="section">
      <h2>{_esc(title)}</h2>
      {sub}
      {body_html}
    </section>"""


PAGE_CSS = """
:root {
  --page:            #f9f9f7;
  --surface:          #fcfcfb;
  --text-primary:     #0b0b0b;
  --text-secondary:   #52514e;
  --muted:            #898781;
  --gridline:         #e1e0d9;
  --baseline:         #c3c2b7;
  --border:           rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #1baf7a; --series-3: #eda100; --series-4: #008300;
  --series-5: #4a3aa7; --series-6: #e34948; --series-7: #e87ba4; --series-8: #eb6834;
  --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root {
    --page:            #0d0d0d;
    --surface:          #1a1a19;
    --text-primary:     #ffffff;
    --text-secondary:   #c3c2b7;
    --muted:            #898781;
    --gridline:         #2c2c2a;
    --baseline:         #383835;
    --border:           rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #199e70; --series-3: #c98500; --series-4: #008300;
    --series-5: #9085e9; --series-6: #e66767; --series-7: #d55181; --series-8: #d95926;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px 24px 64px;
  background: var(--page); color: var(--text-primary);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
.wrap { max-width: 980px; margin: 0 auto; }
h1 { font-size: 26px; margin: 0 0 4px; }
h2 { font-size: 17px; margin: 0 0 4px; }
.subtitle { color: var(--text-secondary); margin: 0 0 28px; }
.section {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px 24px; margin-bottom: 20px;
}
.section__subtitle { color: var(--text-secondary); font-size: 13px; margin: 0 0 16px; }
.stat-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; }
.stat-tile {
  flex: 1 1 160px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px 18px;
}
.stat-tile__label { color: var(--text-secondary); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.stat-tile__value { font-size: 28px; font-weight: 600; margin-top: 4px; font-variant-numeric: tabular-nums; }
.stat-tile__sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.stat-tile--good .stat-tile__value { color: var(--good); }
.stat-tile--warning .stat-tile__value { color: #b8790a; }
.stat-tile--critical .stat-tile__value { color: var(--critical); }
@media (prefers-color-scheme: dark) {
  .stat-tile--warning .stat-tile__value { color: var(--warning); }
}
.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: grid; grid-template-columns: 220px 1fr 56px; align-items: center; gap: 10px; }
.bar-row__label { color: var(--text-secondary); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-row__track { background: var(--gridline); border-radius: 4px; height: 12px; overflow: hidden; }
.bar-row__fill { height: 100%; border-radius: 4px; min-width: 2px; }
.bar-row__value { font-size: 12px; color: var(--text-secondary); text-align: right; font-variant-numeric: tabular-nums; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--gridline); }
th { color: var(--text-secondary); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }
td { font-variant-numeric: tabular-nums; }
.muted { color: var(--muted); }
footer { color: var(--muted); font-size: 12px; margin-top: 24px; }
"""


def page(title: str, generated_at: str, body_sections: list) -> str:
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{_esc(title)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
  <div class="wrap">
    <h1>{_esc(title)}</h1>
    <p class="subtitle">Generated {_esc(generated_at)} &middot; run <code>python qa/run_all.py</code> to regenerate</p>
    {"".join(body_sections)}
    <footer>Conference Finder &mdash; qa/ test &amp; evaluation suite</footer>
  </div>
</body>
</html>"""