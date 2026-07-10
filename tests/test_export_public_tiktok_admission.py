from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export-public-tiktok.py"
spec = importlib.util.spec_from_file_location("export_public_tiktok", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class SourceAdmissionTest(unittest.TestCase):
    def write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_missing_ledger_preserves_legacy_normal_default(self) -> None:
        state = exporter.source_admission_state("source:one", {}, ledger_active=False)
        self.assertEqual(state, "normal_public_card")

    def test_active_ledger_quarantines_unknown_source(self) -> None:
        state = exporter.source_admission_state("source:unknown", {}, ledger_active=True)
        self.assertEqual(state, "private_hold_unclassified")

    def test_ledger_loads_three_terminal_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "admission.jsonl"
            self.write_jsonl(
                path,
                [
                    {"source_id": "source:normal", "admission_state": "normal_public_card"},
                    {"source_id": "source:future", "admission_state": "future_private_backlog"},
                    {"source_id": "source:archive", "admission_state": "provenance_archive_noindex"},
                ],
            )
            rows = exporter.load_source_admission(path)
            self.assertEqual(
                rows,
                {
                    "source:normal": "normal_public_card",
                    "source:future": "future_private_backlog",
                    "source:archive": "provenance_archive_noindex",
                },
            )

    def test_duplicate_or_invalid_rows_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            duplicate = Path(tmp) / "duplicate.jsonl"
            self.write_jsonl(
                duplicate,
                [
                    {"source_id": "source:one", "admission_state": "normal_public_card"},
                    {"source_id": "source:one", "admission_state": "provenance_archive_noindex"},
                ],
            )
            with self.assertRaisesRegex(ValueError, "duplicate source_id"):
                exporter.load_source_admission(duplicate)

            invalid = Path(tmp) / "invalid.jsonl"
            self.write_jsonl(invalid, [{"source_id": "source:bad", "admission_state": "delete"}])
            with self.assertRaisesRegex(ValueError, "invalid admission_state"):
                exporter.load_source_admission(invalid)


if __name__ == "__main__":
    unittest.main()
