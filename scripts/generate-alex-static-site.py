#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from html import escape
from pathlib import Path
import shutil

SITE = "https://aggressorbulkit.online"
TODAY = date.today().isoformat()

OUT = Path("output/releases/alex-static-native-20260628/web")

NAV = [
    ("/", "Home"),
    ("/services/", "Services"),
    ("/ai-visibility-audit/", "AI Visibility"),
    ("/pricing/", "Pricing"),
    ("/knowledge/", "Base2026"),
    ("/about/", "About"),
]

SERVICE_LINKS = [
    ("/ai-visibility-diagnostic-audit/", "AI Visibility Diagnostic Audit"),
    ("/technical-seo-geo-foundation/", "Technical SEO & GEO Foundation"),
    ("/answer-ready-service-pages/", "Answer-Ready Service Pages"),
    ("/entity-trust-source-intelligence/", "Entity, Trust & Source Intelligence"),
    ("/ai-visibility-source-footprint/", "AI Visibility Source Footprint"),
]

@dataclass
class Page:
    path: str
    title: str
    description: str
    h1: str
    kicker: str
    deck: str
    sections: list[str] = field(default_factory=list)
    body_class: str = "alex-page"
    priority: str = "0.7"


def url(path: str) -> str:
    if path == "/":
        return SITE + "/"
    return SITE + path


def form_html(note: str = "Free AI Search Roadmap request") -> str:
    return f"""
<form id="roadmap-form" class="alex-form" method="post" action="/wp-admin/admin-post.php" data-event="form_start_free_ai_search_roadmap">
  <input type="hidden" name="action" value="ay_audit_snapshot">
  <input type="hidden" name="ay_timing" value="ASAP">
  <input type="hidden" name="ay_preferred_contact" value="Email">
  <input type="hidden" name="ay_notes" value="{escape(note)}">
  <input type="hidden" name="utm_source" value=""><input type="hidden" name="utm_medium" value=""><input type="hidden" name="utm_campaign" value=""><input type="hidden" name="utm_content" value=""><input type="hidden" name="utm_term" value=""><input type="hidden" name="landing_page" value=""><input type="hidden" name="referrer" value="">
  <label>Website URL<input name="ay_website" type="url" inputmode="url" autocomplete="url" placeholder="https://" required></label>
  <label>How should I address you?<input name="ay_name" autocomplete="name" required></label>
  <label>Best contact<input name="ay_contact" autocomplete="email tel" placeholder="Email, phone, or WhatsApp" required></label>
  <button type="submit">Get My Free Roadmap</button>
</form>
"""


def bullets(items: list[str]) -> str:
    return '<ul class="alex-checklist">' + ''.join(f'<li>{escape(i)}</li>' for i in items) + '</ul>'


def cards(items: list[tuple[str, str, str]]) -> str:
    return '<div class="alex-card-grid">' + ''.join(
        f'<article class="alex-card"><p class="alex-card-kicker">{escape(k)}</p><h3>{escape(t)}</h3><p>{escape(d)}</p></article>'
        for k,t,d in items
    ) + '</div>'


def cta(label="Check My AI Visibility", href="/ai-visibility-audit/") -> str:
    return f'<div class="alex-actions"><a class="alex-button" href="{href}">{escape(label)}</a><a class="alex-button-secondary" href="/knowledge/ai-visibility-pages/">Explore Base2026 pages</a></div>'


HOME = Page(
    "/", "Free AI Search Visibility Roadmap | SEO, GEO & AEO",
    "Get a free AI Search Visibility Roadmap for your local service business. See how Google, ChatGPT, Gemini and Perplexity understand your site, competitors and trust signals.",
    "Get Your Free AI Search Roadmap", "AI SEARCH VISIBILITY",
    "Your website, competitors and AI visibility broken down into a practical next-step plan.",
    priority="1.0",
    sections=[
        f'<section class="alex-section alex-split"><div><p class="alex-eyebrow">Start here</p><h2>Why We Give This Away for Free</h2>{bullets(["When business owners see what AI search actually understands about their company, they stop guessing.", "The roadmap shows what to fix first across SEO, GEO, AEO, citations, reviews, schema and content.", "If your market is available and the fit is right, we can handle the implementation. If not, you still keep the roadmap."])}</div><aside class="alex-form-card"><p class="alex-eyebrow">Quick request</p><h2>Get the roadmap</h2>{form_html("Free AI Search Roadmap request from native homepage")}</aside></section>',
        '<section class="alex-section"><p class="alex-eyebrow">How it works</p><h2>What happens after the call</h2>' + cards([
            ("1", "We check your market", "One business per industry per local market. If the market is open, you get priority."),
            ("2", "We build your plan", "Your roadmap becomes a strategy for SEO, GEO, AEO, content, citations, reviews and local visibility."),
            ("3", "We get to work", "No random blog posts. We fix the signals that help AI understand, trust, cite and recommend your business."),
        ]) + '</section>',
        '<section class="alex-section alex-proof"><p class="alex-eyebrow">Who this is for</p><h2>Local service businesses that need leads, not dashboards.</h2><p>Built for roofers, contractors, HVAC companies, plumbers, electricians, dentists, med spas, law firms, landscapers and local service brands that want Google, ChatGPT, Perplexity, Gemini and Copilot to understand and recommend them.</p>' + cta() + '</section>',
    ]
)

