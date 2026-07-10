from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "public-data" / "tiktok"
PLANNING = ROOT / ".planning"
PROMPT_VERSION = "base2026-semantic-review-v2"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compact(text: str, limit: int) -> str:
    value = " ".join((text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(limit - 20, 0)].rstrip() + " ... [truncated]"


def candidate_id(row: dict) -> str:
    value = row.get("candidate_id") or row.get("output_hash") or ""
    if value:
        return str(value)[:16]
    payload = "\n".join(
        [
            row.get("source_id") or "",
            row.get("topic_label") or "",
            row.get("claim_text") or "",
            row.get("evidence_excerpt") or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def group_by_source(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source_id = row.get("source_id") or ""
        if source_id:
            grouped[source_id].append(row)
    return grouped


def load_sources(data_root: Path) -> dict[str, dict]:
    path = data_root / "source_records.jsonl"
    if not path.exists():
        return {}
    return {row.get("source_id") or "": row for row in read_jsonl(path) if row.get("source_id")}


def load_passages(data_root: Path) -> dict[str, list[dict]]:
    return group_by_source(read_jsonl(data_root / "passages.jsonl"))


def select_queue_rows(queue: list[dict], candidates_by_source: dict[str, list[dict]], limit: int) -> list[dict]:
    selected: list[dict] = []
    seen: set[str] = set()
    for row in queue:
        source_id = row.get("source_id") or ""
        if not source_id or source_id in seen:
            continue
        selected.append(row)
        seen.add(source_id)
        if len(selected) >= limit:
            return selected

    for source_id in candidates_by_source:
        if source_id in seen:
            continue
        selected.append({"source_id": source_id})
        seen.add(source_id)
        if len(selected) >= limit:
            break
    return selected


def resolve_mode(mode: str, candidates_path: Path | None) -> str:
    if mode != "auto":
        return mode
    return "review" if candidates_path else "extract"


def response_schema(batch_id: str, mode: str) -> dict:
    candidate_note = (
        "existing id, or new:<source_id>:1 for one added supported claim"
        if mode == "review"
        else "new:<source_id>:1, new:<source_id>:2, or new:<source_id>:3"
    )
    decision_note = "approve|rewrite|reject|needs_human|new_candidate" if mode == "review" else "new_candidate|needs_human"
    claim_note = "final approved or rewritten claim, or empty for reject" if mode == "review" else "final concise source-backed claim"
    action_note = "final suggested action, or empty for reject" if mode == "review" else "final concise suggested action"
    return {
        "review_batch_id": batch_id,
        "decisions": [
            {
                "source_id": "string",
                "candidate_id": candidate_note,
                "decision": decision_note,
                "reason": "short reason grounded in the supplied passages",
                "topic_label": "short topic label",
                "claim_text": claim_note,
                "suggested_action": action_note,
                "evidence_excerpt": "exact excerpt copied from a supplied passage",
                "quality_score": "integer 0-5",
            }
        ],
    }


def review_rules(mode: str) -> list[str]:
    base = [
        "Use only the supplied public passages and candidates, if candidates are present.",
        "Do not add outside facts, dates, brands, statistics, or platform claims.",
        "Every approved, rewritten, or new claim must include an exact evidence excerpt copied from a supplied passage.",
        "Reject or skip generic advice that does not preserve the source meaning.",
        "Return strict JSON only, with no markdown and no prose outside the JSON object.",
    ]
    if mode == "review":
        return [
            *base,
            "Review each local candidate for semantic faithfulness, usefulness, and card-copy quality.",
            "Reject semantic mismatches even when the evidence excerpt is an exact substring.",
            "Rewrite awkward claims into concise, attributed, useful product copy when support is clear.",
            "At most one new_candidate per source, only if all candidates miss one obviously useful supported claim.",
        ]
    return [
        *base,
        "Extract 0-3 useful SEO, GEO, AEO, AI visibility, search, content strategy, local business visibility, or knowledge-base claims per source.",
        "Use decision=new_candidate for each extracted claim.",
        "Use candidate_id values like new:<source_id>:1, new:<source_id>:2, and new:<source_id>:3.",
        "Return no decision for a source if the passages do not support a useful card.",
        "Keep claim_text specific enough to be useful but short enough for a public insight card.",
    ]


def reviewer_checklist(mode: str) -> list[str]:
    if mode == "extract":
        return [
            "Return no more than 3 new_candidate decisions per source.",
            "Use quality_score 4 or 5 only for claims ready for private/pending import.",
            "Keep claim_text under 220 characters.",
            "Keep suggested_action under 280 characters.",
            "Keep evidence_excerpt under 900 characters and copy it exactly from one supplied passage.",
            "Prefer 1-2 strong cards over 3 weak cards.",
        ]
    return [
        "Use quality_score 4 or 5 only for candidates ready for private/pending import.",
        "Reject or mark needs_human when evidence text is present but the claim does not follow from it.",
        "Keep rewritten claim_text under 220 characters.",
        "Keep rewritten suggested_action under 280 characters.",
        "Keep evidence_excerpt under 900 characters and copy it exactly from one supplied passage.",
    ]


def build_packet(args: argparse.Namespace) -> dict:
    queue = read_jsonl(args.queue)
    candidates_path = args.candidates if args.candidates else None
    mode = resolve_mode(args.mode, candidates_path)
    candidates = read_jsonl(candidates_path) if candidates_path else []
    candidates_by_source = group_by_source(candidates)
    passages_by_source = load_passages(args.data_root)
    sources = load_sources(args.data_root)
    selected_rows = select_queue_rows(queue, candidates_by_source, args.limit)
    candidate_name = candidates_path.name if candidates_path else "source-only"
    batch_seed = f"{args.queue.name}:{candidate_name}:{mode}:{args.limit}:{now_iso()}"
    batch_id = f"chatgpt-{mode}-" + hashlib.sha256(batch_seed.encode("utf-8")).hexdigest()[:16]

    packet_sources: list[dict] = []
    for row in selected_rows:
        source_id = row.get("source_id") or ""
        source = sources.get(source_id, {})
        source_candidates = candidates_by_source.get(source_id, [])
        packet_sources.append(
            {
                "source_id": source_id,
                "source_url": row.get("source_url") or source.get("source_url") or "",
                "creator_handle": row.get("creator_handle") or source.get("creator_handle") or "",
                "item_id": row.get("item_id") or source.get("item_id") or "",
                "input_hash": row.get("input_hash") or "",
                "published_date": source.get("published_date") or source.get("published_at") or "",
                "title": compact(source.get("title") or "", args.max_title_chars),
                "public_policy": source.get("public_policy") or "",
                "full_transcript_public": bool(source.get("full_transcript_public")),
                "candidate_count": len(source_candidates),
                "passages": [
                    {
                        "passage_id": passage.get("id") or passage.get("chunk_id") or "",
                        "public_policy": passage.get("public_policy") or "",
                        "body": compact(passage.get("body") or "", args.max_passage_chars),
                    }
                    for passage in passages_by_source.get(source_id, [])[: args.max_passages_per_source]
                ],
                "candidates": [
                    {
                        "candidate_id": candidate_id(candidate),
                        "model_name": candidate.get("model_name") or "",
                        "status": candidate.get("status") or "",
                        "topic_label": candidate.get("topic_label") or "",
                        "claim_text": candidate.get("claim_text") or "",
                        "suggested_action": candidate.get("suggested_action") or "",
                        "evidence_excerpt": candidate.get("evidence_excerpt") or "",
                        "evidence_match_method": candidate.get("evidence_match_method") or "",
                        "evidence_score": candidate.get("evidence_score"),
                    }
                    for candidate in source_candidates
                ],
            }
        )

    return {
        "review_batch_id": batch_id,
        "created_at": now_iso(),
        "prompt_version": PROMPT_VERSION,
        "mode": mode,
        "queue": str(args.queue),
        "candidates_input": str(candidates_path or ""),
        "boundary": {
            "allowed_inputs": [
                "public-data/tiktok/passages.jsonl search passages",
                "private pending claim candidates from .planning when supplied",
            ],
            "forbidden_inputs": [
                "raw captions",
                "full private transcripts",
                "local SQLite files",
                "media/audio/video files",
                "cookies, tokens, credentials, and logs",
            ],
        },
        "response_schema": response_schema(batch_id, mode),
        "review_rules": review_rules(mode),
        "reviewer_checklist": reviewer_checklist(mode),
        "sources": packet_sources,
    }


def markdown_for_packet(packet: dict) -> str:
    schema = json.dumps(packet["response_schema"], ensure_ascii=False, indent=2)
    lines = [
        f"# Base2026 ChatGPT {packet.get('mode', 'review').title()} Packet",
        "",
        "Review this packet with the configured Hermes semantic reviewer (currently GPT-5.6 Sol).",
        "This is a gated semantic-review job, not an autonomous publisher. Use only the supplied public passages.",
        "",
        f"- review_batch_id: `{packet['review_batch_id']}`",
        f"- prompt_version: `{packet['prompt_version']}`",
        f"- mode: `{packet.get('mode') or 'review'}`",
        f"- source count: {len(packet['sources'])}",
        "",
        "## Boundary",
        "",
        "Allowed inputs:",
        *[f"- {item}" for item in packet["boundary"]["allowed_inputs"]],
        "",
        "Forbidden inputs:",
        *[f"- {item}" for item in packet["boundary"]["forbidden_inputs"]],
        "",
        "## Instructions",
        "",
        *[f"- {item}" for item in packet["review_rules"]],
        "",
        "## Reviewer Checklist",
        "",
        *[f"- {item}" for item in packet.get("reviewer_checklist", [])],
        "",
        "Return strict JSON in this shape:",
        "",
        "```json",
        schema,
        "```",
        "",
        "## Sources",
        "",
    ]

    for index, source in enumerate(packet["sources"], 1):
        lines += [
            f"### Source {index}: {source['source_id']}",
            "",
            f"- creator_handle: `{source.get('creator_handle') or ''}`",
            f"- source_url: {source.get('source_url') or ''}",
            f"- item_id: `{source.get('item_id') or ''}`",
            f"- published_date: `{source.get('published_date') or ''}`",
            f"- public_policy: `{source.get('public_policy') or ''}`",
            f"- full_transcript_public: `{source.get('full_transcript_public')}`",
            f"- title: {source.get('title') or ''}",
            "",
            "Passages:",
            "",
        ]
        if source["passages"]:
            for passage in source["passages"]:
                lines += [
                    f"[{passage['passage_id']}]",
                    passage["body"],
                    "",
                ]
        else:
            lines += ["No public passages found for this source.", ""]

        lines += ["Candidates:", ""]
        if source["candidates"]:
            for candidate in source["candidates"]:
                lines += [
                    f"- candidate_id: `{candidate['candidate_id']}`",
                    f"  model_name: `{candidate.get('model_name') or ''}`",
                    f"  status: `{candidate.get('status') or ''}`",
                    f"  evidence_match_method: `{candidate.get('evidence_match_method') or ''}`",
                    f"  topic_label: {candidate.get('topic_label') or ''}",
                    f"  claim_text: {candidate.get('claim_text') or ''}",
                    f"  suggested_action: {candidate.get('suggested_action') or ''}",
                    f"  evidence_excerpt: {candidate.get('evidence_excerpt') or ''}",
                    "",
                ]
        else:
            lines += ["No local candidate was generated for this source.", ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe manual ChatGPT packet for Base2026 claim quality work.")
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, default=None)
    parser.add_argument("--mode", choices=["auto", "review", "extract"], default="auto")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--max-passages-per-source", type=int, default=8)
    parser.add_argument("--max-passage-chars", type=int, default=1600)
    parser.add_argument("--max-title-chars", type=int, default=220)
    args = parser.parse_args()

    if args.limit <= 0:
        raise SystemExit("--limit must be positive.")
    if args.mode == "review" and not args.candidates:
        raise SystemExit("--mode review requires --candidates.")

    stamp = datetime.now().strftime("%Y%m%d")
    out_md = args.out_md or (PLANNING / f"chatgpt-review-packet-{stamp}.md")
    out_json = args.out_json or out_md.with_suffix(".json")
    packet = build_packet(args)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown_for_packet(packet), encoding="utf-8")
    write_json(out_json, packet)
    candidate_count = sum(len(source["candidates"]) for source in packet["sources"])
    passage_count = sum(len(source["passages"]) for source in packet["sources"])
    print(
        json.dumps(
            {
                "review_batch_id": packet["review_batch_id"],
                "mode": packet["mode"],
                "out_md": str(out_md),
                "out_json": str(out_json),
                "sources": len(packet["sources"]),
                "candidates": candidate_count,
                "passages": passage_count,
                "boundary": "public passages plus private pending candidates when supplied",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
