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

STYLE_VERSION = "20260629-alex-money-template-v1"
BASE_URL = "https://aggressorbulkit.online/knowledge/"
SOCIAL_IMAGE = "https://aggressorbulkit.online/knowledge/static/assets/base2026-ai-visibility-card.png"
FONTS_HREF = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Inter:wght@500;600;700;800&family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap"


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


def header_html(active: str = "ai-visibility") -> str:
    current = ' aria-current="page"' if active == "ai-visibility" else ""
    return f"""
    <a class="skip-link" href="#content">Skip to content</a>
    <header class="site-header">
      <div class="site-header__bar">
        <a class="site-header__brand" href="/"><span class="site-header__avatar" aria-hidden="true"></span><span>Alex Yarosh</span></a>
        <nav class="site-header__nav" aria-label="Base2026 navigation">
          <a class="site-header__link" href="/knowledge/">Search</a><a class="site-header__link" href="/knowledge/analytics.html">Analytics</a><a class="site-header__link" href="/knowledge/api.html">API</a><a class="site-header__link" href="/knowledge/apply-research.html">Apply Research</a><a class="site-header__link" href="/knowledge/ai-visibility-pages/"{current}>AI Visibility Lab</a><a class="site-header__link" href="/knowledge/creators/">Creators</a><a class="site-header__link" href="/knowledge/methodology.html">Methodology</a><span class="site-header__nav-divider" aria-hidden="true"></span><a class="site-header__link site-header__link--site" href="/services/">Services</a><a class="site-header__link site-header__link--site" href="/pricing/">Pricing</a><a class="site-header__link site-header__link--site" href="/about/">About</a>
        </nav>
        <a class="site-header__cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
        <details class="site-header__mobile-menu">
          <summary aria-label="Open navigation"><span></span><span></span><span></span></summary>
          <div class="site-header__mobile-panel">
            <nav aria-label="Mobile navigation">
              <details class="site-header__mobile-base" open>
                <summary>Base2026</summary>
                <div><a href="/knowledge/">Search</a><a href="/knowledge/analytics.html">Analytics</a><a href="/knowledge/api.html">API</a><a href="/knowledge/apply-research.html">Apply Research</a><a href="/knowledge/ai-visibility-pages/"{current}>AI Visibility Lab</a><a href="/knowledge/creators/">Creators</a><a href="/knowledge/methodology.html">Methodology</a></div>
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
    </header>"""


def footer_html() -> str:
    return """
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
            <li><a href="/knowledge/">Search Base2026</a></li>
            <li><a href="/knowledge/api.html">API &amp; AI access</a></li>
            <li><a href="/knowledge/apply-research.html">Apply research</a></li>
            <li><a href="/knowledge/ai-visibility-pages/">AI Visibility Lab</a></li>
            <li><a href="/knowledge/roadmap.html">Roadmap</a></li>
            <li><a href="/knowledge/topics/">Topics</a></li>
            <li><a href="/knowledge/creators/">Creators</a></li>
            <li><a href="/knowledge/methodology.html">Methodology</a></li>
            <li><a href="/knowledge/support.html">Support</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer legal and trust">
          <h3>Legal &amp; Trust</h3>
          <ul class="ay-footer-menu">
            <li><a href="/privacy-policy/">Privacy Policy</a></li>
            <li><button type="button" class="footer-link-button" data-cookie-preferences>Cookie Preferences</button></li>
            <li><a href="/knowledge/source-policy.html">Source &amp; Content Policy</a></li>
            <li><a href="/knowledge/opt-out.html">Creator Correction / Removal</a></li>
            <li><a href="mailto:offflinerpsy@gmail.com">offflinerpsy@gmail.com</a></li>
          </ul>
        </nav>
      </div>
      <div class="ay-footer-bottom"><span>&copy; 2026 Logic Crafts LLC, Kyrgyzstan. Base2026 was created by Alex Yarosh as an independent experimental startup product. It is not a marketing agency and not a marketing-services offering.</span></div>
    </footer>
    <section class="cookie-banner" data-cookie-banner hidden aria-label="Cookie preferences">
      <div><h2>Cookie preferences</h2><p>We use necessary cookies to run the site and optional cookies to understand what pages are useful. You can accept all, reject non-essential cookies, or manage preferences.</p></div>
      <div class="cookie-actions"><button type="button" class="ay-button" data-cookie-accept>Accept All</button><button type="button" class="ay-button-secondary" data-cookie-reject>Reject Non-Essential</button><button type="button" class="ay-button-secondary" data-cookie-manage>Manage Preferences</button></div>
    </section>
    <script src="/knowledge/static/cookie-consent.js?v=20260617-source-readability1" defer></script>"""



