from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from alex_design_system_v2 import VERSION as STYLE_VERSION
from alex_design_system_v2 import apply_component_classes, stylesheet_href
from alex_v4_static_shell import apply_alex_v4_shell
from base2026_product_shell import footer_html as b26_product_footer_html
from base2026_product_shell import header_html as b26_product_header_html
from base2026_ui_system import stylesheet_tags as b26_stylesheet_tags
from base2026_ui_system import visual_component_attributes as b26_visual_component_attributes
from base2026_ui_system import visual_root_attributes as b26_visual_root_attributes

PAGE_MAP = {
    "00_METHODOLOGY.md": {
        "slug": "methodology.html",
        "eyebrow": "Methodology",
        "title": "Base2026 Methodology",
        "lead": "How Base2026 turns public short-form expert videos into attributed, searchable source records without replacing creator channels.",
        "body_class": "doc-page",
    },
    "01_ROADMAP.md": {
        "slug": "roadmap.html",
        "eyebrow": "Project roadmap",
        "title": "Base2026 Roadmap",
        "lead": "A public roadmap for turning short-form expert video into an attributed, searchable research layer.",
        "body_class": "roadmap-page",
    },
    "02_PROJECT_STORY.md": {
        "slug": "story.html",
        "eyebrow": "Project story",
        "title": "Base2026 Project Story",
        "lead": "How a private SEO/SMM notebook became a public source intelligence experiment.",
        "body_class": "doc-page",
    },
    "03_PRIVACY_POLICY.md": {
        "slug": "privacy.html",
        "eyebrow": "Privacy",
        "title": "Privacy Policy",
        "lead": "Plain-language privacy notes for the early public Base2026 project.",
        "body_class": "doc-page",
    },
    "04_SOURCE_AND_CONTENT_POLICY.md": {
        "slug": "source-policy.html",
        "eyebrow": "Source policy",
        "title": "Source & Content Policy",
        "lead": "How Base2026 handles public sources, attribution, correction, opt-out and content boundaries.",
        "body_class": "doc-page",
    },
    "05_SUPPORT_PAGE.md": {
        "slug": "support.html",
        "eyebrow": "Support",
        "title": "Support Base2026",
        "lead": "Help build a searchable knowledge base for short-form expert video.",
        "body_class": "support-page",
    },
    "06_SITE_STRUCTURE.md": {
        "slug": "site-structure.html",
        "eyebrow": "Site structure",
        "title": "Recommended Site Structure",
        "lead": "A working map for the public Base2026 website and future agent handoffs.",
        "body_class": "doc-page",
    },
    "07_CREATOR_CORRECTION_REMOVAL.md": {
        "slug": "opt-out.html",
        "eyebrow": "Creator correction / removal",
        "title": "Creator Correction / Removal",
        "lead": "How creators can request attribution fixes, excerpt corrections, record removal, or future source suppression.",
        "body_class": "doc-page",
    },
    "08_API_ACCESS.md": {
        "slug": "api.html",
        "eyebrow": "AI and API access",
        "title": "Base2026 API & AI Access",
        "lead": "Public read-only files and agent-readable entry points for using Base2026 as an attributed source intelligence library.",
        "body_class": "doc-page",
    },
    "09_APPLY_RESEARCH.md": {
        "slug": "apply-research.html",
        "eyebrow": "Apply the research",
        "title": "Apply Base2026 Research",
        "lead": "Use Base2026 as a public SEO/GEO/AEO research layer, then route business-specific AI visibility, technical SEO, content and entity trust work into Alex Yarosh audits.",
        "seo_title": "Apply Base2026 Research | SEO, GEO & AEO Source Intelligence",
        "meta_description": "Use Base2026 as a public SEO/GEO/AEO research layer, then route business-specific AI visibility, technical SEO, content and entity trust work into Alex Yarosh audits.",
        "body_class": "doc-page",
    },
}


FAVICON_ASSET_PATH = "static/assets/alex-yarosh-favicon-32.png"
APPLE_TOUCH_ASSET_PATH = "static/assets/alex-yarosh-apple-touch.png"
SOCIAL_IMAGE_URL = "https://aggressorbulkit.online/knowledge/static/assets/alex-yarosh-avatar.png"
SOCIAL_IMAGE_ALT = "Alex Yarosh profile photo"
TWITTER_SITE = "@AleksejAros"

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

