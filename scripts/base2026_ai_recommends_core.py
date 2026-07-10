from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_TEXT_FIELDS = (
    "slug",
    "title",
    "meta_description",
    "audience",
    "problem",
    "primary_query",
    "recommendation",
    "decision_scope",
    "why_now",
    "cadence",
)
MIN_COUNTS = {
    "evidence": 2,
    "authoritative_sources": 1,
    "playbook": 3,
    "checklist": 5,
    "decision_table": 3,
    "risks": 2,
    "kpis": 3,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL in {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Expected object in {path}:{line_number}")
        rows.append(row)
    return rows


def build_public_context(data_root: Path) -> dict[str, Any]:
    sources = read_jsonl(data_root / "source_records.jsonl")
    insights = [row for row in read_jsonl(data_root / "insight_cards.jsonl") if row.get("public")]
    source_by_id = {str(row.get("source_id") or ""): row for row in sources if row.get("source_id")}
    insights_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    claims_by_id: dict[str, dict[str, Any]] = {}
    for row in insights:
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


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def resolve_evidence(solution: dict[str, Any], context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    resolved: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, entry in enumerate(solution.get("evidence") or []):
        if not isinstance(entry, dict):
            errors.append(f"evidence[{index}] must be an object")
            continue
        source_id = str(entry.get("source_id") or "")
        claim_id = str(entry.get("claim_id") or "")
        source = context["source_by_id"].get(source_id)
        claim = context["claims_by_id"].get(claim_id)
        if not source:
            errors.append(f"evidence[{index}] source_id is not in public source records: {source_id}")
            continue
        if not claim:
            errors.append(f"evidence[{index}] claim_id is not a public insight: {claim_id}")
            continue
        if str(claim.get("source_id") or "") != source_id:
            errors.append(f"evidence[{index}] claim_id {claim_id} does not belong to {source_id}")
            continue
        if claim.get("needs_review"):
            errors.append(f"evidence[{index}] claim_id {claim_id} still needs review")
            continue
        if not _nonempty_text(entry.get("why_relevant")):
            errors.append(f"evidence[{index}] requires why_relevant")
        resolved.append({"entry": entry, "source": source, "claim": claim})
    return resolved, errors


def validate_solution(solution: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    slug = str(solution.get("slug") or "")
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_TEXT_FIELDS:
        if not _nonempty_text(solution.get(field)):
            errors.append(f"missing non-empty text field: {field}")
    if slug and not SLUG_RE.fullmatch(slug):
        errors.append("slug must use lowercase ASCII words separated by single hyphens")
    if len(str(solution.get("meta_description") or "")) > 180:
        errors.append("meta_description must be 180 characters or fewer")

    for field, minimum in MIN_COUNTS.items():
        value = solution.get(field)
        if not isinstance(value, list) or len(value) < minimum:
            errors.append(f"{field} requires at least {minimum} entries")

    resolved, evidence_errors = resolve_evidence(solution, context)
    errors.extend(evidence_errors)
    source_ids = {row["entry"].get("source_id") for row in resolved}
    creators = {
        str(row["claim"].get("creator_handle") or row["source"].get("creator_handle") or "").lower()
        for row in resolved
        if row["claim"].get("creator_handle") or row["source"].get("creator_handle")
    }
    if len(source_ids) < 2:
        errors.append("requires at least two distinct resolved public source records")
    if len(creators) < 2:
        errors.append("requires at least two distinct creator/source identities")

    for index, citation in enumerate(solution.get("authoritative_sources") or []):
        if not isinstance(citation, dict):
            errors.append(f"authoritative_sources[{index}] must be an object")
            continue
        for field in ("title", "url", "scope"):
            if not _nonempty_text(citation.get(field)):
                errors.append(f"authoritative_sources[{index}] requires {field}")
        if citation.get("url") and not str(citation["url"]).startswith("https://"):
            errors.append(f"authoritative_sources[{index}] url must use https")

    for index, step in enumerate(solution.get("playbook") or []):
        if not isinstance(step, dict) or not _nonempty_text(step.get("title")) or not _nonempty_text(step.get("body")):
            errors.append(f"playbook[{index}] requires title and body")

    for index, row in enumerate(solution.get("decision_table") or []):
        if not isinstance(row, dict) or any(not _nonempty_text(row.get(key)) for key in ("signal", "decision", "measure")):
            errors.append(f"decision_table[{index}] requires signal, decision and measure")

    cta = solution.get("cta")
    if not isinstance(cta, dict) or not _nonempty_text(cta.get("label")) or not _nonempty_text(cta.get("href")):
        errors.append("cta requires label and href")
    elif not (str(cta["href"]).startswith("/knowledge/") or str(cta["href"]).startswith("#")):
        errors.append("cta href must stay inside the Base2026 product journey")

    editorial = solution.get("editorial")
    if not isinstance(editorial, dict):
        errors.append("editorial must be an object")
    else:
        if editorial.get("status") != "approved_local":
            errors.append("editorial.status must be approved_local for index eligibility")
        for field in ("reviewer", "reviewed_at", "contract_version"):
            if not _nonempty_text(editorial.get(field)):
                errors.append(f"editorial requires {field}")

    if not solution.get("related_solution_slugs"):
        warnings.append("no related solutions declared")

    return {
        "slug": slug,
        "title": solution.get("title") or slug,
        "indexable": not errors,
        "errors": errors,
        "warnings": warnings,
        "resolved_evidence": resolved,
        "resolved_source_count": len(source_ids),
        "resolved_creator_count": len(creators),
    }


def validate_payload(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"ok": False, "errors": ["payload must be an object"], "solutions": []}
    solutions = payload.get("solutions")
    if not isinstance(solutions, list) or not solutions:
        return {"ok": False, "errors": ["payload.solutions must be a non-empty array"], "solutions": []}

    slugs = [str(row.get("slug") or "") for row in solutions if isinstance(row, dict)]
    duplicates = sorted({slug for slug in slugs if slug and slugs.count(slug) > 1})
    if duplicates:
        errors.append(f"duplicate slugs: {', '.join(duplicates)}")
    known_slugs = set(slugs)

    reports: list[dict[str, Any]] = []
    for index, solution in enumerate(solutions):
        if not isinstance(solution, dict):
            reports.append({"slug": f"row-{index}", "indexable": False, "errors": ["solution must be an object"], "warnings": []})
            continue
        report = validate_solution(solution, context)
        for related_slug in solution.get("related_solution_slugs") or []:
            if related_slug not in known_slugs:
                report["errors"].append(f"unknown related solution slug: {related_slug}")
                report["indexable"] = False
        reports.append(report)

    public_reports = [
        {
            key: value
            for key, value in report.items()
            if key != "resolved_evidence"
        }
        for report in reports
    ]
    all_errors = errors + [f"{row['slug']}: {message}" for row in public_reports for message in row.get("errors", [])]
    return {
        "ok": not all_errors,
        "contract_version": payload.get("contract_version"),
        "solution_count": len(solutions),
        "indexable_count": sum(1 for row in public_reports if row.get("indexable")),
        "errors": all_errors,
        "solutions": public_reports,
        "_internal_reports": reports,
    }
