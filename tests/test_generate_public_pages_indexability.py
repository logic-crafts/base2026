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

    def test_workspace_links_use_canonical_query_string_route(self) -> None:
        self.assertEqual(
            pages.workspace_href(topic="internal-linking", q="Internal Linking"),
            "../?topic=internal-linking&q=Internal+Linking",
        )
        self.assertNotIn("#search?", pages.workspace_href(source="tiktok-video-123"))


class TopicSemanticContractTests(unittest.TestCase):
    topic_id = "content-repurposing"

    def setUp(self) -> None:
        self.original_published_topic_ids = set(pages.PUBLISHED_TOPIC_IDS)
        pages.PUBLISHED_TOPIC_IDS.clear()
        pages.PUBLISHED_TOPIC_IDS.add(self.topic_id)

    def tearDown(self) -> None:
        pages.PUBLISHED_TOPIC_IDS.clear()
        pages.PUBLISHED_TOPIC_IDS.update(self.original_published_topic_ids)

    def topic(self, creator_count: int = 1, insight_count: int = 2) -> dict:
        creators = [{"handle": "tjrobertson52", "count": insight_count}]
        if creator_count >= 2:
            creators.append({"handle": "secondcreator", "count": 1})
        return {
            "topic_id": self.topic_id,
            "topic": "content repurposing",
            "definition": "Source-backed creator statements and viewpoints related to content repurposing.",
            "public": True,
            "public_insight_count": insight_count,
            "source_count": max(insight_count, 1),
            "creator_count": creator_count,
            "top_creators": creators,
        }

    def source(self, source_id: str, creator: str) -> dict:
        return {
            "source_id": source_id,
            "item_id": source_id.replace(":", "-"),
            "creator_handle": creator,
            "source_url": f"https://example.com/{source_id}",
            "title": f"Attributed record {source_id}",
            "source_summary_short": "A complete attributed summary for this public source record.",
            "published_date": "2026-07-01",
            "topics": [self.topic_id],
        }

    def insight(self, source_id: str, creator: str, suffix: str) -> dict:
        return {
            "source_id": source_id,
            "topic_id": self.topic_id,
            "topic": "content repurposing",
            "creator_handle": creator,
            "public": True,
            "claim_text": f"Attributed repurposing claim {suffix}.",
            "evidence_excerpt": "A complete reviewed sentence supports this attributed claim.",
            "stance": "asserts",
        }

    def test_one_creator_topic_is_scoped_as_perspective_not_consensus(self) -> None:
        sources = [
            self.source("source:alpha", "tjrobertson52"),
            self.source("source:beta", "tjrobertson52"),
        ]
        insights = [
            self.insight("source:alpha", "tjrobertson52", "one"),
            self.insight("source:beta", "tjrobertson52", "two"),
        ]
        passages = [
            {"source_id": "source:alpha", "topics": [self.topic_id], "body": "ly broken chunk boundary should never be published."},
            {"source_id": "source:beta", "topics": [self.topic_id], "body": "ht another broken chunk boundary should never be published."},
            {"source_id": "source:beta", "topics": [self.topic_id], "body": "hese damaged leading letters should never be published."},
        ]

        # Deliberately stale aggregate metadata says two creators; attributed
        # public evidence still contains only one independent creator.
        html = pages.topic_page(self.topic(creator_count=2), sources, passages, insights)

        self.assertIn("one creator perspective", html)
        self.assertIn("does not represent independent creator consensus", html)
        self.assertIn("Treat it as attributed evidence, not independent consensus", html)
        self.assertIn("Creator Perspective", html)
        self.assertNotIn("@secondcreator", html)
        self.assertNotIn("Compare creator viewpoints", html)
        self.assertNotIn("Compare creators", html)
        self.assertNotIn("creators repeatedly", html)
        self.assertNotIn("Evidence Passages", html)
        self.assertIn("Public Insight Cards", html)
        self.assertIn("Related Source Records", html)
        self.assertNotIn("ly broken chunk boundary", html)
        self.assertNotIn("ht another broken chunk boundary", html)
        self.assertNotIn("hese damaged leading letters", html)
        self.assertIn('name="robots" content="index,follow"', html)
        self.assertIn(
            '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/topics/content-repurposing.html"',
            html,
        )

        compare_html = pages.compare_page(self.topic(creator_count=2), insights)
        self.assertIn("Attributed creator perspective", compare_html)
        self.assertIn("one creator perspective", compare_html)
        self.assertNotIn("Creator viewpoint comparison", compare_html)
        self.assertNotIn("Compare source-backed creator viewpoints", compare_html)
        self.assertNotIn("?compare=content-repurposing", compare_html)
        self.assertIn('name="robots" content="index,follow"', compare_html)
        self.assertIn(
            "https://aggressorbulkit.online/knowledge/compare/content-repurposing.html",
            compare_html,
        )

    def test_strong_multi_creator_topic_keeps_one_clean_excerpt_per_source(self) -> None:
        sources = [
            self.source("source:alpha", "tjrobertson52"),
            self.source("source:beta", "secondcreator"),
            self.source("source:gamma", "tjrobertson52"),
        ]
        insights = [
            self.insight("source:alpha", "tjrobertson52", "one"),
            self.insight("source:beta", "secondcreator", "two"),
            self.insight("source:gamma", "tjrobertson52", "three"),
        ]
        passages = [
            {"source_id": "source:alpha", "topics": [self.topic_id], "body": "ly broken alpha fragment should be withheld."},
            {"source_id": "source:alpha", "topics": [self.topic_id], "body": "Alpha provides one complete attributed excerpt for this source record."},
            {"source_id": "source:alpha", "topics": [self.topic_id], "body": "Alpha duplicate passage must not create a second excerpt card."},
            {"source_id": "source:beta", "topics": [self.topic_id], "body": "ht broken beta fragment should be withheld from the page."},
            {"source_id": "source:beta", "topics": [self.topic_id], "body": "Beta provides one complete attributed excerpt for another source record."},
            {"source_id": "source:gamma", "topics": [self.topic_id], "body": "hese broken gamma letters should be withheld from the page."},
            {"source_id": "source:gamma", "topics": [self.topic_id], "body": "0, which is another chunk-boundary fragment that should be withheld."},
        ]
        brief = {
            "status": "strong",
            "source_count": 3,
            "creator_count": 2,
            "public_insight_count": 3,
        }

        tier_b_html = pages.topic_page(
            self.topic(creator_count=2, insight_count=3),
            sources,
            passages,
            insights,
        )
        self.assertNotIn("Evidence Passages", tier_b_html)
        self.assertIn("Public Insight Cards", tier_b_html)
        self.assertIn("Related Source Records", tier_b_html)

        html = pages.topic_page(
            self.topic(creator_count=2, insight_count=3),
            sources,
            passages,
            insights,
            signal_briefs={self.topic_id: brief},
        )

        self.assertIn("Compare creator viewpoints", html)
        self.assertIn("Evidence Passages", html)
        self.assertEqual(html.count("passage-card--linked"), 2)
        self.assertEqual(html.count("Alpha provides one complete attributed excerpt"), 1)
        self.assertEqual(html.count("Beta provides one complete attributed excerpt"), 1)
        self.assertNotIn("Alpha duplicate passage", html)
        self.assertNotIn("ly broken alpha fragment", html)
        self.assertNotIn("ht broken beta fragment", html)
        self.assertNotIn("hese broken gamma letters", html)
        self.assertNotIn("0, which is another chunk-boundary fragment", html)

        compare_html = pages.compare_page(
            self.topic(creator_count=2, insight_count=3),
            insights,
        )
        self.assertIn("Creator viewpoint comparison", compare_html)
        self.assertIn("Compare source-backed creator viewpoints", compare_html)
        self.assertIn("?compare=content-repurposing", compare_html)

    def test_topic_bridge_routes_every_offer_action_to_one_contextual_research_link(self) -> None:
        bridge = {
            "title": "Apply this evidence honestly",
            "body": "Use the research context before selecting a commercial package.",
            "primary_label": "Start an audit",
            "primary_href": "/ai-visibility-audit/",
            "secondary_label": "Request Diagnostic Audit",
            "secondary_href": "/ai-visibility-audit/?offer=diagnostic_audit",
        }

        html = pages.topic_money_bridge_section(self.topic_id, {"cta": bridge})

        self.assertEqual(html.count('data-topic-contextual-bridge="true"'), 1)
        self.assertEqual(html.count('data-research-bridge="topic_to_apply_research"'), 1)
        self.assertIn(
            'href="/knowledge/apply-research.html?topic=content-repurposing"',
            html,
        )
        self.assertIn('data-research-bridge="topic_to_apply_research"', html)
        self.assertIn('data-origin-id="content-repurposing"', html)
        self.assertIn(">Apply this research</a>", html)
        self.assertNotIn(">Start an audit</a>", html)
        self.assertNotIn("/ai-visibility-audit/", html)
        self.assertNotIn("Request Diagnostic Audit", html)

        sources = [self.source("source:alpha", "tjrobertson52")]
        insights = [self.insight("source:alpha", "tjrobertson52", "one")]
        rendered = pages.topic_page(
            self.topic(),
            sources,
            [],
            insights,
            topic_traffic_pages={self.topic_id: {"cta": bridge}},
        )
        self.assertEqual(rendered.count('data-topic-contextual-bridge="true"'), 1)
        self.assertEqual(rendered.count('data-research-bridge="topic_to_apply_research"'), 1)
        self.assertNotIn("Request Diagnostic Audit</a>", rendered)
        self.assertNotIn("/ai-visibility-audit/", rendered)

    def test_default_topic_page_ends_with_one_contextual_research_bridge(self) -> None:
        sources = [self.source("source:alpha", "tjrobertson52")]
        insights = [self.insight("source:alpha", "tjrobertson52", "one")]

        rendered = pages.topic_page(self.topic(), sources, [], insights)

        self.assertEqual(rendered.count('data-topic-contextual-bridge="true"'), 1)
        self.assertEqual(rendered.count('data-research-bridge="topic_to_apply_research"'), 1)
        self.assertEqual(rendered.count('data-origin-id="content-repurposing"'), 1)
        self.assertEqual(
            rendered.count(
                'href="/knowledge/apply-research.html?topic=content-repurposing"'
            ),
            1,
        )
        self.assertIn("Take this topic into a real decision", rendered)
        self.assertIn("it does not diagnose your business", rendered)
        self.assertGreater(
            rendered.index('data-topic-contextual-bridge="true"'),
            rendered.index("Related Source Records"),
        )
        bridge = pages.topic_money_bridge_section(
            self.topic_id,
            label="content repurposing",
        )
        self.assertNotIn("ay-button-secondary", bridge)

    def test_unlisted_topic_context_is_not_reflected_into_apply_research_query(self) -> None:
        html = pages.topic_bridge_action_link(
            "not-on-the-published-topic-list",
            "ay-button",
            "Start an audit",
            "/ai-visibility-audit/",
        )

        self.assertIn('href="/knowledge/apply-research.html"', html)
        self.assertNotIn("?topic=", html)
        self.assertNotIn("not-on-the-published-topic-list", html)


if __name__ == "__main__":
    unittest.main()
