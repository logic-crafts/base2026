from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from public_manifest_contract import (
    PUBLIC_DATASET_MANIFEST_SCHEMA,
    PUBLIC_PAGE_MANIFEST_SCHEMA,
    validate_public_dataset_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
    return rows


def git_ls_files(prefixes: list[str]) -> list[str]:
    if not prefixes:
        return []
    cmd = ["git", "ls-files", "--", *prefixes]
    result = subprocess.run(cmd, cwd=ROOT, check=True, text=True, capture_output=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def public_insight_count(export_dir: Path) -> int:
    manifest_path = export_dir / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        value = manifest.get("public_insight_cards")
        if isinstance(value, int):
            return value
    return sum(1 for row in read_jsonl(export_dir / "insight_cards.jsonl") if row.get("public"))


def add_violation(violations: list[str], message: str) -> None:
    violations.append(message)


def validate_contract_shape(contract: dict[str, Any], violations: list[str]) -> None:
    public_release = contract.get("public_release") or {}
    manifest_contract = contract.get("public_manifest_contract") or {}
    sitemap_contract = contract.get("sitemap_contract") or {}
    if contract.get("contract_version") != 2:
        add_violation(violations, "public contract_version must be 2")
    if contract.get("release_lane") != "public":
        add_violation(violations, "contract release_lane must be public")
    if public_release.get("include_full_transcripts") is not False:
        add_violation(violations, "public contract must set include_full_transcripts=false")
    if public_release.get("allow_implicit_auto_promote_insights") is not False:
        add_violation(violations, "public contract must set allow_implicit_auto_promote_insights=false")

    statuses = set(public_release.get("allowed_public_insight_review_statuses") or [])
    methods = set(public_release.get("allowed_public_insight_promotion_methods") or [])
    required = {"approved", "reviewed", "public"}
    if not required.issubset(statuses):
        add_violation(violations, "public contract must allow approved/reviewed/public review statuses")
    if not required.issubset(methods):
        add_violation(violations, "public contract must allow approved/reviewed/public promotion methods")
    if manifest_contract != {
        "dataset_schema": PUBLIC_DATASET_MANIFEST_SCHEMA,
        "page_schema": PUBLIC_PAGE_MANIFEST_SCHEMA,
        "exact_key_allowlists": True,
        "reject_private_paths_recursively": True,
    }:
        add_violation(violations, "public manifest contract is incomplete or unsupported")
    expected_sitemap = {
        "schema": "base2026.sitemap-admission/v2",
        "normal_public_card": "included_exactly",
        "provenance_archive_noindex": "excluded",
        "future_private_backlog": "excluded",
        "static_routes": "frozen_exact_allowlist",
        "require_http_200": True,
        "require_indexable": True,
        "require_exactly_one_self_canonical": True,
    }
    if sitemap_contract != expected_sitemap:
        add_violation(violations, "public sitemap admission contract is incomplete or unsupported")


def validate_public_invocations(contract: dict[str, Any], violations: list[str]) -> None:
    public_release = contract.get("public_release") or {}
    forbid_full_switch = (
        public_release.get("allow_package_include_full_transcripts_switch") is False
        and public_release.get("allow_deploy_include_full_transcripts_switch") is False
    )
    forbid_auto_promote = public_release.get("allow_implicit_auto_promote_insights") is False

    for rel_path in contract.get("public_invocation_scripts") or []:
        path = ROOT / rel_path
        if not path.exists():
            add_violation(violations, f"public invocation script missing: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        if forbid_full_switch and ("IncludeFullTranscripts" in text or "--include-full-transcripts" in text):
            add_violation(violations, f"{rel_path} exposes full-transcript public release path")
        if forbid_auto_promote and "--auto-promote-insights" in text:
            add_violation(violations, f"{rel_path} uses implicit public insight auto-promotion")


def validate_generated_git_boundary(contract: dict[str, Any], violations: list[str]) -> None:
    tracked = git_ls_files(contract.get("generated_artifacts_not_committed") or [])
    if tracked:
        add_violation(violations, f"generated/private artifacts are tracked by git: {tracked[:10]}")


def validate_export_dir(contract: dict[str, Any], export_dir: Path, violations: list[str]) -> None:
    public_release = contract.get("public_release") or {}
    manifest_path = export_dir / "manifest.json"
    if not manifest_path.exists():
        add_violation(violations, f"missing export manifest: {manifest_path}")
        return

    manifest = read_json(manifest_path)
    for manifest_issue in validate_public_dataset_manifest(manifest):
        add_violation(
            violations,
            f"public dataset manifest {manifest_issue['pointer']}: {manifest_issue['reason']}",
        )
    if manifest.get("include_full_transcripts") is not False:
        add_violation(violations, f"{export_dir} has include_full_transcripts enabled")
    if public_release.get("allow_implicit_auto_promote_insights") is False and manifest.get("auto_promote_insights"):
        add_violation(violations, f"{export_dir} has auto_promote_insights enabled")

    source_records = read_jsonl(export_dir / "source_records.jsonl")
    insight_cards = read_jsonl(export_dir / "insight_cards.jsonl")
    if not source_records:
        add_violation(violations, f"{export_dir} source_records.jsonl is empty or missing")
    if not insight_cards:
        add_violation(violations, f"{export_dir} insight_cards.jsonl is empty or missing")

    for row in source_records:
        source_id = row.get("source_id") or row.get("item_id") or "<unknown>"
        if row.get("transcript"):
            add_violation(violations, f"full transcript leaked in source record: {source_id}")
        if row.get("full_transcript_public"):
            add_violation(violations, f"source marked full_transcript_public in public lane: {source_id}")
        if "claims" in row:
            add_violation(violations, f"source record includes raw claims field: {source_id}")

    allowed_statuses = set(public_release.get("allowed_public_insight_review_statuses") or [])
    allowed_methods = set(public_release.get("allowed_public_insight_promotion_methods") or [])
    for row in insight_cards:
        if not row.get("public"):
            continue
        insight_id = row.get("id") or row.get("claim_id") or "<unknown>"
        review_status = row.get("review_status") or ""
        promotion_method = row.get("promotion_method") or ""
        if review_status not in allowed_statuses:
            add_violation(
                violations,
                f"public insight is not explicitly reviewed: {insight_id} review_status={review_status!r}",
            )
        if promotion_method not in allowed_methods:
            add_violation(
                violations,
                f"public insight has forbidden promotion method: {insight_id} promotion_method={promotion_method!r}",
            )
        if not row.get("evidence_excerpt"):
            add_violation(violations, f"public insight missing evidence_excerpt: {insight_id}")


def validate_count_floor(
    contract: dict[str, Any],
    export_dir: Path,
    baseline_export_dir: Path | None,
    violations: list[str],
) -> None:
    if baseline_export_dir is None or not baseline_export_dir.exists():
        return
    public_release = contract.get("public_release") or {}
    ratio = float(public_release.get("minimum_public_insight_retention_ratio") or 0)
    if ratio <= 0:
        return

    baseline = public_insight_count(baseline_export_dir)
    candidate = public_insight_count(export_dir)
    if baseline >= 100 and candidate < int(baseline * ratio):
        add_violation(
            violations,
            (
                "candidate export would drop public insight cards below the retention floor: "
                f"baseline={baseline}, candidate={candidate}, floor_ratio={ratio}. "
                "Run a reviewed legacy-card migration or lower the floor in the contract deliberately."
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Base2026 public release contract.")
    parser.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "contracts" / "base2026.public-release-contract.json",
    )
    parser.add_argument("--export-dir", type=Path)
    parser.add_argument("--baseline-export-dir", type=Path)
    parser.add_argument("--enforce-count-floor", action="store_true")
    parser.add_argument("--max-violations", type=int, default=50)
    args = parser.parse_args()

    contract_path = args.contract.resolve()
    contract = read_json(contract_path)
    violations: list[str] = []

    validate_contract_shape(contract, violations)
    validate_public_invocations(contract, violations)
    validate_generated_git_boundary(contract, violations)
    if args.export_dir:
        export_dir = args.export_dir.resolve()
        validate_export_dir(contract, export_dir, violations)
        if args.enforce_count_floor:
            baseline = args.baseline_export_dir.resolve() if args.baseline_export_dir else None
            validate_count_floor(contract, export_dir, baseline, violations)

    shown_violations = violations
    if args.max_violations >= 0 and len(violations) > args.max_violations:
        shown_violations = violations[: args.max_violations]
        shown_violations.append(f"... {len(violations) - args.max_violations} more violation(s)")

    summary = {
        "ok": not violations,
        "contract": str(contract_path.relative_to(ROOT)),
        "export_dir": str(args.export_dir) if args.export_dir else None,
        "violation_count": len(violations),
        "violations": shown_violations,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
