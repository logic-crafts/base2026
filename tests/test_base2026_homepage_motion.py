from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "templates" / "base2026-startup-homepage.html"
STYLESHEET = ROOT / "templates" / "base2026-startup-homepage.css"


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
        # A static homepage must not present an old release counter as current.
        assert initial_value == "Unavailable" or (key == "full_transcripts_published" and initial_value == "0")
        assert len(_visible_text_parts(cell)) >= 3, f"{key} needs a label and visible explanation"

    keys = [
        _nodes_with_attr(cell, "data-b26-public-stat")[0].attrs["data-b26-public-stat"]
        for cell in cells
    ]
    assert keys == list(expected_keys)

    routes_copy = _normalize(cells[2].raw_text()).lower()
    assert "sitemap" in routes_copy
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


def test_homepage_exposes_the_source_lab_and_functional_evidence_brief_contract() -> None:
    source, document = _parse_homepage()

    assert '<title>Base2026 — Source-backed answers from expert video</title>' in source
    assert '<link rel="canonical" href="https://base2026.dev/">' in source
    assert 'type="application/ld+json"' in source
    assert "/static/base2026-evidence-brief.js" in source
    assert "THE SOURCE LABORATORY / SEO + AI SEARCH" in source
    assert "Find the source." in source
    assert "Build on evidence." in source

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

    scene = _nodes_with_attr(document, "data-lab-scene")
    assert len(scene) == 1
    image_nodes = _nodes_with_tag(scene[0], "img")
    assert len(image_nodes) == 1
    image = image_nodes[0]
    assert image.has_class("b26-lab-lens__image")
    assert image.attrs.get("src") == "/static/brand/b26-seal.webp"
    assert image.attrs.get("width") == "116"
    assert image.attrs.get("height") == "116"
    assert "ceramic seal lens" in (image.attrs.get("alt") or "")

    stage = _nodes_with_attr(scene[0], "data-lab-stage")
    assert len(stage) == 1
    source_cards = _nodes_with_attr(scene[0], "data-lab-source-card")
    assert len(source_cards) == 3
    assert len(_nodes_with_attr(scene[0], "data-lab-lens")) == 1
    assert len(_nodes_with_attr(scene[0], "data-lab-excerpt")) == 1
    assert len(_nodes_with_attr(scene[0], "data-lab-action")) == 1
    assert len(_nodes_with_attr(scene[0], "data-lab-excerpt-highlight")) == 1
    assert "Illustrative workflow" in _normalize(scene[0].raw_text())
    assert "source-lab-hero" not in source

    caption = _nodes_with_attr(document, "id", "lab-scene-caption")
    assert len(caption) == 1
    caption_text = _normalize(caption[0].raw_text()).lower()
    assert "illustrative workflow" in caption_text

    assert len(_nodes_with_attr(document, "data-lab-source")) == 1
    assert len(_nodes_with_attr(document, "data-lab-line")) == 1
    assert len(_nodes_with_attr(document, "data-lab-motion-status")) == 1
    motion_controls = _nodes_with_tag(document, "button")
    motion_controls = [node for node in motion_controls if "data-lab-motion" in node.attrs]
    assert len(motion_controls) == 1
    assert motion_controls[0].attrs.get("data-lab-motion") == "toggle"
    assert "hidden" in motion_controls[0].attrs

    progress_values = {
        node.attrs.get("data-lab-progress")
        for node in _nodes_with_attr(document, "data-lab-progress")
    }
    assert {"hero", "tools", "sequence", "snapshot", "method", "final"} <= progress_values

    assert not re.search(r"Live index|Source verified|@build_in_public|2026-07-24|Evidence result preview", source)


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

    inline_scripts = [
        node for node in _nodes_with_tag(document, "script")
        if "src" not in node.attrs
    ]
    assert len(inline_scripts) == 1
    assert inline_scripts[0].attrs.get("type") == "application/ld+json"
    assert "IntersectionObserver" not in source
    assert "b26-motion-ready" not in source

    body_copy = _normalize(main_nodes[0].raw_text())
    for phrase in (
        "Choose your next step.",
        "From source to a usable decision.",
        "See what the public layer contains.",
        "Useful evidence stays inspectable.",
    ):
        assert phrase in body_copy

    css = STYLESHEET.read_text(encoding="utf-8")
    assert not re.search(r"opacity\s*:\s*0(?:\b|\s|;)", css)
    assert not re.search(r"transition\s*:\s*all\b", css, re.I)


def test_homepage_css_reduced_motion_is_static_and_has_no_animation_loop() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")
    reduced_start = re.search(r"@media\s*\([^)]*prefers-reduced-motion\s*:\s*reduce[^)]*\)", css, re.I)
    assert reduced_start, "the homepage needs a reduced-motion override"
    reduced_css = css[reduced_start.start():]
    assert re.search(r"transition\s*:\s*none", reduced_css)

    assert not re.search(r"transition\s*:\s*all\b", css, re.I)
    assert not re.search(r"@keyframes|animation(?:-name)?\s*:", css, re.I)
    assert not re.search(r"\binfinite\b", css, re.I)
    assert not re.search(r"opacity\s*:\s*0(?:\b|\s|;)", css)

    # Keep the scoped homepage token contract small and tied to the shared core palette.
    home_rule = re.search(r"\.b26-home\s*\{([^}]*)\}", css, re.S)
    assert home_rule
    assert "--b26-canvas" not in home_rule.group(1)
    assert "--b26-accent" not in home_rule.group(1)

    # The visual line may be animated by the external GSAP enhancement, but its
    # initial CSS state must remain a readable static line without that runtime.
    line_rules = [body for selector, body in _css_rules(css) if "b26-lab-track" in selector]
    assert line_rules
    assert any("position: absolute" in body for body in line_rules)


def test_homepage_uses_purposeful_groups_without_decorative_indices() -> None:
    source, document = _parse_homepage()
    assert "b26-lab-tool-row__index" not in source
    assert "b26-lab-sequence__number" not in source
    assert not re.search(r">\s*0[1-6]\s*<", source)
    assert len(_nodes_with_attr(document, "data-lab-entry-group")) >= 2
    assert len(_nodes_with_attr(document, "data-lab-entry")) >= 5
