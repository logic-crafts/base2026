from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "base2026-tiktok-pipeline-v2.py"
SPEC = importlib.util.spec_from_file_location("pipeline_v2", MODULE_PATH)
assert SPEC and SPEC.loader
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)


class PipelineV2Tests(unittest.TestCase):
    def test_work_id_is_stable_and_content_addressed(self) -> None:
        first = pipeline.stable_work_id("123", "abc", "2.0.0")
        self.assertEqual(first, pipeline.stable_work_id("123", "abc", "2.0.0"))
        self.assertNotEqual(first, pipeline.stable_work_id("123", "changed", "2.0.0"))
        self.assertNotEqual(first, pipeline.stable_work_id("123", "abc", "2.1.0"))

    def test_classification_order(self) -> None:
        source = {
            "public_source_text": "evidence",
            "topics": ["ai-visibility"],
            "source_summary_short": "A source-backed summary.",
            "source_url": "https://example.test/source",
            "full_transcript_public": False,
        }
        base = dict(
            transcript_status="transcribed",
            word_count=100,
            polished_exists=True,
            qa_status="pass",
            source=source,
            public_insights=1,
            passage_count=1,
        )
        stage, _ = pipeline.classify_item(**base)
        self.assertEqual(stage, "content_ready")
        promoted_with_old_qa = {**base, "qa_status": "needs_review"}
        stage, _ = pipeline.classify_item(**promoted_with_old_qa)
        self.assertEqual(stage, "content_ready")

        cases = [
            ({**base, "transcript_status": "needs_source_review", "public_insights": 0}, "source_review"),
            ({**base, "polished_exists": False, "word_count": 5, "source": {}, "public_insights": 0}, "low_information_hold"),
            ({**base, "polished_exists": False, "source": {}, "public_insights": 0}, "needs_polish"),
            ({**base, "qa_status": "needs_review", "public_insights": 0}, "source_review"),
            ({**base, "source": {}}, "needs_rebuild"),
            ({**base, "public_insights": 0}, "needs_insight"),
            ({**base, "source": {**source, "topics": []}}, "needs_topic_repair"),
            ({**base, "source": {**source, "source_summary_short": ""}}, "page_noindex"),
        ]
        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                stage, _ = pipeline.classify_item(**kwargs)
                self.assertEqual(stage, expected)

    def test_reviewed_no_card_stays_noindex(self) -> None:
        stage, reasons = pipeline.classify_item(
            transcript_status="transcribed",
            word_count=120,
            polished_exists=True,
            qa_status="pass",
            source={"public_source_text": "x", "source_url": "https://example.test"},
            public_insights=0,
            passage_count=1,
            reviewed_no_card=True,
        )
        self.assertEqual(stage, "page_noindex")
        self.assertIn("reviewed_without_public_insight", reasons)

    def test_packet_respects_limit_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = []
            for index in range(3):
                clean = root / f"{index}.txt"
                clean.write_text("word " * 40, encoding="utf-8")
                rows.append(
                    {
                        "work_id": f"work-{index}",
                        "video_id": str(index),
                        "clean_path": clean.name,
                        "stage": "needs_polish",
                    }
                )
            packet = pipeline.build_packet(
                rows,
                stage="needs_polish",
                limit=2,
                max_input_chars=10000,
                root=root,
            )
            self.assertEqual(packet["item_count"], 2)
            self.assertEqual(packet["packet_id"], pipeline.stable_packet_id("needs_polish", ["work-0", "work-1"]))
            self.assertLessEqual(packet["estimated_input_chars"], 10000)

    def test_source_indexability_requires_value_and_attribution(self) -> None:
        source = {
            "public_source_text": "Useful source text",
            "topics": ["ai-visibility"],
            "source_summary_short": "A grounded summary",
            "source_url": "https://example.test/source",
            "full_transcript_public": False,
        }
        self.assertEqual(pipeline.source_indexability(source, 1, 1), (True, []))
        eligible, reasons = pipeline.source_indexability({**source, "topics": []}, 1, 1)
        self.assertFalse(eligible)
        self.assertIn("missing_topic", reasons)


if __name__ == "__main__":
    unittest.main()
