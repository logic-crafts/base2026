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
        return "".join(
            child if isinstance(child, str) else child.raw_text() for child in self.children
        )

    def direct_text(self) -> str:
        return "".join(child for child in self.children if isinstance(child, str))


class _DocumentParser(HTMLParser):
    _VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

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


def _metric_cells(root: _Node) -> list[_Node]:
    grids = _nodes_with_class(root, "b26-proof-grid")
    assert len(grids) == 1, "the homepage should expose one public metric grid"
    cells = [child for child in grids[0].element_children() if child.tag == "div"]
    assert len(cells) == 4, "the four live metrics should remain separate cells"
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


def _motion_controller(root: _Node) -> str:
    scripts = [node for node in root.walk() if node.tag == "script" and "src" not in node.attrs]
    controllers = [node.raw_text() for node in scripts if "IntersectionObserver" in node.raw_text()]
    assert len(controllers) == 1, "the homepage should have one inline motion controller"
    return controllers[0]


def _css_rules(css: str) -> list[tuple[str, str]]:
    return [(selector.strip(), body) for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]


def test_homepage_metrics_explain_the_public_boundary() -> None:
    _, document = _parse_homepage()
    cells = _metric_cells(document)
    expected = (
        ("2,175", None),
        ("1,574", None),
        ("50", "Public evidence routes"),
        ("0", "Full transcripts published"),
    )

    for cell, (value, label) in zip(cells, expected):
        text = _normalize(cell.raw_text())
        assert value in text
        if label:
            assert label.lower() in text.lower()
        # A value plus a label is not an explanation. Require a third visible
        # text-bearing element so the copy remains readable without JavaScript.
        parts = _visible_text_parts(cell)
        assert len(parts) >= 3, f"{value} needs visible explanatory copy"

    packets = _normalize(cells[2].raw_text()).lower()
    assert "cloud projections" not in _normalize(" ".join(_normalize(cell.raw_text()) for cell in cells)).lower()
    assert "dynamic sitemap" in packets
    assert re.search(r"receipt[\s-]+gated", packets)
    assert "private pipeline" in packets
    assert "public d1 index" in packets
    assert re.search(r"project(?:ed|s|ing)?", packets)

    privacy = _normalize(cells[3].raw_text()).lower()
    assert "privacy by design" in privacy
    assert "only reviewed excerpts and attributed source records are public" in privacy
    assert "full third-party transcripts stay private" in privacy

    keys = [cell.element_children()[0].attrs.get("data-b26-public-stat") for cell in cells]
    assert keys == [
        "documents_indexed",
        "distinct_sources",
        "public_evidence_routes",
        "full_transcripts_published",
    ]
    runtime = (ROOT / "templates" / "base2026-evidence-brief.js").read_text(encoding="utf-8")
    assert 'fetch("/api/stats"' in runtime
    assert "Number.isSafeInteger" in runtime


