from datetime import date
from pathlib import Path
from typing import Optional

from ipmatrix.pipeline.config import load_topic_config
from ipmatrix.pipeline.discovery import ArxivClient, discover_candidates
from ipmatrix.pipeline.storage import PipelineStorage


def scan_topic(
    project_root: Path,
    topic_id: str,
    today: Optional[date] = None,
    from_file: Optional[Path] = None,
    arxiv_client: Optional[ArxivClient] = None,
) -> dict:
    topic = load_topic_config(project_root, topic_id)
    if "arxiv" not in topic.sources:
        raise ValueError(f"Topic has no supported source for scan: {topic_id}")

    storage = PipelineStorage(project_root)
    run_date = today or date.today()
    run = storage.create_run(topic, today=run_date)
    window_start = date.fromisoformat(run["window_start"])
    window_end = date.fromisoformat(run["window_end"])

    client = arxiv_client or ArxivClient()
    atom_text = _load_atom(topic, client, from_file, window_start, window_end)
    raw_snapshot = _write_source_snapshot(storage, topic.id, run["id"], "arxiv", atom_text)
    candidates = discover_candidates(
        topic,
        atom_text,
        today=run_date,
        window_start=window_start,
        window_end=window_end,
        limit=topic.max_candidates,
    )

    for candidate in candidates:
        storage.record_paper(candidate)

    storage.write_stage(topic.id, run["id"], "candidates", candidates)
    scan_record = {
        "topic_id": topic.id,
        "run_id": run["id"],
        "window_start": run["window_start"],
        "window_end": run["window_end"],
        "max_candidates": topic.max_candidates,
        "candidate_count": len(candidates),
        "sources": [
            {
                "source": "arxiv",
                "query_url": client.build_query_url(
                    topic,
                    max_results=topic.max_candidates,
                    window_start=window_start,
                    window_end=window_end,
                ),
                "from_file": str(from_file) if from_file else "",
                "raw_snapshot": raw_snapshot,
                "candidate_count": len(candidates),
            }
        ],
    }
    storage.write_stage(topic.id, run["id"], "scan", scan_record)
    storage.update_run_status(topic.id, run["id"], "candidates_ready")
    return {
        "topic_id": topic.id,
        "run_id": run["id"],
        "window_start": run["window_start"],
        "window_end": run["window_end"],
        "candidates": len(candidates),
        "sources": ["arxiv"],
    }


def _load_atom(topic, client: ArxivClient, from_file: Optional[Path], window_start: date, window_end: date) -> str:
    if from_file:
        return Path(from_file).read_text(encoding="utf-8")
    return client.fetch(
        topic,
        max_results=topic.max_candidates,
        window_start=window_start,
        window_end=window_end,
    )


def _write_source_snapshot(storage: PipelineStorage, topic_id: str, run_id: str, source: str, text: str) -> str:
    relative = Path("sources") / f"{source}.atom.xml"
    path = storage.run_dir(topic_id, run_id) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(relative)
