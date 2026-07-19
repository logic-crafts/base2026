from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from public_manifest_contract import PUBLIC_PAGE_MANIFEST_SCHEMA, relative_public_route_issue
from alex_design_system_v2 import NON_SOURCE_DESIGN_VERSION
from base2026_product_shell import footer_html as b26_product_footer_html
from base2026_product_shell import header_html as b26_product_header_html
from base2026_ui_system import stylesheet_tags as b26_stylesheet_tags
from base2026_ui_system import visual_component_attributes as b26_visual_component_attributes
from base2026_ui_system import visual_root_attributes as b26_visual_root_attributes

STYLE_VERSION = NON_SOURCE_DESIGN_VERSION
BASE_URL = "https://aggressorbulkit.online/knowledge/"
SOCIAL_IMAGE = "https://aggressorbulkit.online/knowledge/static/assets/base2026-ai-visibility-card.png"
DESIGN_SYSTEM_HREF = f"/knowledge/static/alex-design-system-v2.css?v={STYLE_VERSION}"
SHELL_SCRIPT_HREF = f"/knowledge/static/alex-v4-static-shell.js?v={STYLE_VERSION}"


def read_payload(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def inline_markdown(value: str) -> str:
    """Escape text, then turn a small safe subset of Markdown links into anchors."""
    pieces: list[str] = []
    cursor = 0
    pattern = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+|/[^\s)]+)\)")
    for match in pattern.finditer(value):
        pieces.append(html.escape(value[cursor:match.start()]))
        label = html.escape(match.group(1))
        href = html.escape(match.group(2), quote=True)
        attrs = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
        pieces.append(f'<a href="{href}"{attrs}>{label}</a>')
        cursor = match.end()
    pieces.append(html.escape(value[cursor:]))
    return "".join(pieces)


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    parts: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            parts.append("</ul>")
            in_ul = False
        if in_ol:
            parts.append("</ol>")
            in_ol = False

    for line in lines:
        value = line.strip()
        if not value:
            close_lists()
            continue
        if value.startswith("# "):
            close_lists()
            parts.append(f"<h1>{html.escape(value[2:])}</h1>")
        elif value.startswith("## "):
            close_lists()
            parts.append(f"<h2>{html.escape(value[3:])}</h2>")
        elif value.startswith("### "):
            close_lists()
            parts.append(f"<h3>{html.escape(value[4:])}</h3>")
        elif value.startswith("- "):
            if not in_ul:
                close_lists()
                parts.append("<ul>")
                in_ul = True
            parts.append(f"<li>{inline_markdown(value[2:])}</li>")
        elif re.match(r"^\d+\. ", value):
            if not in_ol:
                close_lists()
                parts.append("<ol>")
                in_ol = True
            item = re.sub(r"^\d+\. ", "", value)
            parts.append(f"<li>{inline_markdown(item)}</li>")
        else:
            close_lists()
            parts.append(f"<p>{inline_markdown(value)}</p>")
    close_lists()
    return "\n".join(parts)