def test_homepage_motion_hooks_and_controller_are_progressive_and_bounded() -> None:
    source, document = _parse_homepage()
    controller = _motion_controller(document)

    for target_class in ("b26-evidence-console", "b26-rigor-grid"):
        targets = _nodes_with_class(document, target_class)
        assert len(targets) == 1
        hook_blob = " ".join(
            [targets[0].attrs.get("class", "")]
            + [f"{name}={value or ''}" for name, value in targets[0].attrs.items()]
        )
        assert re.search(r"(?:motion|reveal)", hook_blob, re.I), f"{target_class} needs a reveal hook"
        assert "hidden" not in targets[0].attrs

    assert re.search(
        r"(?:\.b26-evidence-console|data-b26-motion-target\s*=\s*['\"]evidence['\"])",
        controller,
    )
    assert re.search(
        r"(?:\.b26-rigor-grid|\.b26-decisions-reveal|data-b26-motion-target\s*=\s*['\"]decisions['\"])",
        controller,
    )
    assert ".b26-site-footer" in controller
    assert "querySelector" in controller
    assert len(re.findall(r"new\s+(?:window\.)?IntersectionObserver\b", controller)) == 1
    assert len(re.findall(r"\.observe\s*\(", controller)) == 1
    assert len(re.findall(r"\.unobserve\s*\(", controller)) == 1

    motion_ready = re.search(
        r"classList\.(?:add|toggle)\(\s*['\"][^'\"]*motion-ready[^'\"]*['\"]",
        controller,
        re.I,
    )
    assert motion_ready, "motion-ready must be opt-in"
    # The capability guard, all target queries, and the injected footer
    # lookup must precede opt-in. Constructing the observer can happen after
    # the class is added because availability was already checked above.
    assert re.search(r"(?:typeof\s+window\.)?IntersectionObserver", controller)
    observer_capability = re.search(
        r"(?:typeof\s+(?:window\.)?IntersectionObserver|(?:IntersectionObserver|window\.IntersectionObserver)\s+in\s+window|!\s*window\.IntersectionObserver)",
        controller,
    )
    assert observer_capability and observer_capability.start() < motion_ready.start()
    for target_query in (
        r"(?:\.b26-evidence-console|data-b26-motion-target\s*=\s*['\"]evidence['\"])",
        r"(?:\.b26-rigor-grid|\.b26-decisions-reveal|data-b26-motion-target\s*=\s*['\"]decisions['\"])",
        r"\.b26-site-footer",
    ):
        query = re.search(target_query, controller)
        assert query and query.start() < motion_ready.start()

    scroll_listeners = re.findall(r"\.addEventListener\s*\(\s*(['\"])scroll\1", controller)
    assert len(scroll_listeners) == 1
    scroll_start = re.search(r"\.addEventListener\s*\(\s*['\"]scroll['\"]", controller)
    assert scroll_start
    scroll_tail = controller[scroll_start.start() : scroll_start.start() + 1200]
    assert re.search(r"passive\s*:\s*true", scroll_tail)
    assert len(re.findall(r"requestAnimationFrame\s*\(", controller)) == 1
    assert re.search(
        r"if\s*\([^)]*(?:pending|frame|ticking|scheduled|raf)[^)]*\)[\s\S]{0,220}requestAnimationFrame",
        controller,
        re.I,
    )
    assert "scrollY" in controller
    assert re.search(r"(?:scrollY|currentScrollY)[^;{}]{0,40}[<>]\s*80", controller, re.I)
    assert re.search(r"(?:scrollY|currentScrollY)[^;{}]{0,40}<\s*24", controller, re.I)
    assert re.search(r"last(?:Scroll)?Y|previous(?:Scroll)?Y", controller, re.I)

    assert re.search(r"matchMedia\s*\([^)]*prefers-reduced-motion[^)]*reduce", controller, re.I)
    assert re.search(r"prefers-reduced-motion[^)]*reduce", controller, re.I)
    assert re.search(r"</script>\s*</body>\s*</html>\s*$", source, re.I)


