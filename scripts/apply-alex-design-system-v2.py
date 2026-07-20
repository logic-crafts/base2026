#!/usr/bin/env python3
"""Apply the shared Visual Reset V2 information architecture to a package.

Generators own page content. This bounded integration pass restores the accepted
page-local navigation, document composition and progressive disclosures after
every data-changing package build. The frozen Search root is deliberately
excluded. A route allowlist supports surgical hotfixes without reserializing an
unrelated corpus.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from alex_design_system_v2 import apply_information_architecture
from base2026_product_shell import footer_html, header_html
from base2026_ui_system import SYSTEM_VERSION


CANONICAL_FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)
LEGACY_STYLESHEET_FRAGMENT = "static/styles.css"


def family_for_legacy_route(route: str) -> str:
    if route.startswith("solutions/") or "/solutions/" in route:
        return "solutions"
    if route == "analytics.html":
        return "analytics"
    if route == "ai-visibility-resources.html":
        return "ai-visibility"
    return "general"


def _class_tokens(node: Tag) -> list[str]:
    value = node.get("class") or []
    return value.split() if isinstance(value, str) else [str(item) for item in value]


def _merge_classes(node: Tag, *classes: str) -> None:
    node["class"] = " ".join(dict.fromkeys([*_class_tokens(node), *classes]))


def apply_v2_shell(page: str, route: str) -> str:
    """Migrate a legacy static shell without touching its page-specific content.

    The historic Analytics, resource-hub and Solution exports already contain
    the reviewed content, but retained an old stylesheet/header shell. This
    narrow pass is deliberately activated only by that old stylesheet marker;
    current V2 pages and the accepted Search workspace remain byte-stable.
    """

    if LEGACY_STYLESHEET_FRAGMENT not in page:
        return page
    soup = BeautifulSoup(page, "html.parser")
    if not isinstance(soup.head, Tag) or not isinstance(soup.body, Tag):
        return page
    body = soup.body
    main = soup.select_one("main")
    if not isinstance(main, Tag):
        return page

    for legacy in soup.head.select(f'link[href*="{LEGACY_STYLESHEET_FRAGMENT}"]'):
        legacy.decompose()
    for font in soup.head.select('link[href*="fonts.googleapis.com"], link[href*="fonts.gstatic.com"]'):
        font.decompose()
    for existing in soup.head.select('link[data-alex-design-system], link[data-b26-asset], script[src*="alex-v4-static-shell.js"]'):
        existing.decompose()

    assets = [
        ('link rel="stylesheet" data-alex-design-system="v2" href="/knowledge/static/alex-design-system-v2.css?v=20260718-visual-reset-v2-r4"',),
        (f'link rel="stylesheet" data-b26-asset="tokens.css" data-b26-system-version="{SYSTEM_VERSION}" href="/knowledge/static/base2026/tokens.css?v={SYSTEM_VERSION}"',),
        (f'link rel="stylesheet" data-b26-asset="shell.css" data-b26-system-version="{SYSTEM_VERSION}" href="/knowledge/static/base2026/shell.css?v={SYSTEM_VERSION}"',),
        (f'link rel="stylesheet" data-b26-asset="components.css" data-b26-system-version="{SYSTEM_VERSION}" href="/knowledge/static/base2026/components.css?v={SYSTEM_VERSION}"',),
        ('script defer src="/knowledge/static/alex-v4-static-shell.js?v=20260718-visual-reset-v2-r4"',),
    ]
    for (fragment,) in assets:
        tag = BeautifulSoup(f"<{fragment} />", "html.parser").find()
        assert isinstance(tag, Tag)
        soup.head.append(tag)

    existing_header = soup.select_one("header")
    replacement_header = BeautifulSoup(header_html(), "html.parser").select_one("header")
    assert isinstance(replacement_header, Tag)
    if isinstance(existing_header, Tag):
        existing_header.replace_with(replacement_header)
    else:
        body.insert(0, replacement_header)

    family = family_for_legacy_route(route)
    _merge_classes(
        body,
        "ayds-root",
        "ayds-mode-editorial",
        "ay-alex-v4-static",
        "ay-stitch-home-v3",
        "ay-stitch-home-v4",
        f"b26-family-{family}",
    )
    body["data-b26-system-version"] = SYSTEM_VERSION
    body["data-b26-family"] = family
    body["data-b26-visual-root"] = "v2"
    main["data-b26-shell"] = ""
    return str(soup)


def apply_global_footer(page: str) -> str:
    """Keep every generated Base page on the accepted global footer contract."""

    rendered, replacements = CANONICAL_FOOTER_RE.subn(footer_html(), page, count=1)
    # The transformer is also deliberately usable against a narrow fragment in
    # tests and maintenance tooling. Public release pages are enforced by the
    # corpus contract below; a footer-less fragment should not become a write
    # error just because it has no site boundary to replace.
    if replacements == 0:
        return page
    return rendered


def apply_to_web_root(
    web_root: Path, *, routes: set[str] | None = None, include_search_footer: bool = False
) -> dict[str, int]:
    root = web_root.resolve()
    if not root.is_dir() or not (root / "index.html").is_file():
        raise FileNotFoundError(f"Base2026 web root is incomplete: {root}")
    scanned = 0
    changed = 0
    for page in sorted(root.rglob("*.html")):
        route = page.relative_to(root).as_posix()
        if route == "index.html":
            continue
        if routes is not None and route not in routes:
            continue
        scanned += 1
        source = page.read_text(encoding="utf-8")
        rendered = apply_global_footer(
            apply_information_architecture(apply_v2_shell(source, route), route)
        )
        if rendered != source:
            page.write_text(rendered, encoding="utf-8")
            changed += 1
    search_root_changed = 0
    if include_search_footer:
        search_root = root / "index.html"
        source = search_root.read_text(encoding="utf-8")
        rendered = apply_global_footer(apply_v2_shell(source, "index.html"))
        if rendered != source:
            search_root.write_text(rendered, encoding="utf-8")
            search_root_changed = 1

    return {"scanned": scanned, "changed": changed, "search_root_changed": search_root_changed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument(
        "--route",
        action="append",
        default=[],
        help="Apply only this root-relative HTML route; repeat for multiple routes.",
    )
    parser.add_argument(
        "--include-search-footer",
        action="store_true",
        help="Sync only the Search root footer without rewriting its frozen workspace markup.",
    )
    args = parser.parse_args()
    requested_routes = {route.lstrip("/") for route in args.route}
    result = apply_to_web_root(
        args.web_root,
        routes=requested_routes or None,
        include_search_footer=args.include_search_footer,
    )
    print(
        f"visual_reset_v2_scanned={result['scanned']} "
        f"changed={result['changed']} search_root_changed={result['search_root_changed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
