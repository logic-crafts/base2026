"""Fail-closed contract for Base2026 dataset manifests that can become public."""

from __future__ import annotations

import re
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
