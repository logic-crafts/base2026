from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "templates" / "base2026-startup-homepage.html"
STYLESHEET = ROOT / "templates" / "base2026-startup-homepage.css"
HEADER = ROOT / "templates" / "base2026-startup-header.html"
FOOTER = ROOT / "templates" / "base2026-startup-footer.html"


class _Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]] | None = None) -> None:
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children: list[_Node | str] = []

    def has_class(self, name: str) -> bool:
        return name in (self.attrs.get("class") or "").split()

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()

    def element_children(self) -> list[_Node]:
        return [child for child in self.children if isinstance(child, _Node)]

    def raw_text(self) -> str:
        return "".join(child if isinstance(child, str) else child.raw_text() for child in self.children)

    def direct_text(self) -> str:
        return "".join(child for child in self.children if isinstance(child, str))


class _DocumentParser(HTMLParser):
    _VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), attrs)
        self._stack[-1].children.append(node)
        if tag.lower() not in self._VOID_ELEMENTS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._stack[-1].children.append(_Node(tag.lower(), attrs))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def _parse_homepage() -> tuple[str, _Node]:
    source = HOMEPAGE.read_text(encoding="utf-8")
    parser = _DocumentParser()
    parser.feed(source)
    parser.close()
    return source, parser.root


def _normalize(value: str) -> str:
    return " ".join(unescape(value).split())


def _nodes_with_class(root: _Node, class_name: str) -> list[_Node]:
    return [node for node in root.walk() if node.has_class(class_name)]


def _nodes_with_attr(root: _Node, attr: str, value: str | None = None) -> list[_Node]:
    return [
        node for node in root.walk()
        if attr in node.attrs and (value is None or node.attrs.get(attr) == value)
    ]


def _nodes_with_tag(root: _Node, tag: str) -> list[_Node]:
    return [node for node in root.walk() if node.tag == tag]


def _metric_cells(root: _Node) -> list[_Node]:
    grids = _nodes_with_class(root, "b26-proof-grid")
    assert len(grids) == 1, "the homepage should expose one public metric grid"
    cells = [child for child in grids[0].element_children() if child.tag == "div"]
    assert len(cells) == 4, "the four public metrics should remain separate cells"
    return cells


def _visible_text_parts(node: _Node) -> list[str]:
    parts: list[str] = []
    for child in node.walk():
        if child is node or child.tag in {"script", "style", "template"}:
            continue
        if "hidden" in child.attrs:
            continue
        if (child.attrs.get("aria-hidden") or "").lower() == "true":
            continue
        if "display:none" in (child.attrs.get("style") or "").replace(" ", "").lower():
            continue
        text = _normalize(child.direct_text())
        if text:
            parts.append(text)
    return parts


def _css_rules(css: str) -> list[tuple[str, str]]:
    return [(selector.strip(), body) for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]


def test_homepage_metrics_are_unavailable_until_the_public_read_succeeds() -> None:
    _, document = _parse_homepage()
    cells = _metric_cells(document)
    expected_keys = (
        "documents_indexed",
        "distinct_sources",
        "public_evidence_routes",
        "full_transcripts_published",
    )

    for cell, key in zip(cells, expected_keys):
        stat_nodes = _nodes_with_attr(cell, "data-b26-public-stat", key)
        assert len(stat_nodes) == 1
        initial_value = _normalize(stat_nodes[0].raw_text())
        assert initial_value == "Unavailable" or (key == "full_transcripts_published" and initial_value == "0")
        assert len(_visible_text_parts(cell)) >= 3, f"{key} needs a label and visible explanation"

    keys = [
        _nodes_with_attr(cell, "data-b26-public-stat")[0].attrs["data-b26-public-stat"]
        for cell in cells
    ]
    assert keys == list(expected_keys)
    assert "sitemap" in _normalize(cells[2].raw_text()).lower()
    assert "private pipeline" not in _normalize(" ".join(cell.raw_text() for cell in cells)).lower()

    transcript_copy = _normalize(cells[3].raw_text()).lower()
    assert "full third-party transcripts stay private" in transcript_copy
    assert "reviewed excerpts and attributed records are public" in transcript_copy

    status_nodes = _nodes_with_attr(document, "data-b26-stats-status")
    assert len(status_nodes) == 1
    assert "unavailable" in _normalize(status_nodes[0].raw_text()).lower()

    runtime = (ROOT / "templates" / "base2026-evidence-brief.js").read_text(encoding="utf-8")
    assert 'fetch("/api/stats"' in runtime
    assert "Number.isSafeInteger" in runtime


def test_homepage_preserves_search_result_and_public_read_contracts() -> None:
    source, document = _parse_homepage()

    titles = _nodes_with_tag(document, "title")
    assert len(titles) == 1
    assert _normalize(titles[0].raw_text()).startswith("Base2026")
    assert '<link rel="canonical" href="https://base2026.dev/">' in source
    assert 'type="application/ld+json"' in source
    assert "/static/base2026-evidence-brief.js" in source

    forms = _nodes_with_class(document, "b26-brief-search")
    assert len(forms) == 1
    form = forms[0]
    assert form.attrs.get("action") == "/workspace/"
    assert form.attrs.get("method") == "get"
    assert form.attrs.get("role") == "search"
    assert form.attrs.get("aria-controls") == "evidence-brief-result"

    inputs = [node for node in form.walk() if node.tag == "input" and node.attrs.get("id") == "b26-brief-query"]
    assert len(inputs) == 1
    assert inputs[0].attrs.get("name") == "q"
    assert inputs[0].attrs.get("type") == "search"
    assert "required" in inputs[0].attrs
    assert "minlength" in inputs[0].attrs and "maxlength" in inputs[0].attrs

    result = _nodes_with_attr(document, "id", "evidence-brief-result")
    assert len(result) == 1
    assert result[0].has_class("b26-brief-result")
    for element_id in (
        "evidence-brief-title",
        "evidence-brief-status",
        "evidence-brief-body",
        "evidence-brief-copy",
        "evidence-brief-reset",
    ):
        assert len(_nodes_with_attr(document, "id", element_id)) == 1


