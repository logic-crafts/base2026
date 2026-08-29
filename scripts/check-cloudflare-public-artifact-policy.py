#!/usr/bin/env python3
"""Validate the Cloudflare-specific Base2026 public artifact profile.

The canonical private export contains seven replay files.  The root-mounted
Cloudflare artifact intentionally publishes only four reviewed read-only files
and records that reduced profile in ``static/manifest.json``.  This versioned
gate validates that exact profile plus the release builder's leak checks and
emits a hash-addressed receipt suitable for a production handoff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from public_manifest_contract import (
    CLOUDFLARE_PUBLIC_DATASET_FILES,
    validate_public_dataset_manifest,
)


SCHEMA = "base2026-cloudflare-publication-gate/v1"
BUILD_RECEIPT = ".base2026-cloudflare-release-receipt.json"
REQUIRED_TRUE_CHECKS = {
    "artifact_files_include_required_root_metadata",
    "binary_bytes_preserved",
    "static_manifest_checked",
    "static_manifest_files_match",
}
REQUIRED_ZERO_CHECKS = {
    "broken_knowledge_product_paths_remaining",
    "decorative_sequence_markers_remaining",
    "local_path_markers_remaining",
    "old_base2026_canonical_origin_remaining",
    "personal_commercial_markers_remaining",
    "personal_route_markers_remaining",
    "personal_shell_markers_remaining",
    "personal_site_origin_markers_remaining",
    "private_token_markers_remaining",
    "wordpress_form_markers_remaining",
}


class ArtifactGateError(ValueError):
    """The static candidate is not safe for the Cloudflare release profile."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactGateError(f"cannot read valid {label}") from exc
    if not isinstance(value, dict):
        raise ArtifactGateError(f"{label} must be an object")
    return value


def count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ArtifactGateError(
                    f"{path.name} contains invalid JSONL at line {line_number}"
                ) from exc
            if not isinstance(value, dict):
                raise ArtifactGateError(f"{path.name} line {line_number} must be an object")
            if path.name == "insight_cards.jsonl":
                if value.get("public") is not True:
                    raise ArtifactGateError(
                        f"insight_cards.jsonl line {line_number} is not public"
                    )
                if value.get("needs_review") is True:
                    raise ArtifactGateError(
                        f"insight_cards.jsonl line {line_number} still needs review"
                    )
                if value.get("public_policy") != "reviewed_insight":
                    raise ArtifactGateError(
                        f"insight_cards.jsonl line {line_number} has a non-public policy"
                    )
            count += 1
    if count == 0:
        raise ArtifactGateError(f"{path.name} is empty")
    return count


def validate_artifact(artifact_dir: Path) -> dict[str, Any]:
    root = artifact_dir.resolve()
    static_dir = root / "static"
    manifest_path = static_dir / "manifest.json"
    build_receipt_path = root / BUILD_RECEIPT
    manifest = load_json(manifest_path, "static manifest")
    issues = validate_public_dataset_manifest(
        manifest,
        allowed_files=CLOUDFLARE_PUBLIC_DATASET_FILES,
    )
    if issues:
        summary = ", ".join(
            f"{item['pointer']}:{item['reason']}" for item in issues[:20]
        )
        raise ArtifactGateError(f"static manifest rejected: {summary}")

    build_receipt = load_json(build_receipt_path, "Cloudflare build receipt")
    artifact = build_receipt.get("artifact")
    verification = build_receipt.get("verification")
    if not isinstance(artifact, dict) or not isinstance(verification, dict):
        raise ArtifactGateError("Cloudflare build receipt is missing artifact verification")
    if any(verification.get(key) is not True for key in REQUIRED_TRUE_CHECKS):
        raise ArtifactGateError("Cloudflare build receipt has an incomplete true gate")
    if any(verification.get(key) != 0 for key in REQUIRED_ZERO_CHECKS):
        raise ArtifactGateError("Cloudflare build receipt contains a non-zero leak marker")
    tree_hash = artifact.get("tree_sha256")
    if not isinstance(tree_hash, str) or len(tree_hash) != 64:
        raise ArtifactGateError("Cloudflare build receipt has an invalid tree hash")
    if not isinstance(artifact.get("file_count"), int) or artifact["file_count"] <= 0:
        raise ArtifactGateError("Cloudflare build receipt has an invalid file count")

    file_receipts: list[dict[str, Any]] = []
    row_counts: dict[str, int] = {}
    for name in sorted(CLOUDFLARE_PUBLIC_DATASET_FILES):
        path = static_dir / name
        if not path.is_file():
            raise ArtifactGateError(f"static manifest file is missing: {name}")
        rows = count_jsonl(path)
        row_counts[name] = rows
        file_receipts.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "rows": rows,
                "sha256": sha256_file(path),
            }
        )

    insight_rows = row_counts["insight_cards.jsonl"]
    if manifest.get("insight_cards") != insight_rows:
        raise ArtifactGateError("static manifest insight_cards count does not match file")
    if manifest.get("public_insight_cards") != insight_rows:
        raise ArtifactGateError("static manifest public_insight_cards count does not match file")

    return {
        "schema": SCHEMA,
        "ok": True,
        "artifact": {
            "file_count": artifact["file_count"],
            "byte_count": artifact.get("byte_count"),
            "tree_sha256": tree_hash,
            "build_receipt_sha256": sha256_file(build_receipt_path),
        },
        "static_manifest_sha256": sha256_file(manifest_path),
        "public_data_files": file_receipts,
        "public_data_profile": "cloudflare-reviewed-readonly-v1",
    }


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise ArtifactGateError(f"receipt path already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            json.dump(payload, target, ensure_ascii=False, sort_keys=True, indent=2)
            target.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Cloudflare public artifact.")
    parser.add_argument("artifact_dir", type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = validate_artifact(args.artifact_dir)
        write_receipt(args.receipt, receipt)
    except ArtifactGateError as exc:
        print(f"Cloudflare publication gate rejected: {exc}")
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "schema": receipt["schema"],
                "tree_sha256": receipt["artifact"]["tree_sha256"],
                "public_data_files": len(receipt["public_data_files"]),
                "receipt": str(args.receipt),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
