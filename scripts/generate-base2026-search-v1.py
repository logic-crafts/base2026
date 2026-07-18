#!/usr/bin/env python3
"""Generate a local Alex Home v4 design overlay for the Base2026 search workspace."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from alex_v4_static_shell import footer_html, header_html, search_shell_css, shell_js
from base2026_ui_system import inject_stylesheet_contract, system_attributes


RESEARCH_CONTEXT_HTML = '''      <section class="research-context" aria-labelledby="research-context-title">
        <div class="research-context__head">
          <p class="eyebrow" id="research-context-title">Research protocol</p>
          <p>Context, application and public-use boundary.</p>
        </div>
        <div class="research-context__rail">
          <details class="research-context__item">
            <summary><span><strong>Independent research pilot</strong><small>Attributed creator-video evidence, without replacing the creators.</small></span><span class="research-context__action">Project context</span></summary>
            <div class="research-context__panel"><p>Base2026 is an independent research product by <a href="/about/">Alex Yarosh</a>. It turns public short-form expert videos into searchable, attributed source records for SEO, GEO, AEO and AI-search research. It does not re-host creator videos, replace creators or package creator work as a private client campaign.</p><nav aria-label="Independent research links"><a href="./story.html">Project Story</a><a href="./methodology.html">Methodology</a><a href="./source-policy.html">Source Policy</a><a href="./opt-out.html">Creator correction</a></nav></div>
          </details>
          <details class="research-context__item">
            <summary><span><strong>Business application</strong><small>Apply public patterns, then audit the business-specific layer.</small></span><span class="research-context__action">Application path</span></summary>
            <div class="research-context__panel"><p>Base2026 surfaces public patterns across SEO, GEO, AEO, content, schema, source trust, local SEO and AI-search visibility. Business-specific diagnosis belongs in the Alex Yarosh audit path rather than inside the public library.</p><nav aria-label="Business application links"><a href="./apply-research.html">Apply research</a><a href="/ai-visibility-audit/">Check AI visibility</a><a href="/ai-visibility-diagnostic-audit/">Diagnostic audit</a></nav></div>
          </details>
          <details class="research-context__item">
            <summary><span><strong>How to use the library</strong><small>Search public patterns; keep private client data outside the workspace.</small></span><span class="research-context__action">Usage boundary</span></summary>
            <div class="research-context__panel"><p>Search repeated patterns, then open source records for matched passages, related topics and creator context. Base2026 is not a lead database, private vault or replacement for original creators. Do not enter credentials, private client data, analytics exports or confidential strategy.</p><nav aria-label="Library usage links"><a href="./methodology.html">Search methodology</a><a href="./source-policy.html">Public source boundary</a><a href="./apply-research.html">How to apply findings</a></nav></div>
          </details>
        </div>
      </section>

'''


def transform(source: str) -> str:
    html = source
    html = re.sub(r'<header class="site-header">.*?</header>', header_html(), html, count=1, flags=re.S)
    html = re.sub(r'<footer class="site-footer">.*?</footer>', footer_html(), html, count=1, flags=re.S)
    html = re.sub(
        r'<body(?:\s+class="[^"]*")?>',
        f'<body class="ay-alex-v4-static base2026-search-v1" {system_attributes("search")}>',
        html,
        count=1,
    )
    html = html.replace('data-manifest-count="documents">1,219', '>1,493', 1)
    html = html.replace('data-manifest-count="chunks">1,715', '>2,052', 1)
    html = html.replace('data-manifest-count="creators">4', '>17', 1)
    html = html.replace('./#search?', './?')
    html = re.sub(
        r'      <section class="project-identity.*?(?=      <section class="search-command")',
        RESEARCH_CONTEXT_HTML,
        html,
        count=1,
        flags=re.S,
    )

    missing_style_links = []
    if 'alex-v4-static-shell.css' not in html:
        missing_style_links.append(
            '    <link rel="stylesheet" href="./static/alex-v4-static-shell.css?v=20260710-search-v1" />'
        )
    if 'base2026-search-v1.css' not in html:
        missing_style_links.append(
            '    <link rel="stylesheet" href="./static/base2026-search-v1.css?v=20260710-search-v1" />'
        )
    if missing_style_links:
        html, inserted = re.subn(
            r'(<link rel="stylesheet" href="\./static/styles\.css\?v=[^"]+"\s*/>)',
            lambda match: match.group(1) + '\n' + '\n'.join(missing_style_links),
            html,
            count=1,
        )
        if inserted != 1:
            raise ValueError('Could not locate the versioned Base2026 styles.css link')
    html = inject_stylesheet_contract(html, ".")

    if 'search-command__heading' not in html:
        html = html.replace(
            '<section class="search-command" aria-label="Knowledge search">',
            '<section class="search-command" aria-label="Knowledge search">\n'
            '        <div class="search-command__heading">\n'
            '          <div><p class="eyebrow">Search the evidence base</p><h2>What do you need to find?</h2></div>\n'
            '          <p>Search source passages, then narrow by creator, source type, or year.</p>\n'
            '        </div>',
            1,
        )
    html = html.replace(
        '<div class="panel-title">\n            <h2>Filter results</h2>\n            <span>Facets</span>\n            <button type="button" id="mobile-filter-close" class="mobile-filter-close" aria-label="Close filters">Close</button>\n          </div>\n          <h3>Creator</h3>\n          <div id="author-refinement"></div>\n          <h3>Source</h3>\n          <div id="source-refinement"></div>\n          <h3>Year</h3>\n          <div id="year-refinement"></div>',
        '<div class="panel-title">\n'
        '            <div class="panel-title__label"><h2>Filters</h2><span id="desktop-filter-count">0 selected</span></div>\n'
        '            <div class="panel-title__actions"><button type="button" id="filter-reset" class="filter-reset">Reset</button><button type="button" id="mobile-filter-close" class="mobile-filter-close" aria-label="Close filters">Close</button></div>\n'
        '          </div>\n'
        '          <section class="filter-facet filter-facet--creator"><h3>Creator</h3><div id="author-refinement"></div></section>\n'
        '          <section class="filter-facet"><h3>Source</h3><div id="source-refinement"></div></section>\n'
        '          <section class="filter-facet"><h3>Year</h3><div id="year-refinement"></div></section>',
        1,
    )
    if 'purify.min.js' not in html:
        html, inserted = re.subn(
            r'(?P<indent>[ \t]*)<script src="\./static/meili\.js\?v=[^"]+"></script>',
            lambda match: (
                f'{match.group("indent")}<script src="./static/purify.min.js?v=20260714-search-security"></script>\n'
                f'{match.group(0)}'
            ),
            html,
            count=1,
        )
        if inserted != 1:
            raise ValueError('Could not locate the versioned meili.js script for DOMPurify ordering')
    missing_scripts = []
    if 'alex-v4-static-shell.js' not in html:
        missing_scripts.append(
            '<script src="./static/alex-v4-static-shell.js?v=20260711-search-v3"></script>'
        )
    if 'base2026-search-v3.js' not in html:
        missing_scripts.append(
            '  <script src="./static/base2026-search-v3.js?v=20260711-search-v3"></script>'
        )
    if missing_scripts:
        html = html.replace('</body>', '\n'.join(missing_scripts) + '\n  </body>', 1)
    component_markers = (
        (
            '<section class="search-command" aria-label="Knowledge search">',
            '<section class="search-command" data-b26-component="B26-01" data-b26-variant="search-console" aria-label="Knowledge search">',
        ),
        (
            '<aside id="mobile-filter-panel" class="filter-panel meili-filters">',
            '<aside id="mobile-filter-panel" class="filter-panel meili-filters" data-b26-component="B26-02" data-b26-variant="filter-drawer">',
        ),
        (
            '<section class="results-panel meili-results">',
            '<section class="results-panel meili-results" data-b26-component="B26-03" data-b26-variant="result-list">',
        ),
        (
            '<aside id="source-detail-panel" class="source-detail-panel" aria-live="polite">',
            '<aside id="source-detail-panel" class="source-detail-panel" data-b26-component="B26-04" data-b26-variant="selected-source" aria-live="polite">',
        ),
        (
            '<div class="hero-card workspace-stat-card" aria-label="Dataset summary">',
            '<div class="hero-card workspace-stat-card" data-b26-component="B26-07" data-b26-variant="dataset-metrics" aria-label="Dataset summary">',
        ),
        (
            '<section class="research-context" aria-labelledby="research-context-title">',
            '<section class="research-context" data-b26-component="B26-08" data-b26-variant="public-boundary" aria-labelledby="research-context-title">',
        ),
    )
    for before, after in component_markers:
        if html.count(before) != 1:
            raise ValueError(f'Could not attach Base2026 component marker: {before}')
        html = html.replace(before, after, 1)
    if './#search?' in html:
        raise ValueError('Legacy hash-based Search route remains after transform')
    return html


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, default=Path('web/static'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(source_root, out)
    index = (source_root / 'index.html').read_text(encoding='utf-8')
    (out / 'index.html').write_text(transform(index), encoding='utf-8')
    (out / 'alex-v4-static-shell.css').write_text(search_shell_css(), encoding='utf-8')
    (out / 'alex-v4-static-shell.js').write_text(shell_js(), encoding='utf-8')
    css_source = Path(__file__).with_name('base2026_search_v1.css')
    (out / 'base2026-search-v1.css').write_text(css_source.read_text(encoding='utf-8'), encoding='utf-8')
    ui_source = Path(__file__).with_name('base2026_search_v3.js')
    (out / 'base2026-search-v3.js').write_text(ui_source.read_text(encoding='utf-8'), encoding='utf-8')
    print(f'generated {out / "index.html"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
