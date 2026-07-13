"""Conference Finder UI — Gradio frontend.

Calls the FastAPI backend (`backend/app.py`) over HTTP per API_CONTRACT.md.
Run the backend first (`uvicorn app:app --port 8000` from backend/), then
`python app.py` here.
"""
import gradio as gr
import requests

BASE_URL = "http://localhost:8000"


def fetch_fields() -> gr.update:
    resp = requests.get(f"{BASE_URL}/fields", timeout=5)
    resp.raise_for_status()
    choices = ["(Any field)"] + resp.json()["fields"]
    return gr.update(choices=choices, value="(Any field)")


def search(field: str, query: str) -> str:
    params = {}
    if field and field != "(Any field)":
        params["field"] = field
    if query:
        params["query"] = query

    try:
        resp = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"**Error contacting backend:** {e}"

    results = resp.json()["results"]
    if not results:
        return "No matching conferences found."

    lines = []
    for r in results:
        lines.append(
            f"### [{r['name']}]({r['url']})  \n"
            f"**Field:** {r['field']} &nbsp;|&nbsp; "
            f"**Location:** {r['location']} &nbsp;|&nbsp; "
            f"**Score:** {r['score']:.2f}  \n"
            f"**Dates:** {r['start_date']} – {r['end_date']} &nbsp;|&nbsp; "
            f"**Submission deadline:** {r['submission_deadline']}"
        )
    return "\n\n---\n\n".join(lines)


with gr.Blocks(title="Conference Finder") as demo:
    gr.Markdown("# Conference Finder")
    gr.Markdown(
        "Pick a broad scientific field and/or describe your research to "
        "find matching academic conferences."
    )

    with gr.Row():
        field_dropdown = gr.Dropdown(choices=["(Any field)"], label="Field", value="(Any field)")
        query_box = gr.Textbox(
            label="Describe your research", placeholder="e.g. protein folding simulations"
        )

    search_btn = gr.Button("Search", variant="primary")
    results_md = gr.Markdown()

    demo.load(fn=fetch_fields, outputs=field_dropdown)
    search_btn.click(fn=search, inputs=[field_dropdown, query_box], outputs=results_md)
    query_box.submit(fn=search, inputs=[field_dropdown, query_box], outputs=results_md)

if __name__ == "__main__":
    demo.launch()
