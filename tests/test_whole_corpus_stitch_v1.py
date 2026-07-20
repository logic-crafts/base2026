from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "derive-base2026-knowledge-stitch-v1.py"
SPEC = importlib.util.spec_from_file_location("derive_base2026_knowledge_stitch_v1", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _page(main_class: str = "app-shell content-page doc-page ai-visibility-page") -> str:
    return f"""<!doctype html>
<html><head><title>AI Visibility Lab</title><link rel="canonical" href="https://example.test/knowledge/ai-visibility-pages/"></head>
<body class="legacy"><header class="site-header"><span>Old header</span></header>
<main class="{main_class}"><section class="ai-pages-intro"><h1>AI Visibility Lab</h1><p>Intro.</p></section><section class="content-section"><h2>Evidence</h2><p>Body.</p></section></main>
<footer class="site-footer"><span>Old footer</span></footer></body></html>"""


def test_ai_visibility_main_classes_remain_tokens_not_characters() -> None:
    rendered, family = MODULE.transform_page(_page(), "ai-visibility-pages/index.html")
    soup = BeautifulSoup(rendered, "html.parser")
    main = soup.select_one("main")

    assert family == "ai-visibility"
    assert main is not None
    assert set(main.get("class") or []) >= {
        "app-shell",
        "content-page",
        "doc-page",
        "ai-visibility-page",
        "b26-k-main",
        "b26-k-ai-visibility",
        "b26-k-reading-page",
    }
    assert "a" not in set(main.get("class") or [])


def test_transform_installs_single_canonical_shell_and_design_assets() -> None:
    rendered, _ = MODULE.transform_page(_page("content-page"), "sample.html")
    soup = BeautifulSoup(rendered, "html.parser")

    assert len(soup.select("header.ay-v2-header")) == 1
    assert len(soup.select("footer.ay-site-footer")) == 1
    assert not soup.select("header.site-header, footer.site-footer")
    assert soup.select_one('link[href*="base2026-knowledge-stitch-v1.css"]')
    assert soup.select_one('link[href*="alex-v4-static-shell.css"]')
    assert soup.select_one('script[src*="alex-v4-static-shell.js"]')


def test_apply_research_retains_route_scoped_interior_contract_after_transform() -> None:
    html = _page("app-shell content-page doc-page").replace(
        "<head>",
        '<head><link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="stylesheet" href="./static/base2026-interior-v1.css?v=stale">',
        1,
    )
    rendered, family = MODULE.transform_page(html, "apply-research.html")
    soup = BeautifulSoup(rendered, "html.parser")
    body = soup.body
    assert family == "document"
    assert body is not None
    assert {"b26-interior-v1", "b26-interior-apply"}.issubset(set(body.get("class") or []))
    assert not soup.select('link[href*="fonts.googleapis.com"], link[href*="fonts.gstatic.com"]')
    assert len(soup.select('link[href*="vendor/geist-local.css"]')) == 1
    assert len(soup.select('link[href*="base2026-interior-v1.css"]')) == 1
    stylesheets = [str(link.get("href") or "") for link in soup.select('head link[rel="stylesheet"]')]
    assert stylesheets.index(next(href for href in stylesheets if "base2026-knowledge-stitch" in href)) < stylesheets.index(next(href for href in stylesheets if "base2026-interior-v1" in href))


def test_non_apply_document_does_not_receive_interior_contract() -> None:
    rendered, _ = MODULE.transform_page(_page("app-shell content-page doc-page"), "methodology.html")
    soup = BeautifulSoup(rendered, "html.parser")
    assert "b26-interior-v1" not in set((soup.body or {}).get("class") or [])
    assert not soup.select('link[href*="base2026-interior-v1.css"]')


def test_document_composition_uses_hero_context_without_a_rail() -> None:
    legacy = _page("app-shell content-page doc-page").replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        '<div class="b26-k-document-layout"><aside class="b26-k-document-rail">Old rail</aside>'
        '<article class="b26-k-document-body"><section class="content-section"><h2>Evidence</h2><p>Body.</p></section></article></div>',
    )
    rendered, family = MODULE.transform_page(legacy, "methodology.html")
    soup = BeautifulSoup(rendered, "html.parser")

    assert family == "document"
    assert not soup.select(".b26-k-document-layout, .b26-k-document-rail")
    assert soup.select_one("main > article.b26-k-document-body")
    assert soup.select_one(".ai-pages-intro .hero-actions .b26-k-document-context[role='note']")


def test_finalize_release_metadata_rebinds_package_identity(tmp_path: Path) -> None:
    source = tmp_path / "base-release"
    output = tmp_path / "whole-corpus-preview-20260715-160000"
    source.mkdir()
    output.mkdir()
    source_manifest = {
        "schema": "base2026.public-hotfix-from-export/v4",
        "release_name": "base-release",
        "required_runtime_files": ["web/index.html"],
    }
    (source / "manifest.json").write_text(json.dumps(source_manifest), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(source_manifest), encoding="utf-8")
    whole = {
        "protected_accepted_pages": 1699,
        "transformed_legacy_pages": 2423,
        "skipped_redirect_pages": ["search.html", "search/index.html"],
        "family_counts": {"topic": 1162},
    }

    MODULE.finalize_release_metadata(source, output, whole)

    package = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert package["release_name"] == output.name
    assert package["package_mode"] == "data-preserving-static-derived-whole-corpus-stitch-v1"
    assert package["whole_corpus_stitch_v1"]["base_release_name"] == "base-release"
    assert package["whole_corpus_stitch_v1"]["transformed_legacy_pages"] == 2423
    assert "web/static/base2026-knowledge-stitch-v1.css" in package["required_runtime_files"]
    assert (output / "RELEASE.txt").read_text(encoding="utf-8").splitlines()[0] == output.name


