from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_roadmaps_match_configured_enrichment_and_measurement_state() -> None:
    roadmap_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "ROADMAP.md",
            "docs/public-pages/01_ROADMAP.md",
            "web/static/roadmap.js",
            "web/static/roadmap.html",
        )
    )
    maps = json.loads(
        (ROOT / "data/base2026_topic_traffic_pages.json").read_text(encoding="utf-8")
    )

    assert len(maps) == 60
    assert all(
        entry.get("answer_capsule")
        and entry.get("proof_source_ids")
        and entry.get("faq")
        for entry in maps.values()
    )
    assert sum(len(entry["proof_source_ids"]) for entry in maps.values()) == 102

    assert "10\u201315" not in roadmap_text
    assert "topic " + "evidence maps" not in roadmap_text.casefold()
    assert "Public VPS deployment" not in roadmap_text
    assert "local-first knowledge base" not in roadmap_text
    assert "Small VPS" not in roadmap_text
    assert "live source content" not in roadmap_text
    for phrase in (
        "private Cloudflare pipeline",
        "60 source-backed entries",
        "measured per entry",
        "22 impressions",
        "0 clicks",
        "55.4",
        "Bing performance data is still preparing",
    ):
        assert phrase in roadmap_text
