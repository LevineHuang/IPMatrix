import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ipmatrix.pipeline.scan import scan_topic


class FakeArxivClient:
    def __init__(self, atom_text):
        self.atom_text = atom_text
        self.calls = []

    def fetch(self, topic, max_results=None, window_start=None, window_end=None):
        self.calls.append(
            {
                "topic_id": topic.id,
                "max_results": max_results,
                "window_start": window_start,
                "window_end": window_end,
            }
        )
        return self.atom_text

    def build_query_url(self, topic, max_results=None, window_start=None, window_end=None):
        return "https://export.arxiv.org/api/query?search_query=test"


ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2607.12345v1</id>
    <updated>2026-07-30T12:00:00Z</updated>
    <published>2026-07-29T12:00:00Z</published>
    <title>Memory Agents for Long Horizon Tasks</title>
    <summary> A paper about long-term memory in LLM agents. </summary>
    <author><name>Alice Zhang</name></author>
    <link href="http://arxiv.org/abs/2607.12345v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2607.12345v1" rel="related" type="application/pdf"/>
    <category term="cs.AI"/>
  </entry>
</feed>
"""


class ScanTopicTests(unittest.TestCase):
    def test_scan_topic_fetches_arxiv_candidates_and_records_source_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_topic(root)
            client = FakeArxivClient(ATOM)

            result = scan_topic(root, "agent-memory", today=date(2026, 7, 31), arxiv_client=client)

            run_dir = root / "data" / "runs" / "agent-memory" / "2026-07-31_7d"
            candidates = json.loads((run_dir / "candidates.json").read_text(encoding="utf-8"))
            scan = json.loads((run_dir / "scan.json").read_text(encoding="utf-8"))
            run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

        self.assertEqual(result["run_id"], "2026-07-31_7d")
        self.assertEqual(result["candidates"], 1)
        self.assertEqual(run["status"], "candidates_ready")
        self.assertEqual(candidates[0]["paper_id"], "arxiv-2607-12345")
        self.assertEqual(scan["sources"][0]["source"], "arxiv")
        self.assertEqual(scan["sources"][0]["candidate_count"], 1)
        self.assertEqual(scan["sources"][0]["raw_snapshot"], "sources/arxiv.atom.xml")
        self.assertEqual(client.calls[0]["window_start"], date(2026, 7, 24))
        self.assertEqual(client.calls[0]["window_end"], date(2026, 7, 31))

    def test_scan_topic_can_use_saved_atom_file_for_repeatable_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_topic(root)
            atom_path = root / "arxiv.xml"
            atom_path.write_text(ATOM, encoding="utf-8")

            result = scan_topic(root, "agent-memory", today=date(2026, 7, 31), from_file=atom_path)

            run_dir = root / "data" / "runs" / "agent-memory" / "2026-07-31_7d"
            snapshot = run_dir / "sources" / "arxiv.atom.xml"
            snapshot_exists = snapshot.exists()

        self.assertEqual(result["candidates"], 1)
        self.assertTrue(snapshot_exists)


def _write_topic(root: Path):
    topic_dir = root / "configs" / "topics"
    topic_dir.mkdir(parents=True)
    (topic_dir / "agent-memory.yml").write_text(
        """
id: agent-memory
name: Agent memory
enabled: true

schedule:
  interval_days: 7
  lookback_days: 7
  max_candidates_multiplier: 3

sources:
  - arxiv

query:
  include:
    - agent memory
  exclude:
    - neuroscience
""".strip()
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
