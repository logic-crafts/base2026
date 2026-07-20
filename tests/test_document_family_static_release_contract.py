from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "web" / "static"
DOCUMENT_ROUTES = (
    "methodology.html",
    "roadmap.html",
    "story.html",
    "privacy.html",
    "source-policy.html",
    "support.html",
    "site-structure.html",
    "opt-out.html",
    "api.html",
    "apply-research.html",
    "analytics.html",
)


def test_static_document_family_uses_full_reading_field_and_hero_context() -> None:
    for route in DOCUMENT_ROUTES:
        soup = BeautifulSoup((STATIC / route).read_text(encoding="utf-8"), "html.parser")
        assert soup.select_one(".b26-k-document-layout, .ayds-document-layout") is None, route
        assert soup.select_one(".b26-k-document-rail, .ayds-document-rail") is None, route
        assert soup.select_one(
            ".page-hero .hero-actions .b26-k-document-context[role='note']"
        ), route
        if route != "roadmap.html":
            assert soup.select_one("main > article.b26-k-document-body"), route
