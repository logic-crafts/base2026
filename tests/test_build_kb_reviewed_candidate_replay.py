from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-kb-sqlite.py"
SPEC = importlib.util.spec_from_file_location("build_kb_sqlite", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReviewedCandidateReplayTests(unittest.TestCase):
    def test_legacy_text_field_replays_as_claim_text(self) -> None:
        row = {
            "claim_id": "claim:editorial:one",
            "text": "Legacy approved insight.",
            "video_id": "123",
            "source_id": "tiktok:creator:123",
            "topic": "answer-ready",
            "suggested_action": "Use the insight.",
            "review_status": "approved",
            "evidence_excerpt": "Exact evidence.",
        }
        with tempfile.TemporaryDirectory(dir=MODULE.KB) as tmp:
            path = Path(tmp) / "reviewed.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            loaded = MODULE.load_reviewed_candidate_claims(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["claim_text"], "Legacy approved insight.")
        self.assertEqual(loaded[0]["review_status"], "approved")
        self.assertEqual(loaded[0]["quote_or_span"], "Exact evidence.")


if __name__ == "__main__":
    unittest.main()
