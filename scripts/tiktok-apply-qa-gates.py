from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
VIDEOS_CSV = TIKTOK / "videos.csv"
TRANSCRIPTS = TIKTOK / "transcripts"
QA_DIR = TRANSCRIPTS / "polished-qa"
POLISHED_DIR = TRANSCRIPTS / "polished"
BACKUP_DIR = ROOT / ".planning" / "backups"
VIDEO_ID_RE = re.compile(r"^## Video\s+(\d+)\s*$", re.MULTILINE)
UNCERTAIN_NOTE_RE = re.compile(
    r"\b(unclear|clipped|asr|likely wrong|kept raw|kept unclear|needs audio|audio verification|mid-sentence)\b",
    re.IGNORECASE,
)


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_batch_video_ids(batch_dir: Path | None) -> set[str]:
    if not batch_dir:
        return set()
    ids: set[str] = set()
    if not batch_dir.exists():
        raise FileNotFoundError(f"Batch dir not found: {batch_dir}")
    for path in sorted(batch_dir.glob("batch-*.md")):
        ids.update(VIDEO_ID_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
    return ids


def qa_payload(video_id: str) -> tuple[str, dict[str, Any], str]:
    path = QA_DIR / f"{video_id}.json"
    if not path.exists():
        return "missing_qa", {}, str(path.relative_to(ROOT))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid_qa_json", {}, str(path.relative_to(ROOT))
    status = str(payload.get("status") or "qa_no_status")
    notes = payload.get("notes", "")
    if status == "pass" and notes:
        notes_text = " ".join(str(note) for note in notes) if isinstance(notes, list) else str(notes)
        if UNCERTAIN_NOTE_RE.search(notes_text):
            return "uncertain_qa_notes", payload, str(path.relative_to(ROOT))
    return status, payload, str(path.relative_to(ROOT))


def append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing} | {note}"


def selected_video_ids(args: argparse.Namespace) -> set[str]:
    ids = {str(video_id).strip() for video_id in args.video_id if str(video_id).strip()}
    ids.update(read_batch_video_ids(args.batch_dir))
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply transcript QA gates to TikTok CSV rows so non-pass polish stays private/source-review gated."
    )
    parser.add_argument("--batch-dir", type=Path, default=None, help="Transcript polish batch directory to inspect.")
    parser.add_argument("--video-id", action="append", default=[], help="Explicit video id to inspect. Repeatable.")
    parser.add_argument("--since-date", default="", help="Also inspect rows with collected_at or published_at >= YYYY-MM-DD.")
    parser.add_argument("--apply", action="store_true", help="Write changes to videos.csv. Default is dry-run.")
    args = parser.parse_args()

    rows, fieldnames = read_rows(VIDEOS_CSV)
    ids = selected_video_ids(args)
    if args.since_date:
        for row in rows:
            row_date = max((row.get("collected_at") or "")[:10], (row.get("published_at") or "")[:10])
            if row_date and row_date >= args.since_date and row.get("video_id"):
                ids.add(row["video_id"])
    if not ids:
        raise SystemExit("Refusing to run without --batch-dir, --video-id, or --since-date scope.")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    inspected = 0
    gated = 0
    passed = 0
    skipped = 0
    missing = 0
    decisions: list[dict[str, Any]] = []

    row_by_id = {row.get("video_id", ""): row for row in rows}
    for video_id in sorted(ids):
        row = row_by_id.get(video_id)
        if not row:
            missing += 1
            decisions.append({"video_id": video_id, "decision": "missing_csv_row"})
            continue
        status = row.get("transcript_status") or ""
        if status != "transcribed":
            skipped += 1
            decisions.append({"video_id": video_id, "decision": "skipped_status", "transcript_status": status})
            continue
        inspected += 1
        qa_status, payload, qa_path = qa_payload(video_id)
        polished_exists = (POLISHED_DIR / f"{video_id}.txt").exists()
        if qa_status == "pass" and polished_exists:
            passed += 1
            decisions.append({"video_id": video_id, "decision": "pass", "qa_status": qa_status})
            continue
        gated += 1
        reason = qa_status if not polished_exists else f"qa_{qa_status}"
        decisions.append(
            {
                "video_id": video_id,
                "decision": "gate_private_source_review",
                "reason": reason,
                "qa_path": qa_path,
                "previous_transcript_status": status,
                "previous_review_status": row.get("review_status") or "",
            }
        )
        if args.apply:
            row["transcript_status"] = "needs_source_review"
            row["review_status"] = "needs_source_review"
            row["notes"] = append_note(
                row.get("notes", ""),
                f"{now} QA gate held private for source/audio review ({reason}).",
            )

    backup = ""
    if args.apply and gated:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / f"videos-before-qa-gates-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
        shutil.copy2(VIDEOS_CSV, backup_path)
        write_rows(VIDEOS_CSV, rows, fieldnames)
        backup = str(backup_path.relative_to(ROOT))

    result = {
        "ok": True,
        "dry_run": not args.apply,
        "scope_count": len(ids),
        "inspected_transcribed": inspected,
        "passed": passed,
        "gated_private_source_review": gated,
        "skipped_non_transcribed": skipped,
        "missing_csv_rows": missing,
        "backup": backup,
        "decisions": decisions[:80],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