SERVICES = Page(
    "/services/", "SEO, GEO & AEO Services for AI Search Visibility",
    "SEO, GEO and AEO services for local service businesses that want stronger visibility across Google, ChatGPT, Gemini, Perplexity and AI-powered search.",
    "SEO, GEO and AEO services built for AI-powered search", "SERVICES",
    "A practical stack for businesses that need to become easier for search engines and answer engines to understand, trust and recommend.",
    priority="0.9",
    sections=[
        '<section class="alex-section"><p class="alex-eyebrow">Core offers</p><h2>Start with the foundation, then build the visibility system.</h2>' + cards([
            ("Audit", "AI Visibility Diagnostic Audit", "A focused diagnosis of crawlability, content, entity clarity, local trust and answer-engine readiness."),
            ("Technical", "Technical SEO & GEO Foundation", "Canonical, sitemap, schema, internal-linking, indexation and performance cleanup."),
            ("Pages", "Answer-Ready Service Pages", "Service pages written for people, search engines and AI answers — clear, specific and citeable."),
            ("Trust", "Entity, Trust & Source Intelligence", "Business profiles, citations, reviews, source footprint and proof signals that support recommendations."),
        ]) + '</section>',
        '<section class="alex-section alex-split"><div><p class="alex-eyebrow">System</p><h2>Services connect directly to Base2026 evidence.</h2><p>The public Base2026 knowledge layer gives us source-backed pages, topic clusters and examples we can link into client strategy instead of inventing generic SEO claims.</p>' + cta("Apply Base2026 Research", "/knowledge/apply-research.html") + '</div><aside class="alex-callout"><h3>Good fit</h3>' + bullets(["Local service business", "Market where one operator can own the category", "Website that needs clear service pages and trust signals", "Owner wants measurable lead growth, not agency theater"]) + '</aside></section>',
    ]
)

PRICING = Page(
    "/pricing/", "AI Search Visibility Pricing | SEO, GEO & AEO Packages",
    "Compare AI Search Visibility pricing for local service businesses: free snapshot, diagnostic audit, 90-day implementation sprint and monthly SEO/GEO/AEO growth support.",
    "AI Search Visibility Pricing", "PRICING",
    "Simple entry points: free snapshot, diagnostic audit, implementation sprint, or monthly growth support.",
    priority="0.9",
    sections=[
        '<section class="alex-section"><p class="alex-eyebrow">Packages</p><h2>Pick the level of help you need now.</h2>' + cards([
            ("Free", "AI Visibility Snapshot", "A quick look at how your business appears across AI search and what the first visibility gaps look like."),
            ("$499", "Diagnostic Audit", "A focused roadmap with technical, content, local and entity recommendations prioritized by impact."),
            ("Sprint", "90-Day Implementation", "We fix foundations, create/update pages, improve trust signals and build a measured visibility system."),
            ("Monthly", "Growth Support", "Ongoing SEO/GEO/AEO, reporting, content and source-footprint work for local markets."),
        ]) + cta("Get Free Snapshot", "/ai-visibility-audit/") + '</section>',
    ]
)