def split_markdown(markdown: str) -> tuple[str, list[str], list[tuple[str, str]]]:
    title = ""
    intro: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = stripped[3:].strip()
            current_lines = []
            continue
        if current_title is None:
            if stripped:
                intro.append(line)
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))
    return title, intro, [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def page_link(item: dict) -> str:
    return f'<a href="/knowledge/{html.escape(item["slug"].strip("/"))}/">{html.escape(item.get("title", item["slug"]))}</a>'


def social_meta(*, title: str, description: str, canonical: str, og_type: str = "article") -> str:
    title_e = html.escape(title)
    description_e = html.escape(description)
    canonical_e = html.escape(canonical)
    image_e = html.escape(SOCIAL_IMAGE)
    return f"""
    <meta property="og:type" content="{html.escape(og_type)}" />
    <meta property="og:site_name" content="Base2026" />
    <meta property="og:title" content="{title_e}" />
    <meta property="og:description" content="{description_e}" />
    <meta property="og:url" content="{canonical_e}" />
    <meta property="og:image" content="{image_e}" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="Base2026 AI visibility research by Alex Yarosh" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title_e}" />
    <meta name="twitter:description" content="{description_e}" />
    <meta name="twitter:image" content="{image_e}" />"""


def cookie_banner_html() -> str:
    """Preserve the existing consent hooks while using the shared controls."""
    return """
    <section class="cookie-banner" data-cookie-banner hidden aria-label="Cookie preferences">
      <div><h2>Cookie preferences</h2><p>We use necessary cookies to run the site and optional cookies to understand what pages are useful. You can accept all, reject non-essential cookies, or manage preferences.</p></div>
      <div class="cookie-actions"><button type="button" class="ay-button ayds-btn ayds-btn--primary" data-cookie-accept>Accept All</button><button type="button" class="ay-button-secondary ayds-btn ayds-btn--secondary" data-cookie-reject>Reject Non-Essential</button><button type="button" class="ay-button-secondary ayds-btn ayds-btn--secondary" data-cookie-manage>Manage Preferences</button></div>
    </section>
    <script src="/knowledge/static/cookie-consent.js?v=20260617-source-readability1" defer></script>"""

def page_schema(page: dict, canonical: str, description: str) -> str:
    title = page.get("title", "Base2026 AI Visibility Audit")
    entity: dict = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": canonical,
        "isPartOf": {"@type": "WebSite", "name": "Base2026", "url": BASE_URL},
        "about": ["AI visibility", "local SEO", "answer engine optimization", "service page SEO"],
        "publisher": {"@type": "Organization", "name": "Base2026"},
        "mainEntityOfPage": canonical,
    }
    if page.get("city") or page.get("niche"):
        entity["spatialCoverage"] = page.get("city", "California")
        entity["keywords"] = [page.get("niche", "local service business"), page.get("city", "California"), "AI visibility audit"]
    return json.dumps(entity, ensure_ascii=False).replace("</", "<\\/")


PRIORITY_BING_SLUGS = [
    "bing-seo-for-roofing-companies",
    "bing-seo-for-hvac-companies",
    "bing-seo-for-law-firms",
    "bing-seo-for-dentists-and-clinics",
    "bing-seo-for-local-contractors",
    "bing-webmaster-tools-ai-visibility-audit",
    "ai-visibility-audit-for-local-service-businesses",
    "ai-visibility-audit-for-bing-traffic",
    "service-area-pages-and-ai-visibility-for-local-businesses",
    "copilot-seo-for-service-businesses",
]


def related_section(title: str, items: list[dict], current_slug: str) -> str:
    links = "\n".join(f"<li>{page_link(item)}</li>" for item in items[:8] if item.get("slug") != current_slug)
    if not links:
        return ""
    return f"<section class=\"content-section ayds-section\"><h2>{html.escape(title)}</h2><ul>{links}</ul></section>"


def priority_bing_cluster_section(pages: list[dict], current_slug: str = "") -> str:
    by_slug = {str(item.get("slug", "")).strip("/"): item for item in pages}
    items = [by_slug[slug] for slug in PRIORITY_BING_SLUGS if slug in by_slug and slug != current_slug]
    links = "\n".join(f"<li>{page_link(item)}</li>" for item in items[:10])
    if not links:
        return ""
    return (
        '<section class="content-section ayds-section ai-pages-priority-cluster">'
        '<p class="eyebrow ayds-eyebrow">Priority crawl path</p>'
        '<h2>Bing and Copilot pages to inspect first</h2>'
        '<p>These pages connect the current IndexNow push to commercial local-service questions, source-backed proof, and audit routing. They are the first set to re-check in Bing Webmaster Tools and Google Search Console.</p>'
        f'<ul>{links}</ul>'
        '</section>'
    )


