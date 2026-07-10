from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING = ROOT / ".planning"
PROMPT_VERSION = "base2026-semantic-review-v2"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json_document(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text.strip(), flags=re.IGNORECASE)
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            value, _end = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError(f"No JSON object found in {path}")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def source_maps(packet: dict) -> tuple[dict[str, dict], dict[tuple[str, str], dict]]:
    sources: dict[str, dict] = {}
    candidates: dict[tuple[str, str], dict] = {}
    for source in packet.get("sources") or []:
        source_id = source.get("source_id") or ""
        if not source_id:
            continue
        sources[source_id] = source
        for candidate in source.get("candidates") or []:
            candidate_id = candidate.get("candidate_id") or ""
            if candidate_id:
                candidates[(source_id, candidate_id)] = candidate
    return sources, candidates


def source_text(source: dict) -> str:
    return "\n".join(passage.get("body") or "" for passage in source.get("passages") or [])


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def evidence_is_present(evidence: str, source: dict) -> bool:
    text = source_text(source)
    if evidence and evidence in text:
        return True
    return bool(normalize(evidence) and normalize(evidence) in normalize(text))


def quality_score(decision: dict) -> int:
    try:
        return int(decision.get("quality_score"))
    except (TypeError, ValueError):
        return -1


def build_candidate_row(source: dict, decision: dict, original: dict | None, provenance: dict) -> dict:
    claim_text = decision.get("claim_text") or (original or {}).get("claim_text") or ""
    topic_label = decision.get("topic_label") or (original or {}).get("topic_label") or ""
    suggested_action = decision.get("suggested_action") or (original or {}).get("suggested_action") or ""
    evidence_excerpt = decision.get("evidence_excerpt") or (original or {}).get("evidence_excerpt") or ""
    payload = {
        "source_id": source.get("source_id") or "",
        "item_id": source.get("item_id") or "",
        "creator_handle": source.get("creator_handle") or "",
        "topic_id": "-".join(topic_label.lower().split())[:120],
        "topic_label": topic_label,
        "claim_text": claim_text,
        "suggested_action": suggested_action,
        "evidence_excerpt": evidence_excerpt,
        "evidence_source": "passage",
        "source_passage_id": "",
        "model_name": provenance["model_name"],
        "model_endpoint_type": provenance["model_endpoint_type"],
        "prompt_version": provenance["prompt_version"],
        "input_hash": source.get("input_hash") or "",
        "status": "candidate",
        "public": False,
        "needs_review": True,
        "created_at": now_iso(),
        "chatgpt_decision": decision.get("decision") or "",
        "chatgpt_reason": decision.get("reason") or "",
        "chatgpt_quality_score": decision.get("quality_score"),
        "review_candidate_id": decision.get("candidate_id") or "",
    }
    payload["output_hash"] = sha256_payload(payload)
    return payload


def apply_review(packet: dict, review: dict, args: argparse.Namespace) -> tuple[list[dict], dict]:
    expected_batch = packet.get("review_batch_id") or ""
    actual_batch = review.get("review_batch_id") or ""
    if expected_batch and actual_batch != expected_batch:
        raise ValueError(f"review_batch_id mismatch: expected {expected_batch}, got {actual_batch}")

    sources, candidates = source_maps(packet)
    provenance = {
        "model_name": review.get("reviewer_model") or "unspecified-reviewer",
        "model_endpoint_type": review.get("reviewer_endpoint_type") or "review_json_import",
        "prompt_version": packet.get("prompt_version") or PROMPT_VERSION,
    }
    output: list[dict] = []
    stats = {
        "review_batch_id": expected_batch,
        "decisions": 0,
        "written": 0,
        "approved": 0,
        "rewritten": 0,
        "new_candidates": 0,
        "rejected": 0,
        "needs_human": 0,
        "skipped_unknown_source": 0,
        "skipped_unknown_candidate": 0,
        "skipped_missing_required_fields": 0,
        "skipped_missing_evidence": 0,
        "skipped_low_quality": 0,
        "skipped_too_many_new_candidates": 0,
        "skipped_too_long": 0,
    }

    allowed_write_decisions = {"approve", "rewrite", "new_candidate"}
    new_counts_by_source: Counter[str] = Counter()
    for decision in review.get("decisions") or []:
        if not isinstance(decision, dict):
            continue
        stats["decisions"] += 1
        source_id = decision.get("source_id") or ""
        decision_type = decision.get("decision") or ""
        candidate_key = decision.get("candidate_id") or ""
        source = sources.get(source_id)
        if not source:
            stats["skipped_unknown_source"] += 1
            continue

        if decision_type == "reject":
            stats["rejected"] += 1
            continue
        if decision_type == "needs_human":
            stats["needs_human"] += 1
            continue
        if decision_type not in allowed_write_decisions:
            stats["skipped_missing_required_fields"] += 1
            continue
        if quality_score(decision) < args.min_quality_score:
            stats["skipped_low_quality"] += 1
            continue

        original = None
        if decision_type != "new_candidate":
            original = candidates.get((source_id, candidate_key))
            if not original:
                stats["skipped_unknown_candidate"] += 1
                continue
        elif not str(candidate_key).startswith(f"new:{source_id}:"):
            stats["skipped_unknown_candidate"] += 1
            continue
        elif new_counts_by_source[source_id] >= args.max_new_candidates_per_source:
            stats["skipped_too_many_new_candidates"] += 1
            continue

        row = build_candidate_row(source, decision, original, provenance)
        if not row["claim_text"] or not row["topic_label"] or not row["evidence_excerpt"]:
            stats["skipped_missing_required_fields"] += 1
            continue
        if (
            len(row["claim_text"]) > args.max_claim_chars
            or len(row["suggested_action"]) > args.max_action_chars
            or len(row["evidence_excerpt"]) > args.max_evidence_chars
        ):
            stats["skipped_too_long"] += 1
            continue
        if not evidence_is_present(row["evidence_excerpt"], source):
            stats["skipped_missing_evidence"] += 1
            continue

        output.append(row)
        if decision_type == "approve":
            stats["approved"] += 1
        elif decision_type == "rewrite":
            stats["rewritten"] += 1
        elif decision_type == "new_candidate":
            stats["new_candidates"] += 1
            new_counts_by_source[source_id] += 1

    stats["written"] = len(output)
    return output, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a manual ChatGPT review JSON into private claim candidates.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--max-new-candidates-per-source", type=int, default=3)
    parser.add_argument("--min-quality-score", type=int, default=4)
    parser.add_argument("--max-claim-chars", type=int, default=220)
    parser.add_argument("--max-action-chars", type=int, default=280)
    parser.add_argument("--max-evidence-chars", type=int, default=900)
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d")
    out = args.out or (PLANNING / f"claim-candidates-{stamp}-chatgpt-reviewed.jsonl")
    report_path = args.report or out.with_suffix(".report.json")
    packet = parse_json_document(args.packet)
    review = parse_json_document(args.review)
    rows, stats = apply_review(packet, review, args)
    write_jsonl(out, rows)
    stats["out"] = str(out)
    stats["packet"] = str(args.packet)
    stats["review"] = str(args.review)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stats["report"] = str(report_path)
    print(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