ABOUT = Page(
    "/about/", "About Alex Yarosh | AI Search Visibility Consultant",
    "Alex Yarosh helps local businesses improve visibility across Google, AI Overviews, ChatGPT, Perplexity, Gemini and local search.",
    "You are already paying. Make it an investment.", "ABOUT ALEX",
    "I help local service businesses turn SEO spend into a clearer visibility system across Google, AI answers and local search.",
    priority="0.8",
    sections=[
        '<section class="alex-section alex-split"><div><p class="alex-eyebrow">Point of view</p><h2>No fake hacks. No random posts. No mystery dashboards.</h2><p>Most businesses are not invisible because they need more noise. They are invisible because their website, pages, profiles, citations and proof signals do not make the business easy to understand and trust.</p><p>Base2026 is the research and source layer. The service work is where that evidence becomes practical visibility.</p>' + cta() + '</div><aside class="alex-callout"><h3>What I care about</h3>' + bullets(["Clear site structure", "Service pages that answer real buyer questions", "Entity and source consistency", "Local proof and trust", "Measured lead-growth work"]) + '</aside></section>',
    ]
)

AUDIT = Page(
    "/ai-visibility-audit/", "Free AI Visibility Snapshot | AI Search Check",
    "Check how your business appears across ChatGPT, Google AI Overviews, Gemini and Perplexity. Compare competitors and find the first visibility fixes.",
    "Find out if AI recommends your business, or your competitors", "FREE SNAPSHOT",
    "A fast diagnostic for local service businesses that need to understand their AI-search visibility before spending more on SEO.",
    priority="0.95",
    sections=[
        f'<section class="alex-section alex-split"><div><p class="alex-eyebrow">What we check</p><h2>Your business, competitors and source footprint.</h2>{bullets(["Can AI systems identify your business and services?", "Do your service pages answer the right questions?", "Are reviews, citations and profiles consistent?", "Do competitors have stronger trust/source signals?", "What should be fixed first?"])}</div><aside class="alex-form-card"><p class="alex-eyebrow">Request snapshot</p><h2>Get My Free Roadmap</h2>{form_html("Free AI Visibility Snapshot request from native audit page")}</aside></section>',
    ]
)

DETAILS = [
    Page("/ai-visibility-diagnostic-audit/", "AI Visibility Diagnostic Audit | Alex Yarosh", "A focused diagnostic audit for AI search visibility, SEO, GEO, AEO, content, technical foundations and trust signals.", "AI Visibility Diagnostic Audit", "DIAGNOSTIC", "A paid, focused audit when you need a clear action plan before a larger build.", sections=['<section class="alex-section"><h2>What the audit covers</h2>' + bullets(["Technical SEO and indexation", "AI-answer readiness", "Service-page clarity", "Entity and citation consistency", "Competitor/source footprint", "Prioritized next actions"]) + cta("Request Diagnostic Audit", "/ai-visibility-audit/?plan=diagnostic") + '</section>']),
    Page("/technical-seo-geo-foundation/", "Technical SEO & GEO Foundation | Alex Yarosh", "Technical SEO and GEO foundation work for local businesses: crawlability, indexation, schema, internal links, speed and AI-search readiness.", "Technical SEO & GEO Foundation", "FOUNDATION", "Fix the technical signals before scaling content or money pages.", sections=['<section class="alex-section"><h2>Foundation work</h2>' + bullets(["Robots, sitemap and canonical cleanup", "Schema and entity clarity", "Internal-linking paths", "Performance and asset cleanup", "Indexation monitoring"]) + cta() + '</section>']),
    Page("/answer-ready-service-pages/", "Answer-Ready Service Pages | Alex Yarosh", "Service pages built for SEO, GEO and AEO: clear buyer answers, local relevance, trust signals and AI-search citeability.", "Answer-Ready Service Pages", "SERVICE PAGES", "Pages that are specific enough for buyers and structured enough for answer engines.", sections=['<section class="alex-section"><h2>What makes a page answer-ready</h2>' + bullets(["Clear service and market", "Direct answers to buyer questions", "Proof and local trust", "Schema-ready structure", "Internal links to supporting evidence"]) + cta() + '</section>']),
    Page("/entity-trust-source-intelligence/", "Entity, Trust & Source Intelligence | Alex Yarosh", "Entity, trust and source intelligence for AI search visibility: citations, profiles, reviews, mentions and source footprint.", "Entity, Trust & Source Intelligence", "TRUST", "Make the business easier to verify across the sources AI systems can see.", sections=['<section class="alex-section"><h2>Trust signals we map</h2>' + bullets(["Business profiles and NAP consistency", "Reviews and reputation signals", "Third-party citations", "Mentions and source footprint", "Competitor trust gaps"]) + cta() + '</section>']),
    Page("/ai-visibility-source-footprint/", "AI Visibility Source Footprint | Alex Yarosh", "Map the external sources, citations, profiles and proof signals that influence AI search visibility and recommendations.", "AI Visibility Source Footprint", "SOURCE FOOTPRINT", "A practical map of what AI can verify about your business beyond your website.", sections=['<section class="alex-section"><h2>Source footprint includes</h2>' + bullets(["Public profiles", "Local citations", "Review platforms", "Industry directories", "Content and proof pages", "Competitor source overlap"]) + cta("See Base2026 Library", "/knowledge/ai-visibility-resources.html") + '</section>']),
]

