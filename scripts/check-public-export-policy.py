from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from public_manifest_contract import validate_public_dataset_manifest


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Base2026 public export policy.")
    parser.add_argument("export_dir", type=Path)
    args = parser.parse_args()

    export_dir = args.export_dir.resolve()
    manifest_path = export_dir / "manifest.json"
    if not manifest_path.exists():
        fail(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_issues = validate_public_dataset_manifest(manifest)
    if manifest_issues:
        safe_summary = ", ".join(
            f"{item['pointer']}:{item['reason']}" for item in manifest_issues[:20]
        )
        fail(f"public dataset manifest contract failed: {safe_summary}")

    source_records = read_jsonl(export_dir / "source_records.jsonl")
    passages = read_jsonl(export_dir / "passages.jsonl")
    insight_cards = read_jsonl(export_dir / "insight_cards.jsonl")
    topics = read_jsonl(export_dir / "topics.jsonl")

    if not source_records:
        fail("source_records.jsonl is empty")
    if not passages:
        fail("passages.jsonl is empty")
    if not topics:
        fail("topics.jsonl is empty")

    include_full = bool(manifest.get("include_full_transcripts"))
    if not include_full:
        leaked = [row.get("source_id") or row.get("item_id") for row in source_records if row.get("transcript")]
        if leaked:
            fail(f"full transcripts leaked in excerpt-only export: {leaked[:5]}")
        claim_leaks = [row.get("source_id") or row.get("item_id") for row in source_records if "claims" in row]
        if claim_leaks:
            fail(f"unreviewed claims leaked in source records: {claim_leaks[:5]}")

    for row in source_records:
        if not row.get("source_id"):
            fail("source record missing source_id")
        if not row.get("source_url"):
            fail(f"source record missing source_url: {row.get('source_id')}")
        if not include_full and row.get("full_transcript_public"):
            fail(f"excerpt-only source marked full_transcript_public: {row.get('source_id')}")

    for row in passages:
        if not row.get("source_id"):
            fail(f"passage missing source_id: {row.get('id')}")
        if not row.get("source_url"):
            fail(f"passage missing source_url: {row.get('id')}")
        if not row.get("body"):
            fail(f"passage missing body: {row.get('id')}")
        if "claims" in row:
            fail(f"unreviewed claims leaked in passage: {row.get('id')}")

    for row in insight_cards:
        if not row.get("source_id"):
            fail(f"insight missing source_id: {row.get('id')}")
        if not row.get("claim_text"):
            fail(f"insight missing claim_text: {row.get('id')}")
        if row.get("public") and not row.get("evidence_excerpt"):
            fail(f"public insight missing evidence_excerpt: {row.get('id')}")

    for row in topics:
        if not row.get("topic_id"):
            fail(f"topic missing topic_id: {row.get('id')}")
        if not row.get("topic"):
            fail(f"topic missing label: {row.get('topic_id')}")
        if int(row.get("source_count") or 0) < 1:
            fail(f"topic has no source records: {row.get('topic_id')}")
        if row.get("public") and int(row.get("public_insight_count") or 0) < 1:
            fail(f"public topic has no public insight cards: {row.get('topic_id')}")

    print(
        json.dumps(
            {
                "ok": True,
                "include_full_transcripts": include_full,
                "source_records": len(source_records),
                "passages": len(passages),
                "insight_cards": len(insight_cards),
                "public_insight_cards": sum(1 for row in insight_cards if row.get("public")),
                "topics": len(topics),
                "public_topics": sum(1 for row in topics if row.get("public")),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
