#!/usr/bin/env python3
"""Validate and apply Base2026 content-freeze editorial decisions.

The script is local-only. It updates reviewed candidate/no-card/future-decision ledgers;
it does not rebuild, export, deploy, index, or publish anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TIKTOK = ROOT / "12_knowledge-base" / "sources" / "tiktok"
PUBLIC_DATA = ROOT / "public-data" / "tiktok"
DEFAULT_QUEUE = ROOT / ".planning" / "insight-repair" / "needs-insight-latest.jsonl"
DEFAULT_ARCHIVE = TIKTOK / "insight-candidates" / "reviewed-candidates.jsonl"
DEFAULT_NO_CARD = ROOT / ".planning" / "reviewed-no-card-sources.jsonl"
DEFAULT_LEDGER = ROOT / ".planning" / "tiktok-pipeline-v2" / "needs-insight-editorial-decisions.jsonl"
SOURCES = PUBLIC_DATA / "source_records.jsonl"
PASSAGES = PUBLIC_DATA / "passages.jsonl"
ALLOWED_DECISIONS = {"approve_card", "reviewed_no_card", "future_cluster_backlog"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Expected object at {path}:{line_no}")
        rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def require_text(row: dict[str, Any], key: str, source_id: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"{source_id}: {key} is required")
    return value


def require_text_any(row: dict[str, Any], keys: tuple[str, ...], source_id: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    raise ValueError(f"{source_id}: one of {', '.join(keys)} is required")


def load_decisions(paths: list[Path]) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in read_jsonl(path):
            source_id = require_text(row, "source_id", f"{path}")
            if source_id in decisions:
                raise ValueError(f"Duplicate decision for {source_id}")
            decision = require_text(row, "decision", source_id)
            if decision not in ALLOWED_DECISIONS:
                raise ValueError(f"{source_id}: invalid decision {decision!r}")
            decisions[source_id] = row
    return decisions


def validate_coverage(queue_rows: list[dict[str, Any]], decisions: dict[str, dict[str, Any]]) -> None:
    queue_ids = [require_text(row, "source_id", "queue row") for row in queue_rows]
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Queue contains duplicate source IDs")
    missing = sorted(set(queue_ids) - set(decisions))
    extra = sorted(set(decisions) - set(queue_ids))
    if missing or extra:
        raise ValueError(f"Coverage mismatch: missing={len(missing)} extra={len(extra)}; missing_sample={missing[:5]} extra_sample={extra[:5]}")


def validate_and_prepare(
    decisions: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    passages_by_source: dict[str, list[dict[str, Any]]],
    decided_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    approved: list[dict[str, Any]] = []
    no_card: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for source_id in sorted(decisions):
        row = decisions[source_id]
        decision = str(row["decision"])
        reason = require_text(row, "reason", source_id)
        cluster = str(row.get("target_cluster") or row.get("suggested_cluster") or "").strip()
        confidence = float(row.get("confidence") or 0.0)
        if confidence < 0 or confidence > 1:
            raise ValueError(f"{source_id}: confidence must be between 0 and 1")
        base_ledger = {
            "source_id": source_id,
            "decision": decision,
            "target_cluster": cluster or None,
            "reason": reason,
            "confidence": confidence,
            "terminal_for_content_freeze": True,
            "public_state": "approved_local_card" if decision == "approve_card" else ("future_backlog" if decision == "future_cluster_backlog" else "source_only"),
            "decided_at": decided_at,
        }
        if decision == "approve_card":
            if source_id not in sources:
                raise ValueError(f"{source_id}: source record not found")
            claim = require_text_any(row, ("claim_text", "claim"), source_id)
            action = require_text_any(row, ("suggested_action", "action_text", "action"), source_id)
            evidence = require_text(row, "evidence_excerpt", source_id)
            if not cluster:
                raise ValueError(f"{source_id}: target_cluster is required for approve_card")
            matches = [p for p in passages_by_source.get(source_id, []) if evidence in str(p.get("body") or "")]
            if len(matches) != 1:
                raise ValueError(f"{source_id}: evidence excerpt must match exactly one passage; matched={len(matches)}")
            source = sources[source_id]
            passage = matches[0]
            claim_id = "claim:editorial:" + hashlib.sha256(f"{source_id}|{claim}".encode("utf-8")).hexdigest()[:16]
            approved.append({
                "archive_version": 1,
                "archived_at": decided_at,
                "claim_id": claim_id,
                "confidence": confidence,
                "creator_handle": source.get("creator_handle"),
                "evidence_excerpt": evidence,
                "evidence_path": passage.get("evidence_path") or f"public-data/tiktok/passages.jsonl#source_id={source_id}",
                "evidence_score": 1.0,
                "item_id": source.get("item_id"),
                "review_status": "approved",
                "source_id": source_id,
                "source_url": source.get("source_url") or source.get("url"),
                "suggested_action": action,
                "claim_text": claim,
                "topic": cluster,
                "video_id": source.get("video_id") or source_id.rsplit(":", 1)[-1],
            })
            base_ledger["claim_id"] = claim_id
        elif decision == "reviewed_no_card":
            no_card.append({
                "source_id": source_id,
                "resolution_decision": "reviewed_no_card",
                "resolution_notes": reason,
                "reviewed_at": decided_at,
                "target_cluster": cluster or None,
            })
        elif decision == "future_cluster_backlog" and not cluster:
            base_ledger["backlog_bucket"] = "unassigned_future_cluster"
        ledger.append(base_ledger)
    return approved, no_card, ledger


def merge_unique(existing: list[dict[str, Any]], additions: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    merged = {str(row.get(key)): row for row in existing if str(row.get(key) or "").strip()}
    for row in additions:
        row_key = str(row.get(key) or "").strip()
        if row_key in merged:
            raise ValueError(f"Refusing to overwrite existing {key}={row_key}")
        merged[row_key] = row
    return [merged[k] for k in sorted(merged)]


def merge_reviewed_candidates(existing: list[dict[str, Any]], additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {str(row.get("source_id")): row for row in existing if str(row.get("source_id") or "").strip()}
    promotable_statuses = {"candidate", "needs_human", "pending", "rejected"}
    for row in additions:
        source_id = str(row.get("source_id") or "").strip()
        previous = merged.get(source_id)
        if previous is not None:
            previous_status = str(previous.get("review_status") or "").strip()
            if previous_status not in promotable_statuses:
                raise ValueError(f"Refusing to overwrite terminal reviewed candidate source_id={source_id} status={previous_status!r}")
            row = {
                **row,
                "previous_review_status": previous_status or None,
                "supersedes_claim_id": previous.get("claim_id"),
            }
        merged[source_id] = row
    return [merged[k] for k in sorted(merged)]


def merge_terminal_ledger(existing: list[dict[str, Any]], additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {str(row.get("source_id")): row for row in existing if str(row.get("source_id") or "").strip()}
    for row in additions:
        source_id = str(row.get("source_id") or "").strip()
        previous = merged.get(source_id)
        if previous is not None and str(previous.get("decision")) != str(row.get("decision")):
            raise ValueError(
                f"Refusing conflicting terminal decision for source_id={source_id}: "
                f"{previous.get('decision')!r} -> {row.get('decision')!r}"
            )
        if previous is None:
            merged[source_id] = row
    return [merged[k] for k in sorted(merged)]


def process(args: argparse.Namespace) -> dict[str, Any]:
    queue_rows = read_jsonl(args.queue)
    decisions = load_decisions(args.decisions)
    validate_coverage(queue_rows, decisions)
    sources = {str(row.get("source_id")): row for row in read_jsonl(SOURCES)}
    passages_by_source: dict[str, list[dict[str, Any]]] = {}
    for passage in read_jsonl(PASSAGES):
        passages_by_source.setdefault(str(passage.get("source_id")), []).append(passage)
    decided_at = now_iso()
    approved, no_card, ledger = validate_and_prepare(decisions, sources, passages_by_source, decided_at)
    summary = {
        "queue_rows": len(queue_rows),
        "decision_rows": len(decisions),
        "approved_cards": len(approved),
        "reviewed_no_card": len(no_card),
        "future_cluster_backlog": sum(row["decision"] == "future_cluster_backlog" for row in ledger),
        "all_evidence_exact": True,
        "dry_run": not args.apply,
    }
    if args.apply:
        archive_rows = merge_reviewed_candidates(read_jsonl(args.reviewed_archive), approved)
        no_card_rows = merge_unique(read_jsonl(args.reviewed_no_card), no_card, "source_id")
        ledger_rows = merge_terminal_ledger(read_jsonl(args.ledger), ledger)
        write_jsonl(args.reviewed_archive, archive_rows)
        write_jsonl(args.reviewed_no_card, no_card_rows)
        write_jsonl(args.ledger, ledger_rows)
        summary.update({
            "reviewed_archive_total": len(archive_rows),
            "reviewed_no_card_total": len(no_card_rows),
            "ledger_rows_total": len(ledger_rows),
            "ledger": str(args.ledger),
        })
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--decisions", type=Path, action="append", required=True)
    parser.add_argument("--reviewed-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--reviewed-no-card", type=Path, default=DEFAULT_NO_CARD)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(process(args), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
