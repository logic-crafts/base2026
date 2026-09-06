#!/usr/bin/env python3
"""Render the public topic index as a progressively enhanced discovery view.

The canonical topic builder still owns topic data and the surrounding document
shell.  This module only reads the already rendered ``topics/index.html`` and
replaces its ``main`` content.  It deliberately fails closed: if the expected
topic cards cannot be read without guessing, the input document is returned
unchanged.
"""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import posixpath
import re
from typing import Iterable, NamedTuple
from urllib.parse import urlsplit


_MAIN_OPEN_RE = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
_MAIN_CLOSE_RE = re.compile(r"</main\s*>", re.IGNORECASE)
_COUNT_RE = re.compile(
    r"^(?P<insights>[0-9][0-9,]*)\s+public\s+insights?\s*·\s*"
    r"(?P<sources>[0-9][0-9,]*)\s+sources?$",
    re.IGNORECASE,
)
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TopicRecord(NamedTuple):
    """The safe, already published fields needed by the discovery UI."""

    title: str
    display_title: str
    description: str
    route: str
    insight_count: int
    source_count: int
    count_label: str
    order: int


class _Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: Iterable[tuple[str, str | None]] = ()) -> None:
        self.tag = tag
        self.attrs = dict(attrs)
        self.children: list[_Node | str] = []

    def has_class(self, value: str) -> bool:
        return value in (self.attrs.get("class") or "").split()

    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text() for child in self.children)

    def walk(self) -> Iterable[_Node]:
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()


class _DocumentParser(HTMLParser):
    _VOID = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document")
        self.stack = [self.root]
        try:
            self.feed(source)
            self.close()
        except Exception:
            # ``HTMLParser`` is intentionally forgiving.  A parser failure is
            # still a fail-closed source failure for the render helper.
            self.failed = True
        else:
            self.failed = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), attrs)
        self.stack[-1].children.append(node)
        if tag.lower() not in self._VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(_Node(tag.lower(), attrs))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _descendants(node: _Node, *, tag: str = "", class_name: str = "") -> list[_Node]:
    return [
        candidate
        for candidate in node.walk()
        if (not tag or candidate.tag == tag)
        and (not class_name or candidate.has_class(class_name))
    ]


def _canonical_route(raw_href: str) -> str | None:
    """Accept only a topic detail path and canonicalise a safe relative href."""

    href = (raw_href or "").strip()
    if not href:
        return None
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None

    path = parsed.path
    if path.startswith("/topics/"):
        candidate = posixpath.normpath(path)
    else:
        # The generated index historically links to ``slug``.  Resolve that
        # existing relative route against the index's /topics/ directory.
        candidate = posixpath.normpath(posixpath.join("/topics/", path))
    if not candidate.startswith("/topics/"):
        return None
    slug = candidate.removeprefix("/topics/")
    if not _SLUG_RE.fullmatch(slug):
        return None
    return f"/topics/{slug}"


def _topic_record(article: _Node, order: int) -> TopicRecord | None:
    headings = _descendants(article, tag="h3")
    meta_nodes = [node for node in _descendants(article, tag="p") if node.has_class("meta")]
    descriptions = [node for node in _descendants(article, tag="p") if not node.has_class("meta")]
    links = [node for node in _descendants(article, tag="a") if node.has_class("button-link")]
    if len(headings) != 1 or len(meta_nodes) != 1 or len(descriptions) != 1 or len(links) != 1:
        return None

    title = _normalise_text(headings[0].text())
    description = _normalise_text(descriptions[0].text())
    count_label = _normalise_text(meta_nodes[0].text())
    route = _canonical_route(links[0].attrs.get("href") or "")
    count_match = _COUNT_RE.fullmatch(count_label)
    if not title or not description or not route or not count_match:
        return None

    insight_count = int(count_match.group("insights").replace(",", ""))
    source_count = int(count_match.group("sources").replace(",", ""))
    if insight_count < 0 or source_count < 0:
        return None
    return TopicRecord(
        title=title,
        # Only a display aid.  The original title remains the search value.
        display_title=title.replace("-", " "),
        description=description,
        route=route,
        insight_count=insight_count,
        source_count=source_count,
        count_label=count_label,
        order=order,
    )


