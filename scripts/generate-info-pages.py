from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


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


CONTACT_EMAIL = "offflinerpsy@gmail.com"
STYLE_VERSION = "20260617-source-readability1"
FONT_LINK = "https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap"
FAVICON_ASSET_PATH = "static/assets/alex-yarosh-favicon-32.png"
APPLE_TOUCH_ASSET_PATH = "static/assets/alex-yarosh-apple-touch.png"
SOCIAL_IMAGE_URL = "https://aggressorbulkit.online/knowledge/static/assets/alex-yarosh-avatar.png"
SOCIAL_IMAGE_ALT = "Alex Yarosh profile photo"
TWITTER_SITE = "@AleksejAros"

PROJECT_NAV_LINKS = [
    ("search", "Search", ""),
    ("analytics", "Analytics", "analytics.html"),
    ("api", "API", "api.html"),
    ("apply", "Apply Research", "apply-research.html"),
    ("ai_visibility_pages", "AI Visibility Pages", "ai-visibility-pages/"),
    ("topics", "Topics", "topics/"),
    ("creators", "Creators", "creators/"),
    ("methodology", "Methodology", "methodology.html"),
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

FOOTER_LINKS = [
    ("Roadmap", "./roadmap.html"),
    ("Methodology", "./methodology.html"),
    ("API & AI access", "./api.html"),
    ("Apply research", "./apply-research.html"),
    ("Source policy", "./source-policy.html"),
    ("Privacy", "./privacy.html"),
    ("Support", "./support.html"),
    ("Creator Correction / Removal", "./opt-out.html"),
]


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


def root_href(relative_root: str, target: str) -> str:
    root = relative_root.rstrip("/")
    return f"{root}/{target.lstrip('/')}"


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


def base2026_dropdown(relative_root: str = ".", current: str = "") -> str:
    links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{html.escape(root_href(relative_root, target))}"{active}>{html.escape(label)}</a>')
    return f"""
          <div class="site-header__base">
            <a class="site-header__link site-header__link--base2026" href="{html.escape(root_href(relative_root, ''))}" aria-haspopup="true">Base2026</a>
            <div class="site-header__base-menu" aria-label="Base2026 navigation">
              <span>Base2026 Library</span>
              {''.join(links)}
            </div>
          </div>
"""


def header_nav_links(relative_root: str = ".", current: str = "") -> str:
    project_links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        project_links.append(f'<a class="site-header__link" href="{html.escape(root_href(relative_root, target))}"{active}>{html.escape(label)}</a>')
    return (
        "".join(project_links)
        + '<span class="site-header__nav-divider" aria-hidden="true"></span>'
        + '<a class="site-header__link site-header__link--site" href="/services/">Services</a>'
        + '<a class="site-header__link site-header__link--site" href="/pricing/">Pricing</a>'
        + '<a class="site-header__link site-header__link--site" href="/about/">About</a>'
    )


def mobile_base2026_links(relative_root: str = ".", current: str = "") -> str:
    links = []
    for key, label, target in PROJECT_NAV_LINKS:
        active = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{html.escape(root_href(relative_root, target))}"{active}>{html.escape(label)}</a>')
    return "".join(links)


def site_header(relative_root: str = ".", current: str = "") -> str:
    return f"""
    <header class="site-header">
      <div class="site-header__bar">
        <a class="site-header__brand" href="/"><span class="site-header__avatar" aria-hidden="true"></span><span>Alex Yarosh</span></a>
        <nav class="site-header__nav" aria-label="Base2026 navigation">
          {header_nav_links(relative_root, current)}
        </nav>
        <a class="site-header__cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
        <details class="site-header__mobile-menu">
          <summary aria-label="Open navigation"><span></span><span></span><span></span></summary>
          <div class="site-header__mobile-panel">
            <nav aria-label="Mobile navigation">
              <details class="site-header__mobile-base" open>
                <summary>Base2026</summary>
                <div>{mobile_base2026_links(relative_root, current)}</div>
              </details>
              <strong class="mobile-menu-label">Alex Yarosh</strong>
              <a href="/services/">Services</a>
              <a href="/pricing/">Pricing</a>
              <a href="/about/">About</a>
              <a class="site-header__mobile-cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
            </nav>
          </div>
        </details>
      </div>
    </header>
"""


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


def flush_list(out: list[str], items: list[str], *, ordered: bool = False) -> None:
    if items:
        tag = "ol" if ordered else "ul"
        out.append(f"<{tag}>" + "".join(f"<li>{inline_md(item)}</li>" for item in items) + f"</{tag}>")
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
        list_ordered = False
        table_lines: list[str] = []
        code_lines: list[str] | None = None
        code_language = ""

        def flush_active_list() -> None:
            flush_list(body, list_items, ordered=list_ordered)

        def flush_table() -> None:
            nonlocal table_lines
            if table_lines:
                flush_paragraph(body, paragraph)
                flush_active_list()
                body.append(render_table(table_lines))
                table_lines = []

        for line in section_lines:
            if code_lines is not None:
                if line.strip().startswith("```"):
                    language_class = (
                        f' class="language-{html.escape(code_language)}"'
                        if code_language
                        else ""
                    )
                    body.append(
                        f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
                    )
                    code_lines = None
                    code_language = ""
                else:
                    code_lines.append(normalize_copy(line))
                continue
            if line.strip().startswith("```"):
                flush_table()
                flush_paragraph(body, paragraph)
                flush_active_list()
                code_language = line.strip()[3:].strip()
                code_lines = []
                continue
            if re.fullmatch(r"\s*-{3,}\s*", line):
                flush_paragraph(body, paragraph)
                flush_active_list()
                continue
            if line.startswith("|") and line.endswith("|"):
                table_lines.append(line)
                continue
            flush_table()
            if not line.strip():
                flush_paragraph(body, paragraph)
                flush_active_list()
                continue
            if line.startswith("### "):
                flush_paragraph(body, paragraph)
                flush_active_list()
                body.append(f"<h3>{inline_md(line[4:])}</h3>")
                continue
            list_match = re.match(r"^\s*(?P<marker>[-*]|\d+\.)\s+(?P<item>.+)", line)
            if list_match:
                flush_paragraph(body, paragraph)
                ordered = list_match.group("marker")[0].isdigit()
                if list_items and ordered != list_ordered:
                    flush_active_list()
                list_ordered = ordered
                list_items.append(list_match.group("item"))
                continue
            if list_items:
                list_items[-1] = f"{list_items[-1]} {line.strip()}"
                continue
            paragraph.append(line)
        flush_table()
        if code_lines is not None:
            language_class = (
                f' class="language-{html.escape(code_language)}"' if code_language else ""
            )
            body.append(
                f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
        flush_paragraph(body, paragraph)
        flush_active_list()

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


def contact_form_markup(kind: str) -> str:
    if kind == "roadmap":
        return """
      <section class="b26-roadmap-contact" aria-labelledby="b26-roadmap-contact-title">
        <div>
          <p class="b26-eyebrow">Roadmap feedback</p>
          <h2 id="b26-roadmap-contact-title">Send corrections and proposals through the project inbox.</h2>
          <p>Use the Support form for roadmap corrections, source suggestions, infrastructure offers or a proposal for the next public build step.</p>
        </div>
        <a class="b26-button--primary" href="/support">Open the Support form</a>
      </section>
"""
    subject = "Base2026 support request" if kind == "support" else "Base2026 roadmap feedback"
    intro = (
        "Send a correction, support note, sponsorship question, or source suggestion."
        if kind == "support"
        else "Send roadmap feedback, phase corrections, or a proposal for the next public build step."
    )
    return f"""
      <section class="base-contact-section" aria-labelledby="base-contact-title">
        <div class="base-contact-copy">
          <p class="eyebrow">Contact</p>
          <h2 id="base-contact-title">Send the message.</h2>
          <p>{html.escape(intro)}</p>
          <a class="contact-email-link" href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
        </div>
        <form class="base-contact-form" action="mailto:{CONTACT_EMAIL}?subject={html.escape(subject).replace(' ', '%20')}" method="post" enctype="text/plain">
          <label>
            <span>Your name</span>
            <input name="name" autocomplete="name" placeholder="Your name" />
          </label>
          <label>
            <span>Email</span>
            <input name="email" type="email" autocomplete="email" placeholder="you@example.com" required />
          </label>
          <label>
            <span>Website or source URL</span>
            <input name="website_or_source" type="url" placeholder="https://example.com" />
          </label>
          <label class="base-contact-form__full">
            <span>Your message</span>
            <textarea name="message" rows="6" placeholder="What should we talk about?" required></textarea>
          </label>
          <button class="ay-button" type="submit">Send Message</button>
        </form>
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
    footer_links = "\n".join(f'<a href="{href}">{label}</a>' for label, href in FOOTER_LINKS)
    roadmap_experience = ""
    support_experience = ""
    contact_experience = ""
    script_tag = ""
    body_markup = body
    if page_class == "roadmap-page":
        roadmap_experience = """
      <section class="roadmap-experience" aria-labelledby="roadmap-experience-title">
        <div class="roadmap-experience__intro">
          <p class="eyebrow">Product roadmap</p>
          <h2 id="roadmap-experience-title">A compact build sequence for the public evidence layer.</h2>
          <p>Trust, cloud ingestion, indexation, creator rights, distribution, and sustainability stay in one inspectable operating map.</p>
        </div>
        <section class="summary-strip" aria-label="Roadmap summary">
          <article>
            <span>Now</span>
            <strong>Monitor indexation and synchronize evidence</strong>
          </article>
          <article>
            <span>Next</span>
            <strong>Evidence maps, data samples, creator controls</strong>
          </article>
          <article>
            <span>Later</span>
            <strong>Read-only MCP, source expansion, sustainability</strong>
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
              <p class="eyebrow">Delivery logic</p>
              <h2 id="funding-title">What each layer unlocks</h2>
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
        contact_experience = contact_form_markup("roadmap")
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
        contact_experience = contact_form_markup("support")
    return f"""<!doctype html>
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
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{FONT_LINK}" rel="stylesheet" />
    <link rel="stylesheet" href="./static/styles.css?v={STYLE_VERSION}" />
  </head>
  <body>
    <a class="skip-link" href="#content">Skip to content</a>
    {site_header(".", current_nav)}
    <main id="content" class="app-shell content-page {page_class}">
      {base2026_breadcrumbs(title)}
      <section class="page-hero">
        <p class="eyebrow">{html.escape(eyebrow)}</p>
        <h1>{html.escape(normalize_copy(h1 or title))}</h1>
        <p class="lead">{html.escape(lead)}</p>
        <div class="hero-actions">
          <a class="ay-button{' is-current' if current_nav == 'search' else ''}" href="./"{' aria-current="page"' if current_nav == 'search' else ''}>Search the library</a>
          <a class="ay-button-secondary{' is-current' if current_nav == 'apply' else ''}" href="./apply-research.html"{' aria-current="page"' if current_nav == 'apply' else ''}>Apply research</a>
          <a class="ay-button-secondary{' is-current' if current_nav == 'roadmap' else ''}" href="./roadmap.html"{' aria-current="page"' if current_nav == 'roadmap' else ''}>Roadmap</a>
          <a class="ay-button-secondary{' is-current' if current_nav == 'support' else ''}" href="./support.html"{' aria-current="page"' if current_nav == 'support' else ''}>Support</a>
        </div>
      </section>
      {roadmap_experience}
      {support_experience}
      {body_markup}
      {contact_experience}
    </main>
    <footer class="site-footer">
      <div class="ay-wrap ay-footer-grid">
        <section>
          <p class="eyebrow">AI Search Visibility</p>
          <h2>Search visibility for local service businesses</h2>
          <p>We help local service businesses improve visibility across Google, ChatGPT, Gemini, Perplexity and AI-powered search through SEO, GEO, AEO, content, schema and trust signals.</p>
          <div class="ay-actions">
            <a class="ay-button" href="/ai-visibility-audit/">Get My Free Roadmap</a>
            <a class="ay-button-secondary" href="/pricing/">View Pricing</a>
            <a class="ay-button ay-button-base2026" href="/knowledge/">Base2026</a>
          </div>
          <div class="ay-footer-socials" aria-label="Social profiles">
            <p class="ay-footer-socials__label">Socials</p>
            <div class="ay-footer-socials__links">
              <a class="ay-social-link" href="https://x.com/AleksejAros" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on X" title="X">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M18.9 2h3.3l-7.2 8.2L23.5 22h-6.7l-5.2-6.8L5.6 22H2.3l7.7-8.8L1.9 2h6.8l4.7 6.2L18.9 2Zm-1.2 17.9h1.8L7.7 4H5.8l11.9 15.9Z"/></svg>
              </a>
              <span class="ay-social-link ay-social-link--disabled" aria-label="TikTok profile coming soon" title="TikTok profile coming soon">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12.5 2c1.2 0 2.4 0 3.6-.1.1 1.5.6 2.9 1.7 4 1.1 1 2.5 1.5 4 1.7v3.8c-1.4 0-2.7-.3-4-.9-.5-.2-1-.5-1.5-.9v7.7c-.1 1.3-.5 2.6-1.3 3.7-1.2 1.8-3.3 3-5.5 3-1.3.1-2.7-.3-3.8-1-1.9-1.1-3.2-3.2-3.4-5.4v-1.4c.2-1.8 1-3.5 2.4-4.7 1.5-1.4 3.7-2 5.8-1.6v4.2c-.9-.3-2-.2-2.8.3-.6.4-1 1-1.3 1.7-.2.5-.1 1-.1 1.5.2 1.5 1.7 2.8 3.3 2.7 1 0 2-.6 2.6-1.5.2-.3.4-.6.4-1 .1-1.7.1-3.4.1-5.1V2Z"/></svg>
              </span>
              <a class="ay-social-link" href="https://github.com/offflinerpsy" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on GitHub" title="GitHub">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 .5A11.5 11.5 0 0 0 8.36 22.9c.58.11.8-.25.8-.56v-2.02c-3.25.71-3.94-1.38-3.94-1.38-.53-1.35-1.3-1.71-1.3-1.71-1.06-.73.08-.72.08-.72 1.18.08 1.8 1.21 1.8 1.21 1.04 1.79 2.74 1.27 3.41.97.11-.76.41-1.27.74-1.56-2.59-.29-5.31-1.3-5.31-5.76 0-1.27.45-2.31 1.2-3.13-.12-.29-.52-1.48.12-3.09 0 0 .98-.31 3.21 1.19A11.08 11.08 0 0 1 12 5.96c.99 0 1.98.13 2.91.39 2.22-1.5 3.2-1.19 3.2-1.19.64 1.61.24 2.8.12 3.09.75.82 1.2 1.86 1.2 3.13 0 4.47-2.73 5.46-5.33 5.75.42.36.79 1.08.79 2.17v3.04c0 .31.21.68.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>
              </a>
            </div>
          </div>
        </section>
        <nav aria-label="Footer services">
          <h3>Services</h3>
          <ul class="ay-footer-menu">
            <li><a href="/ai-visibility-diagnostic-audit/">AI Visibility Diagnostic Audit</a></li>
            <li><a href="/technical-seo-geo-foundation/">Technical SEO &amp; GEO Foundation</a></li>
            <li><a href="/answer-ready-service-pages/">Answer-Ready Service Pages</a></li>
            <li><a href="/entity-trust-source-intelligence/">Entity, Trust &amp; Source Intelligence</a></li>
            <li><a href="/services/#local-seo">Local SEO &amp; Citations</a></li>
            <li><a href="/services/#monitoring">AI Visibility Monitoring</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer start here">
          <h3>Start Here</h3>
          <ul class="ay-footer-menu">
            <li><a href="/services/">Services</a></li>
            <li><a href="/pricing/">Pricing</a></li>
            <li><a href="/#how-it-works">Process / How It Works</a></li>
            <li><a href="/ai-visibility-audit/">Free AI Visibility Snapshot</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer Base2026">
          <h3>Base2026 Pilot Project</h3>
          <p>Independent experimental startup product: a searchable knowledge base for short-form expert video.</p>
          <ul class="ay-footer-menu">
            <li><a href="./">Search Base2026</a></li>
            <li><a href="./api.html">API &amp; AI access</a></li>
            <li><a href="./apply-research.html">Apply research</a></li>
            <li><a href="./roadmap.html">Roadmap</a></li>
            <li><a href="./topics/">Topics</a></li>
            <li><a href="./creators/">Creators</a></li>
            <li><a href="./story.html">Project Story</a></li>
            <li><a href="./methodology.html">Methodology</a></li>
            <li><a href="./support.html">Support</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer legal and trust">
          <h3>Legal &amp; Trust</h3>
          <ul class="ay-footer-menu">
            <li><a href="/privacy-policy/">Privacy Policy</a></li>
            <li><button type="button" class="footer-link-button" data-cookie-preferences>Cookie Preferences</button></li>
            <li><a href="./source-policy.html">Source &amp; Content Policy</a></li>
            <li><a href="./opt-out.html">Creator Correction / Removal</a></li>
            <li><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
          </ul>
        </nav>
      </div>
      <div class="ay-footer-bottom">
        <span>&copy; 2026 Logic Crafts LLC, Kyrgyzstan. Base2026 was created by Alex Yarosh as an independent experimental startup product. It is not a marketing agency and not a marketing-services offering.</span>
      </div>
    </footer>
    {cookie_consent_markup()}
    {script_tag}
  </body>
</html>
"""


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
