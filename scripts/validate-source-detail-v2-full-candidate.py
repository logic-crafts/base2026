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
BASE_PRODUCT_FOOTER_TEMPLATE = ROOT / "templates" / "shared" / "base2026-product-footer.html"
BASE_PRODUCT_FOOTER_TEMPLATE_SHA256 = "31785636250a8afdd3b2dfe831ec5d11ae9141433547334e562431ba611779a7"
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
    """Fail closed if Source Detail drifts from the compact Base product footer.

    The personal-site commercial footer and the Base2026 research-product
    footer have distinct jobs. Check the Base footer's exact canonical markup,
    ownership, navigation, cookie control and responsive CSS without requiring
    a live network request during candidate validation.
    """
    issues: list[str] = []
    fixture_bytes = BASE_PRODUCT_FOOTER_TEMPLATE.read_bytes()
    fixture_digest = hashlib.sha256(fixture_bytes).hexdigest()
    expected_markup = fixture_bytes.decode("utf-8").strip()
    if fixture_digest != BASE_PRODUCT_FOOTER_TEMPLATE_SHA256:
        return [f"Base product footer authority fixture hash drift: {fixture_digest}"]

    page = candidate / route
    page_html = page.read_text(encoding="utf-8")
    raw_footer = re.search(
        r'(<footer\b(?=[^>]*\bdata-b26-product-footer\b)[^>]*>.*?</footer>)',
        page_html,
        flags=re.S,
    )
    if raw_footer is None:
        return ["shared footer missing canonical [data-b26-product-footer]"]
    if raw_footer.group(1).strip() != expected_markup:
        issues.append("shared footer raw DOM drift from SHA-locked Base product authority fixture")

    soup = BeautifulSoup(page_html, "html.parser")
    footer = soup.select_one("footer.ay-site-footer.b26-product-footer[data-b26-product-footer]")
    if not isinstance(footer, Tag):
        return ["shared footer missing canonical Base product classes/marker"]
    expected_soup = BeautifulSoup(expected_markup, "html.parser")
    expected_footer = expected_soup.select_one("footer.ay-site-footer.b26-product-footer[data-b26-product-footer]")
    if not isinstance(expected_footer, Tag):
        return ["Base product footer authority fixture is not parseable"]

    def semantic_signature(node: Tag) -> dict[str, Any]:
        node_grid = node.select_one(":scope > .b26-product-footer__grid[data-b26-shell]")
        if not isinstance(node_grid, Tag):
            return {"grid": None}
        lead = node_grid.find("section", class_="b26-product-footer__identity", recursive=False)
        navs: list[tuple[str, str, list[tuple[str, str]]]] = []
        for nav in node_grid.find_all("nav", recursive=False):
            entries: list[tuple[str, str]] = []
            for control in nav.find_all(["a", "button"], recursive=False):
                target = (
                    "cookie-preferences"
                    if control.name == "button" and control.has_attr("data-cookie-preferences")
                    else attr(control, "href")
                )
                entries.append((text(control), target))
            navs.append((attr(nav, "aria-label"), text(nav.select_one("h3")), entries))
        return {
            "grid": True,
            "root_classes": tuple(node.get("class") or ()),
            "root_label": attr(node, "aria-label"),
            "identity_class": tuple(lead.get("class") or ()) if isinstance(lead, Tag) else None,
            "eyebrow": text(lead.select_one(".eyebrow")) if isinstance(lead, Tag) else "",
            "heading": text(lead.select_one("h2")) if isinstance(lead, Tag) else "",
            "body": text(next((child for child in lead.find_all("p", recursive=False) if "eyebrow" not in (child.get("class") or [])), None)) if isinstance(lead, Tag) else "",
            "navs": navs,
            "cookie_controls": len(node.select("[data-cookie-preferences]")),
            "bottom": text(node.select_one(":scope > .b26-product-footer__bottom[data-b26-shell]")),
        }

    expected_signature = semantic_signature(expected_footer)
    actual_signature = semantic_signature(footer)
    if expected_signature.get("grid") is None:
        return ["Base product footer authority fixture missing canonical compact grid"]
    if actual_signature.get("grid") is None:
        issues.append("shared footer missing canonical Base product grid")
    if actual_signature != expected_signature:
        issues.append("shared footer semantic contract drift from SHA-locked Base product authority fixture")

    css_path = candidate / "static" / "base2026" / "shell.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    expected_css = (
        '[data-b26-visual-root="v2"] .b26-product-footer',
        ".b26-product-footer__grid {",
        "grid-template-columns: minmax(18rem, 1.5fr) repeat(3, minmax(8rem, 1fr));",
        ".b26-product-footer__link-button {",
        ".b26-product-footer__bottom {",
        "background: var(--b26-color-ink-950) !important;",
        "@media (max-width: 48rem)",
    )
    for required in expected_css:
        if required not in css:
            issues.append(f"shared footer missing Base product authority CSS: {required}")
    if any(token in css.lower() for token in ("#c84f07", "#ef6b13", "#d9730d", "fonts.googleapis.com")):
        issues.append("shared footer design asset retains forbidden legacy color/font dependency")
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
