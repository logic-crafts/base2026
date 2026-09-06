"""Static /blog presentation and progressive discovery contracts.

The test-only renderer supplies approved-article fixtures to the template.
Release/catalog validation belongs to the production renderer's own tests.
Actual filter/pagination behavior is tested in base2026_blog_discovery.test.js;
responsive appearance requires native browser verification.
"""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "base2026-blog-index.html"
STYLESHEET = ROOT / "templates" / "base2026-blog.css"
CANONICAL = "https://base2026.dev/blog"
ARTICLE_PATHS = (
    "/journal/source-diversity-check/",
    "/journal/source-backed-video-search-cloudflare/",
)


class _Node:
    def __init__(self, tag: str, attrs=()) -> None:
        self.tag = tag
        self.attrs = dict(attrs)
        self.children: list[_Node | str] = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()

    def has_class(self, value: str) -> bool:
        return value in (self.attrs.get("class") or "").split()

    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text() for child in self.children)


class _Parser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document")
        self.stack = [self.root]
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs) -> None:
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data) -> None:
        self.stack[-1].children.append(data)


def _nodes(root: _Node, *, tag: str = "", class_name: str = "") -> list[_Node]:
    return [
        node for node in root.walk()
        if (not tag or node.tag == tag) and (not class_name or node.has_class(class_name))
    ]


def _fixture_article(index: int, *, featured: bool = False, image: bool = True) -> str:
    # Only the first two records describe real articles. Further records are
    # visibly named fixtures and never enter the public template or catalog.
    path = ARTICLE_PATHS[index] if index < 2 else f"/blog/fixture-note-{index + 1}/"
    title = (
        "Three Sources Are Not Always Three Independent Voices",
        "How I Built Source-Backed Expert-Video Search on Cloudflare",
    )[index] if index < 2 else f"Fixture note {index + 1}: " + "LongUnbrokenTitle" * 10
    description = (
        "A small, reproducible check for source diversity before turning search results into advice."
        if index == 0 else "Engineering notes on the public evidence search and its private processing boundary."
    )
    heading_id = f"blog-{'feature' if featured else 'card'}-fixture-{index}"
    heading = "h2" if featured else "h3"
    category = "Research methods" if index == 0 else "Engineering"
    iso_date = "2026-08-29" if index == 1 else "2026-08-30"
    date_label = "August 29, 2026" if index == 1 else "August 30, 2026"
    meta = (
        f'<p class="b26-blog-card__meta"><span class="b26-blog-card__category">{escape(category)}</span>'
        f'<time datetime="{iso_date}">{date_label}</time></p>'
    )
    body = (
        meta
        + f'<{heading} class="b26-blog-card__title" id="{heading_id}">{escape(title)}</{heading}>'
        + f'<p class="b26-blog-card__excerpt">{escape(description)}</p>'
        + '<div class="b26-blog-card__footer"><span class="b26-blog-card__byline">Alex Yarosh</span>'
        '<span class="b26-blog-card__read">Read article <span aria-hidden="true">→</span></span></div>'
    )
    card_class = "b26-blog-feature" if featured else "b26-blog-card"
    if featured:
        body = f'<div class="b26-blog-feature__body">{body}</div>'
        if image:
            body += (
                '<figure class="b26-blog-feature__media">'
                '<img src="/static/assets/base2026-source-diversity.png" '
                'alt="Blue-and-white evidence card showing video, excerpt and source-link labels." '
                'width="1254" height="1254" loading="eager">'
                '<figcaption>AI-generated editorial illustration, not a screenshot or real-source quote.</figcaption>'
                '</figure>'
            )
        else:
            card_class += " b26-blog-feature--text-only"
    return (
        f'<article class="{card_class}"><a class="b26-blog-card__link" '
        f'href="{escape(path, quote=True)}" aria-labelledby="{heading_id}">{body}</a></article>'
    )


def _render_fixture(count: int = 2, *, image: bool = True, topics: str = "") -> tuple[str, _Node]:
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "@id": CANONICAL, "url": CANONICAL, "name": "Base2026 Blog"},
            {"@type": "Blog", "@id": CANONICAL + "#blog", "url": CANONICAL, "name": "Base2026 Blog"},
        ],
    }
    slots = {
        "STARTUP_HEADER": (ROOT / "templates" / "base2026-startup-header.html").read_text(encoding="utf-8"),
        "STARTUP_FOOTER": (ROOT / "templates" / "base2026-startup-footer.html").read_text(encoding="utf-8"),
        "BLOG_FEATURED": _fixture_article(0, featured=True, image=image),
        "BLOG_CARDS": "".join(_fixture_article(index) for index in range(1, count)),
        "BLOG_TOPIC_LINKS": topics,
        "BLOG_SCHEMA": json.dumps(schema).replace("<", "\\u003c"),
    }
    source = TEMPLATE.read_text(encoding="utf-8")
    for name, value in slots.items():
        source = source.replace("{{" + name + "}}", value)
    return source, _Parser(source).root


