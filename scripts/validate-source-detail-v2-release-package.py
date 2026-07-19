#!/usr/bin/env python3
"""Fail-closed verification of Source Detail V2 inside a staged public release.

The staged package is allowed to differ from the immutable candidate only in the
release cache-bust query applied to the four Source Detail V2 shell assets.
Everything else in every detail page and every candidate static asset must stay
byte-equivalent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CANDIDATE_SCHEMA = "base2026.source-detail-v2-full-candidate/v1"
DETAIL_GLOB = "tiktok-video-*.html"
VERSIONED_ASSET_RE = re.compile(
    r"((?:href|src)=[\"'][^\"']*/(?:"
    r"alex-v4-static-shell\.(?:css|js)|"
    r"source-detail-v2\.(?:css|js)"
    r"))\?v=[^\"']+"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_html(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return VERSIONED_ASSET_RE.sub(r"\1?v=ASSET_VERSION", text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--candidate-label", default="source-detail-candidate")
    parser.add_argument("--web-root", required=True, type=Path)
    parser.add_argument("--web-root-label", default="web")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = args.candidate.resolve()
    web_root = args.web_root.resolve()
    manifest_path = candidate / "candidate-manifest.json"
    errors: list[str] = []

    if not manifest_path.is_file():
        raise SystemExit(f"candidate manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != CANDIDATE_SCHEMA:
        errors.append(
            f"candidate schema mismatch: {manifest.get('schema')!r} != {CANDIDATE_SCHEMA!r}"
        )

    candidate_sources = candidate / "sources"
    staged_sources = web_root / "sources"
    candidate_files = {path.name: path for path in candidate_sources.glob(DETAIL_GLOB)}
    staged_files = {path.name: path for path in staged_sources.glob(DETAIL_GLOB)}
    rendered = {
        Path(item["route"]).name
        for item in manifest.get("rendered", [])
        if isinstance(item, dict) and item.get("route")
    }
    future_private = {
        Path(route).name for route in manifest.get("future_private_not_emitted", [])
    }

    if set(candidate_files) != rendered:
        missing = sorted(rendered - set(candidate_files))
        extra = sorted(set(candidate_files) - rendered)
        errors.append(
            f"candidate rendered/file mismatch: missing={missing[:10]} extra={extra[:10]}"
        )
    if set(staged_files) != rendered:
        missing = sorted(rendered - set(staged_files))
        extra = sorted(set(staged_files) - rendered)
        errors.append(
            f"staged detail file mismatch: missing={missing[:10]} extra={extra[:10]}"
        )

    emitted_future = sorted(future_private & set(staged_files))
    if emitted_future:
        errors.append(f"future-private routes emitted: {emitted_future[:10]}")

    html_mismatches: list[str] = []
    for name in sorted(rendered & set(candidate_files) & set(staged_files)):
        if normalized_html(candidate_files[name]) != normalized_html(staged_files[name]):
            html_mismatches.append(name)
    if html_mismatches:
        errors.append(
            f"staged HTML differs beyond approved cache-bust changes: {html_mismatches[:10]}"
        )

    asset_results: dict[str, dict[str, object]] = {}
    for rel, expected_hash in sorted(manifest.get("asset_sha256", {}).items()):
        candidate_asset = candidate / "static" / rel
        staged_asset = web_root / "static" / rel
        candidate_hash = sha256(candidate_asset) if candidate_asset.is_file() else None
        staged_hash = sha256(staged_asset) if staged_asset.is_file() else None
        ok = candidate_hash == expected_hash and staged_hash == expected_hash
        asset_results[rel] = {
            "expected_sha256": expected_hash,
            "candidate_sha256": candidate_hash,
            "staged_sha256": staged_hash,
            "ok": ok,
        }
        if not ok:
            errors.append(
                f"asset mismatch {rel}: expected={expected_hash} "
                f"candidate={candidate_hash} staged={staged_hash}"
            )

    report = {
        "schema": "base2026.source-detail-v2-release-package-validation/v1",
        "candidate": args.candidate_label,
        "candidate_manifest_sha256": sha256(manifest_path),
        "web_root": args.web_root_label,
        "rendered_expected": len(rendered),
        "candidate_detail_files": len(candidate_files),
        "staged_detail_files": len(staged_files),
        "future_private_not_emitted": len(future_private),
        "html_mismatches": html_mismatches,
        "assets": asset_results,
        "errors": errors,
        "ok": not errors,
    }
    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
