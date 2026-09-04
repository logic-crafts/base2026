#!/usr/bin/env python3
"""Offline tests for the public evidence workflow."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("evidence_pack", ROOT / "evidence_pack.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload: dict):
        self.body = json.dumps(payload).encode("utf-8")
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return self.body


class FakeUrlOpen:
    def __init__(self, source_payloads: dict[str, dict]):
        self.source_payloads = source_payloads
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        message = json.loads(request.data.decode("utf-8"))
        if message["method"] == "server/discover":
            return FakeResponse({
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "resultType": "complete",
                    "supportedVersions": ["2026-07-28"],
                    "capabilities": {"tools": {}},
                    "_meta": {
                        "io.modelcontextprotocol/serverInfo": {
                            "name": "base2026-public-mcp",
                            "version": "fixture",
                        }
                    },
                },
            })
        source_id = message["params"]["arguments"]["source_id"]
        return FakeResponse({
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {
                "resultType": "complete",
                "content": [{"type": "text", "text": json.dumps(self.source_payloads[source_id])}],
                "structuredContent": self.source_payloads[source_id],
                "isError": False,
            },
        })


class EvidencePackTests(unittest.TestCase):
    def test_fixtures_preserve_found_and_not_found_unknowns(self):
        found = MODULE.validate_public_record(fixture("get_source_found.json"))
        missing = MODULE.validate_public_record(fixture("get_source_not_found.json"))
        found_record = MODULE.build_record("tiktok:example_creator:1234567890123456789", found)
        missing_record = MODULE.build_record("tiktok:fixture_creator:0000000000000000000", missing)

        self.assertEqual(found_record["unknowns"], [])
        self.assertEqual(missing_record["unknowns"], ["record_not_found"])
        self.assertEqual(found_record["public_record"]["source_url"], "https://www.tiktok.com/@example_creator/video/1234567890123456789")

    def test_collect_uses_modern_headers_and_is_deterministic(self):
        found_id = "tiktok:example_creator:1234567890123456789"
        missing_id = "tiktok:fixture_creator:0000000000000000000"
        opener = FakeUrlOpen({
            found_id: fixture("get_source_found.json"),
            missing_id: fixture("get_source_not_found.json"),
        })
        with patch.object(MODULE, "urlopen", opener):
            first = MODULE.collect_note("http://127.0.0.1:8787/api/mcp", [missing_id, found_id], timeout=4)
        self.assertEqual(first["summary"], {
            "requested_count": 2,
            "found_count": 1,
            "not_found_count": 1,
            "records_with_unknowns": 1,
        })
        self.assertEqual([record["requested_id"] for record in first["records"]], sorted([found_id, missing_id]))
        self.assertEqual(len(opener.requests), 3)
        discover_request = opener.requests[0][0]
        self.assertEqual(discover_request.get_header("Mcp-method"), "server/discover")
        self.assertEqual(discover_request.get_header("Mcp-protocol-version"), "2026-07-28")
        source_request = opener.requests[1][0]
        self.assertEqual(source_request.get_header("Mcp-method"), "tools/call")
        self.assertEqual(source_request.get_header("Mcp-name"), "get_source")
        self.assertEqual(source_request.get_header("Mcp-protocol-version"), "2026-07-28")

        reversed_records = list(reversed(first["records"]))
        second = MODULE.build_note([found_id, missing_id], reversed_records, first["transport"], endpoint=first["endpoint"])
        self.assertEqual(MODULE.canonical_json(first), MODULE.canonical_json(second))
        self.assertEqual(MODULE.render_markdown(first), MODULE.render_markdown(second))

    def test_bound_and_id_normalization(self):
        self.assertEqual(MODULE.normalize_ids(["b", "a", "a"]), ["a", "b"])
        with self.assertRaisesRegex(MODULE.EvidencePackError, "at most 8"):
            MODULE.normalize_ids([f"id-{index}" for index in range(9)])
        with self.assertRaisesRegex(MODULE.EvidencePackError, "whitespace"):
            MODULE.normalize_ids(["has whitespace"])

    def test_private_field_or_boundary_drift_fails_closed(self):
        payload = fixture("get_source_found.json")
        payload["private_payload"] = {"do_not_publish": True}
        with self.assertRaisesRegex(MODULE.EvidencePackError, "forbidden field"):
            MODULE.validate_public_record(payload)
        payload = fixture("get_source_found.json")
        payload["public_boundary"]["writes"] = True
        with self.assertRaisesRegex(MODULE.EvidencePackError, "read-only boundary"):
            MODULE.validate_public_record(payload)


if __name__ == "__main__":
    unittest.main()
