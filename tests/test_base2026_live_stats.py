from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_stats_are_wired_to_homepage_and_analytics() -> None:
    worker = (ROOT / "cloudflare" / "base2026-worker" / "src" / "index.ts").read_text(encoding="utf-8")
    homepage = (ROOT / "templates" / "base2026-startup-homepage.html").read_text(encoding="utf-8")
    runtime = (ROOT / "templates" / "base2026-evidence-brief.js").read_text(encoding="utf-8")
    analytics = (ROOT / "web" / "static" / "analytics.html").read_text(encoding="utf-8")

    assert 'url.pathname === "/api/stats"' in worker
    assert "full_transcripts_published" in worker
    assert 'fetch("/api/stats"' in runtime
    for key in (
        "documents_indexed",
        "distinct_sources",
        "public_evidence_routes",
        "full_transcripts_published",
    ):
        assert f'data-b26-public-stat="{key}"' in homepage
        assert f'data-b26-public-stat="{key}"' in analytics

    assert "Historical release analytics" in analytics
    assert "2026-07-29 static release" in analytics
    assert "1,724" in analytics
    assert "2,319" in analytics
    assert "1,939" in analytics
    assert "1,204" in analytics
    assert "28 signal briefs" in analytics
    assert "<tbody></tbody>" not in analytics
    assert "/static/base2026-evidence-brief.js" in analytics


def test_public_stats_contract_exposes_no_private_pipeline_payload() -> None:
    worker = (ROOT / "cloudflare" / "base2026-worker" / "src" / "index.ts").read_text(encoding="utf-8")
    stats_contract = worker[worker.index("async function handlePublicStats") : worker.index("function formString")]

    assert "raw_transcript" not in stats_contract
    assert "media" not in stats_contract
    assert "artifact" not in stats_contract
    assert "provider" not in stats_contract
    assert "public_projection_receipts" in stats_contract
    assert "public_projection_cards" in stats_contract
