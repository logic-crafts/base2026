from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "base2026-review-insight-candidates.py"
SPEC = importlib.util.spec_from_file_location("review_insight_candidates", MODULE_PATH)
assert SPEC and SPEC.loader
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


class ScopedInsightCandidateReviewTests(unittest.TestCase):
    def write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def test_source_scope_excludes_unrelated_pending_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "kb.sqlite"
            con = sqlite3.connect(db)
            try:
                con.executescript(
                    """
                    CREATE TABLE claims (
                      claim_id TEXT PRIMARY KEY,
                      claim_text TEXT,
                      topic TEXT,
                      claim_type TEXT,
                      suggested_action TEXT,
                      confidence REAL,
                      review_status TEXT,
                      created_at TEXT,
                      updated_at TEXT
                    );
                    CREATE TABLE claim_evidence (
                      claim_id TEXT,
                      video_id TEXT,
                      evidence_path TEXT,
                      quote_or_span TEXT
                    );
                    """
                )
                for suffix in ("1", "2"):
                    con.execute(
                        "INSERT INTO claims VALUES (?, ?, ?, 'insight_card_candidate', ?, 1.0, 'pending', '2026-07-10', '2026-07-10')",
                        (f"claim-{suffix}", f"Source-backed claim number {suffix} with enough text.", "Test topic", "Take one specific bounded action and measure its result."),
                    )
                    con.execute(
                        "INSERT INTO claim_evidence VALUES (?, ?, ?, ?)",
                        (f"claim-{suffix}", suffix, f"artifact#source_id=tiktok:test:{suffix}", f"Exact evidence passage for source {suffix}."),
                    )
                con.commit()
            finally:
                con.close()

            data_root = root / "data"
            sources = [
                {
                    "source_id": f"tiktok:test:{suffix}",
                    "video_id": suffix,
                    "creator_handle": "@test",
                    "source_url": f"https://example.test/{suffix}",
                    "full_transcript_public": False,
                    "public_policy": "excerpt_only",
                }
                for suffix in ("1", "2")
            ]
            passages = [
                {"source_id": f"tiktok:test:{suffix}", "body": f"Exact evidence passage for source {suffix}."}
                for suffix in ("1", "2")
            ]
            self.write_jsonl(data_root / "source_records.jsonl", sources)
            self.write_jsonl(data_root / "passages.jsonl", passages)
            scope = root / "scope.jsonl"
            self.write_jsonl(scope, [{"source_id": "tiktok:test:1"}])

            args = Namespace(
                db=db,
                data_root=data_root,
                status="pending",
                source_ids_jsonl=scope,
                max_promotion_candidates_per_source=2,
                min_claim_chars=35,
                max_claim_chars=220,
                min_action_chars=35,
                max_action_chars=280,
                min_evidence_chars=20,
                max_evidence_chars=900,
            )
            report = reviewer.review_candidates(args)
            self.assertEqual(report["source_scope_count"], 1)
            self.assertEqual(report["total_candidates"], 1)
            self.assertEqual(report["candidates"][0]["source_id"], "tiktok:test:1")
            self.assertEqual(report["candidates"][0]["recommended_status"], "promotion_candidate")


if __name__ == "__main__":
    unittest.main()
