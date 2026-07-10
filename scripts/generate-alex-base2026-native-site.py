#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from html import escape
from pathlib import Path
import json
import shutil

SITE = "https://aggressorbulkit.online"
RELEASE = "alex-about-stitch-20260708a"
OUT = Path(f"output/releases/{RELEASE}/web")
TODAY = date.today().isoformat()
FONTS = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Inter:wght@500;600;700;800&family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap"

SERVICE_LINKS = [
    ("/ai-visibility-diagnostic-audit/", "AI Visibility Diagnostic Audit"),
    ("/technical-seo-geo-foundation/", "Technical SEO & GEO Foundation"),
    ("/answer-ready-service-pages/", "Answer-Ready Service Pages"),
    ("/entity-trust-source-intelligence/", "Entity, Trust & Source Intelligence"),
    ("/ai-visibility-source-footprint/", "AI Visibility Source Footprint"),
]

NAV = [
    ("/", "Home"),
    ("/services/", "Services"),
    ("/ai-visibility-audit/", "AI Visibility"),
    ("/pricing/", "Pricing"),
    ("/knowledge/ai-visibility-pages/", "Base2026"),
    ("/about/", "About"),
]

PRIMARY_CTA = "Get My Free AI Visibility Snapshot"
SHORT_CTA = "Get Free Snapshot"

@dataclass
class Card:
    tag: str
    title: str
    text: str
    href: str = ""
    accent: str = ""

@dataclass
class Page:
    path: str
    title: str
    description: str
    h1: str
    eyebrow: str
    deck: str
    sections: list[str] = field(default_factory=list)
    faq: list[tuple[str, str]] = field(default_factory=list)
    priority: str = "0.8"
    hero: str = "proof"
    schema_type: str = "WebPage"
    robots: str = "index,follow,max-image-preview:large"
    include_sitemap: bool = True


def canonical(path: str) -> str:
    return SITE + ("/" if path == "/" else path)


def attrs_current(href: str, current: str) -> str:
    return ' aria-current="page"' if href == current else ""


def header(current: str) -> str:
    links = "".join(
        f'<a class="site-header__link" href="{h}"{attrs_current(h, current)}>{escape(label)}</a>'
        for h, label in NAV[:-1]
    )
    links += f'<a class="site-header__link site-header__link--site" href="/about/"{attrs_current("/about/", current)}>About</a>'
    mobile = "".join(f'<a href="{h}"{attrs_current(h, current)}>{escape(label)}</a>' for h, label in NAV)
    return f"""
    <a class="skip-link" href="#content">Skip to content</a>
    <header class="site-header">
      <div class="site-header__bar">
        <a class="site-header__brand" href="/"><span class="site-header__avatar" aria-hidden="true"></span><span>Alex Yarosh</span></a>
        <nav class="site-header__nav" aria-label="Alex Yarosh navigation">{links}</nav>
        <a class="site-header__cta" href="/ai-visibility-audit/">{SHORT_CTA}</a>
        <details class="site-header__mobile-menu"><summary aria-label="Open navigation"><span></span><span></span><span></span></summary><div class="site-header__mobile-panel"><nav aria-label="Mobile navigation">{mobile}<a class="site-header__mobile-cta" href="/ai-visibility-audit/">{SHORT_CTA}</a></nav></div></details>
      </div>
    </header>"""


def footer() -> str:
    services = "".join(f'<li><a href="{href}">{escape(label)}</a></li>' for href, label in SERVICE_LINKS)
    return f"""
    <footer class="site-footer">
      <div class="ay-wrap ay-footer-grid">
        <section>
          <p class="eyebrow">AI Search Visibility</p>
          <h2>Check what AI search can already see.</h2>
          <p>Find out whether AI systems understand your business or leave the answer to competitors.</p>
          <div class="ay-actions"><a class="ay-button" href="/ai-visibility-audit/">{PRIMARY_CTA}</a><a class="ay-button-secondary" href="/pricing/">View Pricing</a></div>
        </section>
        <nav aria-label="Footer services"><h3>Services</h3><ul class="ay-footer-menu">{services}</ul></nav>
        <nav aria-label="Footer start here"><h3>Start Here</h3><ul class="ay-footer-menu"><li><a href="/ai-visibility-audit/">Free AI Visibility Snapshot</a></li><li><a href="/sample-ai-visibility-snapshot/">Sample Snapshot Report</a></li><li><a href="/services/">Services</a></li><li><a href="/pricing/">Pricing</a></li><li><a href="/about/">About Alex Yarosh</a></li></ul></nav>
        <nav aria-label="Footer Base2026"><h3>Base2026 Pilot Project</h3><p>Independent experimental startup product: a searchable knowledge base for short-form expert video.</p><ul class="ay-footer-menu"><li><a href="/knowledge/">Search Base2026</a></li><li><a href="/knowledge/ai-visibility-pages/">AI Visibility Lab</a></li><li><a href="/knowledge/ai-visibility-resources.html">AI Visibility Resources</a></li><li><a href="/knowledge/apply-research.html">Apply Research</a></li><li><a href="/knowledge/methodology.html">Methodology</a></li></ul></nav>
        <nav aria-label="Footer legal"><h3>Legal & Trust</h3><ul class="ay-footer-menu"><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/knowledge/source-policy.html">Source & Content Policy</a></li><li><a href="mailto:offflinerpsy@gmail.com">offflinerpsy@gmail.com</a></li></ul></nav>
      </div>
      <div class="ay-footer-bottom"><span>&copy; 2026 Logic Crafts LLC. Base2026 and Alex Yarosh visibility work.</span></div>
    </footer>"""


def button(label: str, href: str, secondary: bool = False) -> str:
    cls = "ay-button-secondary" if secondary else "ay-button"
    return f'<a class="{cls}" href="{href}">{escape(label)}</a>'


def actions(*items: tuple[str, str, bool]) -> str:
    return '<div class="ay-actions alex-native-actions">' + ''.join(button(*i) for i in items) + '</div>'


def cards(items: list[Card], compact: bool = False) -> str:
    grid_cls = "ai-pages-grid ai-pages-grid-compact" if compact else "ai-pages-grid ai-pages-grid-main"
    out: list[str] = []
    for c in items:
        inner = f'<span>{escape(c.tag)}</span><strong>{escape(c.title)}</strong><p>{escape(c.text)}</p>'
        if c.href:
            out.append(f'<a class="ai-pages-card alex-native-card {escape(c.accent)}" href="{c.href}">{inner}</a>')
        else:
            out.append(f'<article class="ai-pages-card alex-native-card {escape(c.accent)}">{inner}</article>')
    return f'<div class="{grid_cls}">' + ''.join(out) + '</div>'


def core_cards(items: list[Card], grid_cls: str) -> str:
    out: list[str] = []
    for c in items:
        tag = f'<span>{escape(c.tag)}</span>' if c.tag else ''
        inner = f'{tag}<strong>{escape(c.title)}</strong><p>{escape(c.text)}</p>'
        cls = f'alex-core-stitch-card alex-native-card {escape(c.accent)}'.strip()
        if c.href:
            out.append(f'<a class="{cls}" href="{c.href}">{inner}</a>')
        else:
            out.append(f'<article class="{cls}">{inner}</article>')
    return f'<div class="alex-core-stitch-card-grid {escape(grid_cls)}">' + ''.join(out) + '</div>'


def core_section(eyebrow: str, h2: str, body: str, cls: str = "") -> str:
    return f'<section class="content-section alex-core-stitch-repair {cls}"><div class="alex-core-stitch-section-head"><p class="eyebrow">{escape(eyebrow)}</p><h2>{escape(h2)}</h2></div>{body}</section>'


def checklist(items: list[str]) -> str:
    return '<ul class="alex-native-checklist">' + ''.join(f'<li>{escape(i)}</li>' for i in items) + '</ul>'


def paragraph_list(items: list[str]) -> str:
    return ''.join(f'<p>{escape(i)}</p>' for i in items)


def snapshot_form(note: str, title: str = PRIMARY_CTA, intent: str = "snapshot", vertical: str = "") -> str:
    industry_hint = vertical or "Dental clinic, roofing company, HVAC contractor, plumber, law firm..."
    return f"""
    <form class="b26-form ay-form alex-native-form" method="post" action="/wp-admin/admin-post.php" data-default-intent="{escape(intent)}">
      <input type="hidden" name="action" value="ay_audit_snapshot" />
      <input type="hidden" name="ay_intent" value="{escape(intent)}" />
      <input type="hidden" name="ay_timing" value="ASAP" />
      <input type="hidden" name="ay_preferred_contact" value="Email" />
      <input type="hidden" name="ay_notes" value="{escape(note)}" />
      <input type="hidden" name="utm_source" value="" /><input type="hidden" name="utm_medium" value="" /><input type="hidden" name="utm_campaign" value="" /><input type="hidden" name="utm_content" value="" /><input type="hidden" name="utm_term" value="" /><input type="hidden" name="landing_page" value="" /><input type="hidden" name="referrer" value="" />
      <label>Website URL<span>Main website you want checked.</span><input name="ay_website" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com" required /></label>
      <label>Business name<span>Use the public name from your site or Google Business Profile.</span><input name="ay_business_name" autocomplete="organization" placeholder="Your business" required /></label>
      <label>Business category<span>Choose the closest service category.</span><input name="ay_industry" placeholder="{escape(industry_hint)}" required /></label>
      <label>City or service area<span>Tell us where customers should be able to find you.</span><input name="ay_market" placeholder="City, metro, county, or service area" required /></label>
      <label>Priority services<span>What should AI search understand first?</span><textarea name="ay_services" placeholder="Emergency repair, implants, AC installation, family law, etc."></textarea></label>
      <label>Known competitors<span>Optional. Add URLs or names you keep seeing.</span><textarea name="ay_competitors_freeform" placeholder="Competitor names or websites"></textarea></label>
      <label>Your name<input name="ay_name" autocomplete="name" placeholder="Your name" required /></label>
      <label>Email<input name="ay_email" type="email" autocomplete="email" placeholder="name@company.com" required /></label>
      <label>Extra notes<span>Recent redesign, rebrand, new location, weak leads, competitor pressure, or AI answer concern.</span><textarea name="ay_extra_notes" placeholder="Anything unusual we should know?"></textarea></label>
      <button type="submit">{escape(title)}</button>
    </form>"""


def home_snapshot_form() -> str:
    return """
    <form class="b26-form ay-form alex-native-form alex-home-compact-form" method="post" action="/wp-admin/admin-post.php" data-default-intent="snapshot">
      <input type="hidden" name="action" value="ay_audit_snapshot" />
      <input type="hidden" name="ay_intent" value="snapshot" />
      <input type="hidden" name="ay_timing" value="ASAP" />
      <input type="hidden" name="ay_preferred_contact" value="Email" />
      <input type="hidden" name="ay_notes" value="Homepage request for Free AI Visibility Snapshot" />
      <input type="hidden" name="utm_source" value="" /><input type="hidden" name="utm_medium" value="" /><input type="hidden" name="utm_campaign" value="" /><input type="hidden" name="utm_content" value="" /><input type="hidden" name="utm_term" value="" /><input type="hidden" name="landing_page" value="" /><input type="hidden" name="referrer" value="" />
      <label>Website URL<span>Main website to check.</span><input name="ay_website" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com" required /></label>
      <label>Your name<input name="ay_name" autocomplete="name" placeholder="Your name" required /></label>
      <label>Email<input name="ay_email" type="email" autocomplete="email" placeholder="name@company.com" required /></label>
      <button type="submit">Get My Free AI Visibility Snapshot</button>
    </form>"""


def home_stat(label: str, value: str) -> str:
    return f'<div class="alex-home-stat"><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'


def home_system_tile(title: str, text: str) -> str:
    return f'<article class="alex-home-system-tile"><h3>{escape(title)}</h3><p>{escape(text)}</p></article>'


def home_service_card(title: str, text: str, href: str) -> str:
    return f'<a class="alex-home-service-card" href="{href}"><span>Service layer</span><h3>{escape(title)}</h3><p>{escape(text)}</p><em>Open service</em></a>'


def home_faq_unified(page: Page) -> str:
    if not page.faq:
        return ""
    items = ''.join(
        f'<details{ " open" if i == 0 else "" }><summary>{escape(q)}</summary><p>{escape(a)}</p></details>'
        for i, (q, a) in enumerate(page.faq)
    )
    return f"""
      <section class="alex-home-unified-section alex-home-faq-block" aria-labelledby="home-faq-title">
        <div class="alex-home-section-copy">
          <span class="alex-home-section-kicker">Questions</span>
          <h2 id="home-faq-title">Short answers before the snapshot.</h2>
        </div>
        <div class="alex-home-faq-accordion">{items}</div>
      </section>"""


