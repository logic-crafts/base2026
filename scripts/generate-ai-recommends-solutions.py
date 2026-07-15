from __future__ import annotations

import argparse
import importlib.util
import json
from html import escape
from pathlib import Path
from typing import Any

from alex_v4_static_shell import apply_alex_v4_shell, shell_css, shell_js
from base2026_ai_recommends_core import build_public_context, read_json, validate_payload

PUBLIC_PAGES_PATH = Path(__file__).with_name("generate-public-pages.py")
SPEC = importlib.util.spec_from_file_location("base2026_public_pages", PUBLIC_PAGES_PATH)
if not SPEC or not SPEC.loader:
    raise RuntimeError(f"Unable to load {PUBLIC_PAGES_PATH}")
public_pages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_pages)

STYLE_VERSION = "20260715-ai-recommends-solutions-stitch-v1"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


def paragraphs(items: list[str], class_name: str = "") -> str:
    class_attr = f' class="{escape(class_name)}"' if class_name else ""
    return "".join(f"<p{class_attr}>{escape(str(item))}</p>" for item in items if str(item).strip())


def list_html(items: list[str], class_name: str = "solution-list") -> str:
    return f'<ul class="{escape(class_name)}">' + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def source_page_href(source: dict[str, Any]) -> str:
    item_id = source.get("item_id") or source.get("source_id") or "source"
    return f"../sources/{public_pages.slug(str(item_id))}.html"


