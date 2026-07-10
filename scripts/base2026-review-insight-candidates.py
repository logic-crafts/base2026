from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "12_knowledge-base"
DB = KB / "indexes" / "kb.sqlite"
DATA_ROOT = ROOT / "public-data" / "tiktok"
PLANNING = ROOT / ".planning"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_source_scope(path: Path | None) -> set[str]:
    if path is None:
        return set()
    return {str(row.get("source_id")) for row in read_jsonl(path) if row.get("source_id")}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def source_id_from_path(path: str) -> str:
    match = re.search(r"(?:^|[#&?])source_id=([^#&]+)", path or "")
    return match.group(1) if match else ""


def load_source_maps(data_root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    by_source: dict[str, dict] = {}
    by_video: dict[str, dict] = {}
    for row in read_jsonl(data_root / "source_records.jsonl"):
        source_id = row.get("source_id") or ""
        video_id = str(row.get("video_id") or row.get("post_id") or "")
        if source_id:
            by_source[source_id] = row
        if video_id:
            by_video[video_id] = row
    return by_source, by_video


def load_passages(data_root: Path) -> dict[str, list[dict]]:
    passages_by_source: dict[str, list[dict]] = defaultdict(list)
    for row in read_jsonl(data_root / "passages.jsonl"):
        passages_by_source[row.get("source_id") or ""].append(row)
    return passages_by_source


def pending_candidates(db: Path, status: str) -> list[dict]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT
              c.claim_id,
              c.claim_text,
              c.topic,
              c.claim_type,
              c.suggested_action,
              c.confidence,
              c.review_status,
              c.created_at,
              c.updated_at,
              ce.video_id,
              ce.evidence_path,
              ce.quote_or_span
            FROM claims c
            JOIN claim_evidence ce ON ce.claim_id = c.claim_id
            WHERE c.claim_type = 'insight_card_candidate'
              AND c.review_status = ?
            ORDER BY c.created_at ASC, c.claim_id ASC
            """,
            (status,),
        ).fetchall()
    finally:
        con.close()
    return [dict(row) for row in rows]


def existing_public_candidate_counts(db: Path, sources_by_video: dict[str, dict]) -> Counter:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT
              c.claim_id,
              ce.video_id,
              ce.evidence_path
            FROM claims c
            JOIN claim_evidence ce ON ce.claim_id = c.claim_id
            WHERE c.claim_type = 'insight_card_candidate'
              AND c.review_status IN ('approved', 'reviewed', 'public')
            """
        ).fetchall()
    finally:
        con.close()
    counts: Counter = Counter()
    for row in rows:
        source_id = source_id_from_path(row["evidence_path"] or "")
        if not source_id:
            source = sources_by_video.get(str(row["video_id"] or ""), {})
            source_id = source.get("source_id") or ""
        if source_id:
            counts[source_id] += 1
    return counts


def evidence_match(row: dict, source_id: str, passages_by_source: dict[str, list[dict]]) -> tuple[str, float]:
    evidence = row.get("quote_or_span") or ""
    texts = [passage.get("body") or "" for passage in passages_by_source.get(source_id, [])]
    joined = "\n".join(texts)
    if evidence and evidence in joined:
        return "exact", 1.0
    if normalize(evidence) and normalize(evidence) in normalize(joined):
        return "normalized_exact", 0.95
    return "missing", 0.0


def source_id_for(row: dict, sources_by_source: dict[str, dict], sources_by_video: dict[str, dict]) -> str:
    from_path = source_id_from_path(row.get("evidence_path") or "")
    if from_path:
        return from_path
    video_id = str(row.get("video_id") or "")
    source = sources_by_video.get(video_id, {})
    return source.get("source_id") or ""


