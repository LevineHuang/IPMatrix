import tempfile
import unittest
from datetime import date
from pathlib import Path

from ipmatrix.pipeline.config import TopicConfig
from ipmatrix.pipeline.discovery import ArxivClient, discover_candidates
from ipmatrix.pipeline.selection import build_selection_html


ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2607.12345v1</id>
    <updated>2026-07-30T12:00:00Z</updated>
    <published>2026-07-29T12:00:00Z</published>
    <title>Memory Agents for Long Horizon Tasks</title>
    <summary> A paper about long-term memory in LLM agents. </summary>
    <author><name>Alice Zhang</name><arxiv:affiliation>Example Lab</arxiv:affiliation></author>
    <link href="http://arxiv.org/abs/2607.12345v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2607.12345v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.AI"/>
    <category term="cs.AI"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2607.54321v2</id>
    <updated>2026-07-28T12:00:00Z</updated>
    <published>2026-07-27T12:00:00Z</published>
    <title>Retrieval Memory for Agents</title>
    <summary> Memory and retrieval for tool using agents. </summary>
    <author><name>Bob Lee</name></author>
    <link href="http://arxiv.org/abs/2607.54321v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2607.54321v2" rel="related" type="application/pdf"/>
    <category term="cs.CL"/>
  </entry>
</feed>
"""


class DiscoverySelectionTests(unittest.TestCase):
    def test_builds_arxiv_query_url(self):
        topic = _topic()
        url = ArxivClient().build_query_url(topic, max_results=21)

        self.assertIn("search_query=", url)
        self.assertIn("agent+memory", url)
        self.assertIn("LLM+memory", url)
        self.assertIn("max_results=21", url)

    def test_discovers_candidates_from_atom_and_limits_results(self):
        topic = _topic()
        candidates = discover_candidates(topic, ATOM, today=date(2026, 7, 31), limit=1)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["paper_id"], "arxiv-2607-12345")
        self.assertEqual(candidates[0]["source"], "arxiv")
        self.assertEqual(candidates[0]["paper_type"], "unknown")
        self.assertIn("agent memory", candidates[0]["recommendation_reason"])

    def test_builds_selection_html_with_candidate_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "selection.html"
            build_selection_html(
                topic_id="agent-memory",
                run_id="2026-07-31_7d",
                candidates=[
                    {
                        "paper_id": "arxiv-2607-12345",
                        "title": "Memory Agents",
                        "authors": [{"name": "Alice Zhang"}],
                        "published_date": "2026-07-29",
                        "source_url": "https://arxiv.org/abs/2607.12345",
                        "abstract": "About memory.",
                        "recommendation_reason": "Matches agent memory",
                    }
                ],
                output_path=output,
            )

            html = output.read_text(encoding="utf-8")

        self.assertIn("Agent-memory", html)
        self.assertIn("Memory Agents", html)
        self.assertIn("保存 selection.json", html)
        self.assertIn("arxiv-2607-12345", html)


def _topic():
    return TopicConfig(
        id="agent-memory",
        name="Agent memory",
        enabled=True,
        interval_days=7,
        lookback_days=7,
        max_candidates_multiplier=3,
        sources=["arxiv"],
        query_include=["agent memory", "LLM memory"],
        query_exclude=["neuroscience"],
    )


if __name__ == "__main__":
    unittest.main()