def favicon_links(relative_root: str = ".") -> str:
    return "\n".join(
        [
            f'    <link rel="icon" type="image/png" sizes="32x32" href="{relative_root}/{FAVICON_ASSET_PATH}" />',
            f'    <link rel="apple-touch-icon" sizes="180x180" href="{relative_root}/{APPLE_TOUCH_ASSET_PATH}" />',
        ]
    )


def social_meta_tags(title: str, description: str, canonical: str, og_type: str = "website") -> str:
    return "\n".join(
        [
            f'    <meta property="og:type" content="{html.escape(og_type)}" />',
            '    <meta property="og:site_name" content="Base2026" />',
            '    <meta property="og:locale" content="en_US" />',
            f'    <meta property="og:title" content="{html.escape(title)}" />',
            f'    <meta property="og:description" content="{html.escape(description)}" />',
            f'    <meta property="og:url" content="{html.escape(canonical)}" />',
            f'    <meta property="og:image" content="{html.escape(SOCIAL_IMAGE_URL)}" />',
            f'    <meta property="og:image:alt" content="{html.escape(SOCIAL_IMAGE_ALT)}" />',
            '    <meta name="twitter:card" content="summary_large_image" />',
            f'    <meta name="twitter:site" content="{html.escape(TWITTER_SITE)}" />',
            f'    <meta name="twitter:title" content="{html.escape(title)}" />',
            f'    <meta name="twitter:description" content="{html.escape(description)}" />',
            f'    <meta name="twitter:image" content="{html.escape(SOCIAL_IMAGE_URL)}" />',
        ]
    )


def normalize_copy(value: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def nav_key_for_slug(slug_value: str) -> str:
    if slug_value == "roadmap.html":
        return "roadmap"
    if slug_value == "methodology.html":
        return "methodology"
    if slug_value == "support.html":
        return "support"
    if slug_value == "api.html":
        return "api"
    if slug_value == "apply-research.html":
        return "apply"
    return ""


def base2026_breadcrumbs(title: str) -> str:
    current = (title.split("|", 1)[0] or "Current page").strip()
    return f"""
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="./">Base2026</a>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{html.escape(current)}</span>
      </nav>
"""


def inline_md(value: str) -> str:
    code_spans: list[str] = []

    def stash_code_span(match: re.Match[str]) -> str:
        code_spans.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"@@CODESPAN{len(code_spans) - 1}@@"

    text = re.sub(r"`([^`]+)`", stash_code_span, normalize_copy(value.strip()))
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    for index, code_html in enumerate(code_spans):
        text = text.replace(f"@@CODESPAN{index}@@", code_html)
    return text


def flush_paragraph(out: list[str], paragraph: list[str]) -> None:
    if paragraph:
        out.append(f"<p>{inline_md(' '.join(paragraph))}</p>")
        paragraph.clear()


def flush_list(out: list[str], items: list[str]) -> None:
    if items:
        out.append("<ul>" + "".join(f"<li>{inline_md(item)}</li>" for item in items) + "</ul>")
        items.clear()


def render_table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    head_html = "".join(f"<th>{inline_md(cell)}</th>" for cell in head)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{inline_md(cell)}</td>" for cell in row) + "</tr>"
        for row in body
    )
    return f"<div class=\"table-wrap\"><table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table></div>"


def render_markdown(markdown: str, page_class: str) -> tuple[str, str]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    h1 = ""
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            if not h1:
                h1 = line[2:].strip()
                continue
            if current_title or current_lines:
                sections.append((current_title, current_lines))
            current_title = line[2:].strip()
            current_lines = []
            continue
        if line.startswith("## "):
            if current_title or current_lines:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = []
            continue
        current_lines.append(line)
    if current_title or current_lines:
        sections.append((current_title, current_lines))

    rendered_sections = []
    for title, section_lines in sections:
        if not title and not any(line.strip() for line in section_lines):
            continue

        body: list[str] = []
        paragraph: list[str] = []
        list_items: list[str] = []
        table_lines: list[str] = []

        def flush_table() -> None:
            nonlocal table_lines
            if table_lines:
                flush_paragraph(body, paragraph)
                flush_list(body, list_items)
                body.append(render_table(table_lines))
                table_lines = []

        for line in section_lines:
            if re.fullmatch(r"\s*-{3,}\s*", line):
                flush_paragraph(body, paragraph)
                flush_list(body, list_items)
                continue
            if line.startswith("|") and line.endswith("|"):
                table_lines.append(line)
                continue
            flush_table()
            if not line.strip():
                flush_paragraph(body, paragraph)
                flush_list(body, list_items)
                continue
            if line.startswith("### "):
                flush_paragraph(body, paragraph)
                flush_list(body, list_items)
                body.append(f"<h3>{inline_md(line[4:])}</h3>")
                continue
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
                flush_paragraph(body, paragraph)
                list_items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line))
                continue
            paragraph.append(line)
        flush_table()
        flush_paragraph(body, paragraph)
        flush_list(body, list_items)

        section_class = "content-section"
        if page_class == "roadmap-page" and title.lower().startswith("phase"):
            section_class += " roadmap-phase"
        section_heading = f"<h2>{inline_md(title)}</h2>" if title else ""
        rendered_sections.append(f"<section class=\"{section_class}\">{section_heading}{''.join(body)}</section>")
    return h1, "\n".join(rendered_sections)


