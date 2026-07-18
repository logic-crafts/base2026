#!/usr/bin/env python3
"""Derive the bounded Phase 0 P1 preview from the exact immutable R6 ZIP.

This derivation does not rebuild or re-export the corpus.  It changes only the
two public manifest families, sitemap artifacts, and hash-bound release
metadata needed to describe those changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from public_manifest_contract import (
    PUBLIC_DATASET_MANIFEST_SCHEMA,
    PUBLIC_PAGE_MANIFEST_SCHEMA,
    machine_local_value_issues,
    private_value_issues,
    validate_public_dataset_manifest,
    validate_public_page_manifest,
)


BASE_RELEASE = "base2026-whole-corpus-stitch-v1-preview-r6-20260715-174000"
BASE_ZIP_SHA256 = "9e4d7277900649dd35a39d47838989ee8eaefe9b71a0b8d23731b3d39227eed3"
PACKAGE_SCHEMA = "base2026.public-hotfix-from-export/v4"
DERIVATION_SCHEMA = "base2026.phase0-p1-r6-derivation/v1"
RECEIPT_NAME = "BASE2026_PHASE0_P1_DERIVATION.json"
VALIDATION_NAME = "BASE2026_PHASE0_P1_VALIDATION.json"
RELEASE_RE = re.compile(r"^[A-Za-z0-9._-]+-20260717-\d{6}$")
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

REQUIRED_BASE_FILES = {
    "manifest.json",
    "RELEASE.txt",
    "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json",
    "public-data/tiktok/manifest.json",
    "web/manifest.json",
    "web/static/manifest.json",
    "web/sitemap.xml",
}
REQUIRED_CHANGED_FILES = {
    "manifest.json",
    "RELEASE.txt",
    RECEIPT_NAME,
    VALIDATION_NAME,
    "SITEMAP_STATIC_ADMISSION.json",
    "SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json",
    "public-data/tiktok/manifest.json",
    "web/manifest.json",
    "web/static/manifest.json",
    "web/sitemap.xml",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    }


def safe_extract(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            rel = Path(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if rel.is_absolute() or ".." in rel.parts or mode == stat.S_IFLNK:
                raise RuntimeError("Immutable base ZIP contains an unsafe entry")
        archive.extractall(destination)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_deterministic_zip(source_root: Path, zip_path: Path) -> None:
    fixed_time = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(candidate for candidate in source_root.rglob("*") if candidate.is_file()):
            info = zipfile.ZipInfo(path.relative_to(source_root).as_posix(), fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sanitized_dataset_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Dataset manifest is not an object")
    payload.pop("source_admission_ledger", None)
    payload.pop("source_db", None)
    payload["schema"] = PUBLIC_DATASET_MANIFEST_SCHEMA
    issues = validate_public_dataset_manifest(payload)
    if issues:
        raise RuntimeError(f"Dataset manifest contract failed: {issues}")
    return payload


def relative_page_manifest(path: Path, web_root: Path) -> dict[str, Any]:
    original = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(original, dict) or not isinstance(original.get("pages"), list):
        raise RuntimeError("Page manifest is not an object with pages")
    pages: list[str] = []
    for value in original["pages"]:
        if not isinstance(value, str):
            raise RuntimeError("Page manifest route is not a string")
        normalized = value.replace("\\", "/")
        marker = "/web/"
        if marker not in normalized:
            raise RuntimeError("Legacy page manifest route has no web-root boundary")
        route = normalized.rsplit(marker, 1)[1]
        pages.append(route)
    payload = {
        "schema": PUBLIC_PAGE_MANIFEST_SCHEMA,
        "style_version": original.get("style_version"),
        "page_count": len(pages),
        "pages": pages,
    }
    issues = validate_public_page_manifest(payload, web_root=web_root)
    if issues:
        raise RuntimeError(f"Page manifest contract failed: {issues}")
    return payload


def sanitized_source_detail_validation(path: Path) -> dict[str, Any]:
    """Keep the inherited receipt useful without preserving machine-local paths."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "candidate" not in payload or "web_root" not in payload:
        raise RuntimeError("Source Detail package validation receipt is incomplete")
    payload["candidate"] = "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json"
    payload["web_root"] = "web"
    issues = private_value_issues(payload)
    if issues:
        raise RuntimeError(f"Source Detail package validation receipt still contains private path shapes: {issues}")
    return payload


