from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from alex_design_system_v2 import apply_information_architecture  # noqa: E402


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "visual_reset_topic_family", SCRIPTS / "generate-public-pages.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def direct_panel(disclosure):
    return disclosure.select_one(":scope > .b26-k-disclosure__panel--section")


def page_contract(markup: str) -> tuple[str, str, str, str]:
    soup = BeautifulSoup(markup, "html.parser")
    return (
        soup.title.get_text(strip=True),
        soup.select_one("main h1").get_text(" ", strip=True),
        str(soup.select_one('meta[name="robots"]')["content"]),
        str(soup.select_one('link[rel="canonical"]')["href"]),
    )


def test_topic_detail_gets_compact_family_structure_without_content_contract_drift() -> None:
    generator = load_generator()
    topic_id = "content-repurposing"
    topic = {
        "topic_id": topic_id,
        "topic": "content repurposing",
        "definition": "Source-backed creator statements and evidence excerpts related to content repurposing.",
        "public": True,
        "public_insight_count": 2,
        "source_count": 2,
        "creator_count": 1,
        "top_creators": [{"handle": "tjrobertson52", "count": 2}],
    }
    source = {
        "source_id": "source:alpha",
        "item_id": "video-alpha",
        "creator_handle": "tjrobertson52",
        "source_url": "https://example.com/source-alpha",
        "title": "One source record",
        "excerpt": "A reviewed public source excerpt.",
        "published_date": "2026-07-01",
        "topics": [topic_id],
    }
    insight = {
        "source_id": "source:alpha",
        "topic_id": topic_id,
        "topic": "content repurposing",
        "creator_handle": "tjrobertson52",
        "public": True,
        "claim_text": "A source transcript can support several useful assets.",
        "evidence_excerpt": "The reviewed source describes a bounded repurposing workflow.",
        "stance": "asserts",
    }
    passage = {
        "source_id": "source:alpha",
        "topics": [topic_id],
        "body": "A reviewed public passage with enough context for the topic evidence page.",
    }

    generated = generator.topic_page(topic, [source], [passage], [insight])
    transformed = apply_information_architecture(
        generated, "topics/content-repurposing.html"
    )
    soup = BeautifulSoup(transformed, "html.parser")

    assert page_contract(transformed) == page_contract(generated)
    assert "b26-k-family-topic" in (soup.main.get("class") or [])
    assert soup.select_one(".topic-page-hero__main > h1").get_text(strip=True) == (
        "content repurposing"
    )
    assert soup.select_one(".topic-page-hero__tools .topic-stat-grid")

    disclosures = soup.select("main > details.b26-k-disclosure--section")
    assert len(disclosures) == 3
    assert all(disclosure.select_one(":scope > summary h2") for disclosure in disclosures)
    assert all(direct_panel(disclosure) for disclosure in disclosures)
    assert all(not disclosure.has_attr("open") for disclosure in disclosures)

    local_nav = soup.select_one("main > .b26-k-local-nav")
    assert local_nav
    nav_labels = [node.get_text(" ", strip=True) for node in local_nav.select("a")]
    assert nav_labels == [
        "Questions this topic answers",
        "Creator Perspective",
        "Public Insight Cards",
        "Related Source Records",
        "Take this topic into a real decision",
    ]
    transformed_twice = apply_information_architecture(
        transformed, "topics/content-repurposing.html"
    )
    soup_twice = BeautifulSoup(transformed_twice, "html.parser")
    assert page_contract(transformed_twice) == page_contract(transformed)
    assert len(soup_twice.select("main > .b26-k-local-nav")) == 1
    assert len(soup_twice.select("main > details.b26-k-disclosure--section")) == 3
    assert len(soup_twice.select(".b26-k-disclosure__panel--section")) == 3


def test_topic_index_gets_directory_family_marker_and_bounded_overflow() -> None:
    generator = load_generator()
    cards = "".join(
        generator.card(
            f"Topic {index}",
            "Short source-backed topic definition.",
            f"topic-{index}.html",
            f"{index + 2} public insights · {index + 2} sources",
        )
        for index in range(14)
    )
    generated = generator.index_page(
        "Topic Evidence Pages",
        "Topic-level evidence pages with source-backed insights and creator comparison links.",
        cards,
        current="topics",
    )
    transformed = apply_information_architecture(generated, "topics/index.html")
    soup = BeautifulSoup(transformed, "html.parser")

    assert page_contract(transformed) == page_contract(generated)
    assert "b26-k-family-topic-index" in (soup.main.get("class") or [])
    assert len(soup.select("main > section > .card-grid > .intelligence-card")) == 12
    disclosure = soup.select_one("main > section > details.b26-k-disclosure--directory")
    assert disclosure
    assert "Show 2 more directory entries" in disclosure.get_text(" ", strip=True)
    assert len(disclosure.select(".b26-k-disclosure__panel > .intelligence-card")) == 2


def test_topic_family_css_uses_compact_scoped_geometry() -> None:
    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")

    required_fragments = (
        ".b26-k-family-topic-index .page-hero h1",
        ".b26-k-family-topic .topic-page-hero h1",
        "font-size: clamp(42px, 4.5vw, 60px)",
        ".b26-k-family-topic-index > .content-section > .card-grid",
        "grid-template-columns: repeat(3, minmax(0, 1fr))",
        ".b26-k-family-topic > details.b26-k-disclosure--section",
        "min-height: 72px",
        ".b26-k-family-topic .b26-k-disclosure__panel--section",
        ".b26-k-family-topic .evidence-qa-grid",
        "grid-template-columns: repeat(2, minmax(0, 1fr))",
        ".b26-k-family-topic .topic-signal-brief",
        ".b26-k-family-topic .signal-grid",
        "grid-template-columns: repeat(4, minmax(0, 1fr))",
        ".b26-k-family-topic .topic-source-proof__grid",
        ".b26-k-family-topic > section.topic-answer-capsule",
        ".b26-k-family-topic > section.topic-traffic-cta",
        "@media (max-width: 720px)",
    )
    for fragment in required_fragments:
        assert fragment in css

    details_block = re.search(
        r"\.b26-k-family-topic > details\.b26-k-disclosure--section\s*\{([^}]+)\}",
        css,
    )
    assert details_block
    assert "padding: 0" in details_block.group(1)
    assert "border-radius: 20px" in details_block.group(1)