def home_page(page: Page) -> str:
    faq_html = home_faq_unified(page)
    return f"""
      <div class="alex-home-unified alex-home-premium" aria-label="Alex Yarosh homepage">
        <section class="alex-home-premium-hero" aria-labelledby="home-title">
          <div class="alex-home-hero-copy">
            <p class="alex-home-kicker">AI Search Visibility · Local service businesses</p>
            <h1 id="home-title">Make your business readable to AI search.</h1>
            <p class="alex-home-deck">When buyers ask ChatGPT, Gemini, Perplexity or Google AI who to hire, the answer depends on how clearly your public signals line up: services, locations, proof, reviews and source footprint.</p>
            <dl class="alex-home-proof-row" aria-label="Snapshot promise">
              {home_stat("First pass", "Manual review")}
              {home_stat("Inputs", "Website · name · email")}
              {home_stat("Evidence", "Base2026-backed")}
            </dl>
          </div>
          <aside id="home-snapshot-form" class="alex-home-snapshot-card alex-home-premium-form-card" aria-label="Free AI Visibility Snapshot form">
            <div class="alex-home-snapshot-head">
              <span>Free snapshot</span>
              <h2>Check what AI can verify.</h2>
              <p>Three fields are enough for the first read of your public footprint.</p>
            </div>
            {home_snapshot_form()}
            <a class="alex-home-form-link" href="/sample-ai-visibility-snapshot/">View sample report →</a>
          </aside>
        </section>

        <section class="alex-home-premium-section alex-home-readable-system" aria-labelledby="home-system-title">
          <div class="alex-home-section-copy">
            <span class="alex-home-section-kicker">One readable system</span>
            <h2 id="home-system-title">The work is not “more SEO”. It is alignment.</h2>
            <p>AI systems need a business they can parse without guessing. The home page now follows the same logic as the audit: diagnose what is visible, repair the weak layer, then connect the proof across sources.</p>
          </div>
          <div class="alex-home-loop" aria-label="AI visibility operating loop">
            <article><span>01 · Diagnose</span><h3>Find the break</h3><p>Check prompts, competitors, source mentions, profile consistency and service clarity before buying more content.</p></article>
            <article><span>02 · Repair</span><h3>Fix the layer</h3><p>Technical crawl, service pages, entity trust, reviews, citations or source footprint get handled in the right order.</p></article>
            <article><span>03 · Prove</span><h3>Make it verifiable</h3><p>Every claim needs public proof AI systems can use: pages, profiles, reviews, citations and Base2026 research patterns.</p></article>
            <article><span>04 · Monitor</span><h3>Keep the answer stable</h3><p>Visibility shifts by prompt, market and source changes. The system keeps checking the footprint instead of guessing.</p></article>
          </div>
        </section>

        <section class="alex-home-premium-section alex-home-services-block" aria-labelledby="home-services-title">
          <div class="alex-home-section-copy">
            <span class="alex-home-section-kicker">Focused consulting</span>
            <h2 id="home-services-title">Choose the repair layer after the snapshot.</h2>
            <p>The services are not separate islands. They are four ways to repair the same visibility system once the bottleneck is visible.</p>
          </div>
          <div class="alex-home-service-grid">
            {home_service_card("Diagnostic Audit", "Find the weak layer before spending more on SEO, content, citations or redesign work.", "/ai-visibility-diagnostic-audit/")}
            {home_service_card("Technical SEO & GEO Foundation", "Fix crawlability, indexation, canonicals, schema, internal links and page clarity.", "/technical-seo-geo-foundation/")}
            {home_service_card("Answer-Ready Service Pages", "Turn vague service pages into decision-stage pages that answer real buyer questions.", "/answer-ready-service-pages/")}
            {home_service_card("Entity, Trust & Source Intelligence", "Align citations, reviews, profiles and source footprint around one verifiable business entity.", "/entity-trust-source-intelligence/")}
          </div>
        </section>

        <section class="alex-home-premium-section alex-home-base2026-band" aria-labelledby="home-base2026-title">
          <div class="alex-home-section-copy">
            <span class="alex-home-section-kicker">Base2026 evidence layer</span>
            <h2 id="home-base2026-title">Research under the consulting work.</h2>
            <p>Base2026 stays as the product/evidence layer. It keeps source records, AI visibility patterns, topic pages and public findings in one searchable system so recommendations can point back to observable signals.</p>
            <a class="alex-home-button alex-home-button-base" href="/knowledge/ai-visibility-pages/">Open AI Visibility Lab</a>
          </div>
          <div class="alex-home-lab-card" aria-label="Base2026 preview">
            <div class="alex-home-lab-search">Evidence preview</div>
            <ul>
              <li><a href="/knowledge/ai-visibility-pages/"><strong>AI visibility pages</strong><span>Curated prompts, patterns and source-backed findings.</span><em>Open evidence</em></a></li>
              <li><a href="/knowledge/apply-research.html"><strong>Source footprint</strong><span>What external sources can verify about the business.</span><em>Apply research</em></a></li>
              <li><a href="/knowledge/methodology.html"><strong>Priority crawl path</strong><span>Which pages and signals deserve attention first.</span><em>View method</em></a></li>
            </ul>
          </div>
        </section>

        {faq_html}
      </div>"""

def about_page(page: Page) -> str:
    return f"""
      <div class="alex-about-stitch" aria-label="About Alex Yarosh">
        <section class="alex-about-stitch-hero" aria-labelledby="about-title">
          <div class="alex-about-stitch-copy">
            <span class="alex-about-stitch-kicker"><span aria-hidden="true"></span>{escape(page.eyebrow)}</span>
            <h1 id="about-title">{escape(page.h1)}</h1>
            <p>{escape(page.deck)}</p>
            <div class="alex-about-stitch-actions">
              <a class="alex-about-button alex-about-button-primary" href="/ai-visibility-audit/">Get Free Snapshot</a>
              <a class="alex-about-button alex-about-button-secondary" href="/services/">Explore Services <span aria-hidden="true">→</span></a>
            </div>
          </div>
          <figure class="alex-about-stitch-portrait" aria-label="Alex Yarosh portrait">
            <img src="/knowledge/static/assets/alex-yarosh-cutout-v115.png" alt="Alex Yarosh Portrait" loading="eager" decoding="async" width="1400" height="1264" />
          </figure>
        </section>

        <section class="alex-about-stitch-final" aria-labelledby="about-final-title">
          <div class="alex-about-stitch-final-inner">
            <h2 id="about-final-title">Before another month of content, check what AI search can see.</h2>
            <p>Get a practical snapshot of your business, competitors, source signals and first-priority fixes. Send the site. I’ll find the clearest visibility gap.</p>
            <div class="alex-about-stitch-actions alex-about-stitch-final-actions">
              <a class="alex-about-button alex-about-button-light" href="/ai-visibility-audit/">Get Free Snapshot</a>
              <a class="alex-about-button alex-about-button-ghost" href="/pricing/">View Pricing</a>
            </div>
          </div>
        </section>
      </div>"""


def message_form() -> str:
    return """
    <form class="b26-form ay-form alex-native-form" method="post" action="/wp-admin/admin-post.php">
      <input type="hidden" name="action" value="ay_general_inquiry" />
      <label>Name<input name="ay_name" autocomplete="name" placeholder="Enter your name" required /></label>
      <label>Email<input type="email" name="ay_email" autocomplete="email" placeholder="name@company.com" required /></label>
      <label>Website <span class="ay-optional-text">optional</span><input type="url" name="ay_website" inputmode="url" autocomplete="url" placeholder="https://example.com" /></label>
      <label>Your message<textarea name="ay_message" placeholder="What should we talk about?" required></textarea></label>
      <button type="submit">Send Message</button>
    </form>"""


def split_section(left: str, right: str, cls: str = "", aside_cls: str = "alex-native-side") -> str:
    return f'<section class="content-section alex-native-split {cls}"><div>{left}</div><aside class="{escape(aside_cls)}">{right}</aside></section>'


def home_snapshot_bridge() -> str:
    return '<section class="content-section alex-home-snapshot-bridge alex-route-a-start" aria-label="Free AI Visibility Snapshot"><div class="alex-home-snapshot-bridge__label"><p class="eyebrow">/ START HERE</p><h2>Free AI Visibility Snapshot</h2></div><p>Check whether AI systems mention your business, which competitors appear, and which public source signals need fixing first.</p>' + actions(("Get My Free Snapshot", "/ai-visibility-audit/", False), ("View Sample", "/sample-ai-visibility-snapshot/", True)) + '</section>'


def section(eyebrow: str, h2: str, body: str, cls: str = "") -> str:
    return f'<section class="content-section alex-native-section {cls}"><div class="ai-pages-section-head"><p class="eyebrow">{escape(eyebrow)}</p><h2>{escape(h2)}</h2></div>{body}</section>'


def faq_section(page: Page) -> str:
    if not page.faq:
        return ""
    if page.path == "/":
        items = ''.join(
            f'<details{ " open" if i == 0 else "" }><summary>{escape(q)}</summary><p>{escape(a)}</p></details>'
            for i, (q, a) in enumerate(page.faq)
        )
        return core_section("/ FAQ", "Questions buyers ask before the snapshot", f'<div class="alex-home-faq-accordion">{items}</div>', "alex-faq-section")
    items = ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in page.faq)
    return section("FAQ", "Questions buyers ask before the snapshot", f'<div class="alex-native-faq">{items}</div>', "alex-native-faq-section")


def hero(page: Page) -> str:
    hero_lines = {
        "/": ["See whether AI search", "understands your business"],
        "/services/": ["Services that fix", "signals AI can use"],
        "/pricing/": ["Pricing should start", "with diagnosis"],
        "/about/": ["You are already paying.", "Make it an investment."],
        "/ai-visibility-audit/": ["Check whether AI search", "can find your business"],
        "/sample-ai-visibility-snapshot/": ["See the snapshot", "before you request it"],
    }.get(page.path, [page.h1])
    hero_spans = ''.join(f'<span>{escape(line)}</span>' for line in hero_lines)
    quote = (
        f'<h1 class="b26-founder-quote ay-founder-quote">{hero_spans}</h1>'
        if page.path == "/"
        else f'<div class="b26-founder-quote ay-founder-quote" role="presentation">{hero_spans}</div>'
    )
    return f"""
      <section class="b26-about-hero ay-about-contact-hero alex-native-hero" aria-label="Alex Yarosh hero">
        <div class="b26-about-hero-copy ay-about-contact-hero-copy">
          <p class="eyebrow alex-native-hero-eyebrow">{escape(page.eyebrow)}</p>
          {quote}
          <p class="b26-founder-support ay-founder-support">{escape(page.deck)}</p>
        </div>
        <figure class="b26-hero-figure ay-hero-figure"><img class="b26-hero-person ay-hero-person" src="/knowledge/static/assets/alex-yarosh-cutout-v115.png" alt="Alex Yarosh" loading="eager" decoding="async" width="1400" height="1264" /></figure>
      </section>"""


def schema_for(page: Page) -> str:
    c = canonical(page.path)
    graph: list[dict] = [
        {"@type": page.schema_type, "@id": c + "#webpage", "name": page.title, "description": page.description, "url": c, "isPartOf": {"@type": "WebSite", "name": "Alex Yarosh", "url": SITE + "/"}},
    ]
    if page.path != "/":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Alex Yarosh", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": page.h1, "item": c},
        ]})
    if page.faq:
        graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in page.faq]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace('</', '<\\/')


# Shared card data
service_cards = [
    Card("DIAGNOSTIC", "AI Visibility Diagnostic Audit", "Find the weak layer before spending on more SEO, content, citations or redesign work.", "/ai-visibility-diagnostic-audit/"),
    Card("FOUNDATION", "Technical SEO & GEO Foundation", "Fix crawlability, indexation, canonicals, schema, internal links and page clarity.", "/technical-seo-geo-foundation/"),
    Card("PAGES", "Answer-Ready Service Pages", "Turn vague service pages into decision-stage pages that answer real buyer questions.", "/answer-ready-service-pages/"),
    Card("TRUST", "Entity, Trust & Source Intelligence", "Strengthen citations, reviews, profiles, source footprint and entity consistency.", "/entity-trust-source-intelligence/"),
    Card("SOURCE", "AI Visibility Source Footprint", "Map what AI systems can verify beyond your own website.", "/ai-visibility-source-footprint/"),
]

pricing_cards = [
    Card("FREE", "AI Visibility Snapshot", "A first look at whether AI systems understand, ignore, or misread your local business.", "/ai-visibility-audit/?intent=snapshot", "price-free"),
    Card("DIAGNOSTIC", "Diagnostic Audit", "A deeper review before technical, content, local trust, or source-footprint implementation.", "/ai-visibility-audit/?intent=diagnostic", "price-paid"),
    Card("90-DAY", "AI Visibility Sprint", "Focused implementation after the priority gaps are clear.", "/ai-visibility-audit/?intent=sprint", "price-sprint"),
    Card("SUPPORT", "Ongoing Support", "Monitoring and improvement support for competitive local markets.", "/ai-visibility-audit/?intent=growth", "price-monthly"),
]

PAGES: list[Page] = []

PAGES.append(Page(
    "/",
    "AI Visibility Consultant for Local Businesses",
    "See if ChatGPT, Gemini, Perplexity and Google AI understand your local business before competitors get the answer.",
    "See whether AI search understands your business",
    "AI search visibility for local service businesses",
    "When buyers ask ChatGPT, Gemini, Perplexity or Google AI who to hire, your business should be clear enough to find, verify and compare.",
    priority="1.0",
    schema_type="ProfessionalService",
    sections=[
        split_section('<p class="eyebrow">/ Free snapshot</p><h2>What the free snapshot checks</h2><p>The Free AI Visibility Snapshot is not a vanity score. It shows where AI systems may get information, where competitors appear, and where your public signals are weak or unclear.</p>' + checklist(["Whether AI systems mention your business for buyer-style prompts.", "Which competitors appear when your business does not.", "What public sources and profiles support your visibility.", "Whether services, locations, reviews and trust signals are easy to understand.", "What fixes should come before more content, ads or generic SEO spend."]) + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("View pricing", "/pricing/", True)), '<div class="alex-services-form-head"><div><h3>Check My Visibility</h3><p>Website, name and email are enough for the first pass.</p></div></div>' + home_snapshot_form(), "alex-core-stitch-entry alex-home-snapshot-entry alex-home-clean-form", "alex-native-side alex-services-form-card alex-services-stitch-form-card"),
        core_section("/ Why local businesses", "Why this matters for local businesses", '<div class="alex-home-text-flow"><p>Local buyers are no longer using only blue links. They ask AI systems direct questions: who to call, who is trusted, who serves their area, who handles the specific problem and who looks credible.</p><h3>Services and locations</h3><p>Your site needs to explain what you do, where you do it, and which buyer questions each service answers.</p><h3>Proof AI can verify</h3><p>Reviews, profiles, citations, service pages and public mentions should support the same business story.</p><h3>Competitor gaps</h3><p>The snapshot shows where clearer competitors are easier to understand before you buy more content, ads or generic SEO work.</p></div>', "alex-home-proof-section alex-home-text-section"),
        core_section("/ Consulting", "Focused consulting, not agency theater", '<div class="alex-home-text-flow"><p>Alex focuses on the parts of SEO, GEO and AEO that affect whether AI systems can understand and verify a local business: crawl basics, answer-ready service pages, entity clarity, reviews, citations, profiles and source footprint.</p><ul class="alex-home-link-list"><li><a href="/ai-visibility-diagnostic-audit/">AI Visibility Diagnostic Audit</a> — find the weak layer before spending more.</li><li><a href="/technical-seo-geo-foundation/">Technical SEO & GEO Foundation</a> — fix crawlability, indexation, schema, internal links and page clarity.</li><li><a href="/answer-ready-service-pages/">Answer-Ready Service Pages</a> — turn vague pages into buyer-question pages.</li><li><a href="/entity-trust-source-intelligence/">Entity, Trust & Source Intelligence</a> — align citations, reviews, profiles and source footprint.</li></ul></div>', "alex-home-services-section alex-home-text-section"),
        core_section("/ Base2026", "Where Base2026 fits", '<div class="alex-home-text-flow"><p>Base2026 is the research and evidence layer behind the audit. It keeps source records, SEO and AI visibility patterns, topic pages and public findings in one place.</p><p>You do not need to study the library before taking action. It exists so recommendations can point back to observable signals instead of guesswork.</p><p class="alex-home-inline-links"><a href="/knowledge/methodology.html">Methodology</a><span>/</span><a href="/knowledge/ai-visibility-pages/">AI Visibility Lab</a><span>/</span><a href="/knowledge/apply-research.html">Apply Research</a></p></div>', "alex-home-base2026-section alex-home-text-section"),
    ],
    faq=[
        ("What does an AI visibility consultant do?", "An AI visibility consultant checks whether AI systems can understand, verify and recommend your business when buyers ask for services you provide."),
        ("Is this the same as local SEO?", "It overlaps with local SEO, but also looks at how AI systems summarize, cite, compare and recommend businesses from public information."),
        ("Where should I start?", "Start with the Free AI Visibility Snapshot so the first conversation is based on visible gaps, not guesswork."),
    ],
))