def test_blog_template_uses_only_the_root_owned_render_slots() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    assert sorted(re.findall(r"\{\{([A-Z_]+)\}\}", source)) == sorted([
        "STARTUP_HEADER", "STARTUP_FOOTER", "BLOG_FEATURED", "BLOG_CARDS", "BLOG_TOPIC_LINKS", "BLOG_SCHEMA",
    ])
    assert "b26-independent-v1" in source
    assert source.index("base2026-core.css") < source.index("base2026-blog.css")
    assert "Geist+Mono" in source and "Manrope" in source
    assert not re.search(r"(?:\bfixture\b|coming soon|newsletter|subscribers|testimonials)", source, re.I)
    assert '<main id="b26-blog-main"' in source
    for slot in ("BLOG_FEATURED", "BLOG_CARDS", "BLOG_TOPIC_LINKS"):
        start = f"<!--B26_{slot}_START-->"
        end = f"<!--B26_{slot}_END-->"
        assert source.count(start) == source.count(end) == 1
        assert source.index(start) < source.index("{{" + slot + "}}") < source.index(end)


def test_blog_metadata_is_indexable_and_collection_shaped() -> None:
    source, document = _render_fixture()
    canonical = [n for n in _nodes(document, tag="link") if n.attrs.get("rel") == "canonical"]
    assert [n.attrs.get("href") for n in canonical] == [CANONICAL]
    metas = {n.attrs.get("name") or n.attrs.get("property"): n.attrs.get("content") for n in _nodes(document, tag="meta")}
    assert metas["robots"] == "index,follow,max-image-preview:large"
    assert metas["og:url"] == CANONICAL
    assert metas["og:type"] == "website"
    assert metas["description"] and "research" in metas["description"].lower()
    scripts = [node for node in _nodes(document, tag="script") if node.attrs.get("type") == "application/ld+json"]
    assert len(scripts) == 1
    assert scripts[0].attrs == {"type": "application/ld+json", "data-b26-blog-schema": None}
    graph = json.loads(scripts[0].text())["@graph"]
    assert {n["@type"] for n in graph} == {"CollectionPage", "Blog"}
    assert all(n["url"] == CANONICAL for n in graph)
    feed = [n for n in _nodes(document, tag="link") if n.attrs.get("type") == "application/rss+xml"]
    assert len(feed) == 1 and feed[0].attrs["href"] == "/blog/feed.xml"
    assert "{{" not in source


@pytest.mark.parametrize("count", range(2, 11))
def test_blog_is_readable_without_js_with_two_to_ten_articles(count: int) -> None:
    source, document = _render_fixture(count)
    assert len(_nodes(document, tag="h1")) == 1
    assert len(_nodes(document, tag="main")) == 1
    assert len(_nodes(document, class_name="b26-site-header")) == 1
    assert len(_nodes(document, class_name="b26-site-footer")) == 1
    assert len(_nodes(document, class_name="b26-blog-feature")) == 1
    assert len(_nodes(document, class_name="b26-blog-card")) == count - 1
    articles = _nodes(document, tag="article")
    assert len(articles) == count
    for index, article in enumerate(articles):
        links = _nodes(article, tag="a")
        assert len(links) == 1, "a story is one keyboard target, not nested/repeated links"
        title = _nodes(article, class_name="b26-blog-card__title")
        assert len(title) == 1 and title[0].text().strip()
        assert title[0].tag == ("h2" if index == 0 else "h3")
        assert links[0].attrs["aria-labelledby"] == title[0].attrs["id"]
        assert _nodes(article, class_name="b26-blog-card__excerpt")[0].text().strip()
        for node in article.walk():
            assert "hidden" not in node.attrs and "inert" not in node.attrs
            assert not any(attr.startswith("on") for attr in node.attrs)
    article_links = [n.attrs["href"] for n in _nodes(document, class_name="b26-blog-card__link")]
    assert article_links[:2] == list(ARTICLE_PATHS), "existing /journal/ routes must not be moved"
    assert [n.attrs["datetime"] for n in _nodes(document, tag="time")][:2] == ["2026-08-30", "2026-08-29"]
    assert len(set(article_links)) == count
    assert not _nodes(document, tag="template")


