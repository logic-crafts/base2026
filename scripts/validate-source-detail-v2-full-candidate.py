#!/usr/bin/env python3
"""Validate a Source Detail V2 full-family candidate against frozen legacy routes.

The verifier is deliberately independent from the renderer's output manifest:
it reparses canonical input and candidate HTML, compares semantic contracts, and
fails closed on missing future-route exclusion, changed admission, broken local
assets, or Source Detail content/link/schema drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
LIVE_FOOTER_TEMPLATE = ROOT / "templates" / "shared" / "alex-home-v4-footer.html"
LIVE_FOOTER_TEMPLATE_SHA256 = "651aaccefbdfc1c77ed6947db988df14f23d100f8bbbbbc45b2c77a1719ae785"
sys.path.insert(0, str(SCRIPTS))
from template_migration.source_detail import adapt_source_detail  # noqa: E402


def text(node: object | None) -> str:
    return node.get_text(" ", strip=True) if isinstance(node, Tag) else ""


def attr(node: object | None, name: str) -> str:
    return str(node.get(name) or "") if isinstance(node, Tag) else ""


def parse_jsonld(soup: BeautifulSoup) -> list[Any]:
    values: list[Any] = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text()
        if not raw.strip():
            raise ValueError("Empty JSON-LD script")
        values.append(json.loads(raw))
    return values


def local_hrefs(soup: BeautifulSoup) -> set[str]:
    hrefs: set[str] = set()
    main = soup.select_one("main")
    for anchor in main.select("a[href]") if isinstance(main, Tag) else []:
        href = attr(anchor, "href")
        if href and not href.startswith(("http://", "https://", "mailto:", "#")):
            hrefs.add(href)
    return hrefs


def canonical_contract(path: Path, route: str, admission: str) -> dict[str, Any]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    view = adapt_source_detail(path, route, admission)  # type: ignore[arg-type]
    return {
        "title": text(soup.title),
        "canonical": attr(soup.select_one('link[rel="canonical"]'), "href"),
        "robots": attr(soup.select_one('meta[name="robots"]'), "content"),
        "lang": attr(soup.html, "lang"),
        "state": admission,
        "handle": view.handle,
        "date": view.date,
        "thesis": view.thesis,
        "original_link": view.original_link,
        "creator_link": view.creator_link,
        "search_link": view.search_link,
        "policy": view.policy,
        "language": view.language,
        "insight_count": view.insight_count,
        "topics": [topic.model_dump() for topic in view.topics],
        "transcript": text(BeautifulSoup(view.source_html, "html.parser")),
        # JSON mode normalizes typed tuples to the lists emitted by HTML parsing.
        "insights": [insight.model_dump(mode="json") for insight in view.insights],
        "questions": [question.model_dump() for question in view.questions],
        "schema": parse_jsonld(soup),
        "local_hrefs": sorted(local_hrefs(soup)),
    }


def candidate_contract(path: Path) -> dict[str, Any]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    main = soup.select_one("main.b26-source-shell")
    if not isinstance(main, Tag):
        raise ValueError("missing V2 <main class=b26-source-shell>")
    hero = main.select_one(".b26-source-intro")
    rail = main.select_one(".b26-source-rail")
    if not isinstance(hero, Tag) or not isinstance(rail, Tag):
        raise ValueError("missing V2 hero or rail")
    action_links = {text(a).lower(): attr(a, "href") for a in hero.select(".b26-source-actions a[href]")}
    original = next((href for label, href in action_links.items() if label.startswith("open original")), "")
    creator = next((href for label, href in action_links.items() if label == "view creator"), "")
    search = next((href for label, href in action_links.items() if label == "open in search"), "")
    labels: dict[str, str] = {}
    for row in rail.select("dl > div"):
        labels[text(row.select_one("dt"))] = text(row.select_one("dd"))
    hero_topics = [
        {"label": text(anchor), "href": attr(anchor, "href")}
        for anchor in rail.select(".b26-rail-topics a")
    ]
    insights: list[dict[str, Any]] = []
    for card in main.select(".b26-insight"):
        insights.append(
            {
                "claim": text(card.select_one("h3")),
                "meta": text(card.select_one(".b26-insight-meta")),
                "actions": [text(item) for item in card.select(".b26-insight-actions li")],
                "topics": [
                    {"label": text(anchor), "href": attr(anchor, "href")}
                    for anchor in card.select(".b26-insight-topics a")
                ],
            }
        )
    questions = [
        {"question": text(question.select_one("summary")), "answer": text(question.select_one("div p"))}
        for question in main.select(".b26-question")
    ]
    return {
        "title": text(soup.title),
        "canonical": attr(soup.select_one('link[rel="canonical"]'), "href"),
        "robots": attr(soup.select_one('meta[name="robots"]'), "content"),
        "lang": attr(soup.html, "lang"),
        "state": attr(main, "data-admission-state"),
        "handle": text(hero.select_one("h1")),
        "date": text(hero.select_one("time")),
        "thesis": text(hero.select_one(".b26-source-thesis")),
        "original_link": original,
        "creator_link": creator,
        "search_link": search,
        "policy": labels.get("Policy", ""),
        "language": labels.get("Language", ""),
        "insight_count": labels.get("Reviewed insights", ""),
        "topics": hero_topics,
        "transcript": text(main.select_one(".b26-reading-copy")),
        "insights": insights,
        "questions": questions,
        "schema": parse_jsonld(soup),
        "local_hrefs": sorted(local_hrefs(soup)),
    }


def validate_assets(candidate: Path, html_path: Path) -> list[str]:
    """Verify local runtime assets while excluding metadata-only links.

    Canonical/preconnect links are not files.  Stylesheets, icons, scripts and
    images are runtime resources and must resolve inside the isolated candidate.
    """
    issues: list[str] = []
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    resource_nodes: list[tuple[Tag, str, str]] = []
    for link in soup.select("link[href]"):
        rel = {str(value).lower() for value in (link.get("rel") or [])}
        if rel & {"stylesheet", "icon", "apple-touch-icon", "mask-icon"}:
            resource_nodes.append((link, "href", "link asset"))
    resource_nodes.extend((script, "src", "script asset") for script in soup.select("script[src]"))
    resource_nodes.extend((image, "src", "image asset") for image in soup.select("img[src]"))
    for node, name, kind in resource_nodes:
        value = attr(node, name).split("?", 1)[0]
        if not value or value.startswith(("http://", "https://", "data:")):
            continue
        target = (html_path.parent / value).resolve()
        if candidate.resolve() not in (target, *target.parents) or not target.is_file():
            issues.append(f"missing local {kind} {value}")
    return issues


def validate_shared_footer_contract(candidate: Path, route: str) -> list[str]:
    """Fail closed if the portable Home v4 footer drifts from live authority.

    The captured WordPress footer is a shared-shell contract, separate from the
    Source Detail semantic contract.  Check its navigation/copy/CTA structure
    and the deterministic desktop/mobile CSS tokens without requiring a live
    network request during candidate validation.
    """
    issues: list[str] = []
    fixture_bytes = LIVE_FOOTER_TEMPLATE.read_bytes()
    fixture_digest = hashlib.sha256(fixture_bytes).hexdigest()
    expected_inner = fixture_bytes.decode("utf-8").strip()
    if fixture_digest != LIVE_FOOTER_TEMPLATE_SHA256:
        return [f"live footer authority fixture hash drift: {fixture_digest}"]

    page = candidate / route
    page_html = page.read_text(encoding="utf-8")
    raw_footer = re.search(
        r'<footer class="ay-site-footer" aria-label="Site footer">\s*(.*?)\s*</footer>',
        page_html,
        flags=re.S,
    )
    if raw_footer is None:
        return ["shared footer missing canonical .ay-site-footer"]
    if raw_footer.group(1).strip() != expected_inner:
        issues.append("shared footer raw DOM drift from SHA-locked live authority fixture")

    soup = BeautifulSoup(page_html, "html.parser")
    footer = soup.select_one("footer.ay-site-footer")
    if not isinstance(footer, Tag):
        return ["shared footer missing canonical .ay-site-footer"]
    expected_soup = BeautifulSoup(
        f'<footer class="ay-site-footer" aria-label="Site footer">{expected_inner}</footer>',
        "html.parser",
    )
    expected_footer = expected_soup.select_one("footer.ay-site-footer")
    if not isinstance(expected_footer, Tag):
        return ["live footer authority fixture is not parseable"]

    def semantic_signature(node: Tag) -> dict[str, Any]:
        node_grid = node.select_one(":scope > .ay-wrap.ay-footer-grid")
        if not isinstance(node_grid, Tag):
            return {"grid": None}
        lead = node_grid.find("section", recursive=False)
        actions = []
        socials = []
        if isinstance(lead, Tag):
            actions = [
                (text(link), attr(link, "href"), " ".join(link.get("class") or []), attr(link, "data-cta"))
                for link in lead.select(".ay-actions a")
            ]
            socials = [
                (attr(item, "aria-label"), attr(item, "href"), " ".join(item.get("class") or []))
                for item in lead.select(".ay-social-link")
            ]
        navs: list[tuple[str, str, str, list[tuple[str, str]]]] = []
        for nav in node_grid.find_all("nav", recursive=False):
            entries: list[tuple[str, str]] = []
            for item in nav.select(".ay-footer-menu > li"):
                control = item.find(["a", "button"], recursive=False)
                if not isinstance(control, Tag):
                    continue
                target = (
                    "cookie-preferences"
                    if control.name == "button" and control.has_attr("data-cookie-preferences")
                    else attr(control, "href")
                )
                entries.append((text(control), target))
            navs.append((attr(nav, "aria-label"), text(nav.select_one("h3")), text(nav.select_one(":scope > p")), entries))
        return {
            "grid": True,
            "lead_class": tuple(lead.get("class") or ()) if isinstance(lead, Tag) else None,
            "eyebrow": text(lead.select_one(".ay-eyebrow")) if isinstance(lead, Tag) else "",
            "heading": text(lead.select_one("h2")) if isinstance(lead, Tag) else "",
            "body": text(next((child for child in lead.find_all("p", recursive=False) if "ay-eyebrow" not in (child.get("class") or [])), None)) if isinstance(lead, Tag) else "",
            "actions": actions,
            "socials": socials,
            "navs": navs,
            "bottom": text(node.select_one(":scope > .ay-footer-bottom")),
        }

    expected_signature = semantic_signature(expected_footer)
    actual_signature = semantic_signature(footer)
    if expected_signature.get("grid") is None:
        return ["live footer authority fixture missing canonical compact grid"]
    if actual_signature.get("grid") is None:
        issues.append("shared footer missing canonical compact grid")
    if actual_signature != expected_signature:
        issues.append("shared footer semantic contract drift from SHA-locked live authority fixture")

    css_path = candidate / "static" / "alex-v4-static-shell.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    expected_css = (
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer{background:#fff!important;color:var(--stitch-ink)!important;padding:clamp(46px,6vw,72px) 20px 42px",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{width:min(100%,1160px);margin:auto;grid-template-columns:minmax(450px,1.15fr) repeat(4,minmax(110px,.7fr))",
        "body.ay-alex-v4-static .ay-site-footer .ay-actions .ay-button-base2026{border:1px solid var(--stitch-line);background:transparent;color:var(--stitch-ink);box-shadow:none}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-socials{display:grid;gap:10px;margin-top:18px}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link,body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link--disabled{display:inline-flex;width:22px;height:22px;align-items:center;justify-content:center;border:0 solid rgba(15,23,42,.1);border-radius:0;background:rgba(244,241,233,.72)!important;color:var(--stitch-ink)!important",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link svg{width:20px;height:20px;fill:currentColor;flex:0 0 auto}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-social-link--disabled{cursor:default;opacity:.58;pointer-events:none}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-link-button{appearance:none;display:inline-flex;min-height:24px;align-items:center;border:0;background:transparent;color:#f4f0e8",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-menu{display:grid;gap:7px;margin:0;padding:0;list-style:none}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-bottom{width:min(100%,960px);margin:34px auto 0;padding:18px 0 0;border-top:1px solid rgba(255,255,255,.12)",
        "@media(max-width:720px){body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer{padding-top:44px!important}body.ay-alex-v4-static.ay-stitch-home-v3 .ay-footer-grid{gap:30px!important}",
        "body.ay-alex-v4-static.ay-stitch-home-v3 .ay-site-footer h2{max-width:none;margin:0 0 14px;font-family:Manrope,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif;font-size:clamp(22px,2.4vw,28px);font-weight:700;line-height:1.16;letter-spacing:normal}",
    )
    for required in expected_css:
        if required not in css:
            issues.append(f"shared footer missing live authority CSS: {required}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--source-root", default="web/static")
    args = parser.parse_args()
    candidate = Path(args.candidate).resolve()
    source_root = Path(args.source_root).resolve()
    manifest_path = candidate / "candidate-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked = Counter()
    rendered_entries = manifest.get("rendered") or []
    if not rendered_entries:
        errors.append("candidate manifest has no rendered source-detail routes")
    else:
        sample_route = str(rendered_entries[0].get("route") or "")
        if not sample_route or not (candidate / sample_route).is_file():
            errors.append("candidate footer sample route missing")
        else:
            errors.extend(validate_shared_footer_contract(candidate, sample_route))
            checked["shared_footer_contract"] += 1

    for route in manifest["future_private_not_emitted"]:
        if (candidate / route).exists():
            errors.append(f"future-private route emitted: {route}")
        checked["future_404"] += 1

    for entry in manifest["rendered"]:
        route = entry["route"]
        canonical = source_root / route
        rendered = candidate / route
        if not rendered.is_file():
            errors.append(f"missing rendered route: {route}")
            continue
        try:
            before = canonical_contract(canonical, route, entry["admission_state"])
            after = candidate_contract(rendered)
            for key in (
                "title", "canonical", "robots", "lang", "state", "handle", "date", "thesis",
                "original_link", "creator_link", "search_link", "policy", "language", "insight_count",
                "topics", "transcript", "insights", "questions", "schema",
            ):
                if before[key] != after[key]:
                    errors.append(f"semantic drift {route}: {key}")
            dropped_hrefs = set(before["local_hrefs"]) - set(after["local_hrefs"])
            if dropped_hrefs:
                errors.append(f"dropped internal links {route}: {sorted(dropped_hrefs)}")
            errors.extend(f"{route}: {issue}" for issue in validate_assets(candidate, rendered))
            state = entry["admission_state"]
            if state == "normal_public_card" and (not after["insights"] or not after["questions"]):
                errors.append(f"normal route missing public intelligence/question surfaces: {route}")
            if state == "provenance_archive_noindex" and (after["insights"] or after["questions"] or after["creator_link"] or after["search_link"]):
                errors.append(f"archive route leaked normal-public surface: {route}")
            checked[state] += 1
        except Exception as exc:
            errors.append(f"validation error {route}: {type(exc).__name__}: {exc}")

    result = {"checked": dict(checked), "errors": errors, "valid": not errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
