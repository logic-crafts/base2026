from __future__ import annotations

import re
from html import escape
from pathlib import Path

SHELL_VERSION = "20260713-alex-v4-static-footer-live-v3"
ROOT = Path(__file__).resolve().parents[1]
LIVE_FOOTER_TEMPLATE = ROOT / "templates" / "shared" / "alex-home-v4-footer.html"


def header_html() -> str:
    return """<header class="ay-v2-header" data-ay-v2-header aria-label="Alex Yarosh primary header">
      <div class="ay-v2-header-shell">
        <a class="ay-v2-brand" href="/" aria-label="Alex Yarosh home">Alex Yarosh</a>
        <nav class="ay-v2-nav" aria-label="Primary navigation">
          <div class="ay-v2-nav-item ay-v2-has-mega">
            <a href="/services/">Services</a>
            <div class="ay-v2-mega" role="menu" aria-label="Services menu">
              <div class="ay-v2-mega-grid">
                <section><h3>Core Services</h3><a href="/ai-visibility-diagnostic-audit/"><strong>Diagnostic Audit</strong><span>Find the weak layer before spending on more work.</span></a><a href="/technical-seo-geo-foundation/"><strong>Technical SEO &amp; GEO</strong><span>Fix crawlability, indexation, canonicals and schema.</span></a></section>
                <section><h3>Strategic Growth</h3><a href="/answer-ready-service-pages/"><strong>Answer-ready Pages</strong><span>Turn vague pages into decision-stage answers.</span></a><a href="/entity-trust-source-intelligence/"><strong>Entity Intelligence</strong><span>Strengthen citations, reviews and public footprint.</span></a></section>
              </div>
              <a class="ay-v2-mega-all" href="/services/">View all services <span aria-hidden="true">→</span></a>
            </div>
          </div>
          <a href="/ai-visibility-audit/">AI Visibility</a><a href="/pricing/">Pricing</a>
          <div class="ay-v2-nav-item ay-v2-has-mega ay-v2-base-trigger">
            <a href="/knowledge/">Base2026</a>
            <div class="ay-v2-mega ay-v2-base-mega" role="menu" aria-label="Base2026 menu">
              <div class="ay-v2-mega-grid">
                <section><h3>Research workspace</h3><a href="/knowledge/"><strong>Search the library</strong><span>Find sources, claims, creators and topics.</span></a><a href="/knowledge/sources/"><strong>Source Intelligence</strong><span>Read reviewed source text, exact claims and bounded actions.</span></a><a href="/knowledge/topics/"><strong>Topics &amp; viewpoints</strong><span>Synthesize evidence and compare creators inside one topic.</span></a></section>
                <section><h3>Decision support</h3><a href="/knowledge/solutions/"><strong>AI Recommends Solutions</strong><span>Turn source evidence into bounded operating decisions.</span></a><a href="/knowledge/creators/"><strong>Creators</strong><span>Browse attributed expert source profiles.</span></a><a href="/knowledge/methodology.html"><strong>Methodology</strong><span>Review the evidence, editorial and publication rules.</span></a></section>
              </div>
              <form class="ay-v2-mega-search" method="get" action="/knowledge/" role="search"><label for="ay-v2-mega-search-input">Quick search</label><input id="ay-v2-mega-search-input" name="q" type="search" aria-label="Search Base2026"><button type="submit">Search</button></form>
            </div>
          </div>
          <a href="/about/">About</a>
        </nav>
        <a class="ay-v2-header-cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
        <button class="ay-v2-menu-toggle" type="button" aria-expanded="false" aria-controls="ay-v2-mobile-panel">Menu</button>
      </div>
      <div class="ay-v2-mobile-panel" id="ay-v2-mobile-panel" hidden><a href="/services/">Services</a><a href="/ai-visibility-audit/">AI Visibility</a><a href="/pricing/">Pricing</a><a href="/knowledge/">Search Base2026</a><a href="/knowledge/sources/">Source Intelligence</a><a href="/knowledge/topics/">Topics &amp; viewpoints</a><a href="/knowledge/solutions/">AI Recommends Solutions</a><a href="/knowledge/creators/">Creators</a><a href="/about/">About</a></div>
    </header>"""


