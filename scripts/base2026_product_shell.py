"""Canonical compact shell for Base2026 research-product routes.

Base2026 keeps its own product header, while the footer is rendered from the
same frozen global Alex template used by the search entrypoint. That makes the
footer a shared system surface rather than a second Base-only variation.
"""

from __future__ import annotations

from pathlib import Path

from alex_v4_static_shell import footer_html as global_footer_html


ROOT = Path(__file__).resolve().parents[1]
HEADER_TEMPLATE = ROOT / "templates/shared/base2026-product-header.html"


def _template(path: Path) -> str:
    markup = path.read_text(encoding="utf-8").strip()
    if not markup:
        raise ValueError(f"Base2026 product-shell template is empty: {path}")
    return markup


def header_html() -> str:
    return _template(HEADER_TEMPLATE)


def footer_html() -> str:
    return global_footer_html()
