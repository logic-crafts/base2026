#!/usr/bin/env python3
"""Bind a frozen route inventory to the current source-admission ledger.

The refresh is intentionally narrow: existing route-contract rows are preserved
byte-for-value, and only ledger-approved future_private_backlog routes may be
added as 404/non-emitted Source Detail rows.  The output is immutable by
construction: an existing target is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FUTURE_STATE = "future_private_backlog"
SOURCE_PREFIX = "sources/"
SOURCE_SUFFIX = ".html"
EMPTY_FUTURE_CONTRACT: dict[str, Any] = {
    "title": "",
    "description": "",
    "canonical": "",
    "robots": "index,follow",
    "h1": "",
    "json_ld_count": 0,
    "schema_types": [],
    "internal_link_count": 0,
    "asset_link_count": 0,
    "local_asset_paths": [],
    "original_source_url": "",
    "creator_link": "",
    "search_link": "",
    "topic_href": "",
    "original_source_schema_references": 0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contract_digest(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require_planning_output(path: Path) -> Path:
    resolved = path.resolve()
    planning = (ROOT / ".planning").resolve()
    if planning not in (resolved, *resolved.parents):
        raise ValueError(f"Output must be under {planning}, got {resolved}")
    if resolved.exists():
        raise FileExistsError(f"Refusing to overwrite existing inventory: {resolved}")
    return resolved


def future_row(item_id: str) -> dict[str, Any]:
    if not item_id.startswith("tiktok-video-"):
        raise ValueError(f"Unsupported future-private item_id: {item_id!r}")
    contract = dict(EMPTY_FUTURE_CONTRACT)
    return {
        "route": f"{SOURCE_PREFIX}{item_id}{SOURCE_SUFFIX}",
        "page_family": "source_detail",
        "admission_state": FUTURE_STATE,
        "expected_status": 404,
        "current_generator": "scripts/export-public-tiktok.py",
        "target_template": "families/source_detail.html.j2",
        "input_refs": ["12_knowledge-base/sources/tiktok/source-admission.jsonl"],
        "exception_codes": [],
        "contract": contract,
        "contract_digest": contract_digest(contract),
    }


def refresh(base_manifest: Path, ledger: Path, out: Path, summary: Path) -> dict[str, Any]:
    rows = read_jsonl(base_manifest)
    ledger_rows = read_jsonl(ledger)
    if not rows or not ledger_rows:
        raise ValueError("Base manifest and admission ledger must both be non-empty")

    source_rows = [row for row in rows if row.get("page_family") == "source_detail"]
    by_route = {str(row.get("route") or ""): row for row in source_rows}
    if len(by_route) != len(source_rows):
        raise ValueError("Base manifest has duplicate Source Detail routes")

    ledger_by_route: dict[str, dict[str, Any]] = {}
    for admission in ledger_rows:
        item_id = str(admission.get("item_id") or "")
        route = f"{SOURCE_PREFIX}{item_id}{SOURCE_SUFFIX}"
        if not item_id or route in ledger_by_route:
            raise ValueError(f"Invalid or duplicate ledger item_id: {item_id!r}")
        ledger_by_route[route] = admission

    unknown_manifest_routes = sorted(set(by_route) - set(ledger_by_route))
    if unknown_manifest_routes:
        raise ValueError(f"Source routes absent from current ledger: {unknown_manifest_routes[:5]}")

    state_to_status = {
        "normal_public_card": 200,
        "provenance_archive_noindex": 200,
        FUTURE_STATE: 404,
    }
    for route, row in by_route.items():
        ledger_state = str(ledger_by_route[route].get("admission_state") or "")
        expected_status = state_to_status.get(ledger_state)
        if expected_status is None:
            raise ValueError(f"Unsupported ledger admission_state for {route}: {ledger_state!r}")
        if row.get("admission_state") != ledger_state or row.get("expected_status") != expected_status:
            raise ValueError(
                f"Existing manifest row conflicts with ledger: {route}; "
                f"manifest={row.get('admission_state')}/{row.get('expected_status')} "
                f"ledger={ledger_state}/{expected_status}"
            )

    missing_routes = sorted(set(ledger_by_route) - set(by_route))
    non_future_missing = [
        route for route in missing_routes if ledger_by_route[route].get("admission_state") != FUTURE_STATE
    ]
    if non_future_missing:
        raise ValueError(
            "Refusing to invent public 200 route contracts; missing non-future rows: "
            f"{non_future_missing[:5]}"
        )

    added = [future_row(str(ledger_by_route[route]["item_id"])) for route in missing_routes]
    refreshed = sorted([*rows, *added], key=lambda row: str(row.get("route") or ""))
    all_source = [row for row in refreshed if row.get("page_family") == "source_detail"]
    if len(all_source) != len(ledger_rows):
        raise AssertionError(f"Source/ledger count mismatch: {len(all_source)} != {len(ledger_rows)}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in refreshed),
        encoding="utf-8",
    )
    counts = Counter(str(row["admission_state"]) for row in all_source)
    report: dict[str, Any] = {
        "schema": "base2026.source-detail-route-inventory-refresh/v1",
        "base_manifest": str(base_manifest.relative_to(ROOT)),
        "base_manifest_sha256": sha256(base_manifest),
        "admission_ledger": str(ledger.relative_to(ROOT)),
        "admission_ledger_sha256": sha256(ledger),
        "output_manifest": str(out.relative_to(ROOT)),
        "output_manifest_sha256": sha256(out),
        "base_source_routes": len(source_rows),
        "refreshed_source_routes": len(all_source),
        "added_future_private_routes": [row["route"] for row in added],
        "admission_counts": dict(sorted(counts.items())),
        "total_inventory_rows": len(refreshed),
    }
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-manifest", required=True)
    parser.add_argument("--admission-ledger", default="12_knowledge-base/sources/tiktok/source-admission.jsonl")
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    base_manifest = Path(args.base_manifest).resolve()
    ledger = Path(args.admission_ledger).resolve()
    out = require_planning_output(Path(args.out))
    summary = require_planning_output(Path(args.summary))
    report = refresh(base_manifest, ledger, out, summary)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