def infer_money_theme(page: dict) -> dict:
    """Commercial framing for generated Base2026 money/CTPH pages."""
    title = page.get("title", "AI Visibility Audit")
    slug = str(page.get("slug", "")).strip("/")
    lower = f"{title} {slug} {page.get('niche', '')}".lower()
    if "roof" in lower:
        audience = "roofing companies"
        market = "roofing market"
        buyer = "emergency and replacement roofing buyers"
    elif "hvac" in lower:
        audience = "HVAC companies"
        market = "HVAC market"
        buyer = "heating, cooling and emergency-service buyers"
    elif "law" in lower:
        audience = "law firms"
        market = "legal-services market"
        buyer = "high-intent legal buyers"
    elif "service-area" in lower:
        audience = "local service businesses"
        market = "service-area market"
        buyer = "buyers searching by city, service and proof"
    else:
        audience = page.get("niche") or "local service businesses"
        market = page.get("city") or "local market"
        buyer = "buyers comparing options in search and AI answers"
    intent = "Bing and Copilot" if ("bing" in lower or "copilot" in lower) else "Google, Bing and AI answers"
    return {"audience": audience, "market": market, "buyer": buyer, "intent": intent}


def money_hero_section(page: dict, display_title: str, intro_html: str) -> str:
    theme = infer_money_theme(page)
    kicker = "BASE2026 / AI VISIBILITY SYSTEM"
    subcopy = (
        f"A conversion-first Base2026 page for {html.escape(theme['audience'])}: "
        f"make the business easier for {html.escape(theme['intent'])} to crawl, understand, trust and route into a real audit path."
    )
    return f"""
      <section class="b26-money-hero ayds-hero" aria-label="Base2026 money page hero">
        <div class="b26-money-hero__copy">
          <p class="eyebrow ayds-eyebrow">{kicker}</p>
          <h1>{html.escape(display_title)}</h1>
          <p class="b26-money-hero__lead ayds-lead">{subcopy}</p>
          <div class="b26-money-hero__intro">{intro_html}</div>
        </div>
        <aside class="b26-money-hero__panel ayds-card ayds-card--dark" aria-label="Visibility diagnostic panel">
          <p class="eyebrow ayds-eyebrow">Diagnostic panel</p>
          <h2>What gets checked first</h2>
          <ul>
            <li><strong>Answer clarity</strong><span>Can search and AI explain the service, market and proof?</span></li>
            <li><strong>Indexation path</strong><span>Are canonicals, internal links and sitemaps helping discovery?</span></li>
            <li><strong>Commercial proof</strong><span>Are reviews, service evidence and contact paths close to the buyer question?</span></li>
          </ul>
        </aside>
      </section>"""


def diagnostic_strip(page: dict) -> str:
    theme = infer_money_theme(page)
    cards = [
        ("Current visibility", f"Map how {theme['audience']} appear across search, AI answers and competitor pages."),
        ("Category gaps", f"Find the missing service, proof, review and entity signals in the {theme['market']}."),
        ("Content-to-prompt fit", f"Turn buyer questions from {theme['buyer']} into crawlable, answer-ready sections."),
        ("Indexation signals", "Check canonicals, internal links, sitemap inclusion and priority crawl paths before amplification."),
    ]
    return '<section class="b26-money-diagnostic ayds-grid" aria-label="AI visibility diagnostic checkpoints">' + ''.join(
        f'<article><span>{html.escape(label)}</span><p>{html.escape(text)}</p></article>' for label, text in cards
    ) + '</section>'


def method_cards_section(page: dict) -> str:
    theme = infer_money_theme(page)
    cards = [
        ("Money pages", f"Shape pages around the exact commercial questions {theme['buyer']} ask before contacting a provider."),
        ("CTPH pages", "Build crawlable support pages that clarify categories, trust, proof and comparison context."),
        ("AI-answer assets", "Give AI/search systems reusable facts, links and evidence instead of thin marketing copy."),
    ]
    return '<section class="content-section ayds-section b26-money-method"><p class="eyebrow ayds-eyebrow">Base2026 method</p><h2>From public research to useful commercial pages</h2><div class="b26-money-card-grid ayds-grid">' + ''.join(
        f'<article class="ayds-card ayds-card--feature"><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></article>' for title, text in cards
    ) + '</div></section>'


