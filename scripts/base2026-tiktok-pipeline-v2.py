#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
VIDEOS_CSV = TIKTOK / "videos.csv"
CLEAN_DIR = TIKTOK / "transcripts" / "clean"
POLISHED_DIR = TIKTOK / "transcripts" / "polished"
QA_DIR = TIKTOK / "transcripts" / "polished-qa"
PUBLIC_DATA = ROOT / "public-data" / "tiktok"
PLANNING = ROOT / ".planning" / "tiktok-pipeline-v2"
REVIEWED_NO_CARD = ROOT / ".planning" / "reviewed-no-card-sources.jsonl"
REVIEWED_CANDIDATES = TIKTOK / "insight-candidates" / "reviewed-candidates.jsonl"
PIPELINE_VERSION = "2.0.0"
ACTIVE_STAGES = {
    "low_information_hold",
    "needs_polish",
    "source_review",
    "needs_rebuild",
    "needs_insight",
    "needs_topic_repair",
    "page_noindex",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: expected object")
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_work_id(video_id: str, transcript_sha256: str, pipeline_version: str = PIPELINE_VERSION) -> str:
    payload = f"{video_id}\0{transcript_sha256}\0{pipeline_version}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def stable_packet_id(stage: str, work_ids: list[str], pipeline_version: str = PIPELINE_VERSION) -> str:
    payload = "\0".join([stage, pipeline_version, *sorted(work_ids)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def read_videos(path: Path = VIDEOS_CSV) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_qa(video_id: str, qa_dir: Path = QA_DIR) -> dict[str, Any]:
    path = qa_dir / f"{video_id}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid_qa_json"}


def source_indexability(source: dict[str, Any], public_insights: int, passage_count: int) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not (source.get("public_source_text") or source.get("excerpt") or "").strip():
        reasons.append("missing_public_source_text")
    if passage_count <= 0:
        reasons.append("missing_public_passage")
    if public_insights <= 0:
        reasons.append("missing_public_insight")
    if not (source.get("topics") or source.get("topic_labels") or []):
        reasons.append("missing_topic")
    if not (source.get("source_summary_short") or "").strip():
        reasons.append("missing_source_summary")
    if not (source.get("source_url") or "").strip():
        reasons.append("missing_attribution_url")
    if source.get("full_transcript_public") is True:
        reasons.append("full_transcript_public_true")
    return not reasons, reasons


def classify_item(
    *,
    transcript_status: str,
    word_count: int,
    polished_exists: bool,
    qa_status: str,
    source: dict[str, Any] | None,
    public_insights: int,
    passage_count: int,
    reviewed_no_card: bool = False,
    reviewed_candidate: bool = False,
) -> tuple[str, list[str]]:
    source = source or {}
    # Published, evidence-backed artifacts outrank stale CSV/QA flags. Older records
    # may have been explicitly reviewed and promoted even when a conservative QA
    # note remains `needs_review`; reopening them would create a false backlog.
    if source and public_insights > 0:
        topics = source.get("topics") or source.get("topic_labels") or []
        if not topics:
            return "needs_topic_repair", ["missing_topic"]
        eligible, reasons = source_indexability(source, public_insights, passage_count)
        if not eligible:
            return "page_noindex", reasons
        return "content_ready", []
    if transcript_status == "needs_source_review" or qa_status in {"needs_review", "invalid_qa_json"}:
        return "source_review", [qa_status or transcript_status]
    if word_count < 20 and not polished_exists:
        return "low_information_hold", [f"clean_words={word_count}"]
    if not polished_exists or not qa_status:
        return "needs_polish", ["missing_polished" if not polished_exists else "missing_qa"]
    if qa_status != "pass":
        return "source_review", [qa_status]
    if not source:
        return "needs_rebuild", ["qa_pass_not_in_public_export"]
    topics = source.get("topics") or source.get("topic_labels") or []
    if public_insights <= 0 and not reviewed_no_card and not reviewed_candidate:
        return "needs_insight", ["missing_public_insight"]
    if public_insights <= 0 and (reviewed_no_card or reviewed_candidate):
        return "page_noindex", ["reviewed_without_public_insight"]
    if not topics:
        return "needs_topic_repair", ["missing_topic"]
    eligible, reasons = source_indexability(source, public_insights, passage_count)
    if not eligible:
        return "page_noindex", reasons
    return "content_ready", []


def build_inventory(
    *,
    videos_csv: Path = VIDEOS_CSV,
    clean_dir: Path = CLEAN_DIR,
    polished_dir: Path = POLISHED_DIR,
    qa_dir: Path = QA_DIR,
    public_data: Path = PUBLIC_DATA,
) -> list[dict[str, Any]]:
    sources = read_jsonl(public_data / "source_records.jsonl")
    passages = read_jsonl(public_data / "passages.jsonl")
    insights = read_jsonl(public_data / "insight_cards.jsonl")
    sources_by_video = {
        str(row.get("video_id") or row.get("post_id") or ""): row
        for row in sources
        if row.get("video_id") or row.get("post_id")
    }
    passages_by_source = Counter(str(row.get("source_id") or "") for row in passages if row.get("source_id"))
    public_insights_by_source = Counter(
        str(row.get("source_id") or "") for row in insights if row.get("source_id") and row.get("public")
    )
    reviewed_no_card_sources = {
        str(row.get("source_id")) for row in read_jsonl(REVIEWED_NO_CARD) if row.get("source_id")
    }
    reviewed_candidate_sources = {
        str(row.get("source_id"))
        for row in read_jsonl(REVIEWED_CANDIDATES)
        if row.get("source_id") and row.get("review_status") in {"approved", "reviewed", "public"}
    }
    inventory: list[dict[str, Any]] = []
    for video in read_videos(videos_csv):
        video_id = str(video.get("video_id") or "")
        if not video_id:
            continue
        clean_path = clean_dir / f"{video_id}.txt"
        if not clean_path.exists():
            continue
        clean_text = clean_path.read_text(encoding="utf-8", errors="replace").strip()
        transcript_sha256 = sha256_text(clean_text)
        polished_path = polished_dir / f"{video_id}.txt"
        qa = load_qa(video_id, qa_dir)
        qa_status = str(qa.get("status") or "")
        source = sources_by_video.get(video_id, {})
        source_id = str(source.get("source_id") or "")
        public_insights = int(public_insights_by_source[source_id])
        passage_count = int(passages_by_source[source_id])
        stage, reasons = classify_item(
            transcript_status=str(video.get("transcript_status") or ""),
            word_count=len(clean_text.split()),
            polished_exists=polished_path.exists(),
            qa_status=qa_status,
            source=source,
            public_insights=public_insights,
            passage_count=passage_count,
            reviewed_no_card=source_id in reviewed_no_card_sources,
            reviewed_candidate=source_id in reviewed_candidate_sources,
        )
        creator_id = str(video.get("creator_id") or "")
        creator_handle = creator_id.removeprefix("tiktok-") if creator_id else ""
        inventory.append(
            {
                "work_id": stable_work_id(video_id, transcript_sha256),
                "pipeline_version": PIPELINE_VERSION,
                "video_id": video_id,
                "source_id": source_id,
                "creator_id": creator_id,
                "creator_handle": creator_handle,
                "url": video.get("url") or source.get("source_url") or "",
                "published_at": video.get("published_at") or source.get("published_at") or "",
                "title": source.get("title") or video.get("title_or_description") or "",
                "transcript_sha256": transcript_sha256,
                "clean_path": str(clean_path.relative_to(ROOT)),
                "polished_path": str(polished_path.relative_to(ROOT)),
                "qa_path": str((qa_dir / f"{video_id}.json").relative_to(ROOT)),
                "transcript_status": video.get("transcript_status") or "",
                "qa_status": qa_status,
                "word_count": len(clean_text.split()),
                "char_count": len(clean_text),
                "passage_count": passage_count,
                "public_insight_count": public_insights,
                "topic_count": len(source.get("topics") or source.get("topic_labels") or []),
                "stage": stage,
                "reasons": reasons,
            }
        )
    return sorted(inventory, key=lambda row: (row.get("published_at") or "", row["video_id"]), reverse=True)


def summary_for(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    stages = Counter(str(row["stage"]) for row in inventory)
    return {
        "generated_at": now_iso(),
        "pipeline_version": PIPELINE_VERSION,
        "inventory_items": len(inventory),
        "active_queue_items": sum(stages[stage] for stage in ACTIVE_STAGES),
        "stage_counts": dict(sorted(stages.items())),
        "unique_work_ids": len({row["work_id"] for row in inventory}),
        "duplicate_work_ids": len(inventory) - len({row["work_id"] for row in inventory}),
    }


def build_packet(
    inventory: list[dict[str, Any]],
    *,
    stage: str,
    limit: int,
    max_input_chars: int,
    root: Path = ROOT,
    public_data: Path = PUBLIC_DATA,
) -> dict[str, Any]:
    passages_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if stage in {"needs_insight", "needs_topic_repair", "page_noindex"}:
        for passage in read_jsonl(public_data / "passages.jsonl"):
            passages_by_source[str(passage.get("source_id") or "")].append(passage)
    selected: list[dict[str, Any]] = []
    used_chars = 0
    for row in inventory:
        if row.get("stage") != stage:
            continue
        item = {key: value for key, value in row.items() if key not in {"clean_text", "passages"}}
        if stage in {"needs_polish", "source_review", "low_information_hold"}:
            text = (root / row["clean_path"]).read_text(encoding="utf-8", errors="replace").strip()
            item["clean_text"] = text
        else:
            item["passages"] = [
                {
                    "id": passage.get("id") or passage.get("chunk_id") or "",
                    "body": passage.get("body") or "",
                    "public_policy": passage.get("public_policy") or "",
                }
                for passage in passages_by_source.get(str(row.get("source_id") or ""), [])
            ]
        item_chars = len(json.dumps(item, ensure_ascii=False))
        if selected and used_chars + item_chars > max_input_chars:
            break
        if item_chars > max_input_chars and not selected:
            item["packet_warning"] = "single_item_exceeds_budget"
        selected.append(item)
        used_chars += item_chars
        if len(selected) >= limit:
            break
    work_ids = [str(row["work_id"]) for row in selected]
    return {
        "packet_id": stable_packet_id(stage, work_ids),
        "pipeline_version": PIPELINE_VERSION,
        "generated_at": now_iso(),
        "stage": stage,
        "items": selected,
        "item_count": len(selected),
        "estimated_input_chars": used_chars,
        "max_input_chars": max_input_chars,
        "contract": {
            "no_guessing": True,
            "exact_evidence_required": stage in {"needs_insight", "needs_topic_repair", "page_noindex"},
            "unchanged_input_hash_required": True,
            "one_receipt_per_work_id": True,
        },
    }


def command_sync(args: argparse.Namespace) -> int:
    inventory = build_inventory()
    summary = summary_for(inventory)
    queue = [row for row in inventory if row["stage"] in ACTIVE_STAGES]
    summary["outputs"] = {}
    if args.write:
        inventory_path = args.out_dir / "inventory-latest.jsonl"
        queue_path = args.out_dir / "queue-latest.jsonl"
        summary_path = args.out_dir / "summary-latest.json"
        write_jsonl(inventory_path, inventory)
        write_jsonl(queue_path, queue)
        summary["outputs"] = {
            "inventory": str(inventory_path),
            "queue": str(queue_path),
            "summary": str(summary_path),
        }
        write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_packet(args: argparse.Namespace) -> int:
    inventory_path = args.inventory or (args.out_dir / "inventory-latest.jsonl")
    inventory = read_jsonl(inventory_path) if inventory_path.exists() else build_inventory()
    packet = build_packet(
        inventory,
        stage=args.stage,
        limit=args.limit,
        max_input_chars=args.max_input_chars,
    )
    if args.write:
        path = args.output or (args.out_dir / "packets" / f"{args.stage}-{packet['packet_id']}.json")
        write_json(path, packet)
        packet["output"] = str(path)
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotent Base2026 TikTok -> AI Recommends pipeline control plane.")
    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="Reconcile canonical queue state from actual repo artifacts.")
    sync.add_argument("--out-dir", type=Path, default=PLANNING)
    sync.add_argument("--write", action="store_true")
    sync.set_defaults(func=command_sync)

    packet = sub.add_parser("packet", help="Build one bounded, content-addressed agent work packet.")
    packet.add_argument("--stage", required=True, choices=sorted(ACTIVE_STAGES))
    packet.add_argument("--limit", type=int, default=8)
    packet.add_argument("--max-input-chars", type=int, default=32000)
    packet.add_argument("--inventory", type=Path)
    packet.add_argument("--out-dir", type=Path, default=PLANNING)
    packet.add_argument("--output", type=Path)
    packet.add_argument("--write", action="store_true")
    packet.set_defaults(func=command_packet)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
