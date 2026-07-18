from __future__ import annotations

import re
from html import escape
from pathlib import Path

SHELL_VERSION = "20260718-visual-reset-v2"
ROOT = Path(__file__).resolve().parents[1]
LIVE_FOOTER_TEMPLATE = ROOT / "templates" / "shared" / "alex-home-v4-footer.html"
DESIGN_SYSTEM_CSS = ROOT / "web" / "static" / "alex-design-system-v2.css"
SHELL_SCRIPT = ROOT / "web" / "static" / "alex-v4-static-shell.js"


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
                <section><h3>Decision support</h3><a href="/knowledge/solutions/"><strong>AI Recommends Solutions</strong><span>Turn source evidence into bounded operating decisions.</span></a><a href="/knowledge/ai-visibility-pages/"><strong>AI Visibility Lab</strong><span>Inspect practical visibility questions and source-backed playbooks.</span></a><a href="/knowledge/creators/"><strong>Creators</strong><span>Browse attributed expert source profiles.</span></a><a href="/knowledge/methodology.html"><strong>Methodology</strong><span>Review the evidence, editorial and publication rules.</span></a></section>
              </div>
              <form class="ay-v2-mega-search" method="get" action="/knowledge/" role="search"><label for="ay-v2-mega-search-input">Quick search</label><input id="ay-v2-mega-search-input" name="q" type="search" aria-label="Search Base2026"><button type="submit">Search</button></form>
            </div>
          </div>
          <a href="/about/">About</a>
        </nav>
        <a class="ay-v2-header-cta" href="/ai-visibility-audit/">Check My AI Visibility</a>
        <button class="ay-v2-menu-toggle" type="button" aria-expanded="false" aria-controls="ay-v2-mobile-panel">Menu</button>
      </div>
      <div class="ay-v2-mobile-panel" id="ay-v2-mobile-panel" hidden><a href="/services/">Services</a><a href="/ai-visibility-audit/">AI Visibility</a><a href="/pricing/">Pricing</a><a href="/knowledge/">Search Base2026</a><a href="/knowledge/sources/">Source Intelligence</a><a href="/knowledge/topics/">Topics &amp; viewpoints</a><a href="/knowledge/solutions/">AI Recommends Solutions</a><a href="/knowledge/ai-visibility-pages/">AI Visibility Lab</a><a href="/knowledge/apply-research.html">Apply Research</a><a href="/knowledge/creators/">Creators</a><a href="/about/">About</a></div>
    </header>"""




def footer_html() -> str:
    """Render the frozen current-live Home v4 footer template.

    The template was captured from production WordPress and is SHA-locked by
    the independent candidate validator. Keeping renderer markup in one
    template prevents legacy/current function-selection regressions.
    """
    inner = LIVE_FOOTER_TEMPLATE.read_text(encoding="utf-8").strip()
    return f'<footer class="ay-site-footer" aria-label="Site footer">\n{inner}\n</footer>'


def apply_alex_v4_shell(page: str, relative_root: str = "..", mode: str = "editorial") -> str:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"editorial", "product"}:
        raise ValueError("Alex Design System mode must be 'editorial' or 'product'.")

    legacy_header = r'<header\b(?=[^>]*\bclass=["\'][^"\']*\bsite-header\b[^"\']*["\'])[^>]*>.*?</header>'
    legacy_footer = r'<footer\b(?=[^>]*\bclass=["\'][^"\']*\bsite-footer\b[^"\']*["\'])[^>]*>.*?</footer>'
    canonical_header = r'<header\b(?=[^>]*\bclass=["\'][^"\']*\bay-v2-header\b[^"\']*["\'])'
    canonical_footer = r'<footer\b(?=[^>]*\bclass=["\'][^"\']*\bay-site-footer\b[^"\']*["\'])'

    if not re.search(canonical_header, page, flags=re.I):
        page, header_replacements = re.subn(legacy_header, header_html(), page, count=1, flags=re.I | re.S)
        if header_replacements == 0:
            skip_link = r'(<a\b(?=[^>]*\bclass=["\'][^"\']*\bskip-link\b[^"\']*["\'])[^>]*>.*?</a>)'
            page, skip_replacements = re.subn(
                skip_link,
                lambda match: f"{match.group(1)}\n    {header_html()}",
                page,
                count=1,
                flags=re.I | re.S,
            )
            if skip_replacements == 0:
                page = re.sub(
                    r'(<body\b[^>]*>)',
                    lambda match: f"{match.group(1)}\n    {header_html()}",
                    page,
                    count=1,
                    flags=re.I,
                )

    if not re.search(canonical_footer, page, flags=re.I):
        page, footer_replacements = re.subn(legacy_footer, footer_html(), page, count=1, flags=re.I | re.S)
        if footer_replacements == 0 and not re.search(r"<footer\b", page, flags=re.I):
            page = re.sub(
                r"</body>",
                lambda match: f"    {footer_html()}\n{match.group(0)}",
                page,
                count=1,
                flags=re.I,
            )

    body_classes = f"ayds-root ayds-mode-{normalized_mode} ay-alex-v4-static ay-stitch-home-v3 ay-stitch-home-v4"
    if re.search(r"<body\b[^>]*\bclass=", page, flags=re.I):
        page = re.sub(
            r'(<body\b[^>]*\bclass=["\'])([^"\']*)(["\'])',
            lambda match: (
                f"{match.group(1)}"
                + " ".join(
                    dict.fromkeys(
                        (
                            *(token for token in match.group(2).split() if not token.startswith("ayds-mode-")),
                            *body_classes.split(),
                        )
                    )
                )
                + f"{match.group(3)}"
            ),
            page,
            count=1,
            flags=re.I,
        )
    else:
        page = re.sub(r"<body\b", f'<body class="{body_classes}"', page, count=1, flags=re.I)
    assets = ""
    if "alex-design-system-v2.css" not in page:
        assets += f'    <link rel="stylesheet" href="{escape(relative_root)}/static/alex-design-system-v2.css?v={SHELL_VERSION}" />\n'
    if "alex-v4-static-shell.js" not in page:
        assets += f'    <script src="{escape(relative_root)}/static/alex-v4-static-shell.js?v={SHELL_VERSION}" defer></script>\n'
    if assets:
        page = re.sub(r"</head>", lambda match: f"{assets}{match.group(0)}", page, count=1, flags=re.I)
    return page


def shell_js() -> str:
    """Return the single versioned shell script used by compatibility builders."""
    return SHELL_SCRIPT.read_text(encoding="utf-8")




def search_shell_css() -> str:
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


def shell_css() -> str:
    """Return the general Visual Reset V2 design asset for legacy callers."""
    return DESIGN_SYSTEM_CSS.read_text(encoding="utf-8")