def _legacy_footer_html() -> str:
    return """<footer class="ay-site-footer" aria-label="Site footer">
      <div class="ay-wrap ay-footer-grid">
        <section><p class="ay-eyebrow">AI Search Visibility</p><h2>Make your business easier to find, verify, and recommend</h2><p>We help local service businesses become easier to find, understand, verify, and recommend across Google, AI search, and modern discovery systems.</p><div class="ay-actions"><a class="ay-button" href="/ai-visibility-audit/" data-cta="get_my_free_roadmap">Get Free Snapshot</a><a class="ay-button-secondary" href="/pricing/">View Pricing</a><a class="ay-button ay-button-base2026" href="/knowledge/apply-research.html">Apply Base2026 Research</a></div><div class="ay-footer-socials" aria-label="Social profiles"><p class="ay-footer-socials__label">Socials</p><div class="ay-footer-socials__links"><a class="ay-social-link" href="https://x.com/AleksejAros" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on X"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 2h3.3l-7.2 8.2L23.5 22h-6.7l-5.2-6.8L5.6 22H2.3l7.7-8.8L1.9 2h6.8l4.7 6.2L18.9 2Zm-1.2 17.9h1.8L7.7 4H5.8l11.9 15.9Z"/></svg></a><a class="ay-social-link" href="https://github.com/offflinerpsy" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on GitHub"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5A11.5 11.5 0 0 0 8.36 22.9c.58.11.8-.25.8-.56v-2.02c-3.25.71-3.94-1.38-3.94-1.38-.53-1.35-1.3-1.71-1.3-1.71-1.06-.73.08-.72.08-.72 1.18.08 1.8 1.21 1.8 1.21 1.04 1.79 2.74 1.27 3.41.97.11-.76.41-1.27.74-1.56-2.59-.29-5.31-1.3-5.31-5.76 0-1.27.45-2.31 1.2-3.13-.12-.29-.52-1.48.12-3.09 0 0 .98-.31 3.21 1.19A11.08 11.08 0 0 1 12 5.96c.99 0 1.98.13 2.91.39 2.22-1.5 3.2-1.19 3.2-1.19.64 1.61.24 2.8.12 3.09.75.82 1.2 1.86 1.2 3.13 0 4.47-2.73 5.46-5.33 5.75.42.36.79 1.08.79 2.17v3.04c0 .31.21.68.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg></a></div></div></section>
        <nav aria-label="Services"><h3>Services</h3><ul class="ay-footer-menu"><li><a href="/services/">Services hub</a></li><li><a href="/services/#local-seo">Source footprint</a></li><li><a href="/services/#content-strategy">Content engine</a></li><li><a href="/services/#analytics">Measurement stack</a></li></ul></nav>
        <nav aria-label="Start Here"><h3>Start Here</h3><ul class="ay-footer-menu"><li><a href="/contact/">Contact</a></li><li><a href="/work/">Selected work</a></li><li><a href="/free-ai-marketing-tools/">Free AI tools</a></li></ul></nav>
        <nav aria-label="Base2026"><h3>Base2026 pilot project</h3><p>Base2026 is my open pilot project for building a curated source base for AI recommendation engines.</p><ul class="ay-footer-menu"><li><a href="/knowledge/">Search the knowledge base</a></li><li><a href="/knowledge/roadmap.html">Base2026 Roadmap</a></li><li><a href="/knowledge/support.html">Support Base2026</a></li><li><a href="/knowledge/apply-research.html">Apply to participate</a></li><li><a href="/knowledge/api.html">API access</a></li><li><a href="/knowledge/topics.html">Browse topics</a></li><li><a href="/knowledge/creators.html">Explore creators</a></li><li><a href="/knowledge/methodology.html">Methodology</a></li></ul></nav>
        <nav aria-label="Legal"><h3>Legal</h3><ul class="ay-footer-menu"><li><a href="/privacy-policy/">Privacy policy</a></li><li><button type="button" class="ay-footer-link-button" data-cookie-preferences="">Cookie Preferences</button></li><li><a href="/terms/">Terms</a></li></ul></nav>
      </div><div class="ay-footer-bottom"><span>© 2026 Alex Yarosh — AI marketing specialist. Independent consultant working in AI-enabled SEO and content systems.</span></div>
    </footer>"""