def extract_topic_records(index_html: str) -> list[TopicRecord] | None:
    """Extract every original topic card, or ``None`` when it is unsafe."""

    if not isinstance(index_html, str) or not index_html.strip():
        return None
    parser = _DocumentParser(index_html)
    if parser.failed:
        return None
    mains = _descendants(parser.root, tag="main")
    if len(mains) != 1:
        return None
    cards = _descendants(mains[0], tag="article", class_name="intelligence-card")
    if not cards:
        return None

    records: list[TopicRecord] = []
    seen_routes: set[str] = set()
    for order, card in enumerate(cards):
        record = _topic_record(card, order)
        if record is None or record.route in seen_routes:
            return None
        seen_routes.add(record.route)
        records.append(record)
    return records


def _attr(value: str) -> str:
    return escape(value, quote=True)


def _topic_card(record: TopicRecord) -> str:
    return (
        f'<article class="b26-topic-card" data-topic-card="" '
        f'data-topic-title="{_attr(record.title)}" '
        f'data-topic-display-title="{_attr(record.display_title)}" '
        f'data-topic-description="{_attr(record.description)}" '
        f'data-topic-route="{_attr(record.route)}" '
        f'data-topic-insights="{record.insight_count}" '
        f'data-topic-sources="{record.source_count}" '
        f'data-topic-count-label="{_attr(record.count_label)}">'
        f'<a class="b26-topic-card__link" href="{_attr(record.route)}">'
        f'<span class="b26-topic-card__kicker">Topic</span>'
        f'<h3 class="b26-topic-card__title">{escape(record.display_title)}</h3>'
        f'<p class="b26-topic-card__meta">{escape(record.count_label)}</p>'
        f'<p class="b26-topic-card__description">{escape(record.description)}</p>'
        '<span class="b26-topic-card__action">Open topic <span aria-hidden="true">↗</span></span>'
        "</a></article>"
    )


def _collection_card(record: TopicRecord) -> str:
    return (
        f'<a class="b26-topic-collection" href="{_attr(record.route)}">'
        '<span class="b26-topic-collection__eyebrow">Start here</span>'
        f'<h3>{escape(record.display_title)}</h3>'
        f'<p>{escape(record.count_label)}</p>'
        '<span class="b26-topic-collection__action">Explore collection <span aria-hidden="true">↗</span></span>'
        "</a>"
    )


