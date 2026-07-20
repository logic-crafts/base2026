"""Shared renderer contract for Alex Personal × Base2026 public pages.

The module is intentionally small: CSS owns appearance, while generators use
this file to reference the same versioned asset and component vocabulary.  Old
domain classes remain available for data attributes and JavaScript hooks, but
they no longer select a competing legacy visual system.
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag


NON_SOURCE_DESIGN_VERSION = "20260718-visual-reset-v2-r4"
# Compatibility alias for the public generators that already import VERSION.
VERSION = NON_SOURCE_DESIGN_VERSION
ASSET_NAME = "alex-design-system-v2.css"

DOC_NAMES = {
    "methodology.html",
    "roadmap.html",
    "story.html",
    "privacy.html",
    "source-policy.html",
    "support.html",
    "site-structure.html",
    "opt-out.html",
    "api.html",
    "apply-research.html",
    "ai-visibility-resources.html",
    "analytics.html",
    "search-analytics.html",
    "source-intelligence.html",
}

CLASS_ALIASES: dict[str, tuple[str, ...]] = {
    "app-shell": ("ayds-page", "ayds-main"),
    "content-page": ("ayds-content",),
    "page-hero": ("ayds-hero",),
    "solution-hero": ("ayds-hero",),
    "content-section": ("ayds-section",),
    "eyebrow": ("ayds-eyebrow",),
    "lead": ("ayds-lead",),
    "hero-actions": ("ayds-actions",),
    "ay-actions": ("ayds-actions",),
    "solution-hero__actions": ("ayds-actions",),
    "solution-card-actions": ("ayds-actions",),
    "solution-next-action__actions": ("ayds-actions",),
    "ay-button": ("ayds-btn", "ayds-btn--primary"),
    "ay-button-secondary": ("ayds-btn", "ayds-btn--secondary"),
    "button-link": ("ayds-btn", "ayds-btn--small"),
    "site-header__cta": ("ayds-btn", "ayds-btn--primary"),
    "site-header__mobile-cta": ("ayds-btn", "ayds-btn--primary"),
    "card-grid": ("ayds-grid",),
    "solution-hub-grid": ("ayds-grid",),
    "solution-evidence-grid": ("ayds-grid",),
    "topic-stat-grid": ("ayds-grid",),
    "analytics-stat-grid": ("ayds-grid",),
    "intelligence-card": ("ayds-card", "ayds-card--data"),
    "passage-card": ("ayds-card", "ayds-card--data"),
    "comparison-group": ("ayds-card", "ayds-card--data"),
    "analytics-stat": ("ayds-card", "ayds-card--data"),
    "solution-hub-card": ("ayds-card", "ayds-card--feature"),
    "solution-evidence-row": ("ayds-card", "ayds-card--data"),
    "solution-completion-card": ("ayds-card", "ayds-card--feature"),
    "solution-measurement-card": ("ayds-card", "ayds-card--feature"),
    "solution-verdict": ("ayds-card", "ayds-card--dark"),
    "topic-chip": ("ayds-chip",),
    "info-hint": ("ayds-chip",),
    "breadcrumbs": ("ayds-breadcrumbs",),
    "base-contact-section": ("ayds-contact",),
    "base-contact-form": ("ayds-form",),
    "cookie-banner": ("ayds-card", "ayds-card--feature"),
    "cookie-dialog": ("ayds-card", "ayds-card--feature"),
    "site-header": ("ayds-header",),
    "site-footer": ("ayds-footer",),
}


def apply_component_classes(markup: str) -> str:
    """Attach shared component classes while preserving domain-specific ones."""

    def augment(match: re.Match[str]) -> str:
        classes = match.group(1).split()
        expanded = list(classes)
        for class_name in classes:
            for alias in CLASS_ALIASES.get(class_name, ()):
                if alias not in expanded:
                    expanded.append(alias)
        return f'class="{" ".join(expanded)}"'

    return re.sub(r'class="([^"]*)"', augment, markup)


def stylesheet_href(relative_root: str) -> str:
    root = relative_root.rstrip("/") or "."
    return f"{root}/static/{ASSET_NAME}?v={VERSION}"


def _class_tokens(node: Tag) -> list[str]:
    value = node.get("class") or []
    return value.split() if isinstance(value, str) else [str(item) for item in value]


def _add_classes(node: Tag, *classes: str) -> None:
    node["class"] = " ".join(dict.fromkeys([*_class_tokens(node), *classes]))


def _slugify(text: str, fallback: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:80] or fallback


def _family_for(route: str, soup: BeautifulSoup) -> str:
    if route.startswith("topics/"):
        return "topic-index" if route == "topics/index.html" else "topic"
    if route.startswith("compare/"):
        return "compare-index" if route == "compare/index.html" else "compare"
    if route.startswith("creators/"):
        return "creator-index" if route == "creators/index.html" else "creator"
    if route == "sources/index.html":
        return "source-index"
    if route.startswith("ai-visibility-pages/") or soup.select_one(".ai-visibility-page"):
        return "ai-visibility"
    if Path(route).name in DOC_NAMES or soup.select_one("main.doc-page, main.roadmap-page, main.support-page"):
        return "document"
    return "article"


def _add_local_nav(soup: BeautifulSoup, main: Tag) -> None:
    if main.select_one(".b26-k-local-nav"):
        return
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()
    headings: list[Tag] = []
    for section in main.find_all(["section", "details"], recursive=False):
        heading = section.select_one(
            ":scope > h2, :scope > .section-title-row h2, :scope > summary h2"
        )
        if isinstance(heading, Tag):
            headings.append(heading)
    for index, heading in enumerate(headings, start=1):
        label = " ".join(heading.get_text(" ", strip=True).split())
        if not label:
            continue
        anchor = str(heading.get("id") or _slugify(label, f"section-{index}"))
        while anchor in seen:
            anchor = f"{anchor}-{index}"
        seen.add(anchor)
        heading["id"] = anchor
        sections.append((label, anchor))
    if len(sections) < 2:
        return
    nav = soup.new_tag(
        "nav",
        attrs={"class": "b26-k-local-nav ayds-local-nav", "aria-label": "On this page"},
    )
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


def _compose_document(soup: BeautifulSoup, main: Tag, route: str) -> None:
    # Roadmap is an interactive six-phase map. A document rail steals the
    # horizontal space that makes both its controls and sequence readable.
    if Path(route).name == "roadmap.html":
        return
    if main.select_one(".b26-k-document-layout"):
        return
    sections = [
        node
        for node in main.find_all("section", recursive=False)
        if "page-hero" not in _class_tokens(node)
    ]
    if not sections:
        return
    layout = soup.new_tag(
        "div", attrs={"class": "b26-k-document-layout ayds-document-layout"}
    )
    rail = soup.new_tag(
        "aside",
        attrs={
            "class": "b26-k-document-rail ayds-document-rail ayds-card ayds-card--data",
            "aria-label": "Document context",
        },
    )
    rail_label = soup.new_tag("p", attrs={"class": "ayds-eyebrow"})
    rail_label.string = "Base2026 document"
    rail.append(rail_label)
    rail_text = soup.new_tag("p")
    rail_text.string = "Public methodology, governance and operating context."
    rail.append(rail_text)
    article = soup.new_tag(
        "article", attrs={"class": "b26-k-document-body ayds-document-body"}
    )
    sections[0].insert_before(layout)
    layout.append(rail)
    layout.append(article)
    for section in sections:
        article.append(section.extract())


def _direct_tag_children(node: Tag) -> list[Tag]:
    return [child for child in node.children if isinstance(child, Tag)]


def _split_collection(
    soup: BeautifulSoup,
    collection: Tag,
    *,
    limit: int,
    label: str,
    disclosure_class: str,
) -> None:
    children = _direct_tag_children(collection)
    if len(children) <= limit or collection.find_next_sibling("details", class_="b26-k-disclosure"):
        return
    details = soup.new_tag(
        "details",
        attrs={"class": f"b26-k-disclosure ayds-disclosure {disclosure_class}"},
    )
    summary = soup.new_tag(
        "summary",
        attrs={
            "class": "b26-k-disclosure__summary ayds-disclosure__summary",
            "data-b26-injected-text": "true",
        },
    )
    summary.string = label.format(count=len(children) - limit)
    details.append(summary)
    panel_name = "ul" if collection.name in {"ul", "ol"} else "div"
    panel = soup.new_tag(
        panel_name,
        attrs={"class": "b26-k-disclosure__panel b26-k-disclosure-grid ayds-disclosure__panel"},
    )
    _add_classes(panel, *_class_tokens(collection))
    details.append(panel)
    for child in children[limit:]:
        panel.append(child.extract())
    collection.insert_after(details)


def _collapse_section(
    soup: BeautifulSoup, section: Tag, *, wrap_panel: bool = False
) -> None:
    if section.name == "details" or "b26-k-disclosure--section" in _class_tokens(section):
        return
    heading_wrapper = section.select_one(":scope > .section-title-row")
    heading = heading_wrapper if isinstance(heading_wrapper, Tag) else section.select_one(":scope > h2")
    if not isinstance(heading, Tag):
        return
    section.name = "details"
    _add_classes(section, "b26-k-disclosure", "ayds-disclosure", "b26-k-disclosure--section")
    summary = soup.new_tag(
        "summary",
        attrs={"class": "b26-k-disclosure__summary ayds-disclosure__summary b26-k-disclosure__summary--section"},
    )
    summary.append(heading.extract())
    section.insert(0, summary)
    if wrap_panel:
        _ensure_disclosure_panel(soup, section)


def _ensure_disclosure_panel(soup: BeautifulSoup, disclosure: Tag) -> None:
    """Give section disclosures one bounded content surface.

    Older Visual Reset packages converted a ``content-section`` directly to a
    ``details`` element.  The closed control then kept the full marketing
    section padding and looked like an empty 300px card.  Wrapping everything
    after ``summary`` makes the collapsed and expanded states independently
    styleable and also repairs already-derived preview packages idempotently.
    """

    if disclosure.select_one(":scope > .b26-k-disclosure__panel"):
        return
    summary = disclosure.select_one(":scope > summary")
    if not isinstance(summary, Tag):
        return
    panel = soup.new_tag(
        "div",
        attrs={
            "class": (
                "b26-k-disclosure__panel b26-k-disclosure__panel--section "
                "ayds-disclosure__panel"
            )
        },
    )
    for child in list(disclosure.contents):
        if child is summary:
            continue
        panel.append(child.extract())
    disclosure.append(panel)


def _compose_progressive_disclosure(soup: BeautifulSoup, main: Tag, family: str) -> None:
    if family == "ai-visibility":
        for grid in main.select(".ai-pages-grid"):
            _split_collection(
                soup,
                grid,
                limit=6,
                label="Show {count} more playbooks",
                disclosure_class="b26-k-disclosure--ai-directory",
            )
    elif family == "creator":
        for grid in main.select(".card-grid"):
            _split_collection(
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
                _split_collection(
                    soup,
                    evidence_list,
                    limit=2,
                    label="Show {count} more records from this creator",
                    disclosure_class="b26-k-disclosure--comparison-records",
                )
        for grid in main.select(".comparison-grid"):
            _split_collection(
                soup,
                grid,
                limit=2,
                label="Show {count} more creator viewpoints",
                disclosure_class="b26-k-disclosure--comparison",
            )
    elif family.endswith("index"):
        for grid in main.select(".card-grid"):
            _split_collection(
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
            normalized = (
                " ".join(heading.get_text(" ", strip=True).split())
                if isinstance(heading, Tag)
                else ""
            )
            if normalized in collapsible:
                _collapse_section(soup, section, wrap_panel=family == "topic")
        if family == "topic":
            for disclosure in main.select(
                ":scope > details.b26-k-disclosure--section"
            ):
                _ensure_disclosure_panel(soup, disclosure)


def apply_information_architecture(markup: str, route: str) -> str:
    """Restore the accepted TOC, document composition and disclosures without legacy CSS.

    The accepted Phase 5 package added these semantic controls after generation.
    Visual Reset V2 keeps them as first-class shared components so regeneration
    cannot silently drop navigation or visible evidence labels.
    """

    if route in {"index.html", "search.html", "search/index.html"}:
        return apply_component_classes(markup)
    if route.startswith("solutions/") or (
        route.startswith("sources/") and route != "sources/index.html"
    ):
        return apply_component_classes(markup)
    soup = BeautifulSoup(markup, "html.parser")
    main = soup.select_one("main")
    if not isinstance(main, Tag):
        return apply_component_classes(markup)
    family = _family_for(route, soup)
    if family in {"topic", "topic-index", "compare", "compare-index"}:
        _add_classes(main, f"b26-k-family-{family}")
    if family == "document":
        _compose_document(soup, main, route)
    if family in {"topic", "topic-index"}:
        _add_local_nav(soup, main)
        _compose_progressive_disclosure(soup, main, family)
    else:
        _compose_progressive_disclosure(soup, main, family)
        _add_local_nav(soup, main)
    return apply_component_classes(str(soup))