def test_deterministic_zip_ignores_mtime(tmp_path: Path) -> None:
    source = tmp_path / "release"
    source.mkdir()
    payload = source / "payload.txt"
    payload.write_text("stable\n", encoding="utf-8")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    MODULE.write_deterministic_zip(source, first)
    payload.touch()
    MODULE.write_deterministic_zip(source, second)
    assert first.read_bytes() == second.read_bytes()


def _cards(count: int, class_name: str = "intelligence-card") -> str:
    return "".join(
        f'<article class="{class_name}"><h3>Item {index}</h3><p>Body {index}</p></article>'
        for index in range(count)
    )


def test_ai_visibility_directory_is_bounded_with_native_disclosure() -> None:
    html = _page().replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        f'<section class="content-section"><h2>Evidence</h2><div class="ai-pages-grid">{_cards(10, "ai-pages-card")}</div></section>',
    )
    rendered, _ = MODULE.transform_page(html, "ai-visibility-pages/index.html")
    soup = BeautifulSoup(rendered, "html.parser")
    grid = soup.select_one(".ai-pages-grid:not(.b26-k-disclosure-grid)")
    details = soup.select_one("details.b26-k-disclosure--ai-directory")
    assert grid is not None and len(grid.find_all(recursive=False)) == 6
    assert details is not None and len(details.select(":scope > .b26-k-disclosure-grid > .ai-pages-card")) == 4
    assert not details.has_attr("open")


def test_topic_repeated_evidence_layers_become_copy_preserving_details() -> None:
    html = _page("content-page").replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        '<section class="content-section"><h2>Public Insight Cards</h2><p>Body.</p></section>'
        '<section class="content-section"><h2>Related Source Records</h2><p>Sources.</p></section>',
    )
    rendered, _ = MODULE.transform_page(html, "topics/example.html")
    soup = BeautifulSoup(rendered, "html.parser")
    details = soup.select("main > details.b26-k-disclosure--section")
    assert len(details) == 2
    headings = [node.select_one(":scope > summary h2") for node in details]
    assert all(node is not None for node in headings)
    assert [node.get_text(strip=True) for node in headings if node is not None] == [
        "Public Insight Cards",
        "Related Source Records",
    ]
    assert all(not node.has_attr("open") for node in details)


def test_creator_and_compare_collections_have_family_limits() -> None:
    creator = _page("content-page").replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        f'<section class="content-section"><h2>Latest Source Records</h2><div class="card-grid">{_cards(9)}</div></section>',
    )
    creator_rendered, _ = MODULE.transform_page(creator, "creators/example.html")
    creator_soup = BeautifulSoup(creator_rendered, "html.parser")
    assert len(creator_soup.select(".card-grid:not(.b26-k-disclosure-grid) > .intelligence-card")) == 4
    assert len(creator_soup.select(".b26-k-disclosure--source-ledger .intelligence-card")) == 5

    compare_groups = "".join(
        '<article class="comparison-group">'
        f'<h3>Creator {group}</h3><ul>'
        + "".join(f'<li><p>Claim {group}-{item}</p></li>' for item in range(4))
        + "</ul></article>"
        for group in range(7)
    )
    compare = _page("content-page").replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        f'<section class="content-section"><h2>Viewpoints</h2><div class="comparison-grid">{compare_groups}</div></section>',
    )
    compare_rendered, _ = MODULE.transform_page(compare, "compare/example.html")
    compare_soup = BeautifulSoup(compare_rendered, "html.parser")
    assert len(compare_soup.select(".comparison-grid:not(.b26-k-disclosure-grid) > .comparison-group")) == 2
    assert len(compare_soup.select(".b26-k-disclosure--comparison > .b26-k-disclosure-grid > .comparison-group")) == 5
    assert all(
        len(group.select(":scope > ul > li")) == 2
        for group in compare_soup.select(".comparison-group")
    )
    assert len(compare_soup.select("details.b26-k-disclosure--comparison-records")) == 7
    assert all(node.name == "ul" for node in compare_soup.select(".b26-k-disclosure--comparison-records > .b26-k-disclosure-grid"))


def test_large_index_is_bounded_to_twelve_entries() -> None:
    html = _page("content-page").replace(
        '<section class="content-section"><h2>Evidence</h2><p>Body.</p></section>',
        f'<section class="content-section"><h2>Directory</h2><div class="card-grid">{_cards(15)}</div></section>',
    )
    rendered, _ = MODULE.transform_page(html, "topics/index.html")
    soup = BeautifulSoup(rendered, "html.parser")
    assert len(soup.select(".card-grid:not(.b26-k-disclosure-grid) > .intelligence-card")) == 12
    assert len(soup.select(".b26-k-disclosure--directory .intelligence-card")) == 3