def alex_about_hero() -> str:
    return """
      <section class="b26-about-hero ay-about-contact-hero" aria-label="Alex Yarosh visibility hero">
        <div class="b26-about-hero-copy ay-about-contact-hero-copy">
          <div class="b26-founder-quote ay-founder-quote" role="presentation"><span>YOU’RE ALREADY PAYING.</span><span>MAKE IT AN INVESTMENT.</span><span>DO SOMETHING BOLD - <br class="b26-founder-mobile-break">WITH ME.</span></div>
          <p class="b26-founder-support ay-founder-support">Start with your visibility check.</p>
        </div>
        <figure class="b26-hero-figure ay-hero-figure">
          <img class="b26-hero-person ay-hero-person" src="/knowledge/static/assets/alex-yarosh-cutout-v115.png" alt="Alex Yarosh" loading="eager" decoding="async" width="1400" height="1264" />
        </figure>
      </section>"""


def contact_section() -> str:
    return """
      <section class="b26-contact-section" aria-label="Contact Alex Yarosh">
        <div class="b26-contact-layout ay-contact-layout ay-contact-layout-compact">
          <div class="b26-card b26-contact-form-card ay-card ay-contact-form-card">
            <h2>Send a message</h2>
            <p>For partnerships, technical questions, Base2026, or non-audit requests, use this form.</p>
            <form class="b26-form ay-form ay-general-form" method="post" action="/wp-admin/admin-post.php">
              <input type="hidden" name="action" value="ay_general_inquiry" />
              <label>Name<input name="ay_name" autocomplete="name" placeholder="Enter your name" required /></label>
              <label>Email<input type="email" name="ay_email" autocomplete="email" placeholder="name@company.com" required /></label>
              <label>Website <span class="ay-optional-text">optional</span><input type="url" name="ay_website" inputmode="url" autocomplete="url" placeholder="https://example.com" /></label>
              <label>Your message<textarea name="ay_message" placeholder="What should we talk about?" required></textarea></label>
              <button type="submit">Send Message</button>
            </form>
          </div>
          <aside class="b26-card b26-contact-side ay-card ay-contact-side ay-calendar-card">
            <h2>Prefer a call?</h2>
            <p>Send the business context, website URL, and what you want to improve first. If a call is useful, I will send the right Google Calendar slot.</p>
            <div class="b26-calendar-booking-card ay-calendar-booking-card">
              <p class="eyebrow ay-eyebrow">Google Calendar</p>
              <h3>Book a short visibility call.</h3>
              <p>Pick a time if you want to talk through the business, website, and visibility problem directly.</p>
              <a class="ay-button ay-button-small" href="https://calendar.app.google/Cg2Hx6pgM5HH7K6T8" target="_blank" rel="noopener" data-cta="booking_click_base2026_ai_visibility">Open calendar</a>
            </div>
            <p class="ay-small">For full SEO, GEO, AEO, or AI visibility help, start with the free snapshot so the right details are captured.</p>
          </aside>
        </div>
      </section>"""

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
    return f"<section class=\"content-section\"><h2>{html.escape(title)}</h2><ul>{links}</ul></section>"


