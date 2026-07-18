#!/usr/bin/env python3
"""Build five deterministic non-Search representatives for bounded visual QA.

The builder reads the accepted public export and one already-public Source
Detail route.  It never emits the full corpus and never writes into web/static.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from template_migration.source_detail import adapt_source_detail, render_source_detail  # noqa: E402


TOPIC_ID = "content-repurposing"
CREATOR_HANDLE = "@neilpatel"
SOURCE_ROUTE = "sources/tiktok-video-7388244947352210734.html"
RENDERER_VERSION = "base2026-nonsearch-v2-representative-20260718"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "base2026_nonsearch_v2_candidate_generator",
        SCRIPTS / "generate-public-pages.py",
    )
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load public-page generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_out(path: Path) -> Path:
    resolved = path.resolve()
    production = (ROOT / "web/static").resolve()
    if resolved == production or production in resolved.parents:
        raise ValueError("Representative candidate must not write under web/static")
    if resolved.exists():
        raise FileExistsError(f"Refusing to overwrite candidate: {resolved}")
    return resolved


def copy_assets(site: Path) -> dict[str, str]:
    static = site / "static"
    static.mkdir(parents=True)
    shutil.copy2(ROOT / "web/static/alex-design-system-v2.css", static / "alex-design-system-v2.css")
    shutil.copy2(ROOT / "web/static/alex-v4-static-shell.js", static / "alex-v4-static-shell.js")
    shutil.copy2(ROOT / "web/static/share-actions.js", static / "share-actions.js")
    shutil.copy2(ROOT / "web/static/cookie-consent.js", static / "cookie-consent.js")
    shutil.copy2(ROOT / "web/static/base2026-solution-journey.js", static / "base2026-solution-journey.js")
    shutil.copy2(ROOT / "web/static/base2026-solution-journey.css", static / "base2026-solution-journey.css")
    (static / "base2026-solution-journey.json").write_text(
        json.dumps(
            {
                "schema": "base2026.solution-journey-registry/v1",
                "solutions": [],
                "source_mappings": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.copy2(SCRIPTS / "base2026_source_detail_v2.js", static / "source-detail-v2.js")
    shutil.copytree(ROOT / "web/static/base2026", static / "base2026")
    shutil.copytree(ROOT / "web/static/vendor", static / "vendor")
    shutil.copytree(ROOT / "web/static/assets", static / "assets")
    required = (
        "alex-design-system-v2.css",
        "alex-v4-static-shell.js",
        "share-actions.js",
        "cookie-consent.js",
        "source-detail-v2.js",
        "base2026-solution-journey.js",
        "base2026-solution-journey.css",
        "base2026-solution-journey.json",
        "base2026/tokens.css",
        "base2026/shell.css",
        "base2026/components.css",
    )
    return {name: sha256(static / name) for name in required}


def meta_contract(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1 = soup.select_one("main h1")
    robots = soup.select_one('meta[name="robots"]')
    canonical = soup.select_one('link[rel="canonical"]')
    return {
        "title": title,
        "h1": h1.get_text(" ", strip=True) if h1 else "",
        "robots": str(robots.get("content") or "") if robots else "",
        "canonical": str(canonical.get("href") or "") if canonical else "",
    }


def build(args: argparse.Namespace) -> dict[str, object]:
    data = Path(args.data).resolve()
    source_root = Path(args.source_root).resolve()
    traffic_config = Path(args.topic_traffic_config).resolve()
    out = safe_out(Path(args.out))
    generator = load_generator()

    inputs = {
        name: data / name
        for name in (
            "source_records.jsonl",
            "passages.jsonl",
            "insight_cards.jsonl",
            "topics.jsonl",
            "creators.jsonl",
        )
    }
    signal_briefs_path = data / "topic_signal_briefs.jsonl"
    missing = [path.name for path in inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Public export is missing required files: {missing}")
    source_file = source_root / SOURCE_ROUTE
    if not source_file.is_file():
        raise FileNotFoundError(f"Accepted public source route is missing: {SOURCE_ROUTE}")

    sources = generator.read_jsonl(inputs["source_records.jsonl"])
    passages = generator.read_jsonl(inputs["passages.jsonl"])
    insights = generator.read_jsonl(inputs["insight_cards.jsonl"])
    topics = generator.read_jsonl(inputs["topics.jsonl"])
    creators = generator.read_jsonl(inputs["creators.jsonl"])
    traffic = generator.read_json(traffic_config)
    signal_briefs = {
        row.get("topic_id"): row
        for row in generator.read_jsonl(signal_briefs_path)
        if row.get("topic_id")
    }
    generator.PUBLISHED_TOPIC_IDS = {
        generator.slug(row.get("topic_id") or row.get("topic") or "uncategorized")
        for row in topics
        if row.get("public")
    }

    topic = next((row for row in topics if row.get("topic_id") == TOPIC_ID and row.get("public")), None)
    if not topic:
        raise ValueError(f"Public representative topic not found: {TOPIC_ID}")
    creator = next((row for row in creators if row.get("handle") == CREATOR_HANDLE), None)
    if not creator:
        raise ValueError(f"Representative creator not found: {CREATOR_HANDLE}")

    normal_sources = [row for row in sources if generator.source_is_normal_public_card(row)]
    creator_sources = [
        row
        for row in normal_sources
        if row.get("creator_handle") == CREATOR_HANDLE or row.get("handle") == CREATOR_HANDLE
    ]
    public_topics = sorted(
        (row for row in topics if generator.is_indexable_topic(row)),
        key=lambda row: (-(int(row.get("public_insight_count") or 0)), row.get("topic") or ""),
    )
    topic_cards = "".join(
        generator.card(
            row.get("topic") or row.get("topic_id") or "Topic",
            row.get("definition") or "",
            f"{generator.slug(row.get('topic_id') or row.get('topic') or 'topic')}.html",
            f"{row.get('public_insight_count') or 0} public insights · {row.get('source_count') or 0} sources",
            component_id="B26-05",
            component_variant="topic-card",
        )
        for row in public_topics[:12]
    )

    rendered = {
        f"topics/{TOPIC_ID}.html": generator.topic_page(
            topic,
            normal_sources,
            passages,
            insights,
            signal_briefs,
            traffic,
        ),
        "topics/index.html": generator.index_page(
            "Topic Evidence Pages",
            "Topic-level evidence pages with source-backed insights and creator comparison links.",
            topic_cards,
            current="topics",
        ),
        "creators/neilpatel.html": generator.creator_page(
            CREATOR_HANDLE,
            creator,
            creator_sources,
            insights,
        ),
        f"compare/{TOPIC_ID}.html": generator.compare_page(topic, insights),
    }
    source_view = adapt_source_detail(
        source_file,
        SOURCE_ROUTE,
        "normal_public_card",
    )
    rendered[SOURCE_ROUTE] = render_source_detail(source_view, RENDERER_VERSION)

    out.mkdir(parents=True)
    site = out / "knowledge"
    site.mkdir()
    asset_hashes = copy_assets(site)
    route_rows = []
    for route, html in sorted(rendered.items()):
        target = site / route
        generator.write_text(target, html)
        soup = BeautifulSoup(target.read_text(encoding="utf-8"), "html.parser")
        if not soup.body or soup.body.get("data-b26-visual-root") != "v2":
            raise ValueError(f"Representative route lacks B26 visual opt-in: {route}")
        bridges = len(soup.select('[data-b26-component="B26-09"]'))
        if bridges > 1:
            raise ValueError(f"Representative route has duplicate B26-09 bridges: {route}")
        route_rows.append(
            {
                "route": route,
                "sha256": sha256(target),
                "bytes": target.stat().st_size,
                "metadata": meta_contract(str(soup)),
                "b26_components": sorted(
                    {str(node.get("data-b26-component")) for node in soup.select("[data-b26-component]")}
                ),
                "b26_09_count": bridges,
            }
        )

    input_hashes = {name: sha256(path) for name, path in sorted(inputs.items())}
    input_hashes[traffic_config.name] = sha256(traffic_config)
    input_hashes[Path(SOURCE_ROUTE).name] = sha256(source_file)
    manifest: dict[str, object] = {
        "schema": "base2026.nonsearch-v2-representative-candidate/v1",
        "renderer_version": RENDERER_VERSION,
        "source_labels": {
            "public_export": args.data_label,
            "source_root": args.source_root_label,
        },
        "input_sha256": input_hashes,
        "optional_input_state": {
            "topic_signal_briefs.jsonl": {
                "present": signal_briefs_path.is_file(),
                "sha256": sha256(signal_briefs_path) if signal_briefs_path.is_file() else None,
            }
        },
        "asset_sha256": asset_hashes,
        "routes": route_rows,
    }
    manifest_path = out / "candidate-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--data-label", default="accepted-public-export")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-root-label", default="accepted-public-web")
    parser.add_argument(
        "--topic-traffic-config",
        default=str(ROOT / "data/base2026_topic_traffic_pages.json"),
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = build(args)
    print(json.dumps({"out": args.out, "routes": len(result["routes"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
