"""Versioned Base2026 UI-system contract shared by public renderers.

This module intentionally owns only asset/version and component-marker
metadata.  Public data, routes, canonical URLs, robots directives and source
admission states remain owned by their existing generators and contracts.
"""

from __future__ import annotations

from html import escape


SYSTEM_VERSION = "1.1.5"
VISUAL_VERSION = "v2"
ASSET_DIRECTORY = "base2026"
ASSET_FILES = ("tokens.css", "shell.css", "components.css", "context-nav.css")
COMPONENT_IDS = frozenset(f"B26-{number:02d}" for number in range(1, 10))


def stylesheet_href(relative_root: str, asset: str) -> str:
    """Return one release-relative Base2026 stylesheet URL."""

    if asset not in ASSET_FILES:
        raise ValueError(f"Unknown Base2026 UI asset: {asset!r}")
    root = relative_root.rstrip("/") or "."
    return f"{root}/static/{ASSET_DIRECTORY}/{asset}?v={SYSTEM_VERSION}"


def stylesheet_tags(relative_root: str) -> str:
    """Render the ordered, versioned Base2026 stylesheet contract."""

    return "\n".join(
        (
            f'    <link rel="stylesheet" href="{escape(stylesheet_href(relative_root, asset))}" '
            f'data-b26-asset="{escape(asset)}" data-b26-system-version="{SYSTEM_VERSION}" />'
        )
        for asset in ASSET_FILES
    )


def system_attributes(family: str) -> str:
    """Render stable document-level markers without touching page semantics."""

    normalized = family.strip().lower().replace("_", "-")
    if not normalized or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in normalized):
        raise ValueError(f"Invalid Base2026 family marker: {family!r}")
    return (
        f'data-b26-system-version="{SYSTEM_VERSION}" '
        f'data-b26-family="{escape(normalized)}"'
    )


def visual_root_attributes(family: str) -> str:
    """Opt one non-Search document into the reviewed B26 presentation layer."""

    return f'{system_attributes(family)} data-b26-visual-root="{VISUAL_VERSION}"'


def component_attributes(component_id: str, variant: str = "") -> str:
    """Render a validated B26 component marker for fixture and corpus QA."""

    if component_id not in COMPONENT_IDS:
        raise ValueError(f"Unknown Base2026 component id: {component_id!r}")
    attributes = [f'data-b26-component="{component_id}"']
    if variant:
        normalized = variant.strip().lower().replace("_", "-")
        if not normalized or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in normalized):
            raise ValueError(f"Invalid Base2026 component variant: {variant!r}")
        attributes.append(f'data-b26-variant="{escape(normalized)}"')
    return " ".join(attributes)


def visual_component_attributes(component_id: str, variant: str = "") -> str:
    """Opt one semantic B26 component into the reviewed presentation layer."""

    return f'{component_attributes(component_id, variant)} data-b26-visual="{VISUAL_VERSION}"'


def inject_stylesheet_contract(html: str, relative_root: str) -> str:
    """Add the shared assets once to a static/protected HTML shell."""

    present = [f'data-b26-asset="{asset}"' in html for asset in ASSET_FILES]
    if all(present):
        return html
    if any(present):
        raise ValueError("Partial Base2026 UI asset contract in HTML")
    if html.count("</head>") != 1:
        raise ValueError("Base2026 UI asset injection requires exactly one </head>")
    return html.replace("</head>", f"{stylesheet_tags(relative_root)}\n  </head>", 1)
