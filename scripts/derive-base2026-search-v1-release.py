#!/usr/bin/env python3
"""Derive a Base2026 Search V1 release from an immutable deployed package.

The derivation is deliberately data-preserving: it refuses any corpus, sitemap,
source-detail, or public-data change. Only the Search entry shell/assets, two
legacy search compatibility entries, release metadata, and a derivation receipt
may differ from the verified base ZIP.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

SCHEMA = "base2026.search-v1-derived-release/v1"
PACKAGE_SCHEMA = "base2026.public-hotfix-from-export/v3"
RELEASE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
RELEASE_TIMESTAMP_RE = re.compile(r"(\d{8})-(\d{6})$")

ALLOWED_CHANGED = {
    "manifest.json",
    "RELEASE.txt",
    "BASE2026_SEARCH_V1_DERIVATION.json",
    "web/index.html",
    "web/search.html",
    "web/search/index.html",
    "web/static/alex-v4-static-shell.css",
    "web/static/base2026-search-v1.css",
    "web/static/base2026-search-v3.js",
    "web/static/meili.js",
}
REQUIRED_CHANGED = {
    "manifest.json",
    "RELEASE.txt",
    "BASE2026_SEARCH_V1_DERIVATION.json",
    "web/index.html",
    "web/search.html",
    "web/search/index.html",
    "web/static/base2026-search-v1.css",
    "web/static/base2026-search-v3.js",
    "web/static/meili.js",
}
REQUIRED_BASE_FILES = {
    "manifest.json",
    "RELEASE.txt",
    "web/index.html",
    "web/sources/index.html",
    "web/sitemap.xml",
    "web/static/styles.css",
    "public-data/tiktok/manifest.json",
    "public-data/tiktok/source_records.jsonl",
}
SEARCH_ASSETS = (
    "alex-v4-static-shell.css",
    "base2026-search-v1.css",
    "base2026-search-v3.js",
    "meili.js",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        result[path.relative_to(root).as_posix()] = sha256_file(path)
    return result


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
        raise ValueError("Release name must end with YYYYMMDD-HHMMSS for deterministic receipts")
    parsed = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def safe_extract(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            rel = Path(info.filename)
            if rel.is_absolute() or ".." in rel.parts:
                raise RuntimeError(f"Unsafe ZIP entry: {info.filename}")
        archive.extractall(destination)


def cache_bust_search_html(html: str, release_name: str) -> str:
    asset_names = (
        "styles.css",
        "alex-v4-static-shell.css",
        "base2026-search-v1.css",
        "cookie-consent.js",
        "meili.js",
        "alex-v4-static-shell.js",
        "base2026-search-v3.js",
    )
    names = "|".join(re.escape(name) for name in asset_names)
    pattern = re.compile(rf"(\./static/(?:{names}))\?v=[^\"']+")
    return pattern.sub(lambda match: f"{match.group(1)}?v={release_name}", html)


def search_alias_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <meta name=\"robots\" content=\"noindex,follow\">
  <link rel=\"canonical\" href=\"https://aggressorbulkit.online/knowledge/\">
  <title>Base2026 Search</title>
  <script>location.replace('/knowledge/' + location.search + location.hash);</script>
</head>
<body><p>Continue to <a href=\"/knowledge/\">Base2026 Search</a>.</p></body>
</html>
"""


