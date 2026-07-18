#!/usr/bin/env python3
"""Build the public Source -> Solution journey registry from reviewed evidence.

The registry is deliberately derived from the existing Solution validation
contract.  It does not infer relevance from keywords: a Source is linked only
when an approved, indexable Solution names that exact public source/claim pair.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from base2026_ai_recommends_core import validate_payload

REGISTRY_SCHEMA = "base2026.solution-journey-registry/v1"
APPROVAL_SCHEMA = "base2026.approved-solution-ids/v1"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row {line_number} must be an object")
        rows.append(row)
    return rows


def approved_solutions(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict) or payload.get("schema") != APPROVAL_SCHEMA:
        raise ValueError(f"Approval contract must use {APPROVAL_SCHEMA}")
    rows = payload.get("solutions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Approval contract requires a non-empty solutions list")
    approved: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"id", "route"}:
            raise ValueError(f"Approval row {index} must contain only id and route")
        solution_id = str(row.get("id") or "")
        route = str(row.get("route") or "")
        expected_route = f"solutions/{solution_id}.html"
        if not ID_RE.fullmatch(solution_id):
            raise ValueError(f"Invalid approved solution id: {solution_id!r}")
        if route != expected_route:
            raise ValueError(f"Approved route must be {expected_route}, got {route!r}")
        if solution_id in approved:
            raise ValueError(f"Duplicate approved solution id: {solution_id}")
        approved[solution_id] = route
    return approved


def public_context(
    source_rows: list[dict[str, Any]], insight_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    source_by_id = {
        str(row.get("source_id")): row
        for row in source_rows
        if isinstance(row.get("source_id"), str) and row.get("source_id")
    }
    insights_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    claims_by_id: dict[str, dict[str, Any]] = {}
    for row in insight_rows:
        if not row.get("public"):
            continue
        source_id = str(row.get("source_id") or "")
        claim_id = str(row.get("claim_id") or "")
        if source_id:
            insights_by_source[source_id].append(row)
        if claim_id:
            claims_by_id[claim_id] = row
    return {
        "source_by_id": source_by_id,
        "insights_by_source": dict(insights_by_source),
        "claims_by_id": claims_by_id,
    }


def build_registry(
    approval_payload: dict[str, Any],
    solution_payload: dict[str, Any],
    source_rows: list[dict[str, Any]],
    insight_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    approved = approved_solutions(approval_payload)
    context = public_context(source_rows, insight_rows)
    validation = validate_payload(solution_payload, context)
    if not validation.get("ok"):
        raise ValueError(f"Solution evidence validation failed: {validation.get('errors')}")

    solution_by_id = {
        str(row.get("slug")): row
        for row in solution_payload.get("solutions") or []
        if isinstance(row, dict)
    }
    report_by_id = {
        str(row.get("slug")): row for row in validation.get("_internal_reports") or []
    }
    missing = sorted(set(approved) - set(solution_by_id))
    if missing:
        raise ValueError(f"Approved Solution IDs are absent from the payload: {missing}")

    public_solutions: list[dict[str, Any]] = []
    mappings: dict[str, dict[str, Any]] = {}
    seen_evidence: set[tuple[str, str, str]] = set()

    for solution_id in sorted(approved):
        solution = solution_by_id[solution_id]
        report = report_by_id.get(solution_id) or {}
        if not report.get("indexable"):
            raise ValueError(f"Approved Solution is not indexable: {solution_id}")
        route = approved[solution_id]
        public_solutions.append(
            {
                "id": solution_id,
                "title": str(solution.get("title") or solution_id),
                "route": route,
                "href": f"/knowledge/{route}",
                "evidence_count": len(report.get("resolved_evidence") or []),
            }
        )
        for resolved in report.get("resolved_evidence") or []:
            entry = resolved["entry"]
            source = resolved["source"]
            claim = resolved["claim"]
            source_id = str(entry.get("source_id") or "")
            claim_id = str(entry.get("claim_id") or "")
            key = (solution_id, source_id, claim_id)
            if key in seen_evidence:
                raise ValueError(f"Duplicate Solution evidence tuple: {key}")
            seen_evidence.add(key)
            item_id = str(source.get("item_id") or "")
            if not ID_RE.fullmatch(item_id):
                raise ValueError(f"Public source has no safe item_id: {source_id}")
            source_route = f"sources/{item_id}.html"
            mapping = mappings.setdefault(
                item_id,
                {
                    "item_id": item_id,
                    "source_id": source_id,
                    "route": source_route,
                    "solutions": [],
                },
            )
            if mapping["source_id"] != source_id:
                raise ValueError(f"item_id maps to multiple source IDs: {item_id}")
            mapping["solutions"].append(
                {
                    "id": solution_id,
                    "title": str(solution.get("title") or solution_id),
                    "href": f"/knowledge/{route}",
                    "claim_id": claim_id,
                    "why_relevant": str(entry.get("why_relevant") or ""),
                    "evidence_role": "reviewed_creator_signal",
                    "synthesis_role": "base2026_decision_playbook",
                    "claim_topic": str(claim.get("topic") or "Reviewed source signal"),
                }
            )

    source_mappings = sorted(mappings.values(), key=lambda row: row["item_id"])
    for mapping in source_mappings:
        mapping["solutions"] = sorted(mapping["solutions"], key=lambda row: row["id"])
    return {
        "schema": REGISTRY_SCHEMA,
        "updated_at": str(approval_payload.get("updated_at") or solution_payload.get("updated_at") or ""),
        "approved_solution_ids": sorted(approved),
        "solutions": public_solutions,
        "source_mappings": source_mappings,
        "counts": {
            "approved_solutions": len(public_solutions),
            "evidence_bound_sources": len(source_mappings),
            "evidence_links": sum(len(row["solutions"]) for row in source_mappings),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approvals", type=Path, default=Path("contracts/base2026-approved-solution-ids.json"))
    parser.add_argument("--solutions", type=Path, default=Path("data/base2026_ai_recommends_solutions_pilot.json"))
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--insights", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    registry = build_registry(
        read_json(args.approvals),
        read_json(args.solutions),
        read_jsonl(args.sources),
        read_jsonl(args.insights),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(registry["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