def evidence_html(resolved: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for row in resolved:
        entry = row["entry"]
        source = row["source"]
        claim = row["claim"]
        creator = claim.get("creator_handle") or source.get("creator_handle") or "Source"
        source_url = source.get("source_url") or claim.get("source_url") or ""
        original_link = (
            f'<a class="button-link button-link--quiet" href="{escape(source_url)}" target="_blank" rel="noopener noreferrer">Original source</a>'
            if source_url
            else ""
        )
        evidence_excerpt = claim.get("evidence_excerpt") or ""
        action = claim.get("suggested_action") or ""
        cards.append(
            f"""
            <article class="solution-evidence-row" id="evidence-{escape(str(claim.get('claim_id') or 'claim'))}">
              <header class="solution-evidence-row__meta">
                <span class="evidence-role">Reviewed creator signal</span>
                <span>{escape(str(creator))}</span>
                <span>{escape(str(claim.get('published_at') or source.get('published_at') or ''))}</span>
              </header>
              <div class="solution-evidence-row__summary">
                <div>
                  <p class="solution-evidence-row__topic">{escape(str(claim.get('topic') or 'Reviewed source signal'))}</p>
                  <h3>{escape(str(claim.get('claim_text') or ''))}</h3>
                </div>
                <p><strong>Why it matters</strong><span>{escape(str(entry.get('why_relevant') or ''))}</span></p>
              </div>
              <details class="solution-evidence-row__details">
                <summary>Inspect exact evidence and action</summary>
                <div class="solution-evidence-row__detail-grid">
                  {f'<div><span>Exact excerpt</span><blockquote>{escape(str(evidence_excerpt))}</blockquote></div>' if evidence_excerpt else ''}
                  {f'<div><span>Bounded action</span><p>{escape(str(action))}</p></div>' if action else ''}
                </div>
              </details>
              <div class="solution-card-actions">
                <a class="button-link" href="{escape(source_page_href(source))}">Open Source Intelligence</a>
                {original_link}
              </div>
            </article>
            """
        )
    return "".join(cards)


def authority_html(rows: list[dict[str, Any]]) -> str:
    return "".join(
        f"""
        <li>
          <a href="{escape(str(row.get('url') or ''))}" target="_blank" rel="noopener noreferrer">{escape(str(row.get('title') or 'Official documentation'))}</a>
          <span>{escape(str(row.get('scope') or ''))}</span>
        </li>
        """
        for row in rows
    )


def playbook_html(rows: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, row in enumerate(rows):
        critical = index == 2
        cards.append(
            f"""
            <article class="solution-step{' solution-step--critical' if critical else ''}">
              <div class="solution-step__title">
                {f'<span>Critical step</span>' if critical else ''}
                <h3>{escape(str(row.get('title') or 'Action'))}</h3>
              </div>
              <p>{escape(str(row.get('body') or ''))}</p>
            </article>
            """
        )
    return "".join(cards)


def decision_table_html(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{escape(str(row.get('signal') or ''))}</td><td>{escape(str(row.get('decision') or ''))}</td><td>{escape(str(row.get('measure') or ''))}</td></tr>"
        for row in rows
    )
    return f"""
    <div class="solution-decision-copy" aria-label="Copy a decision column">
      <span>Copy one column without dragging through adjacent cells:</span>
      <button type="button" data-copy-column="1">Signals</button>
      <button type="button" data-copy-column="2">Decisions</button>
      <button type="button" data-copy-column="3">Measures</button>
      <span class="solution-copy-status" aria-live="polite"></span>
    </div>
    <div class="table-scroll solution-decision-table">
      <table>
        <thead><tr><th>Signal</th><th>Decision</th><th>Measure</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    """


def solution_js_text() -> str:
    return """
(() => {
  const copyText = async (text) => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    document.execCommand("copy");
    field.remove();
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-column]");
    if (!button) return;
    const wrapper = button.closest(".content-section");
    const table = wrapper?.querySelector(".solution-decision-table table");
    if (!table) return;
    const column = Number(button.dataset.copyColumn);
    const heading = table.querySelector(`thead th:nth-child(${column})`)?.textContent.trim() || "Column";
    const values = [...table.querySelectorAll(`tbody td:nth-child(${column})`)]
      .map((cell) => cell.textContent.trim())
      .filter(Boolean);
    const status = wrapper.querySelector(".solution-copy-status");
    try {
      await copyText([heading, ...values].join("\\n"));
      if (status) status.textContent = `${heading} copied.`;
    } catch {
      if (status) status.textContent = `Copy failed. Select the ${heading.toLowerCase()} cells directly.`;
    }
  });
})();
""".strip() + "\n"


def article_schema(solution: dict[str, Any], resolved: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = f"https://aggressorbulkit.online/knowledge/solutions/{solution['slug']}.html"
    citations = [row["source"].get("source_url") or row["claim"].get("source_url") for row in resolved]
    citations.extend(row.get("url") for row in solution.get("authoritative_sources") or [])
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": solution["title"],
        "description": solution["meta_description"],
        "dateModified": solution.get("updated_at"),
        "author": {"@type": "Person", "name": "Alex Yarosh", "url": "https://aggressorbulkit.online/about/"},
        "publisher": {"@type": "Organization", "name": "Logic Crafts LLC"},
        "mainEntityOfPage": canonical,
        "about": solution.get("primary_query"),
        "citation": [url for url in citations if url],
        "isBasedOn": [url for url in citations if url],
    }


def inject_solution_head(page: str, solution: dict[str, Any], resolved: list[dict[str, Any]]) -> str:
    schema = json.dumps(article_schema(solution, resolved), ensure_ascii=False).replace("</", "<\\/")
    extra = (
        f'    <link rel="stylesheet" href="../static/ai-recommends-solutions.css?v={STYLE_VERSION}" />\n'
        f'    <script src="../static/ai-recommends-solutions.js?v={STYLE_VERSION}" defer></script>\n'
        f'    <script type="application/ld+json">{schema}</script>\n'
    )
    return page.replace("  </head>", extra + "  </head>", 1)


def solution_page(solution: dict[str, Any], report: dict[str, Any]) -> str:
    resolved = report.get("resolved_evidence") or []
    related = solution.get("related_solution_slugs") or []
    related_html = "".join(
        f'<a class="topic-chip" href="{escape(str(slug))}.html">{escape(str(slug).replace("-", " ").title())}</a>'
        for slug in related
    )
    cta = solution.get("cta") or {}
    body = f"""
      <section class="solution-hero">
        <p class="eyebrow">AI Recommends Solution</p>
        <h1>{escape(str(solution.get('title') or ''))}</h1>
        <div class="solution-hero__decision">
          <article class="solution-problem">
            <span>The problem</span>
            <p>{escape(str(solution.get('problem') or ''))}</p>
          </article>
          <aside class="solution-verdict" aria-label="Base2026 recommendation">
            <span>The recommendation</span>
            <p>{escape(str(solution.get('recommendation') or ''))}</p>
            <div class="solution-hero__actions">
              <a class="ay-button" href="#playbook">Open the playbook</a>
              <a class="ay-button-secondary" href="#evidence">Inspect the evidence</a>
            </div>
          </aside>
        </div>
      </section>

      <section class="content-section solution-fit" id="decision" aria-labelledby="solution-fit-title">
        <h2 id="solution-fit-title">Use this when the problem is measurable, but the next move is unclear.</h2>
        <div class="solution-fit__cards">
          <article><span>Audience</span><p>{escape(str(solution.get('audience') or ''))}</p></article>
          <article><span>Primary question</span><p>{escape(str(solution.get('primary_query') or ''))}</p></article>
          <article><span>Decision scope</span><p>{escape(str(solution.get('decision_scope') or ''))}</p></article>
          <article><span>Why this matters now</span><p>{escape(str(solution.get('why_now') or ''))}</p></article>
        </div>
      </section>

      <section class="content-section" id="playbook">
        {public_pages.section_title('How to apply this framework', 'A bounded sequence to follow before scaling the tactic.')}
        <div class="solution-steps">{playbook_html(solution.get('playbook') or [])}</div>
      </section>

      <section class="content-section" id="decision-table">
        {public_pages.section_title('Decision table', 'Use the observed signal to choose an action and a measurement rather than changing everything at once.')}
        {decision_table_html(solution.get('decision_table') or [])}
      </section>

      <section class="content-section solution-operations" aria-label="Completion and measurement">
        <article class="solution-completion-card">
          <h2>Completion gate</h2>
          <div class="solution-operations__group">
            <h3>Requirements</h3>
            {list_html(solution.get('checklist') or [], 'solution-checklist')}
          </div>
          <div class="solution-operations__group solution-operations__group--risk">
            <h3>Pause or reconsider when</h3>
            {list_html(solution.get('risks') or [], 'solution-risk-list')}
          </div>
        </article>
        <article class="solution-measurement-card">
          <h2>Measure the outcome</h2>
          <div class="solution-operations__group">
            <h3>KPIs</h3>
            {list_html(solution.get('kpis') or [], 'solution-kpi-list')}
          </div>
          <aside class="solution-cadence">
            <h3>Review cadence</h3>
            <p>{escape(str(solution.get('cadence') or ''))}</p>
          </aside>
        </article>
      </section>

      <section class="content-section solution-evidence" id="evidence">
        {public_pages.section_title('Evidence behind this framework', 'Reviewed creator signals show what each source said; official documentation bounds platform behavior and metrics.')}
        <p class="section-intro">Claims, exact excerpts and bounded actions stay separate. Expand a row to inspect evidence, or open the full Source Intelligence record.</p>
        <div class="solution-evidence-grid">{evidence_html(resolved)}</div>
        <div class="solution-authority">
          <h3>Authoritative verification</h3>
          <p>Official documentation used to bound current platform behavior and metric definitions.</p>
          <ul>{authority_html(solution.get('authoritative_sources') or [])}</ul>
        </div>
      </section>

      <section class="content-section solution-next-action">
        <p class="eyebrow">Continue in Base2026</p>
        <h2>Open the evidence behind this decision.</h2>
        <p>Continue in the main Search workspace, inspect related source records, and refine the decision before implementation.</p>
        <a class="ay-button" href="{escape(str(cta.get('href') or '/knowledge/'))}">{escape(str(cta.get('label') or 'Explore related evidence'))}</a>
      </section>
      {f'<section class="content-section solution-related"><h2>Related solutions</h2><div class="topic-tags">{related_html}</div></section>' if related_html else ''}
    """
    page = public_pages.page_shell(
        f"{solution['title']} | Base2026",
        body,
        relative_root="..",
        robots="index,follow" if report.get("indexable") else "noindex,follow",
        current="solutions",
        description=solution["meta_description"],
        canonical_path=f"solutions/{solution['slug']}.html",
        main_class="app-shell content-page solution-page",
    )
    return apply_alex_v4_shell(inject_solution_head(page, solution, resolved), relative_root="..")


def hub_page(solutions: list[dict[str, Any]], reports_by_slug: dict[str, dict[str, Any]]) -> str:
    cards: list[str] = []
    for solution in solutions:
        report = reports_by_slug[solution["slug"]]
        status = "Release candidate" if report.get("indexable") else "Held for review"
        cards.append(
            f"""
            <article class="solution-hub-card">
              <div class="solution-hub-card__meta"><span>{escape(status)}</span><span>{report.get('resolved_source_count', 0)} sources</span></div>
              <h2><a href="{escape(solution['slug'])}.html">{escape(solution['title'])}</a></h2>
              <p>{escape(solution['problem'])}</p>
              <p class="solution-hub-card__verdict"><strong>Recommendation:</strong> {escape(solution['recommendation'])}</p>
              <a class="button-link" href="{escape(solution['slug'])}.html">Open solution</a>
            </article>
            """
        )
    body = f"""
      <section class="solution-hero solution-hero--hub">
        <div class="solution-hero__copy">
          <p class="eyebrow">Base2026 decision support</p>
          <h1>AI Recommends Solutions</h1>
          <p class="lead">Evidence-backed playbooks built from reviewed public expert signals, official documentation and explicit measurement gates.</p>
        </div>
        <aside class="solution-verdict"><span>How to use this library</span><p>Choose a problem, inspect the evidence, run the smallest useful test, and measure the outcome.</p></aside>
      </section>
      <section class="content-section">
        {public_pages.section_title('Solution library', 'Source Intelligence proves the signals; each Solution page turns them into a bounded operating decision.')}
        <div class="solution-hub-grid">{''.join(cards)}</div>
      </section>
      <section class="content-section solution-next-action">
        <p class="eyebrow">Trust boundary</p>
        <h2>Creator claims are evidence of a viewpoint, not automatic proof of platform behavior.</h2>
        <p>Every release candidate links reviewed Source Intelligence and current authoritative documentation. Pages that fail a hard gate remain noindex.</p>
        <a class="ay-button" href="../methodology.html">Read the methodology</a>
      </section>
    """
    page = public_pages.page_shell(
        "AI Recommends Solutions | Base2026",
        body,
        relative_root="..",
        robots="index,follow" if any(row.get("indexable") for row in reports_by_slug.values()) else "noindex,follow",
        current="solutions",
        description="Base2026 evidence-backed solution playbooks: inspect reviewed public signals, apply a bounded recommendation and measure the outcome.",
        canonical_path="solutions/",
        main_class="app-shell content-page solution-page solution-hub",
    )
    page = page.replace(
        "  </head>",
        f'    <link rel="stylesheet" href="../static/ai-recommends-solutions.css?v={STYLE_VERSION}" />\n  </head>',
        1,
    )
    return apply_alex_v4_shell(page, relative_root="..")


def _legacy_css_text() -> str:
    return """
.solution-page{--solution-ink:#0F172A;--solution-muted:#5f5e58;--solution-line:rgba(15,23,42,.10);--solution-paper:#fff;--solution-soft:#E5E2DA;--solution-cream:#F4F1E9;--solution-accent:#D9730D}
.solution-page .eyebrow{margin:0 0 16px;color:rgba(15,23,42,.52);font:700 11px/1 Geist,Manrope,sans-serif;letter-spacing:.14em;text-transform:uppercase}.solution-page .lead{max-width:760px;margin:24px 0 0;color:rgba(15,23,42,.68);font:400 clamp(16px,1.45vw,20px)/1.6 Manrope,sans-serif}.solution-hero{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.55fr);gap:22px;align-items:stretch;margin:10px 0 0}.solution-hero__copy,.solution-verdict{border:1px solid var(--solution-line);border-radius:32px;background:rgba(255,255,255,.76);box-shadow:0 18px 54px rgba(15,23,42,.045)}.solution-hero__copy{padding:clamp(34px,5vw,70px)}.solution-hero__copy h1{max-width:920px;margin:0;color:var(--solution-ink);font:800 clamp(48px,6.1vw,84px)/.94 Manrope,sans-serif;letter-spacing:-.062em;text-wrap:balance}.solution-hero__actions,.solution-card-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}.solution-page .ay-button,.solution-page .ay-button-secondary,.solution-page .button-link{position:relative;display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:13px 20px;border:1px solid transparent;border-radius:999px;overflow:hidden;font:700 11px/1 Geist,Manrope,sans-serif;letter-spacing:.1em;text-decoration:none;text-transform:uppercase;transition:transform .28s,box-shadow .28s,background .28s,border-color .28s}.solution-page .ay-button,.solution-page .button-link{background:var(--solution-ink);color:#fff}.solution-page .ay-button-secondary,.solution-page .button-link--quiet{border-color:var(--solution-line);background:transparent;color:var(--solution-ink)}.solution-page .ay-button:hover,.solution-page .button-link:hover{transform:translateY(-1px) scale(1.018);box-shadow:0 18px 40px rgba(15,23,42,.18)}.solution-page .ay-button-secondary:hover,.solution-page .button-link--quiet:hover{transform:translateY(-1px);background:#fff;border-color:rgba(15,23,42,.22);color:var(--solution-ink)}.solution-verdict{display:flex;flex-direction:column;justify-content:space-between;padding:clamp(30px,4vw,48px);background:var(--solution-ink);color:#fff;transform:rotate(.45deg)}.solution-verdict span,.solution-intent-grid span,.solution-hub-card__meta,.evidence-role{font:700 11px/1 Geist,Manrope,sans-serif;letter-spacing:.12em;text-transform:uppercase}.solution-verdict span{color:rgba(255,255,255,.56)}.solution-verdict p{margin:80px 0 0;color:#fff;font:700 clamp(20px,2.1vw,28px)/1.3 Manrope,sans-serif;letter-spacing:-.025em}
.solution-intent-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;padding:0!important;border-top:1px solid var(--solution-line)!important;border-bottom:1px solid var(--solution-line)!important}.solution-intent-grid article{padding:28px;border-right:1px solid var(--solution-line);background:transparent}.solution-intent-grid article:last-child{border-right:0}.solution-intent-grid span{color:rgba(15,23,42,.46)}.solution-intent-grid p{margin:28px 0 0;color:rgba(15,23,42,.75);font-weight:600;line-height:1.55}
.solution-steps{display:grid;gap:0;border-top:1px solid var(--solution-line)}.solution-step{display:grid;grid-template-columns:80px minmax(0,1fr);gap:24px;padding:28px 6px;border-bottom:1px solid var(--solution-line);transition:padding .25s,background .25s}.solution-step:hover{padding-left:18px;padding-right:18px;background:rgba(255,255,255,.48)}.solution-step__number{color:var(--solution-accent);font:700 13px Geist,sans-serif;letter-spacing:.1em}.solution-step h3{margin:0;font:800 20px/1.18 Manrope,sans-serif;letter-spacing:-.025em}.solution-step p{max-width:850px;margin:8px 0 0;color:rgba(15,23,42,.65);line-height:1.65}
.solution-two-column,.solution-measurement__grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.solution-two-column>div,.solution-measurement__grid>div{padding:clamp(24px,3vw,38px);border:1px solid var(--solution-line);border-radius:26px;background:rgba(255,255,255,.58)}.solution-checklist,.solution-risk-list,.solution-measurement ul{margin:24px 0 0;padding:0;list-style:none}.solution-checklist li,.solution-risk-list li,.solution-measurement li{position:relative;margin:0;padding:13px 0 13px 24px;border-bottom:1px solid rgba(15,23,42,.07);color:rgba(15,23,42,.7);line-height:1.55}.solution-checklist li:before,.solution-measurement li:before{content:"✓";position:absolute;left:0;color:#137a48;font-weight:800}.solution-risk-list li:before{content:"—";position:absolute;left:0;color:#a46200;font-weight:800}
.solution-decision-table{overflow:hidden;border:1px solid var(--solution-line);border-radius:26px;background:rgba(255,255,255,.64)}.solution-decision-table table{width:100%;border-collapse:collapse}.solution-decision-table th,.solution-decision-table td{padding:18px 20px;text-align:left;vertical-align:top;border-bottom:1px solid var(--solution-line)}.solution-decision-table th{background:rgba(229,226,218,.62);font:700 11px Geist,sans-serif;letter-spacing:.1em;text-transform:uppercase}.solution-decision-table td{color:rgba(15,23,42,.7);font-size:14px;line-height:1.55}.solution-decision-table tr:last-child td{border-bottom:0}
.solution-evidence-grid,.solution-hub-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.solution-evidence-card,.solution-hub-card{position:relative;padding:30px;border:1px solid var(--solution-line);border-radius:26px;background:rgba(255,255,255,.56);overflow:hidden;transition:transform .28s,box-shadow .28s,background .28s}.solution-evidence-card:hover,.solution-hub-card:hover{transform:translateY(-4px);background:#fff;box-shadow:0 24px 64px rgba(15,23,42,.08)}.solution-evidence-card__meta,.solution-hub-card__meta{display:flex;flex-wrap:wrap;gap:10px 18px;color:rgba(15,23,42,.46)}.solution-hub-card h2{margin:50px 0 14px;font:800 clamp(23px,2.3vw,32px)/1.05 Manrope,sans-serif;letter-spacing:-.04em}.solution-hub-card h2 a{text-decoration:none}.solution-hub-card>p{color:rgba(15,23,42,.66);line-height:1.62}.solution-hub-card__verdict{margin-top:22px;padding-top:18px;border-top:1px solid var(--solution-line)}.solution-hub-card .button-link{margin-top:12px}.solution-evidence-card h3{margin:26px 0 12px;font:800 23px/1.1 Manrope,sans-serif;letter-spacing:-.03em}.solution-evidence-card blockquote{margin:20px 0;padding:18px 20px;border:0;border-left:3px solid var(--solution-accent);border-radius:0 14px 14px 0;background:var(--solution-soft);color:rgba(15,23,42,.72);line-height:1.6}.solution-evidence-card__claim{font-size:17px;font-weight:650;line-height:1.55}.section-intro{max-width:780px;color:rgba(15,23,42,.64);line-height:1.65}
.solution-authority ul{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:26px 0 0;padding:0;list-style:none}.solution-authority li{padding:20px;border:1px solid var(--solution-line);border-radius:18px;background:rgba(255,255,255,.48)}.solution-authority li a{font-weight:750}.solution-authority li span{display:block;margin-top:8px;color:rgba(15,23,42,.58);font-size:13px;line-height:1.5}
.solution-next-action{padding:clamp(48px,7vw,86px)!important;border-radius:34px;background:var(--solution-ink)!important;color:#fff;text-align:center;overflow:hidden}.solution-next-action .eyebrow{color:rgba(255,255,255,.56)}.solution-next-action h2{max-width:900px;margin:0 auto;color:#fff;font:800 clamp(34px,5vw,64px)/1 Manrope,sans-serif;letter-spacing:-.055em;text-wrap:balance}.solution-next-action p{max-width:720px;margin:22px auto 0;color:rgba(255,255,255,.68);font-size:17px;line-height:1.62}.solution-next-action .ay-button{margin-top:28px;background:#fff;color:var(--solution-ink)}.solution-page .topic-tags{display:flex;flex-wrap:wrap;gap:10px}.solution-page .topic-chip{padding:10px 14px;border:1px solid var(--solution-line);border-radius:999px;background:rgba(255,255,255,.52);font:700 11px Geist,sans-serif;letter-spacing:.08em;text-decoration:none;text-transform:uppercase}
@media(max-width:1024px){.solution-intent-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.solution-intent-grid article:nth-child(2){border-right:0}.solution-intent-grid article:nth-child(-n+2){border-bottom:1px solid var(--solution-line)}}
@media(max-width:820px){.solution-hero,.solution-two-column,.solution-measurement__grid,.solution-evidence-grid,.solution-hub-grid,.solution-authority ul{grid-template-columns:1fr}.solution-hero__copy h1{font-size:clamp(34px,9vw,44px);overflow-wrap:normal;word-break:normal}.solution-verdict{transform:none}.solution-verdict p{margin-top:40px}.solution-step{grid-template-columns:46px 1fr}.solution-intent-grid{grid-template-columns:1fr}.solution-intent-grid article{border-right:0;border-bottom:1px solid var(--solution-line)}.solution-intent-grid article:last-child{border-bottom:0}.solution-decision-table{overflow-x:auto}.solution-decision-table table{min-width:720px}}
@media(max-width:520px){.solution-hero__copy,.solution-verdict{border-radius:24px;padding:26px}.solution-hero__actions a,.solution-card-actions a{width:100%}.solution-hub-card,.solution-evidence-card{padding:24px}.solution-hub-card h2{margin-top:34px}.solution-next-action{border-radius:24px!important}.solution-step{padding:22px 0}.solution-step:hover{padding-left:0;padding-right:0}}
/* Services-calibrated body contract: the global 1120px header remains wider than
   the 1040px Solutions content, while the opening decision surface is 960px. */
body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 96px,1040px);max-width:1040px;padding-top:24px}
.solution-page .solution-hero{width:min(100%,960px);margin:8px auto 0;grid-template-columns:minmax(0,1.58fr) minmax(270px,.62fr);gap:16px}
.solution-page .solution-hero__copy,.solution-page .solution-verdict{border-radius:24px;box-shadow:0 14px 38px rgba(15,23,42,.035)}
.solution-page .solution-hero__copy{padding:clamp(34px,4.2vw,52px)}
.solution-page .solution-hero__copy h1{max-width:760px;font-size:clamp(42px,4.35vw,56px);line-height:.98;letter-spacing:-.047em}
.solution-page .lead{max-width:700px;margin-top:18px;font-size:clamp(15px,1.25vw,17px);line-height:1.55}
.solution-page .solution-verdict{padding:30px}
.solution-page .solution-verdict p{margin-top:28px;font-size:16px;line-height:1.52}
.solution-page .content-section{padding:52px 0}
.solution-page .section-title-row{margin-bottom:24px}
.solution-page .section-title-row h2{font-size:clamp(28px,3vw,42px);line-height:1.06;letter-spacing:-.035em}
.solution-page .solution-intent-grid article{padding:22px}
.solution-page .solution-intent-grid p{margin-top:18px;font-size:14px}
.solution-page .solution-step{grid-template-columns:64px minmax(0,1fr);gap:20px;padding:24px 4px}
.solution-page .solution-two-column,.solution-page .solution-measurement__grid{gap:16px}
.solution-page .solution-two-column>div,.solution-page .solution-measurement__grid>div{padding:28px;border-radius:20px}
.solution-page .solution-decision-table{border-radius:20px}
.solution-page .solution-evidence-grid,.solution-page .solution-hub-grid{gap:16px}
.solution-page .solution-evidence-card,.solution-page .solution-hub-card{padding:24px;border-radius:20px}
.solution-page .solution-hub-card h2{margin:32px 0 12px;font-size:clamp(22px,2.15vw,29px);line-height:1.08}
.solution-page .solution-hub-card__verdict{margin-top:16px;padding-top:14px}
.solution-page .solution-next-action{padding:clamp(42px,5.3vw,58px)!important;border-radius:24px}
.solution-page .solution-next-action h2{max-width:760px;font-size:clamp(30px,3.7vw,46px);line-height:1.03;letter-spacing:-.04em}
.solution-page .solution-next-action p{max-width:660px;margin-top:18px;font-size:15px}
@media(max-width:1024px){body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 48px,860px)}.solution-page .solution-hero{width:100%}}
@media(max-width:820px){.solution-page .solution-hero{grid-template-columns:1fr;gap:12px}.solution-page .solution-hero__copy{padding:30px 26px}.solution-page .solution-hero__copy h1{font-size:clamp(34px,8.8vw,42px);line-height:1}.solution-page .solution-verdict{padding:22px 26px;border-radius:20px}.solution-page .solution-verdict p{margin-top:14px}.solution-page .content-section{padding:42px 0}.solution-page .section-title-row h2{font-size:clamp(27px,7vw,36px)}.solution-page .solution-hub-card h2{margin-top:26px}}
@media(max-width:720px){body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 32px,520px)}.solution-page .solution-hero__copy{padding:26px 22px}.solution-page .solution-verdict{padding:20px 22px}.solution-page .solution-hero__actions{margin-top:22px}.solution-page .solution-next-action{padding:34px 22px!important}.solution-page .solution-next-action h2{font-size:clamp(28px,8.2vw,36px)}.solution-page .solution-decision-table{overflow:visible;border:0;background:transparent}.solution-page .solution-decision-table table,.solution-page .solution-decision-table tbody,.solution-page .solution-decision-table tr,.solution-page .solution-decision-table td{display:block;width:100%;min-width:0}.solution-page .solution-decision-table table{min-width:0}.solution-page .solution-decision-table thead{display:none}.solution-page .solution-decision-table tbody{display:grid;gap:12px}.solution-page .solution-decision-table tr{overflow:hidden;border:1px solid var(--solution-line);border-radius:16px;background:rgba(255,255,255,.7)}.solution-page .solution-decision-table td{padding:14px 16px;border:0;border-bottom:1px solid var(--solution-line)}.solution-page .solution-decision-table td:last-child{border-bottom:0}.solution-page .solution-decision-table td::before{display:block;margin-bottom:6px;color:var(--solution-muted);font:700 10px/1 var(--solution-mono);letter-spacing:.12em;text-transform:uppercase}.solution-page .solution-decision-table td:nth-child(1)::before{content:"Signal"}.solution-page .solution-decision-table td:nth-child(2)::before{content:"Decision"}.solution-page .solution-decision-table td:nth-child(3)::before{content:"Measure"}}
""".strip() + "\n"


def css_text() -> str:
    legacy = _legacy_css_text().replace(
        ".solution-step__number{color:var(--solution-accent);font:700 13px Geist,sans-serif;letter-spacing:.1em}",
        "",
    )
    closure = """
/* Content Intelligence closure: Services-calibrated components, compact evidence,
   no decorative sequence numbers, and explicit decision-column copy controls. */
.solution-page .solution-fit{display:grid;grid-template-columns:minmax(0,.72fr) minmax(0,1.28fr);gap:64px;align-items:start;border-top:1px solid var(--solution-line);border-bottom:1px solid var(--solution-line)}
.solution-page .solution-fit__copy h2{max-width:420px;margin:0;color:var(--solution-ink);font:800 clamp(30px,3.4vw,44px)/1.04 Manrope,sans-serif;letter-spacing:-.04em}
.solution-page .solution-fit__copy>p:last-child{max-width:42ch;margin:20px 0 0;color:rgba(15,23,42,.66);font-size:16px;line-height:1.62}
.solution-page .solution-fit__cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.solution-page .solution-fit__cards article{min-height:0;padding:24px;border:1px solid var(--solution-line);border-radius:24px;background:var(--solution-cream)}
.solution-page .solution-fit__cards article:last-child{grid-column:1/-1}
.solution-page .solution-fit__cards span{color:rgba(15,23,42,.48);font:750 11px/1 Geist,sans-serif;letter-spacing:.1em;text-transform:uppercase}
.solution-page .solution-fit__cards p{margin:16px 0 0;color:rgba(15,23,42,.74);font-size:14.5px;font-weight:650;line-height:1.55}
.solution-page .solution-steps{border-top:1px solid var(--solution-line)}
.solution-page .solution-step{display:grid;grid-template-columns:minmax(180px,.48fr) minmax(0,1.52fr);gap:36px;padding:24px 4px;border-bottom:1px solid var(--solution-line);background:transparent;transition:none}
.solution-page .solution-step:hover{padding-left:4px;padding-right:4px;background:transparent}
.solution-page .solution-step h3{margin:0;font:800 18px/1.2 Manrope,sans-serif;letter-spacing:-.02em}
.solution-page .solution-step p{max-width:720px;margin:0;color:rgba(15,23,42,.65);line-height:1.65}
.solution-page .solution-decision-copy{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 12px;color:rgba(15,23,42,.58);font-size:13px}
.solution-page .solution-decision-copy button{min-height:36px;padding:9px 12px;border:1px solid var(--solution-line);border-radius:999px;background:#fff;color:var(--solution-ink);font:750 11px/1 Geist,sans-serif;letter-spacing:.04em;cursor:pointer}
.solution-page .solution-decision-copy button:hover,.solution-page .solution-decision-copy button:focus-visible{border-color:rgba(15,23,42,.3);background:var(--solution-cream)}
.solution-page .solution-copy-status{min-width:120px;color:#2e6848;font-weight:700}
.solution-page .solution-decision-table th,.solution-page .solution-decision-table td{user-select:text;-webkit-user-select:text}
.solution-page .solution-completion__grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,.55fr);gap:24px;align-items:start}
.solution-page .solution-completion__grid h3,.solution-page .solution-measurement__grid h3{margin:0;font:800 19px/1.2 Manrope,sans-serif;letter-spacing:-.02em}
.solution-page .solution-checklist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:28px;margin:18px 0 0;padding:0;list-style:none}
.solution-page .solution-risk-list,.solution-page .solution-kpi-list{margin:18px 0 0;padding:0;list-style:none}
.solution-page .solution-completion__grid aside{padding:24px;border:1px solid var(--solution-line);border-radius:20px;background:var(--solution-cream)}
.solution-page .solution-checklist li,.solution-page .solution-risk-list li,.solution-page .solution-kpi-list li{position:relative;margin:0;padding:12px 0 12px 22px;border-bottom:1px solid rgba(15,23,42,.07);color:rgba(15,23,42,.68);line-height:1.52}
.solution-page .solution-checklist li:before,.solution-page .solution-kpi-list li:before{content:"✓";position:absolute;left:0;color:#2e6848;font-weight:800}
.solution-page .solution-risk-list li:before{content:"—";position:absolute;left:0;color:#8a5a16;font-weight:800}
.solution-page .solution-measurement__grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,.55fr);gap:24px;padding:24px 0;border-top:1px solid var(--solution-line);border-bottom:1px solid var(--solution-line)}
.solution-page .solution-measurement__grid>div,.solution-page .solution-measurement__grid>aside{padding:0;border:0;border-radius:0;background:transparent}
.solution-page .solution-measurement__grid aside{padding-left:24px;border-left:1px solid var(--solution-line)}
.solution-page .solution-measurement__grid aside p{margin:18px 0 0;color:rgba(15,23,42,.68);line-height:1.6}
.solution-page .solution-evidence-grid{display:grid;grid-template-columns:1fr;gap:12px}
.solution-page .solution-evidence-row{padding:24px;border:1px solid var(--solution-line);border-radius:20px;background:rgba(255,255,255,.62)}
.solution-page .solution-evidence-row__meta{display:flex;flex-wrap:wrap;gap:8px 16px;color:rgba(15,23,42,.46);font-size:12px}
.solution-page .solution-evidence-row__summary{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(250px,.75fr);gap:32px;margin-top:18px;align-items:start}
.solution-page .solution-evidence-row__topic{margin:0 0 8px;color:rgba(15,23,42,.48);font:750 11px/1 Geist,sans-serif;letter-spacing:.09em;text-transform:uppercase}
.solution-page .solution-evidence-row h3{margin:0;color:var(--solution-ink);font:800 clamp(19px,2vw,25px)/1.16 Manrope,sans-serif;letter-spacing:-.025em}
.solution-page .solution-evidence-row__summary>p{margin:0;color:rgba(15,23,42,.68);line-height:1.58}
.solution-page .solution-evidence-row__summary>p strong,.solution-page .solution-evidence-row__summary>p span{display:block}
.solution-page .solution-evidence-row__summary>p span{margin-top:8px}
.solution-page .solution-evidence-row__details{margin-top:18px;border-top:1px solid var(--solution-line)}
.solution-page .solution-evidence-row__details summary{padding:14px 0 0;color:rgba(15,23,42,.65);font-weight:750;cursor:pointer}
.solution-page .solution-evidence-row__detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:16px;padding:18px;border-radius:14px;background:var(--solution-cream)}
.solution-page .solution-evidence-row__detail-grid span{display:block;margin-bottom:8px;color:rgba(15,23,42,.48);font:750 10px/1 Geist,sans-serif;letter-spacing:.09em;text-transform:uppercase}
.solution-page .solution-evidence-row__detail-grid blockquote,.solution-page .solution-evidence-row__detail-grid p{margin:0;padding:0;border:0;color:rgba(15,23,42,.72);font-style:normal;line-height:1.58}
.solution-page .solution-evidence-row .solution-card-actions{margin-top:18px}
.solution-page .solution-next-action{padding:44px!important}
.solution-page .solution-next-action h2{font-size:clamp(30px,3.5vw,44px)}
@media(max-width:820px){
  .solution-page .solution-fit,.solution-page .solution-completion__grid,.solution-page .solution-measurement__grid{grid-template-columns:1fr;gap:28px}
  .solution-page .solution-measurement__grid aside{padding:20px 0 0;border-left:0;border-top:1px solid var(--solution-line)}
  .solution-page .solution-evidence-row__summary{grid-template-columns:1fr;gap:18px}
}
@media(max-width:720px){
  .solution-page .solution-fit__cards,.solution-page .solution-checklist,.solution-page .solution-evidence-row__detail-grid{grid-template-columns:1fr}
  .solution-page .solution-fit__cards article:last-child{grid-column:auto}
  .solution-page .solution-step{grid-template-columns:1fr;gap:8px;padding:20px 0}
  .solution-page .solution-decision-copy>span:first-child{width:100%}
  .solution-page .solution-evidence-row{padding:20px}
}
""".strip()
    stitch_template = r"""
/* Stitch V1 accepted detail-page composition. The global Alex shell remains authoritative. */
body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 96px,1040px);max-width:1040px;padding:32px 0 96px}
.solution-page{--solution-ink:#0F172A;--solution-muted:#5F5E58;--solution-line:rgba(15,23,42,.10);--solution-paper:#FFFFFF;--solution-soft:#E5E2DA;--solution-cream:#F4F1E9;--solution-accent:#D9730D}
.solution-page .eyebrow{margin:0 0 16px;color:var(--solution-accent);font:750 11px/1 Geist,Manrope,sans-serif;letter-spacing:.12em;text-transform:uppercase}
.solution-page .content-section{padding:52px 0}
.solution-page .section-title-row{margin-bottom:24px}
.solution-page .section-title-row h2,.solution-page>section>h2,.solution-related h2{margin:0;color:var(--solution-ink);font:800 clamp(28px,3vw,42px)/1.06 Manrope,sans-serif;letter-spacing:-.04em;text-wrap:balance}
.solution-page .section-intro{max-width:720px;margin:-8px 0 28px;color:rgba(15,23,42,.62);font-size:15px;line-height:1.65}

/* Hero: typographic title on canvas, then problem + contained recommendation. */
.solution-page .solution-hero{display:block;width:100%;margin:8px 0 0}
.solution-page .solution-hero>h1{max-width:900px;margin:0;color:var(--solution-ink);font:800 clamp(46px,5.7vw,68px)/1.01 Manrope,sans-serif;letter-spacing:-.052em;text-wrap:balance}
.solution-page .solution-hero__decision{display:grid;grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr);gap:32px;align-items:start;margin-top:48px}
.solution-page .solution-problem{padding:8px 8px 8px 0}
.solution-page .solution-problem>span,.solution-page .solution-verdict>span,.solution-page .solution-operations__group>h3,.solution-page .solution-cadence>h3{display:block;margin:0;color:rgba(15,23,42,.52);font:750 11px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase}
.solution-page .solution-problem p{margin:14px 0 0;color:rgba(15,23,42,.66);font-size:16px;line-height:1.68}
.solution-page .solution-verdict{padding:30px;border:1px solid var(--solution-line);border-radius:24px;background:#fff;box-shadow:0 14px 38px rgba(15,23,42,.035);transform:none}
.solution-page .solution-verdict p{margin:14px 0 0;color:rgba(15,23,42,.70);font-size:16px;line-height:1.6}
.solution-page .solution-hero__actions,.solution-page .solution-card-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
.solution-page .ay-button,.solution-page .ay-button-secondary,.solution-page .button-link{display:inline-flex;min-height:42px;align-items:center;justify-content:center;padding:11px 17px;border:1px solid var(--solution-line);border-radius:999px;font:750 11px/1 Geist,Manrope,sans-serif;letter-spacing:.05em;text-decoration:none;transition:transform .22s,background .22s,box-shadow .22s}
.solution-page .ay-button{border-color:var(--solution-ink);background:var(--solution-ink);color:#fff}
.solution-page .ay-button-secondary,.solution-page .button-link{background:#fff;color:var(--solution-ink)}
.solution-page .button-link--quiet{background:transparent}
.solution-page .ay-button:hover,.solution-page .ay-button-secondary:hover,.solution-page .button-link:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(15,23,42,.08)}

/* Four-card fit ledger. */
.solution-page .solution-fit{display:block;border:0}
.solution-page .solution-fit>h2{max-width:740px;margin-bottom:30px}
.solution-page .solution-fit__cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.solution-page .solution-fit__cards article,.solution-page .solution-fit__cards article:last-child{grid-column:auto;min-height:138px;padding:22px;border:1px solid var(--solution-line);border-radius:18px;background:#fff}
.solution-page .solution-fit__cards span{color:rgba(15,23,42,.50);font:750 10px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase}
.solution-page .solution-fit__cards p{margin:16px 0 0;color:rgba(15,23,42,.78);font-size:14px;font-weight:650;line-height:1.5}

/* Editorial playbook; only the decision pivot becomes a contained card. */
.solution-page .solution-steps{display:grid;gap:10px;border:0}
.solution-page .solution-step{display:grid;grid-template-columns:minmax(210px,.46fr) minmax(0,1.54fr);gap:34px;align-items:center;padding:24px 20px;border:0;border-bottom:1px solid var(--solution-line);background:transparent;transition:none}
.solution-page .solution-step:hover{padding:24px 20px;background:transparent}
.solution-page .solution-step__title span{display:block;margin:0 0 9px;color:var(--solution-accent);font:750 10px/1 Geist,Manrope,sans-serif;letter-spacing:.09em;text-transform:uppercase}
.solution-page .solution-step h3{margin:0;font:800 18px/1.2 Manrope,sans-serif;letter-spacing:-.025em}
.solution-page .solution-step p{max-width:720px;margin:0;color:rgba(15,23,42,.64);font-size:14px;line-height:1.65}
.solution-page .solution-step--critical{margin:2px 0;padding:26px 24px;border:1px solid var(--solution-line);border-radius:22px;background:#fff;box-shadow:0 12px 32px rgba(15,23,42,.035)}
.solution-page .solution-step--critical:hover{padding:26px 24px;background:#fff}

/* Decision ledger with optional per-column copy actions. */
.solution-page .solution-decision-copy{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 12px;color:rgba(15,23,42,.56);font-size:12px}
.solution-page .solution-decision-copy button{min-height:34px;padding:8px 11px;border:1px solid var(--solution-line);border-radius:999px;background:#fff;color:var(--solution-ink);font:750 10px/1 Geist,Manrope,sans-serif;letter-spacing:.04em;cursor:pointer}
.solution-page .solution-copy-status{min-width:110px;color:#2E6848;font-weight:700}
.solution-page .solution-decision-table{overflow:hidden;border:1px solid var(--solution-line);border-radius:18px;background:#fff}
.solution-page .solution-decision-table table{width:100%;border-collapse:collapse}
.solution-page .solution-decision-table th,.solution-page .solution-decision-table td{padding:17px 18px;border:0;border-bottom:1px solid var(--solution-line);text-align:left;vertical-align:top;user-select:text;-webkit-user-select:text}
.solution-page .solution-decision-table th+th,.solution-page .solution-decision-table td+td{border-left:1px solid var(--solution-line)}
.solution-page .solution-decision-table th{background:rgba(15,23,42,.035);font:750 11px/1 Geist,Manrope,sans-serif;letter-spacing:.06em;text-transform:uppercase}
.solution-page .solution-decision-table td{color:rgba(15,23,42,.68);font-size:13.5px;line-height:1.55}
.solution-page .solution-decision-table tr:last-child td{border-bottom:0}

/* Completion and measurement: the accepted two-card operational split. */
.solution-page .solution-operations{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;align-items:stretch}
.solution-page .solution-completion-card,.solution-page .solution-measurement-card{display:flex;min-width:0;flex-direction:column;padding:30px;border:1px solid var(--solution-line);border-radius:24px;background:#fff}
.solution-page .solution-completion-card>h2,.solution-page .solution-measurement-card>h2{margin:0 0 26px;font:800 25px/1.12 Manrope,sans-serif;letter-spacing:-.035em}
.solution-page .solution-operations__group{margin-top:0}
.solution-page .solution-operations__group+.solution-operations__group{margin-top:24px}
.solution-page .solution-operations__group--risk>h3{color:var(--solution-accent)}
.solution-page .solution-checklist,.solution-page .solution-risk-list,.solution-page .solution-kpi-list{display:grid;gap:0;margin:14px 0 0;padding:0;list-style:none}
.solution-page .solution-checklist{grid-template-columns:repeat(2,minmax(0,1fr));column-gap:22px}
.solution-page .solution-checklist li,.solution-page .solution-risk-list li,.solution-page .solution-kpi-list li{position:relative;margin:0;padding:10px 0 10px 21px;border-bottom:1px solid rgba(15,23,42,.07);color:rgba(15,23,42,.68);font-size:13px;line-height:1.45}
.solution-page .solution-checklist li:before,.solution-page .solution-kpi-list li:before{content:"✓";position:absolute;left:0;color:#2E6848;font-weight:800}
.solution-page .solution-risk-list li:before{content:"—";position:absolute;left:0;color:#8A5A16;font-weight:800}
.solution-page .solution-cadence{margin-top:auto;padding:18px;border-radius:15px;background:rgba(15,23,42,.045)}
.solution-page .solution-cadence p{margin:10px 0 0;color:rgba(15,23,42,.70);font-size:13px;line-height:1.55}

/* Creator evidence and authority stay compact; exact excerpts remain inspectable. */
.solution-page .solution-evidence-grid{display:grid;grid-template-columns:1fr;gap:10px}
.solution-page .solution-evidence-row{padding:22px 24px;border:1px solid var(--solution-line);border-radius:18px;background:rgba(255,255,255,.76)}
.solution-page .solution-evidence-row__meta{display:flex;flex-wrap:wrap;gap:7px 14px;color:rgba(15,23,42,.46);font-size:11px}
.solution-page .evidence-role{font-weight:750}
.solution-page .solution-evidence-row__summary{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(220px,.6fr);gap:30px;align-items:start;margin-top:16px}
.solution-page .solution-evidence-row__topic{margin:0 0 7px;color:rgba(15,23,42,.50);font:750 10px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase}
.solution-page .solution-evidence-row h3{margin:0;color:var(--solution-ink);font:800 clamp(18px,1.8vw,23px)/1.18 Manrope,sans-serif;letter-spacing:-.025em}
.solution-page .solution-evidence-row__summary>p{margin:0;color:rgba(15,23,42,.66);font-size:13px;line-height:1.55}
.solution-page .solution-evidence-row__summary>p strong,.solution-page .solution-evidence-row__summary>p span{display:block}
.solution-page .solution-evidence-row__summary>p span{margin-top:7px}
.solution-page .solution-evidence-row__details{margin-top:16px;border-top:1px solid var(--solution-line)}
.solution-page .solution-evidence-row__details summary{padding:13px 0 0;color:rgba(15,23,42,.62);font-size:12px;font-weight:750;cursor:pointer}
.solution-page .solution-evidence-row__detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:14px;padding:17px;border-radius:14px;background:var(--solution-cream)}
.solution-page .solution-evidence-row__detail-grid span{display:block;margin-bottom:7px;color:rgba(15,23,42,.48);font:750 9px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase}
.solution-page .solution-evidence-row__detail-grid blockquote,.solution-page .solution-evidence-row__detail-grid p{margin:0;padding:0;border:0;color:rgba(15,23,42,.70);font-size:13px;font-style:normal;line-height:1.55}
.solution-page .solution-evidence-row .solution-card-actions{margin-top:15px}
.solution-page .solution-authority{margin-top:52px}
.solution-page .solution-authority>h3{margin:0;font:800 20px/1.2 Manrope,sans-serif;letter-spacing:-.025em}
.solution-page .solution-authority>p{max-width:680px;margin:10px 0 20px;color:rgba(15,23,42,.60);font-size:13px;line-height:1.55}
.solution-page .solution-authority ul{display:grid;grid-template-columns:1fr;gap:10px;margin:0;padding:0;list-style:none}
.solution-page .solution-authority li{display:grid;grid-template-columns:minmax(210px,.72fr) minmax(0,1.28fr);gap:24px;align-items:center;padding:16px 18px;border:1px solid var(--solution-line);border-radius:14px;background:rgba(255,255,255,.62)}
.solution-page .solution-authority li a{font-size:13px;font-weight:750;text-decoration:none}
.solution-page .solution-authority li span{margin:0;color:rgba(15,23,42,.58);font-size:12px;line-height:1.5}

/* Contained dark next action and quiet related links. */
.solution-page .solution-next-action{padding:48px!important;border-radius:24px;background:var(--solution-ink)!important;color:#fff;text-align:center}
.solution-page .solution-next-action .eyebrow{color:rgba(255,255,255,.56)}
.solution-page .solution-next-action h2{max-width:760px;margin:0 auto;color:#fff;font:800 clamp(31px,3.8vw,46px)/1.03 Manrope,sans-serif;letter-spacing:-.042em;text-wrap:balance}
.solution-page .solution-next-action p{max-width:650px;margin:18px auto 0;color:rgba(255,255,255,.68);font-size:14px;line-height:1.65}
.solution-page .solution-next-action .ay-button{margin-top:26px;border-color:#fff;background:#fff;color:var(--solution-ink)}
.solution-page .solution-related{padding-top:34px}
.solution-page .solution-related h2{font-size:26px}
.solution-page .topic-tags{display:flex;flex-wrap:wrap;gap:9px;margin-top:18px}
.solution-page .topic-chip{padding:10px 13px;border:1px solid var(--solution-line);border-radius:999px;background:#fff;font:750 10px/1 Geist,Manrope,sans-serif;letter-spacing:.06em;text-decoration:none;text-transform:uppercase}

/* Keep the existing Hub family functional; the accepted Stitch template governs detail pages. */
.solution-hub .solution-hero--hub{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(280px,.55fr);gap:18px}
.solution-hub .solution-hero__copy,.solution-hub .solution-verdict{min-width:0;padding:34px;border:1px solid var(--solution-line);border-radius:24px;background:rgba(255,255,255,.76)}
.solution-hub .solution-hero__copy h1{margin:0;font:800 clamp(44px,5.3vw,68px)/.98 Manrope,sans-serif;letter-spacing:-.052em}
.solution-hub .solution-hero__copy .lead{margin:20px 0 0;color:rgba(15,23,42,.66);line-height:1.6}
.solution-hub-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.solution-hub-card{padding:26px;border:1px solid var(--solution-line);border-radius:20px;background:rgba(255,255,255,.7)}
.solution-hub-card__meta{display:flex;flex-wrap:wrap;gap:8px 16px;color:rgba(15,23,42,.46);font-size:12px}
.solution-hub-card h2{margin:30px 0 12px;font:800 clamp(22px,2.1vw,29px)/1.08 Manrope,sans-serif;letter-spacing:-.035em}
.solution-hub-card h2 a{text-decoration:none}
.solution-hub-card>p{color:rgba(15,23,42,.65);font-size:14px;line-height:1.6}
.solution-hub-card__verdict{padding-top:14px;border-top:1px solid var(--solution-line)}

@media(max-width:1024px){
  body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 48px,860px)}
  .solution-page .solution-fit__cards{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:820px){
  .solution-page .solution-hero__decision,.solution-page .solution-operations,.solution-page .solution-evidence-row__summary,.solution-hub .solution-hero--hub{grid-template-columns:minmax(0,1fr)}
  .solution-page .solution-hero__decision{gap:18px;margin-top:34px}
  .solution-page .solution-problem{padding:0}
  .solution-page .solution-step{grid-template-columns:minmax(170px,.55fr) minmax(0,1.45fr);gap:24px}
  .solution-page .solution-authority li{grid-template-columns:1fr;gap:7px}
  .solution-hub-grid{grid-template-columns:1fr}
}
@media(max-width:720px){
  body.ay-alex-v4-static main.app-shell.solution-page{width:min(100% - 32px,520px);padding-top:22px}
  .solution-page .content-section{padding:40px 0}
  .solution-page .solution-hero>h1{font-size:clamp(36px,10.6vw,46px);line-height:1.01;overflow-wrap:normal;word-break:normal}
  .solution-hub .solution-hero__copy h1{font-size:clamp(31px,9.6vw,40px);line-height:1.02;overflow-wrap:normal;word-break:normal}
  .solution-page .solution-verdict,.solution-page .solution-completion-card,.solution-page .solution-measurement-card{padding:24px 22px;border-radius:20px}
  .solution-page .solution-hero__actions a,.solution-page .solution-card-actions a{width:100%}
  .solution-page .solution-fit__cards,.solution-page .solution-checklist,.solution-page .solution-evidence-row__detail-grid{grid-template-columns:1fr}
  .solution-page .solution-fit__cards article{min-height:0}
  .solution-page .solution-step,.solution-page .solution-step:hover{grid-template-columns:1fr;gap:9px;padding:20px 0}
  .solution-page .solution-step--critical,.solution-page .solution-step--critical:hover{padding:23px 20px}
  .solution-page .solution-decision-copy>span:first-child{width:100%}
  .solution-page .solution-decision-table{overflow:visible;border:0;background:transparent}
  .solution-page .solution-decision-table table,.solution-page .solution-decision-table tbody,.solution-page .solution-decision-table tr,.solution-page .solution-decision-table td{display:block;width:100%;min-width:0}
  .solution-page .solution-decision-table thead{display:none}
  .solution-page .solution-decision-table tbody{display:grid;gap:10px}
  .solution-page .solution-decision-table tr{overflow:hidden;border:1px solid var(--solution-line);border-radius:15px;background:#fff}
  .solution-page .solution-decision-table td{padding:13px 15px;border:0;border-bottom:1px solid var(--solution-line)}
  .solution-page .solution-decision-table td:last-child{border-bottom:0}
  .solution-page .solution-decision-table td:before{display:block;margin-bottom:5px;color:rgba(15,23,42,.48);font:750 9px/1 Geist,Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase}
  .solution-page .solution-decision-table td:nth-child(1):before{content:"Signal"}
  .solution-page .solution-decision-table td:nth-child(2):before{content:"Decision"}
  .solution-page .solution-decision-table td:nth-child(3):before{content:"Measure"}
  .solution-page .solution-evidence-row{padding:20px}
  .solution-page .solution-next-action{padding:36px 22px!important;border-radius:20px}
  .solution-page .solution-next-action h2{font-size:clamp(29px,8.5vw,38px)}
}
@media(max-width:380px){
  .solution-page .solution-hero>h1{font-size:clamp(32px,10.2vw,39px)}
  .solution-page .solution-fit__cards article{padding:19px}
}
""".strip()
    return legacy + "\n" + closure + "\n" + stitch_template + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Base2026 AI Recommends Solution pages from reviewed public evidence.")
    parser.add_argument("--input", type=Path, default=Path("data/base2026_ai_recommends_solutions_pilot.json"))
    parser.add_argument("--data-root", type=Path, default=Path("public-data/tiktok"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = read_json(args.input)
    context = build_public_context(args.data_root)
    validation = validate_payload(payload, context)
    internal_reports = validation.pop("_internal_reports")
    reports_by_slug = {row["slug"]: row for row in internal_reports}
    solutions = payload["solutions"]

    write_text(args.out / "ai-recommends-solutions.css", css_text())
    write_text(args.out / "ai-recommends-solutions.js", solution_js_text())
    write_text(args.out / "alex-v4-static-shell.css", shell_css())
    write_text(args.out / "alex-v4-static-shell.js", shell_js())
    for solution in solutions:
        report = reports_by_slug[solution["slug"]]
        write_text(args.out / "solutions" / f"{solution['slug']}.html", solution_page(solution, report))
    write_text(args.out / "solutions" / "index.html", hub_page(solutions, reports_by_slug))

    public_report = {
        **validation,
        "out": str(args.out),
        "generated_pages": len(solutions) + 1,
        "solution_urls": [f"solutions/{row['slug']}.html" for row in solutions],
    }
    rendered = json.dumps(public_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
