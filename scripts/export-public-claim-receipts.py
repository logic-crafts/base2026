#!/usr/bin/env python3
"""Export a validated public-D1 claim-receipt readback.

The input is a JSON readback of ``GET /api/claim-receipts/v1`` (or the
equivalent owner-only public-D1 read method).  This script never reads local
pipeline tables and never accepts private transcript/import fields.  It
writes exactly two deterministic sidecars:

* ``claim_receipts.jsonl`` — one canonical immutable receipt per line;
* ``claim_receipts_manifest.json`` — the file and ledger digests.

No generation timestamp is copied into either sidecar.  The API's response
timestamp is useful for a live response but is intentionally not part of the
reproducible export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit


LEDGER_SCHEMA = "base2026.claim-receipt-ledger.v1"
RECEIPT_SCHEMA = "base2026.claim-receipt.v1"
STATIC_MANIFEST_SCHEMA = "base2026.claim-receipt-static-manifest.v1"
CANARY_ID = "base2026.internal-linking.canary.v1"
TOPIC = "internal-linking"
POLICY_VERSION = "base2026.claim-receipt-admission.v1"
COUNT = 10
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[a-f0-9]{40}$")
VIDEO_RE = re.compile(r"^[0-9]{10,30}$")
HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{2,256}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PRIVATE_KEY_RE = re.compile(
    r"(?:private|raw|transcript|caption|asr|secret|token|password|credential|contact|email|media|inbox|outreach)",
    re.IGNORECASE,
)
PRIVATE_VALUE_RE = re.compile(
    r"(?:file://|/Users/|/private/var/|/var/www/|(?:^|[/\\])(?:\.planning|\.hermes|meili_data|private)(?:[/\\]|$)|(?:raw[ _-]*(?:transcript|caption|asr)|not[ _-]*for[ _-]*public))",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s().-])?(?:\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10})(?!\d)"
)
SECRET_RE = re.compile(
    r"\b(?:api|access|auth|authentication|client|app|webhook)?[_\s-]*(?:key|token|secret|password|passwd|credential|cookie|session[_\s-]*id)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
SECRET_PHRASE_RE = re.compile(
    r"\b(?:api|access|auth|authentication|client|app|webhook)[_\s-]*(?:key|token|secret|password|passwd|credential)\s*(?:is\s+|[:=]\s*)\S+",
    re.IGNORECASE,
)
TOKEN_FORMAT_RE = re.compile(
    r"\b(?:sk_(?:live|test)_[A-Z0-9]{8,}|(?:ghp|github_pat|xox[baprs])[-_][A-Z0-9-]{8,}|AIza[A-Z0-9_-]{20,})\b",
    re.IGNORECASE,
)
BEARER_RE = re.compile(r"\bbearer\s+[A-Z0-9._~+/=-]{8,}\b", re.IGNORECASE)

RECEIPT_KEYS = {
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
READBACK_KEYS = {
    "schema_version",
    "canary_id",
    "topic",
    "policy_version",
    "count",
    "ledger_sha256",
    "generated_at",
    "receipts",
}


class ExportError(ValueError):
    """The readback is not a complete, public, deterministic canary."""


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ExportError("non-finite numeric value")
        if value.is_integer():
            return int(value)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ExportError(reason)


def check_public_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(isinstance(key, str), "object key must be a string")
            require(not PRIVATE_KEY_RE.search(key), "private field is not exportable")
            check_public_keys(child)
    elif isinstance(value, list):
        for child in value:
            check_public_keys(child)
    elif isinstance(value, str):
        require(not PRIVATE_VALUE_RE.search(value), "private value is not exportable")


def string_value(value: Any, name: str, minimum: int, maximum: int) -> str:
    require(isinstance(value, str), f"{name} must be a string")
    result = value.strip()
    require(minimum <= len(result) <= maximum, f"{name} has an invalid length")
    return result


def public_text_value(value: Any, name: str, minimum: int, maximum: int) -> str:
    result = string_value(value, name, minimum, maximum)
    require(
        not any(
            pattern.search(result)
            for pattern in (
                PRIVATE_VALUE_RE,
                EMAIL_RE,
                PHONE_RE,
                SECRET_RE,
                SECRET_PHRASE_RE,
                TOKEN_FORMAT_RE,
                BEARER_RE,
            )
        ),
        f"{name} contains a private or secret marker",
    )
    return result


def hash_value(value: Any, name: str) -> str:
    result = string_value(value, name, 64, 64).lower()
    require(bool(HASH_RE.fullmatch(result)), f"{name} must be a lowercase SHA-256")
    return result


def id_value(value: Any, name: str) -> str:
    result = string_value(value, name, 40, 40).lower()
    require(bool(ID_RE.fullmatch(result)), f"{name} must be a lowercase public id")
    return result


def date_value(value: Any, name: str) -> str:
    result = string_value(value, name, 10, 10)
    require(bool(DATE_RE.fullmatch(result)), f"{name} must be YYYY-MM-DD")
    year, month, day = (int(part) for part in result.split("-"))
    require(1 <= month <= 12 and 1 <= day <= 31, f"{name} is not a calendar date")
    # datetime is deliberately avoided here: the public projection stores a
    # bounded date and this check only needs to reject impossible month/day
    # combinations without accepting timezone-bearing private metadata.
    days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    require(day <= days_in_month[month - 1], f"{name} is not a calendar date")
    return result


def validate_url(value: Any, name: str, expected: str, maximum: int = 2_048) -> str:
    result = string_value(value, name, 12, maximum)
    try:
        parsed = urlsplit(result)
        has_port = parsed.port
    except ValueError as exc:
        raise ExportError(f"{name} is not canonical") from exc
    require(parsed.scheme == "https" and not parsed.query and not parsed.fragment and not parsed.username and not parsed.password and not has_port, f"{name} is not canonical")
    require(result == expected, f"{name} is not canonical")
    return result


def validate_receipt(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "receipt must be an object")
    require(set(value) == RECEIPT_KEYS, "receipt fields do not match the public allowlist")
    require(value["schema_version"] == RECEIPT_SCHEMA, "unsupported receipt schema")
    require(value["canary_id"] == CANARY_ID, "unexpected canary")
    require(value["policy_version"] == POLICY_VERSION, "unexpected policy")
    receipt_id = string_value(value["receipt_id"], "receipt_id", 64, 64).lower()
    # receipt_id is a 64-character SHA-256 in the Worker ledger.  Projection,
    # card and search identities use the separate 40-character parser below.
    require(bool(HASH_RE.fullmatch(receipt_id)), "receipt_id must be a SHA-256")
    rank = value["selection_rank"]
    require(isinstance(rank, int) and not isinstance(rank, bool) and 1 <= rank <= COUNT, "selection_rank is invalid")
    source_id = string_value(value["source_id"], "source_id", 10, 300)
    source_match = re.fullmatch(r"tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})", source_id)
    require(source_match is not None, "source_id is not canonical")
    handle = source_match.group(1)
    video_id = string_value(value["video_id"], "video_id", 10, 30)
    require(bool(VIDEO_RE.fullmatch(video_id)) and video_id == source_match.group(2), "video_id is not canonical")
    creator_handle = string_value(value["creator_handle"], "creator_handle", 3, 257)
    require(creator_handle == f"@{handle}", "creator_handle does not match source_id")
    creator_display_name = public_text_value(value["creator_display_name"], "creator_display_name", 0, 256)
    creator_url = validate_url(value["creator_url"], "creator_url", f"https://www.tiktok.com/@{handle}", 512)
    original_url = validate_url(value["original_url"], "original_url", f"https://www.tiktok.com/@{handle}/video/{video_id}")
    base_url = validate_url(value["base2026_url"], "base2026_url", f"https://base2026.dev/sources/tiktok-video-{video_id}", 512)
    published_at = date_value(value["published_at"], "published_at")
    published_date = date_value(value["published_date"], "published_date")
    require(published_at == published_date, "published date mismatch")
    claim = public_text_value(value["claim_text"], "claim_text", 20, 360)
    action = public_text_value(value["suggested_action"], "suggested_action", 20, 360)
    topic_label = public_text_value(value["topic_label"], "topic_label", 2, 120)
    evidence = public_text_value(value["evidence_excerpt"], "evidence_excerpt", 20, 520)
    normalized_topic = re.sub(r"[^\w]+", "-", topic_label.casefold(), flags=re.UNICODE).strip("-")
    require(bool(re.fullmatch(r"internal-linking(?:-[a-z0-9]+)*", normalized_topic)), "topic label is outside the canary")
    ordinal = value["card_ordinal"]
    require(isinstance(ordinal, int) and not isinstance(ordinal, bool) and 0 <= ordinal <= 2, "card_ordinal is invalid")
    start = value["evidence_start_seconds"]
    end = value["evidence_end_seconds"]
    require(isinstance(start, (int, float)) and not isinstance(start, bool) and math.isfinite(start) and 0 <= start <= 86_400, "evidence start is invalid")
    require(isinstance(end, (int, float)) and not isinstance(end, bool) and math.isfinite(end) and start <= end <= 86_400, "evidence end is invalid")
    require(abs(round(start * 1_000) / 1_000 - start) <= sys.float_info.epsilon * max(1, start), "evidence start precision is invalid")
    require(abs(round(end * 1_000) / 1_000 - end) <= sys.float_info.epsilon * max(1, end), "evidence end precision is invalid")
    hash_value(value["public_projection_receipt_sha256"], "public_projection_receipt_sha256")
    immutable = dict(value)
    # The Worker derives receipt_id from all immutable fields except the id.
    immutable.pop("receipt_id")
    expected_receipt_id = sha256_text(canonical_json(immutable))
    require(receipt_id == expected_receipt_id, "receipt_id does not match immutable receipt")
    return canonicalize(value)


def validate_readback(value: Any) -> tuple[list[dict[str, Any]], str]:
    require(isinstance(value, dict), "readback must be an object")
    check_public_keys(value)
    require(set(value) == READBACK_KEYS, "readback fields do not match the public API")
    require(value["schema_version"] == LEDGER_SCHEMA, "unsupported ledger schema")
    require(value["canary_id"] == CANARY_ID and value["topic"] == TOPIC, "unexpected canary or topic")
    require(value["policy_version"] == POLICY_VERSION, "unexpected policy")
    require(value["count"] == COUNT, "claim-receipt canary must contain exactly ten rows")
    require(isinstance(value["receipts"], list), "receipts must be an array")
    receipts = [validate_receipt(item) for item in value["receipts"]]
    require(len(receipts) == COUNT, "claim-receipt canary must contain exactly ten rows")
    require([item["selection_rank"] for item in receipts] == list(range(1, COUNT + 1)), "selection ranks must be contiguous")
    require(len({item["receipt_id"] for item in receipts}) == COUNT, "receipt ids must be unique")
    require(len({item["source_id"] for item in receipts}) == COUNT, "sources must be unique")
    creators: dict[str, int] = {}
    for item in receipts:
        creators[item["creator_handle"]] = creators.get(item["creator_handle"], 0) + 1
    require(all(count <= 2 for count in creators.values()), "creator limit exceeded")
    expected_ledger = sha256_text("\n".join(canonical_json(item) for item in receipts) + "\n")
    ledger_sha256 = hash_value(value["ledger_sha256"], "ledger_sha256")
    require(ledger_sha256 == expected_ledger, "ledger digest does not match receipts")
    return receipts, ledger_sha256


def export_readback(readback: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    receipts, ledger_sha256 = validate_readback(dict(readback))
    jsonl_payload = "".join(f"{canonical_json(receipt)}\n" for receipt in receipts)
    jsonl_sha256 = sha256_text(jsonl_payload)
    manifest = {
        "schema": STATIC_MANIFEST_SCHEMA,
        "canary_id": CANARY_ID,
        "topic": TOPIC,
        "policy_version": POLICY_VERSION,
        "count": COUNT,
        "ledger_sha256": ledger_sha256,
        "jsonl": "claim_receipts.jsonl",
        "jsonl_sha256": jsonl_sha256,
        "generated_from": "validated-public-d1-readback",
    }
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "claim_receipts.jsonl"
    manifest_path = output_dir / "claim_receipts_manifest.json"
    require(not jsonl_path.exists() and not manifest_path.exists(), "refusing to overwrite claim-receipt sidecars")
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as target:
        target.write(jsonl_payload)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as target:
        target.write(canonical_json(manifest) + "\n")
    return {
        "jsonl": str(jsonl_path),
        "manifest": str(manifest_path),
        "ledger_sha256": ledger_sha256,
        "jsonl_sha256": jsonl_sha256,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="validated public-D1 JSON readback")
    parser.add_argument("--out-dir", required=True, type=Path, help="new directory for deterministic public sidecars")
    args = parser.parse_args(argv)
    try:
        readback = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = export_readback(readback, args.out_dir)
    except (OSError, UnicodeError, json.JSONDecodeError, ExportError) as exc:
        print(f"claim-receipt export rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **receipt}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
