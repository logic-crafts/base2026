from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "apply-base2026-editorial-decisions.py"
SPEC = importlib.util.spec_from_file_location("apply_base2026_editorial_decisions", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EditorialDecisionTests(unittest.TestCase):
    def test_exact_evidence_creates_approved_candidate(self) -> None:
        source_id = "source:tiktok:1"
        decisions = {
            source_id: {
                "source_id": source_id,
                "decision": "approve_card",
                "target_cluster": "answer-ready",
                "claim_text": "Answer the exact customer question.",
                "suggested_action": "Add a direct answer.",
                "evidence_excerpt": "answer the exact question",
                "reason": "Reusable method.",
                "confidence": 0.9,
            }
        }
        sources = {source_id: {"source_id": source_id, "video_id": "1", "item_id": "tiktok:1", "url": "https://example.com/1", "creator_handle": "creator"}}
        passages = {source_id: [{"body": "The page should answer the exact question before expanding.", "evidence_path": "evidence.txt"}]}
        approved, no_card, ledger = MODULE.validate_and_prepare(decisions, sources, passages, "2026-07-10T00:00:00Z")
        self.assertEqual(len(approved), 1)
        self.assertEqual(no_card, [])
        self.assertEqual(ledger[0]["decision"], "approve_card")

    def test_claim_and_action_aliases_are_accepted(self) -> None:
        source_id = "source:tiktok:alias"
        decisions = {
            source_id: {
                "source_id": source_id,
                "decision": "approve_card",
                "target_cluster": "answer-ready",
                "claim": "Use a direct answer.",
                "action": "Add the answer near the top.",
                "evidence_excerpt": "direct answer near the top",
                "reason": "Delegated ledger schema.",
                "confidence": 0.9,
            }
        }
        sources = {source_id: {"source_id": source_id}}
        passages = {source_id: [{"body": "Put a direct answer near the top of the page.", "evidence_path": "evidence.txt"}]}
        approved, _, _ = MODULE.validate_and_prepare(decisions, sources, passages, "2026-07-10T00:00:00Z")
        self.assertEqual(approved[0]["claim_text"], "Use a direct answer.")
        self.assertEqual(approved[0]["suggested_action"], "Add the answer near the top.")
        self.assertEqual(approved[0]["evidence_path"], "evidence.txt")

    def test_non_exact_evidence_is_rejected(self) -> None:
        source_id = "source:tiktok:1"
        decisions = {
            source_id: {
                "source_id": source_id,
                "decision": "approve_card",
                "target_cluster": "answer-ready",
                "claim_text": "Answer the exact customer question.",
                "suggested_action": "Add a direct answer.",
                "evidence_excerpt": "wording not present",
                "reason": "Reusable method.",
                "confidence": 0.9,
            }
        }
        sources = {source_id: {"source_id": source_id}}
        passages = {source_id: [{"body": "Different evidence.", "evidence_path": "evidence.txt"}]}
        with self.assertRaisesRegex(ValueError, "evidence excerpt"):
            MODULE.validate_and_prepare(decisions, sources, passages, "2026-07-10T00:00:00Z")

    def test_coverage_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Coverage mismatch"):
            MODULE.validate_coverage([{"source_id": "source:tiktok:1"}], {})

    def test_candidate_promotion_preserves_audit_fields(self) -> None:
        existing = [{"source_id": "source:one", "claim_id": "old-claim", "review_status": "needs_human"}]
        additions = [{"source_id": "source:one", "claim_id": "new-claim", "review_status": "approved"}]
        merged = MODULE.merge_reviewed_candidates(existing, additions)
        self.assertEqual(merged[0]["claim_id"], "new-claim")
        self.assertEqual(merged[0]["supersedes_claim_id"], "old-claim")
        self.assertEqual(merged[0]["previous_review_status"], "needs_human")

    def test_terminal_candidate_cannot_be_overwritten(self) -> None:
        existing = [{"source_id": "source:one", "claim_id": "old-claim", "review_status": "approved"}]
        additions = [{"source_id": "source:one", "claim_id": "new-claim", "review_status": "approved"}]
        with self.assertRaisesRegex(ValueError, "terminal reviewed candidate"):
            MODULE.merge_reviewed_candidates(existing, additions)

    def test_terminal_ledger_merges_without_dropping_previous_batches(self) -> None:
        existing = [{"source_id": "source:one", "decision": "future_cluster_backlog"}]
        additions = [{"source_id": "source:two", "decision": "reviewed_no_card"}]
        merged = MODULE.merge_terminal_ledger(existing, additions)
        self.assertEqual({row["source_id"] for row in merged}, {"source:one", "source:two"})

    def test_terminal_ledger_rejects_conflicting_decision(self) -> None:
        existing = [{"source_id": "source:one", "decision": "future_cluster_backlog"}]
        additions = [{"source_id": "source:one", "decision": "reviewed_no_card"}]
        with self.assertRaisesRegex(ValueError, "conflicting terminal decision"):
            MODULE.merge_terminal_ledger(existing, additions)

    def test_future_backlog_without_assigned_cluster_is_terminal(self) -> None:
        source_id = "source:tiktok:future"
        decisions = {
            source_id: {
                "source_id": source_id,
                "decision": "future_cluster_backlog",
                "target_cluster": "",
                "reason": "Useful later, outside current contracts.",
                "confidence": 0.8,
            }
        }
        approved, no_card, ledger = MODULE.validate_and_prepare(decisions, {}, {}, "2026-07-10T00:00:00Z")
        self.assertEqual(approved, [])
        self.assertEqual(no_card, [])
        self.assertEqual(ledger[0]["backlog_bucket"], "unassigned_future_cluster")
        self.assertTrue(ledger[0]["terminal_for_content_freeze"])


if __name__ == "__main__":
    unittest.main()
