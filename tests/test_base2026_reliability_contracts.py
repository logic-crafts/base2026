import hashlib
import json
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "validate_base2026_reliability",
    ROOT / "scripts" / "validate-base2026-reliability.py",
)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_job(
    directory: Path,
    *,
    channel: str,
    state: str,
    response: bool = False,
    publication_receipt: bool = False,
) -> None:
    payload = b"synthetic public-safe channel payload\n"
    artifact_name = "response.md" if response else "draft.md"
    artifact_path = directory / artifact_name
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(payload)
    job = {
        "schema_version": "base2026.channel-author-job.v1",
        "state": state,
        "channel": channel,
        "marker": f"{channel}-synthetic-20260901",
        "response_file" if response else "draft_file": artifact_name,
        "response_sha256" if response else "draft_sha256": hashlib.sha256(payload).hexdigest(),
    }
    if publication_receipt:
        receipt = directory / "publication.json"
        receipt.write_text("{}\n", encoding="utf-8")
        job["publication_receipt"] = receipt.name
    write_json(directory / "job.json", job)


def valid_incident_snapshot() -> dict:
    return {
        "schema_version": "base2026.private-pipeline-incident-snapshot.v1",
        "read_only": True,
        "incident_id": "new_ai_runtime_failures",
        "expected_environment": "production",
        "actual_environment": "production",
        "bounded_cohort": {
            "cohort_id": "cohort_synthetic01",
            "items": [
                {
                    "item_id": "item_0001",
                    "terminal": True,
                    "terminal_receipt": True,
                    "terminal_state": "completed",
                }
            ],
        },
        "orphan_jobs": 0,
        "public_projection_count": 0,
        "accounting_complete": True,
        "external_effects_replayed": False,
        "doctor_runs": [
            {"status": "healthy", "incident_ids": []},
            {"status": "ok", "incident_ids": []},
        ],
    }


def measurement_trace() -> list[dict]:
    common = {
        "schema_version": "base2026.measurement-event.v1",
        "trace_id": "trace_12345678",
        "query_id": "qry_12345678",
    }
    return [
        {
            **common,
            "event_id": "evt_00000001",
            "event_name": "search_submitted",
            "occurred_at": "2026-09-01T20:00:00Z",
            "route": "/tools/evidence-search/",
            "properties": {"query_length_bucket": "4-8", "result_count_bucket": "11-25"},
        },
        {
            **common,
            "event_id": "evt_00000002",
            "event_name": "result_opened",
            "occurred_at": "2026-09-01T20:00:01Z",
            "route": "/tools/evidence-search/",
            "source_id": "src_0001",
            "properties": {},
        },
        {
            **common,
            "event_id": "evt_00000003",
            "event_name": "save_completed",
            "occurred_at": "2026-09-01T20:00:02Z",
            "route": "/tools/evidence-search/",
            "actor_ref": "usr_12345678",
            "source_id": "src_0001",
            "properties": {},
        },
        {
            **common,
            "event_id": "evt_00000004",
            "event_name": "revisit_completed",
            "occurred_at": "2026-09-01T20:00:03Z",
            "route": "/my-research/",
            "actor_ref": "usr_12345678",
            "properties": {"new_auth_session": True},
        },
        {
            **common,
            "event_id": "evt_00000005",
            "event_name": "export_completed",
            "occurred_at": "2026-09-01T20:00:04Z",
            "route": "/my-research/",
            "actor_ref": "usr_12345678",
            "properties": {"unique_sources_bucket": "3+", "export_format": "json"},
        },
    ]


class ProductionManifestTests(unittest.TestCase):
    def test_checked_in_manifest_is_valid_and_explicitly_non_reproducible(self):
        manifest = json.loads(
            (ROOT / "docs" / "reliability" / "BASE2026_PRODUCTION_MANIFEST_2026-09-01.json").read_text(
                encoding="utf-8"
            )
        )
        result = MODULE.validate_production_manifest(manifest)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["exact_commit_binding"], "unresolved")
        self.assertFalse(result["reproducible_from_commit"])
        self.assertTrue(result["binding_drift_present"])
        self.assertFalse(result["release_ready"])

    def test_manifest_rejects_mutation(self):
        manifest = json.loads(
            (ROOT / "docs" / "reliability" / "BASE2026_PRODUCTION_MANIFEST_2026-09-01.json").read_text(
                encoding="utf-8"
            )
        )
        manifest["production_mutation_performed"] = True
        result = MODULE.validate_production_manifest(manifest)
        self.assertFalse(result["ok"])
        self.assertIn("production_mutation_performed", result["errors"])


