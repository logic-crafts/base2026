#!/usr/bin/env python3
"""Derive a whole-corpus Base2026 Stitch V1 preview from a verified release.

Accepted Search, Source Detail V2 and Solutions pages are byte-protected. Every
legacy HTML route is migrated to the canonical Alex V4 shell and a family-aware
semantic composition without changing its URL, metadata, robots, canonical,
JSON-LD, visible copy, or link targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import sys
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup, Tag

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from alex_v4_static_shell import (  # noqa: E402
    SHELL_VERSION,
    footer_html,
    header_html,
    shell_css,
    shell_js,
)

VERSION = "20260715-whole-corpus-stitch-v1-r4"
CSS_NAME = "base2026-knowledge-stitch-v1.css"
INTERIOR_CSS_NAME = "base2026-interior-v1.css"
INTERIOR_VERSION = "20260718-base2026-interior-v1"
DOC_NAMES = {
    "methodology.html", "roadmap.html", "story.html", "privacy.html",
    "source-policy.html", "support.html", "site-structure.html", "opt-out.html",
    "api.html", "apply-research.html", "ai-visibility-resources.html",
    "analytics.html", "search-analytics.html", "source-intelligence.html",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_deterministic_zip(source_root: Path, zip_path: Path) -> None:
    """Write stable release bytes independent of local mtimes and permissions."""
    fixed_time = (2020, 1, 1, 0, 0, 0)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            rel = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(rel, fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def finalize_release_metadata(source_root: Path, out_root: Path, manifest: dict[str, object]) -> None:
    """Bind the copied package to its new whole-corpus release identity."""
    package_path = out_root / "manifest.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    base_release_name = str(package.get("release_name") or "")
    if not base_release_name:
        raise ValueError("Source package manifest has no release_name")
    required_runtime = list(package.get("required_runtime_files") or [])
    for required in (
        "web/static/alex-v4-static-shell.css",
        "web/static/alex-v4-static-shell.js",
        f"web/static/{CSS_NAME}",
        f"web/static/{INTERIOR_CSS_NAME}",
    ):
        if required not in required_runtime:
            required_runtime.append(required)
    package["release_name"] = out_root.name
    package["package_mode"] = "data-preserving-static-derived-whole-corpus-stitch-v1"
    package["required_runtime_files"] = required_runtime
    package["whole_corpus_stitch_v1"] = {
        "version": VERSION,
        "base_release_name": base_release_name,
        "base_manifest_sha256": sha256(source_root / "manifest.json"),
        "protected_accepted_pages": manifest["protected_accepted_pages"],
        "transformed_legacy_pages": manifest["transformed_legacy_pages"],
        "skipped_redirect_pages": manifest["skipped_redirect_pages"],
        "family_counts": manifest["family_counts"],
        "corpus_reexported": False,
        "meilisearch_reindexed": False,
        "wordpress_root_mutation": False,
        "sitemap_changed": False,
    }
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    (out_root / "RELEASE.txt").write_text(
        f"{out_root.name}\nDerived from {base_release_name}\nWhole-corpus Stitch version {VERSION}\n",
        encoding="utf-8",
    )


def accepted_route(rel: str, source: str) -> bool:
    if rel == "index.html":
        return True
    if rel.startswith("solutions/"):
        return True
    if rel.startswith("sources/") and rel != "sources/index.html":
        return True
    classes = set(re.findall(r'<body[^>]*class="([^"]+)"', source)[0].split()) if re.search(r'<body[^>]*class="([^"]+)"', source) else set()
    return bool({"base2026-search-v1", "b26-source-v2"} & classes)


def family_for(rel: str, soup: BeautifulSoup) -> str:
    if rel.startswith("topics/"):
        return "topic-index" if rel == "topics/index.html" else "topic"
    if rel.startswith("compare/"):
        return "compare-index" if rel == "compare/index.html" else "compare"
    if rel.startswith("creators/"):
        return "creator-index" if rel == "creators/index.html" else "creator"
    if rel == "sources/index.html":
        return "source-index"
    if rel.startswith("ai-visibility-pages/") or soup.select_one(".ai-visibility-page"):
        return "ai-visibility"
    if Path(rel).name in DOC_NAMES or soup.select_one("main.doc-page, main.roadmap-page, main.support-page"):
        return "document"
    if rel in {"search/index.html", "search.html"}:
        return "redirect"
    return "article"


def slugify(text: str, fallback: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:80] or fallback


def class_tokens(node: Tag) -> list[str]:
    """Return a Tag's class attribute as whole tokens.

    BeautifulSoup returns a list for parsed classes, but an earlier assignment can
    leave a plain string. Calling ``list()`` on that string splits every class into
    characters, which silently broke the AI Visibility main container.
    """
    value = node.get("class") or []
    if isinstance(value, str):
        return value.split()
    return [str(item) for item in value]


def add_classes(node: Tag, *classes: str) -> None:
    node["class"] = " ".join(dict.fromkeys([*class_tokens(node), *classes]))


def add_local_nav(soup: BeautifulSoup, main: Tag, family: str) -> None:
    if family in {"redirect"} or main.select_one(".b26-k-local-nav"):
        return
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, heading in enumerate(main.select("section h2"), start=1):
        label = " ".join(heading.get_text(" ", strip=True).split())
        if not label:
            continue
        anchor = str(heading.get("id") or slugify(label, f"section-{index}"))
        while anchor in seen:
            anchor = f"{anchor}-{index}"
        seen.add(anchor)
        heading["id"] = anchor
        sections.append((label, anchor))
    if len(sections) < 2:
        return
    nav = soup.new_tag("nav", attrs={"class": "b26-k-local-nav", "aria-label": "On this page"})
    label = soup.new_tag("span", attrs={"class": "b26-k-local-nav__label"})
    label.string = "On this page"
    nav.append(label)
    for text, anchor in sections[:8]:
        link = soup.new_tag("a", href=f"#{anchor}")
        link.string = text
        nav.append(link)
    hero = main.select_one(".page-hero, .b26-money-hero, .ai-pages-intro, .b26-about-hero")
    if isinstance(hero, Tag):
        hero.insert_after(nav)
    else:
        main.insert(0, nav)


def compose_document(soup: BeautifulSoup, main: Tag) -> None:
    if main.select_one(".b26-k-document-layout"):
        return
    sections = [node for node in main.find_all("section", recursive=False) if "page-hero" not in (node.get("class") or [])]
    if not sections:
        return
    layout = soup.new_tag("div", attrs={"class": "b26-k-document-layout"})
    rail = soup.new_tag("aside", attrs={"class": "b26-k-document-rail", "aria-label": "Document context"})
    rail_label = soup.new_tag("p")
    rail_label.string = "Base2026 document"
    rail.append(rail_label)
    rail_text = soup.new_tag("p")
    rail_text.string = "Public methodology, governance and operating context."
    rail.append(rail_text)
    article = soup.new_tag("article", attrs={"class": "b26-k-document-body"})
    sections[0].insert_before(layout)
    layout.append(rail)
    layout.append(article)
    for section in sections:
        article.append(section.extract())


def direct_tag_children(node: Tag) -> list[Tag]:
    return [child for child in node.children if isinstance(child, Tag)]


def split_collection(
    soup: BeautifulSoup,
    collection: Tag,
    *,
    limit: int,
    label: str,
    disclosure_class: str,
) -> None:
    """Keep a bounded first set and preserve the rest in native disclosure."""
    children = direct_tag_children(collection)
    if len(children) <= limit or collection.find_next_sibling("details", class_="b26-k-disclosure"):
        return
    details = soup.new_tag(
        "details",
        attrs={"class": f"b26-k-disclosure {disclosure_class}"},
    )
    summary = soup.new_tag(
        "summary",
        attrs={"class": "b26-k-disclosure__summary", "data-b26-injected-text": "true"},
    )
    summary.string = label.format(count=len(children) - limit)
    details.append(summary)
    panel_name = "ul" if collection.name in {"ul", "ol"} else "div"
    panel = soup.new_tag(panel_name, attrs={"class": "b26-k-disclosure__panel b26-k-disclosure-grid"})
    add_classes(panel, *class_tokens(collection))
    details.append(panel)
    for child in children[limit:]:
        panel.append(child.extract())
    collection.insert_after(details)


def collapse_section(soup: BeautifulSoup, section: Tag) -> None:
    """Turn a repeated evidence layer into a semantic, copy-preserving details row."""
    if section.name == "details" or "b26-k-disclosure--section" in class_tokens(section):
        return
    heading_wrapper = section.select_one(":scope > .section-title-row")
    heading = heading_wrapper if isinstance(heading_wrapper, Tag) else section.select_one(":scope > h2")
    if not isinstance(heading, Tag):
        return
    section.name = "details"
    add_classes(section, "b26-k-disclosure", "b26-k-disclosure--section")
    summary = soup.new_tag(
        "summary",
        attrs={"class": "b26-k-disclosure__summary b26-k-disclosure__summary--section"},
    )
    summary.append(heading.extract())
    section.insert(0, summary)


def compose_progressive_disclosure(soup: BeautifulSoup, main: Tag, family: str) -> None:
    """Replace family-level card walls with bounded semantic compositions."""
    if family == "ai-visibility":
        for grid in main.select(".ai-pages-grid"):
            split_collection(
                soup,
                grid,
                limit=6,
                label="Show {count} more playbooks",
                disclosure_class="b26-k-disclosure--ai-directory",
            )
    elif family == "creator":
        for grid in main.select(".card-grid"):
            split_collection(
                soup,
                grid,
                limit=4,
                label="Show {count} more source records",
                disclosure_class="b26-k-disclosure--source-ledger",
            )
    elif family == "compare":
        for group in main.select(".comparison-grid > .comparison-group"):
            evidence_list = group.select_one(":scope > ul")
            if isinstance(evidence_list, Tag):
                split_collection(
                    soup,
                    evidence_list,
                    limit=2,
                    label="Show {count} more records from this creator",
                    disclosure_class="b26-k-disclosure--comparison-records",
                )
        for grid in main.select(".comparison-grid"):
            split_collection(
                soup,
                grid,
                limit=2,
                label="Show {count} more creator viewpoints",
                disclosure_class="b26-k-disclosure--comparison",
            )
    elif family.endswith("index"):
        for grid in main.select(".card-grid"):
            split_collection(
                soup,
                grid,
                limit=12,
                label="Show {count} more directory entries",
                disclosure_class="b26-k-disclosure--directory",
            )
    if family == "topic":
        collapsible = {
            "Questions this topic answers",
            "Public Insight Cards",
            "Related Source Records",
            "Evidence Passages",
        }
        for section in main.select(":scope > section.content-section"):
            heading = section.select_one("h2")
            normalized = " ".join(heading.get_text(" ", strip=True).split()) if isinstance(heading, Tag) else ""
            if normalized in collapsible:
                collapse_section(soup, section)


def tag_family_components(main: Tag, family: str) -> None:
    hero = main.select_one(".page-hero, .b26-money-hero, .ai-pages-intro")
    if isinstance(hero, Tag):
        add_classes(hero, "b26-k-hero")
    for section in main.select(".content-section"):
        add_classes(section, "b26-k-section")
    if family in {"creator", "topic", "compare", "creator-index", "topic-index", "compare-index", "source-index"}:
        for grid in main.select(".card-grid, .comparison-grid"):
            add_classes(grid, "b26-k-comparison" if "comparison-grid" in class_tokens(grid) else "b26-k-ledger")
        for card in main.select(".intelligence-card, .comparison-group"):
            add_classes(card, "b26-k-ledger-row")
    if family.endswith("index"):
        for grid in main.select(".card-grid"):
            add_classes(grid, "b26-k-directory-grid")
    if family == "ai-visibility":
        add_classes(main, "b26-k-reading-page")


def transform_page(source: str, rel: str) -> tuple[str, str]:
    # Replace the legacy global shell before parsing. The accepted canonical shell
    # is shared with Search, Source Detail V2 and Solutions.
    source, header_count = re.subn(r'<header class="site-header">.*?</header>', header_html(), source, count=1, flags=re.S)
    source, footer_count = re.subn(r'<footer class="site-footer">.*?</footer>', footer_html(), source, count=1, flags=re.S)
    soup = BeautifulSoup(source, "html.parser")
    body = soup.body
    main = soup.select_one("main")
    if not isinstance(body, Tag) or not isinstance(main, Tag):
        return source, "redirect"
    if not soup.select_one("header.ay-v2-header"):
        header_fragment = BeautifulSoup(header_html(), "html.parser").select_one("header")
        if isinstance(header_fragment, Tag):
            body.insert(0, header_fragment)
    if not soup.select_one("footer.ay-site-footer"):
        footer_fragment = BeautifulSoup(footer_html(), "html.parser").select_one("footer")
        if isinstance(footer_fragment, Tag):
            body.append(footer_fragment)
    family = family_for(rel, soup)
    body_classes = f"ay-alex-v4-static ay-stitch-home-v3 ay-stitch-home-v4 b26-knowledge-v1 b26-family-{family}"
    if rel == "apply-research.html":
        body_classes += " b26-interior-v1 b26-interior-apply"
    body["class"] = body_classes
    add_classes(main, "app-shell", "b26-k-main", f"b26-k-{family}")

    head = soup.head
    if isinstance(head, Tag):
        if not head.select_one('link[href*="alex-v4-static-shell.css"]'):
            shell_link = soup.new_tag("link", rel="stylesheet", href=f"/knowledge/static/alex-v4-static-shell.css?v={SHELL_VERSION}")
            head.append(shell_link)
        if not head.select_one(f'link[href*="{CSS_NAME}"]'):
            design_link = soup.new_tag("link", rel="stylesheet", href=f"/knowledge/static/{CSS_NAME}?v={VERSION}")
            head.append(design_link)
        if not head.select_one('script[src*="alex-v4-static-shell.js"]'):
            shell_script = soup.new_tag("script", attrs={"src": f"/knowledge/static/alex-v4-static-shell.js?v={SHELL_VERSION}", "defer": ""})
            head.append(shell_script)
        if rel == "apply-research.html":
            for external_font in head.select(
                'link[href*="fonts.googleapis.com"], link[href*="fonts.gstatic.com"]'
            ):
                external_font.decompose()
            if not head.select_one('link[href*="vendor/geist-local.css"]'):
                local_fonts = soup.new_tag(
                    "link",
                    rel="stylesheet",
                    href=f"/knowledge/static/vendor/geist-local.css?v={INTERIOR_VERSION}",
                )
                local_fonts["data-base2026-local-fonts"] = "geist-manrope"
                head.append(local_fonts)
            for stale_interior in head.select(f'link[href*="{INTERIOR_CSS_NAME}"]'):
                stale_interior.decompose()
            interior_link = soup.new_tag(
                "link",
                rel="stylesheet",
                href=f"/knowledge/static/{INTERIOR_CSS_NAME}?v={INTERIOR_VERSION}",
            )
            interior_link["data-base2026-interior"] = "v1"
            head.append(interior_link)

    tag_family_components(main, family)
    if family == "document":
        compose_document(soup, main)
    compose_progressive_disclosure(soup, main, family)
    add_local_nav(soup, main, family)
    if header_count != 1 and not soup.select_one("header.ay-v2-header"):
        raise ValueError(f"{rel}: canonical header was not installed")
    if footer_count != 1 and not soup.select_one("footer.ay-site-footer"):
        raise ValueError(f"{rel}: canonical footer was not installed")
    return str(soup), family


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source_root = args.source.resolve()
    out_root = args.out.resolve()
    web_source = source_root / "web"
    if not web_source.is_dir():
        raise FileNotFoundError(web_source)
    if out_root.exists():
        shutil.rmtree(out_root)
    shutil.copytree(source_root, out_root)
    web_out = out_root / "web"

    protected: dict[str, str] = {}
    transformed: dict[str, str] = {}
    skipped: list[str] = []
    family_counts: dict[str, int] = {}
    for source_path in sorted(web_source.rglob("*.html")):
        rel = source_path.relative_to(web_source).as_posix()
        source = source_path.read_text(encoding="utf-8")
        target = web_out / rel
        if accepted_route(rel, source):
            protected[rel] = sha256(source_path)
            continue
        rendered, family = transform_page(source, rel)
        if family == "redirect":
            skipped.append(rel)
            continue
        target.write_text(rendered, encoding="utf-8")
        transformed[rel] = sha256(target)
        family_counts[family] = family_counts.get(family, 0) + 1

    static_out = web_out / "static"
    static_out.mkdir(parents=True, exist_ok=True)
    (static_out / "alex-v4-static-shell.css").write_text(shell_css(), encoding="utf-8")
    (static_out / "alex-v4-static-shell.js").write_text(shell_js(), encoding="utf-8")
    css_source = SCRIPT_DIR / "base2026_knowledge_stitch_v1.css"
    (static_out / CSS_NAME).write_text(css_source.read_text(encoding="utf-8"), encoding="utf-8")
    interior_css_source = SCRIPT_DIR.parent / "web" / "static" / INTERIOR_CSS_NAME
    (static_out / INTERIOR_CSS_NAME).write_text(
        interior_css_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    protected_drift = []
    for rel, expected in protected.items():
        actual = sha256(web_out / rel)
        if actual != expected:
            protected_drift.append({"route": rel, "expected": expected, "actual": actual})
    if protected_drift:
        raise SystemExit("Protected accepted pages drifted: " + json.dumps(protected_drift[:5], indent=2))

    source_package = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "version": VERSION,
        "source_release_name": source_package.get("release_name"),
        "source_manifest_sha256": sha256(source_root / "manifest.json"),
        "output_release_name": out_root.name,
        "protected_accepted_pages": len(protected),
        "transformed_legacy_pages": len(transformed),
        "skipped_redirect_pages": skipped,
        "family_counts": family_counts,
        "assets": [
            "web/static/alex-v4-static-shell.css",
            "web/static/alex-v4-static-shell.js",
            f"web/static/{CSS_NAME}",
            f"web/static/{INTERIOR_CSS_NAME}",
        ],
        "protected_drift": protected_drift,
    }
    (out_root / "whole-corpus-stitch-v1-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_release_metadata(source_root, out_root, manifest)
    zip_path = out_root.with_suffix(".zip")
    write_deterministic_zip(out_root, zip_path)
    result = {
        **manifest,
        "zip_path": str(zip_path),
        "zip_sha256": sha256(zip_path),
        "file_count": sum(1 for item in out_root.rglob("*") if item.is_file()),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