def cookie_consent_markup() -> str:
    return f"""
    <section class="cookie-banner" data-cookie-banner hidden aria-label="Cookie preferences">
      <div>
        <h2>Cookie preferences</h2>
        <p>We use necessary cookies to run the site and optional cookies to understand what pages are useful. You can accept all, reject non-essential cookies, or manage preferences.</p>
      </div>
      <div class="cookie-actions">
        <button type="button" class="ay-button" data-cookie-accept>Accept All</button>
        <button type="button" class="ay-button-secondary" data-cookie-reject>Reject Non-Essential</button>
        <button type="button" class="ay-button-secondary" data-cookie-manage>Manage Preferences</button>
      </div>
    </section>
    <dialog class="cookie-dialog" data-cookie-dialog aria-label="Manage cookie preferences">
      <form method="dialog">
        <div class="cookie-dialog-head">
          <p class="eyebrow">Privacy controls</p>
          <h2>Manage cookie preferences</h2>
          <p>Necessary cookies are always active because they keep the site working. Analytics and marketing cookies are optional and will only run if you allow them.</p>
        </div>
        <div class="cookie-options">
          <label><input type="checkbox" checked disabled> Necessary <span>Always on. Required for site operation, security, forms, and preference storage.</span></label>
          <label><input type="checkbox" data-cookie-analytics> Analytics <span>Optional. Not currently active. Reserved for privacy-friendly page usefulness analytics.</span></label>
          <label><input type="checkbox" data-cookie-marketing> Marketing <span>Optional. Not currently active. Reserved for future pixels only if explicitly enabled.</span></label>
        </div>
        <div class="cookie-actions">
          <button type="button" class="ay-button" data-cookie-save>Save Preferences</button>
          <button type="button" class="ay-button-secondary" data-cookie-close>Close</button>
        </div>
      </form>
    </dialog>
    <script src="./static/cookie-consent.js?v={STYLE_VERSION}" defer></script>
	"""


COMMERCIAL_LINK_RE = re.compile(
    r'<a\b[^>]*\bhref=["\'](?:/ai-visibility-audit/|/ai-visibility-diagnostic-audit/|/services/|/pricing/)["\'][^>]*>(?P<label>.*?)</a>',
    flags=re.IGNORECASE | re.DOTALL,
)
OPTIONAL_APPLY_RESEARCH_ROUTES = {"methodology.html", "story.html"}


def remove_commercial_links(markup: str) -> str:
    """Keep research copy while removing direct service jumps from Base pages."""

    return COMMERCIAL_LINK_RE.sub(lambda match: match.group("label"), markup)


def contextual_research_bridge(*, apply_route: bool) -> str:
    href = "/ai-visibility-audit/" if apply_route else "/knowledge/apply-research.html"
    label = "Start the visibility check" if apply_route else "Apply this research"
    context = (
        "This is the single optional handoff from public research to a business-specific visibility check."
        if apply_route
        else "Keep the evidence public; move to Apply Research only when the question becomes business-specific."
    )
    return f"""
      <section class="content-section b26-research-bridge" {b26_visual_component_attributes('B26-09', 'apply-research-bridge')}>
        <p class="eyebrow">Apply this research</p>
        <h2>Move from public evidence to one bounded next step.</h2>
        <p>{html.escape(context)}</p>
        <a class="ay-button" href="{href}">{label}</a>
      </section>
"""


