from __future__ import annotations

import argparse
import importlib.util
import json
from html import escape
from pathlib import Path
from typing import Any

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
    return inject_solution_head(page, solution, resolved)


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
    return page.replace(
        "  </head>",
        f'    <link rel="stylesheet" href="../static/ai-recommends-solutions.css?v={STYLE_VERSION}" />\n  </head>',
        1,
    )


def css_text() -> str:
    return """
.solution-page { --solution-orange: #ff6b18; --solution-ink: #101820; --solution-mist: #eef2f0; }
.solution-hero { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(280px,.7fr); gap:28px; align-items:stretch; margin:18px 0 36px; }
.solution-hero__copy, .solution-verdict { border:1px solid var(--line, #d9ddd9); border-radius:22px; padding:clamp(24px,4vw,52px); background:var(--surface, #fff); }
.solution-hero__copy h1 { max-width:900px; margin:.35rem 0 1rem; font-size:clamp(2.35rem,5vw,5.4rem); line-height:.96; letter-spacing:-.055em; }
.solution-hero__actions, .solution-card-actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:24px; }
.solution-verdict { background:var(--solution-ink); color:#fff; display:flex; flex-direction:column; justify-content:space-between; }
.solution-verdict span, .solution-intent-grid span, .solution-hub-card__meta, .evidence-role { font-family:var(--font-mono, monospace); font-size:.74rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.solution-verdict p { font-size:1.25rem; line-height:1.45; }
.solution-intent-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
.solution-intent-grid article { padding:22px; border:1px solid var(--line, #d9ddd9); border-radius:16px; background:#fff; }
.solution-intent-grid p { margin:.65rem 0 0; }
.solution-steps { display:grid; gap:12px; }
.solution-step { display:grid; grid-template-columns:64px 1fr; gap:18px; padding:22px; border:1px solid var(--line, #d9ddd9); border-radius:16px; background:#fff; }
.solution-step__number { color:var(--solution-orange); font:700 1.25rem var(--font-mono, monospace); }
.solution-step h3, .solution-step p { margin:0; }
.solution-step p { margin-top:.45rem; }
.solution-two-column, .solution-measurement__grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:24px; }
.solution-checklist, .solution-risk-list, .solution-measurement ul { padding-left:1.25rem; }
.solution-checklist li, .solution-risk-list li, .solution-measurement li { margin:.65rem 0; }
.solution-checklist li::marker { color:var(--solution-orange); }
.solution-decision-table table { width:100%; border-collapse:collapse; }
.solution-decision-table th, .solution-decision-table td { padding:14px; text-align:left; vertical-align:top; border-bottom:1px solid var(--line, #d9ddd9); }
.solution-evidence-grid, .solution-hub-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; }
.solution-evidence-card, .solution-hub-card { padding:22px; border:1px solid var(--line, #d9ddd9); border-radius:18px; background:#fff; }
.solution-evidence-card__meta, .solution-hub-card__meta { display:flex; flex-wrap:wrap; gap:10px 18px; color:var(--muted, #59635f); }
.solution-evidence-card blockquote { margin:18px 0; padding:16px 18px; border-left:3px solid var(--solution-orange); background:var(--solution-mist); }
.solution-evidence-card__claim { font-size:1.08rem; font-weight:650; }
.solution-authority li { margin:14px 0; }
.solution-authority li span { display:block; color:var(--muted, #59635f); margin-top:4px; }
.solution-next-action { padding:clamp(24px,4vw,48px); border-radius:20px; background:var(--solution-ink); color:#fff; }
.solution-next-action h2, .solution-next-action p, .solution-next-action .eyebrow { color:#fff; }
.solution-next-action .ay-button { background:var(--solution-orange); border-color:var(--solution-orange); color:#fff; }
.solution-next-action h2 { max-width:800px; }
.solution-next-action p { max-width:760px; }
.solution-hub-card h2 { margin:.8rem 0; }
.solution-hub-card__verdict { padding-top:14px; border-top:1px solid var(--line, #d9ddd9); }
@media (max-width:820px) {
  .solution-hero, .solution-two-column, .solution-measurement__grid, .solution-evidence-grid, .solution-hub-grid, .solution-intent-grid { grid-template-columns:1fr; }
  .solution-hero__copy h1 { font-size:clamp(2.3rem,12vw,4rem); }
  .solution-step { grid-template-columns:44px 1fr; }
}
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