def test_blog_discovery_enhances_native_content_without_phantom_controls() -> None:
    _, document = _render_fixture()
    controls = [node for node in document.walk() if "data-blog-controls" in node.attrs]
    assert len(controls) == 1 and "hidden" in controls[0].attrs
    forms = _nodes(controls[0], tag="form")
    assert len(forms) == 1 and forms[0].attrs.get("role") == "search"
    query = _nodes(forms[0], tag="input")[0]
    assert query.attrs.get("name") == "q" and query.attrs.get("type") == "search"
    assert _nodes(forms[0], tag="label")[0].attrs.get("for") == query.attrs["id"]
    assert any(node.attrs.get("type") == "submit" for node in _nodes(forms[0], tag="button"))
    categories = [node for node in controls[0].walk() if "data-blog-categories" in node.attrs]
    assert len(categories) == 1 and not categories[0].children
    scripts = [node for node in _nodes(document, tag="script") if node.attrs.get("src")]
    assert len(scripts) == 1 and scripts[0].attrs["src"] == "/static/base2026-blog-discovery.js"
    assert "defer" in scripts[0].attrs
    assert "Older articles" in _nodes(document, tag="noscript")[0].text()
    for key in ("data-blog-empty", "data-blog-pagination", "data-blog-retry"):
        nodes = [node for node in document.walk() if key in node.attrs]
        assert len(nodes) == 1 and "hidden" in nodes[0].attrs


def test_blog_primary_actions_remain_visible_and_native() -> None:
    _, document = _render_fixture()
    main = _nodes(document, tag="main")[0]
    actions = {n.attrs["href"]: n for n in _nodes(main, tag="a")}
    assert "Try evidence search" in actions["/workspace/"].text()
    assert "Read the methodology" in actions["/methodology"].text()
    assert "RSS feed" in actions["/blog/feed.xml"].text()
    skip = _nodes(document, class_name="b26-blog-skip")[0]
    assert skip.attrs["href"] == "#" + main.attrs["id"]
    visibility_attribute = "".join(("hid", "den"))
    assert all(visibility_attribute not in actions[href].attrs for href in ("/workspace/", "/methodology", "/blog/feed.xml"))


def test_blog_has_no_phantom_topic_controls_or_image_placeholders() -> None:
    _, document = _render_fixture(image=False)
    assert not _nodes(document, class_name="b26-blog-feature__media")
    assert _nodes(document, class_name="b26-blog-feature--text-only")
    assert not _nodes(_nodes(document, class_name="b26-blog-feature")[0], tag="img")
    topics = _nodes(document, class_name="b26-blog-topics")[0]
    assert not topics.children, "an absent topic slot must match the :empty rule"
    _, populated = _render_fixture(topics='<a href="/journal/source-diversity-check/">Source diversity</a>')
    topic_link = _nodes(_nodes(populated, class_name="b26-blog-topics")[0], tag="a")[0]
    assert topic_link.attrs["href"] == ARTICLE_PATHS[0]
    assert topic_link.text() == "Source diversity"


def test_blog_responsive_css_does_not_hide_or_clip_content() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")
    assert "width: var(--b26-shell)" in css
    assert re.search(r"\.b26-blog\s*\{[^}]*min-width:\s*0", css, re.S)
    assert "overflow-wrap: anywhere" in css
    assert re.search(r"\.b26-blog-feature__media img\s*\{[^}]*width:\s*100%[^}]*height:\s*auto", css, re.S)
    assert "object-fit: contain" in css
    assert not re.search(r"overflow(?:-x)?\s*:\s*(?:hidden|clip)|text-overflow|line-clamp|white-space\s*:\s*nowrap", css)
    assert not re.search(r"min-width\s*:\s*[1-9]|width\s*:\s*100vw", css)
    # No animation gate or JS-ready class may make article text disappear.
    assert not re.search(r"opacity\s*:\s*0(?:\D|$)|visibility\s*:\s*hidden", css)


def test_blog_css_is_additive_with_visible_focus_and_reduced_motion() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")
    assert ":root" not in css
    assert not re.search(r"--b26-(?:canvas|surface|ink|accent|shell)\s*:", css)
    assert not re.search(r"\.b26-(?:home|site-header|site-footer|founder|brief)\b", css)
    assert not re.search(r"#(?:c84f07|d9730d|ef6b13|fffaf0)\b", css, re.I)
    assert ":focus-visible" in css and "outline: 3px solid var(--b26-accent)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    reduced = css.split("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert "scroll-behavior: auto !important" in reduced
    assert not re.search(r"@keyframes|\banimation\s*:|(?<![\w-])transform\s*:|transition:\s*all", css)