RESOURCES = [
    Page("/what-is-ai-search-visibility/", "What Is AI Search Visibility for Local Businesses?", "AI Search Visibility means your business can be found, understood and recommended by AI-powered search tools such as ChatGPT, AI Overviews, Gemini and Perplexity.", "What Is AI Search Visibility for Local Businesses?", "RESOURCE", "AI Search Visibility combines SEO, GEO, AEO, structured content, entity trust and external validation.", sections=['<section class="alex-section"><p>For local businesses, visibility is no longer only about blue links. Search engines and AI systems need clear pages, consistent entities, reviews, citations and trusted sources before they can recommend a business confidently.</p>' + cta() + '</section>']),
    Page("/why-chatgpt-does-not-recommend-your-business/", "Why ChatGPT Does Not Recommend Your Business", "Common reasons ChatGPT and AI search systems do not recommend a local business: unclear services, weak trust signals, thin pages and missing source footprint.", "Why ChatGPT Does Not Recommend Your Business", "RESOURCE", "Usually the problem is not one magic ranking factor. It is a weak set of signals.", sections=['<section class="alex-section">' + bullets(["Services are unclear or generic", "The business lacks consistent external proof", "Pages do not answer buyer questions", "Competitors have stronger citations and reviews", "Important pages are hard to crawl or index"]) + cta() + '</section>']),
    Page("/when-to-rebuild-website-for-seo/", "When Should a Business Rebuild Its Website for SEO?", "A business should rebuild its website for SEO when the current site blocks crawlability, clarity, conversion, content structure or AI-search visibility.", "When Should a Business Rebuild Its Website for SEO?", "RESOURCE", "Do not rebuild for aesthetics alone. Rebuild when the site blocks growth.", sections=['<section class="alex-section">' + bullets(["Important pages are thin or buried", "Technical SEO is hard to fix in the current stack", "Design blocks conversion", "The site cannot support service/location pages", "Content and internal links are chaotic"]) + cta() + '</section>']),
]

PRIVACY = Page("/privacy-policy/", "Privacy Policy | Alex Yarosh", "Privacy policy for Alex Yarosh and Base2026 visibility services.", "Privacy Policy", "LEGAL", "Basic privacy information for roadmap requests and website usage.", priority="0.3", sections=['<section class="alex-section"><p>When you submit a form, we collect the information you provide so we can review your website and respond to your request. We do not sell personal information. Analytics and cookies may be used to understand site performance and improve the service.</p><p>For privacy questions, contact Alex through the same business contact channels used for service requests.</p></section>'])
THANKS = Page("/thank-you-ai-visibility-audit/", "Thank You | AI Visibility Request", "Thank you for requesting an AI visibility roadmap.", "Request received", "THANK YOU", "We received your request. The next step is a quick review of your website and market.", priority="0.2", sections=['<section class="alex-section"><p>Thanks. We will review the website and contact details you submitted and follow up with the next step.</p><a class="alex-button" href="/knowledge/ai-visibility-pages/">Explore AI Visibility Pages</a></section>'])

PAGES = [HOME, SERVICES, AUDIT, PRICING, ABOUT, *DETAILS, *RESOURCES, PRIVACY, THANKS]

