import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from typing import List

from ipmatrix.pipeline.config import TopicConfig


ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivClient:
    base_url = "https://export.arxiv.org/api/query"

    def build_query_url(self, topic: TopicConfig, max_results: int = None) -> str:
        include_terms = [f'all:"{term}"' for term in topic.query_include]
        exclude_terms = [f'ANDNOT all:"{term}"' for term in topic.query_exclude]
        search_query = " OR ".join(include_terms)
        if exclude_terms:
            search_query = f"({search_query}) " + " ".join(exclude_terms)
        params = {
            "search_query": search_query,
            "start": "0",
            "max_results": str(max_results or topic.max_candidates),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def fetch(self, topic: TopicConfig, max_results: int = None) -> str:
        url = self.build_query_url(topic, max_results=max_results)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "IPMatrix/0.1.0 (local-first paper pipeline)"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")


def discover_candidates(topic: TopicConfig, atom_text: str, today: date = None, limit: int = None) -> List[dict]:
    today = today or date.today()
    max_results = limit or topic.max_candidates
    papers = parse_arxiv_atom(atom_text)
    candidates = []
    for paper in papers[:max_results]:
        reason = f"Matches topic {topic.id}: " + ", ".join(topic.query_include[:3])
        candidate = dict(paper)
        candidate.update(
            {
                "topic_id": topic.id,
                "run_date": today.isoformat(),
                "relevance_score": 0.5,
                "novelty_score": 0.5,
                "recommendation_reason": reason,
                "paper_type": "unknown",
                "duplicate_hints": [],
            }
        )
        candidates.append(candidate)
    return candidates


def parse_arxiv_atom(atom_text: str) -> List[dict]:
    root = ET.fromstring(atom_text)
    papers = []
    for entry in root.findall("atom:entry", ATOM_NS):
        raw_id = _text(entry, "atom:id")
        arxiv_id = _normalize_arxiv_id(raw_id)
        links = entry.findall("atom:link", ATOM_NS)
        source_url = _link_href(links, rel="alternate") or raw_id
        pdf_url = _link_href(links, title="pdf") or source_url.replace("/abs/", "/pdf/")
        authors = []
        for author in entry.findall("atom:author", ATOM_NS):
            authors.append(
                {
                    "name": _text(author, "atom:name"),
                    "affiliation": _text(author, "arxiv:affiliation"),
                }
            )
        categories = [
            category.attrib.get("term", "")
            for category in entry.findall("atom:category", ATOM_NS)
            if category.attrib.get("term")
        ]
        papers.append(
            {
                "paper_id": f"arxiv-{arxiv_id}",
                "source": "arxiv",
                "source_url": source_url.replace("http://", "https://"),
                "pdf_url": pdf_url.replace("http://", "https://"),
                "title": _space(_text(entry, "atom:title")),
                "authors": authors,
                "published_date": _date(_text(entry, "atom:published")),
                "updated_date": _date(_text(entry, "atom:updated")),
                "abstract": _space(_text(entry, "atom:summary")),
                "keywords": [],
                "categories": categories,
            }
        )
    return papers


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path, ATOM_NS)
    return "" if found is None or found.text is None else found.text.strip()


def _link_href(links: List[ET.Element], rel: str = None, title: str = None) -> str:
    for link in links:
        if rel and link.attrib.get("rel") != rel:
            continue
        if title and link.attrib.get("title") != title:
            continue
        return link.attrib.get("href", "")
    return ""


def _normalize_arxiv_id(raw_id: str) -> str:
    match = re.search(r"(\d{4}\.\d+)(?:v\d+)?", raw_id)
    if not match:
        return raw_id.rstrip("/").split("/")[-1]
    return match.group(1).replace(".", "-")


def _date(value: str) -> str:
    return value[:10] if value else ""


def _space(value: str) -> str:
    return " ".join(value.split())