def _render_inner(records: list[TopicRecord]) -> str:
    collections = sorted(
        records,
        key=lambda record: (-record.source_count, -record.insight_count, record.order),
    )[:6]
    cards = "\n".join(_topic_card(record) for record in records)
    collection_cards = "\n".join(_collection_card(record) for record in collections)
    total = len(records)
    return f'''\n      <div class="b26-topic-discovery" data-b26-topic-discovery data-topic-page-size="24">\n        <section class="b26-topic-discovery__hero" aria-labelledby="b26-topic-discovery-title">\n          <div>\n            <p class="b26-topic-discovery__eyebrow">Topic index</p>\n            <h1 id="b26-topic-discovery-title">Explore the topics</h1>\n          </div>\n          <p class="b26-topic-discovery__lede">Browse the public evidence by the questions and working areas already present in Base2026.</p>\n        </section>\n\n        <div class="b26-topic-discovery__controls" data-topic-controls hidden>\n          <div class="b26-topic-discovery__field b26-topic-discovery__field--search">\n            <label for="b26-topic-search">Search topics</label>\n            <input id="b26-topic-search" data-topic-search type="search" autocomplete="off" spellcheck="false" placeholder="Search by topic title or description" />\n          </div>\n          <div class="b26-topic-discovery__field">\n            <label for="b26-topic-sort">Sort topics</label>\n            <select id="b26-topic-sort" data-topic-sort>\n              <option value="sources">Most sources</option>\n              <option value="az">A–Z</option>\n            </select>\n          </div>\n          <div class="b26-topic-discovery__field">\n            <label for="b26-topic-coverage">Source coverage</label>\n            <select id="b26-topic-coverage" data-topic-coverage>\n              <option value="all">All coverage</option>\n              <option value="multiple">Multiple sources</option>\n              <option value="single">Single source</option>\n            </select>\n          </div>\n          <button class="b26-topic-discovery__clear" type="button" data-topic-clear hidden>Clear filters</button>\n        </div>\n\n        <section class="b26-topic-discovery__collections" aria-labelledby="b26-topic-collections-title">\n          <div class="b26-topic-discovery__section-head">\n            <p class="b26-topic-discovery__eyebrow">Start with a collection</p>\n            <h2 id="b26-topic-collections-title">The broadest existing topic records</h2>\n            <p>Each collection keeps its published title, source coverage and public insight count.</p>\n          </div>\n          <div class="b26-topic-collection-grid">\n            {collection_cards}\n          </div>\n        </section>\n\n        <section class="b26-topic-discovery__directory" aria-labelledby="b26-topic-directory-title">\n          <div class="b26-topic-discovery__directory-head">\n            <div>\n              <p class="b26-topic-discovery__eyebrow">Full index</p>\n              <h2 id="b26-topic-directory-title">All topics</h2>\n              <p class="b26-topic-discovery__directory-intro">Search every indexed topic, sort by source coverage or browse the complete list without JavaScript.</p>\n            </div>\n            <p class="b26-topic-discovery__count" data-topic-count aria-live="polite">Showing 1–{total} of {total} topics</p>\n          </div>\n\n          <div class="b26-topic-discovery__results" data-topic-results role="list">\n            {cards}\n          </div>\n          <div class="b26-topic-discovery__empty" data-topic-empty hidden>\n            <p data-topic-empty-copy>No topics match these filters.</p>\n            <button class="b26-topic-discovery__clear b26-topic-discovery__clear--empty" type="button" data-topic-empty-clear>Clear search and filters</button>\n          </div>\n          <nav class="b26-topic-discovery__pagination" data-topic-pagination aria-label="Topic pages" hidden>\n            <button class="b26-topic-discovery__page-button" type="button" data-topic-previous>Previous</button>\n            <span class="b26-topic-discovery__page-label" data-topic-page-label aria-live="polite">Page 1</span>\n            <button class="b26-topic-discovery__page-button" type="button" data-topic-next>Next</button>\n          </nav>\n        </section>\n      </div>\n'''


def _apply_review_copy(inner: str) -> str:
    """Apply the compact approved labels after assembling the static markup."""

    replacements = (
        ("The broadest existing topic records", "Start with more sources"),
        (
            "Each collection keeps its published title, source coverage and public insight count.",
            "Explore the topics with the widest source coverage.",
        ),
        (
            "Search every indexed topic, sort by source coverage or browse the complete list without JavaScript.",
            "Find a working area or narrow your research by source coverage.",
        ),
        (
            '<h2 id="b26-topic-directory-title">',
            '<h2 id="b26-topic-directory-title" tabindex="-1">',
        ),
        (
            '<input id="b26-topic-search" data-topic-search type="search"',
            '<input id="b26-topic-search" data-topic-search type="search" maxlength="160"',
        ),
    )
    for before, after in replacements:
        inner = inner.replace(before, after)
    return inner


def render_topic_discovery(index_html: str) -> str:
    """Replace only the topic index main content and preserve the document shell.

    The helper returns the input byte-for-byte when the expected source shape
    is absent, a topic record is malformed, or the document has multiple main
    elements.  Generated markup carries a marker, making the operation exactly
    idempotent when a builder invokes it more than once.
    """

    if not isinstance(index_html, str) or not index_html.strip():
        return index_html
    if "data-b26-topic-discovery" in index_html:
        return index_html
    records = extract_topic_records(index_html)
    if not records:
        return index_html
    openings = list(_MAIN_OPEN_RE.finditer(index_html))
    closings = list(_MAIN_CLOSE_RE.finditer(index_html))
    if len(openings) != 1 or len(closings) != 1 or closings[0].start() < openings[0].end():
        return index_html
    opening = openings[0]
    closing = closings[0]
    inner = _apply_review_copy(_render_inner(records))
    return index_html[: opening.end()] + inner + index_html[closing.start() :]


__all__ = ["TopicRecord", "extract_topic_records", "render_topic_discovery"]