def _obsolete_footer_html() -> str:
    """Return the captured current-live WordPress footer authority.

    Keep this markup portable and deterministic.  The absolute production
    URLs are intentional: the strict visual/semantic parity gate compares
    the live footer's literal navigation contract, not merely resolved URLs.
    """
    return """<footer class="ay-site-footer" aria-label="Site footer">
      <div class="ay-wrap ay-footer-grid">
        <section>
          <p class="ay-eyebrow">AI Marketing Systems</p>
          <h2>Make your business easier to find, verify, and recommend</h2>
          <p></p>
          <div class="ay-actions">
            <a class="ay-button" href="https://aggressorbulkit.online/ai-visibility-audit/">AI Visibility Diagnostic</a>
            <a class="ay-button-secondary" href="https://aggressorbulkit.online/contact/">Get in Touch</a>
            <a class="ay-button ay-button-base2026" href="https://aggressorbulkit.online/knowledge/apply-research.html">Apply for Base2026</a>
          </div>
          <div class="ay-footer-socials" aria-label="Social profiles">
            <p class="ay-footer-socials__label">Socials</p>
            <div class="ay-footer-socials__links">
              <a class="ay-social-link" href="https://x.com/AleksejAros" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on X" title="Alex Yarosh on X"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 2h3.3l-7.2 8.2L23.5 22h-6.7l-5.2-6.8L5.6 22H2.3l7.7-8.8L1.9 2h6.8l4.7 6.2L18.9 2Zm-1.2 17.9h1.8L7.7 4H5.8l11.9 15.9Z"/></svg></a>
              <a class="ay-social-link" href="https://github.com/offflinerpsy" target="_blank" rel="me noopener noreferrer" aria-label="Alex Yarosh on GitHub" title="Alex Yarosh on GitHub"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .7C5.7.7.7 5.8.7 12.1c0 5 3.2 9.2 7.7 10.7.6.1.8-.2.8-.6v-2.2c-3.1.7-3.8-1.3-3.8-1.3-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 1.7 2.6 1.2 3.2.9.1-.7.4-1.2.7-1.5-2.5-.3-5.1-1.3-5.1-5.6 0-1.2.4-2.2 1.1-3-.1-.3-.5-1.5.1-3 0 0 .9-.3 3.1 1.1.9-.3 1.9-.4 2.8-.4s1.9.1 2.8.4c2.1-1.5 3.1-1.1 3.1-1.1.6 1.5.2 2.7.1 3 .7.8 1.1 1.8 1.1 3 0 4.4-2.6 5.3-5.1 5.6.4.4.8 1.1.8 2.1v3.1c0 .4.2.7.8.6 4.5-1.5 7.7-5.7 7.7-10.7C23.3 5.8 18.3.7 12 .7Z"/></svg></a>
              <span class="ay-social-link ay-social-link--disabled" aria-label="TikTok profile coming soon" title="TikTok profile coming soon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.2 2h3.2c.2 1.7 1.2 3.2 2.7 4.1.8.5 1.7.8 2.7.8v3.3c-1.9 0-3.8-.6-5.3-1.7v7.1a6.8 6.8 0 1 1-5.9-6.8v3.4a3.5 3.5 0 1 0 2.6 3.4V2Z"/></svg></span>
            </div>
          </div>
        </section>
        <nav aria-label="Services"><h3>Services</h3><ul class="ay-footer-menu"><li><a href="https://aggressorbulkit.online/ai-visibility-audit/">AI Visibility Diagnostic</a></li><li><a href="https://aggressorbulkit.online/ai-growth-strategy-roadmap/">AI Growth Strategy Roadmap</a></li><li><a href="https://aggressorbulkit.online/digital-authority-optimization/">Digital Authority Optimization</a></li><li><a href="https://aggressorbulkit.online/ai-citation-readiness/">AI Citation Readiness</a></li><li><a href="https://aggressorbulkit.online/ai-first-brand-positioning/">AI-First Brand Positioning</a></li><li><a href="https://aggressorbulkit.online/custom-ai-marketing-systems/">Custom AI Marketing Systems</a></li></ul></nav>
        <nav aria-label="Start Here"><h3>Start Here</h3><ul class="ay-footer-menu"><li><a href="https://aggressorbulkit.online/ai-visibility-audit/">AI Visibility Diagnostic</a></li><li><a href="https://aggressorbulkit.online/work/">Case Studies</a></li><li><a href="https://aggressorbulkit.online/about/">About Me</a></li><li><a href="https://aggressorbulkit.online/pricing/">Pricing</a></li><li><a href="https://aggressorbulkit.online/contact/">Contact</a></li></ul></nav>
        <nav aria-label="Base2026"><h3>Base2026 pilot project</h3><p>Base2026 is my open pilot project for building a curated source base for AI recommendation engines.</p><ul class="ay-footer-menu"><li><a href="https://aggressorbulkit.online/knowledge/">Search the knowledge base</a></li><li><a href="https://aggressorbulkit.online/knowledge/roadmap.html">Base2026 Roadmap</a></li><li><a href="https://aggressorbulkit.online/knowledge/support.html">Support Base2026</a></li><li><a href="https://aggressorbulkit.online/knowledge/apply-research.html">Apply to participate</a></li><li><a href="https://aggressorbulkit.online/knowledge/api.html">API access</a></li><li><a href="https://aggressorbulkit.online/knowledge/topics.html">Browse topics</a></li><li><a href="https://aggressorbulkit.online/knowledge/creators.html">Explore creators</a></li><li><a href="https://aggressorbulkit.online/knowledge/methodology.html">Methodology</a></li></ul></nav>
        <nav aria-label="Legal"><h3>Legal</h3><ul class="ay-footer-menu"><li><a href="https://aggressorbulkit.online/privacy-policy/">Privacy Policy</a></li><li><button type="button" class="ay-footer-link-button" data-cookie-preferences>Cookie Preferences</button></li></ul></nav>
      </div>
      <div class="ay-footer-bottom"><span>© 2026 Alex Yarosh. Independent AI marketing specialist.</span></div>
    </footer>"""


