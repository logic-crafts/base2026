#!/usr/bin/env python3
"""Validate a Base2026 Whole-Corpus Stitch V1 derived release."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, Tag

ACCEPTED_BODY_CLASSES = {"base2026-search-v1", "b26-source-v2"}
REQUIRED_FAMILIES = {
    "ai-visibility": 66,
    "document": 11,
    "compare": 1162,
    "compare-index": 1,
    "creator": 17,
    "creator-index": 1,
    "article": 1,
    "source-index": 1,
    "topic": 1162,
    "topic-index": 1,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attr_set(root: Tag, selector: str, attr: str) -> list[str]:
    return sorted(str(node.get(attr)) for node in root.select(selector) if node.get(attr) is not None)


def main_contract(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main")
    if not isinstance(main, Tag):
        return {"main": False}
    for injected in main.select(".b26-k-local-nav,.b26-k-document-context,[data-b26-injected-text]"):
        injected.decompose()
    forms = []
    for form in main.select("form"):
        fields = sorted((str(field.get("name") or ""), str(field.get("type") or field.name)) for field in form.select("input,select,textarea,button"))
        forms.append((str(form.get("action") or ""), str(form.get("method") or "get").lower(), fields))
    return {
        "main": True,
        "text": " ".join(main.get_text(" ", strip=True).split()),
        "hrefs": attr_set(main, "a[href]", "href"),
        "srcs": attr_set(main, "img[src],source[src],iframe[src],script[src]", "src"),
        "ids": sorted(str(node.get("id")) for node in main.select("[id]") if node.get("id")),
        "forms": forms,
        "data": sorted((node.name, tuple(sorted((key, str(value)) for key, value in node.attrs.items() if key.startswith("data-")))) for node in main.select("*") if any(key.startswith("data-") for key in node.attrs)),
    }


def metadata_contract(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    return {
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "canonical": attr_set(soup, 'link[rel="canonical"]', "href"),
        "meta": sorted((str(node.get("name") or node.get("property") or ""), str(node.get("content") or "")) for node in soup.select("meta[name],meta[property]")),
        "jsonld": sorted(" ".join(node.get_text().split()) for node in soup.select('script[type="application/ld+json"]')),
    }


def accepted_route(rel: str, source: str) -> bool:
    if rel == "index.html" or rel.startswith("solutions/") or (rel.startswith("sources/") and rel != "sources/index.html"):
        return True
    soup = BeautifulSoup(source, "html.parser")
    body = soup.body
    return isinstance(body, Tag) and bool(ACCEPTED_BODY_CLASSES & set(body.get("class") or []))


def balanced_css(css: str) -> bool:
    cleaned = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    cleaned = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "", cleaned)
    return cleaned.count("{") == cleaned.count("}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    candidate = args.candidate.resolve()
    source_web = source / "web"
    candidate_web = candidate / "web"
    errors: list[str] = []
    counts = Counter()

    manifest = json.loads((candidate / "whole-corpus-stitch-v1-manifest.json").read_text(encoding="utf-8"))
    package = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    if package.get("release_name") != candidate.name:
        errors.append(f"package release identity drift: {package.get('release_name')} != {candidate.name}")
    if package.get("package_mode") != "data-preserving-static-derived-whole-corpus-stitch-v1":
        errors.append(f"package mode drift: {package.get('package_mode')}")
    overlay = package.get("whole_corpus_stitch_v1")
    if not isinstance(overlay, dict) or overlay.get("version") != manifest.get("version"):
        errors.append("whole-corpus package lineage missing or inconsistent")
    required_runtime = set(package.get("required_runtime_files") or [])
    for required in (
        "web/static/alex-v4-static-shell.css",
        "web/static/alex-v4-static-shell.js",
        "web/static/base2026-knowledge-stitch-v1.css",
    ):
        if required not in required_runtime:
            errors.append(f"package runtime requirement missing: {required}")
    if manifest.get("protected_drift"):
        errors.append("manifest reports protected drift")
    if manifest.get("family_counts") != REQUIRED_FAMILIES:
        errors.append(f"family counts drift: {manifest.get('family_counts')}")
    if digest(source_web / "sitemap.xml") != digest(candidate_web / "sitemap.xml"):
        errors.append("sitemap.xml changed")

    for source_path in sorted(source_web.rglob("*.html")):
        rel = source_path.relative_to(source_web).as_posix()
        candidate_path = candidate_web / rel
        if not candidate_path.is_file():
            errors.append(f"missing candidate route: {rel}")
            continue
        source_html = source_path.read_text(encoding="utf-8")
        candidate_html = candidate_path.read_text(encoding="utf-8")
        if accepted_route(rel, source_html):
            counts["accepted"] += 1
            if digest(source_path) != digest(candidate_path):
                errors.append(f"accepted byte drift: {rel}")
            continue
        source_main = main_contract(source_html)
        if source_main.get("main") is False:
            counts["redirect"] += 1
            continue
        counts["transformed"] += 1
        if metadata_contract(source_html) != metadata_contract(candidate_html):
            errors.append(f"metadata contract drift: {rel}")
        candidate_main = main_contract(candidate_html)
        for key in ("text", "hrefs", "srcs", "forms", "data"):
            if source_main.get(key) != candidate_main.get(key):
                errors.append(f"main {key} drift: {rel}")
        source_ids = source_main.get("ids")
        candidate_ids = candidate_main.get("ids")
        source_id_set = set(source_ids) if isinstance(source_ids, list) else set()
        candidate_id_set = set(candidate_ids) if isinstance(candidate_ids, list) else set()
        if not source_id_set.issubset(candidate_id_set):
            errors.append(f"original ID removed: {rel}")
        soup = BeautifulSoup(candidate_html, "html.parser")
        body = soup.body
        if not isinstance(body, Tag) or "b26-knowledge-v1" not in (body.get("class") or []):
            errors.append(f"new body contract missing: {rel}")
        if soup.select_one("header.site-header,footer.site-footer"):
            errors.append(f"legacy shell remains: {rel}")
        if not soup.select_one("header.ay-v2-header") or not soup.select_one("footer.ay-site-footer"):
            errors.append(f"canonical shell missing: {rel}")
        if not soup.select_one('link[href*="base2026-knowledge-stitch-v1.css"]'):
            errors.append(f"new stylesheet missing: {rel}")

    css_path = candidate_web / "static" / "base2026-knowledge-stitch-v1.css"
    if not css_path.is_file() or not balanced_css(css_path.read_text(encoding="utf-8")):
        errors.append("knowledge Stitch V1 CSS missing or unbalanced")
    for asset in ("alex-v4-static-shell.css", "alex-v4-static-shell.js"):
        if not (candidate_web / "static" / asset).is_file():
            errors.append(f"missing runtime asset: {asset}")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "counts": dict(counts),
        "expected_total": 4124,
        "errors": errors[:100],
        "error_count": len(errors),
    }
    report_path = candidate / "whole-corpus-stitch-v1-contract-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
