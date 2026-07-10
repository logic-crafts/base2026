from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
VIDEOS_CSV = TIKTOK / "videos.csv"
TRANSCRIPTS = TIKTOK / "transcripts"
RAW_DIR = TRANSCRIPTS / "raw"
AUDIO_DIR = TRANSCRIPTS / "audio-fallback"
CLEAN_DIR = TRANSCRIPTS / "clean"
POLISHED_DIR = TRANSCRIPTS / "polished"
QA_DIR = TRANSCRIPTS / "polished-qa"
DATA_ROOT = ROOT / "public-data" / "tiktok"
PLANNING = ROOT / ".planning" / "insight-repair"
REVIEWED_NO_CARD = ROOT / ".planning" / "reviewed-no-card-sources.jsonl"
REVIEWED_CANDIDATES = TIKTOK / "insight-candidates" / "reviewed-candidates.jsonl"
LOCAL_NOT_LIVE_DECISIONS = ROOT / ".planning" / "tiktok-pipeline-v2" / "local-not-live-decisions.jsonl"
SOURCE_REVIEW_DECISIONS = ROOT / ".planning" / "tiktok-pipeline-v2" / "source-review-decisions.jsonl"
NEEDS_INSIGHT_DECISIONS = ROOT / ".planning" / "tiktok-pipeline-v2" / "needs-insight-editorial-decisions.jsonl"
TERMINAL_LOCAL_NOT_LIVE_DECISIONS = {
    "carry_forward_to_redesign_release",
    "future_cluster_review",
    "retain_provenance_no_card",
    "solution_cluster_contributor",
}
TERMINAL_SOURCE_REVIEW_DECISIONS = {
    "asr_insufficient_private_hold",
    "cold_hold_no_source_or_audio",
    "manual_source_review_complete",
    "terminal_failed_asr_hold",
}
TERMINAL_NEEDS_INSIGHT_DECISIONS = {
    "future_cluster_backlog",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_jsonl(url: str, timeout: int = 25) -> list[dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Base2026 repair queue"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read_videos() -> list[dict[str, str]]:
    with VIDEOS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def raw_caption_exists(video_id: str) -> bool:
    return RAW_DIR.exists() and any(path.is_file() for path in RAW_DIR.rglob(f"{video_id}*.vtt"))


def audio_exists(video_id: str) -> bool:
    if not AUDIO_DIR.exists():
        return False
    return any(path.is_file() and path.stem == video_id for path in AUDIO_DIR.iterdir())


def qa_status(video_id: str) -> str:
    path = QA_DIR / f"{video_id}.json"
    if not path.exists():
        return "missing_qa"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid_qa_json"
    return str(payload.get("status") or "qa_no_status")


def source_review_reason(video_id: str) -> str:
    if raw_caption_exists(video_id):
        return "local_caption_exists"
    if audio_exists(video_id):
        return "audio_available_retry_asr"
    return "no_local_caption_or_audio"


def source_id_for_video(row: dict[str, str]) -> str:
    creator = (row.get("creator_id") or "").replace("tiktok-", "").strip()
    video_id = row.get("video_id") or ""
    return f"tiktok:{creator}:{video_id}" if creator and video_id else ""


def reviewed_sources_from_archive() -> set[str]:
    source_ids: set[str] = set()
    for row in read_jsonl(REVIEWED_CANDIDATES):
        if row.get("review_status") in {"approved", "reviewed", "public"} and row.get("source_id"):
            source_ids.add(str(row["source_id"]))
    return source_ids


def reviewed_no_card_sources() -> set[str]:
    return {str(row.get("source_id")) for row in read_jsonl(REVIEWED_NO_CARD) if row.get("source_id")}


def terminal_local_not_live_decisions(path: Path = LOCAL_NOT_LIVE_DECISIONS) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for row in read_jsonl(path):
        source_id = str(row.get("source_id") or "")
        decision = str(row.get("decision") or "")
        if source_id and row.get("terminal_for_content_freeze") is True and decision in TERMINAL_LOCAL_NOT_LIVE_DECISIONS:
            decisions[source_id] = decision
    return decisions


def terminal_source_review_decisions(path: Path = SOURCE_REVIEW_DECISIONS) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for row in read_jsonl(path):
        video_id = str(row.get("video_id") or "")
        decision = str(row.get("decision") or "")
        if video_id and row.get("terminal_for_content_freeze") is True and decision in TERMINAL_SOURCE_REVIEW_DECISIONS:
            decisions[video_id] = decision
    return decisions


def terminal_needs_insight_decisions(path: Path = NEEDS_INSIGHT_DECISIONS) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for row in read_jsonl(path):
        source_id = str(row.get("source_id") or "")
        decision = str(row.get("decision") or "")
        if source_id and row.get("terminal_for_content_freeze") is True and decision in TERMINAL_NEEDS_INSIGHT_DECISIONS:
            decisions[source_id] = decision
    return decisions


def live_post_ids(live_static_base: str) -> tuple[set[str], str]:
    live_ids: set[str] = set()
    if not live_static_base:
        return live_ids, ""
    try:
        live_rows = fetch_jsonl(live_static_base.rstrip("/") + "/documents.jsonl")
        for row in live_rows:
            for key in ("post_id", "video_id", "source_id", "id"):
                value = str(row.get(key) or "")
                if value:
                    live_ids.add(value)
        live_ids.discard("")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return live_ids, repr(exc)
    return live_ids, ""


def base_source_row(
    source: dict[str, Any],
    source_id: str,
    post_id: str,
    passages_by_source: Counter[str],
    insight_by_source: Counter[str],
    public_insight_by_source: Counter[str],
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "video_id": post_id,
        "item_id": source.get("item_id") or (f"tiktok-video-{post_id}" if post_id else ""),
        "creator_handle": source.get("creator_handle") or source.get("handle") or "",
        "source_url": source.get("source_url") or "",
        "published_at": source.get("published_at") or source.get("published_date") or "",
        "passage_count": int(passages_by_source[source_id]),
        "insight_card_count": int(insight_by_source[source_id]),
        "public_insight_card_count": int(public_insight_by_source[source_id]),
        "reasons": reasons,
    }


def build_insight_queue(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sources = read_jsonl(args.data_root / "source_records.jsonl")
    passages = read_jsonl(args.data_root / "passages.jsonl")
    insights = read_jsonl(args.data_root / "insight_cards.jsonl")
    passages_by_source: Counter[str] = Counter(str(row.get("source_id") or "") for row in passages if row.get("source_id"))
    insight_by_source: Counter[str] = Counter(str(row.get("source_id") or "") for row in insights if row.get("source_id"))
    public_insight_by_source: Counter[str] = Counter(
        str(row.get("source_id") or "") for row in insights if row.get("source_id") and row.get("public")
    )
    reviewed_sources = reviewed_sources_from_archive()
    reviewed_no_card = reviewed_no_card_sources()
    local_not_live_decisions = terminal_local_not_live_decisions()
    needs_insight_decisions = terminal_needs_insight_decisions()
    live_ids, live_error = live_post_ids(args.live_static_base)

    needs_insight_queue: list[dict[str, Any]] = []
    local_not_live_queue: list[dict[str, Any]] = []
    deferred_local_not_live: list[dict[str, Any]] = []
    deferred_needs_insight = 0

    for source in sources:
        source_id = str(source.get("source_id") or "")
        post_id = str(source.get("post_id") or source.get("video_id") or source.get("item_id") or "")
        if post_id.startswith("tiktok-video-"):
            post_id = post_id.removeprefix("tiktok-video-")
        if not source_id or passages_by_source[source_id] == 0:
            continue

        reasons: list[str] = []
        if insight_by_source[source_id] == 0:
            reasons.append("needs_any_insight")
        if public_insight_by_source[source_id] == 0:
            reasons.append("needs_public_insight")
        if live_ids and post_id and post_id not in live_ids:
            reasons.append("local_not_live")
        if source_id in reviewed_no_card:
            reasons.append("reviewed_no_card")
        if source_id in reviewed_sources:
            reasons.append("has_reviewed_candidate_archive")

        base_row = base_source_row(
            source,
            source_id,
            post_id,
            passages_by_source,
            insight_by_source,
            public_insight_by_source,
            reasons,
        )

        if "local_not_live" in reasons:
            local_release_decision = local_not_live_decisions.get(source_id)
            editorial_terminal_decision = needs_insight_decisions.get(source_id)
            no_card_terminal_decision = "reviewed_no_card" if source_id in reviewed_no_card else ""
            terminal_decision = local_release_decision or editorial_terminal_decision or no_card_terminal_decision
            target = deferred_local_not_live if terminal_decision else local_not_live_queue
            target.append(
                {
                    **base_row,
                    "queue_type": "local_not_live_deferred" if terminal_decision else "local_not_live",
                    "priority": 10 if public_insight_by_source[source_id] > 0 else 20,
                    "terminal_decision": terminal_decision or "",
                    "recommended_action": (
                        "carry_forward_to_redesign_release"
                        if local_release_decision
                        else "keep_private_terminal"
                        if terminal_decision
                        else "publish_or_deploy_static_source_after_release_gate"
                    ),
                }
            )

        actionable_insight = (
            ("needs_any_insight" in reasons or "needs_public_insight" in reasons)
            and "reviewed_no_card" not in reasons
            and "has_reviewed_candidate_archive" not in reasons
        )
        if actionable_insight:
            terminal_insight_decision = needs_insight_decisions.get(source_id)
            if terminal_insight_decision:
                deferred_needs_insight += 1
                continue
            priority = 100
            if "needs_any_insight" in reasons:
                priority -= 30
            if str(source.get("published_at") or "") >= args.recent_since:
                priority -= 10
            needs_insight_queue.append(
                {
                    **base_row,
                    "queue_type": "needs_insight",
                    "priority": priority,
                    "recommended_action": "extract_exact_evidence_insight_cards",
                }
            )

    needs_insight_queue.sort(
        key=lambda row: (row["priority"], row.get("published_at") or "", row.get("source_id") or ""),
        reverse=False,
    )
    local_not_live_queue.sort(
        key=lambda row: (row["priority"], row.get("published_at") or "", row.get("source_id") or ""),
        reverse=False,
    )
    summary = {
        "sources": len(sources),
        "passages": len(passages),
        "insight_cards": len(insights),
        "sources_without_any_insight": sum(1 for row in sources if insight_by_source[str(row.get("source_id") or "")] == 0),
        "sources_without_public_insight": sum(1 for row in sources if public_insight_by_source[str(row.get("source_id") or "")] == 0),
        "sources_with_any_insight": sum(1 for row in sources if insight_by_source[str(row.get("source_id") or "")] > 0),
        "sources_with_public_insight": sum(1 for row in sources if public_insight_by_source[str(row.get("source_id") or "")] > 0),
        "queued_needs_insight": len(needs_insight_queue),
        "deferred_needs_insight": deferred_needs_insight,
        "needs_insight_decision_sources": len(needs_insight_decisions),
        "queued_local_not_live": len(local_not_live_queue),
        "deferred_local_not_live": len(deferred_local_not_live),
        "local_not_live_decision_sources": len(local_not_live_decisions),
        "live_ids": len(live_ids),
        "live_error": live_error,
        "reviewed_no_card_sources": len(reviewed_no_card),
        "reviewed_candidate_sources": len(reviewed_sources),
    }
    return needs_insight_queue, local_not_live_queue, summary


def build_source_review_queue(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_videos()
    queue: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    source_review_decisions = terminal_source_review_decisions()
    for row in rows:
        if row.get("transcript_status") != "needs_source_review":
            continue
        video_id = row.get("video_id") or ""
        terminal_decision = source_review_decisions.get(video_id)
        if terminal_decision:
            deferred.append(
                {
                    "video_id": video_id,
                    "source_id": source_id_for_video(row),
                    "decision": terminal_decision,
                }
            )
            continue
        reason = source_review_reason(video_id)
        qa = qa_status(video_id)
        clean_exists = (CLEAN_DIR / f"{video_id}.txt").exists()
        polished_exists = (POLISHED_DIR / f"{video_id}.txt").exists()
        if qa == "pass" and clean_exists and polished_exists:
            action = "clear_reviewed_pass"
            priority = 10
        elif reason == "local_caption_exists":
            action = "manual_or_gpt55_source_review_caption"
            priority = 20
        elif reason == "audio_available_retry_asr":
            action = "retry_asr_then_qa_review"
            priority = 30
        else:
            action = "cold_hold_no_local_caption_or_audio"
            priority = 90
        queue.append(
            {
                "queue_type": "source_review",
                "priority": priority,
                "video_id": video_id,
                "source_id": source_id_for_video(row),
                "creator_id": row.get("creator_id") or "",
                "url": row.get("url") or "",
                "published_at": row.get("published_at") or "",
                "review_status": row.get("review_status") or "",
                "reason": reason,
                "qa_status": qa,
                "clean_exists": clean_exists,
                "polished_exists": polished_exists,
                "recommended_action": action,
            }
        )
    queue.sort(key=lambda row: (row["priority"], row.get("published_at") or "", row.get("video_id") or ""), reverse=False)
    summary = {
        "videos_csv_rows": len(rows),
        "source_review_total": len(queue),
        "source_review_deferred": len(deferred),
        "source_review_decision_rows": len(source_review_decisions),
        "reason_counts": dict(Counter(row["reason"] for row in queue)),
        "qa_counts": dict(Counter(row["qa_status"] for row in queue)),
        "action_counts": dict(Counter(row["recommended_action"] for row in queue)),
    }
    return queue, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build bounded Base2026 TikTok repair queues for source review, insight cards, and local-not-live publication.")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, default=PLANNING)
    parser.add_argument("--live-static-base", default="https://aggressorbulkit.online/knowledge/static")
    parser.add_argument("--recent-since", default="2026-07-01")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    insight_queue, local_not_live_queue, insight_summary = build_insight_queue(args)
    source_review_queue, source_review_summary = build_source_review_queue(args)
    summary = {
        "created_at": now_iso(),
        "insight": insight_summary,
        "source_review": source_review_summary,
        "outputs": {},
        "dry_run": not args.write,
    }
    if args.write:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        insight_path = args.out_dir / f"needs-insight-{stamp}.jsonl"
        local_not_live_path = args.out_dir / f"local-not-live-{stamp}.jsonl"
        source_review_path = args.out_dir / f"source-review-{stamp}.jsonl"
        summary_path = args.out_dir / f"repair-summary-{stamp}.json"
        latest_summary = args.out_dir / "repair-summary-latest.json"
        latest_insight = args.out_dir / "needs-insight-latest.jsonl"
        latest_local_not_live = args.out_dir / "local-not-live-latest.jsonl"
        latest_source_review = args.out_dir / "source-review-latest.jsonl"
        write_jsonl(insight_path, insight_queue)
        write_jsonl(local_not_live_path, local_not_live_queue)
        write_jsonl(source_review_path, source_review_queue)
        write_jsonl(latest_insight, insight_queue)
        write_jsonl(latest_local_not_live, local_not_live_queue)
        write_jsonl(latest_source_review, source_review_queue)
        summary["outputs"] = {
            "insight_queue": str(insight_path),
            "local_not_live_queue": str(local_not_live_path),
            "source_review_queue": str(source_review_path),
            "summary": str(summary_path),
            "latest_insight_queue": str(latest_insight),
            "latest_local_not_live_queue": str(latest_local_not_live),
            "latest_source_review_queue": str(latest_source_review),
            "latest_summary": str(latest_summary),
        }
        write_json(summary_path, summary)
        write_json(latest_summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