CSS = """
:root{--ink:#111;--muted:#59636b;--paper:#f7f2e9;--card:#fffaf1;--line:rgba(18,26,31,.14);--orange:#ef6b13;--orange-dark:#b74704;--green:#283b2b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Geist,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.55}.skip-link{position:absolute;left:-999px}.site-header{position:sticky;top:0;z-index:20;background:rgba(247,242,233,.92);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}.nav{max-width:1180px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:18px}.brand{font-weight:800;color:var(--ink);text-decoration:none}.links{display:flex;gap:14px;align-items:center;margin-left:auto}.links a{color:var(--ink);text-decoration:none;font-size:14px}.nav-cta,.alex-button{background:var(--orange);color:#111!important;text-decoration:none;border:1px solid rgba(17,17,17,.22);box-shadow:4px 4px 0 #111;border-radius:4px;padding:10px 14px;font-weight:800;display:inline-flex}.alex-button-secondary{border:1px solid var(--line);color:#111;text-decoration:none;border-radius:4px;padding:10px 14px;font-weight:700;background:#fffaf1}.wrap{max-width:1180px;margin:0 auto;padding:0 20px}.hero{margin:22px auto 24px;display:grid;grid-template-columns:minmax(0,.95fr) minmax(300px,.65fr);gap:24px;align-items:stretch}.hero-orange{position:relative;overflow:hidden;min-height:370px;padding:clamp(34px,5vw,70px);border:1px solid rgba(17,17,17,.18);border-radius:8px;background:radial-gradient(circle at 18% 18%,rgba(255,255,255,.18),transparent 34%),repeating-linear-gradient(135deg,rgba(17,17,17,.06) 0,rgba(17,17,17,.06) 1px,transparent 1px,transparent 8px),linear-gradient(90deg,rgba(239,107,19,.98),rgba(214,82,9,.96) 63%,rgba(171,59,3,.92));}.eyebrow,.alex-eyebrow,.alex-card-kicker{font-family:'Geist Mono',ui-monospace,monospace;text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:800;color:#253025}.hero h1{position:relative;z-index:2;font-family:'Barlow Condensed','Arial Narrow',sans-serif;font-size:clamp(44px,6vw,84px);line-height:.9;margin:16px 0;text-transform:uppercase;max-width:min(760px,68%)}.hero p{position:relative;z-index:2;font-size:clamp(18px,2.2vw,25px);font-weight:650;max-width:min(680px,66%)}.hero-img{align-self:end;justify-self:end;max-width:280px;width:30%;min-width:180px;position:absolute;right:2%;bottom:0;z-index:1;filter:drop-shadow(0 28px 38px rgba(17,17,17,.32))}.hero-panel{background:#fffaf1;border:1px solid var(--line);border-radius:8px;padding:28px;box-shadow:8px 8px 0 rgba(17,17,17,.08)}.alex-section{max-width:1180px;margin:22px auto;padding:34px 20px;background:#fffaf1;border:1px solid var(--line);border-radius:8px}.alex-section h2{font-size:clamp(28px,3vw,44px);line-height:1.02;margin:8px 0 18px}.alex-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.55fr);gap:24px}.alex-card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.alex-card,.alex-callout,.alex-form-card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:20px}.alex-card h3{margin:6px 0 8px;font-size:22px}.alex-checklist{padding:0;margin:16px 0;list-style:none;display:grid;gap:10px}.alex-checklist li{padding-left:26px;position:relative}.alex-checklist li:before{content:'✓';position:absolute;left:0;color:var(--orange-dark);font-weight:900}.alex-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}.alex-form{display:grid;gap:12px}.alex-form label{font-weight:700;font-size:14px}.alex-form input{width:100%;margin-top:5px;padding:12px;border:1px solid var(--line);border-radius:4px;background:#fff}.alex-form button{cursor:pointer;background:var(--orange);border:1px solid #111;box-shadow:4px 4px 0 #111;border-radius:4px;padding:12px 14px;font-weight:900}.alex-proof{background:#1f2c22;color:#f7f2e9}.alex-proof .alex-eyebrow{color:#ffcfaa}.alex-proof .alex-button-secondary{background:transparent;color:#f7f2e9;border-color:rgba(247,242,233,.35)}.footer{margin-top:40px;background:#111;color:#f7f2e9}.footer a{color:#f7f2e9}.footer-grid{max-width:1180px;margin:0 auto;padding:34px 20px;display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:24px}.footer ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}.breadcrumbs{max-width:1180px;margin:18px auto 0;padding:0 20px;color:var(--muted);font-size:13px}.breadcrumbs a{color:var(--muted)}@media(max-width:860px){.links{display:none}.hero,.alex-split,.footer-grid{grid-template-columns:1fr}.hero-img{opacity:.2;width:260px}.alex-card-grid{grid-template-columns:1fr}.hero-orange{min-height:320px}}
"""