def package_json_private_path_issues(root: Path) -> tuple[int, list[dict[str, str]]]:
    """Audit every JSON artifact without exposing any rejected value."""

    findings: list[dict[str, str]] = []
    json_paths = sorted(root.rglob("*.json"))
    for path in json_paths:
        relative_path = path.relative_to(root).as_posix()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            findings.append(
                {"file": relative_path, "pointer": "/", "reason": "json_parse_error"}
            )
            continue
        for issue_item in machine_local_value_issues(payload):
            findings.append({"file": relative_path, **issue_item})
    return len(json_paths), findings


def sitemap_counts(index_path: Path) -> tuple[int, int]:
    root = ET.parse(index_path).getroot()
    locations = [
        (node.text or "").strip()
        for node in root.findall(f"{{{SITEMAP_NS}}}sitemap/{{{SITEMAP_NS}}}loc")
    ]
    count = 0
    for location in locations:
        name = location.rsplit("/", 1)[-1]
        child = index_path.parent / "sitemaps" / name
        child_root = ET.parse(child).getroot()
        count += len(child_root.findall(f"{{{SITEMAP_NS}}}url"))
    return count, len(locations)


def run_checked(command: list[str], repo_root: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=repo_root, env=environment, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-zip", required=True, type=Path)
    parser.add_argument("--release-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--static-admission-manifest",
        type=Path,
        default=Path("contracts/base2026-sitemap-static-routes.json"),
    )
    args = parser.parse_args()

    if not RELEASE_RE.fullmatch(args.release_name):
        raise SystemExit("Release name must be safe and end with 20260717-HHMMSS")

    repo_root = Path(__file__).resolve().parents[1]
    base_zip = args.base_zip.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    static_contract = args.static_admission_manifest.expanduser()
    if not static_contract.is_absolute():
        static_contract = (repo_root / static_contract).resolve()
    release_root = output_dir / args.release_name
    zip_path = output_dir / f"{args.release_name}.zip"

    if not base_zip.is_file() or sha256_file(base_zip) != BASE_ZIP_SHA256:
        raise SystemExit("Immutable R6 ZIP is missing or its SHA-256 does not match the Phase 0 authority")
    if release_root.exists() or zip_path.exists():
        raise SystemExit("Preview target already exists")
    static_payload = json.loads(static_contract.read_text(encoding="utf-8"))
    if (
        static_payload.get("source_release") != BASE_RELEASE
        or static_payload.get("source_release_zip_sha256") != BASE_ZIP_SHA256
    ):
        raise SystemExit("Static admission contract is not bound to the exact immutable R6 release")

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="base2026-phase0-p1-", dir=output_dir) as temp_dir:
        temp = Path(temp_dir)
        extracted = temp / "release"
        safe_extract(base_zip, extracted)
        before = snapshot(extracted)
        missing = sorted(REQUIRED_BASE_FILES - set(before))
        if missing:
            raise RuntimeError(f"Immutable R6 release misses required inputs: {missing}")

        package_path = extracted / "manifest.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("release_name") != BASE_RELEASE:
            raise RuntimeError("Immutable R6 package identity does not match the Phase 0 authority")

        dataset = sanitized_dataset_manifest(extracted / "public-data/tiktok/manifest.json")
        write_json(extracted / "public-data/tiktok/manifest.json", dataset)
        write_json(extracted / "web/static/manifest.json", dataset)
        pages = relative_page_manifest(extracted / "web/manifest.json", extracted / "web")
        write_json(extracted / "web/manifest.json", pages)
        source_detail_validation_path = extracted / "SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json"
        write_json(
            source_detail_validation_path,
            sanitized_source_detail_validation(source_detail_validation_path),
        )
        shutil.copyfile(static_contract, extracted / "SITEMAP_STATIC_ADMISSION.json")

        lastmod = "2026-07-17"
        sitemap_command = [
            sys.executable,
            str(repo_root / "scripts/generate-base2026-sitemap.py"),
            "--web-root",
            str(extracted / "web"),
            "--source-detail-manifest",
            str(extracted / "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json"),
            "--static-admission-manifest",
            str(extracted / "SITEMAP_STATIC_ADMISSION.json"),
            "--lastmod",
            lastmod,
        ]
        run_checked(sitemap_command, repo_root)
        url_count, child_count = sitemap_counts(extracted / "web/sitemap.xml")
        if (url_count, child_count) != (1734, 5):
            raise RuntimeError("R6 Phase 0 sitemap cohort is not exactly 1,734 URLs in five children")

        package["schema"] = PACKAGE_SCHEMA
        package["release_name"] = args.release_name
        package["package_mode"] = "data-preserving-static-derived-phase0-p1-r6-preview"
        package["source_export_manifest_sha256"] = sha256_file(
            extracted / "public-data/tiktok/manifest.json"
        )
        source_detail = package.get("source_detail")
        if not isinstance(source_detail, dict):
            raise RuntimeError("R6 package has no Source Detail contract")
        source_detail["archive_sitemap_policy"] = "excluded"
        source_detail["future_private_sitemap_policy"] = "excluded"
        source_detail["source_sitemap_admission"] = "exact"
        package["sitemap_contract"] = {
            "schema": "base2026.sitemap-admission/v2",
            "static_admission_manifest_sha256": sha256_file(static_contract),
            "static_admission_policy": "frozen_exact_allowlist",
            "source_admission_policy": "exact",
            "archive_noindex_policy": "excluded",
            "future_private_policy": "excluded",
            "global_exact_admission": True,
        }
        package["required_contract_files"] = [
            "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json",
            "SITEMAP_STATIC_ADMISSION.json",
            RECEIPT_NAME,
            VALIDATION_NAME,
        ]
        runtime = package.get("required_runtime_files")
        if not isinstance(runtime, list):
            raise RuntimeError("R6 package required_runtime_files is not an array")
        for required in (
            "web/manifest.json",
            "web/static/manifest.json",
            "public-data/tiktok/manifest.json",
        ):
            if required not in runtime:
                runtime.append(required)
        package["phase0_p1_overlay"] = {
            "schema": DERIVATION_SCHEMA,
            "base_release": BASE_RELEASE,
            "base_zip_sha256": BASE_ZIP_SHA256,
            "corpus_reexported": False,
            "meilisearch_reindexed": False,
            "wordpress_root_mutation": False,
            "sitemap_urls": url_count,
            "normal_source_urls": 1493,
            "static_urls": 241,
            "archive_noindex_excluded": 199,
            "future_private_excluded": 135,
        }
        write_json(package_path, package)
        (extracted / "RELEASE.txt").write_text(
            "\n".join(
                (
                    args.release_name,
                    f"Derived without corpus re-export from {BASE_RELEASE}",
                    f"Immutable base ZIP SHA-256 {BASE_ZIP_SHA256}",
                    "Phase 0 P1: public manifests allowlisted; sitemap exact at 1,734 URLs.",
                    "Preview only. No production deployment authorization.",
                    "",
                )
            ),
            encoding="utf-8",
        )
        receipt = {
            "schema": DERIVATION_SCHEMA,
            "release_name": args.release_name,
            "base_release": BASE_RELEASE,
            "base_zip_sha256": BASE_ZIP_SHA256,
            "static_admission_manifest_sha256": sha256_file(static_contract),
            "corpus_reexported": False,
            "sitemap": {
                "urls": url_count,
                "children": child_count,
                "normal_source_urls": 1493,
                "static_urls": 241,
                "archive_noindex_excluded": 199,
                "future_private_excluded": 135,
                "global_exact_admission": True,
            },
            "public_manifests": {
                "dataset_schema": PUBLIC_DATASET_MANIFEST_SCHEMA,
                "page_schema": PUBLIC_PAGE_MANIFEST_SCHEMA,
                "dataset_mirrors_identical": True,
                "private_paths_rejected": True,
            },
            "release_metadata": {
                "source_detail_validation_paths_sanitized": True,
                "package_json_machine_local_path_issue_count": 0,
            },
            "production_mutated": False,
        }
        write_json(extracted / RECEIPT_NAME, receipt)

        validate_command = [
            sys.executable,
            str(repo_root / "scripts/validate-public-manifests.py"),
            "--dataset-manifest",
            str(extracted / "public-data/tiktok/manifest.json"),
            "--dataset-manifest",
            str(extracted / "web/static/manifest.json"),
            "--page-manifest",
            str(extracted / "web/manifest.json"),
            "--web-root",
            str(extracted / "web"),
        ]
        run_checked(validate_command, repo_root)
        run_checked([*sitemap_command, "--check-only"], repo_root)
        sitemap_children = sorted((extracted / "web/sitemaps").glob("base2026-*.xml"))
        validation = {
            "schema": "base2026.phase0-p1-r6-validation/v1",
            "release_name": args.release_name,
            "base_zip_sha256": BASE_ZIP_SHA256,
            "public_manifests": {
                "issue_count": 0,
                "dataset_mirrors_identical": (
                    (extracted / "public-data/tiktok/manifest.json").read_bytes()
                    == (extracted / "web/static/manifest.json").read_bytes()
                ),
                "public_data_manifest_sha256": sha256_file(
                    extracted / "public-data/tiktok/manifest.json"
                ),
                "web_static_manifest_sha256": sha256_file(extracted / "web/static/manifest.json"),
                "page_manifest_sha256": sha256_file(extracted / "web/manifest.json"),
            },
            "release_metadata": {
                "source_detail_validation_paths_sanitized": True,
                "source_detail_validation_sha256": sha256_file(
                    extracted / "SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json"
                ),
                "package_json_machine_local_path_issue_count": 0,
            },
            "sitemap": {
                "index_sha256": sha256_file(extracted / "web/sitemap.xml"),
                "child_sha256": {
                    child.name: sha256_file(child) for child in sitemap_children
                },
                "urls": url_count,
                "children": child_count,
                "normal_source_urls": 1493,
                "static_urls": 241,
                "archive_urls": 0,
                "future_private_urls": 0,
                "unapproved_urls": 0,
                "global_exact_admission": True,
                "check_only_passed": True,
            },
            "corpus_reexported": False,
            "production_mutated": False,
        }
        if not validation["public_manifests"]["dataset_mirrors_identical"]:
            raise RuntimeError("Validated public dataset manifest mirrors are not byte-identical")
        write_json(extracted / VALIDATION_NAME, validation)

        json_files_scanned, package_path_issues = package_json_private_path_issues(extracted)
        if package_path_issues:
            raise RuntimeError(
                "Package-wide JSON machine-local path audit failed: "
                + json.dumps(package_path_issues, sort_keys=True)
            )
        receipt["release_metadata"]["package_json_files_scanned"] = json_files_scanned
        validation["release_metadata"]["package_json_files_scanned"] = json_files_scanned
        write_json(extracted / RECEIPT_NAME, receipt)
        write_json(extracted / VALIDATION_NAME, validation)
        final_json_files_scanned, final_package_path_issues = package_json_private_path_issues(
            extracted
        )
        if final_json_files_scanned != json_files_scanned or final_package_path_issues:
            raise RuntimeError(
                "Final package-wide JSON machine-local path audit failed: "
                + json.dumps(final_package_path_issues, sort_keys=True)
            )

        after = snapshot(extracted)
        deleted = set(before) - set(after)
        changed = {
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        }
        allowed = REQUIRED_CHANGED_FILES | {
            path for path in changed if re.fullmatch(r"web/sitemaps/base2026-\d{3}\.xml", path)
        }
        if deleted or not REQUIRED_CHANGED_FILES <= changed or changed - allowed:
            raise RuntimeError(
                "Phase 0 overlay changed files outside the bounded allowlist: "
                f"deleted={len(deleted)}, missing_required={len(REQUIRED_CHANGED_FILES - changed)}, "
                f"unexpected={len(changed - allowed)}"
            )

        staged_release = temp / args.release_name
        extracted.rename(staged_release)
        staged_zip = temp / f"{args.release_name}.zip"
        write_deterministic_zip(staged_release, staged_zip)
        shutil.move(str(staged_release), release_root)
        shutil.move(str(staged_zip), zip_path)

    print(
        json.dumps(
            {
                "schema": DERIVATION_SCHEMA,
                "release_name": args.release_name,
                "zip_sha256": sha256_file(zip_path),
                "sitemap_urls": 1734,
                "sitemap_children": 5,
                "corpus_reexported": False,
                "production_mutated": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