PAGES.append(Page(
    "/ai-visibility-audit/",
    "Free AI Visibility Audit for Local Businesses",
    "Check if ChatGPT, Gemini, Perplexity and Google AI mention your business, ignore it, or show competitors instead.",
    "Check whether AI search can find and understand your business",
    "Free AI Visibility Snapshot",
    "Buyers are asking AI systems who to hire. This free snapshot checks whether your business appears for real buyer-style questions, which competitors appear instead, and what public signals AI systems can use to verify you.",
    priority="0.95",
    schema_type="Service",
    sections=[
        split_section('<p class="eyebrow">What we check</p><h2>Your business, competitors and source footprint.</h2>' + checklist(["AI answers: whether AI systems mention your business for buyer-style prompts.", "Competitor mentions: which local competitors appear when your business does not.", "Cited sources: what pages, profiles, directories or sources support the answer.", "Google and business profile signals: whether public profile information is consistent and complete.", "Service and location clarity: whether your site clearly explains what you do and where you do it.", "Reviews, citations and entity trust: whether public proof supports your business as a real provider."]) + actions(("See the Sample Report", "/sample-ai-visibility-snapshot/", True), ("View Pricing", "/pricing/", True)), '<p class="eyebrow">Request snapshot</p><h2>Share the details needed to check your public footprint.</h2>' + snapshot_form("Free AI Visibility Snapshot request from audit page", PRIMARY_CTA, "snapshot")),
        section("Output", "What you receive", cards([Card("SUMMARY", "How AI understands you", "A short summary of whether AI systems understand your business."), Card("PROMPTS", "Buyer prompts tested", "Example prompts for your category and service area."), Card("COMPETITORS", "Who appears instead", "Competitors that appear in AI answers or source patterns."), Card("SOURCES", "Trust signals found or missing", "Public sources and trust-signal gaps that may limit visibility."), Card("FIXES", "First-priority fixes", "Practical next steps before deeper SEO, GEO, AEO or content work.")], compact=True)),
        section("Boundaries", "What this is not", checklist(["Not a guarantee of rankings, leads or AI recommendations.", "Not an automated score with no context.", "Not a replacement for technical SEO, content, local profile or review work.", "Not a tactic for manipulating AI Overviews or spamming AI systems.", "Not a claim that any AI platform can be controlled."])),
        section("Next step", "What happens after you submit", '<p>Alex reviews the business details, checks the public signals, and prepares a snapshot or next-step response. If a deeper diagnostic is needed, you will see what should be reviewed before committing to implementation.</p>' + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("See Services", "/services/", True))),
    ],
    faq=[
        ("Is this really a free AI visibility audit?", "Yes. The free snapshot gives you a first diagnostic view of how AI search systems may understand, mention or ignore your business."),
        ("Which AI systems are checked?", "The snapshot can look at systems such as ChatGPT, Gemini, Perplexity, Bing Copilot and Google AI Overviews where relevant."),
        ("Can this guarantee that my business appears in AI answers?", "No. AI systems cannot be controlled. The work improves the clarity, consistency and trust signals those systems may use."),
        ("What should I put in the competitor field?", "Add companies you see in Google results, maps, directories, ads or AI answers. If you are not sure, leave it blank."),
    ],
))

PAGES.append(Page(
    "/sample-ai-visibility-snapshot/",
    "AI Visibility Report Example for Local Business",
    "View a fictional sample AI Visibility Snapshot showing prompts, competitors, sources, missing signals and priority fixes.",
    "AI visibility report example for a local business",
    "Sample report",
    "This fictional sample shows the kind of diagnostic a local business can receive: prompts tested, AI systems checked, competitors mentioned, sources found, missing trust signals and first-priority fixes.",
    priority="0.75",
    schema_type="Article",
    sections=[
        section("Fictional sample", "This is not a client case study", '<p>The business below is fictional. The findings are illustrative so you can understand the format and practical value of the snapshot. Your actual snapshot depends on your website, category, location, competitors and public source footprint.</p>' + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("AI Visibility Audit for Dentists", "/ai-visibility-audit-for-dentists/", True))),
        section("Report sections", "Harbor Bend Dental, fictional example", cards([Card("01", "Business/entity summary", "Mixed public naming, general service clarity, and incomplete emergency-care explanation."), Card("02", "Prompts tested", "Emergency dentist, family dentist, dental implants, Invisalign consultation, and broken-tooth prompts."), Card("03", "AI systems checked", "ChatGPT, Gemini, Perplexity, Bing Copilot and Google AI Overviews where relevant."), Card("04", "Competitors mentioned", "Fictional competitors appeared more often for non-brand prompts."), Card("05", "Sources and citations", "Website, Google Business Profile, review platforms and local directories were reviewed."), Card("06", "Priority fixes", "Dedicated emergency page, name consistency, credential summaries, payment clarity and internal links.")], compact=True)),
        section("Example prompts", "Buyer-style prompts used in the sample", checklist(["Best emergency dentist near Charleston for tooth pain.", "Family dentist in Charleston accepting new patients.", "Dentist for dental implants near me.", "Invisalign consultation Charleston dental clinic.", "Which dentist should I call for a broken tooth in Charleston?"])),
        section("Recommended next step", "Diagnosis before a content campaign", '<p>For the fictional business, the best next step would be a Diagnostic Audit before implementation. The main issue appears to be clarity and trust-signal alignment, not just lack of blog content.</p>' + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("View Pricing", "/pricing/", True))),
    ],
    faq=[
        ("Is this report example based on a real client?", "No. It uses a fictional business so prospects can understand the report format without exposing client data or inventing results."),
        ("Will my snapshot look exactly like this?", "Not exactly. The structure may be similar, but prompts, competitors, sources and recommended fixes depend on your business category and market."),
        ("Why include competitors in the report?", "Competitor mentions show which businesses AI systems may be able to verify more easily for the tested buyer prompts."),
    ],
))

PAGES.append(Page(
    "/services/",
    "AI Search Visibility Services for Local Business",
    "Focused SEO, GEO and AEO services that help AI systems understand, verify and recommend your local business.",
    "AI search visibility services that fix the signals AI can use",
    "Services after the snapshot",
    "AI visibility is not solved by publishing random blog posts. Local businesses need clean technical foundations, clear service pages, consistent entity signals, review proof, citations, and source footprints AI systems can understand.",
    priority="0.9",
    schema_type="ProfessionalService",
    sections=[
        section("System", "A focused system, not an everything-agency menu", '<p>Alex’s work starts with finding the bottleneck. Some businesses need technical cleanup. Others need clearer service pages, stronger local proof, better source consistency, or monitoring across AI answers.</p>' + cards(service_cards)),
        split_section('<p class="eyebrow">Technical foundation</p><h2>Technical SEO and crawl foundation</h2><p>If search engines and AI-connected crawlers cannot access, parse or trust your site structure, the rest of the work sits on weak ground.</p>' + checklist(["Indexability and crawl paths", "Canonical signals", "Internal links", "Metadata and headings", "Sitemap signals", "Template blockers"]), '<p class="eyebrow">Answer-ready pages</p><h2>Service pages that answer real buyer questions</h2><p>Many local service pages are too thin, generic or unclear to answer what buyers and AI systems ask.</p>' + checklist(["Service intent", "Location relevance", "FAQs", "Process explanations", "Proof elements", "Internal links"])),
        split_section('<p class="eyebrow">Entity trust</p><h2>Entity trust and source footprint</h2><p>AI systems need to connect your business name, website, services, people, locations and public references.</p>' + checklist(["Business entity clarity", "Schema", "About/team pages", "Source mentions", "Directory references", "Citation consistency"]), '<p class="eyebrow">Local trust</p><h2>Reviews, citations and local trust signals</h2><p>Your website is not the only source AI systems and search engines may use. Profiles, reviews, directories and third-party citations can all influence how your business is described.</p>' + checklist(["Google Business Profile alignment", "Review themes", "Category clarity", "Local citations", "Service-area signals"])),
        section("Monitoring", "AI visibility monitoring and reporting", '<p>AI answers vary by prompt, system, location context and source availability. Competitive markets need recurring prompt checks, competitor appearance tracking, source-change review and priority reporting.</p>' + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("View Pricing", "/pricing/", True))),
    ],
    faq=[
        ("What are AI search visibility services?", "Focused services that improve how AI systems and search engines can understand, verify and describe your business."),
        ("Do I need all of these services?", "Not always. The snapshot and diagnostic audit identify which issues matter first so the work is not over-scoped."),
        ("Can these services guarantee leads?", "No. The services improve visibility signals and clarity. They do not guarantee rankings, AI mentions or lead volume."),
    ],
))

PAGES.append(Page(
    "/pricing/",
    "AI Visibility Pricing and Packages",
    "Compare free snapshot, diagnostic audit, 90-day AI visibility sprint, and ongoing support options for local businesses.",
    "AI visibility pricing should start with diagnosis",
    "Packages and next steps",
    "You should not buy months of content, SEO or AI search consulting before you know what is broken. Start with a free snapshot, then choose the level of audit or implementation your business actually needs.",
    priority="0.9",
    schema_type="Service",
    hero="pricing",
    sections=[
        section("Packages", "Start small. Fix what matters first.", cards(pricing_cards) + actions((PRIMARY_CTA, "/ai-visibility-audit/?intent=snapshot", False), ("Request Diagnostic Audit", "/ai-visibility-audit/?intent=diagnostic", True)), "alex-native-pricing"),
        section("Scope", "Why pricing depends on the problem", '<p>A single-location plumber with five core services does not need the same scope as a multi-location law firm with dozens of practice pages. The snapshot and diagnostic audit prevent over-scoping.</p>' + checklist(["Scope changes with number of services and locations.", "Competitive markets need more source and page depth.", "Implementation access affects speed and cost.", "Some fixes require content, some require technical cleanup, and some require local trust work."])),
        section("Evidence", "Evidence before bigger SEO/GEO work", cards([Card("01", "Source-backed questions", "We start from what buyers and AI systems need to verify."), Card("02", "Trust signal gaps", "Reviews, profiles, citations and pages are checked before implementation."), Card("03", "Package after diagnosis", "A paid scope should follow the visible bottleneck, not a template retainer.")], compact=True)),
    ],
    faq=[
        ("How much does AI visibility work cost?", "Start with the free snapshot. Diagnostic audits, 90-day sprints and ongoing support depend on site size, market complexity and implementation scope."),
        ("Do I have to buy a sprint after the free snapshot?", "No. The snapshot should stand on its own as a useful diagnostic. Deeper work is optional."),
        ("Does pricing include guaranteed AI mentions or rankings?", "No. The work improves public signals that AI systems and search engines can use, but does not guarantee mentions, rankings or leads."),
    ],
))

# Existing service detail and resource pages, kept concise and visually aligned.
DETAILS = [
    ("/ai-visibility-diagnostic-audit/", "AI Visibility Diagnostic Audit | SEO, GEO & AEO Action Plan", "Get an AI Visibility Diagnostic Audit before spending on SEO or content. Find technical, content, entity, citation and trust gaps across Google and AI search.", "AI Visibility Diagnostic Audit", "Diagnostic", "A paid diagnostic for businesses that need a clear action plan before implementation starts.", ["Technical SEO and indexation", "AI-answer readiness", "Service-page clarity", "Entity and citation consistency", "Competitor/source footprint", "Prioritized next actions"]),
    ("/technical-seo-geo-foundation/", "Technical SEO & GEO Foundation | AI Search Visibility", "Fix crawlability, indexation, schema, internal links and page structure so search engines and AI systems can understand your local service business.", "Technical SEO and GEO Foundation for AI-Visible Websites", "Foundation", "Fix crawlability, indexation, schema, internal links and page clarity before scaling content.", ["Robots, sitemap and canonical cleanup", "Schema and entity clarity", "Internal-linking paths", "Performance and asset cleanup", "Indexation monitoring"]),
    ("/answer-ready-service-pages/", "Answer-Ready Service Pages | AEO & AI Visibility Content", "Turn vague service pages into answer-ready content for buyers and AI search. Improve service definitions, FAQs, internal links, proof and conversion paths.", "Answer-Ready Service Pages for Buyers and AI Search", "Service Pages", "Pages that answer buyer questions and expose clear, extractable service logic for AI search.", ["Clear service definition", "Buyer-question mapping", "Proof and local trust", "FAQ and schema-ready structure", "Internal links to supporting evidence"]),
    ("/entity-trust-source-intelligence/", "Entity Trust & Source Intelligence | AI Visibility Consulting", "Strengthen entity trust, citations, reviews, schema and source signals so search engines and AI systems can verify your business and services.", "Entity, Trust and Source Intelligence for AI Recommendations", "Trust", "Make the business easier to identify, verify, compare and recommend.", ["Business entity clarity", "Citations and profiles", "Reviews and reputation signals", "Third-party source proof", "Competitor trust gaps"]),
    ("/ai-visibility-source-footprint/", "AI Visibility Source Footprint | Alex Yarosh", "Map the external sources, citations, profiles and proof signals that influence AI search visibility and recommendations.", "AI search looks beyond your website", "Source Footprint", "Map what AI systems can verify about your business beyond your own website.", ["Website evidence", "Social and UGC signals", "Trust proof", "Research trail", "Monitoring and risk control"]),
]
for path, title, desc, h1, eyebrow, deck, items in DETAILS:
    PAGES.append(Page(path, title, desc, h1, eyebrow, deck, priority="0.75", schema_type="Service", sections=[
        section("Scope", "Built to fix a specific visibility layer", checklist(items) + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("View Pricing", "/pricing/", True))),
        section("System", "How it fits with Base2026", '<p>This page is part of the Alex Yarosh service layer. Base2026 remains the public research layer; the audit path turns evidence into business-specific priorities.</p>' + cards(service_cards[:3], compact=True)),
    ]))

RESOURCES = [
    ("/what-is-ai-search-visibility/", "What Is AI Search Visibility for Local Businesses?", "AI Search Visibility means your business can be found, understood and recommended by AI-powered search tools such as ChatGPT, AI Overviews, Gemini and Perplexity.", "What Is AI Search Visibility for Local Businesses?", "Resource", "AI Search Visibility combines SEO, GEO, AEO, structured content, entity trust and external validation."),
    ("/why-chatgpt-does-not-recommend-your-business/", "Why ChatGPT Does Not Recommend Your Business", "Common reasons ChatGPT and AI search systems do not recommend a local business: unclear services, weak trust signals, thin pages and missing source footprint.", "Why ChatGPT Does Not Recommend Your Business", "Resource", "Usually the problem is not one magic ranking factor. It is a weak set of signals."),
    ("/when-to-rebuild-website-for-seo/", "When Should a Business Rebuild Its Website for SEO?", "A business should rebuild its website for SEO when the current site blocks crawlability, clarity, conversion, content structure or AI-search visibility.", "When Should a Business Rebuild Its Website for SEO?", "Resource", "Do not rebuild for aesthetics alone. Rebuild when the site blocks growth."),
]
for path, title, desc, h1, eyebrow, deck in RESOURCES:
    PAGES.append(Page(path, title, desc, h1, eyebrow, deck, priority="0.65", sections=[section("Next step", "Turn the idea into a visibility check", '<p>Use this as a plain-language starting point, then move into the snapshot or diagnostic path when the business needs specific recommendations.</p>' + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("Explore Base2026 pages", "/knowledge/ai-visibility-pages/", True)))]))

