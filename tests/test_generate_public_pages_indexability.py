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
            "creator_handle": "@creator",
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

    def test_workspace_links_use_canonical_query_string_route(self) -> None:
        self.assertEqual(
            pages.workspace_href(topic="internal-linking", q="Internal Linking"),
            "../?topic=internal-linking&q=Internal+Linking",
        )
        self.assertNotIn("#search?", pages.workspace_href(source="tiktok-video-123"))

    def test_source_titles_are_unique_and_fit_search_result_limits(self) -> None:
        first = {**self.source, "item_id": "tiktok-video-7657638702864223510"}
        second = {**self.source, "item_id": "tiktok-video-7657638702864223511"}
        title_one = pages.source_seo_title(first, "@creator_with_a_long_handle")
        title_two = pages.source_seo_title(second, "@creator_with_a_long_handle")
        self.assertLessEqual(len(title_one), 65)
        self.assertLessEqual(len(title_two), 65)
        self.assertNotEqual(title_one, title_two)
        self.assertIn("2864223510", title_one)
        self.assertNotIn("...", title_one)

        description_one = pages.source_seo_description(first, "@creator_with_a_long_handle")
        description_two = pages.source_seo_description(second, "@creator_with_a_long_handle")
        self.assertLessEqual(len(description_one), 160)
        self.assertLessEqual(len(description_two), 160)
        self.assertNotEqual(description_one, description_two)
        self.assertIn("2864223510", description_one)

    def test_source_schema_does_not_claim_a_video_embed_without_media_metadata(self) -> None:
        source = {**self.source, "item_id": "tiktok-video-7657638702864223510"}
        html = pages.source_page(source, self.passages, self.insights)
        self.assertIn('"@type": "CreativeWork"', html)
        self.assertNotIn('"@type": "VideoObject"', html)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('<p class="source-identity__handle">@creator</p>', html)

    def test_topic_and_compare_browser_titles_fit_search_result_limits(self) -> None:
        topic = {
            "topic_id": "local-seo-operations-and-google-business-profile-maintenance",
            "topic": "Local SEO operations and Google Business Profile maintenance",
            "definition": "A public test definition.",
            "public_insight_count": 1,
            "source_count": 1,
            "creator_count": 1,
        }
        pages.PUBLISHED_TOPIC_IDS = {topic["topic_id"]}
        for rendered in (
            pages.topic_page(topic, [], [], [], [], {}),
            pages.compare_page(topic, []),
        ):
            title = rendered.split("<title>", 1)[1].split("</title>", 1)[0]
            self.assertLessEqual(len(title), 65)

    def test_source_index_pagination_is_bidirectional_and_crawlable(self) -> None:
        self.assertEqual(
            pages.source_index_pagination(1, 3),
            '<nav class="source-index-pagination" aria-label="Source record pages"><a class="button-link" rel="next" href="page-2.html">Older source records</a></nav>',
        )
        middle = pages.source_index_pagination(2, 3)
        self.assertIn('rel="prev" href="./"', middle)
        self.assertIn('rel="next" href="page-3.html"', middle)
        self.assertEqual(pages.source_index_pagination(1, 1), "")


if __name__ == "__main__":
    unittest.main()
