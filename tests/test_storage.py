import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ipmatrix.pipeline.config import TopicConfig
from ipmatrix.pipeline.storage import PipelineStorage


class PipelineStorageTests(unittest.TestCase):
    def test_creates_run_directory_json_record_and_sqlite_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            storage = PipelineStorage(root)
            topic = TopicConfig(
                id="agent-memory",
                name="Agent memory",
                enabled=True,
                interval_days=7,
                lookback_days=7,
                max_candidates_multiplier=3,
                sources=["arxiv"],
                query_include=["agent memory"],
                query_exclude=[],
            )

            run = storage.create_run(topic, today=date(2026, 7, 31))

            run_path = root / "data" / "runs" / "agent-memory" / "2026-07-31_7d"
            self.assertEqual(run["id"], "2026-07-31_7d")
            self.assertEqual(run["status"], "created")
            self.assertTrue((run_path / "run.json").exists())
            saved = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["max_candidates"], 21)

            con = sqlite3.connect(root / "data" / "db" / "pipeline.sqlite")
            rows = con.execute("select topic_id, run_id, status from runs").fetchall()
            con.close()
            self.assertEqual(rows, [("agent-memory", "2026-07-31_7d", "created")])

    def test_updates_run_status_and_writes_stage_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            storage = PipelineStorage(root)
            topic = TopicConfig(
                id="agent-memory",
                name="Agent memory",
                enabled=True,
                interval_days=7,
                lookback_days=7,
                max_candidates_multiplier=3,
                sources=["arxiv"],
                query_include=["agent memory"],
                query_exclude=[],
            )
            storage.create_run(topic, today=date(2026, 7, 31))

            storage.write_stage("agent-memory", "2026-07-31_7d", "candidates", [{"paper_id": "x"}])
            storage.update_run_status("agent-memory", "2026-07-31_7d", "candidates_ready")

            run_path = root / "data" / "runs" / "agent-memory" / "2026-07-31_7d"
            self.assertEqual(
                json.loads((run_path / "candidates.json").read_text(encoding="utf-8")),
                [{"paper_id": "x"}],
            )
            self.assertEqual(
                json.loads((run_path / "run.json").read_text(encoding="utf-8"))["status"],
                "candidates_ready",
            )


if __name__ == "__main__":
    unittest.main()
