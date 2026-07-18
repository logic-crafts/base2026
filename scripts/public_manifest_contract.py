"""Structural contracts for Base2026 manifests that can reach public artifacts.

Validation issues deliberately contain only a JSON pointer and a stable reason
code.  They never echo the rejected value, because the value itself may contain
private filesystem information.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PUBLIC_DATASET_MANIFEST_SCHEMA = "base2026.public-dataset-manifest/v1"
PUBLIC_PAGE_MANIFEST_SCHEMA = "base2026.public-page-manifest/v1"

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
PUBLIC_DATASET_FILES = {
    "documents.jsonl",
    "chunks.jsonl",
    "source_records.jsonl",
    "passages.jsonl",
    "insight_cards.jsonl",
    "topics.jsonl",
    "creators.jsonl",
}
PUBLIC_PAGE_MANIFEST_KEYS = {"schema", "style_version", "page_count", "pages"}

_PRIVATE_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "absolute_posix_path",
        re.compile(r"(?:^|[\s\"'=(]|:(?!//))/(?!/)[A-Za-z0-9._~-]", re.I),
    ),
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

# Package-wide release receipts can legitimately contain public root-relative
# web routes (for example, ``/knowledge/search/``). This narrower set is used
# when auditing every JSON artifact in a release: it rejects machine-local and
# private storage shapes without treating those public routes as leaks.
_MACHINE_LOCAL_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "machine_local_posix_path",
        re.compile(
            r"(?:^|[\s\"'=(]|:(?!//))/(?:Users|home|root|srv|var|private|tmp|opt|mnt|Volumes)(?:/|$)",
            re.I,
        ),
    ),
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


def issue(pointer: str, reason: str) -> dict[str, str]:
    return {"pointer": pointer or "/", "reason": reason}


def private_value_issues(value: Any, pointer: str = "") -> list[dict[str, str]]:
    """Recursively find private path shapes without returning their values."""

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
            for reason in key_reasons:
                issues.append(issue(child_pointer, f"{reason}_in_key"))
            issues.extend(private_value_issues(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(private_value_issues(child, _pointer(pointer, index)))
    elif isinstance(value, str):
        for reason, pattern in _PRIVATE_VALUE_PATTERNS:
            if pattern.search(value):
                issues.append(issue(pointer, reason))
    return issues


def machine_local_value_issues(value: Any, pointer: str = "") -> list[dict[str, str]]:
    """Find machine-local/private storage shapes while allowing public web routes.

    Results are pointer-only and never echo a potentially sensitive value.
    """

    issues: list[dict[str, str]] = []
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            key_reasons = [
                reason
                for reason, pattern in _MACHINE_LOCAL_VALUE_PATTERNS
                if isinstance(key, str) and pattern.search(key)
            ]
            child_pointer = (
                _pointer(pointer, f"_redacted_key_{index}")
                if key_reasons
                else _pointer(pointer, key)
            )
            for reason in key_reasons:
                issues.append(issue(child_pointer, f"{reason}_in_key"))
            issues.extend(machine_local_value_issues(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(machine_local_value_issues(child, _pointer(pointer, index)))
    elif isinstance(value, str):
        for reason, pattern in _MACHINE_LOCAL_VALUE_PATTERNS:
            if pattern.search(value):
                issues.append(issue(pointer, reason))
    return issues


def relative_public_route_issue(route: object) -> str | None:
    if not isinstance(route, str) or not route:
        return "route_must_be_nonempty_string"
    if "\\" in route:
        return "route_must_use_posix_separators"
    if "://" in route or route.startswith("//"):
        return "route_must_not_be_url"
    path = PurePosixPath(route)
    if path.is_absolute():
        return "route_must_be_relative"
    if any(part in {"", ".", ".."} for part in path.parts):
        return "route_has_unsafe_segment"
    if path.as_posix() != route:
        return "route_is_not_normalized"
    return None


def _unexpected_keys(payload: dict[str, Any], allowed: set[str], pointer: str = "") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, _key in enumerate(sorted(set(payload) - allowed, key=str)):
        issues.append(issue(_pointer(pointer, f"_undeclared_key_{index}"), "undeclared_key"))
    for key in sorted(allowed - set(payload)):
        issues.append(issue(_pointer(pointer, key), "required_key_missing"))
    return issues


def _nonnegative_integer_issues(
    payload: dict[str, Any], keys: Iterable[str], pointer: str = ""
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            issues.append(issue(_pointer(pointer, key), "must_be_nonnegative_integer"))
    return issues


def validate_public_dataset_manifest(payload: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return [issue("/", "manifest_must_be_object")]

    issues.extend(_unexpected_keys(payload, PUBLIC_DATASET_MANIFEST_KEYS))
    issues.extend(private_value_issues(payload))
    if payload.get("schema") != PUBLIC_DATASET_MANIFEST_SCHEMA:
        issues.append(issue("/schema", "unsupported_schema"))
    if payload.get("dataset") != "base2026-public-tiktok":
        issues.append(issue("/dataset", "unexpected_dataset"))
    if payload.get("scope") != "public TikTok-only export":
        issues.append(issue("/scope", "unexpected_scope"))
    if not isinstance(payload.get("created_at"), str) or not payload.get("created_at"):
        issues.append(issue("/created_at", "must_be_nonempty_string"))

    issues.extend(_nonnegative_integer_issues(payload, PUBLIC_DATASET_COUNT_KEYS))
    admissions = payload.get("source_admission_counts")
    if not isinstance(admissions, dict):
        issues.append(issue("/source_admission_counts", "must_be_object"))
    else:
        issues.extend(_unexpected_keys(admissions, PUBLIC_ADMISSION_COUNT_KEYS, "/source_admission_counts"))
        issues.extend(_nonnegative_integer_issues(admissions, PUBLIC_ADMISSION_COUNT_KEYS, "/source_admission_counts"))
        if all(isinstance(admissions.get(key), int) for key in PUBLIC_ADMISSION_COUNT_KEYS):
            normal = admissions.get("normal_public_card", 0)
            archive = admissions.get("provenance_archive_noindex", 0)
            if payload.get("documents") != normal:
                issues.append(issue("/documents", "normal_admission_count_mismatch"))
            if payload.get("source_records") != normal + archive:
                issues.append(issue("/source_records", "public_source_admission_count_mismatch"))

    if payload.get("source_admission_active") is not True:
        issues.append(issue("/source_admission_active", "public_admission_must_be_active"))
    if payload.get("include_full_transcripts") is not False:
        issues.append(issue("/include_full_transcripts", "full_transcripts_forbidden"))
    if payload.get("auto_promote_insights") is not False:
        issues.append(issue("/auto_promote_insights", "auto_promotion_forbidden"))
    threshold = payload.get("insight_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
        issues.append(issue("/insight_threshold", "must_be_nonnegative_number"))
    if payload.get("public_policy") != "excerpt_only":
        issues.append(issue("/public_policy", "unexpected_public_policy"))
    files = payload.get("files")
    if not isinstance(files, list) or any(not isinstance(item, str) for item in files):
        issues.append(issue("/files", "must_be_string_array"))
    elif len(files) != len(set(files)) or set(files) != PUBLIC_DATASET_FILES:
        issues.append(issue("/files", "public_file_allowlist_mismatch"))
    return issues


def validate_public_page_manifest(payload: Any, web_root: Path | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return [issue("/", "manifest_must_be_object")]

    issues.extend(_unexpected_keys(payload, PUBLIC_PAGE_MANIFEST_KEYS))
    issues.extend(private_value_issues(payload))
    if payload.get("schema") != PUBLIC_PAGE_MANIFEST_SCHEMA:
        issues.append(issue("/schema", "unsupported_schema"))
    if not isinstance(payload.get("style_version"), str) or not payload.get("style_version"):
        issues.append(issue("/style_version", "must_be_nonempty_string"))
    pages = payload.get("pages")
    if not isinstance(pages, list):
        issues.append(issue("/pages", "must_be_array"))
        return issues
    if isinstance(payload.get("page_count"), bool) or not isinstance(payload.get("page_count"), int):
        issues.append(issue("/page_count", "must_be_nonnegative_integer"))
    elif payload.get("page_count") != len(pages):
        issues.append(issue("/page_count", "page_count_mismatch"))
    if len(pages) != len({item for item in pages if isinstance(item, str)}):
        issues.append(issue("/pages", "duplicate_route"))

    resolved_root = web_root.resolve() if web_root else None
    for index, route in enumerate(pages):
        pointer = _pointer("/pages", index)
        route_problem = relative_public_route_issue(route)
        if route_problem:
            issues.append(issue(pointer, route_problem))
            continue
        if not str(route).endswith(".html"):
            issues.append(issue(pointer, "route_must_target_html"))
            continue
        if resolved_root:
            target = (resolved_root / str(route)).resolve()
            if resolved_root not in target.parents or not target.is_file():
                issues.append(issue(pointer, "route_target_missing_or_outside_web_root"))
    return issues
