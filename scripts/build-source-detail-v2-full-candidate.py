#!/usr/bin/env python3
"""Build a manifest-authoritative, isolated Source Detail V2 full-family candidate.

This deliberately never writes under web/static. It consumes the frozen route
inventory and emits only the 200 Source Detail routes to an explicitly supplied
planning directory; future-private routes are represented only in its manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from template_migration.source_detail import SourceSolution, adapt_source_detail, render_source_detail  # noqa: E402
from alex_v4_static_shell import shell_css, shell_js  # noqa: E402

RENDERER_VERSION = "source-detail-v2-interior-v1-20260718"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    source_rows = [row for row in rows if row.get("page_family") == "source_detail"]
    if not source_rows:
        raise ValueError("Route manifest has no source_detail rows")
    seen: set[str] = set()
    for row in source_rows:
        route = str(row.get("route") or "")
        if not route.startswith("sources/") or not route.endswith(".html"):
            raise ValueError(f"Invalid source_detail route in manifest: {route!r}")
        if route in seen:
            raise ValueError(f"Duplicate source_detail route in manifest: {route}")
        seen.add(route)
        if row.get("expected_status") not in (200, 404):
            raise ValueError(f"Unexpected expected_status for {route}: {row.get('expected_status')!r}")
    return sorted(source_rows, key=lambda row: str(row["route"]))


def safe_candidate_out(path: Path) -> Path:
    resolved = path.resolve()
    planning = (ROOT / ".planning").resolve()
    if planning not in (resolved, *resolved.parents):
        raise ValueError(f"Candidate output must be under {planning}, got {resolved}")
    if resolved.exists():
        raise FileExistsError(f"Refusing to overwrite existing candidate: {resolved}")
    return resolved


def copy_static_assets(out: Path, solution_journey_registry: Path | None = None) -> dict[str, str]:
    """Copy the deployed static layout required by Source Detail documents.

    Legacy source documents reference shell icons as ``../static/assets/...``.
    Those icons live in ``web/static/assets`` before packaging rather than in
    ``web/static/static``.  A candidate must reproduce their eventual deployed
    target under its own static directory, otherwise browser QA can pass only by
    accidentally reading canonical output outside the candidate root.
    """
    static_out = out / "static"
    legacy_static_seed = ROOT / "web" / "static" / "static"
    if legacy_static_seed.is_dir():
        shutil.copytree(legacy_static_seed, static_out)
    else:
        static_out.mkdir(parents=True)
    source_assets = ROOT / "web/static/assets"
    if not source_assets.is_dir():
        raise FileNotFoundError(f"Canonical shell asset directory is missing: {source_assets}")
    shutil.copytree(source_assets, static_out / "assets", dirs_exist_ok=True)
    replacements = {
        "source-detail-v2.css": SCRIPTS / "base2026_source_detail_v2.css",
        "source-detail-v2.js": SCRIPTS / "base2026_source_detail_v2.js",
        "base2026-interior-v1.css": ROOT / "web" / "static" / "base2026-interior-v1.css",
    }
    for name, source in replacements.items():
        shutil.copy2(source, static_out / name)
    vendor_source = ROOT / "web" / "static" / "vendor"
    if not vendor_source.is_dir():
        raise FileNotFoundError(f"Canonical local-font directory is missing: {vendor_source}")
    font_assets = sorted(
        path for path in vendor_source.iterdir()
        if path.is_file() and path.name.startswith(("geist-", "manrope-"))
    )
    if not font_assets or not any(path.name == "geist-local.css" for path in font_assets):
        raise ValueError("Canonical local-font asset set is incomplete")
    (static_out / "vendor").mkdir(parents=True, exist_ok=True)
    for source in font_assets:
        shutil.copy2(source, static_out / "vendor" / source.name)
    if solution_journey_registry is not None:
        for name in ("base2026-solution-journey.js", "base2026-solution-journey.css"):
            shutil.copy2(ROOT / "web" / "static" / name, static_out / name)
        shutil.copy2(solution_journey_registry, static_out / "base2026-solution-journey.json")
    local_shell_css = re.sub(
        r"^@import\s+url\([^\n]+\);\s*",
        "",
        shell_css(),
        count=1,
    )
    if "fonts.googleapis.com" in local_shell_css or "fonts.gstatic.com" in local_shell_css:
        raise ValueError("Candidate shell CSS retains an external font dependency")
    (static_out / "alex-v4-static-shell.css").write_text(local_shell_css, encoding="utf-8")
    (static_out / "alex-v4-static-shell.js").write_text(shell_js(), encoding="utf-8")
    required = [
        "alex-v4-static-shell.css",
        "alex-v4-static-shell.js",
        "source-detail-v2.css",
        "source-detail-v2.js",
        "base2026-interior-v1.css",
        *[f"vendor/{path.name}" for path in font_assets],
        "assets/alex-yarosh-favicon-32.png",
        "assets/alex-yarosh-apple-touch.png",
    ]
    if solution_journey_registry is not None:
        required.extend(
            (
                "base2026-solution-journey.js",
                "base2026-solution-journey.css",
                "base2026-solution-journey.json",
            )
        )
    missing = [name for name in required if not (static_out / name).is_file()]
    if missing:
        raise ValueError(f"Candidate static asset copy missing: {missing}")
    return {name: sha256(static_out / name) for name in required}


def load_solution_mappings(path: Path | None) -> tuple[dict[str, tuple[SourceSolution, ...]], str]:
    if path is None:
        return {}, ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "base2026.solution-journey-registry/v1":
        raise ValueError("Unexpected Solution journey registry schema")
    mappings: dict[str, tuple[SourceSolution, ...]] = {}
    for row in payload.get("source_mappings") or []:
        route = str(row.get("route") or "")
        if not route.startswith("sources/") or not route.endswith(".html"):
            raise ValueError(f"Invalid Solution journey source route: {route!r}")
        solutions = tuple(
            SourceSolution(
                solution_id=str(solution.get("id") or ""),
                title=str(solution.get("title") or ""),
                href=str(solution.get("href") or ""),
                why_relevant=str(solution.get("why_relevant") or ""),
            )
            for solution in row.get("solutions") or []
        )
        if not solutions or route in mappings:
            raise ValueError(f"Invalid or duplicate Solution journey mapping: {route}")
        mappings[route] = solutions
    return mappings, sha256(path)


def build(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.route_manifest).resolve()
    source_root = Path(args.source_root).resolve()
    out = safe_candidate_out(Path(args.out))
    rows = read_manifest(manifest_path)
    registry_path = Path(args.solution_journey_registry).resolve() if args.solution_journey_registry else None
    solution_mappings, registry_sha256 = load_solution_mappings(registry_path)
    expected = Counter((int(row["expected_status"]), str(row["admission_state"])) for row in rows)
    if expected[(200, "normal_public_card")] == 0 or expected[(200, "provenance_archive_noindex")] == 0:
        raise ValueError("Manifest must contain normal and archive Source Detail routes")
    if expected[(404, "future_private_backlog")] == 0:
        raise ValueError("Manifest must contain future-private Source Detail routes")

    out.mkdir(parents=True)
    rendered: list[dict[str, Any]] = []
    future: list[str] = []
    try:
        assets = copy_static_assets(out, registry_path)
        for row in rows:
            route = str(row["route"])
            status = int(row["expected_status"])
            admission = str(row["admission_state"])
            source = source_root / route
            target = out / route
            if status == 404:
                if admission != "future_private_backlog":
                    raise ValueError(f"404 route has wrong admission state: {route} / {admission}")
                if source.exists():
                    raise ValueError(f"Future-private route unexpectedly exists in canonical source: {route}")
                future.append(route)
                continue
            if status != 200 or admission not in {"normal_public_card", "provenance_archive_noindex"}:
                raise ValueError(f"Invalid render admission for {route}: status={status}, state={admission}")
            if not source.is_file():
                raise FileNotFoundError(f"Manifest 200 route is absent from canonical source: {route}")
            view = adapt_source_detail(source, route, admission, solution_mappings.get(route, ()))  # type: ignore[arg-type]
            html = render_source_detail(view, RENDERER_VERSION)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            rendered.append(
                {
                    "route": route,
                    "admission_state": admission,
                    "input_sha256": sha256(source),
                    "output_sha256": sha256(target),
                    "bytes": target.stat().st_size,
                }
            )
        for route in future:
            if (out / route).exists():
                raise AssertionError(f"Future-private route was emitted: {route}")
        result: dict[str, Any] = {
            "schema": "base2026.source-detail-v2-full-candidate/v1",
            "renderer_version": RENDERER_VERSION,
            "route_manifest": str(manifest_path.relative_to(ROOT)),
            "route_manifest_sha256": sha256(manifest_path),
            "source_root": str(source_root.relative_to(ROOT)),
            "asset_sha256": assets,
            "solution_journey_registry_sha256": registry_sha256,
            "solution_journey_source_count": len(solution_mappings),
            "expected": {f"{status}:{state}": count for (status, state), count in sorted(expected.items())},
            "rendered": rendered,
            "future_private_not_emitted": future,
        }
        (out / "candidate-manifest.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return result
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-manifest", required=True)
    parser.add_argument("--source-root", default="web/static")
    parser.add_argument("--out", required=True)
    parser.add_argument("--solution-journey-registry")
    args = parser.parse_args()
    result = build(args)
    print(json.dumps({"out": args.out, "rendered": len(result["rendered"]), "future_private_not_emitted": len(result["future_private_not_emitted"]), "expected": result["expected"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