def test_homepage_css_uses_scoped_motion_tokens_and_static_reduced_mode() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")
    rules = _css_rules(css)
    home_rule = re.search(r"\.b26-home\s*\{([^}]*)\}", css, re.S)
    assert home_rule
    assert "--b26-canvas" not in home_rule.group(1)
    assert "--b26-accent" not in home_rule.group(1)
    assert not re.search(r"background\s*:[^;]*!important", home_rule.group(1))
    assert re.search(r"\.b26-home\s*\{[^}]*--b26-ease-out\s*:\s*cubic-bezier\(0\.23,\s*1,\s*0\.32,\s*1\)", css, re.S)
    assert re.search(r"\.b26-home\s*\{[^}]*--b26-ease-in-out\s*:\s*cubic-bezier\(0\.77,\s*0,\s*0\.175,\s*1\)", css, re.S)
    assert "b26-motion-ready" in css

    assert re.search(
        r"\.b26-home\.b26-motion-ready \.b26-site-header\.is-compact::before\s*\{"
        r"[^}]*transform\s*:\s*translateY\(\s*-1[0-9]px\s*\)",
        css,
        re.S,
    ), "compact header needs a visible composited shell change"
    assert re.search(
        r"\.b26-home\.b26-motion-ready \.b26-site-header\.is-compact "
        r"\.b26-site-header__inner\s*\{[^}]*transform\s*:\s*translateY\(\s*-[5-9]px\s*\)",
        css,
        re.S,
    )
    assert re.search(
        r"\.b26-home \.b26-site-footer nav a\s*\{[^}]*width\s*:\s*fit-content",
        css,
        re.S,
    )

    reduced_start = re.search(r"@media\s*\([^)]*prefers-reduced-motion\s*:\s*reduce[^)]*\)", css, re.I)
    assert reduced_start, "reduced motion needs an explicit static override"
    reduced_css = css[reduced_start.start() :]
    assert re.search(r"transition\s*:\s*none", reduced_css)
    assert re.search(r"animation\s*:\s*none", reduced_css)
    assert re.search(r"transform\s*:\s*none", reduced_css)
    assert re.search(r"opacity\s*:\s*1", reduced_css)
    assert re.search(
        r"\.b26-console-query::after,\s*\n\s*\.b26-home\.b26-motion-ready "
        r"\.b26-console-record p::after\s*\{[^}]*transform\s*:\s*scaleX\(\s*0\s*\)",
        reduced_css,
        re.S,
    ), "reduced motion must remove the text-reveal masks"

    for shell in ("b26-site-header", "b26-site-footer"):
        underline_base = [
            (selector, body)
            for selector, body in rules
            if shell in selector and re.search(r"::(?:after|before)", selector)
        ]
        assert underline_base, f"{shell} text navigation needs a pseudo-element underline"
        assert any(re.search(r"transform\s*:\s*scaleX\(\s*0\s*\)", body) for _, body in underline_base)
        assert any(re.search(r"transition\s*:\s*transform\s+180ms\s+ease", body) for _, body in underline_base)
        assert any(
            re.search(r":hover[^{}]*::(?:after|before)|::(?:after|before)[^{}]*:hover", selector)
            and re.search(r"transform\s*:\s*scaleX\(\s*1\s*\)", body)
            for selector, body in rules
            if shell in selector
        )

    # Reveal rules may opt into opacity zero only through the JS-added class;
    # no-JS HTML must remain fully readable.
    for target_class in ("b26-evidence-console", "b26-rigor-grid", "b26-site-footer"):
        for selector, body in rules:
            if target_class in selector and re.search(r"opacity\s*:\s*0", body):
                assert "motion-ready" in selector, f"{target_class} is hidden before enhancement"


def test_homepage_motion_avoids_forbidden_effects_and_limits_live_pulse() -> None:
    homepage = HOMEPAGE.read_text(encoding="utf-8")
    css = STYLESHEET.read_text(encoding="utf-8")
    controller = _motion_controller(_parse_homepage()[1])
    combined = "\n".join((homepage, css, controller))

    assert not re.search(r"transition\s*:\s*all\b", combined, re.I)
    assert not re.search(r"scale\s*\(\s*0\s*\)", combined, re.I)
    assert not re.search(r"\bparallax\b", combined, re.I)
    assert not re.search(r"animation(?:-name)?\s*:[^;{}]*\binfinite\b", combined, re.I)
    assert not re.search(r"\bsetInterval\s*\(", controller)

    pulse_rules = [
        (selector, body)
        for selector, body in _css_rules(css)
        if "b26-live-dot" in selector and "animation" in body
    ]
    assert pulse_rules, "the live index status should use a finite soft pulse"
    pulse_text = " ".join(body for _, body in pulse_rules)
    assert "1.8s" in pulse_text
    assert re.search(r"(?:\s|^)2(?:\s|;|$)", pulse_text)

    # Scaling is reserved for the underline/reveal pseudo-elements, never a
    # card, button, icon, or link itself.
    for selector, body in _css_rules(css):
        if re.search(r"transform\s*:\s*scaleX?\(", body) and "::" not in selector:
            assert not re.search(r"\.b26-(?:button|icon|proof|system|rigor|roadmap|trust|home-cta)[^,{}]*", selector)
