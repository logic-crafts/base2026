from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from alex_design_system_v2 import apply_information_architecture  # noqa: E402


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "visual_reset_compare_family", SCRIPTS / "generate-public-pages.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def page_contract(markup: str) -> tuple[str, str, str, str]:
    soup = BeautifulSoup(markup, "html.parser")
    return (
        soup.title.get_text(strip=True),
        soup.select_one("main h1").get_text(" ", strip=True),
        str(soup.select_one('meta[name="robots"]')["content"]),
        str(soup.select_one('link[rel="canonical"]')["href"]),
    )


def test_compare_detail_gets_scoped_marker_without_content_contract_drift() -> None:
    generator = load_generator()
    topic = {
        "topic_id": "content-repurposing",
        "topic": "content repurposing",
        "definition": "Attributed public creator evidence.",
        "public": True,
        "public_insight_count": 1,
        "creator_count": 1,
    }
    insight = {
        "source_id": "source:alpha",
        "topic_id": "content-repurposing",
        "creator_handle": "tjrobertson52",
        "public": True,
        "claim_text": "One public source describes a bounded repurposing workflow.",
        "evidence_excerpt": "A reviewed public excerpt.",
        "stance": "asserts",
    }
    generated = generator.compare_page(topic, [insight])
    transformed = apply_information_architecture(
        generated, "compare/content-repurposing.html"
    )
    soup = BeautifulSoup(transformed, "html.parser")

    assert page_contract(transformed) == page_contract(generated)
    assert "b26-k-family-compare" in (soup.main.get("class") or [])
    assert soup.select_one("main.b26-k-family-compare > .page-hero > h1")
    assert transformed.count("b26-k-family-compare") == 1
    assert apply_information_architecture(
        transformed, "compare/content-repurposing.html"
    ).count("b26-k-family-compare") == 1


def test_compare_index_gets_its_own_family_marker() -> None:
    generator = load_generator()
    generated = generator.index_page(
        "Creator Viewpoint Comparisons",
        "Attributed public creator viewpoints.",
        generator.card("Content repurposing", "One attributed view.", "content-repurposing.html"),
        current="topics",
        canonical_path="compare/",
    )
    transformed = apply_information_architecture(generated, "compare/index.html")
    soup = BeautifulSoup(transformed, "html.parser")

    assert page_contract(transformed) == page_contract(generated)
    assert "b26-k-family-compare-index" in (soup.main.get("class") or [])


def test_compare_and_creator_geometry_are_scoped_to_accepted_scale() -> None:
    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")

    for fragment in (
        ".b26-k-family-compare-index .page-hero h1",
        "font-size: clamp(40px, 4.4vw, 60px)",
        ".b26-k-family-compare .page-hero h1",
        "font-size: clamp(40px, 4.6vw, 64px)",
        ".b26-k-family-compare .page-hero { padding: 28px 0 38px; }",
        "font-size: clamp(36px, 10.5vw, 46px)",
        "font: 800 clamp(42px, 4.7vw, 64px)/1 var(--ayds-font-body)",
    ):
        assert fragment in css


@pytest.fixture
def compare_corpus_web_root() -> Path:
    raw = os.environ.get("BASE2026_COMPARE_CORPUS_WEB_ROOT", "").strip()
    if not raw:
        pytest.skip("set BASE2026_COMPARE_CORPUS_WEB_ROOT for generated-corpus QA")
    root = Path(raw).resolve()
    assert (root / "compare" / "index.html").is_file()
    return root


def test_generated_compare_corpus_has_exact_scoped_markers(
    compare_corpus_web_root: Path,
) -> None:
    pages = sorted(
        path
        for path in (compare_corpus_web_root / "compare").glob("*.html")
        if path.name != "index.html"
    )
    assert len(pages) == 1162
    index_soup = BeautifulSoup(
        (compare_corpus_web_root / "compare" / "index.html").read_text(encoding="utf-8"),
        "html.parser",
    )
    assert index_soup.select_one("main.b26-k-family-compare-index > .page-hero > h1")

    for path in pages:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        assert len(soup.select("main.b26-k-family-compare")) == 1, path.stem
        assert len(soup.select("main.b26-k-family-compare > .page-hero > h1")) == 1, path.stem
        assert len(soup.select('link[rel="canonical"]')) == 1, path.stem
        assert len(soup.select('meta[name="robots"]')) == 1, path.stem
