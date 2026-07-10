from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "tiktok-faithful-polish-local.py"
SPEC = importlib.util.spec_from_file_location("tiktok_faithful_polish_local", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FaithfulPolishQaTests(unittest.TestCase):
    def test_normal_spoken_contractions_do_not_trigger_source_review(self) -> None:
        raw = (
            "We're gonna test the page, and I wanna compare the result before we publish. "
            "We've gotta preserve every factual claim and check the final output carefully."
        )
        polished, metrics = MODULE.polish_text(raw)
        status, notes = MODULE.qa_status(raw, polished, metrics)
        self.assertEqual(status, "pass", notes)

    def test_explicit_uncertainty_marker_still_triggers_review(self) -> None:
        raw = (
            "The speaker describes the setup, but this product name is unclear and needs verification. "
            "The remaining transcript is long enough to pass the minimum word-count gate."
        )
        polished, metrics = MODULE.polish_text(raw)
        status, notes = MODULE.qa_status(raw, polished, metrics)
        self.assertEqual(status, "needs_review")
        self.assertIn("Raw transcript contains wording that may need audio/source review.", notes)


if __name__ == "__main__":
    unittest.main()
