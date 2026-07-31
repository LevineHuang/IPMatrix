import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ipmatrix.pipeline.analysis import analyze_run_dry
from ipmatrix.pipeline.config import TopicConfig
from ipmatrix.pipeline.publishing import publish_run_dry
from ipmatrix.pipeline.review import review_run
from ipmatrix.pipeline.storage import PipelineStorage


class DryRunFlowTests(unittest.TestCase):
    def test_analyze_review_and_publish_dry_run(self):
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
            storage.write_stage(
                topic.id,
                run["id"],
                "candidates",
                [
                    {
                        "paper_id": "arxiv-2607-12345",
                        "title": "Memory Agents",
                        "authors": [{"name": "Alice Zhang"}],
                        "abstract": "About memory agents.",
                        "source_url": "https://arxiv.org/abs/2607.12345",
                        "pdf_url": "https://arxiv.org/pdf/2607.12345",
                        "published_date": "2026-07-29",
                    }
                ],
            )
            storage.write_stage(
                topic.id,
                run["id"],
                "selection",
                {
                    "topic_id": topic.id,
                    "run_id": run["id"],
                    "selected_paper_ids": ["arxiv-2607-12345"],
                    "excluded_paper_ids": [],
                },
            )

            analysis = analyze_run_dry(root, storage, topic, run["id"])
            reviewed = review_run(storage, topic.id, run["id"])
            publish = publish_run_dry(root, storage, topic.id, run["id"])

            paper_path = root / "drafts" / topic.id / run["id"] / "papers" / "arxiv-2607-12345.md"
            overview_path = root / "drafts" / topic.id / run["id"] / "overview.md"
            self.assertTrue(paper_path.exists())
            self.assertTrue(overview_path.exists())
            self.assertIn("dry-run", paper_path.read_text(encoding="utf-8"))
            self.assertEqual(analysis["status"], "analyzed")
            self.assertEqual(reviewed["status"], "reviewed")
            self.assertEqual(publish["status"], "sent_to_wechat")
            self.assertTrue(publish["dry_run"])

            publish_path = root / "outputs" / "wechat" / topic.id / run["id"] / "publish-results.json"
            self.assertEqual(json.loads(publish_path.read_text(encoding="utf-8"))["dry_run"], True)


if __name__ == "__main__":
    unittest.main()
