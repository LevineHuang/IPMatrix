import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ipmatrix.pipeline.config import TopicConfig


RUN_STATES = {
    "created",
    "discovered",
    "candidates_ready",
    "selected",
    "ingested",
    "analyzed",
    "reviewed",
    "sent_to_wechat",
    "archived",
}


class PipelineStorage:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.db_path = self.data_dir / "db" / "pipeline.sqlite"
        self._ensure_db()

    def create_run(self, topic: TopicConfig, today: date = None) -> dict:
        today = today or date.today()
        run_id = f"{today.isoformat()}_{topic.lookback_days}d"
        window_start = today - timedelta(days=topic.lookback_days)
        run = {
            "id": run_id,
            "topic_id": topic.id,
            "window_start": window_start.isoformat(),
            "window_end": today.isoformat(),
            "max_candidates": topic.max_candidates,
            "status": "created",
            "created_at": _now_iso(),
        }
        self.write_stage(topic.id, run_id, "run", run)
        with self._connect() as con:
            con.execute(
                """
                insert or replace into runs
                    (topic_id, run_id, status, window_start, window_end, max_candidates, updated_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic.id,
                    run_id,
                    "created",
                    run["window_start"],
                    run["window_end"],
                    topic.max_candidates,
                    _now_iso(),
                ),
            )
        return run

    def run_dir(self, topic_id: str, run_id: str) -> Path:
        return self.data_dir / "runs" / topic_id / run_id

    def read_stage(self, topic_id: str, run_id: str, stage: str) -> Any:
        path = self.run_dir(topic_id, run_id) / f"{stage}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_stage(self, topic_id: str, run_id: str, stage: str, value: Any) -> Path:
        path = self.run_dir(topic_id, run_id) / f"{stage}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def update_run_status(self, topic_id: str, run_id: str, status: str) -> None:
        if status not in RUN_STATES:
            raise ValueError(f"Unknown run status: {status}")
        run = self.read_stage(topic_id, run_id, "run")
        run["status"] = status
        run["updated_at"] = _now_iso()
        self.write_stage(topic_id, run_id, "run", run)
        with self._connect() as con:
            con.execute(
                "update runs set status = ?, updated_at = ? where topic_id = ? and run_id = ?",
                (status, run["updated_at"], topic_id, run_id),
            )

    def record_paper(self, paper: dict) -> None:
        with self._connect() as con:
            con.execute(
                """
                insert or replace into papers
                    (paper_id, source, title, source_url, pdf_url, published_date, updated_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper["paper_id"],
                    paper.get("source", ""),
                    paper.get("title", ""),
                    paper.get("source_url", ""),
                    paper.get("pdf_url", ""),
                    paper.get("published_date", ""),
                    _now_iso(),
                ),
            )

    def record_artifact(self, artifact: dict) -> None:
        with self._connect() as con:
            con.execute(
                """
                insert or replace into artifacts
                    (artifact_id, topic_id, run_id, paper_id, artifact_type, status, path, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact["artifact_id"],
                    artifact["topic_id"],
                    artifact["run_id"],
                    artifact.get("paper_id", ""),
                    artifact["artifact_type"],
                    artifact["status"],
                    artifact["path"],
                    _now_iso(),
                ),
            )

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.executescript(
                """
                create table if not exists runs (
                    topic_id text not null,
                    run_id text not null,
                    status text not null,
                    window_start text not null,
                    window_end text not null,
                    max_candidates integer not null,
                    updated_at text not null,
                    primary key (topic_id, run_id)
                );

                create table if not exists papers (
                    paper_id text primary key,
                    source text not null,
                    title text not null,
                    source_url text not null,
                    pdf_url text not null,
                    published_date text not null,
                    updated_at text not null
                );

                create table if not exists artifacts (
                    artifact_id text primary key,
                    topic_id text not null,
                    run_id text not null,
                    paper_id text not null,
                    artifact_type text not null,
                    status text not null,
                    path text not null,
                    updated_at text not null
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