def header(current: str) -> str:
    links = ''.join(f'<a href="{href}" aria-current="page" data-current="true">{label}</a>' if href == current else f'<a href="{href}">{label}</a>' for href,label in NAV)
    return f'<header class="site-header"><nav class="nav" aria-label="Primary"><a class="brand" href="/">Alex Yarosh</a><div class="links">{links}<a class="nav-cta" href="/ai-visibility-audit/">Check My AI Visibility</a></div></nav></header>'


def footer() -> str:
    services = ''.join(f'<li><a href="{href}">{escape(label)}</a></li>' for href,label in SERVICE_LINKS)
    return f'''<footer class="footer"><div class="footer-grid"><div><p class="eyebrow">AI Search Visibility</p><h2>Search visibility for local service businesses</h2><p>SEO, GEO, AEO, content, schema, trust signals and source-backed Base2026 research.</p><div class="alex-actions"><a class="alex-button" href="/ai-visibility-audit/">Get My Free Roadmap</a></div></div><nav><h3>Services</h3><ul>{services}</ul></nav><nav><h3>Base2026</h3><ul><li><a href="/knowledge/">Search Base2026</a></li><li><a href="/knowledge/ai-visibility-pages/">AI Visibility Pages</a></li><li><a href="/knowledge/ai-visibility-resources.html">AI Visibility Library</a></li><li><a href="/knowledge/apply-research.html">Apply Research</a></li><li><a href="/privacy-policy/">Privacy</a></li></ul></nav></div></footer>'''


def render(page: Page) -> str:
    canonical = url(page.path)
    crumb = '' if page.path == '/' else f'<div class="breadcrumbs"><a href="/">Alex Yarosh</a> / {escape(page.h1)}</div>'
    section_html = '\n'.join(page.sections)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page.title)}</title>
<meta name="description" content="{escape(page.description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Geist+Mono:wght@500;700&family=Geist:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/alex-static/styles.css?v=alex-static-native-20260628">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":{page.title!r},"description":{page.description!r},"url":{canonical!r},"isPartOf":{{"@type":"WebSite","name":"Alex Yarosh","url":"{SITE}/"}}}}</script>
</head>
<body class="{escape(page.body_class)}">
<a class="skip-link" href="#content">Skip to content</a>
{header(page.path)}
{crumb}
<main id="content">
  <section class="wrap hero" aria-label="Hero">
    <div class="hero-orange">
      <p class="eyebrow">{escape(page.kicker)}</p>
      <h1>{escape(page.h1)}</h1>
      <p>{escape(page.deck)}</p>
      <img class="hero-img" src="/knowledge/static/assets/alex-yarosh-cutout-v115.png" alt="Alex Yarosh" width="1400" height="1264" loading="eager" decoding="async">
    </div>
    <aside class="hero-panel"><p class="alex-eyebrow">Start with proof</p><h2>Base2026-backed visibility work</h2><p>Every recommendation should connect to crawlable pages, clear service logic, source evidence or measurable search behavior.</p>{cta()}</aside>
  </section>
  {section_html}
</main>
{footer()}
<script>document.querySelectorAll('input[name="landing_page"]').forEach(i=>i.value=location.href);document.querySelectorAll('input[name="referrer"]').forEach(i=>i.value=document.referrer||'');</script>
</body>
</html>'''


def write_page(page: Page):
    if page.path == '/':
        target = OUT / 'index.html'
    else:
        target = OUT / page.path.strip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(page), encoding='utf-8')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'alex-static').mkdir(parents=True, exist_ok=True)
    (OUT / 'alex-static' / 'styles.css').write_text(CSS, encoding='utf-8')
    for page in PAGES:
        write_page(page)
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in PAGES:
        sitemap.append(f'<url><loc>{url(p.path)}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p.priority}</priority></url>')
    sitemap.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sitemap), encoding='utf-8')
    (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /wp-admin/\nAllow: /wp-admin/admin-post.php\n\nSitemap: https://aggressorbulkit.online/sitemap.xml\nSitemap: https://aggressorbulkit.online/knowledge/sitemap.xml\n', encoding='utf-8')
    (OUT / 'manifest.json').write_text('{"name":"Alex Yarosh","release":"alex-static-native-20260628"}\n', encoding='utf-8')
    print(f'pages={len(PAGES)} out={OUT}')

if __name__ == '__main__':
    main()
