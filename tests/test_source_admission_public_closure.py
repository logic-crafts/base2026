from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-source-admission-public-closure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("source_admission_public_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    ledger = tmp_path / "source-admission.jsonl"
    export = tmp_path / "export"
    export.mkdir()
    write_jsonl(
        ledger,
        [
            {
                "item_id": "tiktok-video-100",
                "source_id": "tiktok:creator:100",
                "admission_state": "normal_public_card",
            },
            {
                "item_id": "tiktok-video-200",
                "source_id": "tiktok:creator:200",
                "admission_state": "provenance_archive_noindex",
            },
            {
                "item_id": "tiktok-video-300",
                "source_id": "tiktok:creator:300",
                "admission_state": "future_private_backlog",
            },
        ],
    )
    write_jsonl(
        export / "source_records.jsonl",
        [
            {"item_id": "tiktok-video-100", "admission_state": "normal_public_card"},
            {
                "item_id": "tiktok-video-200",
                "admission_state": "provenance_archive_noindex",
            },
        ],
    )
    (export / "manifest.json").write_text('{"schema":"fixture"}\n', encoding="utf-8")
    return ledger, export


def test_generic_closure_proves_complete_future_set_absent(tmp_path: Path) -> None:
    module = load_module()
    ledger, export = fixture(tmp_path)
    receipt = module.build_receipt(
        ledger,
        export,
        ledger_label="fixture-ledger",
        export_label="fixture-export",
    )
    assert receipt["status"] == "PASS"
    assert receipt["admission_counts"]["future_private_backlog"] == 1
    assert receipt["verification"][
        "all_future_private_identifiers_absent_from_all_public_export_files"
    ] is True
    assert "all_13_absent_from_all_public_export_files" not in receipt["verification"]


def test_generic_closure_fails_on_future_identifier_leak(tmp_path: Path) -> None:
    module = load_module()
    ledger, export = fixture(tmp_path)
    (export / "passages.jsonl").write_text(
        '{"source_id":"tiktok:creator:300"}\n', encoding="utf-8"
    )
    receipt = module.build_receipt(
        ledger,
        export,
        ledger_label="fixture-ledger",
        export_label="fixture-export",
    )
    assert receipt["status"] == "FAIL"
    assert receipt["verification"]["leaked_public_file_count"] == 1