# Vertical demand pages
VERTICALS = [
    {
        "path": "/ai-visibility-audit-for-dentists/",
        "title": "AI Visibility Audit for Dentists",
        "description": "Check if ChatGPT, Gemini, Perplexity and Google AI can understand and recommend your dental clinic.",
        "h1": "AI visibility audit for dentists",
        "eyebrow": "For dentists and dental clinics",
        "deck": "Patients are asking AI systems where to go for tooth pain, cosmetic work, implants, family care and second opinions. Your clinic needs public signals that make services, location, reviews, payment details and dentist credentials easy to verify.",
        "industry": "Dental clinic",
        "problem": "Dental AI search is built from public proof",
        "problem_body": "AI systems may pull from your website, Google Business Profile, reviews, directories, schema, health-related explanations and third-party sources. If those signals are incomplete or inconsistent, your clinic may be harder to recommend for specific patient needs.",
        "prompts": ["Best dentist near me for emergency tooth pain.", "Dentist in [CITY] accepting new patients.", "Who should I call for a broken tooth near [CITY]?", "Best dental clinic for implants in [CITY].", "Family dentist near me that takes my insurance."],
        "signals": ["Google Business Profile categories, services, hours, photos and location consistency.", "Reviews that mention treatment types, comfort, emergency care, staff and patient experience.", "Clear pages for emergency dentistry, implants, cosmetic dentistry, family dentistry or other priority procedures.", "Insurance, financing, payment and appointment information when accurate.", "Dentist and team credentials, licenses, education and specialty details."],
        "fixes": ["Improve high-intent procedure pages.", "Add emergency dental care details if offered.", "Connect dentist bios to the services they provide.", "Make insurance and payment details easier to find.", "Align Google Business Profile services with website pages."],
        "schema": "Dentist",
    },
    {
        "path": "/ai-visibility-audit-for-roofing-companies/",
        "title": "AI Visibility Audit for Roofers",
        "description": "Check if AI search can find and verify your roofing company for repair, replacement, storm and inspection prompts.",
        "h1": "AI visibility audit for roofers",
        "eyebrow": "For roofing companies",
        "deck": "Homeowners are asking AI systems who to call for roof repair, hail damage, leaks, inspections, replacement and emergency help. If your service area, proof, licenses, reviews and project signals are unclear, AI systems may surface competitors instead.",
        "industry": "Roofing company",
        "problem": "Roofing buyers ask urgent, specific questions",
        "problem_body": "Roofing searches often start with a problem: a leak, storm damage, missing shingles, insurance questions or a replacement estimate. AI systems need clear service pages and trust signals to understand which company is relevant.",
        "prompts": ["Best roofing company near me for storm damage.", "Roof repair company in [CITY] for an active leak.", "Who should I call for hail damage roof inspection in [CITY]?", "Best roof replacement contractor near [SERVICE AREA].", "Roofing company that offers financing in [CITY]."],
        "signals": ["Clear service areas, cities, counties and neighborhoods served.", "Separate pages for roof repair, replacement, storm damage, hail damage and inspections if offered.", "Reviews that mention responsiveness, workmanship, cleanup, insurance help and project outcomes.", "Project proof such as photos, neighborhoods, roof types and before/after examples where allowed.", "License, insurance, certification, manufacturer and warranty information where accurate."],
        "fixes": ["Build or improve storm, hail, leak, inspection and replacement pages.", "Add specific service-area language to high-value pages.", "Strengthen project proof with real examples.", "Align Google Business Profile services with website pages.", "Clarify license, insurance, warranties and financing where applicable."],
        "schema": "RoofingContractor",
    },
    {
        "path": "/ai-visibility-audit-for-hvac-companies/",
        "title": "AI Visibility Audit for HVAC Companies",
        "description": "Check whether AI search can understand and recommend your HVAC company for repair, replacement, maintenance and emergency prompts.",
        "h1": "AI visibility audit for HVAC companies",
        "eyebrow": "For HVAC contractors",
        "deck": "HVAC buyers ask AI systems urgent and seasonal questions: who fixes AC today, who installs heat pumps, who services furnaces, who offers maintenance and who serves their neighborhood.",
        "industry": "HVAC contractor",
        "problem": "HVAC visibility changes by season and service need",
        "problem_body": "A buyer with a broken AC unit is not asking the same question as a homeowner comparing heat pump installation. AI systems need clear service pages, service-area signals, brand expertise, emergency details and reviews.",
        "prompts": ["Best HVAC company near me for AC repair.", "Emergency furnace repair in [CITY].", "Who installs heat pumps near [SERVICE AREA]?", "HVAC company with maintenance plans in [CITY].", "Best local HVAC contractor for replacing an old AC unit."],
        "signals": ["Emergency service details if offered.", "Clear pages for AC repair, AC installation, furnace repair, heat pumps, maintenance and indoor air quality where applicable.", "Brands served, certifications, licenses and technician credentials where accurate.", "Financing options for replacements or installations if offered.", "Reviews that mention responsiveness, professionalism, replacement, maintenance and service quality."],
        "fixes": ["Separate high-intent repair, install and maintenance pages.", "Clarify service area and emergency availability.", "Add brand, certification, financing and technician details where accurate.", "Reflect review themes on service pages.", "Improve internal links from seasonal pages to core services."],
        "schema": "HVACBusiness",
    },
    {
        "path": "/ai-visibility-audit-for-plumbing-companies/",
        "title": "AI Visibility Audit for Plumbers",
        "description": "Check if AI search can find and verify your plumbing company for emergency, drain, sewer and water heater prompts.",
        "h1": "AI visibility audit for plumbers",
        "eyebrow": "For plumbers and plumbing companies",
        "deck": "Plumbing buyers often need help now: burst pipe, clogged drain, broken water heater, sewer backup, leak detection or emergency service. AI systems need clear pages, proof, reviews, licenses, service areas and estimate clarity.",
        "industry": "Plumbing company",
        "problem": "Plumbing searches are urgent and service-specific",
        "problem_body": "A homeowner searching for emergency plumbing is not looking for a generic contractor page. AI systems need clear signals for the exact issue: drains, sewers, water heaters, leaks, toilets, fixtures or emergency response.",
        "prompts": ["Emergency plumber near me for a burst pipe.", "Best drain cleaning company in [CITY].", "Who fixes sewer line backups near [SERVICE AREA]?", "Water heater repair plumber near me.", "Licensed plumber in [CITY] with clear estimate options."],
        "signals": ["Emergency plumbing availability if offered.", "Separate pages for drain cleaning, sewer repair, water heater repair, leak detection and fixture installation where applicable.", "Reviews that mention response, cleanliness, professionalism, pricing clarity and resolved problems.", "Service-area pages for priority cities and neighborhoods.", "License information, business credentials and estimate clarity where accurate."],
        "fixes": ["Improve emergency plumbing page if offered.", "Build or strengthen drain, sewer, leak and water heater pages.", "Add service-area clarity to high-intent pages.", "Align Google Business Profile services with website pages.", "Clarify license, response and estimate claims only where confirmed."],
        "schema": "Plumber",
    },
    {
        "path": "/ai-visibility-audit-for-law-firms/",
        "title": "AI Visibility Audit for Law Firms",
        "description": "Check if AI search can understand and mention your law firm for practice area, attorney, location and trust prompts.",
        "h1": "AI visibility audit for law firms",
        "eyebrow": "For law firms",
        "deck": "Legal buyers ask AI systems who handles their type of matter, which attorneys serve their area, and what sources support trust. Your firm needs clear practice-area pages, attorney entity signals, local citations and careful claims.",
        "industry": "Law firm",
        "problem": "Legal visibility requires clarity and caution",
        "problem_body": "AI systems may summarize practice areas, attorneys, locations, reviews, directories, citations and public sources. For law firms, the copy must be specific enough to be useful but careful enough to avoid unsupported claims or outcome promises.",
        "prompts": ["Best personal injury lawyer near me after a car accident.", "Family law attorney in [CITY] for child custody questions.", "Business lawyer near [SERVICE AREA] for contract review.", "Criminal defense attorney in [CITY] for a first offense.", "Estate planning lawyer near me for wills and trusts."],
        "signals": ["Clear practice-area pages with jurisdiction, matter type, process and next-step information.", "Attorney bio/entity clarity, including names, roles, admissions, education and relevant experience where confirmed.", "Reviews or testimonials where allowed by applicable rules.", "Local citations, directory profiles, bar-related listings and firm profiles.", "Schema and entity consistency across firm, attorney, practice area and location pages."],
        "fixes": ["Improve priority practice-area pages.", "Connect attorney bios to relevant services and locations.", "Align firm name, address, phone and profiles across public sources.", "Review testimonial and case-result language for compliance.", "Add schema and internal links that clarify firm, attorney, location and practice-area relationships."],
        "schema": "LegalService",
    },
]

for v in VERTICALS:
    PAGES.append(Page(
        v["path"], v["title"], v["description"], v["h1"], v["eyebrow"], v["deck"],
        priority="0.72",
        schema_type=v["schema"],
        sections=[
            split_section(f'<p class="eyebrow">Problem</p><h2>{escape(v["problem"])}</h2><p>{escape(v["problem_body"])}</p>' + checklist(v["prompts"]), '<p class="eyebrow">Request snapshot</p><h2>Check this market before more spend.</h2>' + snapshot_form(f'{v["title"]} request', PRIMARY_CTA, "snapshot", v["industry"])),
            section("Trust signals", f'{v["industry"]} trust signals AI systems may look for', checklist(v["signals"])),
            section("Findings", f'What the snapshot can show a {v["industry"].lower()}', cards([Card("MENTIONS", "Whether your business appears", "Do AI systems mention you for high-intent service prompts?"), Card("COMPETITORS", "Who appears instead", "Which competitors show up when your business does not?"), Card("PAGES", "Whether pages match intent", "Do your service pages match how buyers ask for help?"), Card("PROOF", "Whether trust signals support you", "Do reviews, profiles, citations and credentials reinforce the right services?")], compact=True)),
            section("Fixes", "Common fixes after the snapshot", checklist(v["fixes"]) + actions((PRIMARY_CTA, "/ai-visibility-audit/", False), ("See Services", "/services/", True))),
        ],
        faq=[
            (f'What is an {v["h1"]}?', f'It checks whether AI systems can understand, verify and mention your {v["industry"].lower()} for buyer-style prompts about services, locations, competitors and trust signals.'),
            ("Can this guarantee AI recommendations?", "No. The audit identifies visibility gaps and priority fixes. It does not guarantee rankings, AI mentions, leads or revenue."),
            ("What should I include when requesting a snapshot?", "Include your website, priority services, service areas, known competitors and any compliance or factual limits around claims."),
        ],
    ))

PAGES.append(Page(
    "/about/",
    "About Alex Yarosh | AI Visibility Consultant",
    "Alex Yarosh bridges technical development and marketing operations to help local service businesses build verifiable visibility systems for AI search.",
    "I do not sell marketing noise. I fix visibility systems.",
    "About Alex Yarosh",
    "With over 15 years of experience bridging the gap between deep technical development and marketing operations, I help local service businesses establish a verifiable layer of truth for AI search systems.",
    priority="0.8",
    hero="about",
    schema_type="Person",
    sections=[],
))

PAGES.append(Page("/privacy-policy/", "Privacy Policy | Alex Yarosh", "Privacy policy for Alex Yarosh and Base2026 visibility services.", "Privacy Policy", "Legal", "Basic privacy information for snapshot requests and website usage.", priority="0.3", sections=[section("Privacy", "Information we collect", "<p>When you submit a form, we collect the information you provide so we can review your website and respond to your request. We do not sell personal information. Analytics and cookies may be used to understand site performance and improve the service.</p>")]))
PAGES.append(Page("/thank-you-ai-visibility-audit/", "Thank You | AI Visibility Request", "Thank you for requesting an AI visibility snapshot.", "Request received", "Thank you", "We received your request. The next step is a quick review of your website and market.", priority="0.0", robots="noindex,follow", include_sitemap=False, sections=[section("Next", "Explore the visibility library while you wait", actions(("Explore AI Visibility Lab", "/knowledge/ai-visibility-pages/", False), ("Back to Services", "/services/", True)))]))