def text_quality_warnings(row: dict, args: argparse.Namespace) -> list[str]:
    warnings: list[str] = []
    claim = row.get("claim_text") or ""
    action = row.get("suggested_action") or ""
    evidence = row.get("quote_or_span") or ""
    topic = row.get("topic") or ""
    if not topic.strip():
        warnings.append("missing_topic")
    if len(claim.strip()) < args.min_claim_chars:
        warnings.append("claim_too_short")
    if len(claim) > args.max_claim_chars:
        warnings.append("claim_too_long")
    if len(action.strip()) < args.min_action_chars:
        warnings.append("action_too_short")
    if len(action) > args.max_action_chars:
        warnings.append("action_too_long")
    if len(evidence.strip()) < args.min_evidence_chars:
        warnings.append("evidence_too_short")
    if len(evidence) > args.max_evidence_chars:
        warnings.append("evidence_too_long")
    if normalize(claim) == normalize(action):
        warnings.append("action_duplicates_claim")
    if re.search(r"\b(could potentially|suggesting that|suggesting google|may no longer)\b", claim, re.I):
        warnings.append("speculative_claim_language")
    if re.search(r"\b(leverage|utilize|unlock|game[- ]changer|boost your seo|explore the implications|assess how|optimi[sz]e content)\b", action, re.I):
        warnings.append("generic_action_language")
    if re.search(r"\b(repost all|all positive|all feedback|everything positive)\b", action, re.I):
        warnings.append("overbroad_action_language")
    return warnings


def classify(row: dict, soft_warnings: list[str], hard_failures: list[str]) -> str:
    if hard_failures:
        return "reject_candidate"
    if soft_warnings:
        return "needs_human"
    return "promotion_candidate"


