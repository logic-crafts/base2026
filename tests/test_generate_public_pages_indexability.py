from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate-public-pages.py"
SPEC = importlib.util.spec_from_file_location("public_pages", MODULE_PATH)
assert SPEC and SPEC.loader
pages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pages)


class SourceIndexabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "public_source_text": "A useful attributed source excerpt.",
            "topics": ["ai-visibility"],
            "topic_labels": ["AI Visibility"],
            "source_summary_short": "A source-backed summary of the useful finding.",
            "source_url": "https://www.tiktok.com/@creator/video/123",
            "full_transcript_public": False,
        }
        self.passages = [{"body": "Exact public evidence excerpt", "public_policy": "search_passage"}]
        self.insights = [{"public": True, "source_id": "tiktok:creator:123"}]

    def test_valuable_source_is_indexable(self) -> None:
        self.assertTrue(pages.is_indexable_source(self.source, self.passages, self.insights))

    def test_excerpt_without_insight_is_noindex(self) -> None:
        self.assertFalse(pages.is_indexable_source(self.source, self.passages, []))

    def test_missing_topic_or_summary_is_noindex(self) -> None:
        self.assertFalse(pages.is_indexable_source({**self.source, "topics": [], "topic_labels": []}, self.passages, self.insights))
        self.assertFalse(pages.is_indexable_source({**self.source, "source_summary_short": ""}, self.passages, self.insights))

    def test_full_transcript_public_is_never_indexable(self) -> None:
        self.assertFalse(pages.is_indexable_source({**self.source, "full_transcript_public": True}, self.passages, self.insights))

    def test_provenance_archive_is_never_indexable_or_search_linked(self) -> None:
        archive = {
            **self.source,
            "source_id": "tiktok:creator:123",
            "item_id": "tiktok-video-123",
            "creator_handle": "@creator",
            "admission_state": "provenance_archive_noindex",
            "public_surface": "provenance_archive",
        }
        self.assertFalse(pages.is_indexable_source(archive, self.passages, self.insights))
        html = pages.source_page(archive, self.passages, self.insights)
        self.assertIn("Provenance archive", html)
        self.assertIn('name="robots" content="noindex,follow"', html)
        self.assertNotIn("Open in Search Workspace", html)


if __name__ == "__main__":
    unittest.main()
