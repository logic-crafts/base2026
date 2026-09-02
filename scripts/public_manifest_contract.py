"""Fail-closed contract for Base2026 dataset manifests that can become public."""

from __future__ import annotations

import re
import hashlib
import json
from typing import Any


PUBLIC_DATASET_MANIFEST_SCHEMA = "base2026.public-dataset-manifest/v1"
PUBLIC_DATASET_FILES = {
    "documents.jsonl",
    "chunks.jsonl",
    "source_records.jsonl",
    "passages.jsonl",
    "insight_cards.jsonl",
    "topics.jsonl",
    "creators.jsonl",
}
CLOUDFLARE_PUBLIC_DATASET_FILES = {
    "documents.jsonl",
    "insight_cards.jsonl",
    "passages.jsonl",
    "topic_signal_briefs.jsonl",
}
PUBLIC_DATASET_MANIFEST_KEYS = {
    "schema",
    "created_at",
    "dataset",
    "scope",
    "documents",
    "source_records",
    "chunks",
    "passages",
    "creators",
    "topics",
    "insight_cards",
    "public_insight_cards",
    "source_admission_active",
    "source_admission_counts",
    "include_full_transcripts",
    "auto_promote_insights",
    "insight_threshold",
    "public_policy",
    "files",
}
PUBLIC_DATASET_COUNT_KEYS = {
    "documents",
    "source_records",
    "chunks",
    "passages",
    "creators",
    "topics",
    "insight_cards",
    "public_insight_cards",
}
PUBLIC_ADMISSION_COUNT_KEYS = {
    "normal_public_card",
    "provenance_archive_noindex",
    "future_private_backlog",
}

CLAIM_RECEIPT_STATIC_MANIFEST_SCHEMA = "base2026.claim-receipt-static-manifest.v1"
CLAIM_RECEIPT_JSONL_FILENAME = "claim_receipts.jsonl"
CLAIM_RECEIPT_MANIFEST_FILENAME = "claim_receipts_manifest.json"
CLAIM_RECEIPT_CANARY_ID = "base2026.internal-linking.canary.v1"
CLAIM_RECEIPT_TOPIC = "internal-linking"
CLAIM_RECEIPT_POLICY_VERSION = "base2026.claim-receipt-admission.v1"
CLAIM_RECEIPT_COUNT = 10
CLAIM_RECEIPT_HASH_RE = re.compile(r"^[a-f0-9]{64}$")
CLAIM_RECEIPT_ROW_KEYS = {
    "schema_version",
    "receipt_id",
    "canary_id",
    "selection_rank",
    "source_id",
    "projection_id",
    "card_id",
    "search_id",
    "card_ordinal",
    "creator_handle",
    "creator_display_name",
    "creator_url",
    "original_url",
    "video_id",
    "base2026_url",
    "published_at",
    "published_date",
    "claim_text",
    "suggested_action",
    "topic_label",
    "evidence_excerpt",
    "evidence_start_seconds",
    "evidence_end_seconds",
    "public_projection_receipt_sha256",
    "policy_version",
}

_PRIVATE_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("absolute_posix_path", re.compile(r"(?:^|[\s\"'=(]|:(?!//))/(?!/)[A-Za-z0-9._~-]", re.I)),
    ("windows_absolute_path", re.compile(r"(?:^|[\s\"'=(]|:(?!//))[A-Za-z]:[\\/]")),
    ("unc_or_network_path", re.compile(r"(?:^|[\s\"'=(]|:(?!//))(?:\\{2,}|//)[^\\/]")),
    ("file_uri", re.compile(r"file://", re.I)),
    ("private_hermes_path", re.compile(r"(?:^|[\\/])\.hermes(?:[\\/]|$)", re.I)),
    ("private_worktree_path", re.compile(r"(?:^|[\\/])worktrees?(?:[\\/]|$)", re.I)),
    ("private_release_path", re.compile(r"(?:^|[\\/])output[\\/]releases?(?:[\\/]|$)", re.I)),
    ("private_knowledge_path", re.compile(r"(?:^|[\\/])12_knowledge-base(?:[\\/]|$)", re.I)),
    ("private_admission_ledger", re.compile(r"source-admission(?:\.[A-Za-z0-9_-]+)?\.jsonl", re.I)),
    ("private_database_path", re.compile(r"(?:^|[\\/])[^\\/]+\.(?:sqlite3?|db)(?:$|[?#])", re.I)),
)


