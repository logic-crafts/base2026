from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate-evidence-map-canary.py"
SPEC = importlib.util.spec_from_file_location("generate_evidence_map_canary", SCRIPT)
assert SPEC and SPEC.loader
canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)


def demo_config() -> dict[str, object]:
    return {
        "schema_version": "base2026.evidence-map-canary-config.v1",
        "canary_id": "test",
        "maps": [
            {
                "slug": "demo-evidence-map",
                "topic_id": "demo-topic",
                "title": "How should a public evidence map be used?",
                "meta_description": "A public evidence map with a clear answer, diverse sources and bounded next steps.",
                "target_intent": "How should I use a public evidence map?",
                "answer": "Use an evidence map to answer one bounded question, compare independently attributed public records, and turn the comparison into a small next action. The records provide context and examples; they do not establish consensus, guarantee an outcome or replace checking the original source. Keep the page narrow enough that a reader can understand both the evidence and its limits in one sitting.",
                "scope": "This fixture is for testing the public-safe admission and rendering contract.",
                "actions": [
                    "Define the question before selecting records and keep the resulting page focused on that intent.",
                    "Compare source dates, authors and excerpts rather than treating a repeated phrase as independent proof.",
                    "Record the decision and revisit it when the public source or platform context changes."
                ],
            }
        ],
    }


def demo_rows(count: int = 6) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        creator = f"creator{index % 3}"
        video_id = str(1000000000000 + index)
        rows.append(
            {
                "id": f"row-{index}",
                "source_id": f"tiktok:{creator}:{video_id}",
                "creator_handle": f"@{creator}",
                "body": f"Public evidence excerpt number {index} describes a bounded operational observation with enough context to compare it safely.",
                "title": f"Public record {index} describes a useful operational observation.",
                "source_url": f"https://www.tiktok.com/@{creator}/video/{video_id}",
                "published_date": f"2026-08-{10 + index:02d}",
                "topic_labels": ["Demo topic"],
                "topics": ["demo-topic"],
                "full_transcript_public": False,
                "admission_state": "normal_public_card",
            }
        )
    return rows


def write_envelope(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "estimatedTotalHits": len(rows),
                        "hits": rows,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_canary_renders_only_eligible_public_map(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    export_path = tmp_path / "search.json"
    config_path.write_text(json.dumps(demo_config()), encoding="utf-8")
    write_envelope(export_path, demo_rows())

    ledger = canary.build_canary([export_path], config_path, tmp_path / "source-web", "https://base2026.dev", "2026-09-01")

    assert ledger["eligible_count"] == 1
    assert ledger["rejected_count"] == 0
    candidate = ledger["candidates"][0]
    assert candidate["score"] >= 80
    assert all(candidate["gates"].values())
    page = (tmp_path / "source-web" / "evidence-maps" / "demo-evidence-map.html").read_text(encoding="utf-8")
    assert page.count('<link rel="canonical"') == 1
    assert 'content="index,follow"' in page
    assert page.count("<h1>") == 1
    assert "application/ld+json" in page
    assert "Public evidence excerpt number 0" in page
    assert "raw private fixture material" not in page


def test_rendered_canary_passes_content_and_indexation_qa(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    export_path = tmp_path / "search.json"
    output_dir = tmp_path / "source-web"
    config_path.write_text(json.dumps(demo_config()), encoding="utf-8")
    write_envelope(export_path, demo_rows())
    canary.build_canary([export_path], config_path, output_dir, "https://base2026.dev", "2026-09-01")

    qa_path = Path(__file__).parents[1] / "scripts" / "check-evidence-map-canary.py"
    qa_spec = importlib.util.spec_from_file_location("check_evidence_map_canary", qa_path)
    assert qa_spec and qa_spec.loader
    qa = importlib.util.module_from_spec(qa_spec)
    qa_spec.loader.exec_module(qa)
    report = qa.run(output_dir, "https://base2026.dev")

    assert report["ok"] is True
    assert report["pages_checked"] == 2
    assert report["sitemap_urls"] == 2


def test_low_diversity_candidate_is_rejected(tmp_path: Path) -> None:
    item = demo_config()["maps"][0]
    rows = demo_rows(2)
    metrics = canary.candidate_metrics(item, rows, "https://base2026.dev", tmp_path, [item["slug"]])

    assert metrics["eligible"] is False
    assert "INSUFFICIENT_SOURCE_DIVERSITY" in metrics["rejection_reasons"]
    assert "INSUFFICIENT_UNIQUE_EVIDENCE" in metrics["rejection_reasons"]


def test_private_or_full_transcript_rows_are_not_selected(tmp_path: Path) -> None:
    rows = demo_rows()
    rows[0]["body"] = "raw private fixture material that must never be emitted"
    rows[0]["full_transcript_public"] = True
    selected, counts = canary.select_evidence(rows, "demo-topic")

    assert counts["rejected_rows"] == 1
    assert all(row["id"] != "row-0" for row in selected)
    assert all("raw private fixture material" not in row["body"] for row in selected)


def test_sitemap_index_update_is_idempotent(tmp_path: Path) -> None:
    index = tmp_path / "sitemap.xml"
    index.write_text(
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</sitemapindex>\n',
        encoding="utf-8",
    )
    shard = "https://base2026.dev/sitemaps/evidence-maps-canary.xml"

    assert canary.update_sitemap_index(index, shard, "2026-09-01") is True
    assert canary.update_sitemap_index(index, shard, "2026-09-01") is False
    text = index.read_text(encoding="utf-8")
    assert text.count(shard) == 1
