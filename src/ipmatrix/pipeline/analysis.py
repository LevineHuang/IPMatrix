from pathlib import Path
from typing import List

from ipmatrix.pipeline.config import TopicConfig
from ipmatrix.pipeline.storage import PipelineStorage


def analyze_run_dry(project_root: Path, storage: PipelineStorage, topic: TopicConfig, run_id: str) -> dict:
    candidates = storage.read_stage(topic.id, run_id, "candidates")
    selection = storage.read_stage(topic.id, run_id, "selection")
    selected_ids = set(selection.get("selected_paper_ids", []))
    selected = [candidate for candidate in candidates if candidate["paper_id"] in selected_ids]

    artifact_records = []
    overview_path = project_root / "drafts" / topic.id / run_id / "overview.md"
    overview = _overview_markdown(topic, run_id, selected)
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(overview, encoding="utf-8")
    artifact_records.append(
        _artifact_record(
            topic.id,
            run_id,
            "",
            "batch_overview",
            f"{topic.id}__{run_id}__overview",
            overview_path,
        )
    )

    paper_dir = project_root / "drafts" / topic.id / run_id / "papers"
    paper_dir.mkdir(parents=True, exist_ok=True)
    for paper in selected:
        path = paper_dir / f"{paper['paper_id']}.md"
        path.write_text(_paper_markdown(topic, run_id, paper), encoding="utf-8")
        artifact_records.append(
            _artifact_record(
                topic.id,
                run_id,
                paper["paper_id"],
                "paper_interpretation",
                f"{topic.id}__{run_id}__{paper['paper_id']}",
                path,
            )
        )
        storage.record_paper(paper)

    for artifact in artifact_records:
        storage.record_artifact(artifact)

    analysis = {
        "topic_id": topic.id,
        "run_id": run_id,
        "status": "analyzed",
        "dry_run": True,
        "artifact_ids": [artifact["artifact_id"] for artifact in artifact_records],
    }
    storage.write_stage(topic.id, run_id, "analysis", analysis)
    storage.update_run_status(topic.id, run_id, "analyzed")
    return analysis


def _overview_markdown(topic: TopicConfig, run_id: str, papers: List[dict]) -> str:
    paper_lines = "\n".join(f"- {paper['title']} ({paper['paper_id']})" for paper in papers)
    return f"""---
title: "{topic.name} 论文观察"
artifact_id: {topic.id}__{run_id}__overview
artifact_type: batch_overview
topic_id: {topic.id}
run_id: {run_id}
status: draft
generated_by_skill: dry-run
---

# {topic.name} 论文观察

这是 dry-run 批次综述，用于验证数据流、文件结构和状态机。

## 已选论文

{paper_lines if paper_lines else "- 暂无已选论文"}
"""


def _paper_markdown(topic: TopicConfig, run_id: str, paper: dict) -> str:
    authors = ", ".join(author.get("name", "") for author in paper.get("authors", []))
    return f"""---
title: "{paper.get('title', '')}"
artifact_id: {topic.id}__{run_id}__{paper['paper_id']}
artifact_type: paper_interpretation
topic_id: {topic.id}
run_id: {run_id}
paper_id: {paper['paper_id']}
source_url: {paper.get('source_url', '')}
pdf_url: {paper.get('pdf_url', '')}
status: draft
generated_by_skill: dry-run
---

# {paper.get('title', '')}

这是 dry-run 论文解读，用于验证数据流、文件结构和状态机。后续会替换为真实生成能力。

## 论文信息

- 作者：{authors}
- 发布时间：{paper.get('published_date', '')}
- 原文：{paper.get('source_url', '')}

## 摘要

{paper.get('abstract', '')}
"""


def _artifact_record(topic_id: str, run_id: str, paper_id: str, artifact_type: str, artifact_id: str, path: Path) -> dict:
    return {
        "artifact_id": artifact_id,
        "topic_id": topic_id,
        "run_id": run_id,
        "paper_id": paper_id,
        "artifact_type": artifact_type,
        "status": "draft",
        "path": str(path),
    }
