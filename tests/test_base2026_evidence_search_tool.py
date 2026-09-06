from __future__ import annotations

import json
import re
from pathlib import Path

from test_build_base2026_cloudflare_release import builder, write_fixture, write_legacy_plugin_fixture


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_search_build_is_additive_and_indexable(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    (source / "index.html").write_text(
        (source / "index.html").read_text(encoding="utf-8").replace(
            "/wp-admin/admin-post.php", "/support.html"
        ),
        encoding="utf-8",
    )

    receipt = builder.build_release(
        source,
        output,
        homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
        homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
    )

    page_path = output / "tools" / "evidence-search" / "index.html"
    stylesheet_path = output / "static" / "base2026-evidence-search.css"
    script_path = output / "static" / "base2026-evidence-search.js"
    assert page_path.is_file()
    assert stylesheet_path.read_bytes() == builder.DEFAULT_EVIDENCE_SEARCH_STYLESHEET.read_bytes()
    assert script_path.read_bytes() == builder.DEFAULT_EVIDENCE_SEARCH_SCRIPT.read_bytes()
    assert "https://base2026.dev/tools/evidence-search/" in (
        output / builder.HUB_SITEMAP_FILENAME
    ).read_text(encoding="utf-8")
    assert receipt["verification"]["private_token_markers_remaining"] == 0


def test_evidence_search_page_has_one_h1_honest_boundaries_and_contextual_check_link() -> None:
    page = builder.DEFAULT_EVIDENCE_SEARCH_TEMPLATE.read_text(encoding="utf-8")

    assert len(re.findall(r"<h1(?:\s|>)", page)) == 1
    assert '<link rel="canonical" href="https://base2026.dev/tools/evidence-search/">' in page
    assert '<meta name="robots" content="index,follow">' in page
    assert "Search Inside Expert Videos | Base2026 Evidence Search" in page
    assert "Search inside Base2026's bounded corpus of processed" in page
    assert "Search inside expert videos for attributable evidence" in page
    assert 'action="/tools/evidence-search/"' in page
    assert "Interactive D1 results are unavailable without JavaScript" in page
    assert "keeps your query in this tool page URL" in page
    assert 'href="/workspace/"' in page
    assert "not a verdict on whether a recommendation works" in page
    assert "2026-09-01 at 16:49:09 UTC" in page
    assert "where attribution is available" in page
    assert "when it is available" in page
    assert "not a TikTok-wide search engine" in page
    assert "full-transcript database" in page
    assert "Build a source-backed brief" in page
    assert 'href="/tools/source-diversity-check/"' in page
    assert page.count('href="/tools/source-backed-brief/"') == 1
    assert 'href="/methodology"' in page
    assert 'href="/api"' in page
    assert 'href="/topics/"' in page
    assert "/knowledge/" not in page
    assert "Maharani" not in page
    assert "Primavera" not in page

    payloads = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.DOTALL
    )
    structured_types = {json.loads(payload)["@type"] for payload in payloads}
    assert structured_types == {"WebApplication", "BreadcrumbList"}
    assert "aggregateRating" not in page


def test_evidence_search_runtime_uses_public_bounded_read_only_contract() -> None:
    script = builder.DEFAULT_EVIDENCE_SEARCH_SCRIPT.read_text(encoding="utf-8")

    assert 'const INDEX_UID = "base2026_public_tiktok";' in script
    assert 'const MAX_EXCERPT_CHARS = 360;' in script
    assert 'method: "POST"' in script
    assert 'credentials: "omit"' in script
    request_contract = script.split("function publicRequest", 1)[1].split(
        "function normalizeResponse", 1
    )[0]
    assert '"body"' not in request_contract
    assert '"creator_display_name"' in request_contract
    assert "attributesToCrop" not in request_contract
    assert "boundedExcerpt(hit.title)" in script
    assert "hit.body" not in script
    assert "innerHTML" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert ".cookie" not in script
    assert "Authorization" not in script
    assert "_formatted" not in script
    assert 'window.location.hash = nextHash' in script
    assert 'new CustomEvent("base2026:analytics"' in script
    assert "Original source unavailable in this record" in script
    assert "Creator attribution unavailable in this record" in script
    assert 'topicIndexLink.href = "/topics/";' in script
    assert '"/topics/" + encodeURIComponent(topic.slug)' not in script
    assert "function sourceDiversityHandoff(rows)" in script
    assert ".slice(0, 10)" in script
    assert '"/tools/source-diversity-check/?ids=" + encodeURIComponent(ids.join(","))' in script
    assert "/knowledge/" not in script
    assert "evidence_record_selected" not in script
