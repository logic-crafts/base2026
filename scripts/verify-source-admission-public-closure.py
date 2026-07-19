#!/usr/bin/env python3
"""Prove the current admission ledger has no future/private public effect.

The receipt is intentionally generic: it binds the complete current
``future_private_backlog`` set, not a historical delta count.  It verifies
exact public Source membership and scans every accepted export artifact for
future/private item, source, and video identifiers without emitting those
identifiers into the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


PUBLIC_STATES = {"normal_public_card", "provenance_archive_noindex"}
FUTURE_STATE = "future_private_backlog"
SUPPORTED_STATES = PUBLIC_STATES | {FUTURE_STATE}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def public_files(root: Path) -> list[Path]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise ValueError("Public export root contains no files")
    return files


def tree_sha256(root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_receipt(
    ledger: Path,
    export_root: Path,
    *,
    ledger_label: str,
    export_label: str,
) -> dict[str, Any]:
    ledger_rows = read_jsonl(ledger)
    if not ledger_rows:
        raise ValueError("Admission ledger is empty")
    by_item: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for row in ledger_rows:
        item_id = str(row.get("item_id") or "")
        source_id = str(row.get("source_id") or "")
        state = str(row.get("admission_state") or "")
        if not item_id or not source_id or state not in SUPPORTED_STATES:
            errors.append("ledger row lacks a supported item/source/admission contract")
            continue
        if item_id in by_item:
            errors.append(f"duplicate ledger item_id hash={hashlib.sha256(item_id.encode()).hexdigest()}")
            continue
        by_item[item_id] = row

    source_records_path = export_root / "source_records.jsonl"
    manifest_path = export_root / "manifest.json"
    if not source_records_path.is_file() or not manifest_path.is_file():
        raise ValueError("Public export must contain source_records.jsonl and manifest.json")
    source_rows = read_jsonl(source_records_path)
    exported_by_item: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        item_id = str(row.get("item_id") or "")
        if not item_id or item_id in exported_by_item:
            errors.append("public source_records contains a missing or duplicate item_id")
            continue
        exported_by_item[item_id] = row

    expected_public = {
        item_id: row
        for item_id, row in by_item.items()
        if str(row.get("admission_state") or "") in PUBLIC_STATES
    }
    missing_public = sorted(set(expected_public) - set(exported_by_item))
    unexpected_public = sorted(set(exported_by_item) - set(expected_public))
    state_mismatches = sorted(
        item_id
        for item_id in set(expected_public) & set(exported_by_item)
        if str(expected_public[item_id].get("admission_state") or "")
        != str(exported_by_item[item_id].get("admission_state") or "")
    )
    if missing_public:
        errors.append(f"public export is missing {len(missing_public)} ledger-approved source records")
    if unexpected_public:
        errors.append(f"public export contains {len(unexpected_public)} non-public source records")
    if state_mismatches:
        errors.append(f"public export has {len(state_mismatches)} admission-state mismatches")

    future_rows = [
        row for row in by_item.values() if str(row.get("admission_state") or "") == FUTURE_STATE
    ]
    future_identifiers: set[bytes] = set()
    for row in future_rows:
        item_id = str(row["item_id"])
        source_id = str(row["source_id"])
        video_id = item_id.removeprefix("tiktok-video-")
        future_identifiers.update(
            value.encode("utf-8") for value in (item_id, source_id, video_id) if value
        )

    files = public_files(export_root)
    leaked_files: set[str] = set()
    leaked_identifier_hashes: set[str] = set()
    for path in files:
        payload = path.read_bytes()
        for identifier in future_identifiers:
            if identifier in payload:
                leaked_files.add(path.relative_to(export_root).as_posix())
                leaked_identifier_hashes.add(hashlib.sha256(identifier).hexdigest())
    if leaked_files:
        errors.append(
            f"future/private identifiers occur in {len(leaked_files)} public export artifacts"
        )

    counts = Counter(str(row.get("admission_state") or "") for row in by_item.values())
    exact_membership = not missing_public and not unexpected_public and not state_mismatches
    all_future_absent = not leaked_files and bool(future_rows)
    return {
        "schema": "base2026.source-admission-public-closure/v2",
        "status": "PASS" if not errors and exact_membership and all_future_absent else "FAIL",
        "ledger_label": ledger_label,
        "ledger_new_sha256": sha256(ledger),
        "public_export_label": export_label,
        "public_export_manifest_sha256": sha256(manifest_path),
        "public_export_tree_sha256": tree_sha256(export_root, files),
        "admission_counts": dict(sorted(counts.items())),
        "public_export_counts": {"source_records": len(source_rows)},
        "verification": {
            "exact_public_source_membership": exact_membership,
            "all_future_private_identifiers_absent_from_all_public_export_files": all_future_absent,
            "future_private_records_checked": len(future_rows),
            "future_private_identifiers_checked": len(future_identifiers),
            "public_export_files_scanned": len(files),
            "leaked_public_file_count": len(leaked_files),
            "leaked_identifier_hash_count": len(leaked_identifier_hashes),
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--admission-ledger",
        default="12_knowledge-base/sources/tiktok/source-admission.jsonl",
    )
    parser.add_argument("--public-export-root", required=True)
    parser.add_argument("--ledger-label", default="current-source-admission-ledger")
    parser.add_argument("--public-export-label", default="accepted-public-export")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite closure receipt: {out}")
    receipt = build_receipt(
        Path(args.admission_ledger).resolve(),
        Path(args.public_export_root).resolve(),
        ledger_label=args.ledger_label,
        export_label=args.public_export_label,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
