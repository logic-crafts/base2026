"""Canonical shell composition for Base2026 research-product routes.

The Alex Home V4 header and footer are the sole site-level shell. Base2026
adds its research IA below that header as compact context navigation, rather
than shipping a second product header or a competing product footer.
"""

from __future__ import annotations

from pathlib import Path

from alex_v4_static_shell import footer_html as global_footer_html
from alex_v4_static_shell import header_html as global_header_html


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_NAV_TEMPLATE = ROOT / "templates/shared/base2026-context-nav.html"


def _template(path: Path) -> str:
    markup = path.read_text(encoding="utf-8").strip()
    if not markup:
        raise ValueError(f"Base2026 product-shell template is empty: {path}")
    return markup


def context_nav_html() -> str:
    """Render Base2026's local research IA beneath the global header."""

    return _template(CONTEXT_NAV_TEMPLATE)


def header_html() -> str:
    """Render one exact Alex Home V4 header plus Base2026 context nav."""

    return f"{global_header_html()}\n{context_nav_html()}"


def footer_html() -> str:
    """Render the one global Alex Home V4 footer."""

    return global_footer_html()
