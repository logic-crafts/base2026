from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate-base2026-sitemap.py"
SPEC = importlib.util.spec_from_file_location("generate_base2026_sitemap", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_html(path: Path, head: str) -> None:
    path.write_text(f"<!doctype html><html><head>{head}</head><body></body></html>\n", encoding="utf-8")


def test_noindex_detection_is_attribute_order_independent(tmp_path: Path) -> None:
    first = tmp_path / "first.html"
    second = tmp_path / "second.html"
    write_html(first, '<meta name="robots" content="noindex,follow">')
    write_html(second, '<meta content="noindex,follow" name="robots">')

    assert MODULE.is_indexable(first) is False
    assert MODULE.is_indexable(second) is False


def test_indexable_page_and_canonical_are_attribute_order_independent(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    write_html(
        page,
        '<meta content="index,follow" name="robots">'
        '<link href="https://aggressorbulkit.online/knowledge/page.html" rel="canonical">',
    )

    assert MODULE.is_indexable(page) is True
    assert MODULE.canonical_url(page) == "https://aggressorbulkit.online/knowledge/page.html"


def test_noindex_token_is_exact_not_substring(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    write_html(page, '<meta content="noindex-preview,follow" name="robots">')

    assert MODULE.is_indexable(page) is True


def test_source_detail_manifest_includes_archive_noindex_and_excludes_future(
    tmp_path: Path, monkeypatch
) -> None:
    web_root = tmp_path / "web"
    sources = web_root / "sources"
    sources.mkdir(parents=True)
    write_html(sources / "normal.html", '<meta content="index,follow" name="robots">')
    write_html(sources / "archive.html", '<meta content="noindex,follow" name="robots">')
    manifest = tmp_path / "candidate-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "rendered": [
                    {"route": "sources/normal.html", "admission_state": "normal_public_card"},
                    {"route": "sources/archive.html", "admission_state": "provenance_archive_noindex"},
                ],
                "future_private_not_emitted": ["sources/future.html"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--web-root",
            str(web_root),
            "--source-detail-manifest",
            str(manifest),
            "--chunk-size",
            "10",
        ],
    )

    assert MODULE.main() == 0
    chunk = (web_root / "sitemaps" / "base2026-001.xml").read_text(encoding="utf-8")
    locations = set(re.findall(r"<loc>(.*?)</loc>", chunk))
    assert "https://aggressorbulkit.online/knowledge/sources/normal.html" in locations
    assert "https://aggressorbulkit.online/knowledge/sources/archive.html" in locations
    assert all("future.html" not in location for location in locations)


def test_source_detail_manifest_fails_closed_if_future_route_is_emitted(
    tmp_path: Path, monkeypatch
) -> None:
    web_root = tmp_path / "web"
    sources = web_root / "sources"
    sources.mkdir(parents=True)
    write_html(sources / "future.html", '<meta content="noindex,follow" name="robots">')
    manifest = tmp_path / "candidate-manifest.json"
    manifest.write_text(
        json.dumps({"rendered": [], "future_private_not_emitted": ["sources/future.html"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT), "--web-root", str(web_root), "--source-detail-manifest", str(manifest)],
    )

    try:
        MODULE.main()
    except SystemExit as exc:
        assert "future_private_emitted=1" in str(exc)
    else:
        raise AssertionError("future/private route emission must fail closed")
