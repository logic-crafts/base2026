#!/usr/bin/env python3
"""Validate every Base2026 manifest copied into a public release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from public_manifest_contract import (
    validate_public_dataset_manifest,
    validate_public_page_manifest,
)


def read_json(path: Path) -> tuple[Any | None, list[dict[str, str]]]:
    if not path.is_file():
        return None, [{"pointer": "/", "reason": "manifest_missing"}]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, [{"pointer": "/", "reason": "manifest_not_valid_utf8_json"}]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-manifest", action="append", type=Path, default=[])
    parser.add_argument("--page-manifest", action="append", type=Path, default=[])
    parser.add_argument("--web-root", type=Path)
    args = parser.parse_args()

    reports: list[dict[str, Any]] = []
    if not args.dataset_manifest and not args.page_manifest:
        reports.append(
            {
                "kind": "configuration",
                "index": 0,
                "issues": [{"pointer": "/", "reason": "no_manifest_inputs"}],
            }
        )
    dataset_hashes: list[str] = []
    for index, path in enumerate(args.dataset_manifest):
        payload, issues = read_json(path)
        if payload is not None:
            issues.extend(validate_public_dataset_manifest(payload))
            dataset_hashes.append(sha256(path))
        reports.append({"kind": "dataset", "index": index, "issues": issues})

    if len(dataset_hashes) > 1 and len(set(dataset_hashes)) != 1:
        reports.append(
            {
                "kind": "dataset_mirrors",
                "index": 0,
                "issues": [{"pointer": "/", "reason": "dataset_manifest_mirror_mismatch"}],
            }
        )

    web_root = args.web_root.resolve() if args.web_root else None
    for index, path in enumerate(args.page_manifest):
        payload, issues = read_json(path)
        if payload is not None:
            issues.extend(validate_public_page_manifest(payload, web_root=web_root))
        reports.append({"kind": "pages", "index": index, "issues": issues})

    issue_count = sum(len(item["issues"]) for item in reports)
    print(
        json.dumps(
            {
                "schema": "base2026.public-manifest-validation/v1",
                "ok": issue_count == 0,
                "manifests_checked": len(args.dataset_manifest) + len(args.page_manifest),
                "issue_count": issue_count,
                "reports": reports,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if issue_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
