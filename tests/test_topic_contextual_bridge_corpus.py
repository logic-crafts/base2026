from __future__ import annotations

import os
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def topic_corpus_web_root() -> Path:
    raw = os.environ.get("BASE2026_TOPIC_CORPUS_WEB_ROOT", "").strip()
    if not raw:
        pytest.skip("set BASE2026_TOPIC_CORPUS_WEB_ROOT for generated-corpus QA")
    root = Path(raw).resolve()
    assert (root / "topics" / "index.html").is_file()
    return root


def section_heading(section) -> str:
    heading = section.select_one(":scope > h2, :scope > summary h2")
    return heading.get_text(" ", strip=True) if heading else ""


def test_frozen_corpus_has_exactly_one_contextual_bridge_per_public_topic(
    topic_corpus_web_root: Path,
) -> None:
    pages = sorted(
        path
        for path in (topic_corpus_web_root / "topics").glob("*.html")
        if path.name != "index.html"
    )

    assert len(pages) == 1162
    for path in pages:
        topic_id = path.stem
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        bridges = soup.select(
            'main > section[data-topic-contextual-bridge="true"]'
        )
        links = soup.select(
            'main a[data-research-bridge="topic_to_apply_research"]'
        )
        assert len(bridges) == 1, topic_id
        assert len(links) == 1, topic_id
        assert links[0].get("href") == (
            f"/knowledge/apply-research.html?topic={topic_id}"
        )
        assert links[0].get("data-origin-id") == topic_id

        direct_sections = soup.select("main > section, main > details")
        bridge_index = direct_sections.index(bridges[0])
        evidence_indexes = [
            index
            for index, section in enumerate(direct_sections)
            if section_heading(section)
            in {"Public Insight Cards", "Related Source Records", "Evidence Passages"}
        ]
        assert evidence_indexes and max(evidence_indexes) < bridge_index, topic_id

        assert not bridges[0].select(".hero-actions > .ay-button-secondary"), topic_id