CSS = """
/* Alex native pages using the Base2026 shell. Scoped only to body.alex-native-site. */
body.alex-native-site .app-shell { max-width: 1180px; }
body.alex-native-site .site-header__nav { gap: 10px; }
body.alex-native-site .alex-native-hero { margin-top: 18px; background: radial-gradient(circle at 18% 18%, rgba(255,255,255,.16), transparent 34%), repeating-linear-gradient(135deg, rgba(17,24,32,.045) 0, rgba(17,24,32,.045) 1px, transparent 1px, transparent 9px), linear-gradient(90deg, #d96313 0%, #c6530b 58%, #994008 100%); }
body.alex-native-site .alex-native-hero .b26-founder-quote span { max-width: 780px; font-size: clamp(42px, 7vw, 92px); }
body.alex-native-site .alex-native-hero-eyebrow { color: rgba(17,24,32,.86); margin-bottom: 10px; }
body.alex-native-site .alex-native-intro { margin-top: 18px; }
body.alex-native-site .alex-native-intro p { max-width: 860px; }
body.alex-native-site .alex-native-actions { margin-top: 18px; flex-wrap: wrap; }
body.alex-native-site .alex-native-section { padding: clamp(24px, 4vw, 44px); }
body.alex-native-site .alex-native-split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, .74fr); gap: clamp(18px, 4vw, 42px); align-items: start; }
body.alex-native-site .alex-native-side { border: 1px solid rgba(18,26,31,.14); border-radius: 8px; background: rgba(255,250,240,.92); padding: clamp(18px, 3vw, 28px); box-shadow: 0 10px 26px rgba(17,24,32,.07); }
body.alex-native-site .alex-native-card p { margin: 0; color: var(--ay-muted); font-size: 14px; }
body.alex-native-site .alex-native-card.price-free { background: #fffaf0; }
body.alex-native-site .alex-native-card.price-paid { background: #fff4e7; border-color: rgba(200,79,7,.35); }
body.alex-native-site .alex-native-card.price-sprint { background: #f8ead9; }
body.alex-native-site .alex-native-card.price-monthly { background: #eef1e7; }
body.alex-native-site .alex-native-checklist { display: grid; gap: 10px; margin: 16px 0 0; padding: 0; list-style: none; }
body.alex-native-site .alex-native-checklist li { position: relative; padding-left: 26px; }
body.alex-native-site .alex-native-checklist li::before { content: "✓"; position: absolute; left: 0; top: 0; color: var(--ay-orange); font-weight: 900; }
body.alex-native-site .alex-native-form { display: grid; gap: 12px; }
body.alex-native-site .alex-native-form label { display: grid; gap: 6px; font-weight: 800; color: var(--ay-text); }
body.alex-native-site .alex-native-form label span { color: var(--ay-muted); font-weight: 500; font-size: 13px; }
body.alex-native-site .alex-native-form input, body.alex-native-site .alex-native-form textarea { width: 100%; border: 1px solid rgba(18,26,31,.18); border-radius: 6px; background: #fffdf8; padding: 12px 13px; font: inherit; }
body.alex-native-site .alex-native-form textarea { min-height: 96px; resize: vertical; }
body.alex-native-site .alex-native-form button { border: 1px solid var(--ay-orange); border-radius: 8px; background: var(--ay-orange); box-shadow: none; color: #fff; font-weight: 900; padding: 12px 14px; cursor: pointer; }
body.alex-native-site .alex-native-pricing .ai-pages-grid-main { grid-template-columns: repeat(4, minmax(0,1fr)); }
body.alex-native-site .alex-native-faq { display: grid; gap: 12px; }
body.alex-native-site .alex-native-faq details { border: 1px solid rgba(18,26,31,.14); border-radius: 8px; background: rgba(255,250,240,.92); padding: 16px 18px; }
body.alex-native-site .alex-native-faq summary { cursor: pointer; font-weight: 900; color: var(--ay-text); }
body.alex-native-site .alex-native-faq p { margin: 10px 0 0; color: var(--ay-muted); }
body.alex-native-site .ay-actions a,
body.alex-native-site .site-header a,
body.alex-native-site .alex-native-intro a { text-decoration: none !important; }
body.alex-native-site .alex-native-actions .ay-button { background: var(--ay-orange) !important; border-color: var(--ay-orange) !important; color: #fff !important; box-shadow: none !important; border-radius: 8px !important; }
body.alex-native-site .alex-native-actions .ay-button-secondary { color: var(--ay-text) !important; }
body.alex-native-site .alex-native-card { text-decoration: none !important; }
body.alex-native-site .alex-native-card strong,
body.alex-native-site .alex-native-card span,
body.alex-native-site .alex-native-card p { text-decoration: none !important; }
body.alex-native-site .alex-native-hero .b26-about-hero-copy { position: relative; z-index: 2; }
body.alex-native-site .alex-native-hero .b26-hero-figure { z-index: 1; opacity: .72; transform: translateX(8%); }
body.alex-native-site .alex-native-hero .b26-founder-quote { max-width: min(700px, 64%); }
@media (max-width: 980px) { body.alex-native-site .alex-native-split { grid-template-columns: 1fr; } body.alex-native-site .alex-native-pricing .ai-pages-grid-main { grid-template-columns: repeat(2, minmax(0,1fr)); } body.alex-native-site .alex-native-hero .b26-founder-quote { max-width: 100%; } body.alex-native-site .alex-native-hero .b26-hero-figure { opacity: .55; } }
body.alex-native-site.alex-home-page .alex-home-compact-form label:first-of-type,
body.alex-native-site.alex-home-page .alex-home-compact-form button { grid-column: 1 / -1; }
body.alex-native-site.alex-home-page .alex-home-compact-form label span { max-width: 32rem; }
body.alex-native-site.alex-home-page .alex-core-stitch-card-grid .alex-core-stitch-card,
body.alex-native-site.alex-home-page .alex-core-stitch-card-grid .alex-native-card {
  border-left: 4px solid rgba(200,79,7,.42);
  background: linear-gradient(135deg, rgba(255,250,240,.98), rgba(255,246,232,.94));
  box-shadow: 0 18px 42px rgba(17,24,32,.075);
}
body.alex-native-site.alex-home-page .alex-core-stitch-card-grid .alex-core-stitch-card span,
body.alex-native-site.alex-home-page .alex-core-stitch-card-grid .alex-native-card span {
  display: inline-flex;
  width: auto;
  min-width: 0;
  height: auto;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #a83900;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: .12em;
  text-transform: uppercase;
}
@media (max-width: 620px) { body.alex-native-site .alex-native-pricing .ai-pages-grid-main { grid-template-columns: 1fr; } body.alex-native-site .alex-native-hero .b26-founder-quote span { font-size: clamp(34px, 15vw, 64px); } }

/* alex-home-route-a-rescue-20260704a
   Route A: editorial conversion system for Alex home. Scoped to Home only. */
body.alex-native-site.alex-home-page .app-shell { max-width: min(1088px, calc(100% - clamp(72px, 12vw, 150px))) !important; margin-inline: auto !important; }
body.alex-native-site.alex-home-page .alex-native-page { padding-top: clamp(22px, 3vw, 36px) !important; }
body.alex-native-site.alex-home-page .alex-native-hero {
  display: grid !important;
  min-height: clamp(300px, 24vw, 342px) !important;
  margin-top: clamp(8px, 1.5vw, 14px) !important;
  margin-bottom: clamp(26px, 3.5vw, 42px) !important;
  padding: clamp(34px, 4.3vw, 48px) clamp(36px, 5.4vw, 58px) !important;
  border-radius: 18px !important;
  grid-template-columns: minmax(0, .59fr) minmax(285px, .41fr) !important;
  gap: clamp(22px, 4.2vw, 52px) !important;
  align-items: center !important;
  box-shadow: 0 28px 80px rgba(17,24,32,.13) !important;
}
body.alex-native-site.alex-home-page .alex-native-hero .b26-founder-quote,
body.alex-native-site.alex-home-page .alex-native-hero h1.b26-founder-quote { max-width: 680px !important; margin: 0 !important; }
body.alex-native-site.alex-home-page .alex-native-hero .b26-founder-quote span { max-width: 680px !important; font-size: clamp(38px, 5.45vw, 68px) !important; line-height: .88 !important; letter-spacing: -.055em !important; }
body.alex-native-site.alex-home-page .alex-native-hero .b26-founder-support { max-width: 52ch !important; margin-top: clamp(16px, 2vw, 22px) !important; font-size: clamp(15.5px, 1.22vw, 17.5px) !important; line-height: 1.46 !important; }
body.alex-native-site.alex-home-page .alex-native-hero .b26-hero-figure,
body.alex-native-site.alex-home-page .alex-native-hero .ay-hero-figure { height: clamp(260px, 24vw, 328px) !important; max-height: 92% !important; transform: translateX(0) !important; filter: drop-shadow(-18px 24px 28px rgba(17,17,17,.24)) !important; }
body.alex-native-site.alex-home-page .alex-native-hero .b26-hero-person,
body.alex-native-site.alex-home-page .alex-native-hero .ay-hero-person { height: 100% !important; width: auto !important; max-height: 100% !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge {
  display: grid !important;
  grid-template-columns: minmax(210px, .48fr) minmax(0, 1fr) auto !important;
  gap: clamp(18px, 3vw, 34px) !important;
  align-items: center !important;
  margin: 0 0 clamp(34px, 4.6vw, 56px) !important;
  padding: clamp(20px, 2.8vw, 30px) !important;
  border-radius: 18px !important;
  border: 1px solid rgba(18,26,31,.14) !important;
  border-left: 6px solid #df650e !important;
  background: linear-gradient(135deg, #fffdf8 0%, #fff6e8 100%) !important;
  box-shadow: 0 16px 44px rgba(17,24,32,.075) !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge .eyebrow,
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge h2,
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge p { margin: 0 !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge h2 { max-width: 360px; color: #1c1b1b; font-size: clamp(25px, 2.45vw, 34px) !important; line-height: 1.02; letter-spacing: -.035em; }
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge > p { max-width: 58ch; color: #444748; font-size: clamp(15.5px, 1.28vw, 18px); line-height: 1.52; }
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge .alex-native-actions { justify-content: flex-end; margin-top: 0 !important; white-space: nowrap; }
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge .alex-native-actions .ay-button,
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form button { background: #df650e !important; border-color: #111820 !important; color: #111820 !important; box-shadow: 3px 3px 0 #111820 !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry { grid-template-columns: minmax(0, 1.06fr) minmax(340px, .82fr) !important; gap: clamp(34px, 5vw, 58px) !important; padding-bottom: clamp(48px, 6vw, 70px) !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry > div:first-child { border-right: 0 !important; padding-right: 0 !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-native-checklist { margin-top: 22px !important; gap: 12px !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-stitch-form-card { align-self: start !important; padding: clamp(26px, 3.2vw, 34px) !important; border: 1px solid rgba(18,26,31,.16) !important; border-radius: 20px !important; background: radial-gradient(circle at 0 0, rgba(223,101,14,.13), transparent 36%), linear-gradient(135deg, rgba(255,253,248,.98), rgba(255,246,232,.96)) !important; box-shadow: 0 26px 64px rgba(17,24,32,.12) !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-form-head { margin-bottom: 18px !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-form-head h3 { font-size: clamp(28px, 3vw, 38px) !important; margin: 0 0 6px; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-form-head p { margin: 0; color: #5d6162; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form { grid-template-columns: 1fr !important; gap: 14px !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form label:first-of-type,
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form button { grid-column: 1 / -1 !important; }
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form input { min-height: 46px !important; border-radius: 10px !important; background: rgba(255,255,255,.86) !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-repair { padding: clamp(24px, 4vw, 44px) 0 clamp(52px, 7vw, 82px) !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-section-head { max-width: 760px !important; margin-bottom: clamp(22px, 3vw, 34px) !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-section-head .eyebrow { margin: 0 0 10px !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-section-head h2 { margin: 0 !important; color: #1c1b1b !important; font-size: clamp(32px, 4vw, 48px) !important; line-height: 1.02 !important; letter-spacing: -.045em !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-repair > p { max-width: 760px !important; margin: 0 0 clamp(24px, 3vw, 34px) !important; color: #444748; font-size: clamp(16px, 1.35vw, 19px); line-height: 1.62; }
body.alex-native-site.alex-home-page .alex-core-stitch-card-grid { display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)) !important; gap: clamp(14px, 1.7vw, 20px) !important; border: 0 !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-card { display: block !important; min-width: 0 !important; padding: clamp(24px, 3vw, 32px) !important; text-decoration: none !important; }
body.alex-native-site.alex-home-page .alex-core-stitch-card strong { display: block !important; margin: 6px 0 6px !important; color: #1c1b1b !important; font-size: clamp(18px, 2vw, 23px); line-height: 1.08; }
body.alex-native-site.alex-home-page .alex-core-stitch-card p { margin: 0 !important; color: #555; line-height: 1.55; }
body.alex-native-site.alex-home-page .alex-home-proof-grid .alex-core-stitch-card { position: relative !important; min-height: 178px !important; border: 1px solid rgba(18,26,31,.12) !important; border-left: 0 !important; border-radius: 16px !important; background: #fffdf8 !important; box-shadow: 0 14px 36px rgba(17,24,32,.055) !important; }
body.alex-native-site.alex-home-page .alex-home-proof-grid .alex-core-stitch-card::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 5px; border-radius: 16px 0 0 16px; background: #df650e; }
body.alex-native-site.alex-home-page .alex-home-proof-grid .alex-core-stitch-card span { display: none !important; }
body.alex-native-site.alex-home-page .alex-home-service-grid a.alex-core-stitch-card { position: relative !important; min-height: 190px !important; border: 1px solid rgba(18,26,31,.16) !important; border-left: 4px solid #111820 !important; border-radius: 16px !important; background: linear-gradient(135deg, #fffaf0, #fff3df) !important; box-shadow: 0 18px 48px rgba(17,24,32,.085) !important; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important; }
body.alex-native-site.alex-home-page .alex-home-service-grid a.alex-core-stitch-card::after { content: "Open →"; display: inline-flex; margin-top: 18px; color: #a83900; font-weight: 900; font-size: 13px; letter-spacing: .04em; text-transform: uppercase; }
body.alex-native-site.alex-home-page .alex-home-service-grid a.alex-core-stitch-card:hover { transform: translateY(-3px) !important; box-shadow: 0 26px 64px rgba(17,24,32,.13) !important; border-color: rgba(17,24,32,.28) !important; }
body.alex-native-site.alex-home-page .alex-home-base-grid a.alex-core-stitch-card { border-radius: 16px !important; border: 1px solid rgba(61,80,51,.22) !important; border-left: 4px solid #607348 !important; background: linear-gradient(135deg, #f7f3e8, #eef1e7) !important; box-shadow: 0 16px 42px rgba(61,80,51,.09) !important; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important; }
body.alex-native-site.alex-home-page .alex-home-base-grid a.alex-core-stitch-card::after { content: "Open evidence →"; display: inline-flex; margin-top: 16px; color: #607348; font-weight: 900; font-size: 13px; letter-spacing: .04em; text-transform: uppercase; }
body.alex-native-site.alex-home-page .alex-home-base-grid a.alex-core-stitch-card:hover { transform: translateY(-3px) !important; box-shadow: 0 24px 58px rgba(61,80,51,.14) !important; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion { display: grid; gap: 12px; max-width: 900px; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion details { border: 1px solid rgba(18,26,31,.14); border-radius: 16px; background: #fffdf8; box-shadow: 0 12px 32px rgba(17,24,32,.055); overflow: hidden; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary { cursor: pointer; padding: 20px 24px; color: #1c1b1b; font-weight: 900; list-style: none; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary::-webkit-details-marker { display: none; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary::after { content: "+"; float: right; color: #df650e; font-weight: 900; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion details[open] summary::after { content: "–"; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion p { margin: 0 !important; padding: 0 24px 22px; color: #444748; line-height: 1.62; }
@media (max-width: 980px) { body.alex-native-site.alex-home-page .app-shell { max-width: calc(100% - 36px) !important; } body.alex-native-site.alex-home-page .alex-native-hero, body.alex-native-site.alex-home-page .alex-home-snapshot-entry, body.alex-native-site.alex-home-page .alex-home-snapshot-bridge { grid-template-columns: 1fr !important; } body.alex-native-site.alex-home-page .alex-native-hero .b26-hero-figure, body.alex-native-site.alex-home-page .alex-native-hero .ay-hero-figure { max-width: min(420px, 90%) !important; justify-self: center !important; } }
@media (max-width: 720px) { body.alex-native-site.alex-home-page .alex-core-stitch-card-grid { grid-template-columns: 1fr !important; } body.alex-native-site.alex-home-page .alex-home-proof-grid .alex-core-stitch-card, body.alex-native-site.alex-home-page .alex-home-service-grid a.alex-core-stitch-card { min-height: 0 !important; } }
@media (max-width: 620px) { body.alex-native-site.alex-home-page .app-shell { max-width: calc(100% - 28px) !important; } body.alex-native-site.alex-home-page .alex-native-hero { padding: 28px 22px !important; border-radius: 16px !important; } body.alex-native-site.alex-home-page .alex-native-hero .b26-founder-quote span { font-size: clamp(34px, 13.5vw, 58px) !important; } body.alex-native-site.alex-home-page .alex-home-snapshot-bridge, body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-stitch-form-card, body.alex-native-site.alex-home-page .alex-home-proof-grid .alex-core-stitch-card, body.alex-native-site.alex-home-page .alex-home-service-grid a.alex-core-stitch-card, body.alex-native-site.alex-home-page .alex-home-base-grid a.alex-core-stitch-card { border-radius: 14px !important; } }

/* alex-home-clean-text-20260704a
   Correction pass: no decorative grids on Home; text-first sections, one color system. */
body.alex-native-site.alex-home-page { --ay-orange: #c84f07; --ay-orange-hover: #ef6b13; --ay-text: #111820; --ay-muted: #5f6a72; }
body.alex-native-site.alex-home-page .site-header__cta,
body.alex-native-site.alex-home-page .ay-button,
body.alex-native-site.alex-home-page .alex-native-form button {
  background: var(--ay-orange) !important;
  border: 1px solid var(--ay-orange) !important;
  color: #fff !important;
  box-shadow: none !important;
  border-radius: 8px !important;
}
body.alex-native-site.alex-home-page .ay-button:hover,
body.alex-native-site.alex-home-page .alex-native-form button:hover { background: var(--ay-orange-hover) !important; border-color: var(--ay-orange-hover) !important; color: #fff !important; }
body.alex-native-site.alex-home-page .ay-button-secondary,
body.alex-native-site.alex-home-page .alex-native-actions .ay-button-secondary {
  background: transparent !important;
  border: 1px solid rgba(17,24,32,.18) !important;
  color: var(--ay-text) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-native-actions .ay-button-secondary {
  border-color: transparent !important;
  background: transparent !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  color: var(--ay-text) !important;
  text-decoration: underline !important;
  text-underline-offset: 3px;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge {
  border-radius: 14px !important;
  border: 1px solid rgba(18,26,31,.12) !important;
  border-left: 4px solid var(--ay-orange) !important;
  background: #fffaf0 !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge .alex-native-actions .ay-button,
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form button {
  background: var(--ay-orange) !important;
  border-color: var(--ay-orange) !important;
  color: #fff !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-bridge .alex-native-actions .ay-button:hover,
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form button:hover {
  background: var(--ay-orange-hover) !important;
  border-color: var(--ay-orange-hover) !important;
  color: #fff !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-entry {
  border-top: 1px solid rgba(18,26,31,.10) !important;
  padding-top: clamp(32px, 4vw, 48px) !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-services-stitch-form-card {
  border-radius: 14px !important;
  border: 1px solid rgba(18,26,31,.14) !important;
  background: #fffaf0 !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-entry .alex-home-compact-form input {
  border-radius: 8px !important;
  background: #fffdf8 !important;
}
body.alex-native-site.alex-home-page .alex-home-text-section {
  display: block !important;
  padding: clamp(44px, 5vw, 64px) clamp(36px, 5vw, 58px) !important;
  margin: 0 !important;
  border-top: 1px solid rgba(18,26,31,.12) !important;
  border-right: 0 !important;
  border-bottom: 0 !important;
  border-left: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-text-section .alex-core-stitch-section-head {
  max-width: 760px !important;
  margin: 0 0 clamp(18px, 2.4vw, 28px) !important;
}
body.alex-native-site.alex-home-page .alex-home-text-section .alex-core-stitch-section-head h2 {
  font-size: clamp(30px, 3.6vw, 44px) !important;
  line-height: 1.05 !important;
}
body.alex-native-site.alex-home-page .alex-home-text-flow {
  max-width: 820px;
  color: var(--ay-text);
}
body.alex-native-site.alex-home-page .alex-home-text-flow p {
  max-width: 760px !important;
  margin: 0 0 18px !important;
  color: #3f474c !important;
  font-size: clamp(16px, 1.25vw, 18px);
  line-height: 1.66;
}
body.alex-native-site.alex-home-page .alex-home-text-flow h3 {
  margin: 28px 0 7px !important;
  color: var(--ay-text) !important;
  font-size: clamp(19px, 1.55vw, 22px);
  line-height: 1.18;
  letter-spacing: -.012em;
}
body.alex-native-site.alex-home-page .alex-home-link-list {
  display: grid;
  gap: 12px;
  margin: 20px 0 0 !important;
  padding-left: 1.15rem !important;
  color: #3f474c;
  font-size: clamp(16px, 1.2vw, 18px);
  line-height: 1.62;
}
body.alex-native-site.alex-home-page .alex-home-link-list li { padding-left: .2rem; }
body.alex-native-site.alex-home-page .alex-home-link-list a,
body.alex-native-site.alex-home-page .alex-home-inline-links a {
  color: var(--ay-text) !important;
  font-weight: 850;
  text-decoration: underline !important;
  text-decoration-color: rgba(200,79,7,.45) !important;
  text-underline-offset: 3px;
}
body.alex-native-site.alex-home-page .alex-home-inline-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-top: 22px !important;
  font-weight: 800;
}
body.alex-native-site.alex-home-page .alex-home-inline-links span { color: rgba(17,24,32,.35); }
body.alex-native-site.alex-home-page .alex-home-base2026-section,
body.alex-native-site.alex-home-page .alex-home-base2026-section * {
  --ay-accent: var(--ay-orange) !important;
}
body.alex-native-site.alex-home-page .alex-home-faq-accordion {
  max-width: 820px !important;
  gap: 0 !important;
  border-top: 1px solid rgba(18,26,31,.14);
}
body.alex-native-site.alex-home-page .alex-home-faq-accordion details {
  border: 0 !important;
  border-bottom: 1px solid rgba(18,26,31,.14) !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary {
  padding: 18px 0 !important;
  color: var(--ay-text) !important;
}
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary::after { color: var(--ay-orange) !important; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion p {
  padding: 0 0 20px !important;
  color: #3f474c !important;
}
@media (max-width: 720px) {
  body.alex-native-site.alex-home-page .alex-home-text-section { padding: 36px 0 !important; }
  body.alex-native-site.alex-home-page .alex-home-snapshot-entry { padding-left: 0 !important; padding-right: 0 !important; }
}

/* alex-home-unified-system-20260705a
   Unified homepage template: one visual language, one hero/form system, clear static vs clickable blocks. */
body.alex-native-site.alex-home-page {
  --ay-home-bg: #f6efe4;
  --ay-home-panel: #fffaf0;
  --ay-home-panel-strong: #fffdf8;
  --ay-home-text: #111820;
  --ay-home-muted: #566067;
  --ay-home-line: rgba(17, 24, 32, .14);
  --ay-home-orange: #c84f07;
  --ay-home-orange-2: #e86b16;
  --ay-home-green: #607348;
  background: var(--ay-home-bg);
}
body.alex-native-site.alex-home-page .app-shell {
  width: min(1120px, calc(100% - clamp(28px, 7vw, 112px))) !important;
  max-width: none !important;
  margin-inline: auto !important;
  padding-top: clamp(20px, 2.7vw, 34px) !important;
}
body.alex-native-site.alex-home-page .alex-home-unified,
body.alex-native-site.alex-home-page .alex-home-unified * { box-sizing: border-box; }
body.alex-native-site.alex-home-page .alex-home-unified { display: grid; gap: clamp(34px, 5.5vw, 72px); }
body.alex-native-site.alex-home-page .alex-home-unified a { text-decoration: none !important; }
body.alex-native-site.alex-home-page .alex-home-unified-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(330px, .72fr);
  gap: clamp(24px, 4vw, 48px);
  align-items: stretch;
  padding: clamp(30px, 4.4vw, 54px);
  border: 1px solid rgba(17,24,32,.18);
  border-radius: 24px;
  background:
    radial-gradient(circle at 12% 16%, rgba(255,255,255,.22), transparent 30%),
    linear-gradient(135deg, #dc6817 0%, #c6530b 56%, #994008 100%);
  box-shadow: 0 28px 76px rgba(17,24,32,.16);
  overflow: hidden;
}
body.alex-native-site.alex-home-page .alex-home-hero-copy { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
body.alex-native-site.alex-home-page .alex-home-kicker,
body.alex-native-site.alex-home-page .alex-home-section-kicker,
body.alex-native-site.alex-home-page .alex-home-service-card span,
body.alex-native-site.alex-home-page .alex-home-snapshot-head span {
  display: inline-flex;
  margin: 0 0 12px;
  color: rgba(17,24,32,.82);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .12em;
  line-height: 1;
  text-transform: uppercase;
}
body.alex-native-site.alex-home-page .alex-home-hero-copy h1 {
  max-width: 680px;
  margin: 0;
  color: #171511;
  font-family: var(--font-display, 'Barlow Condensed', sans-serif);
  font-size: clamp(46px, 6.4vw, 86px);
  line-height: .89;
  letter-spacing: -.055em;
}
body.alex-native-site.alex-home-page .alex-home-deck {
  max-width: 58ch;
  margin: clamp(18px, 2vw, 24px) 0 0;
  color: rgba(17,24,32,.86);
  font-size: clamp(16px, 1.25vw, 18px);
  line-height: 1.55;
}
body.alex-native-site.alex-home-page .alex-home-hero-actions,
body.alex-native-site.alex-home-page .alex-home-button { display: inline-flex; align-items: center; }
body.alex-native-site.alex-home-page .alex-home-hero-actions { flex-wrap: wrap; gap: 12px; margin-top: clamp(20px, 2.6vw, 30px); }
body.alex-native-site.alex-home-page .alex-home-button {
  min-height: 46px;
  justify-content: center;
  border-radius: 12px;
  padding: 12px 18px;
  font-weight: 900;
  letter-spacing: -.01em;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease;
}
body.alex-native-site.alex-home-page .alex-home-button-primary {
  border: 1px solid #111820;
  background: #111820;
  color: #fff !important;
  box-shadow: 4px 4px 0 rgba(17,24,32,.24);
}
body.alex-native-site.alex-home-page .alex-home-button-secondary {
  border: 1px solid rgba(17,24,32,.24);
  background: rgba(255,253,248,.72);
  color: #111820 !important;
}
body.alex-native-site.alex-home-page .alex-home-button-base {
  margin-top: 12px;
  border: 1px solid rgba(61,80,51,.32);
  background: #607348;
  color: #fff !important;
}
body.alex-native-site.alex-home-page .alex-home-button:hover { transform: translateY(-1px); }
body.alex-native-site.alex-home-page .alex-home-stat-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  max-width: 720px;
  margin: clamp(22px, 3vw, 36px) 0 0;
}
body.alex-native-site.alex-home-page .alex-home-stat {
  min-width: 0;
  padding: 14px 16px;
  border: 1px solid rgba(17,24,32,.16);
  border-radius: 14px;
  background: rgba(255,253,248,.36);
}
body.alex-native-site.alex-home-page .alex-home-stat dt { margin: 0 0 4px; color: rgba(17,24,32,.62); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }
body.alex-native-site.alex-home-page .alex-home-stat dd { margin: 0; color: #111820; font-size: 14px; font-weight: 900; line-height: 1.2; }
body.alex-native-site.alex-home-page .alex-home-snapshot-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  border: 1px solid rgba(17,24,32,.20);
  border-radius: 22px;
  padding: clamp(20px, 2.6vw, 30px);
  background: rgba(255,250,240,.92);
  box-shadow: 0 22px 58px rgba(17,24,32,.12);
}
body.alex-native-site.alex-home-page .alex-home-snapshot-head {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-head img {
  width: 58px;
  height: 58px;
  object-fit: cover;
  object-position: top center;
  border-radius: 50%;
  background: #e36a17;
  border: 1px solid rgba(17,24,32,.16);
}
body.alex-native-site.alex-home-page .alex-home-snapshot-head h2 { margin: 0 0 4px; color: #111820; font-size: clamp(24px, 2.4vw, 32px); line-height: 1; letter-spacing: -.035em; }
body.alex-native-site.alex-home-page .alex-home-snapshot-head p { margin: 0; color: var(--ay-home-muted); font-size: 14px; line-height: 1.45; }
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 8px 10px; }
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form label { gap: 6px; color: #111820; font-size: 13px; font-weight: 850; }
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form label span { color: var(--ay-home-muted); font-weight: 500; }
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form input {
  min-height: 40px;
  border: 1px solid rgba(17,24,32,.18) !important;
  border-radius: 10px !important;
  background: #fffdf8 !important;
  color: #111820;
}
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form button {
  min-height: 42px;
  border: 1px solid var(--ay-home-orange) !important;
  border-radius: 12px !important;
  background: var(--ay-home-orange) !important;
  color: #fff !important;
  box-shadow: none !important;
  font-weight: 950;
}
body.alex-native-site.alex-home-page .alex-home-unified-section {
  display: grid;
  grid-template-columns: minmax(270px, .56fr) minmax(0, 1fr);
  gap: clamp(24px, 4.6vw, 60px);
  align-items: start;
  padding: clamp(34px, 5vw, 64px) 0;
  border-top: 1px solid var(--ay-home-line);
}
body.alex-native-site.alex-home-page .alex-home-section-copy { min-width: 0; }
body.alex-native-site.alex-home-page .alex-home-section-copy h2 {
  max-width: 620px;
  margin: 0;
  color: var(--ay-home-text);
  font-size: clamp(31px, 4vw, 48px);
  line-height: 1.03;
  letter-spacing: -.045em;
}
body.alex-native-site.alex-home-page .alex-home-section-copy p {
  max-width: 64ch;
  margin: 16px 0 0;
  color: #3f474c;
  font-size: clamp(16px, 1.18vw, 18px);
  line-height: 1.65;
}
body.alex-native-site.alex-home-page .alex-home-system-grid,
body.alex-native-site.alex-home-page .alex-home-service-grid { display: grid; gap: 14px; }
body.alex-native-site.alex-home-page .alex-home-system-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
body.alex-native-site.alex-home-page .alex-home-system-tile {
  position: relative;
  min-height: 184px;
  padding: 26px 24px;
  border: 1px solid rgba(17,24,32,.13);
  border-radius: 18px;
  background: #fffdf8;
  box-shadow: 0 12px 32px rgba(17,24,32,.045);
}
body.alex-native-site.alex-home-page .alex-home-system-tile::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: 18px 0 0 18px;
  background: var(--ay-home-orange);
}
body.alex-native-site.alex-home-page .alex-home-system-tile h3,
body.alex-native-site.alex-home-page .alex-home-service-card h3 { margin: 0 0 9px; color: #111820; font-size: clamp(19px, 1.65vw, 24px); line-height: 1.08; letter-spacing: -.02em; }
body.alex-native-site.alex-home-page .alex-home-system-tile p,
body.alex-native-site.alex-home-page .alex-home-service-card p { margin: 0; color: var(--ay-home-muted); line-height: 1.55; }
body.alex-native-site.alex-home-page .alex-home-service-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
body.alex-native-site.alex-home-page .alex-home-service-card {
  display: flex;
  min-height: 210px;
  flex-direction: column;
  padding: 26px;
  border: 1px solid rgba(17,24,32,.18);
  border-left: 4px solid #111820;
  border-radius: 18px;
  background: linear-gradient(135deg, #fffaf0, #fff2dd);
  box-shadow: 0 18px 48px rgba(17,24,32,.075);
}
body.alex-native-site.alex-home-page .alex-home-service-card em { margin-top: auto; padding-top: 20px; color: #a83900; font-style: normal; font-weight: 950; letter-spacing: .02em; }
body.alex-native-site.alex-home-page .alex-home-service-card em::after { content: " →"; }
body.alex-native-site.alex-home-page .alex-home-service-card:hover { transform: translateY(-2px); box-shadow: 0 24px 60px rgba(17,24,32,.12); }
body.alex-native-site.alex-home-page .alex-home-base2026-band {
  margin-top: -8px;
  padding: clamp(30px, 4.4vw, 54px);
  border: 1px solid rgba(61,80,51,.22);
  border-radius: 22px;
  background: linear-gradient(135deg, #f8f2e5, #eef1e7);
}
body.alex-native-site.alex-home-page .alex-home-lab-card {
  border: 1px solid rgba(61,80,51,.22);
  border-radius: 18px;
  background: #fffdf8;
  box-shadow: 0 18px 44px rgba(61,80,51,.09);
  overflow: hidden;
}
body.alex-native-site.alex-home-page .alex-home-lab-search {
  margin: 18px 18px 0;
  padding: 13px 14px;
  border: 1px solid rgba(61,80,51,.20);
  border-radius: 12px;
  color: rgba(17,24,32,.58);
  font-weight: 750;
}
body.alex-native-site.alex-home-page .alex-home-lab-card ul { display: grid; gap: 0; margin: 18px 0 0; padding: 0; list-style: none; }
body.alex-native-site.alex-home-page .alex-home-lab-card li { display: grid; gap: 4px; padding: 18px; border-top: 1px solid rgba(61,80,51,.16); }
body.alex-native-site.alex-home-page .alex-home-lab-card strong { color: #111820; font-size: 17px; }
body.alex-native-site.alex-home-page .alex-home-lab-card span { color: var(--ay-home-muted); line-height: 1.5; }
body.alex-native-site.alex-home-page .alex-home-faq-block { grid-template-columns: minmax(270px, .56fr) minmax(0, .92fr); padding-top: clamp(24px, 4vw, 52px); }
body.alex-native-site.alex-home-page .alex-home-faq-accordion { display: grid; gap: 0; border-top: 1px solid var(--ay-home-line); }
body.alex-native-site.alex-home-page .alex-home-faq-accordion details { border: 0 !important; border-bottom: 1px solid var(--ay-home-line) !important; border-radius: 0 !important; background: transparent !important; box-shadow: none !important; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary { cursor: pointer; padding: 18px 0; color: #111820; font-weight: 900; list-style: none; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary::-webkit-details-marker { display: none; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion summary::after { content: "+"; float: right; color: var(--ay-home-orange); }
body.alex-native-site.alex-home-page .alex-home-faq-accordion details[open] summary::after { content: "–"; }
body.alex-native-site.alex-home-page .alex-home-faq-accordion p { margin: 0; padding: 0 0 20px; color: #3f474c; line-height: 1.65; }
@media (max-width: 980px) {
  body.alex-native-site.alex-home-page .alex-home-unified-hero,
  body.alex-native-site.alex-home-page .alex-home-unified-section,
  body.alex-native-site.alex-home-page .alex-home-base2026-band,
  body.alex-native-site.alex-home-page .alex-home-faq-block { grid-template-columns: 1fr; }
  body.alex-native-site.alex-home-page .alex-home-system-grid { grid-template-columns: 1fr; }
  body.alex-native-site.alex-home-page .alex-home-snapshot-card { justify-content: flex-start; }
}
@media (max-width: 720px) {
  body.alex-native-site.alex-home-page .app-shell { width: min(100% - 28px, 1120px) !important; }
  body.alex-native-site.alex-home-page .alex-home-unified { gap: 28px; }
  body.alex-native-site.alex-home-page .alex-home-unified-hero { padding: 24px 20px; border-radius: 20px; }
  body.alex-native-site.alex-home-page .alex-home-hero-copy h1 { font-size: clamp(40px, 12vw, 58px); }
  body.alex-native-site.alex-home-page .alex-home-stat-strip,
  body.alex-native-site.alex-home-page .alex-home-service-grid { grid-template-columns: 1fr; }
  body.alex-native-site.alex-home-page .alex-home-button { width: 100%; }
  body.alex-native-site.alex-home-page .alex-home-system-tile,
  body.alex-native-site.alex-home-page .alex-home-service-card { min-height: 0; }
  body.alex-native-site.alex-home-page .alex-home-base2026-band { padding: 24px 20px; }
}

/* alex-home-unified-system-20260705a QA tightening */
body.alex-native-site.alex-home-page .site-header__avatar {
  display: inline-grid !important;
  place-items: center !important;
  background: #111820 !important;
  border-color: #111820 !important;
  color: #fff !important;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .06em;
}
body.alex-native-site.alex-home-page .site-header__avatar::after { content: "AY"; }
body.alex-native-site.alex-home-page .alex-home-hero-copy h1 {
  font-size: clamp(44px, 5.9vw, 80px) !important;
  line-height: .92 !important;
}
body.alex-native-site.alex-home-page .alex-home-unified-hero {
  align-items: center !important;
  padding: clamp(24px, 2.8vw, 32px) !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-card { padding: 20px !important; }
body.alex-native-site.alex-home-page .alex-home-button-primary {
  border-color: var(--ay-home-orange) !important;
  background: var(--ay-home-orange) !important;
  color: #fff !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-button-secondary {
  background: transparent !important;
  border-color: rgba(17,24,32,.22) !important;
  color: #111820 !important;
}
body.alex-native-site.alex-home-page .alex-home-snapshot-card { transform: translateY(8px); }
body.alex-native-site.alex-home-page .alex-home-snapshot-head { margin-bottom: 14px !important; display: block !important; }
body.alex-native-site.alex-home-page .alex-home-form-link {
  display: inline-flex;
  align-self: flex-start;
  margin-top: 14px;
  color: #111820 !important;
  font-weight: 900;
  text-decoration: underline !important;
  text-decoration-color: rgba(200,79,7,.45) !important;
  text-underline-offset: 3px;
}
body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form input {
  border-color: rgba(17,24,32,.28) !important;
}
body.alex-native-site.alex-home-page .alex-home-service-card {
  border-left-color: var(--ay-home-orange) !important;
}
body.alex-native-site.alex-home-page .alex-home-service-card em {
  display: inline-flex;
  align-self: flex-start;
  background: transparent !important;
  border: 0 !important;
  padding: 18px 0 0 !important;
  color: #a83900 !important;
}
body.alex-native-site.alex-home-page .alex-home-lab-search {
  border-color: transparent !important;
  background: #607348 !important;
  color: #fff !important;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}
body.alex-native-site.alex-home-page .alex-home-lab-card li { padding: 0 !important; }
body.alex-native-site.alex-home-page .alex-home-lab-card li a {
  display: grid;
  gap: 4px;
  padding: 18px;
  color: inherit !important;
}
body.alex-native-site.alex-home-page .alex-home-lab-card li a em {
  margin-top: 6px;
  color: #607348;
  font-style: normal;
  font-weight: 900;
}
body.alex-native-site.alex-home-page .alex-home-lab-card li a em::after { content: " →"; }
body.alex-native-site.alex-home-page .site-footer .ay-button-secondary {
  color: #fff !important;
  border-color: rgba(255,255,255,.35) !important;
}
@media (max-width: 720px) {
  body.alex-native-site.alex-home-page { overflow-x: hidden !important; }
  body.alex-native-site.alex-home-page .app-shell {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
  }
  body.alex-native-site.alex-home-page .alex-home-unified { gap: 28px; max-width: 100% !important; overflow-x: hidden; }
  body.alex-native-site.alex-home-page .alex-home-unified-hero {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    overflow: hidden !important;
    padding: 22px 16px !important;
    border-radius: 18px;
    gap: 20px !important;
  }
  body.alex-native-site.alex-home-page .alex-home-hero-copy,
  body.alex-native-site.alex-home-page .alex-home-snapshot-card,
  body.alex-native-site.alex-home-page .alex-home-section-copy,
  body.alex-native-site.alex-home-page .alex-home-system-grid,
  body.alex-native-site.alex-home-page .alex-home-service-grid,
  body.alex-native-site.alex-home-page .alex-home-lab-card {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }
  body.alex-native-site.alex-home-page .alex-home-hero-copy h1 {
    max-width: 100% !important;
    font-size: clamp(34px, 10vw, 44px) !important;
    line-height: .96 !important;
    letter-spacing: -.04em !important;
    overflow-wrap: normal;
  }
  body.alex-native-site.alex-home-page .alex-home-deck { max-width: 100% !important; font-size: 15.5px; }
  body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form { grid-template-columns: 1fr !important; }
  body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form input,
  body.alex-native-site.alex-home-page .alex-home-unified .alex-home-compact-form button { max-width: 100% !important; min-width: 0 !important; }
  body.alex-native-site.alex-home-page .alex-home-snapshot-card { transform: none; padding: 16px !important; }
  body.alex-native-site.alex-home-page .alex-home-service-card em { padding-top: 14px !important; }
  body.alex-native-site.alex-home-page .alex-home-base2026-band { padding: 24px 16px !important; }
}

/* alex-home-premium-refactor-20260705b
   Premium editorial conversion pass: one visible reading path, integrated form, ordered operating loop. */
body.alex-native-site.alex-home-page {
  --ay-premium-bg: #f6efe4;
  --ay-premium-paper: #fffaf0;
  --ay-premium-paper-strong: #fffdf8;
  --ay-premium-ink: #111820;
  --ay-premium-muted: #59636b;
  --ay-premium-line: rgba(17,24,32,.14);
  --ay-premium-orange: #c84f07;
  --ay-premium-orange-2: #ea6b16;
  --ay-premium-green: #607348;
  background:
    radial-gradient(circle at 14% 0%, rgba(232,107,22,.14), transparent 34rem),
    linear-gradient(180deg, #f8f2e8 0%, #f3eadb 100%) !important;
}
body.alex-native-site.alex-home-page .app-shell {
  width: min(1080px, calc(100% - clamp(32px, 8vw, 144px))) !important;
  padding-top: clamp(18px, 2.2vw, 28px) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium {
  display: grid;
  gap: clamp(32px, 4.8vw, 58px) !important;
  color: var(--ay-premium-ink);
}
body.alex-native-site.alex-home-page .alex-home-premium-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(318px, .72fr);
  gap: clamp(24px, 4vw, 46px);
  align-items: center;
  padding: clamp(26px, 3.2vw, 38px);
  border: 1px solid rgba(17,24,32,.16);
  border-radius: 30px;
  background:
    linear-gradient(90deg, rgba(200,79,7,.12) 0 6px, transparent 6px),
    radial-gradient(circle at 0% 0%, rgba(255,255,255,.9), transparent 31rem),
    linear-gradient(135deg, #fffaf0 0%, #f8ead9 58%, #efe1ce 100%);
  box-shadow: 0 30px 84px rgba(17,24,32,.13);
  overflow: hidden;
}
body.alex-native-site.alex-home-page .alex-home-premium-hero::after {
  content: "";
  position: absolute;
  inset: 18px 18px auto auto;
  width: 150px;
  height: 150px;
  border: 1px solid rgba(17,24,32,.08);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(200,79,7,.16), transparent 58%);
  pointer-events: none;
}
body.alex-native-site.alex-home-page .alex-home-premium-hero > * { position: relative; z-index: 1; }
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-kicker,
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-section-kicker,
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card span,
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-snapshot-head span,
body.alex-native-site.alex-home-page .alex-home-loop article span {
  color: #9f3c05 !important;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .13em;
  text-transform: uppercase;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-hero-copy h1 {
  max-width: 720px !important;
  color: var(--ay-premium-ink) !important;
  font-family: var(--font-display, 'Barlow Condensed', sans-serif);
  font-size: clamp(44px, 5.4vw, 68px) !important;
  line-height: .92 !important;
  letter-spacing: -.055em !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-deck {
  max-width: 60ch !important;
  color: #30383e !important;
  font-size: clamp(16px, 1.18vw, 18px) !important;
  line-height: 1.56 !important;
}
body.alex-native-site.alex-home-page .alex-home-proof-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: clamp(16px, 2.1vw, 22px) 0 0;
  max-width: 660px;
}
body.alex-native-site.alex-home-page .alex-home-proof-row .alex-home-stat {
  padding: 10px 12px !important;
  border: 1px solid rgba(17,24,32,.14) !important;
  border-radius: 16px !important;
  background: rgba(255,253,248,.58) !important;
  box-shadow: none !important;
}
body.alex-native-site.alex-home-page .alex-home-proof-row dt { color: rgba(17,24,32,.58) !important; }
body.alex-native-site.alex-home-page .alex-home-proof-row dd { color: var(--ay-premium-ink) !important; }
body.alex-native-site.alex-home-page .alex-home-hero-note {
  max-width: 56ch;
  margin: 18px 0 0;
  padding-left: 14px;
  border-left: 3px solid var(--ay-premium-orange);
  color: #485159;
  font-size: 14.5px;
  line-height: 1.55;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card {
  align-self: center;
  justify-content: flex-start !important;
  transform: none !important;
  padding: clamp(18px, 2vw, 22px) !important;
  border: 1px solid rgba(17,24,32,.17) !important;
  border-radius: 24px !important;
  background: rgba(255,253,248,.92) !important;
  box-shadow: 0 22px 62px rgba(17,24,32,.10) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-snapshot-head {
  display: block !important;
  margin-bottom: 12px !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-snapshot-head h2 {
  max-width: 100%;
  margin: 0 0 5px !important;
  font-size: clamp(24px, 2.2vw, 30px) !important;
  line-height: .98 !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-snapshot-head span { margin-bottom: 8px !important; }
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-snapshot-head p {
  font-size: 13.5px !important;
  line-height: 1.38 !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form label { gap: 4px !important; }
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form label span { display: none !important; }
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 7px 9px !important;
  margin-top: 0 !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form label:first-of-type,
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form button { grid-column: 1 / -1 !important; }
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form input {
  min-height: 38px !important;
  border-radius: 11px !important;
  background: #fffaf0 !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form button {
  min-height: 40px !important;
  border-radius: 12px !important;
  background: var(--ay-premium-orange) !important;
  border-color: var(--ay-premium-orange) !important;
}
body.alex-native-site.alex-home-page .alex-home-form-link {
  color: var(--ay-premium-ink) !important;
  text-decoration-color: rgba(200,79,7,.5) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium-section {
  display: grid;
  grid-template-columns: minmax(250px, .55fr) minmax(0, 1fr);
  gap: clamp(24px, 4.6vw, 58px);
  align-items: start;
  padding: clamp(28px, 4.6vw, 56px) 0;
  border-top: 1px solid var(--ay-premium-line);
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-section-copy h2 {
  max-width: 600px;
  color: var(--ay-premium-ink) !important;
  font-size: clamp(31px, 3.8vw, 46px) !important;
  line-height: 1.04 !important;
  letter-spacing: -.045em !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-section-copy p {
  color: #465058 !important;
  line-height: 1.64 !important;
}
body.alex-native-site.alex-home-page .alex-home-loop {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
body.alex-native-site.alex-home-page .alex-home-loop article {
  min-height: 178px;
  padding: 22px 22px 24px;
  border: 1px solid rgba(17,24,32,.13);
  border-radius: 20px;
  background: rgba(255,253,248,.76);
  box-shadow: 0 14px 38px rgba(17,24,32,.052);
}
body.alex-native-site.alex-home-page .alex-home-loop article h3 {
  margin: 12px 0 8px;
  color: var(--ay-premium-ink);
  font-size: clamp(20px, 1.7vw, 25px);
  line-height: 1.08;
  letter-spacing: -.025em;
}
body.alex-native-site.alex-home-page .alex-home-loop article p { margin: 0; color: var(--ay-premium-muted); line-height: 1.55; }
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 14px !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card {
  min-height: 204px !important;
  padding: 24px !important;
  border: 1px solid rgba(17,24,32,.16) !important;
  border-left: 5px solid var(--ay-premium-orange) !important;
  border-radius: 20px !important;
  background: linear-gradient(135deg, #fffdf8, #fff3df) !important;
  box-shadow: 0 18px 48px rgba(17,24,32,.075) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card:hover,
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card:focus-visible {
  transform: translateY(-2px);
  box-shadow: 0 25px 64px rgba(17,24,32,.13) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card em {
  color: #9f3c05 !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-base2026-band {
  margin-top: 0 !important;
  padding: clamp(28px, 4.2vw, 48px) !important;
  border: 1px solid rgba(61,80,51,.25) !important;
  border-radius: 26px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(96,115,72,.14), transparent 26rem),
    linear-gradient(135deg, #f9f3e6, #edf1e5) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-button-base {
  background: var(--ay-premium-green) !important;
  border-color: var(--ay-premium-green) !important;
  border-radius: 12px !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-lab-card {
  border-radius: 20px !important;
  background: #fffdf8 !important;
  box-shadow: 0 18px 44px rgba(61,80,51,.10) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-faq-block {
  grid-template-columns: minmax(250px, .55fr) minmax(0, 1fr) !important;
  padding-top: clamp(22px, 4vw, 46px) !important;
}
body.alex-native-site.alex-home-page .alex-home-premium .alex-home-faq-accordion {
  max-width: none !important;
}
@media (max-width: 980px) {
  body.alex-native-site.alex-home-page .app-shell { width: min(100% - 36px, 1080px) !important; }
  body.alex-native-site.alex-home-page .alex-home-premium-hero,
  body.alex-native-site.alex-home-page .alex-home-premium-section,
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-faq-block { grid-template-columns: 1fr !important; }
  body.alex-native-site.alex-home-page .alex-home-premium-form-card { align-self: start; }
}
@media (max-width: 720px) {
  body.alex-native-site.alex-home-page .app-shell { width: 100% !important; padding-left: 14px !important; padding-right: 14px !important; }
  body.alex-native-site.alex-home-page .alex-home-premium { gap: 28px !important; }
  body.alex-native-site.alex-home-page .alex-home-premium-hero { padding: 22px 16px !important; border-radius: 22px !important; }
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-hero-copy h1 { font-size: clamp(36px, 10vw, 44px) !important; line-height: .96 !important; }
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-deck { font-size: 14.5px !important; line-height: 1.48 !important; }
  body.alex-native-site.alex-home-page .alex-home-proof-row { grid-template-columns: repeat(3, minmax(0, 1fr)) !important; gap: 6px !important; }
  body.alex-native-site.alex-home-page .alex-home-proof-row .alex-home-stat { padding: 8px 7px !important; border-radius: 12px !important; }
  body.alex-native-site.alex-home-page .alex-home-proof-row dt { font-size: 9px !important; letter-spacing: .04em !important; }
  body.alex-native-site.alex-home-page .alex-home-proof-row dd { font-size: 11.5px !important; line-height: 1.15 !important; }
  body.alex-native-site.alex-home-page .alex-home-loop,
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-grid,
  body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form { grid-template-columns: 1fr !important; }
  body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form label,
  body.alex-native-site.alex-home-page .alex-home-premium-form-card .alex-home-compact-form button { grid-column: 1 / -1 !important; }
  body.alex-native-site.alex-home-page .alex-home-loop article,
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-service-card { min-height: 0 !important; }
  body.alex-native-site.alex-home-page .alex-home-premium .alex-home-base2026-band { padding: 24px 16px !important; border-radius: 22px !important; }
}
/* Stitch-imported About body. Header/footer remain global from the Base2026 shell. */
body.alex-native-site.alex-about-page { background: #fff8ec; color: #111820; }
body.alex-native-site.alex-about-page .app-shell {
  width: 100% !important;
  max-width: none !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
body.alex-native-site.alex-about-page .alex-about-stitch {
  width: 100%;
  overflow: hidden;
  background: #fff8ec;
}
body.alex-native-site.alex-about-page .alex-about-stitch-hero {
  width: min(100% - 48px, 1280px);
  min-height: clamp(560px, 70vw, 720px);
  margin: clamp(52px, 8vw, 104px) auto clamp(92px, 10vw, 150px);
  display: grid;
  grid-template-columns: minmax(0, 7fr) minmax(300px, 5fr);
  gap: clamp(28px, 5vw, 72px);
  align-items: center;
}
body.alex-native-site.alex-about-page .alex-about-stitch-copy { padding-top: clamp(8px, 4vw, 72px); }
body.alex-native-site.alex-about-page .alex-about-stitch-kicker {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 24px;
  color: #66717a;
  font-family: "Geist Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .19em;
  line-height: 1.2;
  text-transform: uppercase;
}
body.alex-native-site.alex-about-page .alex-about-stitch-kicker span {
  display: inline-block;
  width: 32px;
  height: 1px;
  background: rgba(17,24,32,.24);
}
body.alex-native-site.alex-about-page .alex-about-stitch-copy h1 {
  max-width: 790px;
  margin: 0 0 30px;
  color: #c84f07;
  font-family: "Barlow Condensed", "Geist", system-ui, sans-serif;
  font-size: clamp(54px, 7.8vw, 100px);
  font-weight: 700;
  line-height: .98;
  letter-spacing: -.038em;
}
body.alex-native-site.alex-about-page .alex-about-stitch-copy p {
  max-width: 720px;
  margin: 0 0 38px;
  color: #5d6871;
  font-size: clamp(18px, 1.65vw, 22px);
  line-height: 1.58;
}
body.alex-native-site.alex-about-page .alex-about-stitch-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}
body.alex-native-site.alex-about-page .alex-about-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 54px;
  padding: 15px 30px;
  border: 1px solid transparent;
  border-radius: 10px;
  font-family: "Geist Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .12em;
  line-height: 1;
  text-decoration: none !important;
  text-transform: uppercase;
  transition: transform .2s ease, background-color .2s ease, color .2s ease, border-color .2s ease, opacity .2s ease;
}
body.alex-native-site.alex-about-page .alex-about-button:hover,
body.alex-native-site.alex-about-page .alex-about-button:focus-visible { transform: translateY(-1px); }
body.alex-native-site.alex-about-page .alex-about-button-primary { background: #c84f07; border-color: #c84f07; color: #fffdf8 !important; }
body.alex-native-site.alex-about-page .alex-about-button-secondary { background: transparent; border-color: #c84f07; color: #c84f07 !important; gap: 8px; }
body.alex-native-site.alex-about-page .alex-about-button-secondary:hover { background: rgba(200,79,7,.06); }
body.alex-native-site.alex-about-page .alex-about-stitch-portrait {
  position: relative;
  align-self: end;
  display: flex;
  justify-content: flex-end;
  align-items: flex-end;
  min-height: clamp(420px, 54vw, 660px);
  margin: 0;
  overflow: visible;
}
body.alex-native-site.alex-about-page .alex-about-stitch-portrait img {
  display: block;
  width: min(118%, 610px);
  max-width: none;
  height: auto;
  object-fit: contain;
  object-position: bottom right;
  transform: translate(6%, 5%) scale(1.13);
  filter: drop-shadow(0 34px 46px rgba(17,24,32,.22));
}
body.alex-native-site.alex-about-page .alex-about-stitch-final {
  width: 100%;
  margin: clamp(64px, 8vw, 126px) 0 0;
  padding: clamp(72px, 9vw, 104px) 24px;
  background: #121a20;
  color: #fffdf8;
  text-align: center;
}
body.alex-native-site.alex-about-page .alex-about-stitch-final-inner {
  max-width: 940px;
  margin: 0 auto;
}
body.alex-native-site.alex-about-page .alex-about-stitch-final h2 {
  max-width: 900px;
  margin: 0 auto 24px;
  color: #fffdf8;
  font-family: "Barlow Condensed", "Geist", system-ui, sans-serif;
  font-size: clamp(48px, 6.8vw, 88px);
  font-weight: 700;
  line-height: .98;
  letter-spacing: -.04em;
}
body.alex-native-site.alex-about-page .alex-about-stitch-final p {
  max-width: 690px;
  margin: 0 auto 44px;
  color: #cfd6dd;
  font-size: clamp(17px, 1.55vw, 21px);
  line-height: 1.62;
}
body.alex-native-site.alex-about-page .alex-about-stitch-final-actions { justify-content: center; }
body.alex-native-site.alex-about-page .alex-about-button-light { background: #fffdf8; border-color: #fffdf8; color: #c84f07 !important; }
body.alex-native-site.alex-about-page .alex-about-button-ghost { background: transparent; border-color: rgba(255,253,248,.44); color: #fffdf8 !important; }
body.alex-native-site.alex-about-page .alex-about-button-ghost:hover { background: rgba(255,255,255,.06); }
@media (max-width: 980px) {
  body.alex-native-site.alex-about-page .alex-about-stitch-hero {
    grid-template-columns: 1fr;
    width: min(100% - 36px, 760px);
    min-height: 0;
    margin-top: 42px;
  }
  body.alex-native-site.alex-about-page .alex-about-stitch-copy { padding-top: 0; }
  body.alex-native-site.alex-about-page .alex-about-stitch-portrait {
    justify-content: center;
    min-height: 360px;
  }
  body.alex-native-site.alex-about-page .alex-about-stitch-portrait img {
    width: min(92vw, 520px);
    transform: translateY(5%) scale(1.05);
  }
}
@media (max-width: 640px) {
  body.alex-native-site.alex-about-page .alex-about-stitch-hero { width: calc(100% - 28px); margin-bottom: 66px; }
  body.alex-native-site.alex-about-page .alex-about-stitch-actions { display: grid; grid-template-columns: 1fr; }
  body.alex-native-site.alex-about-page .alex-about-button { width: 100%; }
  body.alex-native-site.alex-about-page .alex-about-stitch-copy h1 { font-size: clamp(44px, 15vw, 62px); }
  body.alex-native-site.alex-about-page .alex-about-stitch-portrait { min-height: 300px; }
  body.alex-native-site.alex-about-page .alex-about-stitch-final { padding-left: 16px; padding-right: 16px; }
}
"""


