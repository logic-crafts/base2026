"""Canonical compact shell for Base2026 research-product routes.

The full Alex commercial footer remains owned by the personal site.  Base2026
uses these two static templates so generator families and strict Source Detail
cannot drift into separate navigation or conversion systems.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER_TEMPLATE = ROOT / "templates/shared/base2026-product-header.html"
FOOTER_TEMPLATE = ROOT / "templates/shared/base2026-product-footer.html"


def _template(path: Path) -> str:
    markup = path.read_text(encoding="utf-8").strip()
    if not markup:
        raise ValueError(f"Base2026 product-shell template is empty: {path}")
    return markup


def header_html() -> str:
    return _template(HEADER_TEMPLATE)


def footer_html() -> str:
    return _template(FOOTER_TEMPLATE)
