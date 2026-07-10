from __future__ import annotations

import importlib.util
import unittest
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "base2026-apply-chatgpt-review.py"
SPEC = importlib.util.spec_from_file_location("apply_semantic_review", MODULE_PATH)
assert SPEC and SPEC.loader
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


class ApplySemanticReviewTests(unittest.TestCase):
    def args(self) -> Namespace:
        return Namespace(
            min_quality_score=4,
            max_new_candidates_per_source=3,
            max_claim_chars=220,
            max_action_chars=280,
            max_evidence_chars=900,
        )

    def packet(self) -> dict:
        return {
            "review_batch_id": "batch-1",
            "prompt_version": "base2026-semantic-review-v2",
            "sources": [
                {
                    "source_id": "tiktok:test:123",
                    "item_id": "tiktok-video-123",
                    "creator_handle": "@test",
                    "passages": [{"body": "Exact public evidence."}],
                    "candidates": [],
                }
            ],
        }

    def review(self) -> dict:
        return {
            "review_batch_id": "batch-1",
            "reviewer_model": "gpt-5.6-sol",
            "reviewer_endpoint_type": "hermes-agent-session",
            "decisions": [
                {
                    "source_id": "tiktok:test:123",
                    "candidate_id": "new:tiktok:test:123:1",
                    "decision": "new_candidate",
                    "reason": "Specific source-backed claim.",
                    "topic_label": "Test topic",
                    "claim_text": "A concise claim.",
                    "suggested_action": "Take a bounded action.",
                    "evidence_excerpt": "Exact public evidence.",
                    "quality_score": 5,
                }
            ],
        }

    def test_explicit_reviewer_provenance_is_preserved(self) -> None:
        rows, stats = reviewer.apply_review(self.packet(), self.review(), self.args())
        self.assertEqual(stats["written"], 1)
        self.assertEqual(rows[0]["model_name"], "gpt-5.6-sol")
        self.assertEqual(rows[0]["model_endpoint_type"], "hermes-agent-session")
        self.assertEqual(rows[0]["prompt_version"], "base2026-semantic-review-v2")

    def test_missing_provenance_never_claims_a_specific_model(self) -> None:
        review = self.review()
        review.pop("reviewer_model")
        review.pop("reviewer_endpoint_type")
        rows, _stats = reviewer.apply_review(self.packet(), review, self.args())
        self.assertEqual(rows[0]["model_name"], "unspecified-reviewer")
        self.assertEqual(rows[0]["model_endpoint_type"], "review_json_import")


if __name__ == "__main__":
    unittest.main()