def page_shell(meta: dict[str, str], h1: str, body: str) -> str:
    title = normalize_copy(meta["title"])
    page_title = normalize_copy(meta.get("seo_title", f"{title} | Base2026"))
    eyebrow = normalize_copy(meta["eyebrow"])
    lead = normalize_copy(meta["lead"])
    meta_description = normalize_copy(meta.get("meta_description", lead))
    page_class = meta["body_class"]
    current_nav = nav_key_for_slug(meta["slug"])
    canonical = f"https://aggressorbulkit.online/knowledge/{meta['slug']}"
    robots = "index,follow"
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_title,
        "description": meta_description,
        "url": canonical,
        "isPartOf": {
            "@type": "WebSite",
            "name": "Base2026",
            "url": "https://aggressorbulkit.online/knowledge/",
        },
    }
    roadmap_experience = ""
    support_experience = ""
    script_tag = ""
    body_markup = body
    is_apply_research = meta["slug"] == "apply-research.html"
    body_classes = "ayds-root ayds-mode-editorial b26-family-governance"
    if is_apply_research:
        body_classes += " b26-family-apply-research"
    if page_class == "roadmap-page":
        roadmap_experience = """
      <section class="roadmap-experience" aria-labelledby="roadmap-experience-title">
        <div class="roadmap-experience__intro">
          <p class="eyebrow">Product roadmap</p>
          <h2 id="roadmap-experience-title">A compact build sequence for the public knowledge layer.</h2>
          <p>Trust, ingestion, knowledge, rights, signals, and revenue stay in one inspectable operating map.</p>
        </div>
        <section class="summary-strip" aria-label="Roadmap summary">
          <article>
            <span>Now</span>
            <strong>Public Trust Foundation</strong>
          </article>
          <article>
            <span>Next</span>
            <strong>Content Ingestion Pipeline</strong>
          </article>
          <article>
            <span>Later</span>
            <strong>AI Knowledge Layer, Creator Controls, Analytics, Monetization</strong>
          </article>
        </section>
        <section class="control-strip" aria-label="Roadmap controls">
          <div id="phase-tabs" class="phase-tabs"></div>
          <div class="view-note">Click a phase to inspect purpose, status, and milestone sequence.</div>
        </section>
        <section class="viz-grid" aria-label="Roadmap visualization">
          <article class="roadmap-panel roadmap-panel-wide" aria-labelledby="map-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Sequence</p>
              <h2 id="map-title">Phase sequence</h2>
            </div>
            <div id="roadmap-flow" class="flow-canvas"></div>
          </article>
          <article class="roadmap-panel" aria-labelledby="phase-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Selected phase</p>
              <h2 id="phase-title">Phase detail</h2>
            </div>
            <div id="phase-detail"></div>
          </article>
          <article class="roadmap-panel" aria-labelledby="load-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Milestones</p>
              <h2 id="load-title">Phase density</h2>
            </div>
            <div id="workload-chart" class="bar-stack"></div>
          </article>
          <article class="roadmap-panel roadmap-panel-wide" aria-labelledby="funding-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Funding logic</p>
              <h2 id="funding-title">What support unlocks</h2>
            </div>
            <div id="funding-grid" class="funding-grid"></div>
          </article>
          <article class="roadmap-panel roadmap-panel-wide" aria-labelledby="priority-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Execution order</p>
              <h2 id="priority-title">Now / Next / Later</h2>
            </div>
            <div id="priority-stack" class="priority-stack"></div>
          </article>
          <article class="roadmap-panel roadmap-panel-wide proof-panel" aria-labelledby="proof-title">
            <div class="roadmap-panel-head">
              <p class="eyebrow">Roadmap logic</p>
              <h2 id="proof-title">What this roadmap proves</h2>
            </div>
            <div class="proof-grid">
              <article class="proof-card">
                <h3>Trust before scale</h3>
                <p>Policies, attribution, correction paths, and public status come before expanding the database.</p>
              </article>
              <article class="proof-card">
                <h3>Pipeline before AI</h3>
                <p>Ingestion, transcription, metadata, and review must be stable before answer generation becomes public.</p>
              </article>
              <article class="proof-card">
                <h3>Governance before revenue</h3>
                <p>Creator controls and source transparency stay visible before analytics, sponsors, or paid access are added.</p>
              </article>
            </div>
          </article>
        </section>
      </section>
"""
        body_markup = f'<section class="roadmap-fallback" aria-label="Roadmap fallback details">{body}</section>'
        script_tag = f'\n    <script src="./static/roadmap.js?v={STYLE_VERSION}" defer></script>'
    if page_class == "support-page":
        support_experience = """
      <section class="support-experience" aria-labelledby="support-experience-title">
        <div class="support-experience__intro">
          <p class="eyebrow">Support logic</p>
          <h2 id="support-experience-title">What support actually funds.</h2>
          <p>Base2026 support is tied to a public operating model: source intake, review, readable records, creator controls, and transparent product maintenance.</p>
        </div>
        <div class="support-lanes" aria-label="Support priorities">
          <article>
            <span>01</span>
            <h3>Keep the public layer trustworthy</h3>
            <p>Policies, attribution, correction paths, and stable source pages stay live before scale.</p>
          </article>
          <article>
            <span>02</span>
            <h3>Build repeatable ingestion</h3>
            <p>New videos need structured metadata, transcription, review, and safe public excerpts.</p>
          </article>
          <article>
            <span>03</span>
            <h3>Make the knowledge useful</h3>
            <p>Cards, topics, comparisons, and search pages should turn noisy short-form content into usable evidence.</p>
          </article>
        </div>
        <div class="support-flow" aria-label="Base2026 support flow">
          <span>Public source</span>
          <span>Review</span>
          <span>Evidence card</span>
          <span>Searchable page</span>
          <span>Correction path</span>
        </div>
      </section>
"""
    body_markup = remove_commercial_links(body_markup)
    if page_class == "support-page":
        body_markup = body_markup.replace("Use the contact form below or email ", "Email ")
    research_bridge = ""
    if is_apply_research or meta["slug"] in OPTIONAL_APPLY_RESEARCH_ROUTES:
        research_bridge = contextual_research_bridge(apply_route=is_apply_research)
    page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{html.escape(meta_description)}" />
    <meta name="robots" content="{html.escape(robots)}" />
    <link rel="canonical" href="{html.escape(canonical)}" />
{social_meta_tags(page_title, meta_description, canonical)}
    <title>{html.escape(page_title)}</title>
    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
{favicon_links(".")}
    <link rel="stylesheet" href="{stylesheet_href('.')}" data-alex-design-system="v2" />
{b26_stylesheet_tags('/knowledge')}
  </head>
  <body class="{body_classes}" {b26_visual_root_attributes('governance')}>
    <a class="skip-link" href="#content">Skip to content</a>
    {b26_product_header_html()}
    <main id="content" class="app-shell content-page {page_class}" data-b26-shell>
      {base2026_breadcrumbs(title)}
      <section class="page-hero">
        <p class="eyebrow">{html.escape(eyebrow)}</p>
        <h1>{html.escape(normalize_copy(h1 or title))}</h1>
        <p class="lead">{html.escape(lead)}</p>
        <div class="hero-actions">
          <a class="ay-button{' is-current' if current_nav == 'search' else ''}" href="/knowledge/"{' aria-current="page"' if current_nav == 'search' else ''}>Search the library</a>
          <a class="ay-button-secondary{' is-current' if current_nav == 'roadmap' else ''}" href="/knowledge/roadmap.html"{' aria-current="page"' if current_nav == 'roadmap' else ''}>Roadmap</a>
          <a class="ay-button-secondary{' is-current' if current_nav == 'support' else ''}" href="/knowledge/support.html"{' aria-current="page"' if current_nav == 'support' else ''}>Support</a>
          {'<span class="b26-k-document-context" role="note">Base2026 document</span>' if page_class == 'roadmap-page' else ''}
        </div>
      </section>
      {roadmap_experience}
      {support_experience}
      {body_markup}
      {research_bridge}
    </main>
    {b26_product_footer_html()}
    {cookie_consent_markup()}
    {script_tag}
  </body>
</html>
"""
    return apply_component_classes(
        apply_alex_v4_shell(page, relative_root=".", mode="editorial")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Base2026 informational pages from public markdown.")
    parser.add_argument("--source", type=Path, default=Path("docs/public-pages"))
    parser.add_argument("--out", type=Path, default=Path("web/static"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    written = []
    for file_name, meta in PAGE_MAP.items():
        source = args.source / file_name
        if not source.exists():
            raise FileNotFoundError(source)
        h1, body = render_markdown(source.read_text(encoding="utf-8"), meta["body_class"])
        target = args.out / meta["slug"]
        write_text(target, page_shell(meta, h1, body))
        written.append(str(target))
    print(f"info_pages={len(written)}")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
