from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class TopicConfig:
    id: str
    name: str
    enabled: bool
    interval_days: int
    lookback_days: int
    max_candidates_multiplier: int
    sources: List[str]
    query_include: List[str]
    query_exclude: List[str]

    @property
    def max_candidates(self) -> int:
        return self.lookback_days * self.max_candidates_multiplier


def load_topic_config(project_root: Path, topic_id: str) -> TopicConfig:
    path = project_root / "configs" / "topics" / f"{topic_id}.yml"
    if not path.exists():
        raise FileNotFoundError(f"Topic config not found: {path}")

    data = parse_simple_yaml(path.read_text(encoding="utf-8"))
    if data.get("enabled", True) is not True:
        raise ValueError(f"Topic is disabled: {topic_id}")

    schedule = data.get("schedule", {})
    query = data.get("query", {})
    return TopicConfig(
        id=str(data["id"]),
        name=str(data.get("name", data["id"])),
        enabled=bool(data.get("enabled", True)),
        interval_days=int(schedule.get("interval_days", 7)),
        lookback_days=int(schedule.get("lookback_days", 7)),
        max_candidates_multiplier=int(schedule.get("max_candidates_multiplier", 3)),
        sources=list(data.get("sources", [])),
        query_include=list(query.get("include", [])),
        query_exclude=list(query.get("exclude", [])),
    )


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse the small YAML subset used by topic configs."""
    root: Dict[str, Any] = {}
    stack: List[Any] = [root]
    indents = [0]

    lines = [line.rstrip() for line in text.splitlines()]
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while indent < indents[-1]:
            stack.pop()
            indents.pop()

        parent = stack[-1]
        if line.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent: {raw}")
            parent.append(_parse_scalar(line[2:].strip()))
            continue

        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"Invalid YAML line: {raw}")
        key = key.strip()
        value = value.strip()

        if value:
            parent[key] = _parse_scalar(value)
            continue

        child = _guess_child(lines, raw, indent)
        parent[key] = child
        stack.append(child)
        indents.append(indent + 2)

    return root


def _guess_child(lines: List[str], current: str, indent: int) -> Any:
    index = lines.index(current)
    for nxt in lines[index + 1 :]:
        if not nxt.strip() or nxt.lstrip().startswith("#"):
            continue
        next_indent = len(nxt) - len(nxt.lstrip(" "))
        if next_indent <= indent:
            return {}
        return [] if nxt.strip().startswith("- ") else {}
    return {}


def _parse_scalar(value: str) -> Any:
    if value == "true":
        return True
    if value == "false":
        return False
    if value in {"null", "~"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value