def test_homepage_exposes_an_actual_source_linked_worked_example() -> None:
    source, document = _parse_homepage()
    examples = _nodes_with_attr(document, "data-worked-example")
    assert len(examples) == 1
    example = examples[0]
    assert example.attrs.get("id") == "worked-example"
    assert example.attrs.get("aria-labelledby") == "example-caption"

    panels = _nodes_with_attr(example, "data-example-panel")
    steps = _nodes_with_attr(example, "data-example-step")
    assert len(panels) == 3
    assert len(steps) == 3
    assert len(_nodes_with_attr(example, "data-example-play")) == 1
    assert len(_nodes_with_attr(example, "data-example-status")) == 1
    assert len(_nodes_with_attr(example, "data-example-note")) == 1
    assert len(_nodes_with_attr(example, "data-example-copy")) == 1

    example_text = _normalize(example.raw_text()).lower()
    for phrase in (
        "original practitioner source",
        "base2026 source note",
        "creator’s suggestion",
        "base2026 context",
        "finding:",
        "next step:",
    ):
        assert phrase in example_text

    source_links = [node.attrs.get("href") for node in _nodes_with_tag(example, "a") if (node.attrs.get("href") or "").startswith("/sources/")]
    assert len(source_links) == 1
    assert "tiktok-video-" in source_links[0]
    assert any("learn.microsoft.com/en-us/clarity/ai-visibility/bot-activity-overview" in (node.attrs.get("href") or "") for node in _nodes_with_tag(example, "a"))

    for obsolete_attr in (
        "data-lab-source-card",
        "data-lab-lens",
        "data-lab-excerpt",
        "data-lab-action",
        "data-lab-excerpt-highlight",
        "data-lab-scene",
    ):
        assert not _nodes_with_attr(example, obsolete_attr), f"obsolete {obsolete_attr} must stay removed"

    assert "source-lab-hero" not in source
    assert not re.search(r"\b(?:certified|fact certification|truth certification|source verified)\b", source, re.I)


def test_homepage_content_is_visible_without_motion_enhancement() -> None:
    source, document = _parse_homepage()
    main_nodes = _nodes_with_tag(document, "main")
    assert len(main_nodes) == 1
    sections = _nodes_with_tag(main_nodes[0], "section")
    assert sections
    for section in sections:
        if section.attrs.get("id") == "evidence-brief-result":
            assert "hidden" in section.attrs, "the result panel may wait for a submitted question"
        else:
            assert "hidden" not in section.attrs, f"{section.attrs.get('class', 'section')} must render without JavaScript"
            assert _normalize(section.raw_text()), "each public section needs a static content fallback"

    worked_example = _nodes_with_attr(document, "data-worked-example")[0]
    assert all("hidden" not in panel.attrs for panel in _nodes_with_attr(worked_example, "data-example-panel"))

    inline_scripts = [node for node in _nodes_with_tag(document, "script") if "src" not in node.attrs]
    assert len(inline_scripts) == 1
    assert inline_scripts[0].attrs.get("type") == "application/ld+json"
    assert "IntersectionObserver" not in source
    assert "b26-motion-ready" not in source

    links = {node.attrs.get("href") for node in _nodes_with_tag(document, "a")}
    assert "/investors" in links
    assert "/factory/" in links
    assert "/about#how-we-grow" in links


def test_homepage_css_keeps_the_worked_example_static_and_reduced_motion_safe() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")
    reduced_start = re.search(r"@media\s*\([^)]*prefers-reduced-motion\s*:\s*reduce[^)]*\)", css, re.I)
    assert reduced_start, "the homepage needs a reduced-motion override"
    reduced_css = css[reduced_start.start():]
    assert re.search(r"transition\s*:\s*none", reduced_css)

    assert not re.search(r"transition\s*:\s*all\b", css, re.I)
    assert not re.search(r"@keyframes|animation(?:-name)?\s*:", css, re.I)
    assert not re.search(r"\binfinite\b", css, re.I)
    assert not re.search(r"opacity\s*:\s*0(?:\b|\s|;)", css)

    example_rules = [body for selector, body in _css_rules(css) if ".b26-example" in selector]
    assert example_rules
    assert any("border" in body and "background" in body for body in example_rules)
    assert any("[hidden]" in selector or "hidden" in selector for selector, _ in _css_rules(css) if ".b26-example-panel" in selector)


def test_homepage_uses_purposeful_groups_without_decorative_indices() -> None:
    source, document = _parse_homepage()
    assert "b26-lab-tool-row__index" not in source
    assert "b26-lab-sequence__number" not in source
    assert not re.search(r">\s*0[1-6]\s*<", source)
    assert len(_nodes_with_attr(document, "data-lab-entry-group")) >= 2
    assert len(_nodes_with_attr(document, "data-lab-entry")) >= 5


def test_shared_shell_keeps_investor_growth_factory_and_creator_routes() -> None:
    header = HEADER.read_text(encoding="utf-8")
    footer = FOOTER.read_text(encoding="utf-8")
    assert "/investors" in header and "/investors" in footer
    assert "/factory/" in header and "/factory/" in footer
    assert "/about#how-we-grow" in header
    assert "/opt-out" in header or "/opt-out.html" in header
