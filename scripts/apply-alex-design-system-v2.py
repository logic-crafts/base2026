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

from alex_design_system_v2 import apply_information_architecture
from base2026_product_shell import footer_html


CANONICAL_FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)


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
        rendered = apply_global_footer(apply_information_architecture(source, route))
        if rendered != source:
            page.write_text(rendered, encoding="utf-8")
            changed += 1
    search_root_changed = 0
    if include_search_footer:
        search_root = root / "index.html"
        source = search_root.read_text(encoding="utf-8")
        rendered = apply_global_footer(source)
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
        f"changed={result['changed']} search_root_changed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
