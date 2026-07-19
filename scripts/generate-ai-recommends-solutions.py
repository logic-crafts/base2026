from __future__ import annotations

import argparse
import importlib.util
import json
import re
from html import escape
from pathlib import Path
from typing import Any

from alex_design_system_v2 import VERSION as DESIGN_SYSTEM_VERSION
from alex_design_system_v2 import apply_component_classes, stylesheet_href
from alex_v4_static_shell import apply_alex_v4_shell, shell_js
from base2026_ai_recommends_core import build_public_context, read_json, validate_payload
from base2026_product_shell import footer_html as b26_product_footer_html
from base2026_product_shell import header_html as b26_product_header_html
from base2026_ui_system import visual_component_attributes as b26_visual_component_attributes

PUBLIC_PAGES_PATH = Path(__file__).with_name("generate-public-pages.py")
SPEC = importlib.util.spec_from_file_location("base2026_public_pages", PUBLIC_PAGES_PATH)
if not SPEC or not SPEC.loader:
    raise RuntimeError(f"Unable to load {PUBLIC_PAGES_PATH}")
public_pages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_pages)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


LEGACY_STYLESHEET_RE = re.compile(
    r"""<link\b[^>]*(?:
        ai-recommends-solutions\.css
        |base2026-interior-v1\.css
        |alex-v4-static-shell\.css
        |vendor/geist-local\.css
        |fonts\.googleapis\.com
        |fonts\.gstatic\.com
    )[^>]*>""",
    re.IGNORECASE | re.VERBOSE,
)
SHARED_STYLESHEET_RE = re.compile(
    r"""<link\b[^>]*alex-design-system-v2\.css[^>]*>""",
    re.IGNORECASE,
)
CANONICAL_HEADER_RE = re.compile(
    r'<header\b(?=[^>]*\bclass=["\'][^"\']*\bay-v2-header\b[^"\']*["\'])[^>]*>.*?</header>',
    re.IGNORECASE | re.DOTALL,
)
CANONICAL_FOOTER_RE = re.compile(
    r'<footer\b(?=[^>]*\bclass=["\'][^"\']*\bay-site-footer\b[^"\']*["\'])[^>]*>.*?</footer>',
    re.IGNORECASE | re.DOTALL,
)
FORBIDDEN_PUBLIC_ASSET_MARKERS = (
    "ai-recommends-solutions.css",
    "base2026-interior-v1.css",
    "alex-v4-static-shell.css",
    "vendor/geist-local.css",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
)


def apply_solution_design_system(page: str) -> str:
    """Apply shared runtime assets while enforcing the Base product shell."""

    rendered = apply_alex_v4_shell(page, relative_root="..", mode="product")
    rendered, header_count = CANONICAL_HEADER_RE.subn(
        lambda _match: b26_product_header_html(), rendered, count=1
    )
    rendered, footer_count = CANONICAL_FOOTER_RE.subn(
        lambda _match: b26_product_footer_html(), rendered, count=1
    )
    if header_count != 1 or footer_count != 1:
        raise ValueError("Solution page is missing a unique Base product shell boundary")
    rendered = SHARED_STYLESHEET_RE.sub("\n", rendered)
    rendered = LEGACY_STYLESHEET_RE.sub("\n", rendered)
    shared_link = (
        f'    <link rel="stylesheet" href="{escape(stylesheet_href(".."))}" '
        'data-alex-design-system="v2" />\n'
    )
    rendered, head_count = re.subn(
        r"</head>",
        lambda match: shared_link + match.group(0),
        rendered,
        count=1,
        flags=re.IGNORECASE,
    )
    if head_count != 1:
        raise ValueError("Solution page is missing a unique head boundary")
    rendered = apply_component_classes(rendered)

    leaked = [marker for marker in FORBIDDEN_PUBLIC_ASSET_MARKERS if marker in rendered]
    if leaked:
        raise ValueError(f"Solution page retains legacy public assets: {', '.join(leaked)}")
    if rendered.count("alex-design-system-v2.css") != 1:
        raise ValueError("Solution page must reference exactly one shared design-system stylesheet")
    if rendered.count("data-b26-product-header") != 1 or rendered.count("data-b26-product-footer") != 1:
        raise ValueError("Solution page must contain exactly one canonical Base product header and footer")
    return rendered


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
  const runtimeScript = document.currentScript;
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
  if (runtimeScript?.src && !document.querySelector('[data-base2026-solution-journey="runtime"]')) {
    const journey = document.createElement("script");
    journey.src = new URL("./base2026-solution-journey.js", runtimeScript.src).href;
    journey.dataset.base2026SolutionJourney = "runtime";
    document.head.append(journey);
  }
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
        f'    <script src="../static/ai-recommends-solutions.js?v={DESIGN_SYSTEM_VERSION}" defer></script>\n'
        f'    <script type="application/ld+json">{schema}</script>\n'
    )
    rendered, head_count = re.subn(
        r"</head>",
        lambda match: extra + match.group(0),
        page,
        count=1,
        flags=re.IGNORECASE,
    )
    if head_count != 1:
        raise ValueError("Solution page is missing a unique head boundary")
    return rendered


def solution_page(solution: dict[str, Any], report: dict[str, Any]) -> str:
    resolved = report.get("resolved_evidence") or []
    related = solution.get("related_solution_slugs") or []
    related_html = "".join(
        f'<a class="topic-chip" href="{escape(str(slug))}.html">{escape(str(slug).replace("-", " ").title())}</a>'
        for slug in related
    )
    cta = solution.get("cta") or {}
    bridge_html = ""
    if report.get("indexable"):
        bridge_html = (
            '<a class="ay-button-secondary" href="/knowledge/apply-research.html" '
            'data-research-bridge="solution_to_apply_research" '
            f'data-origin-id="{escape(str(solution.get("slug") or ""))}">Apply this research</a>'
            '<p class="solution-next-action__boundary">Optional: use this bridge only when the public research needs business-specific diagnosis. '
            'The Base2026 research path remains complete without a service request.</p>'
        )
    body = f"""
      <section class="solution-hero">
        <div class="solution-hero__copy">
          <p class="eyebrow">AI Recommends Solution</p>
          <h1>{escape(str(solution.get('title') or ''))}</h1>
          <article class="solution-problem">
            <span>The problem</span>
            <p>{escape(str(solution.get('problem') or ''))}</p>
          </article>
        </div>
        <aside class="solution-verdict" aria-label="Base2026 recommendation">
          <span>The recommendation</span>
          <p>{escape(str(solution.get('recommendation') or ''))}</p>
          <div class="solution-hero__actions">
            <a class="ay-button" href="#playbook">Open the playbook</a>
            <a class="ay-button-secondary" href="#evidence">Inspect the evidence</a>
          </div>
        </aside>
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

      <section class="content-section solution-operations solution-operations-grid" aria-label="Completion and measurement">
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

      <section class="content-section solution-next-action" {b26_visual_component_attributes('B26-09', 'solution-research-bridge')}>
        <p class="eyebrow">Continue in Base2026</p>
        <h2>Open the evidence behind this decision.</h2>
        <p>Continue in the main Search workspace, inspect related source records, and refine the decision before implementation.</p>
        <div class="solution-next-action__actions">
          <a class="ay-button" href="{escape(str(cta.get('href') or '/knowledge/'))}">{escape(str(cta.get('label') or 'Explore related evidence'))}</a>
          {bridge_html}
        </div>
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
    return apply_solution_design_system(inject_solution_head(page, solution, resolved))


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
    return apply_solution_design_system(page)



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

    write_text(args.out / "ai-recommends-solutions.js", solution_js_text())
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