def offer_fit_section(page: dict) -> str:
    theme = infer_money_theme(page)
    return f"""
<section class="content-section ayds-section b26-money-offer"><div><p class="eyebrow ayds-eyebrow">Offer fit</p><h2>Use this page when the business needs clarity before spend.</h2><p>This is for {html.escape(theme['audience'])} that need a better public footprint before buying more ads, citations, SEO content or redesign work.</p></div><ul><li>Good fit: unclear service pages, weak proof, poor AI/search understanding, thin internal links.</li><li>Not a fit: secret data, guaranteed rankings, fake authority, or publishing unreviewed source material.</li><li>Next step: start with a visibility snapshot, then route deeper issues into a diagnostic audit.</li></ul></section>"""


def render_content_sections(sections: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'<section class="content-section ayds-section"><h2>{html.escape(heading)}</h2>{markdown_to_html(body)}</section>'
        for heading, body in sections
    )


def decision_table(page: dict) -> str:
    city = page.get("city") or "the market"
    niche = page.get("niche") or "local service business"
    return f"""
<section class="content-section ayds-section"><h2>How this maps to business work</h2><div class="table-wrap"><table><thead><tr><th>Business question</th><th>Visibility signal</th><th>Recommended action</th></tr></thead><tbody>
<tr><td>Why are competitors easier to find or recommend?</td><td>Competitor pages, citations, reviews, service clarity and entity signals in {html.escape(city)}.</td><td>Request an AI Visibility Diagnostic Audit.</td></tr>
<tr><td>Are the {html.escape(niche)} pages answer-ready?</td><td>Service definitions, buyer questions, proof, internal links, schema and local relevance.</td><td>Review Answer-Ready Service Pages.</td></tr>
<tr><td>Is technical SEO blocking discovery?</td><td>Crawlability, indexation, canonicals, sitemap coverage, metadata and structured data.</td><td>Review Technical SEO &amp; GEO Foundation.</td></tr>
<tr><td>Is the business trusted enough to cite?</td><td>Reviews, citations, profiles, proof pages, business entity consistency and source signals.</td><td>Review Entity, Trust &amp; Source Intelligence.</td></tr>
</tbody></table></div></section>"""


def workflow_section() -> str:
    return """
<section class="content-section ayds-section"><h2>Recommended workflow</h2>
<h3>1. Check what search and AI can understand</h3><p>Start with the public footprint: pages, services, locations, proof, reviews, schema, citations and competitor visibility.</p>
<h3>2. Identify the weak layer</h3><p>The problem may be technical, content-based, local, entity-related, citation-related or competitive. Do not buy random content before the weak layer is clear.</p>
<h3>3. Route private diagnosis into the audit path</h3><p>Base2026 stays public. A business-specific recommendation belongs in the Alex Yarosh audit workflow with the website, market and competitor context.</p>
<h3>4. Build only what supports visibility</h3><p>Improve the pages, internal links, schema, proof, citations and trust signals that make the business easier to crawl, verify, cite and recommend.</p>
</section>"""


def boundary_section() -> str:
    return """
<section class="content-section ayds-section"><h2>What this page is not</h2><ul><li>not a guarantee of rankings or AI mentions;</li><li>not a private analytics vault;</li><li>not a lead database;</li><li>not a replacement for a business-specific audit;</li><li>not a place to upload credentials, customer lists or confidential documents;</li><li>not generic SEO content pretending to be proof.</li></ul><p>Base2026 remains the public research layer. Alex Yarosh's site remains the conversion, audit and service layer.</p></section>"""


def contextual_research_bridge() -> str:
    return f"""
<section class="content-section ayds-section b26-research-bridge" {b26_visual_component_attributes('B26-09', 'apply-research-bridge')}>
  <p class="eyebrow ayds-eyebrow">Apply this research</p>
  <h2>Use the public evidence before making a business-specific decision.</h2>
  <p>Continue to Apply Research only when the question needs the website, market and competitive context. The research path remains complete without a service request.</p>
  <a class="ay-button ayds-btn ayds-btn--primary" href="/knowledge/apply-research.html">Apply this research</a>
</section>"""


def should_noindex_page(page: dict, *, indexable_run: bool) -> bool:
    """Keep broad hubs indexable during an indexable run, but hold templated city/niche pages until evidence is unique."""
    if not indexable_run:
        return True
    if page.get("type") == "city_niche_ai_visibility_audit" and not page.get("allow_index"):
        return True
    return False


