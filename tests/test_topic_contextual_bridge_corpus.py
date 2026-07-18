from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "topic_contextual_bridge_corpus", SCRIPTS / "generate-public-pages.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
    generator = load_generator()
    config = json.loads(
        (ROOT / "data" / "base2026_topic_traffic_pages.json").read_text(
            encoding="utf-8"
        )
    )
    explicitly_configured = {
        topic_id for topic_id, row in config.items() if (row or {}).get("cta")
    } | set(generator.TOPIC_MONEY_BRIDGE_COPY)
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

        secondary = bridges[0].select(".hero-actions > .ay-button-secondary")
        if secondary:
            assert topic_id in explicitly_configured, topic_id