def priority_bing_cluster_section(pages: list[dict], current_slug: str = "") -> str:
    by_slug = {str(item.get("slug", "")).strip("/"): item for item in pages}
    items = [by_slug[slug] for slug in PRIORITY_BING_SLUGS if slug in by_slug and slug != current_slug]
    links = "\n".join(f"<li>{page_link(item)}</li>" for item in items[:10])
    if not links:
        return ""
    return (
        '<section class="content-section ai-pages-priority-cluster">'
        '<p class="eyebrow">Priority crawl path</p>'
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
      <section class="b26-money-hero" aria-label="Base2026 money page hero">
        <div class="b26-money-hero__copy">
          <p class="eyebrow">{kicker}</p>
          <h1>{html.escape(display_title)}</h1>
          <p class="b26-money-hero__lead">{subcopy}</p>
          <div class="b26-money-hero__intro">{intro_html}</div>
          <div class="b26-money-hero__actions">
            <a class="ay-button" href="/ai-visibility-audit/">Check My AI Visibility</a>
            <a class="ay-button-secondary" href="/pricing/">View Pricing</a>
          </div>
        </div>
        <aside class="b26-money-hero__panel" aria-label="Visibility diagnostic panel">
          <p class="eyebrow">Diagnostic panel</p>
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
    return '<section class="b26-money-diagnostic" aria-label="AI visibility diagnostic checkpoints">' + ''.join(
        f'<article><span>{html.escape(label)}</span><p>{html.escape(text)}</p></article>' for label, text in cards
    ) + '</section>'


def method_cards_section(page: dict) -> str:
    theme = infer_money_theme(page)
    cards = [
        ("Money pages", f"Shape pages around the exact commercial questions {theme['buyer']} ask before contacting a provider."),
        ("CTPH pages", "Build crawlable support pages that clarify categories, trust, proof and comparison context."),
        ("AI-answer assets", "Give AI/search systems reusable facts, links and evidence instead of thin marketing copy."),
    ]
    return '<section class="content-section b26-money-method"><p class="eyebrow">Base2026 method</p><h2>From public research to useful commercial pages</h2><div class="b26-money-card-grid">' + ''.join(
        f'<article><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></article>' for title, text in cards
    ) + '</div></section>'


def offer_fit_section(page: dict) -> str:
    theme = infer_money_theme(page)
    return f"""
<section class="content-section b26-money-offer"><div><p class="eyebrow">Offer fit</p><h2>Use this page when the business needs clarity before spend.</h2><p>This is for {html.escape(theme['audience'])} that need a better public footprint before buying more ads, citations, SEO content or redesign work.</p></div><ul><li>Good fit: unclear service pages, weak proof, poor AI/search understanding, thin internal links.</li><li>Not a fit: secret data, guaranteed rankings, fake authority, or publishing unreviewed source material.</li><li>Next step: start with a visibility snapshot, then route deeper issues into a diagnostic audit.</li></ul></section>"""


def money_final_cta() -> str:
    return """
<section class="content-section b26-money-final-cta"><p class="eyebrow">Next step</p><h2>Turn the page into a visibility system, not another SEO article.</h2><p>Send the site, market and service category. The first useful output is a clear visibility roadmap: what to fix, what to build, and what to measure.</p><div class="b26-money-final-cta__actions"><a class="ay-button" href="/ai-visibility-audit/">Get My Free Roadmap</a><a class="ay-button-secondary" href="/ai-visibility-diagnostic-audit/">Request Diagnostic Audit</a><a class="ay-button-secondary" href="/pricing/">View Pricing</a></div></section>"""


def render_content_sections(sections: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'<section class="content-section"><h2>{html.escape(heading)}</h2>{markdown_to_html(body)}</section>'
        for heading, body in sections
    )


def decision_table(page: dict) -> str:
    city = page.get("city") or "the market"
    niche = page.get("niche") or "local service business"
    return f"""
<section class="content-section"><h2>How this maps to business work</h2><div class="table-wrap"><table><thead><tr><th>Business question</th><th>Visibility signal</th><th>Recommended action</th></tr></thead><tbody>
<tr><td>Why are competitors easier to find or recommend?</td><td>Competitor pages, citations, reviews, service clarity and entity signals in {html.escape(city)}.</td><td>Request an AI Visibility Diagnostic Audit.</td></tr>
<tr><td>Are the {html.escape(niche)} pages answer-ready?</td><td>Service definitions, buyer questions, proof, internal links, schema and local relevance.</td><td>Review Answer-Ready Service Pages.</td></tr>
<tr><td>Is technical SEO blocking discovery?</td><td>Crawlability, indexation, canonicals, sitemap coverage, metadata and structured data.</td><td>Review Technical SEO &amp; GEO Foundation.</td></tr>
<tr><td>Is the business trusted enough to cite?</td><td>Reviews, citations, profiles, proof pages, business entity consistency and source signals.</td><td>Review Entity, Trust &amp; Source Intelligence.</td></tr>
</tbody></table></div></section>"""


def workflow_section() -> str:
    return """
<section class="content-section"><h2>Recommended workflow</h2>
<h3>1. Check what search and AI can understand</h3><p>Start with the public footprint: pages, services, locations, proof, reviews, schema, citations and competitor visibility.</p>
<h3>2. Identify the weak layer</h3><p>The problem may be technical, content-based, local, entity-related, citation-related or competitive. Do not buy random content before the weak layer is clear.</p>
<h3>3. Route private diagnosis into the audit path</h3><p>Base2026 stays public. A business-specific recommendation belongs in the Alex Yarosh audit workflow with the website, market and competitor context.</p>
<h3>4. Build only what supports visibility</h3><p>Improve the pages, internal links, schema, proof, citations and trust signals that make the business easier to crawl, verify, cite and recommend.</p>
</section>"""


def boundary_section() -> str:
    return """
<section class="content-section"><h2>What this page is not</h2><ul><li>not a guarantee of rankings or AI mentions;</li><li>not a private analytics vault;</li><li>not a lead database;</li><li>not a replacement for a business-specific audit;</li><li>not a place to upload credentials, customer lists or confidential documents;</li><li>not generic SEO content pretending to be proof.</li></ul><p>Base2026 remains the public research layer. Alex Yarosh's site remains the conversion, audit and service layer.</p></section>"""


def final_cta() -> str:
    return """
<section class="content-section"><h2>Start with the first useful visibility check</h2><p>If the business is not easy to find, understand, verify or recommend, start with a free AI Visibility Snapshot. If the issue is deeper, move into a Diagnostic Audit before spending on more SEO pages, ads, citations or redesign work.</p><p><a href="/ai-visibility-audit/">Check My AI Visibility</a> <a href="/ai-visibility-diagnostic-audit/">Request Diagnostic Audit</a> <a href="/pricing/">View Pricing</a></p></section>"""


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
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{FONTS_HREF}" rel="stylesheet" />
    <link rel="stylesheet" href="/knowledge/static/styles.css?v={STYLE_VERSION}" />
  </head>
  <body>
{header_html()}
    <main id="content" class="app-shell content-page doc-page ai-visibility-page">
      <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/knowledge/">Base2026</a><span aria-hidden="true">/</span><a href="/knowledge/ai-visibility-pages/">AI Visibility Pages</a><span aria-hidden="true">/</span><span aria-current="page">{html.escape(title)}</span></nav>
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
      {money_final_cta()}
      {contact_section()}
    </main>
{footer_html()}
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
                f'<a class="ai-pages-card" data-lab-card data-search="{haystack}" href="/knowledge/{slug}/"><span>{html.escape(tag)}</span><strong>{title_text}</strong></a>'
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
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{FONTS_HREF}" rel="stylesheet" />
    <link rel="stylesheet" href="/knowledge/static/styles.css?v={STYLE_VERSION}" />
  </head>
  <body>
{header_html()}
    <main id="content" class="app-shell content-page doc-page ai-visibility-page">
      <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/knowledge/">Base2026</a><span aria-hidden="true">/</span><span aria-current="page">AI Visibility Lab</span></nav>
{alex_about_hero()}
      <section class="content-section ai-pages-intro ai-lab-intro"><p class="eyebrow">AI visibility lab</p><h1>AI Visibility Lab</h1><p>A searchable Base2026 playbook of practical questions, answers, source-backed findings and ready-to-use visibility workflows for local service businesses. This is where the strongest Base2026 AI-search research is organized for humans: marketers, founders, operators and business owners who need clear next steps.</p><div class="ai-lab-search" role="search"><label for="ai-lab-search-input">Search the lab</label><input id="ai-lab-search-input" type="search" placeholder="Search Bing, ChatGPT, roofing, reviews, service pages…" autocomplete="off" /><p><span data-lab-count>{len(hubs) + len(city_pages)}</span> lab entries visible</p></div></section>
      <section class="content-section ai-pages-directory"><div class="ai-pages-section-head"><p class="eyebrow">Best of Base2026</p><h2>Core AI visibility playbooks</h2><p>Commercial, practical pages grouped as lab cards: questions people actually ask, problems businesses actually face, and workflows that connect research to action.</p></div><div class="ai-pages-grid ai-pages-grid-main" data-lab-grid="main">{card_grid(hubs)}</div></section>
      {priority_bing_cluster_section(hubs)}
      <section class="content-section ai-pages-directory"><div class="ai-pages-section-head"><p class="eyebrow">Market experiments</p><h2>City and niche AI visibility questions</h2><p>Local-intent lab entries stay discoverable for research and QA, while indexation is controlled until each market has enough unique local evidence.</p></div><div class="ai-pages-grid ai-pages-grid-compact" data-lab-grid="city">{card_grid(city_pages)}</div></section>
      {workflow_section()}
      {boundary_section()}
      {final_cta()}
      {contact_section()}
    </main>
{footer_html()}
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