def page_html(page: dict, *, noindex: bool, related_groups: list[tuple[str, list[dict]]] | None = None) -> str:
    title = page.get("title", "Base2026 AI Visibility Audit")
    slug = page.get("slug", "")
    description = page.get("meta_description", "Base2026 AI visibility research page.")
    canonical = BASE_URL + slug.strip("/") + "/"
    robots = "noindex,nofollow" if noindex else "index,follow"
    md_title, intro_lines, sections = split_markdown(page.get("body_markdown", ""))
    display_title = md_title or title
    intro_html = markdown_to_html("\n\n".join(intro_lines[:3]))
    schema = page_schema(page, canonical, description)
    eyebrow = "City and niche AI visibility" if page.get("type") == "city_niche_ai_visibility_audit" else "AI visibility audit"
    related_html = ""
    if related_groups:
        related_html = "\n".join(related_section(section_title, items, slug) for section_title, items in related_groups)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{html.escape(description)}" />
    <meta name="robots" content="{robots}" />
    <link rel="canonical" href="{html.escape(canonical)}" />
{social_meta(title=title, description=description, canonical=canonical)}
    <title>{html.escape(title)} | Base2026</title>
    <script type="application/ld+json">{schema}</script>
    <link rel="icon" type="image/png" sizes="32x32" href="/knowledge/static/assets/alex-yarosh-favicon-32.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="/knowledge/static/assets/alex-yarosh-apple-touch.png" />
    <link rel="stylesheet" href="{DESIGN_SYSTEM_HREF}" />
{b26_stylesheet_tags('/knowledge')}
    <script src="{SHELL_SCRIPT_HREF}" defer></script>
  </head>
  <body class="ayds-root ayds-mode-editorial ay-alex-v4-static ay-stitch-home-v3 ay-stitch-home-v4 b26-family-ai-visibility" {b26_visual_root_attributes('ai-visibility')}>
    <a class="skip-link" href="#content">Skip to content</a>
{b26_product_header_html()}
    <main id="content" class="app-shell content-page doc-page ai-visibility-page ayds-page" data-b26-shell>
      <nav class="breadcrumbs ayds-breadcrumbs" aria-label="Breadcrumb"><a href="/knowledge/">Base2026</a><span aria-hidden="true">/</span><a href="/knowledge/ai-visibility-pages/">AI Visibility Lab</a><span aria-hidden="true">/</span><span aria-current="page">{html.escape(title)}</span></nav>
      {money_hero_section(page, display_title, intro_html)}
      {diagnostic_strip(page)}
      {method_cards_section(page)}
      {render_content_sections(sections)}
      {decision_table(page)}
      {workflow_section()}
      {priority_bing_cluster_section(next((items for section_title, items in (related_groups or []) if section_title in {"Priority Bing/Copilot pages", "Base2026 AI visibility hubs"}), []), slug)}
      {offer_fit_section(page)}
      {boundary_section()}
      {related_html}
      {contextual_research_bridge()}
    </main>
{b26_product_footer_html()}
{cookie_banner_html()}
  </body>
