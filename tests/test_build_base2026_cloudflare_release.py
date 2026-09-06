from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import zipfile
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
    (root / "static" / "insight_cards.jsonl").write_text(
        json.dumps(
            {
                "id": "insight:fixture-public",
                "public": True,
                "needs_review": False,
                "public_policy": "reviewed_insight",
            }
        )
        + "\n",
        encoding="utf-8",
    )
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
    (root / builder.ASSETSIGNORE_FILENAME).write_text(
        "stale generated metadata\n", encoding="utf-8"
    )
    (root / builder.RECEIPT_FILENAME).write_text(
        json.dumps({"artifact": {"tree_sha256": "stale"}}), encoding="utf-8"
    )
    (root / "knowledge" / "solutions" / "solutions").mkdir(parents=True)
    (root / "knowledge" / "solutions" / "solutions" / "index.html").write_text(
        "stale", encoding="utf-8"
    )


def write_legacy_plugin_fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> bytes:
    """Add a tiny deterministic retained-archive fixture for standalone tests."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entry = zipfile.ZipInfo(
            "base2026-evidence-sidebar/readme.txt", (2026, 9, 5, 0, 0, 0)
        )
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, b"legacy fixture\n", compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = buffer.getvalue()
    legacy_path = root / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_bytes(payload)
    monkeypatch.setattr(
        builder, "WORDPRESS_PLUGIN_LEGACY_DOWNLOAD_SHA256", hashlib.sha256(payload).hexdigest()
    )
    return payload


def test_tree_digest_is_independent_of_walk_order() -> None:
    records = [
        builder.FileRecord(name, digest, digest, 4, 4, "text", False)
        for name, digest in (("z.html", "b" * 64), ("a/index.html", "a" * 64))
    ]
    assert builder._tree_digest(records, source=True) == builder._tree_digest(list(reversed(records)), source=False)


def test_wordpress_download_is_deterministic_and_exact_source_only() -> None:
    payload = builder._wordpress_plugin_package()
    assert payload == builder._wordpress_plugin_package()
    assert len(payload) == 20165
    assert hashlib.sha256(payload).hexdigest() == "0909cd308c94b356b7831113891dac55e6039225a3c1f5c603730b0502c8eea4"
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.namelist() == [f"base2026-evidence-sidebar/{name}" for name in builder.WORDPRESS_PLUGIN_FILES]
        for entry, relative in zip(archive.infolist(), builder.WORDPRESS_PLUGIN_FILES):
            assert archive.read(entry) == (builder.WORDPRESS_PLUGIN_ROOT / relative).read_bytes()
            assert entry.date_time == (2026, 9, 5, 0, 0, 0)
            assert entry.flag_bits & 1 == 0
    assert builder._is_excluded_source_path(Path(builder.WORDPRESS_PLUGIN_DOWNLOAD))
    assert not builder._is_excluded_source_path(Path(builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD))
    builder._validate_public_relative_path(Path(builder.WORDPRESS_PLUGIN_DOWNLOAD))
    builder._validate_public_relative_path(Path(builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD))
    with pytest.raises(builder.ReleaseBuildError, match="archive"):
        builder._validate_public_relative_path(Path("downloads/arbitrary-release.zip"))


def test_wordpress_download_rejects_header_filename_version_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        builder,
        "WORDPRESS_PLUGIN_DOWNLOAD",
        "downloads/base2026-evidence-sidebar-v0.1.0.zip",
    )
    with pytest.raises(builder.ReleaseBuildError, match="version"):
        builder._wordpress_plugin_package()


def test_standalone_release_requires_retained_legacy_plugin_zip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_fixture(source)

    with pytest.raises(builder.ReleaseBuildError, match="requires the retained legacy"):
        builder.build_release(
            source,
            tmp_path / "release",
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )


def test_standalone_release_rejects_tampered_retained_legacy_plugin_zip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_fixture(source)
    payload = write_legacy_plugin_fixture(source, monkeypatch)
    (source / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD).write_bytes(payload + b"tampered")

    with pytest.raises(builder.ReleaseBuildError, match="legacy WordPress plugin archive hash"):
        builder.build_release(
            source,
            tmp_path / "release",
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )


def test_nonstandalone_release_preserves_pinned_legacy_plugin_zip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_fixture(source)
    payload = write_legacy_plugin_fixture(source, monkeypatch)

    receipt = builder.build_release(source, tmp_path / "release")
    output_path = tmp_path / "release" / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD
    assert output_path.read_bytes() == payload
    assert builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD not in receipt["excluded_source_paths"]
    assert receipt["verification"]["wordpress_plugin_legacy_download_present"] is True
    assert receipt["verification"]["wordpress_plugin_legacy_download_verified"] is True
    assert receipt["verification"]["wordpress_plugin_legacy_download_sha256"] == hashlib.sha256(payload).hexdigest()


def test_wordpress_package_rejects_symlink_and_private_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "plugin"
    root.mkdir()
    monkeypatch.setattr(builder, "WORDPRESS_PLUGIN_ROOT", root)
    monkeypatch.setattr(builder, "WORDPRESS_PLUGIN_FILES", ("readme.txt",))
    (root / "readme.txt").write_text("/Users/example/private/release.txt", encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError, match="private marker"):
        builder._wordpress_plugin_package()
    (root / "readme.txt").unlink()
    (root / "readme.txt").symlink_to(tmp_path / "outside.txt")
    with pytest.raises(builder.ReleaseBuildError, match="regular reviewed"):
        builder._wordpress_plugin_package()


def test_current_plugin_zip_is_never_inherited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    old_archive = source / builder.WORDPRESS_PLUGIN_DOWNLOAD
    old_archive.parent.mkdir(exist_ok=True)
    old_archive.write_bytes(b"untrusted old archive bytes must never be served")
    result = builder.build_release(
        source, tmp_path / "candidate",
        homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
        homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
    )
    assert builder.WORDPRESS_PLUGIN_DOWNLOAD in result["excluded_source_paths"]
    assert (tmp_path / "candidate" / builder.WORDPRESS_PLUGIN_DOWNLOAD).read_bytes() == builder._wordpress_plugin_package()
    legacy_output = tmp_path / "candidate" / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD
    assert legacy_output.read_bytes() == (source / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD).read_bytes()
    assert result["verification"]["wordpress_plugin_legacy_download_verified"] is True


def test_member_assets_are_additive_idempotent_and_require_complete_html() -> None:
    original = (
        '<html><head><title>Search</title></head><body>'
        '<main id="hits">Public results stay here</main>'
        '<script src="/static/meili.js?v=protected"></script></body></html>'
    )
    actual = builder._with_member_workspace_assets(original)
    assert '<main id="hits">Public results stay here</main>' in actual
    assert '<script src="/static/meili.js?v=protected"></script>' in actual
    assert actual.count("base2026-members.js") == 1
    assert actual.count("base2026-members.css") == 1
    assert builder._with_member_workspace_assets(actual) == actual
    with pytest.raises(builder.ReleaseBuildError):
        builder._with_member_workspace_assets("<main>Incomplete source</main>")


def test_member_workspace_requires_explicit_shell_and_preserves_public_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    (source / "search.html").write_text(
        '<html><head><title>Search</title></head><body>'
        '<main id="hits">Public results</main>'
        '<script src="/static/meili.js"></script></body></html>', encoding="utf-8"
    )
    (source / "static" / "meili.js").write_text("/* protected search renderer */", encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError, match="current startup shell"):
        builder.build_release(source, tmp_path / "no-shell", members_workspace=True)

    options = {
        "homepage_template": builder.DEFAULT_HOMEPAGE_TEMPLATE,
        "homepage_stylesheet": builder.DEFAULT_HOMEPAGE_STYLESHEET,
    }
    base = builder.build_release(source, tmp_path / "base", **options)
    candidate = builder.build_release(source, tmp_path / "member", members_workspace=True, **options)
    base_files = {entry["path"]: entry["artifact_sha256"] for entry in base["files"]}
    member_files = {entry["path"]: entry["artifact_sha256"] for entry in candidate["files"]}
    assert set(member_files) - set(base_files) == {
        "my-research/index.html", "static/base2026-members.css", "static/base2026-members.js"
    }
    assert {name for name in base_files if base_files[name] != member_files[name]} == {
        "workspace/index.html", "privacy.html"
    }
    assert base_files["static/meili.js"] == member_files["static/meili.js"]
    member_html = (tmp_path / "member/my-research/index.html").read_text(encoding="utf-8")
    assert "noindex" in member_html
    for sitemap in (tmp_path / "member").rglob("*.xml"):
        assert "/my-research" not in sitemap.read_text(encoding="utf-8")
    assert 'id="b26-members-privacy"' in (tmp_path / "member/privacy.html").read_text(encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError, match="explicit --members-workspace"):
        builder.build_release(tmp_path / "member", tmp_path / "unintended-downgrade", **options)


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
        '<a href="/api.html">API</a>'
        '<a href="../topics/internal-linking.html#sources">Topic</a>'
        '<a href="creators/example.html">Creator</a>',
        standalone_startup=True,
    )
    assert 'href="https://base2026.dev/roadmap"' in standalone.text
    assert 'href="/api"' in standalone.text
    assert 'href="../topics/internal-linking#sources"' in standalone.text
    assert 'href="creators/example"' in standalone.text
    assert standalone.replacements.html_urls_to_extensionless == 4


def test_runtime_guides_are_removed_from_static_sitemap_only() -> None:
    guide = builder.RUNTIME_GUIDE_ROUTES[0]
    other = "/topics/another-public-topic"
    sitemap = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>https://base2026.dev{other}-before</loc></url>'
        f'<url><loc>https://base2026.dev{guide}</loc></url>'
        f'<url><loc>https://base2026.dev{other}</loc></url>'
        '</urlset>'
    )
    cleaned = builder._remove_runtime_owned_urls_from_static_sitemap(sitemap)
    assert guide not in cleaned
    assert other in cleaned
    assert f"{other}-before" in cleaned


def test_hub_urls_are_owned_only_by_the_hub_sitemap() -> None:
    route = "/analytics"
    sitemap = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://base2026.dev/keep</loc></url>'
        f'<url><loc>https://base2026.dev{route}</loc></url>'
        '</urlset>'
    )
    cleaned = builder._remove_runtime_owned_urls_from_static_sitemap(sitemap)
    assert route not in cleaned
    assert "/keep" in cleaned


def _write_source_pagination_page(root: Path, page_number: int, *, old_origin: bool = False) -> None:
    canonical = (
        f"https://aggressorbulkit.online/knowledge/sources/page-{page_number}.html"
        if old_origin
        else f"https://base2026.dev/sources/page-{page_number}"
    )
    path = root / "sources" / f"page-{page_number}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<!doctype html><html><head>"
        '<meta name="robots" content="index,follow">'
        f'<link rel="canonical" href="{canonical}">'
        f"</head><body>Source page {page_number}</body></html>\n",
        encoding="utf-8",
    )


def _write_source_pagination_sitemap(root: Path, locations: list[str]) -> None:
    (root / "sitemaps").mkdir(parents=True, exist_ok=True)
    urls = "".join(f"<url><loc>{location}</loc></url>" for location in locations)
    (root / "sitemaps" / "base2026-001.xml").write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>\n",
        encoding="utf-8",
    )


def test_source_pagination_sitemap_contract_is_exactly_once_and_not_hub_owned(
    tmp_path: Path,
) -> None:
    stage = tmp_path / "stage"
    _write_source_pagination_page(stage, 2)
    _write_source_pagination_page(stage, 20)
    page_urls = [
        "https://base2026.dev/sources/page-2",
        "https://base2026.dev/sources/page-20",
    ]
    _write_source_pagination_sitemap(stage, page_urls)
    hub_sitemap = stage / builder.HUB_SITEMAP_FILENAME
    hub_sitemap.write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://base2026.dev/</loc></url></urlset>\n",
        encoding="utf-8",
    )

    verification = builder._validate_source_pagination_sitemap_contract(stage)

    assert verification == {
        "source_pagination_indexable_pages": 2,
        "source_pagination_static_sitemap_urls": 2,
        "source_pagination_static_sitemap_shards": 1,
        "source_pagination_runtime_owned_urls": 0,
    }
    static_sitemap = builder._sitemap_locs(stage / "sitemaps/base2026-001.xml")
    assert all(static_sitemap.count(url) == 1 for url in page_urls)
    assert all(url not in hub_sitemap.read_text(encoding="utf-8") for url in page_urls)

    hub_sitemap.write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{page_urls[0]}</loc></url></urlset>\n",
        encoding="utf-8",
    )
    with pytest.raises(builder.ReleaseBuildError, match="source pagination sitemap contract failed"):
        builder._validate_source_pagination_sitemap_contract(stage)

    hub_sitemap.write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://base2026.dev/</loc></url></urlset>\n",
        encoding="utf-8",
    )

    _write_source_pagination_sitemap(stage, page_urls + [page_urls[0]])
    with pytest.raises(builder.ReleaseBuildError, match="source pagination sitemap contract failed"):
        builder._validate_source_pagination_sitemap_contract(stage)


def test_startup_release_fails_closed_when_source_pagination_is_missing_from_static_sitemap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    _write_source_pagination_page(source, 2, old_origin=True)
    _write_source_pagination_page(source, 20, old_origin=True)
    _write_source_pagination_sitemap(
        source,
        ["https://aggressorbulkit.online/knowledge/sources/page-2.html"],
    )

    output = tmp_path / "release"
    with pytest.raises(builder.ReleaseBuildError, match="source pagination sitemap contract failed"):
        builder.build_release(
            source,
            output,
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )
    assert not output.exists()


def test_excluded_route_removal_never_consumes_adjacent_sitemap_entries() -> None:
    sitemap = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://base2026.dev/keep-before</loc></url>'
        '<url><loc>https://base2026.dev/retired</loc></url>'
        '<url><loc>https://base2026.dev/keep-after</loc></url>'
        '</urlset>'
    )
    cleaned = builder._remove_excluded_startup_route_references(sitemap, ["/retired"])
    assert "/retired" not in cleaned
    assert "/keep-before" in cleaned
    assert "/keep-after" in cleaned


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
    assert receipt["source"]["file_count"] == 15
    assert receipt["source"]["excluded_file_count"] == 4
    assert receipt["artifact"]["file_count"] == 13
    assert receipt["output"]["file_count"] == 15
    assert all(
        record["path"] not in {builder.ASSETSIGNORE_FILENAME, builder.RECEIPT_FILENAME}
        for record in receipt["files"]
    )
    assert receipt["verification"]["static_manifest_files_match"] is True
    assert receipt["verification"]["binary_bytes_preserved"] is True
    assert receipt["verification"]["local_path_markers_remaining"] == 0
    assert receipt["verification"]["private_token_markers_remaining"] == 0


def test_static_cache_headers_keep_html_and_jsonl_rules_disjoint() -> None:
    headers = builder.HEADERS_PAYLOAD

    assert "/*\n  Cache-Control: no-cache" not in headers
    assert "/*.html\n  Cache-Control: no-cache" in headers
    assert "/*/\n  Cache-Control: no-cache" in headers
    assert "/static/*\n  Cache-Control: no-cache" not in headers
    assert (
        "/static/*.jsonl\n"
        "  Content-Type: application/x-ndjson; charset=utf-8\n"
        "  Cache-Control: public, max-age=300, s-maxage=3600"
    ) in headers


def test_startup_homepage_overlay_preserves_search_as_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    homepage = tmp_path / "startup-homepage.html"
    stylesheet = tmp_path / "startup-homepage.css"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
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
    assert (output / "founder.html").is_file()
    assert (output / "dataset.html").is_file()
    assert (output / "journal" / "source-backed-video-search-cloudflare" / "index.html").is_file()
    assert (output / "apply-research.html").is_file()
    assert (output / "ai-visibility-resources.html").is_file()
    assert (output / "static" / "base2026-forms.js").is_file()
    assert (output / "static" / "base2026-evidence-brief.js").read_bytes() == builder.DEFAULT_EVIDENCE_BRIEF_SCRIPT.read_bytes()
    assert (output / "static" / "roadmap.js").read_bytes() == builder.DEFAULT_ROADMAP_SCRIPT.read_bytes()
    roadmap = (output / "roadmap.html").read_text(encoding="utf-8")
    assert "The complete public product runs on Cloudflare" in roadmap
    assert "Cloudflare Workers serves the site, read-only API, forms, and public search." in roadmap
    assert "Public D1 with FTS5 powers the search workspace without a browser API key." in roadmap
    for stale_phrase in ("Public VPS deployment", "local-first knowledge base", "Small VPS"):
        assert stale_phrase not in roadmap
    analytics = (output / "analytics.html").read_text(encoding="utf-8")
    assert 'data-b26-public-stat="documents_indexed"' in analytics
    assert "Historical release analytics" in analytics
    assert "2026-07-29 static release" in analytics
    assert "1,724" in analytics
    assert "2,319" in analytics
    assert "1,939" in analytics
    assert "1,204" in analytics
    assert "28 signal briefs" in analytics
    assert "<tbody></tbody>" not in analytics
    api_page = (output / "api.html").read_text(encoding="utf-8")
    assert "GET /api/stats" in api_page
    assert "D1 FTS5" in api_page
    assert "server-side Meilisearch proxy" not in api_page
    mcp_page = (output / "mcp.html").read_text(encoding="utf-8")
    assert "POST https://base2026.dev/api/mcp" in mcp_page
    assert "search_sources" in mcp_page
    integrations_page = (output / "integrations.html").read_text(encoding="utf-8")
    assert "codex mcp add base2026" in integrations_page
    assert "claude mcp add --transport http base2026" in integrations_page
    data_dictionary = json.loads((output / "data-dictionary.json").read_text(encoding="utf-8"))
    assert "full private transcripts" in data_dictionary["public_boundary"]["not_public"]
    llms = (output / "llms.txt").read_text(encoding="utf-8")
    root_llms = (output / "root-llms.txt").read_text(encoding="utf-8")
    assert "https://base2026.dev/api/mcp" in llms
    assert "https://base2026.dev/api/mcp" in root_llms
    api_index = json.loads((output / "api-index.json").read_text(encoding="utf-8"))
    endpoint_urls = {endpoint["url"] for endpoint in api_index["endpoints"]}
    assert "https://base2026.dev/api/stats" in endpoint_urls
    assert "https://base2026.dev/api/evidence-brief/v2?q={question}" in endpoint_urls
    entry_point_urls = {
        entry_point["id"]: entry_point["url"]
        for entry_point in api_index["entry_points"]
    }
    assert entry_point_urls["human_search_workspace"] == "https://base2026.dev/workspace/"
    assert (output / "static" / "brand" / "github.svg").is_file()
    assert (output / "static" / "base2026-mark.svg").is_file()
    assert (output / "static" / "base2026-founder.css").read_bytes() == builder.DEFAULT_FOUNDER_STYLESHEET.read_bytes()
    assert (output / "static" / "assets" / "alex-yarosh-founder-step-wall.webp").read_bytes() == builder.DEFAULT_FOUNDER_HERO_IMAGE.read_bytes()
    assert (output / builder.HUB_SITEMAP_FILENAME).is_file()
    assert builder.HUB_SITEMAP_URL in (output / "sitemap.xml").read_text(encoding="utf-8")
    assert "sitemap-dynamic.xml" in (output / "robots.txt").read_text(encoding="utf-8")
    assert "https://base2026.dev/roadmap.html" not in (output / "sitemap.xml").read_text(encoding="utf-8")
    support = (output / "support.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/support">' in support
    assert 'href="/roadmap"' in support
    founder = (output / "founder.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/founder">' in founder
    assert "Alex Yarosh" in founder
    assert 'id="selected-work"' in founder
    assert 'href="/static/base2026-founder.css?v=20260906-founder-editorial-v1"' in founder
    assert 'src="/static/assets/founder-editorial-20260906/alex-yarosh-cobalt-portrait.webp"' in founder
    assert receipt["verification"]["editorial_media_verified"] is True
    assert receipt["verification"]["editorial_media_count"] == 4
    for name, (size, digest) in builder.EDITORIAL_MEDIA_ALLOWLIST.items():
        payload = (output / name).read_bytes()
        assert (len(payload), hashlib.sha256(payload).hexdigest()) == (size, digest)
    assert 'href="/founder"' in rendered_homepage
    assert 'href="/dataset"' in rendered_homepage
    dataset = (output / "dataset.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/dataset">' in dataset
    assert '"@type":"Dataset"' in dataset
    assert "https://base2026.dev/static/documents.jsonl" in dataset
    assert "full private transcripts" in dataset
    journal = (
        output / "journal" / "source-backed-video-search-cloudflare" / "index.html"
    ).read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/journal/source-backed-video-search-cloudflare/">' in journal
    assert '"@type":"TechArticle"' in journal
    assert "Alex Yarosh" in journal
    assert "raw media, raw captions and raw ASR" in journal
    assert "works entirely for free" not in journal
    assert "https://base2026.dev/journal/source-backed-video-search-cloudflare/" in (
        output / builder.HUB_SITEMAP_FILENAME
    ).read_text(encoding="utf-8")
    hub_sitemap = (output / builder.HUB_SITEMAP_FILENAME).read_text(encoding="utf-8")
    assert "https://base2026.dev/workspace/" not in hub_sitemap
    assert 'href="/workspace/"' in rendered_homepage
    assert "Maharani" not in founder
    assert "Primavera" not in founder
    assert receipt["verification"]["personal_site_origin_markers_remaining"] == 0
    assert receipt["replacements"]["html_urls_to_extensionless"] > 0
    assert receipt["verification"]["redirecting_html_canonical_markers_remaining"] == 0
    assert receipt["verification"]["redirecting_html_sitemap_markers_remaining"] == 0
    # Blog files, guide assets, the three public tools, activation, and the
    # tools hub's HTML/CSS/JS are additive; retained assets stay intact.
    tools_studio = (output / "tools" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/tools/">' in tools_studio
    assert "Free tools. Real next steps." in tools_studio
    assert 'href="/tools/"' in rendered_homepage
    assert "https://base2026.dev/tools/" in hub_sitemap
    assert hub_sitemap.count("https://base2026.dev/tools/page-readiness/") == 1
    assert (output / "static" / "base2026-tools-studio.css").read_bytes() == builder.DEFAULT_TOOLS_STUDIO_STYLESHEET.read_bytes()
    assert (output / "static" / "base2026-tools-studio.js").read_bytes() == builder.DEFAULT_TOOLS_STUDIO_SCRIPT.read_bytes()
    page_source = (output / "tools/page-readiness/index.html").read_text(encoding="utf-8")
    assert "Page Source Check" in page_source
    assert '<link rel="canonical" href="https://base2026.dev/tools/page-readiness/">' in page_source
    assert page_source.count('<header class="b26-site-header') == 1
    assert builder.STARTUP_CORE_LINK in page_source
    for extension in ("css", "js"):
        assert (output / f"static/base2026-page-readiness.{extension}").read_bytes() == (
            ROOT / f"templates/base2026-page-readiness.{extension}"
        ).read_bytes()
    media_manifest_path = ROOT / "templates/assets/tools-studio/asset-manifest.json"
    media_manifest = json.loads(media_manifest_path.read_text(encoding="utf-8"))
    media_entries = {entry["file"]: entry for entry in media_manifest["assets"]}
    media_records = {
        record["path"]: record
        for record in receipt["files"]
        if record["path"].startswith("static/assets/tools-studio/")
    }
    assert not (output / builder.TOOLS_STUDIO_MEDIA_MANIFEST_OUTPUT).exists()
    assert set(media_records) == {
        f"static/assets/tools-studio/{name}"
        for name in builder.TOOLS_STUDIO_REVIEWED_MEDIA_NAMES
    }
    for name in builder.TOOLS_STUDIO_REVIEWED_MEDIA_NAMES:
        manifest_entry = media_entries[name]
        expected_path = f"static/assets/tools-studio/{name}"
        expected_payload = (ROOT / "templates/assets/tools-studio" / name).read_bytes()
        assert (output / expected_path).read_bytes() == expected_payload
        record = media_records[expected_path]
        assert record["kind"] == "binary"
        assert record["changed"] is False
        assert record["source_bytes"] == manifest_entry["bytes"]
        assert record["artifact_bytes"] == manifest_entry["bytes"]
        assert record["source_sha256"] == manifest_entry["sha256"]
        assert record["artifact_sha256"] == manifest_entry["sha256"]
    provenance = receipt["reviewed_repository_media"]
    assert sorted(entry["output_path"] for entry in provenance) == sorted(media_records)
    for entry in provenance:
        manifest_entry = media_entries[entry["file"]]
        assert entry["source_path"] == f"templates/assets/tools-studio/{entry['file']}"
        assert entry["manifest_path"] == "templates/assets/tools-studio/asset-manifest.json"
        assert entry["source_sha256"] == manifest_entry["sha256"]
        assert entry["artifact_sha256"] == manifest_entry["sha256"]
        assert entry["source_bytes"] == manifest_entry["bytes"]
        assert entry["artifact_bytes"] == manifest_entry["bytes"]
        assert entry["manifest_sha256"] == builder.TOOLS_STUDIO_REVIEWED_MEDIA_MANIFEST_SHA256
        assert entry["candidate_url"] == manifest_entry["candidateUrl"]
        assert entry["provenance"] == manifest_entry["source"]
        assert entry["kind"] == "binary"
    assert receipt["verification"]["reviewed_repository_media_verified"] is True
    assert receipt["verification"]["reviewed_repository_media_count"] == 4
    assert receipt["verification"]["reviewed_repository_media_manifest_sha256"] == builder.TOOLS_STUDIO_REVIEWED_MEDIA_MANIFEST_SHA256
    current_plugin_output = output / builder.WORDPRESS_PLUGIN_DOWNLOAD
    legacy_plugin_output = output / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD
    assert current_plugin_output.read_bytes() == builder._wordpress_plugin_package()
    assert legacy_plugin_output.read_bytes() == (source / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD).read_bytes()
    assert receipt["verification"]["wordpress_plugin_package_verified"] is True
    assert receipt["verification"]["wordpress_plugin_legacy_download_verified"] is True
    assert receipt["artifact"]["file_count"] == 122
    for generated_path in (
        "static/base2026-investors.css",
        "static/base2026-public-pages.css",
        "roadmap.html",
        "methodology.html",
        "source-policy.html",
    ):
        assert (output / generated_path).is_file()
    blog = (output / "blog.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/blog">' in blog
    assert 'data-b26-blog-schema' in blog
    assert "{{BLOG_" not in blog
    assert blog.count("<!--B26_BLOG_FEATURED_START-->") == 1
    assert 'href="/journal/source-diversity-check/"' in blog
    assert 'href="/journal/source-backed-video-search-cloudflare/"' in blog
    assert 'href="/blog/"' in rendered_homepage
    assert "https://base2026.dev/blog" in hub_sitemap
    assert "Sitemap: https://base2026.dev/sitemap-blog.xml" in (output / "robots.txt").read_text(encoding="utf-8")
    # The blog sitemap is an independent index; do not nest it in sitemap.xml.
    assert "sitemap-blog.xml" not in (output / "sitemap.xml").read_text(encoding="utf-8")
    assert (output / "static/base2026-blog.css").read_bytes() == builder.DEFAULT_BLOG_STYLESHEET.read_bytes()
    assert (output / "static/base2026-blog-article.css").read_bytes() == builder.DEFAULT_BLOG_ARTICLE_STYLESHEET.read_bytes()
    assert "Sitemap: https://base2026.dev/sitemap-guides.xml" in (output / "robots.txt").read_text(encoding="utf-8")
    assert "sitemap-guides.xml" not in (output / "sitemap.xml").read_text(encoding="utf-8")
    assert (output / "static/base2026-evidence-guide.css").read_bytes() == builder.DEFAULT_EVIDENCE_GUIDE_STYLESHEET.read_bytes()
    assert (output / "static/base2026-evidence-guide.js").read_bytes() == builder.DEFAULT_EVIDENCE_GUIDE_SCRIPT.read_bytes()
    assert (output / "static/base2026-activation-measurement.js").read_bytes() == builder.DEFAULT_ACTIVATION_MEASUREMENT_SCRIPT.read_bytes()
    source_diversity_page = output / "tools/source-diversity-check/index.html"
    assert source_diversity_page.is_file()
    assert (output / "static/base2026-source-diversity-check.css").read_bytes() == builder.DEFAULT_SOURCE_DIVERSITY_CHECK_STYLESHEET.read_bytes()
    assert (output / "static/base2026-source-diversity-check.js").read_bytes() == builder.DEFAULT_SOURCE_DIVERSITY_CHECK_SCRIPT.read_bytes()
    assert '<link rel="canonical" href="https://base2026.dev/tools/source-diversity-check/">' in source_diversity_page.read_text(encoding="utf-8")
    assert "https://base2026.dev/tools/source-diversity-check/" in hub_sitemap
    assert (output / "static/assets/base2026-ai-visibility-measurement.png").read_bytes() == builder.DEFAULT_EDITORIAL_MEASUREMENT_IMAGE.read_bytes()


def test_startup_release_rejects_tampered_retained_tools_studio_media(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    retained = source / builder.TOOLS_STUDIO_MEDIA_OUTPUT_PREFIX / "evidence-workbench.webp"
    retained.parent.mkdir(parents=True)
    retained.write_bytes(b"tampered retained media")

    with pytest.raises(builder.ReleaseBuildError, match="retained Tools Studio media hash/bytes mismatch"):
        builder.build_release(
            source,
            output,
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )
    assert not output.exists()


def test_startup_release_accepts_exact_retained_tools_studio_media(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    retained_root = source / builder.TOOLS_STUDIO_MEDIA_OUTPUT_PREFIX
    retained_root.mkdir(parents=True)
    repository_root = ROOT / "templates/assets/tools-studio"
    for name in builder.TOOLS_STUDIO_REVIEWED_MEDIA_NAMES:
        (retained_root / name).write_bytes((repository_root / name).read_bytes())
    (retained_root / "asset-manifest.json").write_bytes(
        (repository_root / "asset-manifest.json").read_bytes()
    )

    receipt = builder.build_release(
        source,
        output,
        homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
        homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
    )

    assert receipt["artifact"]["file_count"] == 122
    assert receipt["verification"]["reviewed_repository_media_verified"] is True
    assert not (output / builder.TOOLS_STUDIO_MEDIA_MANIFEST_OUTPUT).exists()


def test_startup_release_rejects_incomplete_retained_tools_studio_media(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    retained_root = source / builder.TOOLS_STUDIO_MEDIA_OUTPUT_PREFIX
    retained_root.mkdir(parents=True)
    repository_root = ROOT / "templates/assets/tools-studio"
    (retained_root / "evidence-workbench.webp").write_bytes(
        (repository_root / "evidence-workbench.webp").read_bytes()
    )

    with pytest.raises(builder.ReleaseBuildError, match="media set is incomplete"):
        builder.build_release(
            source,
            output,
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )
    assert not output.exists()


def test_startup_release_rejects_tampered_retained_tools_studio_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    retained_manifest = source / builder.TOOLS_STUDIO_MEDIA_MANIFEST_OUTPUT
    retained_manifest.parent.mkdir(parents=True)
    retained_manifest.write_text("{}\n", encoding="utf-8")

    with pytest.raises(builder.ReleaseBuildError, match="retained Tools Studio media manifest"):
        builder.build_release(
            source,
            output,
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )
    assert not output.exists()


def _patch_tools_studio_media_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    missing: str | None = None,
    tamper_manifest: bool = False,
) -> None:
    media_root = tmp_path / "reviewed-tools-studio-media"
    media_root.mkdir()
    source_root = ROOT / "templates/assets/tools-studio"
    for name in builder.TOOLS_STUDIO_REVIEWED_MEDIA_NAMES:
        if name != missing:
            (media_root / name).write_bytes((source_root / name).read_bytes())
    manifest_bytes = (source_root / "asset-manifest.json").read_bytes()
    if tamper_manifest:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        manifest["assets"][0]["sha256"] = "0" * 64
        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    manifest_path = media_root / "asset-manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    monkeypatch.setattr(builder, "DEFAULT_TOOLS_STUDIO_MEDIA_ROOT", media_root)
    monkeypatch.setattr(builder, "DEFAULT_TOOLS_STUDIO_MEDIA_MANIFEST", manifest_path)


def test_startup_release_rejects_missing_reviewed_tools_studio_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_tools_studio_media_fixture(
        tmp_path, monkeypatch, missing="evidence-search-card.png"
    )
    source = tmp_path / "source-web"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)

    with pytest.raises(builder.ReleaseBuildError, match="media source is missing"):
        builder.build_release(
            source,
            tmp_path / "release",
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )


def test_startup_release_rejects_wrong_reviewed_tools_studio_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_tools_studio_media_fixture(tmp_path, monkeypatch, tamper_manifest=True)
    source = tmp_path / "source-web"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)

    with pytest.raises(builder.ReleaseBuildError, match="media manifest hash"):
        builder.build_release(
            source,
            tmp_path / "release",
            homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
            homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
        )


def test_startup_homepage_exposes_product_first_evidence_brief_search() -> None:
    homepage = (ROOT / "templates" / "base2026-startup-homepage.html").read_text(encoding="utf-8")

    assert "Ask what SEO and AI-search practitioners actually said." in homepage
    assert 'action="/workspace/"' in homepage
    assert 'method="get"' in homepage
    assert 'name="q"' in homepage
    assert '<button class="b26-button--primary" type="submit">' in homepage
    assert homepage.count('class="b26-button--primary"') >= 1
    assert homepage.count('class="b26-suggested-queries"') == 1
    assert homepage.count('href="/workspace/?q=') >= 3
    assert 'id="evidence-brief-result"' in homepage
    assert '/static/base2026-evidence-brief.js' in homepage
    runtime = (ROOT / "templates" / "base2026-evidence-brief.js").read_text(encoding="utf-8")
    assert 'fetch(`/api/evidence-brief/v2?q=${encodeURIComponent(question)}`' in runtime
    assert "textContent" in runtime
    assert "innerHTML" not in runtime


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


def test_workspace_rewrite_keeps_project_story_on_the_about_route() -> None:
    rendered = builder._rewrite_workspace_html(
        '<a href="/workspace/">Project Story</a>'
        '<a href="/workspace/">Search workspace</a>'
        '<a href="./story.html">Project Story</a>'
    )

    assert rendered.count('<a href="/about">Project Story</a>') == 2
    assert '<a href="/workspace/">Project Story</a>' not in rendered
    assert '<a href="/workspace/">Search workspace</a>' in rendered


def test_workspace_fallback_counts_come_from_the_static_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "documents": 1525,
                "chunks": 2095,
                "creators": 18,
                "created_at": "2026-07-29T14:27:42",
            }
        ),
        encoding="utf-8",
    )
    rendered = builder._rewrite_workspace_html(
        '<strong data-manifest-count="documents">1,219</strong>'
        '<strong data-manifest-count="chunks">1,715</strong>'
        '<strong data-manifest-count="creators">4</strong>',
        builder._workspace_manifest_counts(manifest),
        builder._workspace_manifest_snapshot_date(manifest),
    )

    assert 'data-manifest-count="documents">1,525' in rendered
    assert 'data-manifest-count="chunks">2,095' in rendered
    assert 'data-manifest-count="creators">18' in rendered
    assert "Static snapshot · 2026-07-29" in rendered


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
    assert "https://base2026.dev/dataset" in llms
    assert "independent review question" in api


def test_public_insight_export_drops_review_holds_and_rejects_contradictions() -> None:
    held = {
        "id": "insight:held",
        "public": False,
        "needs_review": True,
        "public_policy": "needs_review",
    }
    public = {
        "id": "insight:public",
        "public": True,
        "needs_review": False,
        "public_policy": "reviewed_insight",
    }
    rendered = builder._rewrite_public_api_docs(
        Path("static/insight_cards.jsonl"),
        json.dumps(held) + "\n" + json.dumps(public) + "\n",
    )
    assert "insight:held" not in rendered
    assert "insight:public" in rendered

    contradictory = dict(public, needs_review=True)
    with pytest.raises(builder.ReleaseBuildError, match="contradictory public row"):
        builder._rewrite_public_api_docs(
            Path("static/insight_cards.jsonl"), json.dumps(contradictory) + "\n"
        )

    api_index = builder._rewrite_public_api_docs(
        Path("api-index.json"),
        '{"description": "Server-side Meilisearch multi-search proxy used by the public UI. Prefer static JSONL for bulk/offline analysis; use this endpoint when live search ranking is needed.", "guide": "Human-readable bridge from Base2026 public source intelligence to Alex Yarosh\'s business-specific AI visibility audit and service workflow."}',
    )
    assert "business-specific AI visibility audit" not in api_index
    assert "cloudflare_worker_d1_fts5" in api_index

    extensionless_api = builder._rewrite_public_api_docs(
        Path("api.html"),
        "<p>For business-specific implementation, use <code>/apply-research</code> as the public bridge from Base2026 source intelligence to Alex Yarosh&#x27;s AI Visibility Snapshot, Diagnostic Audit, and service workflow.</p>",
    )
    assert "service workflow" not in extensionless_api
    assert "independent review question" in extensionless_api


def test_api_index_workspace_route_is_owned_by_source_and_builder() -> None:
    source_text = (ROOT / "web" / "static" / "api-index.json").read_text(encoding="utf-8")
    source_payload = json.loads(source_text)
    source_workspace = next(
        entry
        for entry in source_payload["entry_points"]
        if entry["id"] == "human_search_workspace"
    )
    assert source_workspace["url"] == "https://base2026.dev/workspace/"

    legacy_root = source_text.replace(
        "https://base2026.dev/workspace/", "https://base2026.dev/"
    )
    rewritten = builder._rewrite_public_api_docs(Path("api-index.json"), legacy_root)
    rewritten_payload = json.loads(rewritten)
    rewritten_workspace = next(
        entry
        for entry in rewritten_payload["entry_points"]
        if entry["id"] == "human_search_workspace"
    )
    assert rewritten_workspace["url"] == "https://base2026.dev/workspace/"


def test_hub_sitemap_includes_developer_distribution_routes() -> None:
    payload = builder._hub_sitemap_payload().decode("utf-8")

    assert "https://base2026.dev/api" in payload
    assert "https://base2026.dev/mcp" in payload
    assert "https://base2026.dev/integrations" in payload


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


def test_startup_footer_keeps_cloudflare_provenance_mark() -> None:
    footer = (ROOT / "templates" / "base2026-startup-footer.html").read_text(encoding="utf-8")
    stylesheet = (ROOT / "templates" / "base2026-core.css").read_text(encoding="utf-8")

    assert footer.count('class="b26-cloudflare-mark"') == 1
    assert footer.count("Powered by") == 2
    assert 'href="https://www.cloudflare.com/"' in footer
    assert 'src="https://www.cloudflare.com/img/logo-cloudflare-dark.svg"' in footer
    assert ".b26-cloudflare-mark" in stylesheet


def test_source_lab_runtime_is_idempotent_and_vendor_loading_is_scoped() -> None:
    header = '<header class="b26-site-header">Base2026</header>'
    footer = '<footer class="b26-site-footer">Footer</footer>'
    for scene in (False, True):
        text = '<html><head></head><body><main' + (' data-lab-scene' if scene else '') + '>Readable</main></body></html>'
        once = builder._apply_startup_shell(text, header, footer)
        twice = builder._apply_startup_shell(once, header, footer)
        assert twice.count('src="/static/base2026-source-lab.js?v=20260906-agency"') == 1
        assert twice.count('src="/static/vendor/gsap/gsap.min.js?v=20260906-agency"') == int(scene)
        assert twice.count('src="/static/vendor/gsap/ScrollTrigger.min.js?v=20260906-agency"') == int(scene)
        assert '<main' in twice and 'Readable</main>' in twice


def test_workspace_keeps_search_before_background_copy_without_removing_content() -> None:
    source = '<html><head><title>Search</title></head><body class="legacy"><main><section class="hero workspace-hero"><h1>Original title</h1></section><section class="project-identity" aria-labelledby="identity"><h2 id="identity">Background</h2></section><section class="research-bridge" aria-labelledby="library-workflow-title"><p>Public boundary</p></section><section class="search-command"><div id="searchbox"></div></section><section class="meili-grid"><div id="hits"></div></section></main></body></html>'
    rendered = builder._rewrite_workspace_html(source)
    assert 'class="legacy b26-workspace"' in rendered
    assert rendered.index('id="searchbox"') < rendered.index('id="hits"') < rendered.index('id="identity"')
    assert rendered.count('id="identity"') == 1
    assert '<h1>Original title</h1>' in rendered and '<p>Public boundary</p>' in rendered
    assert builder._rewrite_workspace_html(rendered) == rendered


def test_source_lab_rebuild_preserves_explicit_released_member_runtime(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    released = b'/* newer released auth runtime */\nconst scope = "public";\n'
    (source / "search.html").write_text('<html><head><title>Search</title></head><body><main>Public search</main></body></html>')
    (source / "static/base2026-members.js").write_bytes(released)
    options = dict(homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE, homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET)
    with pytest.raises(builder.ReleaseBuildError, match="requires --members-workspace"):
        builder.build_release(source, tmp_path / "invalid", retain_member_script=True, **options)
    receipt = builder.build_release(source, tmp_path / "retained", members_workspace=True, retain_member_script=True, **options)
    assert (tmp_path / "retained/static/base2026-members.js").read_bytes() == released
    assert receipt["verification"]["member_script_retained"] is True
    assert receipt["verification"]["binary_bytes_preserved"] is True
    for name, (size, digest) in builder.SOURCE_LAB_MEDIA_ALLOWLIST.items():
        asset = tmp_path / "retained/static/assets/source-lab" / name
        assert asset.stat().st_size == size
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == digest
    homepage = (tmp_path / "retained/index.html").read_text()
    assert homepage.count('src="/static/vendor/gsap/gsap.min.js?v=20260906-agency"') == 1
    assert homepage.count('src="/static/vendor/gsap/ScrollTrigger.min.js?v=20260906-agency"') == 1
    assert homepage.count('src="/static/base2026-source-lab.js?v=20260906-agency"') == 1
    for route in ("tools/index.html", "workspace/index.html", "my-research/index.html"):
        page = (tmp_path / "retained" / route).read_text()
        assert page.count('src="/static/base2026-source-lab.js?v=20260906-agency"') == 1


def test_source_lab_asset_tampering_cannot_reach_output(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    media = tmp_path / "media"
    media.mkdir()
    for name in (*builder.SOURCE_LAB_MEDIA_ALLOWLIST, "asset-manifest.json"):
        (media / name).write_bytes((builder.SOURCE_LAB_MEDIA_ROOT / name).read_bytes())
    (media / "source-lab-hero.webp").write_bytes(b"changed")
    monkeypatch.setattr(builder, "SOURCE_LAB_MEDIA_ROOT", media)
    with pytest.raises(builder.ReleaseBuildError, match="differs from reviewed bytes"):
        builder.build_release(source, tmp_path / "rejected", homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE, homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET)
    assert not (tmp_path / "rejected").exists()


def test_brand_icons_replace_inherited_identity_once() -> None:
    original = '<html><head><link rel="icon" href="/old.svg"><link rel="apple-touch-icon" href="/personal.png"><link rel="stylesheet" href="/static/base2026-core.css?v=old"></head><body>Readable</body></html>'
    once = builder._with_brand_identity(original)
    assert builder._with_brand_identity(once) == once
    assert '/old.svg' not in once and '/personal.png' not in once
    assert once.count(builder.STARTUP_FAVICON_LINK) == 1
    assert once.count(builder.STARTUP_APPLE_ICON_LINK) == 1
    assert once.count(builder.STARTUP_CORE_LINK) == 1


def test_brand_manifest_cannot_authorize_changed_asset_bytes(tmp_path: Path, monkeypatch) -> None:
    media = tmp_path / "brand"
    media.mkdir()
    for name in (*builder.BRAND_MEDIA_ALLOWLIST, "b26-brand-manifest.json"):
        (media / name).write_bytes((builder.BRAND_MEDIA_ROOT / name).read_bytes())
    monkeypatch.setattr(builder, "BRAND_MEDIA_ROOT", media)
    assert set(builder._reviewed_brand_assets()) == set(builder.BRAND_MEDIA_ALLOWLIST)
    changed = b'not the approved mark'
    (media / "b26-seal.webp").write_bytes(changed)
    manifest = json.loads((media / "b26-brand-manifest.json").read_text())
    manifest["assets"]["b26-seal.webp"].update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
    (media / "b26-brand-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(builder.ReleaseBuildError, match="differs from reviewed bytes"):
        builder._reviewed_brand_assets()


def test_topic_conversion_rejects_missing_published_metadata() -> None:
    with pytest.raises(builder.ReleaseBuildError, match="without guessing"):
        builder._with_topic_discovery('<html><head></head><body><main><h1>Topics</h1></main></body></html>')


def test_editorial_media_allowlist_excludes_unreviewed_siblings(tmp_path: Path, monkeypatch) -> None:
    for name in builder.EDITORIAL_MEDIA_ALLOWLIST:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((builder.EDITORIAL_MEDIA_ROOT / name).read_bytes())
    sibling = tmp_path / next(iter(builder.EDITORIAL_MEDIA_ALLOWLIST))
    sibling.with_name("unreviewed-original.png").write_bytes(b"private source image")
    monkeypatch.setattr(builder, "EDITORIAL_MEDIA_ROOT", tmp_path)
    assert set(builder._reviewed_editorial_assets()) == set(builder.EDITORIAL_MEDIA_ALLOWLIST)


@pytest.mark.parametrize("replacement", ["changed", "symlink"])
def test_changed_editorial_media_cannot_reach_a_release(tmp_path: Path, monkeypatch, replacement: str) -> None:
    source = tmp_path / "source"
    write_fixture(source)
    write_legacy_plugin_fixture(source, monkeypatch)
    media_root = tmp_path / "media"
    for name in builder.EDITORIAL_MEDIA_ALLOWLIST:
        target = media_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((builder.EDITORIAL_MEDIA_ROOT / name).read_bytes())
    target = media_root / next(iter(builder.EDITORIAL_MEDIA_ALLOWLIST))
    if replacement == "changed":
        target.write_bytes(b"unreviewed replacement")
    else:
        original = tmp_path / "original.webp"
        original.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(original)
    monkeypatch.setattr(builder, "EDITORIAL_MEDIA_ROOT", media_root)
    output = tmp_path / "rejected"
    with pytest.raises(builder.ReleaseBuildError, match="editorial asset"):
        builder.build_release(source, output, homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE, homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET)
    assert not output.exists()
