import tempfile
import unittest
from pathlib import Path

from ipmatrix.pipeline.config import TopicConfig, load_topic_config


class TopicConfigTests(unittest.TestCase):
    def test_loads_topic_config_from_yaml_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
    - LLM memory
  exclude:
    - neuroscience
""".strip()
                + "\n",
                encoding="utf-8",
            )

            topic = load_topic_config(root, "agent-memory")

        self.assertIsInstance(topic, TopicConfig)
        self.assertEqual(topic.id, "agent-memory")
        self.assertEqual(topic.name, "Agent memory")
        self.assertEqual(topic.max_candidates, 21)
        self.assertEqual(topic.query_include, ["agent memory", "LLM memory"])
        self.assertEqual(topic.query_exclude, ["neuroscience"])

    def test_rejects_disabled_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            topic_dir = root / "configs" / "topics"
            topic_dir.mkdir(parents=True)
            (topic_dir / "agent-memory.yml").write_text(
                "id: agent-memory\nenabled: false\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_topic_config(root, "agent-memory")


if __name__ == "__main__":
    unittest.main()