</html>"""


def index_html(pages: list[dict], *, noindex: bool) -> str:
    robots = "noindex,nofollow" if noindex else "index,follow"
    title = "AI Visibility Lab"
    description = "A searchable Base2026 lab of AI visibility playbooks, questions, answers and source-backed SEO/GEO/AEO findings for local service businesses."
    canonical = f"{BASE_URL}ai-visibility-pages/"
    hubs = [p for p in pages if p.get("type") == "main_ai_visibility_hub"]
    city_pages = [p for p in pages if p.get("type") == "city_niche_ai_visibility_audit"]

    def card_grid(items: list[dict], *, limit: int | None = None) -> str:
        shown = items[:limit] if limit else items
        cards: list[str] = []
        for item in shown:
            title_text = html.escape(item.get("title", item["slug"]))
            slug = html.escape(item["slug"].strip("/"))
            item_slug = item.get("slug", "")
            kind = item.get("type", "")
            if "bing" in item_slug or "copilot" in item_slug:
                tag = "Bing / Copilot"
            elif kind == "city_niche_ai_visibility_audit":
                tag = "City audit draft"
            elif "review" in item_slug or "trust" in item_slug:
                tag = "Trust signal"
            elif "service" in item_slug:
                tag = "Service pages"
            else:
                tag = "AI visibility"
            haystack = html.escape(" ".join([tag, item.get("title", ""), item.get("slug", ""), item.get("meta_description", ""), item.get("niche", ""), item.get("city", "")]).lower(), quote=True)
            cards.append(
                f'<a class="ai-pages-card ayds-card ayds-card--feature" data-lab-card data-search="{haystack}" href="/knowledge/{slug}/"><span>{html.escape(tag)}</span><strong>{title_text}</strong></a>'
            )
        return "\n".join(cards)

    schema = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": canonical, "isPartOf": {"@type": "WebSite", "name": "Base2026", "url": BASE_URL}}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)} | Base2026</title>
    <meta name="description" content="{html.escape(description)}" />
    <meta name="robots" content="{robots}" />
    <link rel="canonical" href="{canonical}" />
{social_meta(title=title, description=description, canonical=canonical, og_type="website")}
    <script type="application/ld+json">{schema}</script>
    <link rel="icon" type="image/png" sizes="32x32" href="/knowledge/static/assets/alex-yarosh-favicon-32.png" />
    <link rel="stylesheet" href="{DESIGN_SYSTEM_HREF}" />
{b26_stylesheet_tags('/knowledge')}
    <script src="{SHELL_SCRIPT_HREF}" defer></script>
  </head>
  <body class="ayds-root ayds-mode-product ay-alex-v4-static ay-stitch-home-v3 ay-stitch-home-v4 b26-family-ai-visibility" {b26_visual_root_attributes('ai-visibility')}>
    <a class="skip-link" href="#content">Skip to content</a>
{b26_product_header_html()}
    <main id="content" class="app-shell content-page doc-page ai-visibility-page ayds-page" data-b26-shell>
      <nav class="breadcrumbs ayds-breadcrumbs" aria-label="Breadcrumb"><a href="/knowledge/">Base2026</a><span aria-hidden="true">/</span><span aria-current="page">AI Visibility Lab</span></nav>
      <section class="content-section ayds-section ayds-hero ai-pages-intro ai-lab-intro"><p class="eyebrow ayds-eyebrow">AI visibility lab</p><h1>AI Visibility Lab</h1><p class="ayds-lead">A searchable Base2026 playbook of practical questions, answers, source-backed findings and ready-to-use visibility workflows for local service businesses. This is where the strongest Base2026 AI-search research is organized for humans: marketers, founders, operators and business owners who need clear next steps.</p><div class="ai-lab-search ayds-card ayds-card--data" role="search"><label for="ai-lab-search-input">Search the lab</label><input id="ai-lab-search-input" type="search" placeholder="Search Bing, ChatGPT, roofing, reviews, service pages…" autocomplete="off" /><p><span data-lab-count>{len(hubs) + len(city_pages)}</span> lab entries visible</p></div></section>
      <section class="content-section ayds-section ai-pages-directory"><div class="ai-pages-section-head"><p class="eyebrow ayds-eyebrow">Best of Base2026</p><h2>Core AI visibility playbooks</h2><p>Commercial, practical pages grouped as lab cards: questions people actually ask, problems businesses actually face, and workflows that connect research to action.</p></div><div class="ai-pages-grid ai-pages-grid-main ayds-grid" data-lab-grid="main">{card_grid(hubs)}</div></section>
      {priority_bing_cluster_section(hubs)}
      <section class="content-section ayds-section ai-pages-directory"><div class="ai-pages-section-head"><p class="eyebrow ayds-eyebrow">Market experiments</p><h2>City and niche AI visibility questions</h2><p>Local-intent lab entries stay discoverable for research and QA, while indexation is controlled until each market has enough unique local evidence.</p></div><div class="ai-pages-grid ai-pages-grid-compact ayds-grid" data-lab-grid="city">{card_grid(city_pages)}</div></section>
      {workflow_section()}
      {boundary_section()}
      {contextual_research_bridge()}
    </main>
{b26_product_footer_html()}
{cookie_banner_html()}
  <script>
    (() => {{
      const input = document.getElementById('ai-lab-search-input');
      const cards = Array.from(document.querySelectorAll('[data-lab-card]'));
      const count = document.querySelector('[data-lab-count]');
      if (!input || !cards.length) return;
      const update = () => {{
        const query = input.value.trim().toLowerCase();
        let visible = 0;
        for (const card of cards) {{
          const match = !query || (card.dataset.search || card.textContent || '').toLowerCase().includes(query);
          card.hidden = !match;
          if (match) visible += 1;
        }}
        if (count) count.textContent = String(visible);
      }};
      input.addEventListener('input', update);
      update();
    }})();
  </script>
  </body>
</html>"""