class ChannelReconciliationTests(unittest.TestCase):
    def test_known_drift_is_held_and_unknown_effect_is_fenced_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dev = root / "channel-chats" / "dev-synthetic"
            dev.mkdir(parents=True)
            write_json(
                dev / "job.json",
                {
                    "schema_version": "base2026.channel-publication-job.v1",
                    "state": "native_draft_saved",
                    "channel": "dev",
                    "marker": "dev-synthetic-20260901",
                    "post_file": "post.md",
                },
            )
            make_job(root / "channel-chats" / "linkedin-synthetic", channel="linkedin", state="published_verified", response=True, publication_receipt=True)
            make_job(root / "channel-chats" / "medium-synthetic", channel="medium", state="published_verified", response=True, publication_receipt=True)
            make_job(root / "channel-chats" / "x-synthetic", channel="x", state="publishing", response=True)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

            result = MODULE.reconcile_channels(root)

            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            self.assertEqual(before, after)
            self.assertEqual(result["job_count"], 4)
            self.assertEqual(result["invalid_count"], 2)
            self.assertFalse(result["valid"])
            by_channel = {item["channel"]: item for item in result["jobs"]}
            self.assertEqual(by_channel["dev"]["canonical_disposition"], "held_contract")
            self.assertEqual(by_channel["dev"]["next_action"], "repair_job_contract")
            self.assertEqual(by_channel["x"]["canonical_disposition"], "fenced_no_retry")
            self.assertEqual(by_channel["x"]["next_action"], "inspect_same_external_target_before_retry")
            self.assertFalse(by_channel["x"]["replay_performed"])
            self.assertEqual(by_channel["linkedin"]["canonical_disposition"], "terminal_verified")
            self.assertEqual(by_channel["medium"]["canonical_disposition"], "terminal_verified")


class IncidentClosureTests(unittest.TestCase):
    def test_bounded_cohort_and_two_clean_doctor_runs_close_incident(self):
        result = MODULE.validate_incident_snapshot(valid_incident_snapshot())
        self.assertTrue(result["closure_ready"], result["errors"])
        self.assertEqual(result["checked_item_count"], 1)
        self.assertEqual(result["doctor_runs_checked"], 2)
        self.assertFalse(result["external_action_performed"])

    def test_shadow_or_degraded_snapshot_stays_open(self):
        snapshot = valid_incident_snapshot()
        snapshot["actual_environment"] = "shadow"
        snapshot["orphan_jobs"] = 1
        snapshot["public_projection_count"] = 1
        snapshot["accounting_complete"] = False
        snapshot["external_effects_replayed"] = True
        snapshot["doctor_runs"][-1] = {"status": "degraded", "incident_ids": [snapshot["incident_id"]]}
        result = MODULE.validate_incident_snapshot(snapshot)
        self.assertFalse(result["closure_ready"])
        for error in (
            "environment_mismatch",
            "orphan_jobs_nonzero",
            "public_projection_detected",
            "accounting_incomplete",
            "external_effect_replay_detected",
            "doctor_run_degraded_or_failed",
            "doctor_run_still_degraded_by_incident",
        ):
            self.assertIn(error, result["errors"])


class MeasurementContractTests(unittest.TestCase):
    def test_five_event_trace_is_valid(self):
        trace = measurement_trace()
        self.assertTrue(MODULE.validate_measurement_trace(trace)["ok"])
        for event in trace:
            self.assertTrue(MODULE.validate_measurement_event(event)["ok"])

    def test_raw_query_and_incomplete_revisit_are_rejected(self):
        trace = measurement_trace()
        trace[0]["properties"]["query"] = "do not store this"
        self.assertFalse(MODULE.validate_measurement_event(trace[0])["ok"])
        trace = measurement_trace()
        trace[3]["properties"]["new_auth_session"] = False
        result = MODULE.validate_measurement_trace(trace)
        self.assertFalse(result["ok"])
        self.assertIn("event_4:new_auth_session_required", result["errors"])

    def test_contract_files_are_valid_json_with_expected_versions(self):
        expected = {
            "base2026.production-manifest.schema.json": "base2026.production-manifest.v1",
            "base2026.channel-publication-job.schema.json": "base2026.channel-publication-job.v2",
            "base2026.measurement-event.schema.json": "base2026.measurement-event.v1",
            "base2026.private-pipeline-incident-snapshot.schema.json": "base2026.private-pipeline-incident-snapshot.v1",
        }
        for filename, version in expected.items():
            payload = json.loads((ROOT / "contracts" / filename).read_text(encoding="utf-8"))
            if filename == "base2026.production-manifest.schema.json":
                self.assertEqual(payload["properties"]["schema_version"]["const"], version)
            elif filename == "base2026.channel-publication-job.schema.json":
                self.assertEqual(payload["properties"]["schema_version"]["const"], version)
            elif filename == "base2026.measurement-event.schema.json":
                self.assertEqual(payload["properties"]["schema_version"]["const"], version)
            else:
                self.assertEqual(payload["properties"]["schema_version"]["const"], version)


if __name__ == "__main__":
    unittest.main()
