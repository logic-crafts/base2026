"""Article CSS/markup contract checks, not browser or production-renderer QA."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STYLESHEET = ROOT / "templates" / "base2026-blog-article.css"


def _css() -> str:
    return STYLESHEET.read_text(encoding="utf-8")


def _rules(css: str) -> list[tuple[str, str]]:
    without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(selector.strip(), declarations) for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", without_comments)]


def test_article_styles_are_strictly_scoped_and_keep_shared_authority() -> None:
    css = _css()
    rules = _rules(css)
    assert rules
    for group, _ in rules:
        for selector in group.split(","):
            assert re.match(r"^\.b26-blog-article(?:$|[\s\[:])", selector.strip()), selector
    assert ":root" not in css
    assert not re.search(r"--b26-(?:canvas|surface|ink|accent|shell)\s*:", css)
    assert not re.search(r"\.b26-(?:site-header|site-footer|home|founder|blog-bridge)\b", css)
    assert not re.search(r"#(?:c84f07|d9730d|ef6b13|fffaf0)\b", css, re.I)
    assert "var(--b26-shell)" in css
    assert "font-family: Manrope" in css and '"Geist Mono"' in css


def test_article_prose_and_mobile_layout_are_bounded_without_clipping() -> None:
    css = _css()
    assert re.search(r"\.b26-blog-article\s*\{[^}]*min-width:\s*0", css, re.S)
    assert "max-width: 70ch" in css
    assert "overflow-wrap: anywhere" in css
    assert "grid-template-columns: minmax(0, 190px) minmax(0, 70ch)" in css
    assert "@media (max-width: 980px)" in css
    mobile = css.split("@media (max-width: 980px)", 1)[1].split("@media", 1)[0]
    assert "grid-template-columns: minmax(0, 70ch)" in mobile
    assert "position: static" in mobile and "overflow: visible" in mobile
    phone = css.split("@media (max-width: 620px)", 1)[1].split("@media", 1)[0]
    assert "font-size: 16px" in phone
    assert "padding: 28px 0 56px" in phone
    assert "font-size: clamp(36px, 4.8vw, 62px)" in css
    assert not re.search(r"overflow(?:-x|-y)?\s*:\s*(?:hidden|clip)|text-overflow|line-clamp|white-space\s*:\s*nowrap", css)
    assert not re.search(r"width\s*:\s*100vw|height\s*:\s*100vh", css)
    # Inline citations are the only nonzero minimum width; no card or prose
    # column may impose a fixed minimum that overflows a 390px viewport.
    declarations = "\n".join(body for _, body in _rules(css))
    minimums = re.findall(r"(?<![\w-])min-width\s*:\s*([^;]+)", declarations)
    assert set(minimums) == {"0", "24px"}


def test_article_toc_is_sticky_only_on_tall_desktop_and_anchors_clear_header() -> None:
    css = _css()
    assert "scroll-margin-top: 112px" in css
    assert "@media (min-width: 981px) and (min-height: 740px)" in css
    desktop = css.split("@media (min-width: 981px) and (min-height: 740px)", 1)[1].split("@media", 1)[0]
    assert "position: sticky" in desktop and "top: 104px" in desktop
    assert "max-height: calc(100vh - 128px)" in desktop
    assert "overflow-y: auto" in desktop
    assert css.count("position: sticky") == 1
    assert re.search(r"\.b26-blog-article \.b26-article-layout--no-toc\s*\{[^}]*minmax\(0, 70ch\)", css, re.S)


def test_article_images_preserve_unknown_aspect_and_keep_caption_readable() -> None:
    css = _css()
    image_rule = next(body for selector, body in _rules(css) if selector == ".b26-blog-article .b26-article-hero img")
    assert "width: 100%" in image_rule
    assert "height: auto" in image_rule
    assert "object-fit: contain" in image_rule
    assert "aspect-ratio" not in image_rule and "max-height" not in image_rule
    caption = next(body for selector, body in _rules(css) if selector == ".b26-blog-article .b26-article-hero figcaption")
    assert "font-size: 12px" in caption and "line-height: 1.7" in caption


def test_article_focus_citations_and_motion_do_not_depend_on_javascript() -> None:
    css = _css()
    assert "a:focus-visible" in css
    assert "outline: 3px solid var(--b26-accent)" in css
    assert ".b26-blog-article a.b26-article-citation" in css
    assert ".b26-article-sources li:target" in css
    assert "min-height: 24px" in css and "min-width: 24px" in css
    assert "@keyframes" not in css
    assert not re.search(r"(?<![\w-])transform\s*:|transition:\s*all", css)
    reduced = css.split("@media (prefers-reduced-motion: reduce)", 1)[1].split("@media", 1)[0]
    assert "scroll-behavior: auto !important" in reduced
    assert "animation: none !important" in reduced
    assert "transition: none !important" in reduced
    screen = css.split("@media print", 1)[0]
    assert not re.search(r"display:\s*none|visibility:\s*hidden|opacity:\s*0(?:\D|$)", screen)


def test_article_print_keeps_evidence_and_prints_original_source_urls() -> None:
    css = _css()
    print_css = css.split("@media print", 1)[1]
    assert "font-size: 10.5pt" in print_css
    assert "display: block" in print_css
    assert "white-space: pre-wrap" in print_css
    assert "orphans: 3" in print_css and "widows: 3" in print_css
    assert 'content: " (" attr(href) ")"' in print_css
    for selectors, body in _rules(print_css):
        if re.search(r"display:\s*none", body):
            assert set(selectors.split(",\n  ")) == {
                ".b26-blog-article .b26-article-breadcrumb",
                ".b26-blog-article .b26-article-toc",
            }, "printing must not suppress body, sources, disclosure, or related links"


class _Elements(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs) -> None:
        self.elements.append((tag, dict(attrs)))


def test_article_markup_contract_uses_native_links_and_unique_source_targets() -> None:
    # A test-only example of the root's rendering contract, not a generated
    # public article and not a substitute for production renderer tests.
    fixture = """
    <main id="b26-blog-main" class="b26-blog-article">
      <article>
        <nav class="b26-article-breadcrumb" aria-label="Breadcrumb"><a href="/blog">Blog</a></nav>
        <header class="b26-article-header"><p class="b26-blog-eyebrow">Test fixture</p>
          <h1>Source-first research note fixture</h1><p class="b26-article-lede">Contract example.</p>
          <p class="b26-article-meta"><span>Example author</span><time datetime="2026-08-30">August 30, 2026</time></p>
        </header>
        <div class="b26-article-layout">
          <aside class="b26-article-toc" aria-labelledby="toc-title"><h2 id="toc-title">In this article</h2>
            <nav aria-labelledby="toc-title"><ol><li><a href="#observation">Observation</a></li><li><a href="#sources">Sources</a></li></ol></nav>
          </aside>
          <div class="b26-article-body">
            <section id="observation"><h2>Observation</h2><p>Fixture text with its reference.
              <a class="b26-article-citation" href="#source-example" aria-label="Source 1">[1]</a></p>
              <ul><li>Keep the claim and its source context together.</li></ul>
            </section>
            <section class="b26-article-sources" id="sources"><h2>Sources and notes</h2><ol>
              <li id="source-example"><a href="https://example.com/research-note">Original source fixture</a>
              — Example author, <time datetime="2026-08-30">August 30, 2026</time>.</li></ol>
            </section>
            <aside class="b26-article-disclosure" aria-label="Disclosure"><p>Test fixture; not a public finding.</p></aside>
            <nav class="b26-article-related" aria-labelledby="related-title"><h2 id="related-title">Related reading</h2>
              <ul><li><a href="/journal/source-diversity-check/">The source-diversity check</a></li></ul>
            </nav>
          </div>
        </div>
      </article>
    </main>
    """
    elements = _Elements(fixture).elements
    tags = [tag for tag, _ in elements]
    assert tags.count("main") == tags.count("article") == tags.count("h1") == 1
    assert not set(tags) & {"script", "form", "button", "template"}
    ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    links = [attrs for tag, attrs in elements if tag == "a"]
    assert any(attrs["href"] == "/blog" for attrs in links)
    for attrs in links:
        href = attrs["href"] or ""
        if href.startswith("#"):
            assert href[1:] in ids
        assert href.startswith(("/", "#", "https://")) and not href.startswith("//")
        assert not any(name.startswith("on") for name in attrs)
    assert all("hidden" not in attrs and "inert" not in attrs for _, attrs in elements)
