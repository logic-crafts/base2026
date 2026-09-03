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
            "cta": {"label": "Explore the evidence", "href": "/knowledge/?q=example"},
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
        self.assertIn("Reviewed creator signals show what each source said", html)
        self.assertIn('class="content-section solution-fit"', html)
        self.assertIn('data-copy-column="2"', html)
        self.assertNotIn("solution-step__number", html)
        self.assertIn('href="/knowledge/?q=example"', html)
        self.assertNotIn('href="/knowledge/apply-research.html?solution=example"', html)
        self.assertNotIn("apply-research.html", html)

    def test_solution_css_implements_accepted_stitch_template(self) -> None:
        css = generator.css_text()
        self.assertIn("max-width:1040px", css)
        self.assertIn("grid-template-columns:repeat(4,minmax(0,1fr))", css)
        self.assertIn(".solution-page .solution-step--critical", css)
        self.assertIn(".solution-page .solution-operations", css)
        self.assertIn(".solution-page .solution-evidence-row__detail-grid", css)
        self.assertIn(".solution-page .solution-next-action", css)
        self.assertIn("width:min(100% - 32px,520px)", css)
        self.assertIn(".solution-page .solution-decision-table thead{display:none}", css)
        self.assertIn(".solution-hub .solution-hero__copy h1{font-size:clamp(31px,9.6vw,40px)", css)
        self.assertNotIn(".solution-step__number{color", css)

    def test_stitch_template_renders_canonical_content_without_demo_copy(self) -> None:
        report = validate_solution(self.solution, self.context)
        html = generator.solution_page(self.solution, report)
        canonical_values = [
            self.solution["problem"],
            self.solution["recommendation"],
            self.solution["audience"],
            self.solution["primary_query"],
            self.solution["decision_scope"],
            self.solution["why_now"],
            self.solution["cadence"],
            *[row["title"] for row in self.solution["playbook"]],
            *[row["body"] for row in self.solution["playbook"]],
            *self.solution["checklist"],
            *self.solution["risks"],
            *self.solution["kpis"],
            *[row[key] for row in self.solution["decision_table"] for key in ("signal", "decision", "measure")],
        ]
        for value in canonical_values:
            self.assertIn(value, html)
        self.assertEqual(html.count('class="solution-evidence-row"'), 2)
        self.assertIn('class="solution-step solution-step--critical"', html)
        self.assertIn('class="content-section solution-operations"', html)
        self.assertIn("Alex Yarosh", html)
        self.assertNotIn("40% traffic increase", html)
        self.assertNotIn("September 12, 2023", html)
        self.assertNotIn("March 28, 2024", html)
        self.assertNotIn("April 15, 2024", html)

    def test_solution_column_copy_script_is_same_origin_static_asset(self) -> None:
        report = validate_solution(self.solution, self.context)
        html = generator.solution_page(self.solution, report)
        script = generator.solution_js_text()
        self.assertIn('../static/ai-recommends-solutions.js?v=', html)
        self.assertIn('data-copy-column="2"', html)
        self.assertIn('navigator.clipboard?.writeText', script)
        self.assertIn('join("\\n")', script)
        self.assertNotIn("http://", script)
        self.assertNotIn("https://", script)

    def test_solution_article_schema_has_public_image(self) -> None:
        report = validate_solution(self.solution, self.context)
        html = generator.solution_page(self.solution, report)
        self.assertIn(
            '"image": "https://aggressorbulkit.online/knowledge/static/assets/base2026-ai-visibility-card.png"',
            html,
        )

    def test_solution_shell_explains_base2026_jobs_without_legacy_apply_link(self) -> None:
        report = validate_solution(self.solution, self.context)
        html = generator.solution_page(self.solution, report)
        header = html.split("</header>", 1)[0]
        self.assertIn("Search the library", header)
        self.assertIn("Source Intelligence", header)
        self.assertIn("Topics &amp; viewpoints", header)
        self.assertIn("AI Recommends Solutions", header)
        self.assertIn("Creators", header)
        self.assertIn("Methodology", header)
        self.assertNotIn("apply-research.html", header)


if __name__ == "__main__":
    unittest.main()
