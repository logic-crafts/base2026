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

STYLE_VERSION = "20260710-ai-recommends-solutions-v1"


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
            <article class="solution-evidence-card" id="evidence-{escape(str(claim.get('claim_id') or 'claim'))}">
              <div class="solution-evidence-card__meta">
                <span class="evidence-role">Creator signal</span>
                <span>{escape(str(creator))}</span>
                <span>{escape(str(claim.get('published_at') or source.get('published_at') or ''))}</span>
              </div>
              <h3>{escape(str(claim.get('topic') or 'Reviewed source signal'))}</h3>
              <p class="solution-evidence-card__claim">{escape(str(claim.get('claim_text') or ''))}</p>
              {f'<blockquote>{escape(str(evidence_excerpt))}</blockquote>' if evidence_excerpt else ''}
              <p><strong>Why it is in this solution:</strong> {escape(str(entry.get('why_relevant') or ''))}</p>
              {f'<p><strong>Bounded action from the reviewed card:</strong> {escape(str(action))}</p>' if action else ''}
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
    return "".join(
        f"""
        <article class="solution-step">
          <span class="solution-step__number">{index:02d}</span>
          <div><h3>{escape(str(row.get('title') or 'Step'))}</h3><p>{escape(str(row.get('body') or ''))}</p></div>
        </article>
        """
        for index, row in enumerate(rows, start=1)
    )


def decision_table_html(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{escape(str(row.get('signal') or ''))}</td><td>{escape(str(row.get('decision') or ''))}</td><td>{escape(str(row.get('measure') or ''))}</td></tr>"
        for row in rows
    )
    return f"""
    <div class="table-scroll solution-decision-table">
      <table>
        <thead><tr><th>Signal</th><th>Decision</th><th>Measure</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    """


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
        <div class="solution-hero__copy">
          <p class="eyebrow">AI Recommends Solution</p>
          <h1>{escape(str(solution.get('title') or ''))}</h1>
          <p class="lead">{escape(str(solution.get('problem') or ''))}</p>
          <div class="solution-hero__actions">
            <a class="ay-button" href="#playbook">Open the playbook</a>
            <a class="ay-button-secondary" href="#evidence">Inspect the evidence</a>
          </div>
        </div>
        <aside class="solution-verdict" aria-label="Base2026 recommendation">
          <span>Base2026 verdict</span>
          <p>{escape(str(solution.get('recommendation') or ''))}</p>
        </aside>
      </section>

      <section class="content-section solution-intent-grid" id="decision">
        <article><span>Audience</span><p>{escape(str(solution.get('audience') or ''))}</p></article>
        <article><span>Primary question</span><p>{escape(str(solution.get('primary_query') or ''))}</p></article>
        <article><span>Scope</span><p>{escape(str(solution.get('decision_scope') or ''))}</p></article>
        <article><span>Why now</span><p>{escape(str(solution.get('why_now') or ''))}</p></article>
      </section>

      <section class="content-section" id="playbook">
        {public_pages.section_title('Recommended playbook', 'A bounded sequence to apply before scaling the tactic.')}
        <div class="solution-steps">{playbook_html(solution.get('playbook') or [])}</div>
      </section>

      <section class="content-section" id="decision-table">
        {public_pages.section_title('Decision table', 'Use the observed signal to choose an action and a measurement rather than changing everything at once.')}
        {decision_table_html(solution.get('decision_table') or [])}
      </section>

      <section class="content-section solution-two-column">
        <div>
          {public_pages.section_title('Implementation checklist', 'The reusable completion gate for this solution.')}
          {list_html(solution.get('checklist') or [], 'solution-checklist')}
        </div>
        <div>
          {public_pages.section_title('Risks and when not to use it', 'Limits that prevent the recommendation from becoming a blanket claim.')}
          {list_html(solution.get('risks') or [], 'solution-risk-list')}
        </div>
      </section>

      <section class="content-section solution-measurement">
        {public_pages.section_title('Measure the outcome', 'Record a baseline before implementation, then use the same definitions at each review.')}
        <div class="solution-measurement__grid">
          <div><h3>KPIs</h3>{list_html(solution.get('kpis') or [])}</div>
          <div><h3>Cadence</h3><p>{escape(str(solution.get('cadence') or ''))}</p></div>
        </div>
      </section>

      <section class="content-section" id="evidence">
        {public_pages.section_title('Source Intelligence evidence', 'Reviewed creator signals prove what the source said. They do not replace authoritative product documentation.')}
        <p class="section-intro">Base2026 keeps creator claims, synthesis and platform facts separate. Open any Source Intelligence record to inspect attribution and reviewed evidence.</p>
        <div class="solution-evidence-grid">{evidence_html(resolved)}</div>
      </section>

      <section class="content-section solution-authority">
        {public_pages.section_title('Authoritative verification', 'Official documentation used to bound current platform behavior and metric definitions.')}
        <ul>{authority_html(solution.get('authoritative_sources') or [])}</ul>
      </section>

      <section class="content-section solution-next-action">
        <p class="eyebrow">Apply and measure</p>
        <h2>Use the recommendation as a test, not a promise.</h2>
        <p>Capture the baseline, apply the smallest useful version, review the stated KPIs, and keep or reverse the change based on evidence.</p>
        <a class="ay-button" href="{escape(str(cta.get('href') or '#playbook'))}">{escape(str(cta.get('label') or 'Apply this solution'))}</a>
      </section>
      {f'<section class="content-section"><h2>Related solutions</h2><div class="topic-tags">{related_html}</div></section>' if related_html else ''}
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


def css_text() -> str:
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
