from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-base2026-cloudflare-release.py"
SPEC = importlib.util.spec_from_file_location("build_base2026_cloudflare_release", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def write_fixture(root: Path) -> None:
    (root / "static").mkdir(parents=True)
    (root / "search").mkdir()
    (root / "index.html").write_text(
        """<!doctype html>
<link rel="canonical" href="https://aggressorbulkit.online/knowledge/">
<a class="base" href="/knowledge/topics/seo.html">Topics</a>
<a class="personal" href="/about/">About</a>
<form action="/wp-admin/admin-post.php"></form>
<script>window.BASE2026_MEILI_URL = "/knowledge-search";</script>
<a href="https://www.tiktok.com/@creator/knowledge/example">Creator</a>
""",
        encoding="utf-8",
    )
    (root / "search" / "index.html").write_text(
        '<link rel="stylesheet" href="../static/site.css"><a href="./analytics.html">Analytics</a>',
        encoding="utf-8",
    )
    (root / "search.html").write_text(
        '<title>Base2026 SEO, GEO &amp; AEO Source Library</title>'
        '<link rel="canonical" href="https://base2026.dev/" />'
        '<meta name="base2026-legacy-alias-source" content="index.html" /\n'
        '<link rel="stylesheet" href="static/site.css">'
        '<main class="app-shell" id="searchbox">Search application</main>'
        '<script>fetch("static/manifest.json"); fetch(\'./static/analytics.json\')</script>',
        encoding="utf-8",
    )
    (root / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<sitemap><loc>https://base2026.dev/sitemaps/base2026-001.xml</loc></sitemap>'
        '</sitemapindex>\n',
        encoding="utf-8",
    )
    (root / "static" / "site.css").write_text(
        'body{background:url("/wp-content/themes/alex/assets/a.png")} /* /knowledge/ */',
        encoding="utf-8",
    )
    (root / "static" / "documents.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "static" / "passages.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "static" / "insight_cards.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "static" / "topic_signal_briefs.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "static" / "manifest.json").write_text(
        json.dumps({"files": ["private.jsonl", "stale.jsonl"]}) + "\n", encoding="utf-8"
    )
    # It must remain byte-identical even though it has an unknown extension.
    (root / "static" / "avatar.bin").write_bytes(b"\x89PNG\r\n\x00\xff\x01\x02")
    # Known local artifacts are excluded from the public output.
    (root / "manifest.json").write_text(
        json.dumps({"pages": ["/Users/example/private/release/index.html"]}), encoding="utf-8"
    )
    (root / "knowledge" / "solutions" / "solutions").mkdir(parents=True)
    (root / "knowledge" / "solutions" / "solutions" / "index.html").write_text(
        "stale", encoding="utf-8"
    )


def test_transform_maps_boundaries_and_preserves_external_creator_urls() -> None:
    result = builder.transform_text(
        '<a href="https://aggressorbulkit.online/knowledge/sources/1.html">Base</a>'
        '<a href="/knowledge/topics/seo.html">Topic</a>'
        '<form action="/wp-admin/admin-post.php"></form>'
        '<a href="https://www.tiktok.com/@creator/knowledge/example">Creator</a>'
        '<script>const endpoint="/knowledge-search/multi-search";</script>'
    )

    assert "https://base2026.dev/sources/1.html" in result.text
    assert 'href="/topics/seo.html"' in result.text
    assert 'action="https://aggressorbulkit.online/wp-admin/admin-post.php"' in result.text
    assert "https://www.tiktok.com/@creator/knowledge/example" in result.text
    assert "/api/search/multi-search" in result.text
    assert builder.scan_for_broken_paths(result.text) == {
        "old_base2026_canonical_origin": 0,
        "broken_knowledge_product_path": 0,
    }
    assert result.replacements.old_base2026_origin_to_root == 1
    assert result.replacements.internal_knowledge_paths_to_root == 1
    assert result.replacements.old_search_prefix_to_api == 1
    assert result.replacements.wordpress_routes_absolutized == 1

    standalone = builder.transform_text(
        '<link rel="canonical" href="https://base2026.dev/roadmap.html">'
        '<a href="/api.html">API</a>',
        standalone_startup=True,
    )
    assert 'href="https://base2026.dev/roadmap"' in standalone.text
    assert 'href="/api"' in standalone.text
    assert standalone.replacements.html_urls_to_extensionless == 2


def test_build_excludes_private_stale_inputs_and_emits_root_contract(tmp_path: Path) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)

    receipt = builder.build_release(source, output)

    assert not (output / "manifest.json").exists()
    assert not (output / "knowledge").exists()
    assert (output / "robots.txt").read_text(encoding="utf-8") == builder.ROBOTS_PAYLOAD
    assert (output / "_headers").read_text(encoding="utf-8") == builder.HEADERS_PAYLOAD
    assert (output / builder.ASSETSIGNORE_FILENAME).read_text(encoding="utf-8").endswith(
        f"{builder.RECEIPT_FILENAME}\n"
    )

    manifest = json.loads((output / "static/manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == [
        "documents.jsonl",
        "insight_cards.jsonl",
        "passages.jsonl",
        "topic_signal_briefs.jsonl",
    ]
    assert (output / "static/avatar.bin").read_bytes() == b"\x89PNG\r\n\x00\xff\x01\x02"
    assert receipt["source"]["file_count"] == 13
    assert receipt["source"]["excluded_file_count"] == 2
    assert receipt["artifact"]["file_count"] == 13
    assert receipt["verification"]["static_manifest_files_match"] is True
    assert receipt["verification"]["binary_bytes_preserved"] is True
    assert receipt["verification"]["local_path_markers_remaining"] == 0
    assert receipt["verification"]["private_token_markers_remaining"] == 0


def test_startup_homepage_overlay_preserves_search_as_workspace(tmp_path: Path) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    homepage = tmp_path / "startup-homepage.html"
    stylesheet = tmp_path / "startup-homepage.css"
    write_fixture(source)
    (source / "index.html").write_text(
        (source / "index.html").read_text(encoding="utf-8").replace(
            '/wp-admin/admin-post.php', '/support.html'
        ),
        encoding="utf-8",
    )
    homepage.write_text(
        '<!doctype html><link rel="canonical" href="https://base2026.dev/">'
        '{{STARTUP_HEADER}}<a href="https://base2026.dev/workspace/">Search</a>{{STARTUP_FOOTER}}',
        encoding="utf-8",
    )
    stylesheet.write_text("body{color:#111820}\n", encoding="utf-8")

    receipt = builder.build_release(
        source,
        output,
        homepage_template=homepage,
        homepage_stylesheet=stylesheet,
    )

    rendered_homepage = (output / "index.html").read_text(encoding="utf-8")
    assert "b26-site-header" in rendered_homepage
    assert "b26-site-footer" in rendered_homepage
    assert builder.STARTUP_CORE_LINK in rendered_homepage
    assert "https://base2026.dev/workspace/" in rendered_homepage
    assert builder.SOCIAL_IMAGE_URL in rendered_homepage
    workspace = (output / "workspace" / "index.html").read_text(encoding="utf-8")
    assert "Search application" in workspace
    assert 'content="index.html" />' in workspace
    assert '<base href="/">' in workspace
    assert '<link rel="canonical" href="https://base2026.dev/workspace/" />' in workspace
    assert builder.SOCIAL_IMAGE_URL in workspace
    assert builder.STARTUP_CORE_LINK in workspace
    assert 'href="/static/site.css"' in workspace
    assert 'fetch("/static/manifest.json")' in workspace
    assert "fetch('/static/analytics.json')" in workspace
    assert '"static/' not in workspace
    assert "'./static/" not in workspace
    assert (output / "static" / "base2026-startup-homepage.css").read_bytes() == stylesheet.read_bytes()
    assert (output / "static" / "base2026-core.css").read_bytes() == builder.DEFAULT_CORE_STYLESHEET.read_bytes()
    assert (output / "support.html").is_file()
    assert (output / "partner.html").is_file()
    assert (output / "privacy.html").is_file()
    assert (output / "about.html").is_file()
    assert (output / "apply-research.html").is_file()
    assert (output / "ai-visibility-resources.html").is_file()
    assert (output / "static" / "base2026-forms.js").is_file()
    assert (output / "static" / "roadmap.js").read_bytes() == builder.DEFAULT_ROADMAP_SCRIPT.read_bytes()
    assert (output / "static" / "brand" / "github.svg").is_file()
    assert (output / "static" / "base2026-mark.svg").is_file()
    assert (output / builder.HUB_SITEMAP_FILENAME).is_file()
    assert builder.HUB_SITEMAP_URL in (output / "sitemap.xml").read_text(encoding="utf-8")
    assert "sitemap-dynamic.xml" in (output / "robots.txt").read_text(encoding="utf-8")
    assert "https://base2026.dev/roadmap.html" not in (output / "sitemap.xml").read_text(encoding="utf-8")
    support = (output / "support.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/support">' in support
    assert 'href="/roadmap"' in support
    assert receipt["verification"]["personal_site_origin_markers_remaining"] == 0
    assert receipt["replacements"]["html_urls_to_extensionless"] > 0
    assert receipt["verification"]["redirecting_html_canonical_markers_remaining"] == 0
    assert receipt["verification"]["redirecting_html_sitemap_markers_remaining"] == 0
    assert receipt["artifact"]["file_count"] == 29


def test_startup_shell_injects_a_missing_legacy_header() -> None:
    header = '<header class="b26-site-header">Base2026</header>'
    footer = '<footer class="b26-site-footer">Footer</footer>'
    rendered = builder._apply_startup_shell(
        '<!doctype html><html><head></head><body><main>Roadmap</main><footer class="site-footer">Old</footer></body></html>',
        header,
        footer,
    )

    assert rendered.count('class="b26-site-header"') == 1
    assert rendered.count('class="b26-site-footer"') == 1
    assert rendered.index('class="b26-site-header"') < rendered.index("<main>")


def test_startup_shell_replaces_an_existing_b26_shell() -> None:
    rendered = builder._apply_startup_shell(
        '<!doctype html><html><body><header class="b26-site-header">Old</header>'
        '<main>Workspace</main><footer class="b26-site-footer">Old footer</footer></body></html>',
        '<header class="b26-site-header">New</header>',
        '<footer class="b26-site-footer">New footer</footer>',
    )

    assert "Old footer" not in rendered
    assert ">Old<" not in rendered
    assert "New footer" in rendered
    assert ">New<" in rendered


def test_startup_shell_removes_decorative_solution_sequence_numbers() -> None:
    rendered = builder._apply_startup_shell(
        '<!doctype html><html><body><main><article class="solution-step"><span class="solution-step__number">01</span><h2>Step</h2></article><section aria-labelledby="source-footprint-bridge-local"><a href="/ai-visibility-audit/">Get a free AI Visibility Snapshot</a></section><section class="base-contact-section"><form action="mailto:offflinerpsy@gmail.com?subject=Base2026%20roadmap%20feedback"><button>Send Message</button></form></section></main></body></html>',
        '<header class="b26-site-header">Header</header>',
        '<footer class="b26-site-footer">Footer</footer>',
    )

    assert "solution-step__number" not in rendered
    assert ">01<" not in rendered
    assert "Free AI Visibility Snapshot" not in rendered
    assert "mailto:" not in rendered
    assert builder.ROADMAP_CONTACT_MARKUP in rendered


def test_independent_information_templates_are_base_only() -> None:
    for template_path in (
        builder.DEFAULT_APPLY_RESEARCH_TEMPLATE,
        builder.DEFAULT_AI_VISIBILITY_RESOURCES_TEMPLATE,
    ):
        text = template_path.read_text(encoding="utf-8")
        assert text.count("{{STARTUP_HEADER}}") == 1
        assert text.count("{{STARTUP_FOOTER}}") == 1
        assert "Alex Yarosh" not in text
        assert "Get Free Snapshot" not in text


def test_workspace_rewrite_removes_legacy_commercial_handoff() -> None:
    rendered = builder._rewrite_workspace_html(
        '<meta name="base2026-legacy-alias-source" content="index.html" /\n'
        '<p>Base2026 is an independent research product by <a href="/solutions/">Alex Yarosh</a>.</p>'
        '<section class="research-bridge" aria-labelledby="research-bridge-title">'
        '<a class="ay-button" href="/solutions/">Check My AI Visibility</a></section>'
        '<p>Do not use the public search workspace for private client data, credentials, analytics exports or confidential strategy. Route business-specific diagnosis into the Alex Yarosh workflow.</p>'
        '<a class="ay-button-secondary" href="/solutions/">AI Visibility Diagnostic Audit</a>'
    )

    assert 'content="index.html" />' in rendered
    assert "Check My AI Visibility" not in rendered
    assert "AI Visibility Diagnostic Audit" not in rendered
    assert "Alex Yarosh workflow" not in rendered
    assert "Alex Yarosh's audit" not in rendered
    assert "independent public research pilot" in rendered


def test_public_ai_docs_are_rewritten_to_the_base2026_only_contract() -> None:
    root_llms = builder._rewrite_public_api_docs(Path("root-llms.txt"), "legacy")
    llms = builder._rewrite_public_api_docs(Path("llms.txt"), "Base2026 Search workspace")
    api = builder._rewrite_public_api_docs(
        Path("api.html"),
        "<section><h2>AI usage</h2><p>For business-specific implementation, use <code>/apply-research.html</code> as the public bridge from Base2026 source intelligence to Alex Yarosh&#x27;s AI Visibility Snapshot, Diagnostic Audit, and service workflow.</p></section>",
    )

    for rendered in (root_llms, llms, api):
        assert "Alex Yarosh" not in rendered
        assert "AI Visibility Snapshot" not in rendered
        assert "Diagnostic Audit" not in rendered
    assert "Base2026" in root_llms
    assert "Search workspace" in llms
    assert "independent review question" in api

    api_index = builder._rewrite_public_api_docs(
        Path("api-index.json"),
        '{"description": "Server-side Meilisearch multi-search proxy used by the public UI. Prefer static JSONL for bulk/offline analysis; use this endpoint when live search ranking is needed.", "guide": "Human-readable bridge from Base2026 public source intelligence to Alex Yarosh\'s business-specific AI visibility audit and service workflow."}',
    )
    assert "business-specific AI visibility audit" not in api_index
    assert "cloudflare_worker_d1_fts5" in api_index


def test_legacy_styles_are_normalized_at_the_release_boundary() -> None:
    rendered = builder._rewrite_legacy_base_styles(
        Path("static/styles.css"),
        ':root{--ay-bg:#f7f4ee;--ay-paper:#fffaf0;--ay-orange:#c84f07;--ay-orange-2:#ef6b13}.photo{background:url("/wp-content/themes/alex-yarosh/assets/alex-yarosh-avatar.png") center / cover no-repeat;}',
    )
    solution = builder._rewrite_legacy_base_styles(
        Path("static/ai-recommends-solutions.css"),
        '.solution-page{--solution-orange: #ff6b18; --solution-ink: #101820; --solution-mist: #eef2f0;--solution-accent:#D9730D}.solution-step__number{color:#ff6b18}',
    )

    assert "#F7F9FC" in rendered
    assert "#315EEA" in rendered
    assert "alex-yarosh" not in rendered
    assert "#315EEA" in solution
    assert "#0B1736" in solution
    assert "solution-step__number" not in solution
    assert "#D9730D" not in solution


def test_build_is_deterministic_and_refuses_existing_or_nested_paths(tmp_path: Path) -> None:
    source = tmp_path / "source-web"
    first = tmp_path / "release-one"
    second = tmp_path / "release-two"
    write_fixture(source)

    first_receipt = builder.build_release(source, first)
    second_receipt = builder.build_release(source, second)

    assert first_receipt["hashes"] == second_receipt["hashes"]
    assert (first / builder.RECEIPT_FILENAME).read_bytes() == (
        second / builder.RECEIPT_FILENAME
    ).read_bytes()
    assert sorted(
        path.relative_to(first).as_posix()
        for path in first.rglob("*")
        if path.is_file() and path.name not in {builder.RECEIPT_FILENAME}
    ) == sorted(
        path.relative_to(second).as_posix()
        for path in second.rglob("*")
        if path.is_file() and path.name not in {builder.RECEIPT_FILENAME}
    )

    with pytest.raises(builder.ReleaseBuildError, match="existing output"):
        builder.build_release(source, first)
    with pytest.raises(builder.ReleaseBuildError, match="must not be nested"):
        builder.build_release(source, source / "nested-output")
    with pytest.raises(builder.ReleaseBuildError, match="different paths"):
        builder.validate_paths(source, source)


def test_build_fails_closed_on_local_path_leak_and_allows_explicit_redirect_doc(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source-web"
    write_fixture(source)
    (source / "leak.txt").write_text("/Users/example/private/release\n", encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError, match="local/private path markers"):
        builder.build_release(source, tmp_path / "failed-release")

    redirect_source = tmp_path / "redirect-source"
    redirect_source.mkdir()
    (redirect_source / "redirects.txt").write_text(
        builder.INTENTIONAL_REDIRECT_MARKER
        + "\nOld URL: https://aggressorbulkit.online/knowledge/ -> https://base2026.dev/\n",
        encoding="utf-8",
    )
    receipt = builder.build_release(redirect_source, tmp_path / "redirect-release")
    assert receipt["verification"]["intentional_redirect_documentation_files"] == 1


def test_tree_hash_changes_for_text_but_not_binary_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    source.mkdir()
    (source / "index.html").write_text("<a href='/knowledge/'>Base</a>", encoding="utf-8")
    binary = b"\x00\x01\xff\xfe\x7f"
    (source / "asset.bin").write_bytes(binary)

    builder.build_release(source, output)
    assert (output / "asset.bin").read_bytes() == binary
    assert hashlib.sha256((output / "asset.bin").read_bytes()).hexdigest() == hashlib.sha256(binary).hexdigest()
    assert (output / "index.html").read_text(encoding="utf-8") == "<a href='/'>Base</a>"
