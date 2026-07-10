from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
CLEAN_DIR = TIKTOK / "transcripts" / "clean"
POLISHED_DIR = TIKTOK / "transcripts" / "polished"
QA_DIR = TIKTOK / "transcripts" / "polished-qa"
VIDEOS_CSV = TIKTOK / "videos.csv"
VIDEO_ID_RE = re.compile(r"^## Video\s+(\d+)\s*$", re.MULTILINE)
UNCERTAIN_NOTE_RE = re.compile(
    r"\b(unclear|clipped|asr|likely wrong|kept raw|kept unclear|needs audio|audio verification|mid-sentence)\b",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_batch_video_ids(batch_dir: Path | None) -> set[str]:
    if not batch_dir:
        return set()
    ids: set[str] = set()
    if not batch_dir.exists():
        return ids
    for path in sorted(batch_dir.glob("batch-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        ids.update(VIDEO_ID_RE.findall(text))
    return ids


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def preservation_score(raw: str, polished: str) -> float:
    raw_words = words(raw)
    polished_words = words(polished)
    if not raw_words:
        return 1.0 if not polished_words else 0.0
    raw_counts: dict[str, int] = {}
    for word in raw_words:
        raw_counts[word] = raw_counts.get(word, 0) + 1
    kept = 0
    for word in polished_words:
        if raw_counts.get(word, 0) > 0:
            raw_counts[word] -= 1
            kept += 1
    return kept / max(len(raw_words), len(polished_words), 1)


def qa_has_uncertain_notes(qa: dict) -> bool:
    notes = qa.get("notes", "")
    if isinstance(notes, list):
        notes_text = " ".join(str(note) for note in notes)
    else:
        notes_text = str(notes)
    return bool(UNCERTAIN_NOTE_RE.search(notes_text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-preservation", type=float, default=0.72)
    parser.add_argument("--batch-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--allow-needs-review",
        action="store_true",
        help="Exit 0 when polished outputs exist but QA intentionally gates rows as needs_review.",
    )
    args = parser.parse_args()

    batch_ids = read_batch_video_ids(args.batch_dir)
    rows = [r for r in read_csv(VIDEOS_CSV) if r.get("transcript_status") == "transcribed"]
    if batch_ids:
        rows = [r for r in rows if r.get("video_id") in batch_ids]
    clean = []
    polished = []
    needs_review = []
    missing = []

    for row in rows:
        video_id = row.get("video_id", "")
        clean_path = CLEAN_DIR / f"{video_id}.txt"
        polished_path = POLISHED_DIR / f"{video_id}.txt"
        qa_path = QA_DIR / f"{video_id}.json"
        if clean_path.exists():
            clean.append(video_id)
        if polished_path.exists():
            polished.append(video_id)
            raw = clean_path.read_text(encoding="utf-8", errors="replace") if clean_path.exists() else ""
            text = polished_path.read_text(encoding="utf-8", errors="replace")
            score = preservation_score(raw, text)
            if score < args.min_preservation:
                needs_review.append({"video_id": video_id, "preservation_score": round(score, 4)})
            if qa_path.exists():
                try:
                    qa = json.loads(qa_path.read_text(encoding="utf-8"))
                    if qa.get("status") == "needs_review":
                        needs_review.append({"video_id": video_id, "issue": "qa_status_needs_review"})
                    elif qa_has_uncertain_notes(qa):
                        needs_review.append({"video_id": video_id, "issue": "uncertain_qa_notes"})
                except json.JSONDecodeError:
                    needs_review.append({"video_id": video_id, "issue": "invalid_qa_json"})
            else:
                needs_review.append({"video_id": video_id, "issue": "missing_qa"})
        elif clean_path.exists():
            missing.append(video_id)

    data = {
        "transcribed": len(rows),
        "clean_files": len(clean),
        "polished_files": len(polished),
        "missing_polished": len(missing),
        "needs_review": len(needs_review),
        "batch_dir": str(args.batch_dir) if args.batch_dir else "",
        "batch_video_ids": sorted(batch_ids),
        "sample_missing": missing[: args.limit],
        "sample_needs_review": needs_review[: args.limit],
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}={value}")
    if missing:
        return 2
    if needs_review and not args.allow_needs_review:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
