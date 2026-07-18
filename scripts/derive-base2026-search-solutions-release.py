#!/usr/bin/env python3
"""Derive an immutable Search V1 + AI Recommends Solutions release.

The exact approved Search V1 ZIP is the immutable base. This derivation may only
add/replace the six generated Solutions routes, their stylesheet, release
metadata, and a hash-bound derivation receipt. Public data, sitemap, Search,
source-detail pages, and every other baseline file must remain byte-identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

SCHEMA = "base2026.search-solutions-derived-release/v1"
PACKAGE_SCHEMA = "base2026.public-hotfix-from-export/v4"
RELEASE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
RELEASE_TIMESTAMP_RE = re.compile(r"(\d{8})-(\d{6})$")

SOLUTION_ROUTES = (
    "solutions/index.html",
    "solutions/google-business-profile-visibility-audit.html",
    "solutions/search-console-high-impression-low-ctr.html",
    "solutions/measure-ai-search-visibility.html",
    "solutions/answer-ready-service-page-checklist.html",
    "solutions/content-refresh-prioritization.html",
)
SOLUTION_PAYLOADS = (*SOLUTION_ROUTES, "static/ai-recommends-solutions.css", "static/ai-recommends-solutions.js")
RECEIPT_NAME = "BASE2026_SEARCH_SOLUTIONS_DERIVATION.json"
ALLOWED_CHANGED = {
    "manifest.json",
    "RELEASE.txt",
    RECEIPT_NAME,
    *(f"web/{path}" for path in SOLUTION_PAYLOADS),
}
REQUIRED_BASE_FILES = {
    "manifest.json",
    "RELEASE.txt",
    "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json",
    "BASE2026_SEARCH_V1_DERIVATION.json",
    "web/index.html",
    "web/sources/index.html",
    "web/sitemap.xml",
    "web/static/styles.css",
    "web/static/base2026-search-v1.css",
    "web/static/base2026-search-v3.js",
    "public-data/tiktok/manifest.json",
    "public-data/tiktok/source_records.jsonl",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> Dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    }


def digest_snapshot(items: Dict[str, str]) -> str:
    digest = hashlib.sha256()
    for rel, file_hash in sorted(items.items()):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def deterministic_release_timestamp(release_name: str) -> str:
    match = RELEASE_TIMESTAMP_RE.search(release_name)
    if not match:
        raise ValueError("Release name must end with YYYYMMDD-HHMMSS")
    parsed = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def safe_extract(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            rel = Path(info.filename)
            if rel.is_absolute() or ".." in rel.parts:
                raise RuntimeError(f"Unsafe ZIP entry: {info.filename}")
        archive.extractall(destination)


def write_deterministic_zip(source_root: Path, zip_path: Path) -> None:
    fixed_time = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
            rel = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(rel, fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def cache_bust_html(html: str, release_name: str) -> str:
    assets = "|".join(
        re.escape(name)
        for name in (
            "alex-v4-static-shell.css",
            "alex-v4-static-shell.js",
            "ai-recommends-solutions.css",
            "ai-recommends-solutions.js",
        )
    )
    pattern = re.compile(rf'((?:href|src)="[^"]*(?:{assets}))\?v=[^"]*(")', re.IGNORECASE)
    return pattern.sub(lambda match: f"{match.group(1)}?v={release_name}{match.group(2)}", html)


def generated_payload_snapshot(root: Path, release_name: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for rel in SOLUTION_PAYLOADS:
        generated_rel = rel.removeprefix("static/") if rel.startswith("static/ai-recommends-solutions.") else rel
        source = root / generated_rel
        if not source.is_file():
            raise RuntimeError(f"Generated Solutions payload is missing: {source}")
        if rel.endswith(".html"):
            data = cache_bust_html(source.read_text(encoding="utf-8"), release_name).encode("utf-8")
        else:
            data = source.read_bytes()
        result[rel] = hashlib.sha256(data).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-zip", required=True, type=Path)
    parser.add_argument("--expected-base-sha256", required=True)
    parser.add_argument("--release-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--solutions-input",
        type=Path,
        default=Path("data/base2026_ai_recommends_solutions_pilot.json"),
    )
    args = parser.parse_args()

    if not RELEASE_RE.fullmatch(args.release_name):
        raise SystemExit(f"Unsafe release name: {args.release_name}")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_base_sha256):
        raise SystemExit("Expected base SHA256 must be 64 hexadecimal characters")

    repo_root = Path(__file__).resolve().parents[1]
    base_zip = args.base_zip.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    solutions_input = args.solutions_input.expanduser()
    if not solutions_input.is_absolute():
        solutions_input = (repo_root / solutions_input).resolve()
    release_root = output_dir / args.release_name
    zip_path = output_dir / f"{args.release_name}.zip"

    if not base_zip.is_file():
        raise SystemExit(f"Base ZIP not found: {base_zip}")
    actual_base_sha = sha256_file(base_zip)
    if actual_base_sha != args.expected_base_sha256.lower():
        raise SystemExit(
            f"Immutable Search base mismatch: expected {args.expected_base_sha256.lower()}, got {actual_base_sha}"
        )
    if not solutions_input.is_file():
        raise SystemExit(f"Solutions input not found: {solutions_input}")
    if release_root.exists() or zip_path.exists():
        raise SystemExit(f"Derived release target already exists: {release_root} or {zip_path}")

    generator = repo_root / "scripts/generate-ai-recommends-solutions.py"
    validator = repo_root / "scripts/validate-ai-recommends-solutions.py"
    html_validator = repo_root / "scripts/validate-ai-recommends-html.py"
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="base2026-search-solutions-derive-") as temp_dir:
        temp = Path(temp_dir)
        extracted = temp / "release"
        safe_extract(base_zip, extracted)
        before = snapshot(extracted)
        missing = sorted(REQUIRED_BASE_FILES - before.keys())
        if missing:
            raise RuntimeError(f"Search base misses required files: {missing}")

        manifest_path = extracted / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != PACKAGE_SCHEMA:
            raise RuntimeError(f"Unsupported base package schema: {manifest.get('schema')}")
        base_search_release = str(manifest.get("release_name") or "")
        if not base_search_release.startswith("base2026-search-v1-"):
            raise RuntimeError(f"Unexpected immutable Search base release: {base_search_release}")
        if manifest.get("package_mode") != "data-preserving-static-derived-search-release":
            raise RuntimeError(f"Unexpected Search base package mode: {manifest.get('package_mode')}")

        data_root = extracted / "public-data/tiktok"
        validation_report = temp / "solutions-validation.json"
        subprocess.run(
            [
                sys.executable,
                str(validator),
                "--input",
                str(solutions_input),
                "--data-root",
                str(data_root),
                "--report",
                str(validation_report),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        generated_roots = []
        generation_reports = []
        for label in ("a", "b"):
            generated = temp / f"generated-{label}"
            report = temp / f"generation-{label}.json"
            subprocess.run(
                [
                    sys.executable,
                    str(generator),
                    "--input",
                    str(solutions_input),
                    "--data-root",
                    str(data_root),
                    "--out",
                    str(generated),
                    "--report",
                    str(report),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            generated_roots.append(generated)
            generation_reports.append(report)

        generated_a = generated_payload_snapshot(generated_roots[0], args.release_name)
        generated_b = generated_payload_snapshot(generated_roots[1], args.release_name)
        if generated_a != generated_b:
            raise RuntimeError("Solutions generation is not deterministic")

        web_root = extracted / "web"
        for rel in SOLUTION_ROUTES:
            source = generated_roots[0] / rel
            target = web_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                cache_bust_html(source.read_text(encoding="utf-8"), args.release_name),
                encoding="utf-8",
            )
        for asset_name in ("ai-recommends-solutions.css", "ai-recommends-solutions.js"):
            asset_target = web_root / "static" / asset_name
            asset_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(generated_roots[0] / asset_name, asset_target)

        html_report = temp / "solutions-html-validation.json"
        subprocess.run(
            [
                sys.executable,
                str(html_validator),
                "--out",
                str(web_root),
                "--generation-report",
                str(generation_reports[0]),
                "--report",
                str(html_report),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        solutions_input_sha = sha256_file(solutions_input)
        generator_sha = sha256_file(generator)
        manifest["release_name"] = args.release_name
        manifest["package_mode"] = "data-preserving-static-derived-search-solutions-release"
        manifest["search_solutions_overlay"] = {
            "schema": SCHEMA,
            "base_search_release": base_search_release,
            "base_search_zip_sha256": actual_base_sha,
            "solutions_input_sha256": solutions_input_sha,
            "generator_sha256": generator_sha,
            "generated_payload_sha256": generated_a,
            "corpus_reexported": False,
            "meilisearch_reindexed": False,
            "wordpress_root_mutation": False,
            "sitemap_changed": False,
        }
        required_runtime = list(manifest.get("required_runtime_files") or [])
        for required in (f"web/{path}" for path in SOLUTION_PAYLOADS):
            if required not in required_runtime:
                required_runtime.append(required)
        manifest["required_runtime_files"] = required_runtime
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (extracted / "RELEASE.txt").write_text(
            f"{args.release_name}\n"
            f"Derived from {base_search_release}\n"
            f"Search base ZIP SHA256 {actual_base_sha}\n"
            f"Solutions input SHA256 {solutions_input_sha}\n",
            encoding="utf-8",
        )

        interim = snapshot(extracted)
        changed_without_receipt = {
            rel for rel in set(before) | set(interim) if before.get(rel) != interim.get(rel)
        }
        unexpected = sorted(changed_without_receipt - (ALLOWED_CHANGED - {RECEIPT_NAME}))
        if unexpected:
            raise RuntimeError(f"Derivation changed forbidden paths: {unexpected}")

        receipt = {
            "schema": SCHEMA,
            "created_at": deterministic_release_timestamp(args.release_name),
            "release_name": args.release_name,
            "base_search_release": base_search_release,
            "base_search_zip_sha256": actual_base_sha,
            "solutions_input": solutions_input.relative_to(repo_root).as_posix(),
            "solutions_input_sha256": solutions_input_sha,
            "generator_sha256": generator_sha,
            "changed_paths": sorted(changed_without_receipt | {RECEIPT_NAME}),
            "generated_payload_sha256": generated_a,
            "unchanged_files": len(before) - len(changed_without_receipt),
            "unchanged_tree_digest": digest_snapshot(
                {rel: digest for rel, digest in interim.items() if rel not in changed_without_receipt}
            ),
            "corpus_reexported": False,
            "meilisearch_reindexed": False,
            "wordpress_root_mutation": False,
            "indexnow_submitted": False,
            "sitemap_sha256": interim["web/sitemap.xml"],
            "public_data_manifest_sha256": interim["public-data/tiktok/manifest.json"],
            "source_records_sha256": interim["public-data/tiktok/source_records.jsonl"],
            "search_index_sha256": interim["web/index.html"],
            "search_runtime_sha256": interim["web/static/base2026-search-v3.js"],
        }
        (extracted / RECEIPT_NAME).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

        final = snapshot(extracted)
        changed = {rel for rel in set(before) | set(final) if before.get(rel) != final.get(rel)}
        unexpected = sorted(changed - ALLOWED_CHANGED)
        missing_required = sorted(ALLOWED_CHANGED - changed)
        if unexpected or missing_required:
            raise RuntimeError(
                f"Derivation boundary failed: unexpected={unexpected}, missing_required={missing_required}"
            )
        for protected in (
            "web/index.html",
            "web/sitemap.xml",
            "web/static/base2026-search-v1.css",
            "web/static/base2026-search-v3.js",
            "public-data/tiktok/manifest.json",
            "public-data/tiktok/source_records.jsonl",
        ):
            if final[protected] != before[protected]:
                raise RuntimeError(f"Protected Search/data path changed: {protected}")
        for prefix in ("public-data/", "web/sources/", "web/static/sources/"):
            drift = [rel for rel in changed if rel.startswith(prefix)]
            if drift:
                raise RuntimeError(f"Protected tree changed under {prefix}: {drift[:10]}")

        shutil.move(str(extracted), str(release_root))

    write_deterministic_zip(release_root, zip_path)
    result = {
        "status": "PASS",
        "release_name": args.release_name,
        "release_root": str(release_root),
        "zip_path": str(zip_path),
        "zip_sha256": sha256_file(zip_path),
        "base_search_zip_sha256": actual_base_sha,
        "changed_paths": sorted(ALLOWED_CHANGED),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
