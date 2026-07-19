#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


CACHE_BUST_RE = re.compile(rb"([?&]v=)[^&\"'\s<>]+")
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalized_payload(path: Path, payload: bytes) -> bytes:
    if path.suffix.lower() in {".html", ".htm"}:
        return CACHE_BUST_RE.sub(rb"\1__CACHE_BUST__", payload)
    return payload


def oracle_sha(entries: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative, payload in entries:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path, required=True)
    parser.add_argument("--source-label", default="accepted-search-root")
    parser.add_argument("--staged-label", default="web")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    for value in (args.source_label, args.staged_label):
        if not SAFE_LABEL_RE.fullmatch(value):
            parser.error("labels may contain only letters, numbers, dot, underscore, and dash")

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("schema") != "base2026.search-protected-files/v1":
        raise SystemExit("unsupported protected Search contract schema")
    files = contract.get("files")
    if not isinstance(files, list) or not files or any(not isinstance(item, str) for item in files):
        raise SystemExit("protected Search contract must contain a non-empty string file list")

    errors: list[str] = []
    source_entries: list[tuple[str, bytes]] = []
    staged_entries: list[tuple[str, bytes]] = []
    file_reports: list[dict[str, object]] = []
    for relative in sorted(set(files)):
        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts or "\\" in relative:
            raise SystemExit(f"unsafe protected Search path: {relative}")
        source_path = args.source_root / rel_path
        staged_path = args.staged_root / rel_path
        source_exists = source_path.is_file()
        staged_exists = staged_path.is_file()
        if not source_exists:
            errors.append(f"source_missing:{relative}")
        if not staged_exists:
            errors.append(f"staged_missing:{relative}")
        if not source_exists or not staged_exists:
            file_reports.append({"path": relative, "ok": False})
            continue

        source_raw = source_path.read_bytes()
        staged_raw = staged_path.read_bytes()
        source_normalized = normalized_payload(rel_path, source_raw)
        staged_normalized = normalized_payload(rel_path, staged_raw)
        matches = source_normalized == staged_normalized
        if not matches:
            errors.append(f"semantic_mismatch:{relative}")
        source_entries.append((relative, source_normalized))
        staged_entries.append((relative, staged_normalized))
        file_reports.append(
            {
                "path": relative,
                "ok": matches,
                "source_sha256": sha256_bytes(source_raw),
                "staged_sha256": sha256_bytes(staged_raw),
                "normalized_sha256": sha256_bytes(staged_normalized),
            }
        )

    source_oracle = oracle_sha(source_entries)
    staged_oracle = oracle_sha(staged_entries)
    ok = not errors and source_oracle == staged_oracle and len(source_entries) == len(set(files))
    report = {
        "schema": "base2026.search-semantic-oracle/v1",
        "status": "PASS" if ok else "FAIL",
        "policy": "exact protected Search files; HTML cache-bust query values normalized",
        "source_root": args.source_label,
        "staged_root": args.staged_label,
        "protected_file_count": len(set(files)),
        "source_oracle_sha256": source_oracle,
        "staged_oracle_sha256": staged_oracle,
        "search_oracle_sha256": staged_oracle if ok else None,
        "errors": errors,
        "files": file_reports,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} protected_files={report['protected_file_count']} "
        f"search_oracle_sha256={report['search_oracle_sha256'] or '-'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
