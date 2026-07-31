import html
import json
from pathlib import Path
from typing import List


def build_selection_html(topic_id: str, run_id: str, candidates: List[dict], output_path: Path) -> Path:
    title = topic_id.capitalize()
    candidate_cards = "\n".join(_candidate_card(candidate) for candidate in candidates)
    payload = json.dumps(candidates, ensure_ascii=False)
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · {html.escape(run_id)}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17212b; background: #f7f8fa; }}
    header {{ position: sticky; top: 0; padding: 16px 24px; background: #ffffff; border-bottom: 1px solid #dde2e8; z-index: 2; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0; font-size: 22px; }}
    .actions {{ margin-top: 12px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
    button {{ border: 1px solid #1f6feb; background: #1f6feb; color: #fff; border-radius: 6px; padding: 9px 14px; cursor: pointer; }}
    article {{ background: #fff; border: 1px solid #dde2e8; border-radius: 8px; padding: 16px; margin-bottom: 14px; }}
    h2 {{ font-size: 17px; margin: 0 0 8px; }}
    .meta {{ color: #5d6978; font-size: 13px; margin-bottom: 10px; }}
    .abstract {{ line-height: 1.55; }}
    label {{ display: flex; gap: 10px; align-items: flex-start; }}
    input {{ margin-top: 4px; }}
    textarea {{ width: 100%; min-height: 220px; margin-top: 16px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)} · {html.escape(run_id)}</h1>
    <div class="actions">
      <button type="button" onclick="saveSelection()">保存 selection.json</button>
      <span>勾选要进入分析阶段的论文。</span>
    </div>
  </header>
  <main>
    {candidate_cards}
    <textarea id="selection-output" aria-label="selection json"></textarea>
  </main>
  <script>
    const candidates = {payload};
    function saveSelection() {{
      const selected = candidates.filter((candidate) => {{
        const input = document.querySelector('[data-paper-id="' + candidate.paper_id + '"]');
        return input && input.checked;
      }});
      const selection = {{
        topic_id: "{topic_id}",
        run_id: "{run_id}",
        selected_paper_ids: selected.map((candidate) => candidate.paper_id),
        excluded_paper_ids: candidates.filter((candidate) => !selected.includes(candidate)).map((candidate) => candidate.paper_id),
        generated_by: "local-selection-page"
      }};
      const text = JSON.stringify(selection, null, 2);
      document.getElementById("selection-output").value = text;
      const blob = new Blob([text + "\\n"], {{ type: "application/json" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "selection.json";
      link.click();
      URL.revokeObjectURL(link.href);
    }}
  </script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")
    return output_path


def _candidate_card(candidate: dict) -> str:
    authors = ", ".join(author.get("name", "") for author in candidate.get("authors", []))
    return f"""<article>
  <label>
    <input type="checkbox" data-paper-id="{html.escape(candidate["paper_id"])}" checked>
    <div>
      <h2>{html.escape(candidate.get("title", ""))}</h2>
      <div class="meta">{html.escape(candidate.get("published_date", ""))} · {html.escape(authors)}</div>
      <div class="meta"><a href="{html.escape(candidate.get("source_url", ""))}" target="_blank" rel="noreferrer">{html.escape(candidate.get("paper_id", ""))}</a></div>
      <p class="abstract">{html.escape(candidate.get("abstract", ""))}</p>
      <p>{html.escape(candidate.get("recommendation_reason", ""))}</p>
    </div>
  </label>
</article>"""
