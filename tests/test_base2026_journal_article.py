from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "templates" / "base2026-journal-cloudflare.html"
CANONICAL = "https://base2026.dev/journal/source-backed-video-search-cloudflare/"


def test_journal_article_has_one_indexable_canonical_and_techarticle_schema() -> None:
    source = ARTICLE.read_text(encoding="utf-8")

    assert source.lower().count("<h1") == 1
    assert f'<link rel="canonical" href="{CANONICAL}">' in source
    assert '<meta name="robots" content="index,follow,max-image-preview:large">' in source
    assert f'<meta property="og:url" content="{CANONICAL}">' in source
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', source, flags=re.DOTALL
    )
    assert len(blocks) == 1
    schema = json.loads(blocks[0])
    article = next(node for node in schema["@graph"] if node["@type"] == "TechArticle")
    assert article["url"] == CANONICAL
    assert article["isAccessibleForFree"] is True
    assert article["author"]["name"] == "Alex Yarosh"


def test_journal_article_uses_verified_layers_and_preserves_public_boundary() -> None:
    source = ARTICLE.read_text(encoding="utf-8")

    for expected in ("2,175", "1,574", "1,939", "524", "83", "zero-full-transcript"):
        assert expected in source
    for expected in (
        "Cloudflare D1 + FTS5",
        "Workers Static Assets",
        "Queues and Workflows",
        "Workers AI",
        "not a transcript dump",
        "not enough evidence",
        "Evidence Brief V1 and V2 are live deterministic retrieval endpoints",
    ):
        assert expected.lower() in source.lower()
    for forbidden in (
        "entire pipeline is free",
        "works entirely for free",
        "universal coverage",
        "guaranteed rankings",
        "working toward",
    ):
        assert forbidden.lower() not in source.lower()

    assert "@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}}" in source


def test_journal_article_anchor_navigation_resolves_to_existing_sections() -> None:
    source = ARTICLE.read_text(encoding="utf-8")
    targets = re.findall(r'<a href="#([a-z0-9-]+)">', source)

    assert targets
    for target in targets:
        assert source.count(f'id="{target}"') == 1


def test_journal_article_links_to_public_product_and_open_source_repository() -> None:
    source = ARTICLE.read_text(encoding="utf-8")

    assert 'href="/dataset"' in source
    assert 'href="/workspace/?q=AI%20search%20visibility"' in source
    assert 'href="https://github.com/offflinerpsy/base2026"' in source
    assert "{{STARTUP_HEADER}}" in source
    assert "{{STARTUP_FOOTER}}" in source
