#!/usr/bin/env python3
"""Read-only validators for Base2026 release, channel, incident, and UX contracts.

The command intentionally reports a safe aggregate view. It never writes a
receipt, changes a job, calls an external service, or retries an effect.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "reliability" / "BASE2026_PRODUCTION_MANIFEST_2026-09-01.json"

LEGACY_STATES = {
    "prepared",
    "draft_ready",
    "submit_attempted",
    "submitted",
    "response_complete",
    "review_passed",
    "publishing",
    "published_verified",
    "blocked_owner",
    "blocked_transport",
}
CANONICAL_STATES = LEGACY_STATES | {"held_contract", "fenced_no_retry"}
EVENT_NAMES = (
    "search_submitted",
    "result_opened",
    "save_completed",
    "revisit_completed",
    "export_completed",
)
EVENT_PROPERTIES = {
    "query_length_bucket",
    "result_count_bucket",
    "latency_bucket_ms",
    "viewport_bucket",
    "unique_sources_bucket",
    "new_auth_session",
    "export_format",
}
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
UUID_RE = re.compile(r"^[a-f0-9-]{36}$")
EVENT_ID_RE = re.compile(r"^evt_[A-Za-z0-9_-]{8,128}$")
TRACE_ID_RE = re.compile(r"^trace_[A-Za-z0-9_-]{8,128}$")
QUERY_ID_RE = re.compile(r"^qry_[A-Za-z0-9_-]{8,128}$")
ACTOR_RE = re.compile(r"^usr_[A-Za-z0-9_-]{8,128}$")
SOURCE_RE = re.compile(r"^src_[A-Za-z0-9_-]{4,128}$")
RELATIVE_PATH_RE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.?(?:/|$))[A-Za-z0-9._/-]+$")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_datetime(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_hash(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        errors.append(f"invalid:{label}")


def _validate_uuid(value: Any, label: str, errors: list[str], allow_null: bool = False) -> None:
    if allow_null and value is None:
        return
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        errors.append(f"invalid:{label}")


def validate_production_manifest(manifest: Any) -> dict[str, Any]:
    """Validate the redacted production manifest without treating it as auth."""

    errors: list[str] = []
    if not isinstance(manifest, dict):
        return {
            "ok": False,
            "read_only": True,
            "errors": ["invalid_manifest_object"],
            "exact_commit_binding": "unresolved",
        }

    if manifest.get("schema_version") != "base2026.production-manifest.v1":
        errors.append("invalid:schema_version")
    if _parse_datetime(manifest.get("recorded_at")) is None:
        errors.append("invalid:recorded_at")
    if manifest.get("status") != "observed_not_deployment_authorization":
        errors.append("invalid:status")
    if manifest.get("production_mutation_performed") is not False:
        errors.append("production_mutation_performed")

    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append("missing:source")
        source = {}
    if not isinstance(source.get("repository"), str) or not source.get("repository", "").startswith("github.com/"):
        errors.append("invalid:source.repository")
    for field in ("baseline_commit", "post_release_candidate_commit"):
        if not isinstance(source.get(field), str) or not COMMIT_RE.fullmatch(source[field]):
            errors.append(f"invalid:source.{field}")
    for field in ("deployed_artifact_tree_sha256", "release_config_sha256", "artifact_receipt_sha256"):
        _validate_hash(source.get(field), f"source.{field}", errors)
    if source.get("source_state_at_release") not in {"clean", "dirty_uncommitted_unpushed", "unknown"}:
        errors.append("invalid:source.source_state_at_release")
    exact_binding = source.get("exact_commit_binding")
    if exact_binding not in {"resolved", "unresolved", "withheld"}:
        errors.append("invalid:source.exact_commit_binding")
    if not isinstance(source.get("reproducible_from_commit"), bool):
        errors.append("invalid:source.reproducible_from_commit")
    if not isinstance(source.get("post_release_candidate_recorded_after_deploy"), bool):
        errors.append("invalid:source.post_release_candidate_recorded_after_deploy")
    if source.get("source_state_at_release") != "clean" and exact_binding == "resolved":
        errors.append("dirty_source_cannot_have_resolved_commit_binding")
    if source.get("post_release_candidate_recorded_after_deploy") is True and exact_binding == "resolved":
        errors.append("post_release_candidate_cannot_prove_deployed_commit")
    if exact_binding != "resolved" and source.get("reproducible_from_commit") is True:
        errors.append("unresolved_commit_cannot_be_reproducible")

    workers = manifest.get("workers")
    if not isinstance(workers, dict):
        errors.append("missing:workers")
        workers = {}
    for role in ("public", "redirect", "private"):
        worker = workers.get(role)
        if not isinstance(worker, dict):
            errors.append(f"missing:workers.{role}")
            continue
        if not isinstance(worker.get("name"), str) or not worker.get("name"):
            errors.append(f"invalid:workers.{role}.name")
        if not isinstance(worker.get("version_label"), str) or not worker.get("version_label"):
            errors.append(f"invalid:workers.{role}.version_label")
        if not _is_int(worker.get("traffic_percent")) or not 0 <= worker["traffic_percent"] <= 100:
            errors.append(f"invalid:workers.{role}.traffic_percent")
        if role == "private":
            if worker.get("version_id") is not None or worker.get("version_id_status") != "withheld_private":
                errors.append("private_worker_identifier_not_withheld")
        else:
            _validate_uuid(worker.get("version_id"), f"workers.{role}.version_id", errors)
            if worker.get("version_id_status") != "public":
                errors.append(f"invalid:workers.{role}.version_id_status")
            if worker.get("traffic_percent") != 100:
                errors.append(f"invalid:workers.{role}.traffic_percent_not_full")
        if worker.get("deployment_id") is not None:
            _validate_uuid(worker.get("deployment_id"), f"workers.{role}.deployment_id", errors)

    routes = manifest.get("routes")
    if not isinstance(routes, dict):
        errors.append("missing:routes")
        routes = {}
    for field in ("custom_domains", "worker_first_patterns", "live_verified"):
        if not isinstance(routes.get(field), list) or not routes[field]:
            errors.append(f"missing:routes.{field}")
    for route in routes.get("custom_domains", []) if isinstance(routes.get("custom_domains"), list) else []:
        if not isinstance(route, dict) or not route.get("domain") or not route.get("worker"):
            errors.append("invalid:routes.custom_domains")
    for field in ("worker_first_patterns", "live_verified"):
        values = routes.get(field)
        if isinstance(values, list) and any(not isinstance(value, str) or not value.startswith("/") for value in values):
            errors.append(f"invalid:routes.{field}")

    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict):
        errors.append("missing:bindings")
        bindings = {}
    public_bindings = bindings.get("public_worker")
    if not isinstance(public_bindings, dict):
        errors.append("missing:bindings.public_worker")
    else:
        observed = public_bindings.get("observed_runtime")
        tracked = public_bindings.get("tracked_config")
        missing = public_bindings.get("missing_from_tracked_config")
        if not all(isinstance(value, list) for value in (observed, tracked, missing)):
            errors.append("invalid:bindings.public_worker.binding_lists")
        elif not all(
            isinstance(item, str)
            for values in (observed, tracked, missing)
            for item in values
        ):
            errors.append("invalid:bindings.public_worker.binding_names")
        elif sorted(set(observed) - set(tracked)) != sorted(set(missing)):
            errors.append("binding_drift_not_reconciled")
        if public_bindings.get("secret_values_read_or_uploaded") is not False:
            errors.append("secret_values_read_or_uploaded")
    private_bindings = bindings.get("private_worker")
    if not isinstance(private_bindings, dict):
        errors.append("missing:bindings.private_worker")
    else:
        if private_bindings.get("source_visibility") != "protected_not_in_public_repo":
            errors.append("private_source_visibility_not_protected")
        if private_bindings.get("identifiers_committed") is not False:
            errors.append("private_identifiers_committed")

    migrations = manifest.get("migrations")
    if not isinstance(migrations, dict):
        errors.append("missing:migrations")
        migrations = {}
    public_migrations = migrations.get("public_worker")
    if not isinstance(public_migrations, dict):
        errors.append("missing:migrations.public_worker")
    else:
        for binding in ("DB", "INBOX_DB", "OUTREACH_DB", "AUTH_DB"):
            item = public_migrations.get(binding)
            if not isinstance(item, dict) or not isinstance(item.get("source_files"), list):
                errors.append(f"missing:migrations.public_worker.{binding}")
            elif item.get("fresh_full_readback_required") is not True:
                errors.append(f"missing:migrations.public_worker.{binding}.fresh_full_readback_required")
    private_migrations = migrations.get("private_worker")
    if not isinstance(private_migrations, dict):
        errors.append("missing:migrations.private_worker")
    else:
        for field in ("applied_count_observed", "pending_observed"):
            if not _is_int(private_migrations.get(field)) or private_migrations[field] < 0:
                errors.append(f"invalid:migrations.private_worker.{field}")
        if private_migrations.get("fresh_full_readback_required") is not True:
            errors.append("missing:migrations.private_worker.fresh_full_readback_required")

    live_checks = manifest.get("live_checks")
    if not isinstance(live_checks, dict):
        errors.append("missing:live_checks")
        live_checks = {}
    public_health = live_checks.get("public_health")
    if not isinstance(public_health, dict) or public_health.get("ok") is not True:
        errors.append("public_health_not_ok")
    public_stats = live_checks.get("public_stats")
    if not isinstance(public_stats, dict):
        errors.append("missing:live_checks.public_stats")
    elif public_stats.get("full_transcripts_published") != 0:
        errors.append("public_full_transcript_invariant_failed")
    private_health = live_checks.get("private_health")
    if not isinstance(private_health, dict) or private_health.get("http_status") != 200:
        errors.append("private_health_not_200")
    route_status = live_checks.get("route_status")
    if not isinstance(route_status, dict) or any(value != 200 for value in route_status.values()):
        errors.append("live_route_check_failed")
    privacy = live_checks.get("privacy_invariants")
    if not isinstance(privacy, dict) or privacy.get("full_transcripts_published") != 0:
        errors.append("privacy_invariant_failed")

    recommendations = manifest.get("unapplied_recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        errors.append("missing:unapplied_recommendations")

    return {
        "ok": not errors,
        "read_only": True,
        "exact_commit_binding": exact_binding,
        "reproducible_from_commit": source.get("reproducible_from_commit"),
        "binding_drift_present": bool((bindings.get("public_worker") or {}).get("missing_from_tracked_config")),
        "release_ready": (
            not errors
            and exact_binding == "resolved"
            and source.get("reproducible_from_commit") is True
            and not bool((bindings.get("public_worker") or {}).get("missing_from_tracked_config"))
        ),
        "errors": errors,
    }


def _safe_artifact_path(job_path: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not RELATIVE_PATH_RE.fullmatch(value):
        return None, "unsafe_artifact_path"
    candidate = (job_path.parent / value).resolve()
    try:
        candidate.relative_to(job_path.parent.resolve())
    except ValueError:
        return None, "unsafe_artifact_path"
    return candidate, None


def _check_artifact(job_path: Path, name: Any, expected_hash: Any, errors: list[str]) -> bool:
    if not name:
        errors.append("missing:prompt_file_or_draft_file")
        return False
    artifact_path, path_error = _safe_artifact_path(job_path, name)
    if path_error or artifact_path is None:
        errors.append(path_error or "unsafe_artifact_path")
        return False
    if not artifact_path.is_file():
        errors.append("missing_artifact")
        return False
    if expected_hash:
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != expected_hash:
            errors.append("hash_mismatch:artifact")
            return False
    return True


def _check_receipt(job_path: Path, field: str, job: dict[str, Any], errors: list[str]) -> bool:
    value = job.get(field)
    if not value:
        errors.append(f"missing:{field}")
        return False
    receipt_path, path_error = _safe_artifact_path(job_path, value)
    if path_error or receipt_path is None:
        errors.append(path_error or f"unsafe:{field}")
        return False
    if not receipt_path.is_file():
        errors.append(f"missing:{field}_file")
        return False
    return True


def inspect_channel_job(job_path: Path) -> dict[str, Any]:
    """Inspect one legacy or canonical job while suppressing private values."""

    try:
        job = _load_json(job_path)
    except (OSError, json.JSONDecodeError):
        return {
            "channel": "unknown",
            "observed_state": "unreadable",
            "canonical_disposition": "held_contract",
            "valid": False,
            "errors": ["invalid_job_json"],
            "next_action": "repair_job_contract",
            "external_action_performed": False,
            "replay_performed": False,
        }
    if not isinstance(job, dict):
        return {
            "channel": "unknown",
            "observed_state": "invalid",
            "canonical_disposition": "held_contract",
            "valid": False,
            "errors": ["invalid_job_object"],
            "next_action": "repair_job_contract",
            "external_action_performed": False,
            "replay_performed": False,
        }

    raw_channel = job.get("channel")
    channel = raw_channel if isinstance(raw_channel, str) and raw_channel in {"dev", "linkedin", "medium", "x"} else "unknown"
    raw_state = job.get("state")
    state = raw_state if isinstance(raw_state, str) else None
    errors: list[str] = []
    schema_version = job.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        errors.append("missing:schema_version")
    if not isinstance(job.get("marker"), str) or not job.get("marker"):
        errors.append("missing:marker")
    if channel == "unknown":
        errors.append("invalid:channel")
    if state not in CANONICAL_STATES:
        if state == "native_draft_saved":
            errors.append("unsupported_state:native_draft_saved")
        else:
            errors.append("unsupported_state" if state else "missing:state")

    if state in {"response_complete", "review_passed", "publishing", "published_verified"}:
        artifact_name = job.get("response_file")
        artifact_hash = job.get("response_sha256")
    else:
        artifact_name = job.get("prompt_file") or job.get("draft_file")
        artifact_hash = job.get("prompt_sha256") or job.get("draft_sha256")
    artifact_ok = _check_artifact(job_path, artifact_name, artifact_hash, errors)

    if state == "published_verified":
        _check_receipt(job_path, "publication_receipt", job, errors)
    if state == "review_passed" and not job.get("review_receipt"):
        errors.append("missing:review_receipt")
    if state in {"submit_attempted", "submitted", "response_complete"} and not job.get("attempt_receipt"):
        errors.append("missing:attempt_receipt")

    visual_missing = False
    if state in {"review_passed", "publishing"}:
        visual_name = job.get("visual_manifest")
        if not visual_name:
            errors.append("visual:missing_manifest")
            visual_missing = True
        else:
            visual_path, path_error = _safe_artifact_path(job_path, visual_name)
            if path_error or visual_path is None or not visual_path.is_file():
                errors.append("visual:missing_manifest_file")
                visual_missing = True
            else:
                try:
                    visual_payload = _load_json(visual_path)
                except (OSError, json.JSONDecodeError):
                    errors.append("visual:invalid_manifest_json")
                    visual_missing = True
                else:
                    if not isinstance(visual_payload, dict):
                        errors.append("visual:invalid_manifest_object")
                        visual_missing = True

    # An unsupported native-draft state is held before any external action.
    if state == "native_draft_saved":
        disposition = "held_contract"
        next_action = "repair_job_contract"
    elif state == "publishing" and (visual_missing or errors):
        # Publishing implies an external effect may already exist; fence it.
        disposition = "fenced_no_retry"
        next_action = "inspect_same_external_target_before_retry"
    elif state == "published_verified" and not errors and artifact_ok:
        disposition = "terminal_verified"
        next_action = "none"
    elif state in LEGACY_STATES and not errors and artifact_ok:
        disposition = "contract_legacy_valid"
        next_action = {
            "prepared": "resume_author_chat" if channel == "medium" else "prepare_channel_draft",
            "draft_ready": "prepare_linkedin_computer_use" if channel == "linkedin" else "prepare_external_editor",
            "submit_attempted": "inspect_same_external_target_before_retry",
            "submitted": "resume_same_conversation_and_capture_complete_response",
            "response_complete": "independent_review",
            "review_passed": "prepare_publication_and_request_action_time_confirmation",
            "blocked_owner": "recheck_recorded_blocker_without_blind_retry",
            "blocked_transport": "recheck_recorded_blocker_without_blind_retry",
        }.get(state, "none")
    else:
        disposition = "held_contract"
        next_action = "repair_job_contract"

    # Keep the legacy controller's useful explicit error for this known drift.
    if state == "native_draft_saved" and "missing:prompt_file_or_draft_file" not in errors:
        errors.append("missing:prompt_file_or_draft_file")

    return {
        "channel": channel,
        "observed_schema_version": schema_version if isinstance(schema_version, str) else None,
        "observed_state": state or "missing",
        "canonical_disposition": disposition,
        "valid": not errors and disposition in {"terminal_verified", "contract_legacy_valid"},
        "errors": errors,
        "next_action": next_action,
        "external_action_performed": False,
        "replay_performed": False,
    }


def reconcile_channels(root: Path) -> dict[str, Any]:
    """Read channel jobs and return a non-mutating reconciliation summary."""

    if not root.is_dir():
        return {
            "schema_version": "base2026.channel-reconciliation.v1",
            "read_only": True,
            "external_action_performed": False,
            "replay_performed": False,
            "job_count": 0,
            "valid": False,
            "invalid_count": 1,
            "active_backlog": True,
            "next_action": "repair_job_contract",
            "jobs": [],
            "errors": ["missing_channel_root"],
        }
    paths = sorted(root.glob("channel-chats/*/job.json"))
    jobs = [inspect_channel_job(path) for path in paths]
    invalid_count = sum(1 for job in jobs if not job["valid"])
    next_action = next((job["next_action"] for job in jobs if not job["valid"]), "none")
    return {
        "schema_version": "base2026.channel-reconciliation.v1",
        "read_only": True,
        "external_action_performed": False,
        "replay_performed": False,
        "job_count": len(jobs),
        "valid": invalid_count == 0,
        "invalid_count": invalid_count,
        "active_backlog": invalid_count > 0,
        "next_action": next_action,
        "jobs": jobs,
    }


def validate_incident_snapshot(snapshot: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(snapshot, dict):
        return {
            "closure_ready": False,
            "read_only": True,
            "external_action_performed": False,
            "errors": ["invalid_snapshot_object"],
        }
    if snapshot.get("schema_version") != "base2026.private-pipeline-incident-snapshot.v1":
        errors.append("invalid:schema_version")
    if snapshot.get("read_only") is not True:
        errors.append("snapshot_not_read_only")
    incident_id = snapshot.get("incident_id")
    if not isinstance(incident_id, str) or not re.fullmatch(r"^[a-z0-9][a-z0-9_-]{2,96}$", incident_id):
        errors.append("invalid:incident_id")
    expected = snapshot.get("expected_environment")
    actual = snapshot.get("actual_environment")
    if expected != actual:
        errors.append("environment_mismatch")
    if actual != "production":
        errors.append("environment_not_production")

    cohort = snapshot.get("bounded_cohort")
    items = cohort.get("items") if isinstance(cohort, dict) else None
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        errors.append("bounded_cohort_missing_or_out_of_bounds")
        items = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            errors.append("invalid:cohort_item")
            continue
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not re.fullmatch(r"^item_[A-Za-z0-9_-]{4,96}$", item_id):
            errors.append("invalid:cohort_item_id")
        elif item_id in seen:
            errors.append("duplicate:cohort_item_id")
        else:
            seen.add(item_id)
        if item.get("terminal") is not True:
            errors.append("cohort_item_not_terminal")
        if item.get("terminal_receipt") is not True:
            errors.append("cohort_item_missing_terminal_receipt")
        if item.get("terminal_state") not in {"completed", "held", "failed_terminal", "published_verified", "blocked_owner"}:
            errors.append("invalid:cohort_terminal_state")

    if not _is_int(snapshot.get("orphan_jobs")) or snapshot.get("orphan_jobs") != 0:
        errors.append("orphan_jobs_nonzero")
    if not _is_int(snapshot.get("public_projection_count")) or snapshot.get("public_projection_count") != 0:
        errors.append("public_projection_detected")
    if snapshot.get("accounting_complete") is not True:
        errors.append("accounting_incomplete")
    if snapshot.get("external_effects_replayed") is not False:
        errors.append("external_effect_replay_detected")

    doctor_runs = snapshot.get("doctor_runs")
    if not isinstance(doctor_runs, list) or len(doctor_runs) < 2:
        errors.append("fewer_than_two_subsequent_doctor_runs")
        doctor_runs = []
    for run in doctor_runs[-2:]:
        if not isinstance(run, dict):
            errors.append("invalid:doctor_run")
            continue
        if run.get("status") not in {"healthy", "ok"}:
            errors.append("doctor_run_degraded_or_failed")
        incident_ids = run.get("incident_ids")
        if not isinstance(incident_ids, list):
            errors.append("invalid:doctor_run.incident_ids")
        elif incident_id in incident_ids:
            errors.append("doctor_run_still_degraded_by_incident")

    return {
        "closure_ready": not errors,
        "read_only": True,
        "checked_item_count": len(items),
        "doctor_runs_checked": min(2, len(doctor_runs)),
        "external_action_performed": False,
        "errors": errors,
    }


def _event_field(event: dict[str, Any], field: str, pattern: re.Pattern[str], errors: list[str]) -> None:
    value = event.get(field)
    if not isinstance(value, str) or not pattern.fullmatch(value):
        errors.append(f"invalid:{field}")


def validate_measurement_event(event: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(event, dict):
        return {"ok": False, "read_only": True, "errors": ["invalid_event_object"]}
    required = {"schema_version", "event_id", "trace_id", "event_name", "occurred_at", "route", "query_id", "properties"}
    allowed = required | {"actor_ref", "source_id", "$schema"}
    errors.extend(f"unknown_field:{key}" for key in sorted(set(event) - allowed))
    errors.extend(f"missing:{key}" for key in sorted(required - set(event)))
    if event.get("schema_version") != "base2026.measurement-event.v1":
        errors.append("invalid:schema_version")
    _event_field(event, "event_id", EVENT_ID_RE, errors)
    _event_field(event, "trace_id", TRACE_ID_RE, errors)
    _event_field(event, "query_id", QUERY_ID_RE, errors)
    if event.get("event_name") not in EVENT_NAMES:
        errors.append("invalid:event_name")
    if _parse_datetime(event.get("occurred_at")) is None:
        errors.append("invalid:occurred_at")
    if event.get("route") not in {"/tools/evidence-search/", "/my-research/"}:
        errors.append("invalid:route")

    if "actor_ref" in event:
        _event_field(event, "actor_ref", ACTOR_RE, errors)
    if "source_id" in event:
        _event_field(event, "source_id", SOURCE_RE, errors)
    properties = event.get("properties")
    if not isinstance(properties, dict):
        errors.append("invalid:properties")
        properties = {}
    errors.extend(f"unknown_property:{key}" for key in sorted(set(properties) - EVENT_PROPERTIES))
    if "query" in properties or "query_text" in properties or "raw_query" in properties:
        errors.append("raw_query_forbidden")

    event_name = event.get("event_name")
    if event_name == "search_submitted":
        if event.get("route") != "/tools/evidence-search/":
            errors.append("search_route_required")
        if properties.get("query_length_bucket") not in {"0", "1-3", "4-8", "9+"}:
            errors.append("query_length_bucket_required")
    elif event_name == "result_opened":
        if event.get("route") != "/tools/evidence-search/":
            errors.append("result_route_required")
        if not isinstance(event.get("source_id"), str) or not SOURCE_RE.fullmatch(event["source_id"]):
            errors.append("source_id_required")
    elif event_name == "save_completed":
        if event.get("route") not in {"/tools/evidence-search/", "/my-research/"}:
            errors.append("save_route_required")
        if not isinstance(event.get("actor_ref"), str) or not ACTOR_RE.fullmatch(event["actor_ref"]):
            errors.append("actor_ref_required")
        if not isinstance(event.get("source_id"), str) or not SOURCE_RE.fullmatch(event["source_id"]):
            errors.append("source_id_required")
    elif event_name == "revisit_completed":
        if event.get("route") != "/my-research/":
            errors.append("revisit_route_required")
        if not isinstance(event.get("actor_ref"), str) or not ACTOR_RE.fullmatch(event["actor_ref"]):
            errors.append("actor_ref_required")
        if properties.get("new_auth_session") is not True:
            errors.append("new_auth_session_required")
    elif event_name == "export_completed":
        if event.get("route") != "/my-research/":
            errors.append("export_route_required")
        if not isinstance(event.get("actor_ref"), str) or not ACTOR_RE.fullmatch(event["actor_ref"]):
            errors.append("actor_ref_required")
        if properties.get("unique_sources_bucket") != "3+":
            errors.append("unique_sources_bucket_3_plus_required")
        if properties.get("export_format") not in {"json", "csv"}:
            errors.append("export_format_required")

    return {"ok": not errors, "read_only": True, "event_name": event_name, "errors": errors}


def validate_measurement_trace(events: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(events, list) or len(events) != len(EVENT_NAMES):
        return {
            "ok": False,
            "read_only": True,
            "event_count": len(events) if isinstance(events, list) else 0,
            "errors": ["trace_must_contain_exactly_five_events"],
        }
    event_results = [validate_measurement_event(event) for event in events]
    for index, result in enumerate(event_results):
        errors.extend(f"event_{index + 1}:{error}" for error in result["errors"])
    names = [event.get("event_name") if isinstance(event, dict) else None for event in events]
    if names != list(EVENT_NAMES):
        errors.append("event_sequence_mismatch")
    trace_ids = {
        event.get("trace_id")
        for event in events
        if isinstance(event, dict) and isinstance(event.get("trace_id"), str)
    }
    query_ids = {
        event.get("query_id")
        for event in events
        if isinstance(event, dict) and isinstance(event.get("query_id"), str)
    }
    if len(trace_ids) != 1:
        errors.append("trace_id_mismatch")
    if len(query_ids) != 1:
        errors.append("query_id_mismatch")
    event_ids = [event.get("event_id") for event in events if isinstance(event, dict) and isinstance(event.get("event_id"), str)]
    if len(set(event_ids)) != len(event_ids):
        errors.append("event_id_not_unique")
    times = [_parse_datetime(event.get("occurred_at")) for event in events if isinstance(event, dict)]
    if any(value is None for value in times) or any(left >= right for left, right in zip(times, times[1:])):
        errors.append("event_times_not_strictly_increasing")
    actor_values = [events[index].get("actor_ref") for index in (2, 3, 4) if isinstance(events[index], dict)]
    if len(actor_values) != 3 or len(set(actor_values)) != 1:
        errors.append("member_actor_ref_mismatch")
    return {
        "ok": not errors,
        "read_only": True,
        "event_count": len(events),
        "event_names": names,
        "errors": errors,
    }


def _command_result(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "manifest":
        return validate_production_manifest(_load_json(args.path))
    if args.command == "channels":
        return reconcile_channels(args.root.resolve())
    if args.command == "incident":
        return validate_incident_snapshot(_load_json(args.path))
    if args.command == "measurement":
        return validate_measurement_event(_load_json(args.path))
    if args.command == "trace":
        return validate_measurement_trace(_load_json(args.path))
    raise ValueError("unknown command")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Base2026 reliability contract validator.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--path", type=Path, default=MANIFEST_PATH)

    channels_parser = subparsers.add_parser("channels")
    channels_parser.add_argument("--root", type=Path, required=True)

    incident_parser = subparsers.add_parser("incident")
    incident_parser.add_argument("--snapshot", dest="path", type=Path, required=True)

    measurement_parser = subparsers.add_parser("measurement")
    measurement_parser.add_argument("--event", dest="path", type=Path, required=True)

    trace_parser = subparsers.add_parser("trace")
    trace_parser.add_argument("--input", dest="path", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        result = _command_result(args)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "read_only": True, "errors": ["input_unreadable"]}, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    success_key = "closure_ready" if args.command == "incident" else "ok" if args.command in {"manifest", "measurement", "trace"} else "valid"
    return 0 if result.get(success_key) is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
