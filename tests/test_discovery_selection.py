import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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
  <entry>
    <id>http://arxiv.org/abs/2607.99999v1</id>
    <updated>2026-07-20T12:00:00Z</updated>
    <published>2026-07-20T12:00:00Z</published>
    <title>Older Memory Agent Paper</title>
    <summary> Outside the configured scan window. </summary>
    <author><name>Carol Liu</name></author>
    <link href="http://arxiv.org/abs/2607.99999v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2607.99999v1" rel="related" type="application/pdf"/>
    <category term="cs.AI"/>
  </entry>
</feed>
"""


class DiscoverySelectionTests(unittest.TestCase):
    def test_builds_arxiv_query_url(self):
        topic = _topic()
        url = ArxivClient().build_query_url(
            topic,
            max_results=21,
            window_start=date(2026, 7, 24),
            window_end=date(2026, 7, 31),
        )
        query = parse_qs(urlparse(url).query)["search_query"][0]

        self.assertIn("search_query=", url)
        self.assertIn('all:"agent memory"', query)
        self.assertIn('all:"LLM memory"', query)
        self.assertIn("submittedDate:[202607240000 TO 202607312359]", query)
        self.assertIn("max_results=21", url)

    def test_discovers_candidates_from_atom_and_limits_results(self):
        topic = _topic()
        candidates = discover_candidates(
            topic,
            ATOM,
            today=date(2026, 7, 31),
            window_start=date(2026, 7, 24),
            window_end=date(2026, 7, 31),
            limit=1,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["paper_id"], "arxiv-2607-12345")
        self.assertEqual(candidates[0]["source"], "arxiv")
        self.assertEqual(candidates[0]["paper_type"], "unknown")
        self.assertIn("agent memory", candidates[0]["recommendation_reason"])

    def test_discovers_candidates_filters_by_scan_window(self):
        topic = _topic()
        candidates = discover_candidates(
            topic,
            ATOM,
            today=date(2026, 7, 31),
            window_start=date(2026, 7, 24),
            window_end=date(2026, 7, 31),
        )

        paper_ids = [candidate["paper_id"] for candidate in candidates]
        self.assertEqual(paper_ids, ["arxiv-2607-12345", "arxiv-2607-54321"])

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
                        "updated_date": "2026-07-30",
                        "source_url": "https://arxiv.org/abs/2607.12345",
                        "pdf_url": "https://arxiv.org/pdf/2607.12345",
                        "abstract": "About memory.",
                        "categories": ["cs.AI", "cs.CL"],
                        "relevance_score": 0.82,
                        "novelty_score": 0.67,
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
        self.assertIn("关键词过滤", html)
        self.assertIn("只看已选", html)
        self.assertIn("已选 <strong id=\"selected-count\">1</strong> / 1", html)
        self.assertIn("data-search=\"memory agents alice zhang cs.ai cs.cl about memory. matches agent memory\"", html)
        self.assertIn("相关 0.82", html)
        self.assertIn("新颖 0.67", html)
        self.assertIn("cs.AI", html)
        self.assertIn("PDF", html)
        self.assertIn("toggleAbstract", html)
        self.assertIn("renderSelection", html)


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
