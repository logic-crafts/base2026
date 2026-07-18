from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "derive-base2026-phase0-p1-preview.py"
SPEC = importlib.util.spec_from_file_location("derive_base2026_phase0_p1_preview", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _dataset_manifest() -> dict[str, object]:
    return {
        "created_at": "2026-07-17T00:00:00Z",
        "dataset": "base2026-public-tiktok",
        "scope": "public TikTok-only export",
        "documents": 1,
        "source_records": 2,
        "chunks": 3,
        "passages": 3,
        "creators": 1,
        "topics": 1,
        "insight_cards": 1,
        "public_insight_cards": 1,
        "source_admission_active": True,
        "source_admission_counts": {
            "normal_public_card": 1,
            "provenance_archive_noindex": 1,
            "future_private_backlog": 1,
        },
        "include_full_transcripts": False,
        "auto_promote_insights": False,
        "insight_threshold": 0.45,
        "public_policy": "excerpt_only",
        "files": [
            "documents.jsonl",
            "chunks.jsonl",
            "source_records.jsonl",
            "passages.jsonl",
            "insight_cards.jsonl",
            "topics.jsonl",
            "creators.jsonl",
        ],
        "source_admission_ledger": "/private/source-admission.jsonl",
        "source_db": "C:\\private\\kb.sqlite",
    }


def test_dataset_overlay_removes_private_fields_and_adds_schema(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_dataset_manifest()), encoding="utf-8")

    payload = MODULE.sanitized_dataset_manifest(path)

    assert payload["schema"] == "base2026.public-dataset-manifest/v1"
    assert "source_admission_ledger" not in payload
    assert "source_db" not in payload


def test_page_overlay_emits_relative_routes_and_count(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    target = web_root / "alpha" / "index.html"
    target.parent.mkdir(parents=True)
    target.write_text("<!doctype html>", encoding="utf-8")
    path = web_root / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "style_version": "fixture",
                "pages": ["/private/output/releases/fixture/web/alpha/index.html"],
            }
        ),
        encoding="utf-8",
    )

    payload = MODULE.relative_page_manifest(path, web_root)

    assert payload == {
        "schema": "base2026.public-page-manifest/v1",
        "style_version": "fixture",
        "page_count": 1,
        "pages": ["alpha/index.html"],
    }


def test_inherited_source_detail_receipt_replaces_machine_paths(tmp_path: Path) -> None:
    path = tmp_path / "SOURCE_DETAIL_V2_PACKAGE_VALIDATION.json"
    path.write_text(
        json.dumps(
            {
                "schema": "fixture",
                "ok": True,
                "candidate": "/private/output/releases/example/SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json",
                "web_root": r"C:\\private\\output\\releases\\example\\web",
            }
        ),
        encoding="utf-8",
    )

    payload = MODULE.sanitized_source_detail_validation(path)

    assert payload["candidate"] == "SOURCE_DETAIL_V2_CANDIDATE_MANIFEST.json"
    assert payload["web_root"] == "web"
    assert MODULE.private_value_issues(payload) == []


def test_package_json_scan_is_pointer_only_and_allows_public_routes(tmp_path: Path) -> None:
    (tmp_path / "public.json").write_text(
        json.dumps({"route": "/knowledge/search/?q={query}"}), encoding="utf-8"
    )
    (tmp_path / "leak.json").write_text(
        json.dumps({"candidate": "/Users/example/private/candidate.json"}), encoding="utf-8"
    )

    files_scanned, issues = MODULE.package_json_private_path_issues(tmp_path)

    assert files_scanned == 2
    assert issues == [
        {
            "file": "leak.json",
            "pointer": "/candidate",
            "reason": "machine_local_posix_path",
        }
    ]
    assert "/Users/example" not in json.dumps(issues)


def test_deterministic_zip_ignores_mtime(tmp_path: Path) -> None:
    source = tmp_path / "release"
    source.mkdir()
    payload = source / "payload.txt"
    payload.write_text("stable\n", encoding="utf-8")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    MODULE.write_deterministic_zip(source, first)
    payload.touch()
    MODULE.write_deterministic_zip(source, second)
    assert first.read_bytes() == second.read_bytes()