def review_candidates(args: argparse.Namespace) -> dict:
    rows = pending_candidates(args.db, args.status)
    sources_by_source, sources_by_video = load_source_maps(args.data_root)
    source_scope = load_source_scope(args.source_ids_jsonl)
    if source_scope:
        rows = [
            row
            for row in rows
            if source_id_for(row, sources_by_source, sources_by_video) in source_scope
        ]
    passages_by_source = load_passages(args.data_root)
    public_candidate_counts = existing_public_candidate_counts(args.db, sources_by_video)
    source_counts = Counter()
    reviewed: list[dict] = []

    for row in rows:
        source_id = source_id_for(row, sources_by_source, sources_by_video)
        source = sources_by_source.get(source_id, {})
        source_counts[source_id] += 1
        hard: list[str] = []
        soft = text_quality_warnings(row, args)
        if not source_id:
            hard.append("missing_source_id")
        if source_id and source_id not in sources_by_source:
            hard.append("source_record_missing")
        method, evidence_score = evidence_match(row, source_id, passages_by_source)
        if method == "missing":
            hard.append("evidence_missing_from_public_passages")
        if source.get("full_transcript_public"):
            soft.append("source_full_transcript_public_true")
        if (source.get("public_policy") or "") not in {"excerpt_only", "search_passage"}:
            soft.append("unexpected_source_public_policy")

        reviewed.append(
            {
                "claim_id": row.get("claim_id") or "",
                "source_id": source_id,
                "video_id": row.get("video_id") or "",
                "creator_handle": source.get("creator_handle") or source.get("handle") or "",
                "source_url": source.get("source_url") or "",
                "claim_text": row.get("claim_text") or "",
                "topic": row.get("topic") or "",
                "suggested_action": row.get("suggested_action") or "",
                "evidence_excerpt": row.get("quote_or_span") or "",
                "confidence": row.get("confidence"),
                "review_status": row.get("review_status") or "",
                "created_at": row.get("created_at") or "",
                "evidence_match_method": method,
                "evidence_score": evidence_score,
                "existing_public_candidate_count": public_candidate_counts.get(source_id, 0),
                "hard_failures": hard,
                "soft_warnings": soft,
                "recommended_status": classify(row, soft, hard),
            }
        )

    per_source_rank: dict[str, int] = defaultdict(int)
    for row in reviewed:
        if row["recommended_status"] != "promotion_candidate":
            continue
        per_source_rank[row["source_id"]] += 1
        row["source_candidate_rank"] = per_source_rank[row["source_id"]]
        remaining_slots = max(
            0,
            args.max_promotion_candidates_per_source - row["existing_public_candidate_count"],
        )
        if row["source_candidate_rank"] > remaining_slots:
            row["soft_warnings"].append("over_source_promotion_limit")
            row["recommended_status"] = "needs_human"
    for row in reviewed:
        row.setdefault("source_candidate_rank", 0)

    counts = Counter(row["recommended_status"] for row in reviewed)
    evidence_counts = Counter(row["evidence_match_method"] for row in reviewed)
    warning_counts = Counter(warning for row in reviewed for warning in row["soft_warnings"])
    failure_counts = Counter(failure for row in reviewed for failure in row["hard_failures"])
    return {
        "generated_at": now_iso(),
        "db": str(args.db),
        "status": args.status,
        "source_scope_file": str(args.source_ids_jsonl or ""),
        "source_scope_count": len(source_scope),
        "total_candidates": len(reviewed),
        "recommendation_counts": dict(sorted(counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "failure_counts": dict(sorted(failure_counts.items())),
        "sources": len({row["source_id"] for row in reviewed if row["source_id"]}),
        "max_promotion_candidates_per_source": args.max_promotion_candidates_per_source,
        "candidates": reviewed,
    }


def markdown_for_report(report: dict) -> str:
    lines = [
        "# Base2026 Pending Insight Candidate Review",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- total_candidates: {report['total_candidates']}",
        f"- sources: {report['sources']}",
        f"- max_promotion_candidates_per_source: {report['max_promotion_candidates_per_source']}",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["recommendation_counts"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Evidence", ""]
    for key, value in report["evidence_counts"].items():
        lines.append(f"- {key}: {value}")
    if report["failure_counts"]:
        lines += ["", "## Hard Failures", ""]
        for key, value in report["failure_counts"].items():
            lines.append(f"- {key}: {value}")
    if report["warning_counts"]:
        lines += ["", "## Soft Warnings", ""]
        for key, value in report["warning_counts"].items():
            lines.append(f"- {key}: {value}")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in report["candidates"]:
        grouped[row["recommended_status"]].append(row)

    for status in ["promotion_candidate", "needs_human", "reject_candidate"]:
        rows = grouped.get(status, [])
        lines += ["", f"## {status}", ""]
        if not rows:
            lines.append("None.")
            continue
        for row in rows:
            lines += [
                f"### {row['claim_id']}",
                "",
                f"- source: `{row['source_id']}`",
                f"- creator: `{row['creator_handle']}`",
                f"- topic: `{row['topic']}`",
                f"- evidence: `{row['evidence_match_method']}`",
                f"- warnings: {', '.join(row['soft_warnings']) if row['soft_warnings'] else 'none'}",
                f"- failures: {', '.join(row['hard_failures']) if row['hard_failures'] else 'none'}",
                f"- claim: {row['claim_text']}",
                f"- action: {row['suggested_action']}",
                f"- evidence_excerpt: {row['evidence_excerpt']}",
                "",
            ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review private pending Base2026 insight-card candidates before promotion.")
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--status", default="pending")
    parser.add_argument(
        "--source-ids-jsonl",
        type=Path,
        default=None,
        help="Optional JSONL scope; only pending candidates whose source_id appears in this file are reviewed.",
    )
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument(
        "--out-candidates-jsonl",
        type=Path,
        default=None,
        help="Optional strict-check input containing only promotion_candidate rows from this scoped report.",
    )
    parser.add_argument("--max-promotion-candidates-per-source", type=int, default=2)
    parser.add_argument("--min-claim-chars", type=int, default=35)
    parser.add_argument("--max-claim-chars", type=int, default=220)
    parser.add_argument("--min-action-chars", type=int, default=35)
    parser.add_argument("--max-action-chars", type=int, default=280)
    parser.add_argument("--min-evidence-chars", type=int, default=20)
    parser.add_argument("--max-evidence-chars", type=int, default=900)
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d")
    out_json = args.out_json or (PLANNING / f"pending-insight-candidate-review-{stamp}.json")
    out_md = args.out_md or out_json.with_suffix(".md")
    report = review_candidates(args)
    write_json(out_json, report)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown_for_report(report), encoding="utf-8")
    strict_rows = [
        row for row in report["candidates"] if row["recommended_status"] == "promotion_candidate"
    ]
    if args.out_candidates_jsonl:
        write_jsonl(args.out_candidates_jsonl, strict_rows)
    summary = {
        "out_json": str(out_json),
        "out_md": str(out_md),
        "out_candidates_jsonl": str(args.out_candidates_jsonl or ""),
        "strict_candidates": len(strict_rows),
        "total_candidates": report["total_candidates"],
        "sources": report["sources"],
        "recommendation_counts": report["recommendation_counts"],
        "evidence_counts": report["evidence_counts"],
        "failure_counts": report["failure_counts"],
        "warning_counts": report["warning_counts"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
