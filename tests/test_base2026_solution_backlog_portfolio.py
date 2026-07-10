from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "base2026-solution-backlog-portfolio.py"
SPEC = importlib.util.spec_from_file_location("base2026_solution_backlog_portfolio", MODULE_PATH)
assert SPEC and SPEC.loader
portfolio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(portfolio)


class SolutionBacklogPortfolioTests(unittest.TestCase):
    def top(self, text: str) -> str:
        rows = portfolio.score_clusters(text)
        return rows[0][0] if rows else ""

    def test_google_business_profile_is_green_cluster(self) -> None:
        self.assertEqual(self.top("Audit a Google Business Profile category and Map Pack visibility"), "google-business-profile-visibility-audit")

    def test_search_console_ctr_is_green_cluster(self) -> None:
        self.assertEqual(self.top("Use Google Search Console to find high impressions and low CTR"), "search-console-high-impression-low-ctr")

    def test_ai_agent_workflow_is_not_search_measurement(self) -> None:
        self.assertEqual(self.top("An AI agent automates a localization workflow for content managers"), "ai-agent-workflows")

    def test_ai_visibility_with_analytics_is_measurement(self) -> None:
        self.assertEqual(self.top("Measure ChatGPT referral traffic and AI search visibility in analytics"), "measure-ai-search-visibility")

    def test_generic_story_remains_unclassified(self) -> None:
        self.assertEqual(self.top("Steve Jobs almost skipped an iconic photography session"), "")


if __name__ == "__main__":
    unittest.main()