def footer_html() -> str:
    """Render the frozen current-live Home v4 footer template.

    The template was captured from production WordPress and is SHA-locked by
    the independent candidate validator. Keeping renderer markup in one
    template prevents legacy/current function-selection regressions.
    """
    inner = LIVE_FOOTER_TEMPLATE.read_text(encoding="utf-8").strip()
    return f'<footer class="ay-site-footer" aria-label="Site footer">\n{inner}\n</footer>'


def apply_alex_v4_shell(page: str, relative_root: str = "..") -> str:
    page = re.sub(r'<header class="site-header">.*?</header>', header_html(), page, count=1, flags=re.S)
    page = re.sub(r'<footer class="site-footer">.*?</footer>', footer_html(), page, count=1, flags=re.S)
    page = page.replace("<body>", '<body class="ay-alex-v4-static ay-stitch-home-v3 ay-stitch-home-v4">', 1)
    assets = (
        f'    <link rel="stylesheet" href="{escape(relative_root)}/static/alex-v4-static-shell.css?v={SHELL_VERSION}" />\n'
        f'    <script src="{escape(relative_root)}/static/alex-v4-static-shell.js?v={SHELL_VERSION}" defer></script>\n'
    )
    return page.replace("  </head>", assets + "  </head>", 1)


def shell_js() -> str:
    return """(() => {
  const body = document.body;
  const button = document.querySelector('.ay-v2-menu-toggle');
  const panel = document.getElementById('ay-v2-mobile-panel');
  const sync = () => body.classList.toggle('ay-v2-condensed', window.scrollY > 44);
  sync();
  window.addEventListener('scroll', sync, { passive: true });
  if (!button || !panel) return;
  const setOpen = (open) => { panel.toggleAttribute('hidden', !open); button.setAttribute('aria-expanded', open ? 'true' : 'false'); body.classList.toggle('ay-v2-menu-open', open); };
  button.addEventListener('click', () => setOpen(panel.hasAttribute('hidden')));
  panel.addEventListener('click', event => { if (event.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') setOpen(false); });
})();\n"""


