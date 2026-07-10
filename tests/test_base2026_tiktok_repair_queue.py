from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "base2026-tiktok-repair-queue.py"
SPEC = importlib.util.spec_from_file_location("base2026_tiktok_repair_queue", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TerminalLocalNotLiveDecisionTests(unittest.TestCase):
    def test_only_explicit_terminal_allowlisted_decisions_are_loaded(self) -> None:
        rows = [
            {
                "source_id": "source:approved",
                "decision": "carry_forward_to_redesign_release",
                "terminal_for_content_freeze": True,
            },
            {
                "source_id": "source:not-terminal",
                "decision": "carry_forward_to_redesign_release",
                "terminal_for_content_freeze": False,
            },
            {
                "source_id": "source:unknown-decision",
                "decision": "publish_now",
                "terminal_for_content_freeze": True,
            },
            {
                "source_id": "",
                "decision": "retain_provenance_no_card",
                "terminal_for_content_freeze": True,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            decisions = MODULE.terminal_local_not_live_decisions(path)
        self.assertEqual(decisions, {"source:approved": "carry_forward_to_redesign_release"})

    def test_source_review_loader_requires_terminal_allowlisted_decision(self) -> None:
        rows = [
            {
                "video_id": "terminal-video",
                "decision": "cold_hold_no_source_or_audio",
                "terminal_for_content_freeze": True,
            },
            {
                "video_id": "active-video",
                "decision": "cold_hold_no_source_or_audio",
                "terminal_for_content_freeze": False,
            },
            {
                "video_id": "unsafe-video",
                "decision": "publish_now",
                "terminal_for_content_freeze": True,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-review-decisions.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            decisions = MODULE.terminal_source_review_decisions(path)
        self.assertEqual(decisions, {"terminal-video": "cold_hold_no_source_or_audio"})

    def test_source_review_loader_accepts_asr_insufficient_private_hold(self) -> None:
        rows = [
            {
                "video_id": "failed-asr",
                "decision": "asr_insufficient_private_hold",
                "terminal_for_content_freeze": True,
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-review-decisions.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            decisions = MODULE.terminal_source_review_decisions(path)
        self.assertEqual(decisions, {"failed-asr": "asr_insufficient_private_hold"})

    def test_needs_insight_loader_accepts_only_terminal_future_backlog(self) -> None:
        rows = [
            {
                "source_id": "source:future",
                "decision": "future_cluster_backlog",
                "terminal_for_content_freeze": True,
            },
            {
                "source_id": "source:not-terminal",
                "decision": "future_cluster_backlog",
                "terminal_for_content_freeze": False,
            },
            {
                "source_id": "source:approved",
                "decision": "approve_card",
                "terminal_for_content_freeze": True,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "needs-insight-decisions.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            decisions = MODULE.terminal_needs_insight_decisions(path)
        self.assertEqual(decisions, {"source:future": "future_cluster_backlog"})


if __name__ == "__main__":
    unittest.main()
