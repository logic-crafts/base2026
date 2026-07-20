#!/usr/bin/env python3
"""Build an isolated Base2026 shell-unification preview.

This pass is intentionally presentation-only.  It copies an existing static
tree, replaces site boundaries with the shared Alex Home V4 shell plus the
Base2026 context nav, and leaves all page body/content/metadata untouched.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

from base2026_product_shell import footer_html, header_html
from base2026_ui_system import ASSET_FILES, inject_stylesheet_contract


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ASSET_ROOT = ROOT / "web" / "static" / "base2026"
HEADER_RE = re.compile(r"<header\b[^>]*>.*?</header>", re.IGNORECASE | re.DOTALL)
FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r"(<body\b[^>]*>)", re.IGNORECASE)
BODY_CLOSE_RE = re.compile(r"</body>", re.IGNORECASE)
REDIRECT_RE = re.compile(r"<meta\b(?=[^>]*\bhttp-equiv=[\"']refresh[\"'])[^>]*>", re.IGNORECASE)
NOINDEX_RE = re.compile(r"<meta\b(?=[^>]*\bname=[\"'](?:robots|googlebot|bingbot)[\"'])[^>]*\bcontent=[\"'][^\"']*\bnoindex\b[^\"']*[\"'][^>]*>", re.IGNORECASE)
BASE_ASSET_LINK_RE = re.compile(
    r"\s*<link\b(?=[^>]*\b(?:data-b26-asset=[\"'](?:tokens|shell|components|context-nav)\.css[\"']|"
    r"(?:href|src)=[\"'][^\"']*/static/base2026/(?:tokens|shell|components|context-nav)\.css(?:\?[^\"']*)?[\"']))[^>]*>",
    re.IGNORECASE,
)


def is_redirect_shell(markup: str) -> bool:
    """Keep intentionally bare noindex redirect documents bare."""

    return bool(REDIRECT_RE.search(markup) and NOINDEX_RE.search(markup))


def normalize_base_asset_contract(markup: str, *, relative_root: str) -> str:
    """Replace only known Base CSS links with the complete current contract.

    Historic pages can carry zero, partial, duplicated, or older-version Base
    asset tags.  Removing just those known links before injection is safer than
    weakening the shared asset validator and leaves page-specific CSS intact.
    """

    without_base_assets = BASE_ASSET_LINK_RE.sub("\n", markup)
    rendered = inject_stylesheet_contract(without_base_assets, relative_root)
    for asset in ASSET_FILES:
        if rendered.count(f'data-b26-asset="{asset}"') != 1:
            raise ValueError(f"Preview page must contain one normalized Base asset: {asset}")
    return rendered


def render_page(markup: str, *, relative_root: str) -> str:
    """Replace only page boundaries and add the shared asset contract once."""

    rendered, header_count = HEADER_RE.subn(header_html(), markup, count=1)
    if header_count == 0:
        rendered, body_count = BODY_RE.subn(lambda match: f"{match.group(1)}\n{header_html()}", rendered, count=1)
        if body_count != 1:
            raise ValueError("Preview page has no usable body for global header insertion")

    rendered, footer_count = FOOTER_RE.subn(footer_html(), rendered, count=1)
    if footer_count == 0:
        rendered, body_close_count = BODY_CLOSE_RE.subn(lambda _match: f"{footer_html()}\n</body>", rendered, count=1)
        if body_close_count != 1:
            raise ValueError("Preview page has no usable body for global footer insertion")

    rendered = normalize_base_asset_contract(rendered, relative_root=relative_root)
    if rendered.count('data-ay-v2-header') != 1:
        raise ValueError("Preview page must contain exactly one global header")
    if rendered.count('data-b26-context-nav') != 1:
        raise ValueError("Preview page must contain exactly one Base2026 context nav")
    if rendered.count('data-footer-contract="personal-v1"') != 1:
        raise ValueError("Preview page must contain exactly one global footer")
    return rendered


def build_preview(source_root: Path, out_root: Path) -> dict[str, object]:
    """Copy a source tree and render all non-redirect pages into a preview."""

    source = source_root.resolve()
    output = out_root.resolve()
    if not source.is_dir() or not (source / "index.html").is_file():
        raise FileNotFoundError(f"Source web root is incomplete: {source}")
    if output.exists():
        raise FileExistsError(f"Preview destination already exists: {output}")
    missing_assets = [asset for asset in ASSET_FILES if not (SYSTEM_ASSET_ROOT / asset).is_file()]
    if missing_assets:
        raise FileNotFoundError(f"Missing preview system assets: {', '.join(missing_assets)}")

    shutil.copytree(source, output)
    asset_target_root = output / "static" / "base2026"
    asset_target_root.mkdir(parents=True, exist_ok=True)
    # The HTML contract and its CSS ship as one unit. Do not inject the
    # current shell markup while retaining archived release CSS.
    for asset in ASSET_FILES:
        shutil.copy2(SYSTEM_ASSET_ROOT / asset, asset_target_root / asset)
    rendered_routes: list[str] = []
    redirect_shells: list[str] = []
    for page in sorted(output.rglob("*.html")):
        route = page.relative_to(output).as_posix()
        source_markup = page.read_text(encoding="utf-8")
        if is_redirect_shell(source_markup):
            redirect_shells.append(route)
            continue
        relative_root = os.path.relpath(output, page.parent).replace("\\", "/")
        page.write_text(render_page(source_markup, relative_root=relative_root), encoding="utf-8")
        rendered_routes.append(route)

    receipt = {
        "schema": "base2026.shell-unification-preview/v1",
        "source_root": "web/static",
        "rendered_routes": rendered_routes,
        "redirect_shells_preserved": redirect_shells,
    }
    (output / "shell-unification-preview.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_preview(args.source_root, args.out)
    print(
        f"shell_preview_rendered={len(receipt['rendered_routes'])} "
        f"redirect_shells_preserved={len(receipt['redirect_shells_preserved'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
