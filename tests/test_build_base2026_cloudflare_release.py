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
    assert receipt["source"]["file_count"] == 11
    assert receipt["source"]["excluded_file_count"] == 2
    assert receipt["artifact"]["file_count"] == 11
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
        )
        + '<link rel="stylesheet" href="static/site.css">'
        + '<script>fetch("static/manifest.json"); fetch(\'./static/analytics.json\')</script>',
        encoding="utf-8",
    )
    homepage.write_text(
        '<!doctype html><link rel="canonical" href="https://base2026.dev/">'
        '<a href="https://base2026.dev/workspace/">Search</a>',
        encoding="utf-8",
    )
    stylesheet.write_text("body{color:#111820}\n", encoding="utf-8")

    receipt = builder.build_release(
        source,
        output,
        homepage_template=homepage,
        homepage_stylesheet=stylesheet,
    )

    assert (output / "index.html").read_bytes() == homepage.read_bytes()
    workspace = (output / "workspace" / "index.html").read_text(encoding="utf-8")
    assert '<base href="/">' in workspace
    assert '<link rel="canonical" href="https://base2026.dev/workspace/" />' in workspace
    assert 'href="/static/site.css"' in workspace
    assert 'fetch("/static/manifest.json")' in workspace
    assert "fetch('/static/analytics.json')" in workspace
    assert '"static/' not in workspace
    assert "'./static/" not in workspace
    assert (output / "static" / "base2026-startup-homepage.css").read_bytes() == stylesheet.read_bytes()
    assert (output / "support.html").is_file()
    assert (output / "partner.html").is_file()
    assert (output / "privacy.html").is_file()
    assert (output / "about.html").is_file()
    assert (output / "static" / "base2026-forms.js").is_file()
    assert (output / "static" / "brand" / "github.svg").is_file()
    assert (output / "static" / "base2026-mark.svg").is_file()
    assert receipt["verification"]["personal_site_origin_markers_remaining"] == 0
    assert receipt["artifact"]["file_count"] == 22


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
