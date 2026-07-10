from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "12_knowledge-base"
TIKTOK = KB / "sources" / "tiktok"
INDEXES = KB / "indexes"
DB_PATH = INDEXES / "kb.sqlite"
SCHEMA_PATH = INDEXES / "kb.v2.schema.sql"
CANON = KB / "canonical"
SOURCE_CARDS = TIKTOK / "source-cards"
CLAIM_CARDS = CANON / "claims"
TITLE_ENRICHMENT_CSV = TIKTOK / "metadata" / "titles.csv"
REVIEWED_CANDIDATES_JSONL = TIKTOK / "insight-candidates" / "reviewed-candidates.jsonl"
REVIEWED_LEGACY_INSIGHTS_JSONL = TIKTOK / "insight-candidates" / "reviewed-legacy-insights.jsonl"
LOCAL_SOURCE_PREFIXES = (
    "00_",
    "01_",
    "02_",
    "03_",
    "04_",
    "05_",
    "06_",
    "07_",
    "08_",
    "09_",
    "10_",
    "99_",
)
LOCAL_SOURCE_EXCLUDES = {"11_dreamwood_offer", "12_knowledge-base", "scripts"}
LOCAL_SOURCE_EXTS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(KB)).replace("\\", "/")


def rel_project(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean_pipe_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"


def tiktok_handle_from_creator_id(creator_id: str) -> str:
    safe = (creator_id or "").strip()
    if safe.startswith("tiktok-"):
        safe = safe[len("tiktok-") :]
    safe = safe.replace("-", "_")
    return f"@{safe}" if safe else ""


def title_is_truncated(title: str | None) -> bool:
    text = (title or "").strip()
    return text.endswith("...") or text.endswith("…")


def load_title_enrichment() -> dict[str, dict[str, str]]:
    rows = read_csv(TITLE_ENRICHMENT_CSV)
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        video_id = (row.get("video_id") or "").strip()
        if not video_id:
            continue
        output[video_id] = row
    return output


def best_platform_title(video: dict[str, str], enrichment: dict[str, str] | None) -> tuple[str, dict[str, str]]:
    original = (video.get("title_or_description") or "").replace("\n", " ").strip()
    if enrichment:
        enriched = (enrichment.get("source_title_full") or enrichment.get("source_title_raw") or "").replace("\n", " ").strip()
        if enriched and enrichment.get("status") == "ok":
            return enriched, {
                "title_source": enrichment.get("title_source") or "tiktok_oembed",
                "title_status": "ok",
                "source_title_raw": enrichment.get("source_title_raw") or enriched,
                "source_title_full": enriched,
                "source_payload_path": enrichment.get("source_payload_path") or "",
                "title_error": enrichment.get("error") or "",
            }
    return original, {
        "title_source": "inventory_title",
        "title_status": "truncated" if title_is_truncated(original) else "raw",
        "source_title_raw": original,
        "source_title_full": "",
        "source_payload_path": "",
        "title_error": enrichment.get("error") if enrichment else "",
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def chunk_text(text: str, size: int = 1800, overlap: int = 150) -> list[tuple[int, int, str]]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[tuple[int, int, str]] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        chunks.append((start, end, normalized[start:end]))
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def parse_claim_tables(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not path.exists():
        return rows

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("|"):
            continue
        cells = [clean_pipe_cell(c) for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        if cells[0].lower() in {"claim id", "claim_id", "---"}:
            continue
        if not (cells[0].startswith("tiktok-") or cells[0].startswith("batch-")):
            continue

        if "batch-" in path.name:
            claim_id, video_id, creator_id, topic, claim_text, action, evidence, review = cells[:8]
        else:
            claim_id, video_id, creator_id, topic, claim_text, action = cells[:6]
            evidence = cells[7] if len(cells) >= 9 and "transcripts/" in cells[7] else f"transcripts/clean/{video_id}.txt"
            review = cells[-1]

        review_status = review or "pending"
        if review_status not in {
            "pending",
            "keep",
            "test",
            "reject",
            "duplicate",
            "contradiction",
            "promoted",
            "needs_evidence",
            "supported",
            "contradicted",
            "outdated",
            "promoted_to_method",
        }:
            review_status = "pending"

        rows.append(
            {
                "claim_id": claim_id,
                "video_id": video_id,
                "creator_id": creator_id,
                "topic": topic,
                "claim_text": claim_text,
                "suggested_action": action,
                "evidence_path": evidence.strip("`"),
                "review_status": review_status,
                "source_file": rel(path),
            }
        )
    return rows


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_reviewed_candidate_claims(path: Path) -> list[dict[str, str]]:
    replay_statuses = {"approved", "reviewed", "public", "needs_human", "rejected", "reject_candidate"}
    rows: list[dict[str, str]] = []
    for row in read_jsonl(path):
        review_status = (row.get("review_status") or "").strip()
        if review_status not in replay_statuses:
            continue
        claim_id = (row.get("claim_id") or "").strip()
        claim_text = (row.get("claim_text") or row.get("text") or "").strip()
        video_id = str(row.get("video_id") or "").strip()
        if not claim_id or not claim_text or not video_id:
            continue
        source_id = (row.get("source_id") or "").strip()
        rows.append(
            {
                "claim_id": claim_id,
                "video_id": video_id,
                "topic": (row.get("topic") or row.get("topic_label") or "Uncategorized").strip(),
                "claim_text": claim_text,
                "claim_type": "insight_card_candidate",
                "suggested_action": (row.get("suggested_action") or "").strip(),
                "confidence": row.get("confidence") if row.get("confidence") is not None else row.get("evidence_score"),
                "review_status": review_status,
                "evidence_path": (row.get("evidence_path") or f"public-data/tiktok/passages.jsonl#source_id={source_id}").strip(),
                "quote_or_span": (row.get("evidence_excerpt") or "").strip(),
                "source_file": rel(path),
            }
        )
    return rows


def load_reviewed_legacy_insights(path: Path) -> list[dict[str, str]]:
    replay_statuses = {"approved", "reviewed", "public", "needs_human", "rejected", "reject_candidate", "needs_visual_context"}
    rows: list[dict[str, str]] = []
    for row in read_jsonl(path):
        review_status = (row.get("review_status") or "").strip()
        if review_status not in replay_statuses:
            continue
        claim_id = (row.get("claim_id") or "").strip()
        claim_text = (row.get("claim_text") or "").strip()
        source_id = (row.get("source_id") or "").strip()
        video_id = str(row.get("video_id") or row.get("post_id") or source_id.split(":")[-1]).strip()
        if not claim_id or not claim_text or not video_id:
            continue
        claim_type = (row.get("claim_type") or "").strip()
        if claim_type not in {"claim", "risk"}:
            claim_type = "claim"
        rows.append(
            {
                "claim_id": claim_id,
                "video_id": video_id,
                "topic": (row.get("topic") or row.get("topic_label") or "Uncategorized").strip(),
                "claim_text": claim_text,
                "claim_type": claim_type,
                "suggested_action": (row.get("suggested_action") or "").strip(),
                "confidence": row.get("confidence") if row.get("confidence") is not None else row.get("evidence_score"),
                "review_status": "approved" if review_status == "public" else review_status,
                "evidence_path": (row.get("evidence_path") or f"public-data/tiktok/passages.jsonl#source_id={source_id}").strip(),
                "quote_or_span": (row.get("evidence_excerpt") or "").strip(),
                "source_file": rel(path),
            }
        )
    return rows


def write_source_card(video: dict[str, str], transcript_path: Path | None) -> Path:
    SOURCE_CARDS.mkdir(parents=True, exist_ok=True)
    video_id = video.get("video_id", "")
    path = SOURCE_CARDS / f"{video_id}.md"
    title = (video.get("title_or_description") or "").replace("\n", " ").strip()
    frontmatter = [
        "---",
        f"source_card_id: source-card-{video_id}",
        f"video_id: {video_id}",
        f"creator_id: {video.get('creator_id', '')}",
        "platform: tiktok",
        f"url: {video.get('url', '')}",
        f"published_at: {video.get('published_at', '')}",
        f"collected_at: {video.get('collected_at', '')}",
        f"transcript_status: {video.get('transcript_status', '')}",
        f"caption_source: {video.get('caption_source', '')}",
        f"review_status: {video.get('review_status', '')}",
        "---",
        "",
        f"# TikTok Source {video_id}",
        "",
        f"- Creator: `{video.get('creator_id', '')}`",
        f"- URL: {video.get('url', '')}",
        f"- Published: `{video.get('published_at', '')}`",
        f"- Transcript: `{rel(transcript_path) if transcript_path else ''}`",
        "",
        "## Title / Description",
        "",
        title,
        "",
        "## Notes",
        "",
        video.get("notes", ""),
        "",
    ]
    path.write_text("\n".join(frontmatter), encoding="utf-8")
    return path


def write_claim_card(claim: dict[str, str]) -> Path:
    CLAIM_CARDS.mkdir(parents=True, exist_ok=True)
    path = CLAIM_CARDS / f"{claim['claim_id']}.md"
    body = [
        "---",
        f"claim_id: {claim['claim_id']}",
        f"video_id: {claim['video_id']}",
        f"creator_id: {claim['creator_id']}",
        f"topic: {claim['topic']}",
        f"review_status: {claim['review_status'] or 'pending'}",
        f"source_file: {claim['source_file']}",
        "---",
        "",
        f"# {claim['claim_id']}",
        "",
        "## Claim",
        "",
        claim["claim_text"],
        "",
        "## Suggested Action",
        "",
        claim["suggested_action"],
        "",
        "## Evidence",
        "",
        f"- Video: `{claim['video_id']}`",
        f"- Path: `{claim['evidence_path']}`",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def import_markdown_folder(
    conn: sqlite3.Connection,
    folder: Path,
    table: str,
    id_col: str,
    title_prefix: str,
) -> int:
    if not folder.exists():
        return 0
    count = 0
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
        item_id = stable_id(title_prefix, rel(path))
        now = datetime.now().isoformat(timespec="seconds")
        if table == "methods":
            conn.execute(
                """
                INSERT OR REPLACE INTO methods
                (method_id, title, method_text, status, risk_level, applicability, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item_id, title, text, "draft", None, None, now, now),
            )
            conn.execute(
                "INSERT INTO methods_fts (method_id, title, method_text, applicability) VALUES (?, ?, ?, ?)",
                (item_id, title, text, None),
            )
        elif table == "strategy_blocks":
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_blocks
                (strategy_block_id, title, use_case, body, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (item_id, title, None, text, "draft", now, now),
            )
        count += 1
    return count


def local_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relp = path.relative_to(ROOT)
        first = relp.parts[0] if relp.parts else ""
        if first.startswith(".") or first in LOCAL_SOURCE_EXCLUDES:
            continue
        if first == "README.md" or first == "manifest.json":
            pass
        elif not first.startswith(LOCAL_SOURCE_PREFIXES):
            continue
        if path.suffix.lower() not in LOCAL_SOURCE_EXTS:
            continue
        files.append(path)
    return sorted(files)


def extract_title(path: Path, text: str) -> str:
    if path.suffix.lower() == ".md":
        for line in text.splitlines():
            if line.startswith("# "):
                return line.lstrip("# ").strip() or path.stem
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.name


def import_local_sources(conn: sqlite3.Connection) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    count = 0
    for path in local_source_files():
        relp = rel_project(path)
        first = path.relative_to(ROOT).parts[0]
        source_id = f"source-local-{stable_id('folder', first)[7:]}"
        source_name = first if first not in {"README.md", "manifest.json"} else "project-root"
        conn.execute(
            """
            INSERT OR REPLACE INTO source_registry
            (source_id, source_type, source_name, url, input_value, scope, status, added_at, last_checked_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "local_folder",
                source_name,
                None,
                source_name,
                "project_files",
                "active",
                datetime.now().date().isoformat(),
                now,
                "Imported local SEO/GEO/AEO project files. Excludes 11_dreamwood_offer by project rule.",
            ),
        )

        text = path.read_text(encoding="utf-8", errors="ignore")
        title = extract_title(path, text)
        item_id = stable_id("local-file", relp)
        doc_id = stable_id("local-doc", relp)
        file_hash = sha256_file(path)
        conn.execute(
            """
            INSERT OR REPLACE INTO generic_items
            (item_id, source_id, source_type, platform_item_id, canonical_url, title, author,
             published_at, captured_at, status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                source_id,
                "local_file",
                relp,
                f"project://{relp}",
                title,
                None,
                None,
                now,
                "imported",
                json.dumps({"path": relp, "extension": path.suffix.lower()}, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO raw_artifacts
            (artifact_id, item_id, artifact_type, path, sha256, captured_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (stable_id("artifact-local", relp), item_id, "local_file", relp, file_hash, now),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO generic_documents
            (document_id, item_id, document_type, clean_path, language, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, item_id, path.suffix.lower().lstrip(".") or "text", relp, None, file_hash, now),
        )
        for idx, (start, end, chunk) in enumerate(chunk_text(text)):
            chunk_id = f"{stable_id('chunk-local', relp)}-{idx:04d}"
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks
                (chunk_id, document_id, item_id, chunk_index, text, start_offset, end_offset, timestamp_start, timestamp_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, doc_id, item_id, idx, chunk, start, end, None, None),
            )
            conn.execute(
                "INSERT INTO chunks_fts (chunk_id, item_id, body) VALUES (?, ?, ?)",
                (chunk_id, item_id, chunk),
            )
        conn.execute(
            """
            INSERT OR REPLACE INTO events
            (event_id, entity_type, entity_id, event_type, event_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                stable_id("event-local-ingested", relp),
                "generic_item",
                item_id,
                "local_file_ingested",
                json.dumps({"path": relp, "sha256": file_hash}, ensure_ascii=False),
                now,
            ),
        )
        count += 1
    return count


def main() -> None:
    INDEXES.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(schema)
    conn.execute("DELETE FROM transcripts_fts")
    conn.execute("DELETE FROM claims_fts")
    conn.execute("DELETE FROM methods_fts")
    conn.execute("DELETE FROM chunks_fts")
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM generic_documents")
    conn.execute("DELETE FROM raw_artifacts")
    conn.execute("DELETE FROM item_title_enrichment")
    conn.execute("DELETE FROM jobs")
    conn.execute("DELETE FROM events")
    conn.execute("DELETE FROM generic_items")
    conn.execute("DELETE FROM source_cards")
    conn.execute("DELETE FROM transcripts")
    conn.execute("DELETE FROM claim_reviews")
    conn.execute("DELETE FROM claim_topics")
    conn.execute("DELETE FROM claim_evidence")
    conn.execute("DELETE FROM method_evidence")
    conn.execute("DELETE FROM strategy_block_evidence")
    conn.execute("DELETE FROM contradictions")
    conn.execute("DELETE FROM methods")
    conn.execute("DELETE FROM strategy_blocks")
    conn.execute("DELETE FROM sop_blocks")
    conn.execute("DELETE FROM claims")
    conn.execute("DELETE FROM topics")
    conn.execute("DELETE FROM videos")
    conn.execute("DELETE FROM creators")
    conn.execute("DELETE FROM source_registry")

    creators = read_csv(TIKTOK / "creators.csv")
    videos = read_csv(TIKTOK / "videos.csv")
    known_creator_ids = {
        (row.get("creator_id") or "").strip()
        for row in creators
        if (row.get("creator_id") or "").strip()
    }
    missing_creator_ids = sorted(
        {
            (row.get("creator_id") or "").strip()
            for row in videos
            if (row.get("creator_id") or "").strip()
        }
        - known_creator_ids
    )
    for creator_id in missing_creator_ids:
        handle = tiktok_handle_from_creator_id(creator_id)
        creators.append(
            {
                "creator_id": creator_id,
                "platform": "tiktok",
                "handle": handle,
                "url": f"https://www.tiktok.com/{handle}" if handle else "",
                "niche": "",
                "language": "en",
                "priority": "normal",
                "status": "active",
                "added_at": datetime.now().date().isoformat(),
                "notes": "Auto-registered from TikTok videos.csv intake row.",
            }
        )
    for row in creators:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT OR REPLACE INTO creators
            (creator_id, platform, handle, url, niche, language, priority, status, added_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("creator_id"),
                row.get("platform"),
                row.get("handle"),
                row.get("url"),
                row.get("niche"),
                row.get("language"),
                row.get("priority"),
                row.get("status"),
                row.get("added_at") or datetime.now().date().isoformat(),
                row.get("notes"),
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO source_registry
            (source_id, source_type, source_name, url, input_value, scope, status, added_at, last_checked_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"source-tiktok-{row.get('creator_id')}",
                "tiktok_creator",
                row.get("handle") or row.get("creator_id"),
                row.get("url"),
                row.get("url"),
                "last_year",
                row.get("status") or "active",
                row.get("added_at") or datetime.now().date().isoformat(),
                now,
                row.get("notes"),
            ),
        )

    registered_tiktok_sources = {
        f"source-tiktok-{(row.get('creator_id') or '').strip()}"
        for row in creators
        if (row.get("creator_id") or "").strip()
    }
    for creator_id in sorted({(row.get("creator_id") or "").strip() for row in videos if (row.get("creator_id") or "").strip()}):
        source_id = f"source-tiktok-{creator_id}"
        if source_id in registered_tiktok_sources:
            continue
        now = datetime.now().isoformat(timespec="seconds")
        handle = tiktok_handle_from_creator_id(creator_id)
        profile_url = f"https://www.tiktok.com/{handle}" if handle else ""
        conn.execute(
            """
            INSERT OR REPLACE INTO source_registry
            (source_id, source_type, source_name, url, input_value, scope, status, added_at, last_checked_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "tiktok_creator",
                handle or creator_id,
                profile_url,
                profile_url,
                "last_year",
                "active",
                datetime.now().date().isoformat(),
                now,
                "Auto-registered from TikTok videos.csv intake row.",
            ),
        )
        registered_tiktok_sources.add(source_id)

    title_enrichment = load_title_enrichment()
    transcribed = 0
    for row in videos:
        conn.execute(
            """
            INSERT OR REPLACE INTO videos
            (video_id, creator_id, platform, url, published_at, collected_at, title_or_description,
             hashtags, duration_seconds, metrics_json, transcript_status, caption_source,
             evidence_path, review_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("video_id"),
                row.get("creator_id"),
                row.get("platform") or "tiktok",
                row.get("url"),
                row.get("published_at"),
                row.get("collected_at") or datetime.now().date().isoformat(),
                row.get("title_or_description"),
                row.get("hashtags"),
                int(row["duration_seconds"]) if row.get("duration_seconds", "").isdigit() else None,
                row.get("metrics_json"),
                row.get("transcript_status") or "queued",
                row.get("caption_source"),
                row.get("evidence_path"),
                row.get("review_status") or "new",
                row.get("notes"),
            ),
        )

        video_id = row.get("video_id", "")
        captured_at = row.get("collected_at") or datetime.now().date().isoformat()
        generic_item_id = f"tiktok-video-{video_id}"
        display_title, title_meta = best_platform_title(row, title_enrichment.get(video_id))
        metadata = {
            "creator_id": row.get("creator_id"),
            "hashtags": row.get("hashtags"),
            "duration_seconds": row.get("duration_seconds"),
            "metrics_json": row.get("metrics_json"),
            "caption_source": row.get("caption_source"),
            "review_status": row.get("review_status"),
            "title_source": title_meta["title_source"],
            "title_status": title_meta["title_status"],
            "source_title_raw": title_meta["source_title_raw"],
            "source_title_full": title_meta["source_title_full"],
        }
        conn.execute(
            """
            INSERT OR REPLACE INTO generic_items
            (item_id, source_id, source_type, platform_item_id, canonical_url, title, author,
             published_at, captured_at, status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generic_item_id,
                f"source-tiktok-{row.get('creator_id')}",
                "tiktok_video",
                video_id,
                row.get("url"),
                display_title,
                row.get("creator_id"),
                row.get("published_at"),
                captured_at,
                row.get("transcript_status") or "queued",
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            ),
        )
        enrichment_row = title_enrichment.get(video_id) or {}
        conn.execute(
            """
            INSERT OR REPLACE INTO item_title_enrichment
            (item_id, platform, platform_item_id, source_title_raw, source_title_full, title_source,
             status, source_payload_path, source_payload_json, enriched_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generic_item_id,
                row.get("platform") or "tiktok",
                video_id,
                title_meta["source_title_raw"],
                title_meta["source_title_full"],
                title_meta["title_source"],
                enrichment_row.get("status") or title_meta["title_status"],
                title_meta["source_payload_path"],
                enrichment_row.get("source_payload_json") or "",
                enrichment_row.get("enriched_at") or datetime.now().isoformat(timespec="seconds"),
                title_meta["title_error"],
            ),
        )
        clean_path = TIKTOK / "transcripts" / "clean" / f"{video_id}.txt"
        polished_path = TIKTOK / "transcripts" / "polished" / f"{video_id}.txt"
        polished_qa_path = TIKTOK / "transcripts" / "polished-qa" / f"{video_id}.json"
        transcript_status = row.get("transcript_status") or ""
        if clean_path.exists() and transcript_status == "transcribed":
            transcribed += 1
            transcript_id = f"transcript-{video_id}"
            conn.execute(
                """
                INSERT OR REPLACE INTO transcripts
                (transcript_id, video_id, source_type, raw_path, clean_path, language, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript_id,
                    video_id,
                    row.get("caption_source") or "unknown",
                    row.get("evidence_path"),
                    rel(clean_path),
                    "en",
                    None,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            text = clean_path.read_text(encoding="utf-8", errors="ignore")
            conn.execute(
                "INSERT INTO transcripts_fts (video_id, creator_id, title, body) VALUES (?, ?, ?, ?)",
                (video_id, row.get("creator_id"), display_title, text),
            )
            transcript_hash = sha256_file(clean_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO raw_artifacts
                (artifact_id, item_id, artifact_type, path, sha256, captured_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"artifact-transcript-{video_id}",
                    generic_item_id,
                    "tiktok_transcript_clean",
                    rel(clean_path),
                    transcript_hash,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            search_path = polished_path if polished_path.exists() else clean_path
            search_text = search_path.read_text(encoding="utf-8", errors="ignore")
            search_hash = sha256_file(search_path)
            search_doc_type = "transcript_polished" if polished_path.exists() else "transcript_clean"
            search_doc_id = f"doc-{search_doc_type}-{video_id}"
            conn.execute(
                """
                INSERT OR REPLACE INTO generic_documents
                (document_id, item_id, document_type, clean_path, language, sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    search_doc_id,
                    generic_item_id,
                    search_doc_type,
                    rel(search_path),
                    "en",
                    search_hash,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            if polished_path.exists():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO raw_artifacts
                    (artifact_id, item_id, artifact_type, path, sha256, captured_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"artifact-transcript-polished-{video_id}",
                        generic_item_id,
                        "tiktok_transcript_polished",
                        rel(polished_path),
                        search_hash,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
            if polished_qa_path.exists():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO raw_artifacts
                    (artifact_id, item_id, artifact_type, path, sha256, captured_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"artifact-transcript-polished-qa-{video_id}",
                        generic_item_id,
                        "tiktok_transcript_polished_qa",
                        rel(polished_qa_path),
                        sha256_file(polished_qa_path),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
            for idx, (start, end, chunk) in enumerate(chunk_text(search_text)):
                chunk_prefix = "chunk-transcript-polished" if polished_path.exists() else "chunk-transcript"
                chunk_id = f"{chunk_prefix}-{video_id}-{idx:04d}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunks
                    (chunk_id, document_id, item_id, chunk_index, text, start_offset, end_offset, timestamp_start, timestamp_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, search_doc_id, generic_item_id, idx, chunk, start, end, None, None),
                )
                conn.execute(
                    """
                    INSERT INTO chunks_fts (chunk_id, item_id, body)
                    VALUES (?, ?, ?)
                    """,
                    (chunk_id, generic_item_id, chunk),
                )
            source_card_video = dict(row)
            source_card_video["title_or_description"] = display_title
            card_path = write_source_card(source_card_video, clean_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO raw_artifacts
                (artifact_id, item_id, artifact_type, path, sha256, captured_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"artifact-source-card-{video_id}",
                    generic_item_id,
                    "source_card",
                    rel(card_path),
                    sha256_file(card_path),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO source_cards
                (source_card_id, video_id, path, summary, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"source-card-{video_id}",
                    video_id,
                    rel(card_path),
                    display_title,
                    "draft",
                    datetime.now().isoformat(timespec="seconds"),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        elif (row.get("transcript_status") or "") not in {"out_of_scope_old", "needs_source_review"}:
            job_id = f"job-asr-{video_id}"
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs
                (job_id, task_type, item_type, item_id, status, priority, lease_until, attempt_count,
                 last_error, input_hash, output_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    "asr_transcript",
                    "generic_item",
                    generic_item_id,
                    "queued",
                    50,
                    None,
                    0,
                    None,
                    stable_id("input", row.get("url") or video_id),
                    None,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO events
                (event_id, entity_type, entity_id, event_type, event_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"event-needs-asr-{video_id}",
                    "generic_item",
                    generic_item_id,
                    "needs_asr",
                    json.dumps({"url": row.get("url"), "creator_id": row.get("creator_id")}, ensure_ascii=False),
                    now,
                ),
            )

    claim_rows: list[dict[str, str]] = []
    for path in sorted((TIKTOK / "extracted-claims").glob("*.md")):
        claim_rows.extend(parse_claim_tables(path))
    reviewed_legacy_rows = load_reviewed_legacy_insights(REVIEWED_LEGACY_INSIGHTS_JSONL)
    reviewed_candidate_rows = load_reviewed_candidate_claims(REVIEWED_CANDIDATES_JSONL)

    for claim in claim_rows:
        created = datetime.now().isoformat(timespec="seconds")
        claim_type = "risk" if re.search(r"risk|avoid|spam|манип", claim["topic"], re.I) else "claim"
        conn.execute(
            """
            INSERT OR REPLACE INTO claims
            (claim_id, claim_text, topic, claim_type, suggested_action, confidence, review_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim["claim_id"],
                claim["claim_text"],
                claim["topic"],
                claim_type,
                claim["suggested_action"],
                None,
                claim["review_status"] or "pending",
                created,
                created,
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO claim_evidence
            (claim_id, video_id, evidence_path, quote_or_span)
            VALUES (?, ?, ?, ?)
            """,
            (claim["claim_id"], claim["video_id"], claim["evidence_path"], None),
        )
        conn.execute(
            "INSERT INTO claims_fts (claim_id, topic, claim_text, suggested_action) VALUES (?, ?, ?, ?)",
            (claim["claim_id"], claim["topic"], claim["claim_text"], claim["suggested_action"]),
        )
        write_claim_card(claim)

    for claim in reviewed_legacy_rows:
        created = datetime.now().isoformat(timespec="seconds")
        try:
            confidence = float(claim["confidence"]) if claim.get("confidence") not in {"", None} else None
        except (TypeError, ValueError):
            confidence = None
        conn.execute("DELETE FROM claims_fts WHERE claim_id = ?", (claim["claim_id"],))
        conn.execute("DELETE FROM claim_evidence WHERE claim_id = ?", (claim["claim_id"],))
        conn.execute(
            """
            INSERT OR REPLACE INTO claims
            (claim_id, claim_text, topic, claim_type, suggested_action, confidence, review_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim["claim_id"],
                claim["claim_text"],
                claim["topic"],
                claim["claim_type"],
                claim["suggested_action"],
                confidence,
                claim["review_status"],
                created,
                created,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO claim_evidence
            (claim_id, video_id, evidence_path, quote_or_span)
            VALUES (?, ?, ?, ?)
            """,
            (claim["claim_id"], claim["video_id"], claim["evidence_path"], claim.get("quote_or_span") or None),
        )
        conn.execute(
            "INSERT INTO claims_fts (claim_id, topic, claim_text, suggested_action) VALUES (?, ?, ?, ?)",
            (claim["claim_id"], claim["topic"], claim["claim_text"], claim["suggested_action"]),
        )

    for claim in reviewed_candidate_rows:
        created = datetime.now().isoformat(timespec="seconds")
        try:
            confidence = float(claim["confidence"]) if claim.get("confidence") not in {"", None} else None
        except (TypeError, ValueError):
            confidence = None
        conn.execute(
            """
            INSERT OR REPLACE INTO claims
            (claim_id, claim_text, topic, claim_type, suggested_action, confidence, review_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim["claim_id"],
                claim["claim_text"],
                claim["topic"],
                claim["claim_type"],
                claim["suggested_action"],
                confidence,
                claim["review_status"],
                created,
                created,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO claim_evidence
            (claim_id, video_id, evidence_path, quote_or_span)
            VALUES (?, ?, ?, ?)
            """,
            (claim["claim_id"], claim["video_id"], claim["evidence_path"], claim.get("quote_or_span") or None),
        )
        conn.execute(
            "INSERT INTO claims_fts (claim_id, topic, claim_text, suggested_action) VALUES (?, ?, ?, ?)",
            (claim["claim_id"], claim["topic"], claim["claim_text"], claim["suggested_action"]),
        )

    methods_imported = import_markdown_folder(conn, CANON / "methods", "methods", "method_id", "method")
    strategy_imported = import_markdown_folder(conn, CANON / "strategy-blocks", "strategy_blocks", "strategy_block_id", "strategy")
    local_files_imported = import_local_sources(conn)

    conn.commit()

    stats = {
        "db": str(DB_PATH),
        "creators": conn.execute("SELECT COUNT(*) FROM creators").fetchone()[0],
        "videos": conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0],
        "transcripts": conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0],
        "source_cards": conn.execute("SELECT COUNT(*) FROM source_cards").fetchone()[0],
        "claims": conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0],
        "claim_cards": len(list(CLAIM_CARDS.glob("*.md"))),
        "reviewed_legacy_insight_claims": len(reviewed_legacy_rows),
        "reviewed_candidate_claims": len(reviewed_candidate_rows),
        "methods": conn.execute("SELECT COUNT(*) FROM methods").fetchone()[0],
        "strategy_blocks": conn.execute("SELECT COUNT(*) FROM strategy_blocks").fetchone()[0],
        "source_registry": conn.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0],
        "generic_items": conn.execute("SELECT COUNT(*) FROM generic_items").fetchone()[0],
        "generic_documents": conn.execute("SELECT COUNT(*) FROM generic_documents").fetchone()[0],
        "chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "queued_asr_jobs": conn.execute("SELECT COUNT(*) FROM jobs WHERE task_type='asr_transcript' AND status='queued'").fetchone()[0],
        "local_files_imported": local_files_imported,
        "transcribed_files_seen": transcribed,
        "methods_imported": methods_imported,
        "strategy_imported": strategy_imported,
    }
    conn.close()
    for key, value in stats.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