def shell_css() -> str:
    return r"""@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
body.ay-alex-v4-static{--stitch-cream:#F4F1E9;--stitch-paper:#fff;--stitch-ink:#0F172A;--stitch-muted:#5f5e58;--stitch-soft:#E5E2DA;--stitch-line:rgba(15,23,42,.10);margin:0;background:var(--stitch-cream);color:var(--stitch-ink);font-family:Manrope,Inter,ui-sans-serif,system-ui,sans-serif;padding-top:100px}
body.ay-alex-v4-static *{box-sizing:border-box} body.ay-alex-v4-static a{color:inherit}
.ay-v2-header{position:fixed;inset:0 0 auto;z-index:9999;pointer-events:none;padding:14px 0 0;transition:padding .34s ease}.ay-v2-header-shell{width:min(100% - 72px,1120px);height:72px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:22px;padding:0 22px;border:1px solid rgba(15,23,42,.06);background:rgba(244,241,233,.92);backdrop-filter:blur(18px) saturate(160%);box-shadow:0 12px 38px rgba(15,23,42,.035);pointer-events:auto;transition:width .36s,height .36s,border-radius .36s,background .36s,box-shadow .36s}.ay-v2-brand{font:800 21px/1 Manrope,sans-serif;letter-spacing:-.035em;text-decoration:none;white-space:nowrap}.ay-v2-nav{display:flex;align-items:center;gap:24px;height:100%}.ay-v2-nav>a,.ay-v2-nav-item>a,.ay-v2-header-cta,.ay-v2-menu-toggle{font:700 12px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase;text-decoration:none}.ay-v2-nav>a,.ay-v2-nav-item>a{position:relative;display:flex;align-items:center;height:100%}.ay-v2-nav>a:after,.ay-v2-nav-item>a:after{content:"";position:absolute;left:0;right:0;bottom:18px;height:1px;background:var(--stitch-ink);transform:scaleX(0);transition:transform .25s}.ay-v2-nav>a:hover:after,.ay-v2-nav-item:hover>a:after{transform:scaleX(1)}.ay-v2-header-cta{display:inline-flex;align-items:center;min-height:40px;padding:0 17px;border-radius:999px;background:var(--stitch-ink);color:#fff!important;white-space:nowrap;transition:transform .25s,opacity .25s,max-width .35s,padding .35s}.ay-v2-header-cta:hover{transform:translateY(-1px)}.ay-v2-menu-toggle{display:none;border:0;background:transparent;cursor:pointer}.ay-v2-nav-item{height:100%;display:flex;align-items:center;position:relative}.ay-v2-mega{position:absolute;top:66px;left:50%;width:min(680px,calc(100vw - 48px));padding:22px;border:1px solid var(--stitch-line);border-radius:24px;background:rgba(255,255,255,.97);box-shadow:0 28px 70px rgba(15,23,42,.16);opacity:0;visibility:hidden;transform:translate(-50%,10px);transition:.22s;pointer-events:none}.ay-v2-base-mega{left:auto;right:-160px;transform:translate(0,10px)}.ay-v2-nav-item:hover .ay-v2-mega,.ay-v2-nav-item:focus-within .ay-v2-mega{opacity:1;visibility:visible;transform:translate(-50%,0);pointer-events:auto}.ay-v2-base-trigger:hover .ay-v2-base-mega,.ay-v2-base-trigger:focus-within .ay-v2-base-mega{transform:translate(0,0)}.ay-v2-mega-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.ay-v2-mega h3{margin:0 0 12px;color:rgba(15,23,42,.52);font:700 11px/1 Geist,sans-serif;letter-spacing:.12em;text-transform:uppercase}.ay-v2-mega section>a{display:block;padding:11px;border-radius:12px;text-decoration:none}.ay-v2-mega section>a:hover{background:#F4F1E9}.ay-v2-mega strong{display:block;font-size:14px}.ay-v2-mega span{display:block;margin-top:4px;color:rgba(15,23,42,.61);font-size:12px;line-height:1.4}.ay-v2-mega-all{display:block;margin-top:14px;padding-top:14px;border-top:1px solid var(--stitch-line);font:700 12px Geist,sans-serif;text-decoration:none}.ay-v2-mega-search{display:grid;grid-template-columns:1fr auto;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid var(--stitch-line)}.ay-v2-mega-search label{grid-column:1/-1;font:700 10px Geist,sans-serif;letter-spacing:.12em;text-transform:uppercase}.ay-v2-mega-search input{min-width:0;border:1px solid var(--stitch-line);border-radius:999px;padding:10px 14px;font:500 13px Manrope,sans-serif}.ay-v2-mega-search button{border:0;border-radius:999px;padding:0 16px;background:var(--stitch-ink);color:#fff;font:700 11px Geist,sans-serif;text-transform:uppercase}.ay-v2-mobile-panel{width:min(100% - 32px,680px);margin:8px auto 0;padding:14px;border:1px solid var(--stitch-line);border-radius:22px;background:rgba(255,255,255,.98);box-shadow:0 24px 60px rgba(15,23,42,.15);pointer-events:auto}.ay-v2-mobile-panel a{display:block;padding:12px 10px;border-bottom:1px solid rgba(15,23,42,.06);font:700 12px Geist,sans-serif;letter-spacing:.08em;text-transform:uppercase;text-decoration:none}.ay-v2-mobile-panel a:last-child{border-bottom:0}.ay-v2-condensed .ay-v2-header{padding-top:10px}.ay-v2-condensed .ay-v2-header-shell{width:min(max-content,calc(100% - 40px));height:50px;padding:0 18px;border-radius:999px;background:rgba(255,255,255,.78);box-shadow:0 18px 50px rgba(15,23,42,.12)}.ay-v2-condensed .ay-v2-brand,.ay-v2-condensed .ay-v2-header-cta{opacity:0;max-width:0;padding-left:0;padding-right:0;overflow:hidden;pointer-events:none}
/* The reading column is never wider than the desktop header plate. */
body.ay-alex-v4-static main.app-shell{width:min(100% - 72px,1120px);max-width:1120px;margin:0 auto;padding:28px 0 92px}.ay-alex-v4-static .breadcrumbs{margin:8px 0 32px;color:rgba(15,23,42,.55);font:600 12px Geist,sans-serif;letter-spacing:.04em}.ay-alex-v4-static .breadcrumbs a{text-decoration:none}.ay-alex-v4-static .content-section{margin:0;padding:72px 0;border:0;background:transparent;box-shadow:none}.ay-alex-v4-static .section-title-row{display:flex;align-items:center;gap:12px;margin-bottom:32px}.ay-alex-v4-static .section-title-row h2{margin:0;font:800 clamp(30px,3.2vw,46px)/1.04 Manrope,sans-serif;letter-spacing:-.04em}.ay-alex-v4-static .info-hint{display:none}
.ay-site-footer{padding:72px 0 0;background:#fff;color:var(--stitch-ink);border-top:1px solid var(--stitch-line)}/* Keep the footer's compact homepage footprint: lead column + four visible menus. */
.ay-wrap{width:min(100% - 120px,1160px);margin:auto}.ay-footer-grid{display:grid;grid-template-columns:450px repeat(4,minmax(0,1fr));gap:24px}.ay-footer-grid>nav:last-child{grid-column:auto}.ay-footer-grid>section{grid-row:auto}.ay-site-footer .ay-eyebrow,.ay-site-footer h3,.ay-footer-socials__label{margin:0 0 16px;color:rgba(15,23,42,.58);font:700 11px Geist,sans-serif;letter-spacing:.12em;text-transform:uppercase}.ay-site-footer h2{max-width:440px;margin:0 0 18px;font:800 28px/1.16 Manrope,sans-serif;letter-spacing:-.045em}.ay-site-footer p{color:rgba(15,23,42,.66);font-size:14px;line-height:1.65}.ay-site-footer .ay-actions{display:grid;max-width:310px;gap:10px;margin:26px 0}.ay-site-footer .ay-actions a{display:flex;align-items:center;justify-content:center;min-height:42px;padding:11px 15px;border:1px solid var(--stitch-line);border-radius:999px;font:700 11px Geist,sans-serif;letter-spacing:.09em;text-align:center;text-transform:uppercase;text-decoration:none;transition:transform .25s,box-shadow .25s}.ay-site-footer .ay-actions .ay-button{background:var(--stitch-ink);border-color:var(--stitch-ink);color:#fff}.ay-site-footer .ay-actions a:hover{transform:translateY(-1px);box-shadow:0 14px 32px rgba(15,23,42,.14)}.ay-footer-menu{list-style:none;margin:0;padding:0}.ay-footer-menu li{margin:0 0 10px}.ay-footer-menu a,.ay-footer-link-button{position:relative;border:0;padding:0;background:none;color:rgba(15,23,42,.67);font:500 13px/1.45 Manrope,sans-serif;text-align:left;text-decoration:none;cursor:pointer}.ay-footer-menu a:after,.ay-footer-link-button:after{content:"";position:absolute;left:0;right:0;bottom:-2px;height:1px;background:var(--stitch-ink);transform:scaleX(0);transform-origin:left;transition:transform .25s}.ay-footer-menu a:hover:after,.ay-footer-link-button:hover:after{transform:scaleX(1)}.ay-footer-socials{margin-top:28px}.ay-footer-socials__links{display:flex;gap:8px}.ay-social-link{display:grid;place-items:center;width:36px;height:36px;border:1px solid var(--stitch-line);border-radius:999px;background:#F4F1E9;text-decoration:none}.ay-social-link svg{width:16px;height:16px;fill:currentColor}.ay-footer-bottom{margin-top:54px;padding:20px 36px;border-top:1px solid var(--stitch-line);color:rgba(15,23,42,.55);font-size:12px;text-align:center}
body.ay-alex-v4-static .cookie-banner{z-index:10000}
/* Current live WordPress footer authority: portable and deterministic. */
body.ay-alex-v4-static .ay-site-footer{padding:clamp(46px,6vw,72px) 0 42px;border-top:0;box-shadow:inset 0 1px 0 var(--stitch-line);font-size:14px;line-height:1.5}
body.ay-alex-v4-static .ay-footer-grid{grid-template-columns:minmax(450px,1.15fr) repeat(4,minmax(110px,.7fr));gap:clamp(18px,1.8vw,28px)}
body.ay-alex-v4-static .ay-footer-grid>section,body.ay-alex-v4-static .ay-footer-grid>nav{min-width:0}
body.ay-alex-v4-static .ay-site-footer h2{max-width:none}
body.ay-alex-v4-static .ay-site-footer section>p:not(.ay-eyebrow){max-width:330px;font-size:14px;line-height:1.45}
body.ay-alex-v4-static .ay-site-footer .ay-actions .ay-button-base2026{border:1px solid var(--stitch-line);background:transparent;color:var(--stitch-ink);box-shadow:none}
body.ay-alex-v4-static .ay-footer-socials{display:grid;gap:10px;margin-top:18px}
body.ay-alex-v4-static .ay-site-footer .ay-footer-socials__label{margin:0;font-family:Geist,Manrope,sans-serif;font-size:12px;font-weight:800;line-height:1;letter-spacing:.08em;text-transform:uppercase}
body.ay-alex-v4-static .ay-footer-socials__links{gap:10px}
body.ay-alex-v4-static .ay-social-link{width:38px;height:38px}
body.ay-alex-v4-static .ay-footer-menu{display:grid;gap:7px;margin:0;padding:0;list-style:none}
body.ay-alex-v4-static .ay-footer-menu li{margin:0}
body.ay-alex-v4-static .ay-footer-menu a,body.ay-alex-v4-static .ay-footer-link-button{display:block;padding:4px 0;font-size:13px;line-height:1.45}
body.ay-alex-v4-static .ay-footer-bottom{width:min(100% - 40px,960px);margin:34px auto 0;padding:18px 0 0;border-top:1px solid var(--stitch-line);color:rgba(15,23,42,.68);font-size:14px;line-height:1.5;text-align:left}
@media(max-width:1024px){.ay-v2-nav,.ay-v2-header-cta{display:none}.ay-v2-menu-toggle{display:block}.ay-v2-header-shell{width:min(100% - 32px,680px)}.ay-v2-condensed .ay-v2-brand{opacity:1;max-width:220px}.ay-footer-grid{grid-template-columns:1.2fr 1fr 1fr}.ay-footer-grid>section{grid-column:1/-1;grid-row:auto}.ay-footer-grid>nav:last-child{grid-column:auto}.ay-alex-v4-static main.app-shell{width:min(100% - 48px,860px)}}
@media(max-width:720px){body.ay-alex-v4-static{padding-top:78px}.ay-v2-header-shell{height:58px}.ay-v2-brand{font-size:18px}.ay-alex-v4-static main.app-shell{width:min(100% - 32px,520px);padding-top:20px}.ay-alex-v4-static .breadcrumbs{margin-bottom:20px}.ay-alex-v4-static .content-section{padding:52px 0}.ay-wrap{width:min(100% - 40px,520px)}.ay-footer-grid{grid-template-columns:1fr;gap:34px}.ay-footer-grid>nav:last-child{grid-column:auto}.ay-site-footer{padding-top:52px}.ay-site-footer h2{font-size:22px;line-height:1.16}.ay-footer-bottom{margin-top:40px;padding:18px 16px}.ay-site-footer .ay-actions{max-width:none}.ay-v2-menu-open{overflow:hidden}}
/* Canonical Home v4 shell state: quiet on canvas, pill only after scroll. */
.ay-v2-header{padding-top:16px;transition:padding .42s cubic-bezier(.22,1,.36,1)}
.ay-v2-header-shell{background:transparent;border-color:transparent;box-shadow:none;backdrop-filter:none;-webkit-backdrop-filter:none}
body.ay-alex-v4-static.ay-v2-condensed .ay-v2-header{padding-top:10px}
body.ay-alex-v4-static.ay-v2-condensed .ay-v2-header-shell{width:min(max-content,calc(100% - 40px));height:50px;padding:0 18px;border:1px solid rgba(15,23,42,.08);border-radius:999px;background:rgba(255,255,255,.76);backdrop-filter:blur(20px) saturate(170%);-webkit-backdrop-filter:blur(20px) saturate(170%);box-shadow:0 18px 50px rgba(15,23,42,.13),0 2px 8px rgba(15,23,42,.04)}
body.ay-alex-v4-static.ay-v2-condensed .ay-v2-brand,body.ay-alex-v4-static.ay-v2-condensed .ay-v2-header-cta{opacity:0;max-width:0;padding-left:0;padding-right:0;overflow:hidden;pointer-events:none;margin:0}

@media(max-width:1100px) and (min-width:821px){body.ay-alex-v4-static .ay-footer-grid{grid-template-columns:minmax(220px,1.15fr) repeat(4,minmax(105px,.62fr));gap:24px 16px}.ay-site-footer h2{font-size:26px}.ay-site-footer p,.ay-footer-menu a,.ay-footer-link-button{font-size:11px}}
@media(max-width:820px){body.ay-alex-v4-static .ay-footer-grid{grid-template-columns:1fr 1fr;gap:30px 22px}body.ay-alex-v4-static .ay-footer-grid>section{grid-column:1/-1}body.ay-alex-v4-static .ay-site-footer .ay-actions{grid-template-columns:1fr;max-width:310px}body.ay-alex-v4-static .ay-site-footer .ay-actions a{font-size:10px}body.ay-alex-v4-static .ay-footer-bottom{margin-top:28px}}
@media(max-width:560px){body.ay-alex-v4-static .ay-footer-grid{grid-template-columns:1fr;gap:28px}body.ay-alex-v4-static .ay-footer-grid>section{grid-column:auto}}
@media(max-width:720px){body.ay-alex-v4-static .ay-site-footer{padding:44px 0 42px}body.ay-alex-v4-static .ay-footer-grid{gap:30px}body.ay-alex-v4-static .ay-footer-bottom{width:min(100% - 40px,960px);margin-top:34px;padding:18px 0 0}}
/* Exact captured current-live footer authority. Keep after portable fallbacks. */
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer{background:#fff!important;color:var(--stitch-ink)!important;padding:clamp(46px,6vw,72px) 20px 42px;border-top:0;box-shadow:inset 0 1px 0 var(--stitch-line);font-family:Manrope,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;line-height:1.5}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{width:min(100%,1160px);margin:auto;grid-template-columns:minmax(450px,1.15fr) repeat(4,minmax(110px,.7fr));gap:clamp(18px,1.8vw,28px)}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer h2{max-width:none;margin:0 0 14px;font-family:Manrope,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:clamp(22px,2.4vw,28px);font-weight:700;line-height:1.16;letter-spacing:normal}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer h3{margin:0 0 14px;font-family:Geist,Manrope,sans-serif!important;font-size:15px;font-weight:700;line-height:1.5;letter-spacing:.11em!important;text-transform:uppercase!important;color:rgba(15,23,42,.72)!important}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer p{max-width:330px;font-size:14px;line-height:1.45;color:rgba(15,23,42,.68)!important}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-eyebrow{margin:0 0 14px;font-family:Geist,Manrope,sans-serif!important;font-weight:650;color:rgba(15,23,42,.72)!important;letter-spacing:.11em!important;text-transform:uppercase!important}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions{display:grid!important;grid-template-columns:1fr!important;max-width:310px;gap:10px!important;align-items:stretch!important;margin:28px 0 0}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions a{width:100%;justify-content:center;white-space:normal;text-align:center;font-family:Geist,Manrope,sans-serif;font-size:11px;font-weight:700;line-height:1;letter-spacing:.09em}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions .ay-button{box-shadow:0 12px 28px rgba(15,23,42,.12)}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-socials{display:grid;gap:10px;margin-top:18px}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-footer-socials__label{margin:0;font-family:Manrope,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:12px;font-weight:800;line-height:1;letter-spacing:.08em;text-transform:uppercase}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-socials__links{display:flex;flex-wrap:wrap;align-items:center;gap:14px}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link,body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link--disabled{display:inline-flex;width:22px;height:22px;align-items:center;justify-content:center;border:0 solid rgba(15,23,42,.1);border-radius:0;background:rgba(244,241,233,.72)!important;color:var(--stitch-ink)!important;line-height:1;padding:0;text-decoration:none}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link svg{width:20px;height:20px;fill:currentColor;flex:0 0 auto}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link--disabled{cursor:default;opacity:.58;pointer-events:none}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-menu{display:grid;gap:7px;margin:0;padding:0;list-style:none}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-menu li{margin:0}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-footer-menu a{display:inline;padding:0;font-family:Manrope,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;font-weight:400;line-height:1.5;color:rgba(15,23,42,.68)!important;text-decoration:none!important}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-link-button{appearance:none;display:inline-flex;min-height:24px;align-items:center;border:0;background:transparent;color:#f4f0e8;cursor:pointer;font:inherit;padding:0;text-align:left}
body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-bottom{width:min(100%,960px);margin:34px auto 0;padding:18px 0 0;border-top:1px solid rgba(255,255,255,.12);color:rgba(15,23,42,.68)!important;font-size:14px;line-height:1.5;text-align:left}
@media(max-width:1100px) and (min-width:901px){body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{grid-template-columns:minmax(450px,1.15fr) repeat(2,minmax(135px,.75fr));gap:28px}}
@media(max-width:900px){body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{grid-template-columns:1fr}}
@media(max-width:720px){body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer{padding-top:44px!important}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{gap:30px!important}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-eyebrow{margin-bottom:6px}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions{flex-direction:column;margin:10px 0 0}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions a{font-size:11px;line-height:1.2;letter-spacing:.09em}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-footer-menu a{display:inline;padding:4px 0;line-height:1.45!important}}
@media(max-width:360px){body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions{width:100%!important;max-width:100%!important}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer .ay-actions a{width:100%!important;max-width:100%!important;box-sizing:border-box!important;white-space:normal!important}}
@media(prefers-reduced-motion:reduce){.ay-alex-v4-static *,.ay-alex-v4-static *::before,.ay-alex-v4-static *::after{transition:none!important;animation:none!important}}
"""