def render(page: Page) -> str:
    c = canonical(page.path)
    crumbs = '' if page.path == '/' else f'<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Alex Yarosh</a><span aria-hidden="true">/</span><span aria-current="page">{escape(page.eyebrow)}</span></nav>'
    schema_json = schema_for(page)
    intro_actions = actions((SHORT_CTA, "/ai-visibility-audit/", False), ("Explore Base2026 Evidence", "/knowledge/ai-visibility-pages/", True))
    if page.path == "/":
        body_class = "alex-native-site alex-home-page"
        main_html = home_page(page)
    elif page.path == "/about/":
        body_class = "alex-native-site alex-about-page"
        main_html = about_page(page)
    else:
        body_class = "alex-native-site"
        sections_html = ''.join(page.sections) + faq_section(page)
        intro_html = f'<section class="content-section alex-native-intro"><p class="eyebrow">{escape(page.eyebrow)}</p><h1>{escape(page.h1)}</h1><p>{escape(page.deck)}</p>{intro_actions}</section>'
        main_html = f"""{crumbs}
{hero(page)}
      {intro_html}
      {sections_html}"""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escape(page.title)}</title>
    <meta name="description" content="{escape(page.description)}" />
    <meta name="robots" content="{escape(page.robots)}" />
    <link rel="canonical" href="{escape(c)}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Alex Yarosh" />
    <meta property="og:title" content="{escape(page.title)}" />
    <meta property="og:description" content="{escape(page.description)}" />
    <meta property="og:url" content="{escape(c)}" />
    <meta property="og:image" content="https://aggressorbulkit.online/knowledge/static/assets/base2026-ai-visibility-card.png" />
    <script type="application/ld+json">{schema_json}</script>
    <link rel="icon" type="image/png" sizes="32x32" href="/knowledge/static/assets/alex-yarosh-favicon-32.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="{FONTS}" rel="stylesheet" />
    <link rel="stylesheet" href="/knowledge/static/styles.css?v=base2026-ai-pages-cardfix-20260628" />
    <link rel="stylesheet" href="/alex-native/styles.css?v={RELEASE}" />
  </head>
  <body class="{body_class}">
{header(page.path)}
    <main id="content" class="app-shell content-page doc-page ai-visibility-page alex-native-page">
      {main_html}
    </main>
{footer()}
    <script>
    (() => {{
      const params = new URLSearchParams(location.search);
      const intent = params.get('intent') || params.get('plan') || '';
      document.querySelectorAll('input[name="landing_page"]').forEach(i=>i.value=location.href);
      document.querySelectorAll('input[name="referrer"]').forEach(i=>i.value=document.referrer||'');
      document.querySelectorAll('form[data-default-intent]').forEach(form => {{
        const field = form.querySelector('input[name="ay_intent"]');
        const resolved = intent || form.dataset.defaultIntent || (field ? field.value : 'snapshot');
        if (field) field.value = resolved;
        const notes = form.querySelector('input[name="ay_notes"]');
        if (notes && !notes.value.includes('Intent:')) notes.value = `Intent: ${{resolved}}; ${{notes.value}}`;
      }});
      document.querySelectorAll('textarea[name="ay_extra_notes"]').forEach(t => {{
        t.addEventListener('input', () => {{
          const form = t.closest('form');
          const notes = form && form.querySelector('input[name="ay_notes"]');
          const field = form && form.querySelector('input[name="ay_intent"]');
          if (notes) notes.value = `Intent: ${{field ? field.value : 'snapshot'}}; Extra notes: ${{t.value}}`;
        }});
      }});
    }})();
    </script>
  </body>
