from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from public_manifest_contract import PUBLIC_DATASET_MANIFEST_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "12_knowledge-base"
DB = KB / "indexes" / "kb.sqlite"
OUT = ROOT / "public-data" / "tiktok"
SOURCE_ADMISSION = KB / "sources" / "tiktok" / "source-admission.jsonl"

NORMAL_PUBLIC_CARD = "normal_public_card"
FUTURE_PRIVATE_BACKLOG = "future_private_backlog"
PROVENANCE_ARCHIVE_NOINDEX = "provenance_archive_noindex"
PRIVATE_HOLD_UNCLASSIFIED = "private_hold_unclassified"
ALLOWED_ADMISSION_STATES = {
    NORMAL_PUBLIC_CARD,
    FUTURE_PRIVATE_BACKLOG,
    PROVENANCE_ARCHIVE_NOINDEX,
}


def read_kb_text(rel_path: str | None) -> str:
    if not rel_path:
        return ""
    path = (KB / rel_path).resolve()
    try:
        path.relative_to(KB.resolve())
    except ValueError:
        return ""
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_admission(path: Path) -> dict[str, str]:
    admissions: dict[str, str] = {}
    if not path.exists():
        return admissions
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            source_id = (row.get("source_id") or "").strip()
            state = (row.get("admission_state") or "").strip()
            if not source_id:
                raise ValueError(f"missing source_id at {path}:{line_number}")
            if source_id in admissions:
                raise ValueError(f"duplicate source_id {source_id} at {path}:{line_number}")
            if state not in ALLOWED_ADMISSION_STATES:
                raise ValueError(f"invalid admission_state {state!r} for {source_id}")
            admissions[source_id] = state
    return admissions


def source_admission_state(source_id: str, admissions: dict[str, str], *, ledger_active: bool) -> str:
    if not ledger_active:
        return NORMAL_PUBLIC_CARD
    return admissions.get(source_id, PRIVATE_HOLD_UNCLASSIFIED)


def creator_profile(profiles: dict, creator_id: str, handle: str) -> dict:
    candidates = [
        creator_id,
        handle,
        handle.lstrip("@"),
        f"@{handle.lstrip('@')}" if handle else "",
    ]
    for key in candidates:
        if key and isinstance(profiles.get(key), dict):
            return profiles[key]
    return {}


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}