def validate_pages(pages: list[dict]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    banned = ["not just", "unlock", "game-changer", "seamless", "robust", "delve", "in today"]
    for page in pages:
        slug = page.get("slug", "")
        body = page.get("body_markdown", "")
        if not slug:
            issues.append("missing slug")
        if slug in seen:
            issues.append(f"duplicate slug: {slug}")
        seen.add(slug)
        lower = body.lower()
        for phrase in banned:
            if phrase in lower:
                issues.append(f"{slug}: banned phrase {phrase}")
        if "—" in body or "–" in body:
            issues.append(f"{slug}: dash character")
        if len(body.split()) < 350:
            issues.append(f"{slug}: too short")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Base2026 AI visibility pages from a JSON page batch.")
    parser.add_argument("--input", default="data/ai_visibility_pages_batch01.json")
    parser.add_argument("--out", default="output/ai_visibility_pages_batch01_preview")
    parser.add_argument("--indexable", action="store_true", help="Render index,follow instead of noindex,nofollow.")
    args = parser.parse_args()

    payload = read_payload(Path(args.input))
    pages = payload.get("pages", [])
    issues = validate_pages(pages)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(issues))

    out_dir = Path(args.out)
    rendered = []
    hubs = [item for item in pages if item.get("type") == "main_ai_visibility_hub"]
    city_pages = [item for item in pages if item.get("type") == "city_niche_ai_visibility_audit"]
    for page in pages:
        slug = page["slug"].strip("/")
        route = f"{slug}/index.html"
        route_problem = relative_public_route_issue(route)
        if route_problem:
            raise SystemExit(f"Unsafe public page slug: {route_problem}")
        target = out_dir / route
        if page.get("type") == "main_ai_visibility_hub":
            page_niche = str(page.get("slug", "")).split("-")[0]
            matching_city_pages = [item for item in city_pages if page_niche and page_niche in str(item.get("niche", ""))]
            related_groups = [
                ("Priority Bing/Copilot pages", hubs),
                ("City and niche AI visibility pages", matching_city_pages or city_pages),
            ]
        else:
            same_city = [item for item in city_pages if item.get("city") == page.get("city")]
            same_niche = [item for item in city_pages if item.get("niche") == page.get("niche")]
            related_groups = [
                (f"More AI visibility audits in {page.get('city', 'this market')}", same_city),
                (f"More {page.get('niche', 'local-service')} AI visibility audits", same_niche),
                ("Base2026 AI visibility hubs", hubs),
            ]
        write_text(target, page_html(page, noindex=should_noindex_page(page, indexable_run=args.indexable), related_groups=related_groups))
        rendered.append(route)

    index_target = out_dir / "ai-visibility-pages" / "index.html"
    write_text(index_target, index_html(pages, noindex=not args.indexable))
    rendered.append(index_target.relative_to(out_dir).as_posix())

    write_text(
        out_dir / "manifest.json",
        json.dumps(
            {
                "schema": PUBLIC_PAGE_MANIFEST_SCHEMA,
                "style_version": STYLE_VERSION,
                "page_count": len(rendered),
                "pages": rendered,
            },
            indent=2,
        ),
    )
    print(json.dumps({"pages": len(rendered), "out": str(out_dir), "indexable": bool(args.indexable)}, indent=2))


if __name__ == "__main__":
    main()