</html>"""


def write_page(page: Page) -> None:
    target = OUT / ("index.html" if page.path == "/" else f"{page.path.strip('/')}/index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(page), encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "alex-native").mkdir(parents=True, exist_ok=True)
    (OUT / "alex-native" / "styles.css").write_text(CSS, encoding="utf-8")
    static_file_pairs = (
        (Path("web/static/styles.css"), OUT / "knowledge/static/styles.css"),
        (Path("web/static/assets/base2026-ai-visibility-card.png"), OUT / "knowledge/static/assets/base2026-ai-visibility-card.png"),
        (Path("web/static/assets/alex-yarosh-favicon-32.png"), OUT / "knowledge/static/assets/alex-yarosh-favicon-32.png"),
        (Path("web/static/assets/alex-yarosh-cutout-v115.png"), OUT / "knowledge/static/assets/alex-yarosh-cutout-v115.png"),
    )
    for src, dst in static_file_pairs:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for p in PAGES:
        write_page(p)
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in PAGES:
        if p.include_sitemap and not p.robots.startswith("noindex"):
            sitemap.append(f'<url><loc>{canonical(p.path)}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p.priority}</priority></url>')
    sitemap.append('</urlset>')
    (OUT / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /wp-admin/\nAllow: /wp-admin/admin-post.php\n\nSitemap: https://aggressorbulkit.online/sitemap.xml\nSitemap: https://aggressorbulkit.online/knowledge/sitemap.xml\n", encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({"release": RELEASE, "pages": len(PAGES), "sitemap_urls": sum(1 for p in PAGES if p.include_sitemap and not p.robots.startswith("noindex"))}, indent=2) + "\n", encoding="utf-8")
    print(f"release={RELEASE} pages={len(PAGES)} sitemap_urls={sum(1 for p in PAGES if p.include_sitemap and not p.robots.startswith('noindex'))} out={OUT}")


if __name__ == "__main__":
    main()
