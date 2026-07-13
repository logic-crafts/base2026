"""Strict Jinja setup for isolated Base2026 renderers."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "j2"), default_for_string=True),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
