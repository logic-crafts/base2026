from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "templates" / "base2026-journal-source-diversity.html"
CANONICAL = "https://base2026.dev/journal/source-diversity-check/"
QUERY_URL = "https://base2026.dev/api/evidence-brief/v2?q=AI%20citation%20tracking"
MODULE_PATH = ROOT / "scripts" / "build-base2026-cloudflare-release.py"
SPEC = importlib.util.spec_from_file_location("build_base2026_cloudflare_release", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def test_source_diversity_article_has_reviewed_metadata_and_body_boundary() -> None:
    source = ARTICLE.read_text(encoding="utf-8")

    assert source.lower().count("<h1") == 1
    assert f'<link rel="canonical" href="{CANONICAL}">' in source
    assert '<meta name="robots" content="index,follow,max-image-preview:large">' in source
    assert f'<meta property="og:url" content="{CANONICAL}">' in source
    assert '<meta property="article:published_time" content="2026-08-30">' in source
    assert source.count('<section id="') == 4

    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', source, flags=re.DOTALL
    )
    assert len(blocks) == 1
    schema = json.loads(blocks[0])
    article = next(node for node in schema["@graph"] if node["@type"] == "TechArticle")
    assert article["url"] == CANONICAL
    assert article["datePublished"] == "2026-08-30"
    assert article["dateModified"] == "2026-08-30"
    assert article["isAccessibleForFree"] is True
    assert article["author"]["name"] == "Alex Yarosh"

    for expected in (
        "AI-assisted research and writing.",
        "I’m building Base2026",
        QUERY_URL,
        "matched_records: 12",
        "selected_sources: 3",
        "distinct_creators: 2",
        "published_date_min: 2025-11-28",
        "published_date_max: 2026-07-14",
        "Six research note fields",
        "AI-generated editorial illustration, not a screenshot or real-source quote.",
    ):
        assert expected in source

    assert "Editorial illustration: generated with AI" not in source
    assert "Publication state:" not in source
    assert "../assets/keep-the-source-attached-v1.png" not in source
    assert "full transcript dump" in source
    assert "creators endorse the project" in source


def test_source_diversity_article_is_wired_into_public_release() -> None:
    source = ARTICLE.read_text(encoding="utf-8")
    cloudflare_article = (ROOT / "templates" / "base2026-journal-cloudflare.html").read_text(
        encoding="utf-8"
    )

    assert 'src="/static/assets/base2026-source-diversity.png"' in source
    assert builder.DEFAULT_JOURNAL_SOURCE_DIVERSITY_TEMPLATE == ARTICLE
    assert builder.DEFAULT_JOURNAL_SOURCE_DIVERSITY_IMAGE == (
        ROOT / "static" / "assets" / "base2026-source-diversity.png"
    )
    assert "/journal/source-diversity-check/" in builder.HUB_SITEMAP_ROUTES
    assert 'href="/journal/source-diversity-check/"' in cloudflare_article
    assert (ROOT / "static" / "assets" / "base2026-source-diversity.png").is_file()
    assert "{{STARTUP_HEADER}}" in source
    assert "{{STARTUP_FOOTER}}" in source