def compact_text(value: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if not limit or len(text) <= limit:
        return text
    candidate = text[: max(limit - 3, 0)].rstrip()
    sentence_cut = max(candidate.rfind(". "), candidate.rfind("? "), candidate.rfind("! "))
    if sentence_cut >= max(80, int(limit * 0.55)):
        candidate = candidate[: sentence_cut + 1].rstrip()
    else:
        word_cut = candidate.rfind(" ")
        if word_cut >= max(40, int(limit * 0.65)):
            candidate = candidate[:word_cut].rstrip()
    return candidate.rstrip(" ,;:.") + "..."


def normalize_public_source_text(transcript: str, chunk_rows: list[sqlite3.Row]) -> str:
    text = (transcript or "").strip()
    if not text:
        text = "\n\n".join((chunk["text"] or "").strip() for chunk in chunk_rows if (chunk["text"] or "").strip())
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = []
    for paragraph in re.split(r"\n{2,}", text):
        clean = re.sub(r"[ \t]+", " ", paragraph).strip()
        if clean:
            paragraphs.append(clean)
    if paragraphs:
        return "\n\n".join(paragraphs)
    return re.sub(r"\s+", " ", text).strip()


def public_excerpt_text(transcript: str, chunk_rows: list[sqlite3.Row], limit: int = 1600) -> str:
    public_text = ""
    for chunk in chunk_rows:
        public_text = chunk["text"] or ""
        if public_text.strip():
            break
    if not public_text:
        public_text = transcript or ""
    return compact_text(public_text, limit)


def first_sentence(value: str, limit: int = 180) -> str:
    text = compact_text(value, 0)
    if not text:
        return ""
    match = re.match(r"(.{24,220}?[.!?])(?:\s|$)", text)
    return compact_text(match.group(1) if match else text, limit)


def reviewed_claims(claim_rows: list[dict]) -> list[dict]:
    public_statuses = {"approved", "reviewed", "public"}
    return [
        claim
        for claim in claim_rows
        if (claim.get("review_status") or "").lower() in public_statuses
        and (claim.get("claim_text") or "").strip()
    ]


def source_summary_short(title: str, title_status: str, topic_labels: list[str], source_text: str, claim_rows: list[dict]) -> str:
    title_text = compact_text(title, 180)
    if title_text and (title_status or "").lower() != "truncated":
        return title_text
    claims = reviewed_claims(claim_rows)
    if claims:
        return compact_text(claims[0].get("claim_text") or "", 180)
    if topic_labels:
        return compact_text(f"This video discusses {', '.join(topic_labels[:3])}.", 180)
    return first_sentence(source_text, 180)


def source_summary_long(short_summary: str, topic_labels: list[str], source_text: str, claim_rows: list[dict]) -> str:
    claims = [compact_text(claim.get("claim_text") or "", 180) for claim in reviewed_claims(claim_rows)[:3]]
    claims = [claim for claim in claims if claim]
    if claims:
        detail = " ".join(claims)
    elif topic_labels:
        detail = f"This source is indexed under {', '.join(topic_labels[:5])}."
    else:
        return ""
    topic_note = f" Main topics: {', '.join(topic_labels[:5])}." if topic_labels else ""
    if short_summary and detail and not detail.lower().startswith(short_summary.lower()):
        return compact_text(f"{short_summary} {detail}{topic_note}", 700)
    return compact_text(f"{detail or short_summary}{topic_note}", 700)


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def evidence_is_in_chunks(evidence: str, chunk_rows: list[sqlite3.Row]) -> bool:
    normalized_evidence = re.sub(r"\s+", " ", (evidence or "").strip()).lower()
    if not normalized_evidence:
        return False
    normalized_text = re.sub(
        r"\s+",
        " ",
        " ".join((chunk["text"] or "") for chunk in chunk_rows).strip(),
    ).lower()
    return normalized_evidence in normalized_text


def slugify(value: str) -> str:
    slug = "-".join(re.findall(r"[a-z0-9]+", (value or "").lower()))
    return slug[:80] or "uncategorized"


def best_evidence_excerpt(claim_text: str, chunk_rows: list[sqlite3.Row]) -> tuple[str, float]:
    claim_tokens = tokenize(claim_text)
    if not claim_tokens:
        return "", 0.0
    best_text = ""
    best_score = 0.0
    for chunk in chunk_rows:
        text = chunk["text"] or ""
        chunk_tokens = tokenize(text)
        if not chunk_tokens:
            continue
        score = len(claim_tokens & chunk_tokens) / max(len(claim_tokens), 1)
        if score > best_score:
            best_score = score
            best_text = text
    return compact_text(best_text), round(best_score, 3)


def build_topic_records(insight_cards: list[dict], chunks: list[dict]) -> list[dict]:
    topic_labels: dict[str, str] = {}
    insight_counts: Counter[str] = Counter()
    public_insight_counts: Counter[str] = Counter()
    passage_counts: Counter[str] = Counter()
    source_ids: dict[str, set[str]] = defaultdict(set)
    public_source_ids: dict[str, set[str]] = defaultdict(set)
    creator_counts: dict[str, Counter[str]] = defaultdict(Counter)
    public_creator_counts: dict[str, Counter[str]] = defaultdict(Counter)
    latest_dates: dict[str, str] = {}

    for insight in insight_cards:
        topic_id = insight.get("topic_id") or slugify(insight.get("topic") or "")
        if not topic_id:
            continue
        topic_labels.setdefault(topic_id, insight.get("topic") or topic_id.replace("-", " ").title())
        insight_counts[topic_id] += 1
        source_id = insight.get("source_id") or ""
        creator = insight.get("creator_handle") or ""
        if source_id:
            source_ids[topic_id].add(source_id)
        if creator:
            creator_counts[topic_id][creator] += 1
        published_at = insight.get("published_at") or ""
        if published_at > latest_dates.get(topic_id, ""):
            latest_dates[topic_id] = published_at
        if insight.get("public"):
            public_insight_counts[topic_id] += 1
            if source_id:
                public_source_ids[topic_id].add(source_id)
            if creator:
                public_creator_counts[topic_id][creator] += 1

    for chunk in chunks:
        for topic_id in chunk.get("topics") or []:
            topic_labels.setdefault(topic_id, topic_id.replace("-", " ").title())
            passage_counts[topic_id] += 1
            source_id = chunk.get("source_id") or ""
            creator = chunk.get("creator_handle") or chunk.get("handle") or ""
            if source_id:
                source_ids[topic_id].add(source_id)
            if creator:
                creator_counts[topic_id][creator] += 1

    records: list[dict] = []
    for topic_id in sorted(topic_labels):
        public_count = public_insight_counts[topic_id]
        creator_counter = public_creator_counts[topic_id] if public_count else creator_counts[topic_id]
        records.append(
            {
                "id": f"topic:{topic_id}",
                "topic_id": topic_id,
                "topic": topic_labels[topic_id],
                "definition": f"Source-backed creator statements and evidence excerpts related to {topic_labels[topic_id]}.",
                "source_count": len(source_ids[topic_id]),
                "public_source_count": len(public_source_ids[topic_id]),
                "passage_count": passage_counts[topic_id],
                "insight_count": insight_counts[topic_id],
                "public_insight_count": public_count,
                "creator_count": len(creator_counts[topic_id]),
                "top_creators": [
                    {"handle": handle, "count": count}
                    for handle, count in creator_counter.most_common(8)
                ],
                "latest_published_at": latest_dates.get(topic_id, ""),
                "public": public_count > 0,
                "public_policy": "topic_index",
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Export public TikTok-only Base2026 dataset.")
    parser.add_argument(
        "--include-full-transcripts",
        action="store_true",
        default=False,
        help="Include full transcripts. Off by default; use only for private/gated/noindex review exports.",
    )
    parser.add_argument(
        "--auto-promote-insights",
        action="store_true",
        default=False,
        help="Mark high-confidence pending insight cards public when evidence matching passes.",
    )
    parser.add_argument("--insight-threshold", type=float, default=0.45)
    parser.add_argument(
        "--creator-profiles",
        type=Path,
        default=ROOT / "config" / "creator-profiles.json",
        help="Optional local metadata override keyed by creator_id or handle. Supports avatar_url and display_name.",
    )
    parser.add_argument(
        "--admission-ledger",
        type=Path,
        default=SOURCE_ADMISSION,
        help="Private one-row-per-source admission ledger. Unknown sources are held private when the ledger exists.",
    )
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    creator_profiles = read_optional_json(args.creator_profiles)
    admission_active = args.admission_ledger.exists()
    admissions = load_source_admission(args.admission_ledger)

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        documents: list[dict] = []
        source_records: list[dict] = []
        chunks: list[dict] = []
        passages: list[dict] = []
        insight_cards: list[dict] = []
        creators: dict[str, dict] = {}
        emitted_source_ids: set[str] = set()
        admission_counts: Counter[str] = Counter()

        item_rows = con.execute(
            """
            SELECT
              i.item_id,
              i.platform_item_id AS video_id,
              i.source_type,
              i.canonical_url,
              i.title,
              i.author,
              i.published_at,
              i.captured_at,
              i.metadata_json,
              cr.handle,
              cr.url AS creator_url,
              cr.niche,
              cr.language,
              te.title_source,
              te.status AS title_status
            FROM generic_items i
            LEFT JOIN creators cr ON cr.creator_id = i.author
            LEFT JOIN item_title_enrichment te ON te.item_id = i.item_id
            WHERE i.source_type = 'tiktok_video'
              AND i.status != 'out_of_scope_old'
            ORDER BY COALESCE(i.published_at, '') DESC, i.item_id
            """
        ).fetchall()

        for item in item_rows:
            item_id = item["item_id"]
            video_id = item["video_id"]
            creator_id = item["author"] or ""
            handle = item["handle"] or creator_id
            source_handle = handle.lstrip("@")
            source_id = f"tiktok:{source_handle}:{video_id}" if video_id else item_id
            doc_row = con.execute(
                """
                SELECT document_id, document_type, clean_path, language
                FROM generic_documents
                WHERE item_id = ?
                ORDER BY CASE document_type WHEN 'transcript_polished' THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (item_id,),
            ).fetchone()
            transcript = read_kb_text(doc_row["clean_path"] if doc_row else "")
            claim_rows = [
                dict(row)
                for row in con.execute(
                    """
                    SELECT c.claim_id, c.topic, c.claim_text, c.claim_type, c.suggested_action, c.review_status, e.quote_or_span
                    FROM claim_evidence e
                    JOIN claims c ON c.claim_id = e.claim_id
                    WHERE e.video_id = ?
                    ORDER BY c.claim_id
                    """,
                    (video_id,),
                )
            ]
            topic_pairs = sorted(
                {
                    (slugify(claim.get("topic") or ""), claim.get("topic") or "")
                    for claim in claim_rows
                    if claim.get("topic")
                }
            )
            topic_ids = [topic_id for topic_id, _label in topic_pairs if topic_id]
            topic_labels = [label for _topic_id, label in topic_pairs if label]
            profile = creator_profile(creator_profiles, creator_id, handle)
            avatar_url = profile.get("avatar_url") or profile.get("profile_image_url") or ""
            display_name = profile.get("display_name") or profile.get("name") or ""
            base = {
                "item_id": item_id,
                "source_id": source_id,
                "video_id": video_id,
                "post_id": video_id,
                "platform": "tiktok",
                "source_type": item["source_type"],
                "source_url": item["canonical_url"],
                "title": item["title"],
                "title_source": item["title_source"],
                "title_status": item["title_status"],
                "creator_id": creator_id,
                "creator_handle": handle,
                "handle": handle,
                "creator_url": item["creator_url"],
                "avatar_url": avatar_url,
                "creator_display_name": display_name,
                "published_at": item["published_at"],
                "published_date": (item["published_at"] or "")[:10],
                "year": (item["published_at"] or "")[:4],
                "captured_at": item["captured_at"],
                "topics": topic_ids,
                "topic_labels": topic_labels,
                "public_policy": "full_transcript" if args.include_full_transcripts else "excerpt_only",
                "full_transcript_public": bool(args.include_full_transcripts),
            }
            item_chunks = con.execute(
                """
                SELECT chunk_id, chunk_index, text
                FROM chunks
                WHERE item_id = ?
                ORDER BY chunk_index
                """,
                (item_id,),
            ).fetchall()
            if not transcript.strip() and not item_chunks:
                continue
            emitted_source_ids.add(source_id)
            admission_state = source_admission_state(source_id, admissions, ledger_active=admission_active)
            admission_counts[admission_state] += 1
            if admission_state in {FUTURE_PRIVATE_BACKLOG, PRIVATE_HOLD_UNCLASSIFIED}:
                continue
            is_normal_public_card = admission_state == NORMAL_PUBLIC_CARD
            public_surface = "main_search" if is_normal_public_card else "provenance_archive"
            base["admission_state"] = admission_state
            base["public_surface"] = public_surface
            creators[creator_id] = {
                "creator_id": creator_id,
                "handle": item["handle"],
                "url": item["creator_url"],
                "niche": item["niche"],
                "language": item["language"],
                "avatar_url": avatar_url,
                "display_name": display_name,
            }
            public_source_text = normalize_public_source_text(transcript, item_chunks)
            summary_short = source_summary_short(
                item["title"] or "",
                item["title_status"] or "",
                topic_labels,
                public_source_text,
                claim_rows,
            )
            summary_long = source_summary_long(summary_short, topic_labels, public_source_text, claim_rows)
            source_record = {
                **base,
                "transcript_type": doc_row["document_type"] if doc_row else "",
                "language": doc_row["language"] if doc_row else "en",
                "transcript": transcript if args.include_full_transcripts else "",
                "public_source_text": public_source_text,
                "public_source_text_available": bool(public_source_text),
                "source_summary_short": summary_short,
                "source_summary_long": summary_long,
                "excerpt": public_excerpt_text(public_source_text, item_chunks),
            }
            source_records.append(source_record)
            if is_normal_public_card:
                documents.append(source_record)
            for chunk in item_chunks:
                passage = {
                    **base,
                    "id": chunk["chunk_id"],
                    "chunk_id": chunk["chunk_id"],
                    "chunk_index": chunk["chunk_index"],
                    "body": chunk["text"],
                    "topics": topic_ids,
                    "topic_labels": topic_labels,
                    "public_policy": "search_passage" if is_normal_public_card else "archive_passage",
                }
                passages.append(passage)
                if is_normal_public_card:
                    chunks.append(passage)
            if not is_normal_public_card:
                continue
            for claim in claim_rows:
                review_status = claim["review_status"] or "pending"
                claim_type = claim["claim_type"] or "claim"
                if claim_type == "insight_card_candidate" and review_status not in {"approved", "reviewed", "public"}:
                    continue
                reviewed_evidence = compact_text(claim.get("quote_or_span") or "", 900)
                if reviewed_evidence and evidence_is_in_chunks(reviewed_evidence, item_chunks):
                    evidence_excerpt, evidence_score = reviewed_evidence, 1.0
                else:
                    evidence_excerpt, evidence_score = best_evidence_excerpt(claim["claim_text"], item_chunks)
                is_reviewed_public = review_status in {"approved", "reviewed", "public"} and evidence_score >= 0.25
                is_auto_public = (
                    args.auto_promote_insights
                    and claim_type != "insight_card_candidate"
                    and evidence_score >= args.insight_threshold
                    and bool(evidence_excerpt)
                )
                is_public = is_reviewed_public or is_auto_public
                insight_cards.append(
                    {
                        "id": f"insight:{claim['claim_id']}",
                        "claim_id": claim["claim_id"],
                        "item_id": item_id,
                        "topic_id": slugify(claim["topic"]),
                        "topic": claim["topic"],
                        "source_id": source_id,
                        "post_id": video_id,
                        "source_url": item["canonical_url"],
                        "platform": "tiktok",
                        "creator_handle": handle,
                        "published_at": item["published_at"],
                        "claim_text": claim["claim_text"],
                        "suggested_action": claim["suggested_action"],
                        "claim_type": claim_type,
                        "evidence_excerpt": evidence_excerpt,
                        "evidence_score": evidence_score,
                        "stance": "asserts",
                        "confidence": evidence_score,
                        "review_status": review_status,
                        "promotion_method": "auto_evidence_match" if is_auto_public and not is_reviewed_public else review_status,
                        "public": is_public,
                        "needs_review": not is_public,
                        "public_policy": "reviewed_insight" if is_public else "needs_review",
                    }
                )

        if admission_active:
            unclassified_source_ids = sorted(emitted_source_ids - set(admissions))
            stale_admission_ids = sorted(set(admissions) - emitted_source_ids)
            if unclassified_source_ids or stale_admission_ids:
                raise ValueError(
                    "source admission ledger mismatch: "
                    f"unclassified={len(unclassified_source_ids)} stale={len(stale_admission_ids)} "
                    f"unclassified_sample={unclassified_source_ids[:5]} stale_sample={stale_admission_ids[:5]}"
                )

        out = args.out
        out.mkdir(parents=True, exist_ok=True)
        topics = build_topic_records(insight_cards, chunks)
        write_jsonl(out / "documents.jsonl", documents)
        write_jsonl(out / "chunks.jsonl", chunks)
        write_jsonl(out / "source_records.jsonl", source_records)
        write_jsonl(out / "passages.jsonl", passages)
        write_jsonl(out / "insight_cards.jsonl", insight_cards)
        write_jsonl(out / "topics.jsonl", topics)
        write_jsonl(out / "creators.jsonl", sorted(creators.values(), key=lambda x: x.get("handle") or ""))
        manifest = {
            "schema": PUBLIC_DATASET_MANIFEST_SCHEMA,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "dataset": "base2026-public-tiktok",
            "scope": "public TikTok-only export",
            "documents": len(documents),
            "source_records": len(source_records),
            "chunks": len(chunks),
            "passages": len(passages),
            "creators": len(creators),
            "topics": len(topics),
            "insight_cards": len(insight_cards),
            "public_insight_cards": sum(1 for row in insight_cards if row["public"]),
            "source_admission_active": admission_active,
            "source_admission_counts": dict(sorted(admission_counts.items())),
            "include_full_transcripts": bool(args.include_full_transcripts),
            "auto_promote_insights": bool(args.auto_promote_insights),
            "insight_threshold": args.insight_threshold,
            "public_policy": "full_transcript" if args.include_full_transcripts else "excerpt_only",
            "files": [
                "documents.jsonl",
                "chunks.jsonl",
                "source_records.jsonl",
                "passages.jsonl",
                "insight_cards.jsonl",
                "topics.jsonl",
                "creators.jsonl",
            ],
        }
        (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print(
            f"documents={len(documents)} source_records={len(source_records)} "
            f"chunks={len(chunks)} passages={len(passages)} creators={len(creators)} "
            f"topics={len(topics)} admission={dict(sorted(admission_counts.items()))} out={out}"
        )
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
