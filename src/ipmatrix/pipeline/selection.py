import html
import json
from pathlib import Path
from typing import List


def build_selection_html(topic_id: str, run_id: str, candidates: List[dict], output_path: Path) -> Path:
    title = topic_id.capitalize()
    candidate_cards = "\n".join(_candidate_card(candidate) for candidate in candidates)
    payload = json.dumps(candidates, ensure_ascii=False)
    total = len(candidates)
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · {html.escape(run_id)}</title>
  <style>
    :root {{ color-scheme: light; --line: #d9e0e7; --ink: #17212b; --muted: #637083; --accent: #1f6feb; --panel: #ffffff; --bg: #f5f7fa; --tag: #eef2f7; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
    header {{ position: sticky; top: 0; padding: 16px 24px; background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line); z-index: 2; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 20px 24px 40px; }}
    h1 {{ margin: 0; font-size: 22px; }}
    h2 {{ font-size: 17px; line-height: 1.35; margin: 0; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    button {{ border: 1px solid var(--accent); background: var(--accent); color: #fff; border-radius: 6px; padding: 8px 12px; cursor: pointer; }}
    button.secondary {{ background: #fff; color: var(--accent); }}
    .toolbar {{ display: grid; grid-template-columns: minmax(240px, 1fr) auto; gap: 12px; align-items: end; margin-top: 14px; }}
    .filters {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: end; }}
    .field {{ display: grid; gap: 5px; font-size: 13px; color: var(--muted); }}
    .field input[type="search"] {{ min-width: 260px; border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; font: inherit; color: var(--ink); background: #fff; }}
    .check-filter {{ display: flex; gap: 7px; align-items: center; padding: 8px 0; color: var(--ink); }}
    .summary {{ color: var(--muted); font-size: 14px; }}
    .summary strong {{ color: var(--ink); }}
    .actions {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }}
    .layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 18px; align-items: start; }}
    .paper-list {{ display: grid; gap: 12px; }}
    article {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    article.hidden {{ display: none; }}
    .paper-head {{ display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 12px; align-items: start; }}
    .select-box {{ width: 20px; height: 20px; margin-top: 2px; accent-color: var(--accent); }}
    .meta {{ color: var(--muted); font-size: 13px; line-height: 1.45; margin-top: 6px; }}
    .badges {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }}
    .badge {{ display: inline-flex; align-items: center; gap: 4px; border-radius: 999px; background: var(--tag); padding: 3px 8px; font-size: 12px; color: #405064; }}
    .reason {{ margin: 10px 0 0; color: #354255; line-height: 1.5; }}
    .abstract {{ margin: 10px 0 0; line-height: 1.58; color: #263241; }}
    .abstract.collapsed {{ display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
    .links {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; font-size: 13px; }}
    .inline-action {{ border: 0; background: transparent; color: var(--accent); padding: 0; font: inherit; cursor: pointer; }}
    aside {{ position: sticky; top: 116px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    aside h2 {{ font-size: 15px; margin-bottom: 8px; }}
    textarea {{ width: 100%; min-height: 260px; border: 1px solid var(--line); border-radius: 6px; padding: 10px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; line-height: 1.45; color: #243044; background: #fbfcfe; }}
    .empty {{ display: none; border: 1px dashed var(--line); border-radius: 8px; padding: 24px; text-align: center; color: var(--muted); background: #fff; }}
    .empty.visible {{ display: block; }}
    @media (max-width: 860px) {{
      header {{ position: static; }}
      .toolbar, .layout {{ grid-template-columns: 1fr; }}
      .actions {{ justify-content: flex-start; }}
      aside {{ position: static; }}
      .field input[type="search"] {{ min-width: 0; width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)} · {html.escape(run_id)}</h1>
    <div class="toolbar">
      <div class="filters">
        <label class="field">关键词过滤
          <input id="query" type="search" placeholder="标题、作者、分类、摘要" oninput="applyFilters()">
        </label>
        <label class="check-filter">
          <input id="selected-only" type="checkbox" onchange="applyFilters()"> 只看已选
        </label>
        <span class="summary">已选 <strong id="selected-count">{total}</strong> / {total}</span>
      </div>
      <div class="actions">
        <button type="button" class="secondary" onclick="setAll(true)">全选</button>
        <button type="button" class="secondary" onclick="setAll(false)">清空</button>
        <button type="button" onclick="saveSelection()">保存 selection.json</button>
      </div>
    </div>
  </header>
  <main class="layout">
    <section>
      <div class="paper-list" id="paper-list">
        {candidate_cards}
      </div>
      <div class="empty" id="empty-state">没有符合当前筛选条件的论文。</div>
    </section>
    <aside>
      <h2>下一步分析对象</h2>
      <p class="meta">勾选论文后，这里会实时生成可保存的 `selection.json`。</p>
      <textarea id="selection-output" aria-label="selection json" readonly></textarea>
    </aside>
  </main>
  <script>
    const candidates = {payload};
    const paperCards = Array.from(document.querySelectorAll("[data-paper-card]"));

    function getCheckedIds() {{
      return paperCards
        .filter((card) => card.querySelector("[data-paper-id]").checked)
        .map((card) => card.dataset.paperId);
    }}

    function renderSelection() {{
      const selectedIds = getCheckedIds();
      const selected = new Set(selectedIds);
      const selection = {{
        topic_id: "{topic_id}",
        run_id: "{run_id}",
        selected_paper_ids: selectedIds,
        excluded_paper_ids: candidates
          .filter((candidate) => !selected.has(candidate.paper_id))
          .map((candidate) => candidate.paper_id),
        generated_by: "local-selection-page"
      }};
      document.getElementById("selected-count").textContent = selectedIds.length;
      document.getElementById("selection-output").value = JSON.stringify(selection, null, 2);
      return selection;
    }}

    function applyFilters() {{
      const query = document.getElementById("query").value.trim().toLowerCase();
      const selectedOnly = document.getElementById("selected-only").checked;
      let visible = 0;
      paperCards.forEach((card) => {{
        const checked = card.querySelector("[data-paper-id]").checked;
        const matchesQuery = !query || card.dataset.search.includes(query);
        const matchesSelected = !selectedOnly || checked;
        const show = matchesQuery && matchesSelected;
        card.classList.toggle("hidden", !show);
        if (show) visible += 1;
      }});
      document.getElementById("empty-state").classList.toggle("visible", visible === 0);
      renderSelection();
    }}

    function setAll(checked) {{
      paperCards.forEach((card) => {{
        card.querySelector("[data-paper-id]").checked = checked;
      }});
      applyFilters();
    }}

    function toggleAbstract(button) {{
      const abstract = button.closest("article").querySelector(".abstract");
      const collapsed = abstract.classList.toggle("collapsed");
      button.textContent = collapsed ? "展开摘要" : "收起摘要";
    }}

    function saveSelection() {{
      const text = JSON.stringify(renderSelection(), null, 2);
      const blob = new Blob([text + "\\n"], {{ type: "application/json" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "selection.json";
      link.click();
      URL.revokeObjectURL(link.href);
    }}

    applyFilters();
  </script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")
    return output_path


def _candidate_card(candidate: dict) -> str:
    authors = ", ".join(author.get("name", "") for author in candidate.get("authors", []))
    categories = candidate.get("categories", [])
    category_badges = "".join(f'<span class="badge">{html.escape(category)}</span>' for category in categories)
    relevance = _format_score(candidate.get("relevance_score"))
    novelty = _format_score(candidate.get("novelty_score"))
    search = _search_blob(candidate, authors)
    return f"""<article data-paper-card data-paper-id="{html.escape(candidate["paper_id"])}" data-search="{html.escape(search)}">
  <div class="paper-head">
    <input class="select-box" type="checkbox" data-paper-id="{html.escape(candidate["paper_id"])}" checked onchange="applyFilters()" aria-label="选择 {html.escape(candidate.get("title", ""))}">
    <div>
      <h2>{html.escape(candidate.get("title", ""))}</h2>
      <div class="meta">{html.escape(candidate.get("published_date", ""))} 发布 · {html.escape(candidate.get("updated_date", ""))} 更新 · {html.escape(authors)}</div>
      <div class="badges">
        <span class="badge">{html.escape(candidate.get("paper_id", ""))}</span>
        <span class="badge">相关 {relevance}</span>
        <span class="badge">新颖 {novelty}</span>
        {category_badges}
      </div>
      <p class="reason">{html.escape(candidate.get("recommendation_reason", ""))}</p>
      <p class="abstract collapsed">{html.escape(candidate.get("abstract", ""))}</p>
      <button type="button" class="inline-action" onclick="toggleAbstract(this)">展开摘要</button>
      <div class="links">
        <a href="{html.escape(candidate.get("source_url", ""))}" target="_blank" rel="noreferrer">arXiv</a>
        <a href="{html.escape(candidate.get("pdf_url", ""))}" target="_blank" rel="noreferrer">PDF</a>
      </div>
    </div>
  </div>
</article>"""


def _format_score(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):.2f}"


def _search_blob(candidate: dict, authors: str) -> str:
    parts = [
        candidate.get("title", ""),
        authors,
        " ".join(candidate.get("categories", [])),
        candidate.get("abstract", ""),
        candidate.get("recommendation_reason", ""),
    ]
    return " ".join(" ".join(parts).lower().split())
