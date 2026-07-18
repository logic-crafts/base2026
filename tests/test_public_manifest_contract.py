from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "public_manifest_contract.py"
SPEC = importlib.util.spec_from_file_location("public_manifest_contract", MODULE_PATH)
assert SPEC and SPEC.loader
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


def dataset_manifest() -> dict:
    return {
        "schema": CONTRACT.PUBLIC_DATASET_MANIFEST_SCHEMA,
        "created_at": "2026-07-17T12:00:00",
        "dataset": "base2026-public-tiktok",
        "scope": "public TikTok-only export",
        "documents": 2,
        "source_records": 3,
        "chunks": 4,
        "passages": 5,
        "creators": 1,
        "topics": 2,
        "insight_cards": 3,
        "public_insight_cards": 2,
        "source_admission_active": True,
        "source_admission_counts": {
            "normal_public_card": 2,
            "provenance_archive_noindex": 1,
            "future_private_backlog": 1,
        },
        "include_full_transcripts": False,
        "auto_promote_insights": False,
        "insight_threshold": 0.45,
        "public_policy": "excerpt_only",
        "files": sorted(CONTRACT.PUBLIC_DATASET_FILES),
    }


def test_valid_dataset_manifest_passes_exact_allowlist() -> None:
    assert CONTRACT.validate_public_dataset_manifest(dataset_manifest()) == []


def test_undeclared_path_field_is_rejected_without_echoing_value() -> None:
    payload = dataset_manifest()
    leaked = "/Users/example/private/index.sqlite"
    payload["source_db"] = leaked

    issues = CONTRACT.validate_public_dataset_manifest(payload)
    serialized = json.dumps(issues)
    assert any(item["reason"] == "undeclared_key" for item in issues)
    assert leaked not in serialized


def test_private_path_in_dictionary_key_is_redacted_from_pointer() -> None:
    leaked_key = "/Users/example/private/index.sqlite"
    issues = CONTRACT.private_value_issues({"nested": {leaked_key: "safe"}})
    serialized = json.dumps(issues)

    assert any(item["reason"].endswith("_in_key") for item in issues)
    assert leaked_key not in serialized
    assert "/Users" not in serialized


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("/Users/example/project/data.json", "absolute_posix_path"),
        ("/root/private/data.json", "absolute_posix_path"),
        ("/srv/base2026/data.json", "absolute_posix_path"),
        ("prefix:/Users/example/project/data.json", "absolute_posix_path"),
        (r"C:\\Users\\example\\secret.db", "windows_absolute_path"),
        (r"prefix:C:\\Users\\example\\secret.db", "windows_absolute_path"),
        (r"\\\\server\\share\\secret.json", "unc_or_network_path"),
        (r"prefix:\\\\server\\share\\secret.json", "unc_or_network_path"),
        ("//server/share/secret.json", "unc_or_network_path"),
        ("file:///tmp/secret.json", "file_uri"),
        ("relative/.hermes/private.json", "private_hermes_path"),
        ("output/releases/private.json", "private_release_path"),
        ("12_knowledge-base/private.json", "private_knowledge_path"),
        ("source-admission.jsonl", "private_admission_ledger"),
        ("relative/private.sqlite", "private_database_path"),
    ],
)
def test_recursive_private_path_rejection_is_pointer_only(value: str, reason: str) -> None:
    issues = CONTRACT.private_value_issues({"nested": [{"payload": value}]})

    assert any(item == {"pointer": "/nested/0/payload", "reason": reason} for item in issues)
    assert value not in json.dumps(issues)


def test_public_https_urls_and_counts_are_not_path_leaks() -> None:
    payload = {"url": "https://aggressorbulkit.online/knowledge/sources/example.html", "count": 1493}
    assert CONTRACT.private_value_issues(payload) == []


def test_package_scan_allows_public_root_routes_but_rejects_machine_paths() -> None:
    public_payload = {
        "query_url_format": "/knowledge/search/?q={query}",
        "avatar_url": "/knowledge/static/assets/avatar.webp",
    }
    assert CONTRACT.machine_local_value_issues(public_payload) == []

    leaked = "prefix:/Users/example/private/export.json"
    issues = CONTRACT.machine_local_value_issues({"receipt": leaked})
    assert issues == [{"pointer": "/receipt", "reason": "machine_local_posix_path"}]
    assert leaked not in json.dumps(issues)


def test_page_manifest_requires_relative_existing_posix_routes(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    target = web_root / "topic" / "index.html"
    target.parent.mkdir(parents=True)
    target.write_text("<!doctype html>", encoding="utf-8")
    payload = {
        "schema": CONTRACT.PUBLIC_PAGE_MANIFEST_SCHEMA,
        "style_version": "v1",
        "page_count": 1,
        "pages": ["topic/index.html"],
    }

    assert CONTRACT.validate_public_page_manifest(payload, web_root) == []


@pytest.mark.parametrize(
    "route",
    [
        "/topic/index.html",
        "../topic/index.html",
        r"topic\\index.html",
        "https://example.com/topic/index.html",
        "//server/share/index.html",
    ],
)
def test_page_manifest_rejects_non_relative_routes(tmp_path: Path, route: str) -> None:
    payload = {
        "schema": CONTRACT.PUBLIC_PAGE_MANIFEST_SCHEMA,
        "style_version": "v1",
        "page_count": 1,
        "pages": [route],
    }
    assert CONTRACT.validate_public_page_manifest(payload, tmp_path)


def test_validator_cli_fails_closed_with_no_inputs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate-public-manifests.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "no_manifest_inputs" in result.stdout