def _pointer_token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _pointer(parent: str, value: object) -> str:
    token = _pointer_token(value)
    return f"{parent}/{token}" if parent else f"/{token}"


def _issue(pointer: str, reason: str) -> dict[str, str]:
    return {"pointer": pointer or "/", "reason": reason}


def private_value_issues(value: Any, pointer: str = "") -> list[dict[str, str]]:
    """Return pointer-only issues, never a rejected private value."""
    issues: list[dict[str, str]] = []
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            key_reasons = [
                reason
                for reason, pattern in _PRIVATE_VALUE_PATTERNS
                if isinstance(key, str) and pattern.search(key)
            ]
            child_pointer = (
                _pointer(pointer, f"_redacted_key_{index}")
                if key_reasons
                else _pointer(pointer, key)
            )
            issues.extend(_issue(child_pointer, f"{reason}_in_key") for reason in key_reasons)
            issues.extend(private_value_issues(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(private_value_issues(child, _pointer(pointer, index)))
    elif isinstance(value, str):
        issues.extend(
            _issue(pointer, reason)
            for reason, pattern in _PRIVATE_VALUE_PATTERNS
            if pattern.search(value)
        )
    return issues


def _nonnegative_integer_issues(payload: dict[str, Any], keys: set[str], pointer: str = "") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            issues.append(_issue(_pointer(pointer, key), "must_be_nonnegative_integer"))
    return issues


def validate_public_dataset_manifest(
    payload: Any,
    *,
    allowed_files: set[str] | frozenset[str] | None = None,
) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [_issue("/", "manifest_must_be_object")]

    issues = private_value_issues(payload)
    for index, _key in enumerate(sorted(set(payload) - PUBLIC_DATASET_MANIFEST_KEYS, key=str)):
        issues.append(_issue(f"/_undeclared_key_{index}", "undeclared_key"))
    for key in sorted(PUBLIC_DATASET_MANIFEST_KEYS - set(payload)):
        issues.append(_issue(_pointer("", key), "required_key_missing"))

    if payload.get("schema") != PUBLIC_DATASET_MANIFEST_SCHEMA:
        issues.append(_issue("/schema", "unsupported_schema"))
    if payload.get("dataset") != "base2026-public-tiktok":
        issues.append(_issue("/dataset", "unexpected_dataset"))
    if payload.get("scope") != "public TikTok-only export":
        issues.append(_issue("/scope", "unexpected_scope"))
    if not isinstance(payload.get("created_at"), str) or not payload.get("created_at"):
        issues.append(_issue("/created_at", "must_be_nonempty_string"))
    issues.extend(_nonnegative_integer_issues(payload, PUBLIC_DATASET_COUNT_KEYS))

    admissions = payload.get("source_admission_counts")
    if not isinstance(admissions, dict):
        issues.append(_issue("/source_admission_counts", "must_be_object"))
    else:
        if set(admissions) != PUBLIC_ADMISSION_COUNT_KEYS:
            issues.append(_issue("/source_admission_counts", "admission_key_allowlist_mismatch"))
        issues.extend(_nonnegative_integer_issues(admissions, PUBLIC_ADMISSION_COUNT_KEYS, "/source_admission_counts"))
        if all(isinstance(admissions.get(key), int) for key in PUBLIC_ADMISSION_COUNT_KEYS):
            normal = admissions.get("normal_public_card", 0)
            archive = admissions.get("provenance_archive_noindex", 0)
            if payload.get("documents") != normal:
                issues.append(_issue("/documents", "normal_admission_count_mismatch"))
            if payload.get("source_records") != normal + archive:
                issues.append(_issue("/source_records", "public_source_admission_count_mismatch"))

    if payload.get("source_admission_active") is not True:
        issues.append(_issue("/source_admission_active", "public_admission_must_be_active"))
    if payload.get("include_full_transcripts") is not False:
        issues.append(_issue("/include_full_transcripts", "full_transcripts_forbidden"))
    if payload.get("auto_promote_insights") is not False:
        issues.append(_issue("/auto_promote_insights", "auto_promotion_forbidden"))
    if payload.get("public_policy") != "excerpt_only":
        issues.append(_issue("/public_policy", "unexpected_public_policy"))
    threshold = payload.get("insight_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
        issues.append(_issue("/insight_threshold", "must_be_nonnegative_number"))
    files = payload.get("files")
    expected_files = PUBLIC_DATASET_FILES if allowed_files is None else set(allowed_files)
    if not isinstance(files, list) or any(not isinstance(item, str) for item in files):
        issues.append(_issue("/files", "must_be_string_array"))
    elif len(files) != len(set(files)) or set(files) != expected_files:
        issues.append(_issue("/files", "public_file_allowlist_mismatch"))
    return issues


def _claim_receipt_canonical_json(value: Any) -> str:
    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: normalize(item[key]) for key in sorted(item)}
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, float) and item.is_integer():
            return int(item)
        return item

    return json.dumps(
        normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _claim_receipt_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_claim_receipt_sidecars(
    jsonl_payload: Any,
    manifest: Any,
) -> list[dict[str, str]]:
    """Validate the optional public claim-receipt sidecar pair.

    The pair is intentionally separate from the four-file dataset manifest.
    A caller must provide both payloads; this validator performs the same
    canonical row and ledger digest checks used by the deterministic exporter.
    """

    issues: list[dict[str, str]] = []

    def issue(pointer: str, reason: str) -> None:
        issues.append({"pointer": pointer, "reason": reason})

    if not isinstance(manifest, dict):
        issue("/", "claim_receipt_manifest_must_be_object")
        return issues
    expected_manifest_keys = {
        "schema",
        "canary_id",
        "topic",
        "policy_version",
        "count",
        "ledger_sha256",
        "jsonl",
        "jsonl_sha256",
        "generated_from",
    }
    for key in sorted(set(manifest) - expected_manifest_keys):
        issue(f"/{key}", "undeclared_key")
    for key in sorted(expected_manifest_keys - set(manifest)):
        issue(f"/{key}", "required_key_missing")
    if manifest.get("schema") != CLAIM_RECEIPT_STATIC_MANIFEST_SCHEMA:
        issue("/schema", "unsupported_schema")
    if manifest.get("canary_id") != CLAIM_RECEIPT_CANARY_ID:
        issue("/canary_id", "unexpected_canary")
    if manifest.get("topic") != CLAIM_RECEIPT_TOPIC:
        issue("/topic", "unexpected_topic")
    if manifest.get("policy_version") != CLAIM_RECEIPT_POLICY_VERSION:
        issue("/policy_version", "unexpected_policy")
    if manifest.get("count") != CLAIM_RECEIPT_COUNT:
        issue("/count", "must_equal_ten")
    if manifest.get("jsonl") != CLAIM_RECEIPT_JSONL_FILENAME:
        issue("/jsonl", "unexpected_jsonl_filename")
    if manifest.get("generated_from") != "validated-public-d1-readback":
        issue("/generated_from", "unexpected_export_provenance")
    for key in ("ledger_sha256", "jsonl_sha256"):
        value = manifest.get(key)
        if not isinstance(value, str) or not CLAIM_RECEIPT_HASH_RE.fullmatch(value):
            issue(f"/{key}", "must_be_lowercase_sha256")
    issues.extend(private_value_issues(manifest))

    if not isinstance(jsonl_payload, str):
        issue("/jsonl", "jsonl_payload_must_be_text")
        return issues
    if not jsonl_payload or not jsonl_payload.endswith("\n"):
        issue("/jsonl", "jsonl_must_end_with_newline")
    raw_lines = jsonl_payload.splitlines()
    if len(raw_lines) != CLAIM_RECEIPT_COUNT:
        issue("/jsonl", "row_count_must_equal_ten")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw_lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            issue(f"/jsonl/{line_number}", "invalid_json")
            continue
        if not isinstance(row, dict):
            issue(f"/jsonl/{line_number}", "row_must_be_object")
            continue
        if set(row) != CLAIM_RECEIPT_ROW_KEYS:
            issue(f"/jsonl/{line_number}", "row_allowlist_mismatch")
            continue
        if row.get("schema_version") != "base2026.claim-receipt.v1":
            issue(f"/jsonl/{line_number}/schema_version", "unsupported_schema")
        if row.get("canary_id") != CLAIM_RECEIPT_CANARY_ID:
            issue(f"/jsonl/{line_number}/canary_id", "unexpected_canary")
        if row.get("policy_version") != CLAIM_RECEIPT_POLICY_VERSION:
            issue(f"/jsonl/{line_number}/policy_version", "unexpected_policy")
        receipt_id = row.get("receipt_id")
        if not isinstance(receipt_id, str) or not CLAIM_RECEIPT_HASH_RE.fullmatch(receipt_id):
            issue(f"/jsonl/{line_number}/receipt_id", "must_be_lowercase_sha256")
        else:
            immutable = dict(row)
            immutable.pop("receipt_id", None)
            if receipt_id != _claim_receipt_sha256(_claim_receipt_canonical_json(immutable)):
                issue(f"/jsonl/{line_number}/receipt_id", "immutable_receipt_digest_mismatch")
        rank = row.get("selection_rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or not 1 <= rank <= CLAIM_RECEIPT_COUNT:
            issue(f"/jsonl/{line_number}/selection_rank", "invalid_selection_rank")
        projection_id = row.get("projection_id")
        card_id = row.get("card_id")
        search_id = row.get("search_id")
        for key, value in (("projection_id", projection_id), ("card_id", card_id), ("search_id", search_id)):
            if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{40}", value):
                issue(f"/jsonl/{line_number}/{key}", "invalid_public_identity")
        source_id = row.get("source_id")
        source_match = re.fullmatch(r"tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})", source_id) if isinstance(source_id, str) else None
        if source_match is None:
            issue(f"/jsonl/{line_number}/source_id", "invalid_source_identity")
        else:
            handle, video_id = source_match.groups()
            if row.get("video_id") != video_id or row.get("creator_handle") != f"@{handle}":
                issue(f"/jsonl/{line_number}", "source_creator_video_mismatch")
            if row.get("creator_url") != f"https://www.tiktok.com/@{handle}":
                issue(f"/jsonl/{line_number}/creator_url", "noncanonical_creator_url")
            if row.get("original_url") != f"https://www.tiktok.com/@{handle}/video/{video_id}":
                issue(f"/jsonl/{line_number}/original_url", "noncanonical_original_url")
            if row.get("base2026_url") != f"https://base2026.dev/sources/tiktok-video-{video_id}":
                issue(f"/jsonl/{line_number}/base2026_url", "noncanonical_base_url")
        topic = row.get("topic_label")
        normalized_topic = re.sub(r"[^\w]+", "-", topic.casefold(), flags=re.UNICODE).strip("-") if isinstance(topic, str) else ""
        if not re.fullmatch(r"internal-linking(?:-[a-z0-9]+)*", normalized_topic):
            issue(f"/jsonl/{line_number}/topic_label", "topic_outside_canary")
        for key, minimum, maximum in (
            ("claim_text", 20, 360),
            ("suggested_action", 20, 360),
            ("evidence_excerpt", 20, 520),
        ):
            value = row.get(key)
            if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
                issue(f"/jsonl/{line_number}/{key}", "invalid_public_text_length")
        rows.append(row)

    if len(rows) == CLAIM_RECEIPT_COUNT:
        ranks = [row.get("selection_rank") for row in rows]
        if ranks != list(range(1, CLAIM_RECEIPT_COUNT + 1)):
            issue("/jsonl", "selection_ranks_not_contiguous")
        source_ids = [
            row.get("source_id") if isinstance(row.get("source_id"), str) else repr(row.get("source_id"))
            for row in rows
        ]
        if len(set(source_ids)) != CLAIM_RECEIPT_COUNT:
            issue("/jsonl", "sources_not_unique")
        creator_counts: dict[Any, int] = {}
        for row in rows:
            creator_value = row.get("creator_handle")
            creator = creator_value if isinstance(creator_value, str) else repr(creator_value)
            creator_counts[creator] = creator_counts.get(creator, 0) + 1
        if any(count > 2 for count in creator_counts.values()):
            issue("/jsonl", "creator_limit_exceeded")
        try:
            ledger = _claim_receipt_sha256("".join(f"{_claim_receipt_canonical_json(row)}\n" for row in rows))
        except (TypeError, ValueError):
            ledger = ""
            issue("/jsonl", "noncanonical_json_value")
        if manifest.get("ledger_sha256") != ledger:
            issue("/ledger_sha256", "ledger_digest_mismatch")
    if manifest.get("jsonl_sha256") != _claim_receipt_sha256(jsonl_payload):
        issue("/jsonl_sha256", "jsonl_digest_mismatch")
    issues.extend(private_value_issues(rows))
    return issues
