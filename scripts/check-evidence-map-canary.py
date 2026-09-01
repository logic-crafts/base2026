#!/usr/bin/env python3
"""Run local content, canonical and sitemap checks for an evidence-map canary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


MARKER = "BASE2026_EVIDENCE_MAP_CANARY_V1"
CANONICAL_RE = re.compile(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', re.IGNORECASE)
REVERSE_CANONICAL_RE = re.compile(r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.IGNORECASE)
ROBOTS_RE = re.compile(r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', re.IGNORECASE)
REVERSE_ROBOTS_RE = re.compile(r'<meta\b[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']robots["\']', re.IGNORECASE)
H1_RE = re.compile(r"<h1\b[^>]*>([\s\S]*?)</h1>", re.IGNORECASE)
SCHEMA_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', re.IGNORECASE)
HREF_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)', re.IGNORECASE)
LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


class QaError(Exception):
    pass


def metadata(text: str, pattern: re.Pattern[str], reverse: re.Pattern[str]) -> list[str]:
    return pattern.findall(text) + reverse.findall(text)


def visible_words(text: str) -> int:
    return len(re.findall(r"[\w][\w'’-]*", TAG_RE.sub(" ", text), flags=re.UNICODE))


def check_page(path: Path, canonical: str, expected_routes: set[str]) -> dict[str, object]:
    if not path.is_file():
        raise QaError(f"missing generated page: {path}")
    text = path.read_text(encoding="utf-8")
    if MARKER not in text:
        raise QaError(f"missing canary marker: {path}")
    canonicals = metadata(text, CANONICAL_RE, REVERSE_CANONICAL_RE)
    if canonicals != [canonical]:
        raise QaError(f"canonical mismatch in {path}: {canonicals!r} != {[canonical]!r}")
    robots = metadata(text, ROBOTS_RE, REVERSE_ROBOTS_RE)
    if robots != ["index,follow"]:
        raise QaError(f"robots gate failed in {path}: {robots!r}")
    headings = H1_RE.findall(text)
    if len(headings) != 1:
        raise QaError(f"expected one H1 in {path}, found {len(headings)}")
    schemas = SCHEMA_RE.findall(text)
    if len(schemas) != 1:
        raise QaError(f"expected one JSON-LD block in {path}, found {len(schemas)}")
    try:
        json.loads(schemas[0])
    except json.JSONDecodeError as exc:
        raise QaError(f"invalid JSON-LD in {path}: {exc}") from exc
    if visible_words(text) < 260:
        raise QaError(f"page is too thin after rendering: {path}")
    if "full_transcript_public" in text or "file:///" in text or "/Users/" in text or "\\Users\\" in text:
        raise QaError(f"private/runtime marker found in {path}")
    for href in HREF_RE.findall(text):
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            continue
        if parsed.path.startswith("/evidence-maps"):
            route = parsed.path.rstrip("/") or "/evidence-maps"
            if route not in expected_routes:
                raise QaError(f"internal canary link has no generated target: {path} -> {href}")
    return {"path": str(path), "canonical": canonical, "visible_words": visible_words(text), "schema_count": 1}


def run(output_dir: Path, base_url: str) -> dict[str, object]:
    ledger_path = output_dir / "evidence-map-canary-ledger.json"
    if not ledger_path.is_file():
        raise QaError(f"missing canary ledger: {ledger_path}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    candidates = [item for item in ledger.get("candidates", []) if item.get("eligible")]
    if not candidates:
        raise QaError("ledger contains no eligible candidates")
    base = base_url.rstrip("/")
    routes = {"/evidence-maps"} | {str(item["route"]) for item in candidates}
    pages = []
    hub_canonical = f"{base}/evidence-maps"
    pages.append(check_page(output_dir / "evidence-maps.html", hub_canonical, routes))
    for item in candidates:
        route = str(item["route"])
        pages.append(check_page(output_dir / "evidence-maps" / f"{item['slug']}.html", f"{base}{route}", routes))

    shard = output_dir / "sitemaps" / "evidence-maps-canary.xml"
    if not shard.is_file():
        raise QaError(f"missing sitemap shard: {shard}")
    sitemap_text = shard.read_text(encoding="utf-8")
    if MARKER not in sitemap_text:
        raise QaError("missing canary marker in sitemap shard")
    sitemap_urls = set(LOC_RE.findall(sitemap_text))
    expected_urls = {f"{base}{route}" for route in routes}
    if sitemap_urls != expected_urls:
        raise QaError(f"sitemap membership mismatch: {sorted(sitemap_urls)} != {sorted(expected_urls)}")
    css = output_dir / "static" / "evidence-map-canary.css"
    if not css.is_file() or MARKER not in css.read_text(encoding="utf-8"):
        raise QaError(f"missing canary stylesheet: {css}")
    return {"ok": True, "pages_checked": len(pages), "sitemap_urls": len(sitemap_urls), "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated Base2026 evidence-map canary content and indexation gates.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-url", default="https://base2026.dev")
    args = parser.parse_args()
    try:
        report = run(args.output_dir, args.base_url)
    except (QaError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
