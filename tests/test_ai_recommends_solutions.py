from __future__ import annotations

import importlib.util
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

CORE_PATH = SCRIPTS / "base2026_ai_recommends_core.py"
CORE_SPEC = importlib.util.spec_from_file_location("base2026_ai_recommends_core", CORE_PATH)
assert CORE_SPEC and CORE_SPEC.loader
core = importlib.util.module_from_spec(CORE_SPEC)
CORE_SPEC.loader.exec_module(core)
validate_solution = core.validate_solution

GENERATOR_PATH = SCRIPTS / "generate-ai-recommends-solutions.py"
SPEC = importlib.util.spec_from_file_location("ai_recommends_generator", GENERATOR_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class AIRecommendsSolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.solution = {
            "slug": "example-solution",
            "title": "Example Solution",
            "meta_description": "A bounded description.",
            "audience": "Operators with a measured problem.",
            "problem": "The current process creates waste.",
            "primary_query": "How should the problem be solved?",
            "recommendation": "Run a controlled test.",
            "decision_scope": "One verified workflow.",
            "why_now": "The source data now supports a decision.",
            "evidence": [
                {"source_id": "source:1", "claim_id": "claim:1", "why_relevant": "First signal."},
                {"source_id": "source:2", "claim_id": "claim:2", "why_relevant": "Second signal."},
            ],
            "authoritative_sources": [
                {"title": "Official guide", "url": "https://example.com/official", "scope": "Defines the metric."}
            ],
            "playbook": [
                {"title": "Baseline", "body": "Save the before state."},
                {"title": "Test", "body": "Change one variable."},
                {"title": "Review", "body": "Compare the same metric."},
            ],
            "checklist": ["One", "Two", "Three", "Four", "Five"],
            "decision_table": [
                {"signal": "A", "decision": "Do A", "measure": "Measure A"},
                {"signal": "B", "decision": "Do B", "measure": "Measure B"},
                {"signal": "C", "decision": "Do C", "measure": "Measure C"},
            ],
            "risks": ["Risk one", "Risk two"],
            "kpis": ["KPI one", "KPI two", "KPI three"],
            "cadence": "Review after a stable window.",
            "cta": {"label": "Apply", "href": "/knowledge/apply-research.html?solution=example"},
            "related_solution_slugs": ["another-solution"],
            "editorial": {
                "status": "approved_local",
                "reviewer": "test-reviewer",
                "reviewed_at": "2026-07-10T09:00:20-04:00",
                "contract_version": "base2026-ai-recommends-solution-v1",
            },
        }
        source_1 = {"source_id": "source:1", "item_id": "item-1", "creator_handle": "@one", "source_url": "https://example.com/one"}
        source_2 = {"source_id": "source:2", "item_id": "item-2", "creator_handle": "@two", "source_url": "https://example.com/two"}
        claim_1 = {
            "source_id": "source:1", "claim_id": "claim:1", "creator_handle": "@one", "public": True,
            "needs_review": False, "claim_text": "First reviewed signal.", "topic": "First", "evidence_excerpt": "Evidence one."
        }
        claim_2 = {
            "source_id": "source:2", "claim_id": "claim:2", "creator_handle": "@two", "public": True,
            "needs_review": False, "claim_text": "Second reviewed signal.", "topic": "Second", "evidence_excerpt": "Evidence two."
        }
        self.context = {
            "source_by_id": {"source:1": source_1, "source:2": source_2},
            "insights_by_source": {"source:1": [claim_1], "source:2": [claim_2]},
            "claims_by_id": {"claim:1": claim_1, "claim:2": claim_2},
        }

    def test_two_source_two_creator_solution_is_indexable(self) -> None:
        report = validate_solution(self.solution, self.context)
        self.assertTrue(report["indexable"], report["errors"])
        self.assertEqual(report["resolved_source_count"], 2)
        self.assertEqual(report["resolved_creator_count"], 2)

    def test_claim_source_mismatch_blocks_indexability(self) -> None:
        solution = deepcopy(self.solution)
        solution["evidence"][1]["claim_id"] = "claim:1"
        report = validate_solution(solution, self.context)
        self.assertFalse(report["indexable"])
        self.assertTrue(any("does not belong" in error for error in report["errors"]))

    def test_single_creator_synthesis_is_blocked(self) -> None:
        context = deepcopy(self.context)
        context["claims_by_id"]["claim:2"]["creator_handle"] = "@one"
        report = validate_solution(self.solution, context)
        self.assertFalse(report["indexable"])
        self.assertTrue(any("two distinct creator" in error for error in report["errors"]))

    def test_external_cta_is_blocked(self) -> None:
        solution = deepcopy(self.solution)
        solution["cta"]["href"] = "https://example.com/agency-offer"
        report = validate_solution(solution, self.context)
        self.assertFalse(report["indexable"])
        self.assertTrue(any("Base2026 product journey" in error for error in report["errors"]))

    def test_failed_gate_renders_noindex(self) -> None:
        report = validate_solution(self.solution, self.context)
        report["indexable"] = False
        html = generator.solution_page(self.solution, report)
        self.assertIn('name="robots" content="noindex,follow"', html)
        self.assertIn("Reviewed creator signals prove what the source said", html)


if __name__ == "__main__":
    unittest.main()