def write_deterministic_zip(source_root: Path, zip_path: Path) -> None:
    fixed_time = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
            rel = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(rel, fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-zip", required=True, type=Path)
    parser.add_argument("--expected-base-sha256", required=True)
    parser.add_argument("--release-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    if not RELEASE_RE.fullmatch(args.release_name):
        raise SystemExit(f"Unsafe release name: {args.release_name}")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_base_sha256):
        raise SystemExit("Expected base SHA256 must be 64 hexadecimal characters")

    base_zip = args.base_zip.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    release_root = output_dir / args.release_name
    zip_path = output_dir / f"{args.release_name}.zip"
    if not base_zip.is_file():
        raise SystemExit(f"Base ZIP not found: {base_zip}")
    actual_base_sha = sha256_file(base_zip)
    if actual_base_sha != args.expected_base_sha256.lower():
        raise SystemExit(
            f"Immutable base mismatch: expected {args.expected_base_sha256.lower()}, got {actual_base_sha}"
        )
    if release_root.exists() or zip_path.exists():
        raise SystemExit(f"Derived release target already exists: {release_root} or {zip_path}")

    script_dir = Path(__file__).resolve().parent
    generator = script_dir / "generate-base2026-search-v1.py"
    if not generator.is_file():
        raise SystemExit(f"Search generator missing: {generator}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="base2026-search-v1-derive-") as temp_dir:
        temp = Path(temp_dir)
        extracted = temp / "release"
        safe_extract(base_zip, extracted)
        before = snapshot(extracted)
        missing = sorted(REQUIRED_BASE_FILES - before.keys())
        if missing:
            raise RuntimeError(f"Base artifact misses required files: {missing}")

        manifest_path = extracted / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != PACKAGE_SCHEMA:
            raise RuntimeError(f"Unsupported base package schema: {manifest.get('schema')}")
        base_release_name = str(manifest.get("release_name", ""))
        if not base_release_name:
            raise RuntimeError("Base package manifest has no release_name")

        web_root = extracted / "web"
        overlay = temp / "overlay"
        subprocess.run(
            [
                sys.executable,
                str(generator),
                "--source-root",
                str(web_root),
                "--out",
                str(overlay),
            ],
            check=True,
        )

        overlay_html = cache_bust_search_html(
            (overlay / "index.html").read_text(encoding="utf-8"), args.release_name
        )
        required_markers = (
            'body class="ay-alex-v4-static base2026-search-v1"',
            "./static/base2026-search-v1.css?v=",
            "./static/base2026-search-v3.js?v=",
            'rel="canonical" href="https://aggressorbulkit.online/knowledge/"',
        )
        absent = [marker for marker in required_markers if marker not in overlay_html]
        if absent:
            raise RuntimeError(f"Generated Search HTML misses required markers: {absent}")
        (web_root / "index.html").write_text(overlay_html, encoding="utf-8")

        static_root = web_root / "static"
        static_root.mkdir(parents=True, exist_ok=True)
        runtime_source = script_dir.parent / "web" / "static" / "meili.js"
        if not runtime_source.is_file():
            raise RuntimeError(f"Canonical Search runtime missing: {runtime_source}")
        shutil.copy2(runtime_source, overlay / "meili.js")
        for asset in SEARCH_ASSETS:
            source = overlay / asset
            if not source.is_file():
                raise RuntimeError(f"Generated Search asset missing: {source}")
            shutil.copy2(source, static_root / asset)

        alias = search_alias_html()
        alias_dir = web_root / "search"
        alias_dir.mkdir(parents=True, exist_ok=True)
        (alias_dir / "index.html").write_text(alias, encoding="utf-8")
        (web_root / "search.html").write_text(alias, encoding="utf-8")

        manifest["release_name"] = args.release_name
        manifest["package_mode"] = "data-preserving-static-derived-search-release"
        manifest["derived_from"] = {
            "release_name": base_release_name,
            "zip_sha256": actual_base_sha,
            "policy": "search-shell-assets-and-compatibility-route-only",
            "corpus_reexported": False,
            "meilisearch_reindexed": False,
            "wordpress_root_mutation": False,
        }
        required_runtime = list(manifest.get("required_runtime_files") or [])
        for required in (
            "web/static/base2026-search-v1.css",
            "web/static/base2026-search-v3.js",
            "web/static/meili.js",
            "web/search/index.html",
        ):
            if required not in required_runtime:
                required_runtime.append(required)
        manifest["required_runtime_files"] = required_runtime
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (extracted / "RELEASE.txt").write_text(
            f"{args.release_name}\nDerived from {base_release_name}\nBase ZIP SHA256 {actual_base_sha}\n",
            encoding="utf-8",
        )

        interim = snapshot(extracted)
        changed_without_receipt = {
            rel for rel in set(before) | set(interim) if before.get(rel) != interim.get(rel)
        }
        unexpected = sorted(changed_without_receipt - (ALLOWED_CHANGED - {"BASE2026_SEARCH_V1_DERIVATION.json"}))
        if unexpected:
            raise RuntimeError(f"Derivation changed forbidden paths: {unexpected}")

        unchanged = {
            rel: file_hash
            for rel, file_hash in interim.items()
            if rel not in changed_without_receipt
        }
        receipt = {
            "schema": SCHEMA,
            "created_at": deterministic_release_timestamp(args.release_name),
            "release_name": args.release_name,
            "base_release_name": base_release_name,
            "base_zip_sha256": actual_base_sha,
            "changed_paths": sorted(changed_without_receipt | {"BASE2026_SEARCH_V1_DERIVATION.json"}),
            "unchanged_files": len(unchanged),
            "unchanged_tree_digest": digest_snapshot(unchanged),
            "corpus_reexported": False,
            "meilisearch_reindexed": False,
            "wordpress_root_mutation": False,
            "sitemap_sha256": interim["web/sitemap.xml"],
            "public_data_manifest_sha256": interim["public-data/tiktok/manifest.json"],
            "source_records_sha256": interim["public-data/tiktok/source_records.jsonl"],
            "search_contract": {
                "canonical": "https://aggressorbulkit.online/knowledge/",
                "query_url_format": "/knowledge/?q={query}",
                "legacy_routes": ["/knowledge/search/", "/knowledge/search.html"],
                "body_classes": ["ay-alex-v4-static", "base2026-search-v1"],
            },
        }
        receipt_path = extracted / "BASE2026_SEARCH_V1_DERIVATION.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

        final = snapshot(extracted)
        changed = {rel for rel in set(before) | set(final) if before.get(rel) != final.get(rel)}
        unexpected = sorted(changed - ALLOWED_CHANGED)
        missing_required = sorted(REQUIRED_CHANGED - changed)
        if unexpected or missing_required:
            raise RuntimeError(
                f"Derivation boundary failed: unexpected={unexpected}, missing_required={missing_required}"
            )
        if final["web/sitemap.xml"] != before["web/sitemap.xml"]:
            raise RuntimeError("Sitemap changed during Search-only derivation")
        for prefix in ("public-data/", "web/sources/", "web/static/sources/"):
            drift = [rel for rel in changed if rel.startswith(prefix)]
            if drift:
                raise RuntimeError(f"Protected tree changed under {prefix}: {drift[:10]}")

        shutil.move(str(extracted), str(release_root))

    write_deterministic_zip(release_root, zip_path)
    zip_sha = sha256_file(zip_path)
    print(json.dumps({
        "status": "PASS",
        "release_name": args.release_name,
        "release_root": str(release_root),
        "zip_path": str(zip_path),
        "zip_sha256": zip_sha,
        "base_zip_sha256": actual_base_sha,
        "changed_paths": sorted(ALLOWED_CHANGED),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
