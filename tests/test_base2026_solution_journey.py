from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from base2026_solution_journey import build_registry  # noqa: E402


def solution(source_ids: tuple[str, str], claim_ids: tuple[str, str]) -> dict:
    return {
        "slug": "example-solution",
        "title": "Example Solution",
        "meta_description": "A bounded example Solution.",
        "audience": "Operators",
        "problem": "A measurable problem",
        "primary_query": "What should an operator do?",
        "recommendation": "Inspect the evidence before acting.",
        "decision_scope": "One bounded decision",
        "why_now": "A baseline exists.",
        "cadence": "Review after 28 days.",
        "evidence": [
            {"source_id": source_ids[0], "claim_id": claim_ids[0], "why_relevant": "Signal one supports the bounded decision."},
            {"source_id": source_ids[1], "claim_id": claim_ids[1], "why_relevant": "Signal two provides an independent check."},
        ],
        "authoritative_sources": [{"title": "Official docs", "url": "https://example.com/docs", "scope": "Verification boundary"}],
        "playbook": [
            {"title": "Save baseline", "body": "Record the before state."},
            {"title": "Change one thing", "body": "Apply one bounded change."},
            {"title": "Measure", "body": "Compare the same cohort."},
        ],
        "checklist": ["One", "Two", "Three", "Four", "Five"],
        "decision_table": [
            {"signal": "A", "decision": "B", "measure": "C"},
            {"signal": "D", "decision": "E", "measure": "F"},
            {"signal": "G", "decision": "H", "measure": "I"},
        ],
        "risks": ["Risk one", "Risk two"],
        "kpis": ["KPI one", "KPI two", "KPI three"],
        "cta": {"label": "Search evidence", "href": "/knowledge/?q=example"},
        "related_solution_slugs": ["example-solution"],
        "editorial": {
            "status": "approved_local",
            "reviewer": "fixture-reviewer",
            "reviewed_at": "2026-07-17T00:00:00Z",
            "contract_version": "base2026-ai-recommends-solution-v1",
        },
    }


def fixture_payloads() -> tuple[dict, dict, list[dict], list[dict]]:
    source_ids = ("tiktok:creator_one:111", "tiktok:creator_two:222")
    claim_ids = ("claim-one", "claim-two")
    approval = {
        "schema": "base2026.approved-solution-ids/v1",
        "updated_at": "2026-07-17",
        "solutions": [{"id": "example-solution", "route": "solutions/example-solution.html"}],
    }
    solutions = {
        "contract_version": "base2026-ai-recommends-solution-v1",
        "updated_at": "2026-07-17",
        "solutions": [solution(source_ids, claim_ids)],
    }
    sources = [
        {"source_id": source_ids[0], "item_id": "tiktok-video-111", "creator_handle": "creator_one"},
        {"source_id": source_ids[1], "item_id": "tiktok-video-222", "creator_handle": "creator_two"},
    ]
    insights = [
        {"source_id": source_ids[0], "claim_id": claim_ids[0], "creator_handle": "creator_one", "topic": "First", "public": True},
        {"source_id": source_ids[1], "claim_id": claim_ids[1], "creator_handle": "creator_two", "topic": "Second", "public": True},
    ]
    return approval, solutions, sources, insights


def test_registry_is_allowlisted_and_evidence_bound() -> None:
    registry = build_registry(*fixture_payloads())
    assert registry["schema"] == "base2026.solution-journey-registry/v1"
    assert registry["approved_solution_ids"] == ["example-solution"]
    assert registry["counts"] == {
        "approved_solutions": 1,
        "evidence_bound_sources": 2,
        "evidence_links": 2,
    }
    first = registry["source_mappings"][0]
    assert first["route"].startswith("sources/tiktok-video-")
    assert first["solutions"][0]["evidence_role"] == "reviewed_creator_signal"
    assert first["solutions"][0]["synthesis_role"] == "base2026_decision_playbook"


def test_registry_rejects_claim_source_mismatch() -> None:
    approval, solutions, sources, insights = fixture_payloads()
    solutions["solutions"][0]["evidence"][0]["claim_id"] = "claim-two"
    with pytest.raises(ValueError, match="validation failed"):
        build_registry(approval, solutions, sources, insights)


def test_runtime_uses_master_measurement_event_ids_and_approved_ids() -> None:
    runtime = (ROOT / "web/static/base2026-solution-journey.js").read_text(encoding="utf-8")
    contract = json.loads((ROOT / "contracts/base2026-approved-solution-ids.json").read_text(encoding="utf-8"))
    for event_id in (
        "product_search_submitted",
        "source_opened",
        "evidence_actioned",
        "solution_opened",
        "research_bridge_clicked",
    ):
        assert event_id in runtime
    for deprecated in ("decision_asset_used", "research_bridge_opened"):
        assert deprecated not in runtime
    for row in contract["solutions"]:
        assert f'"{row["id"]}"' in runtime
    assert "raw_query" not in runtime
    assert "page_referrer" not in runtime
    assert "page_location" not in runtime


def test_runtime_value_domains_fail_closed_in_node_fixture() -> None:
    fixture = ROOT / "tests/base2026_solution_journey_value_gate.mjs"
    completed = subprocess.run(
        ["node", str(fixture)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert json.loads(completed.stdout) == {"valid": 5, "rejected": 14, "consent_gate": True}


def test_source_overlay_preserves_robots_and_canonical(tmp_path: Path) -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "tiktok-video-111.html"
    source.write_text(
        '<!doctype html><html><head><meta name="robots" content="index,follow">'
        '<link rel="canonical" href="https://example.test/knowledge/sources/tiktok-video-111.html">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">'
        '</head><body>'
        '<main id="content" class="b26-source-shell" data-admission-state="normal_public_card">'
        '<section class="b26-source-section b26-source-intelligence" id="intelligence"><h2>Source Intelligence</h2></section>'
        '<aside><nav><a href="#questions">Questions</a></nav></aside></main></body></html>',
        encoding="utf-8",
    )
    mapping = {
        "item_id": "tiktok-video-111",
        "route": "sources/tiktok-video-111.html",
        "solutions": [{
            "id": "example-solution",
            "title": "Example Solution",
            "href": "/knowledge/solutions/example-solution.html",
            "why_relevant": "A reviewed signal contributes to this playbook.",
        }],
    }
    result = module.patch_source_page(source, mapping)
    rendered = source.read_text(encoding="utf-8")
    assert result["robots"] == "index,follow"
    assert result["canonical"].endswith("tiktok-video-111.html")
    assert rendered.count('id="solutions"') == 1
    assert 'data-source-item-id="tiktok-video-111"' in rendered
    assert rendered.index('id="intelligence"') < rendered.index('id="solutions"')
    assert "fonts.googleapis.com" not in rendered
    assert "fonts.gstatic.com" not in rendered
    assert "../static/vendor/geist-local.css" in rendered


def test_solution_overlay_is_optional_and_preserves_search_state(tmp_path: Path) -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4_solution", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    solution_id = "example-solution"
    path = tmp_path / f"{solution_id}.html"
    path.write_text(
        '<!doctype html><html><head><meta name="robots" content="index,follow">'
        f'<link rel="canonical" href="https://aggressorbulkit.online/knowledge/solutions/{solution_id}.html">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">'
        '</head><body><main class="app-shell content-page solution-page">'
        '<section class="content-section solution-next-action"><p>Research stays complete.</p>'
        '<a class="ay-button" href="/knowledge/?q=example">Explore evidence</a></section>'
        '</main></body></html>',
        encoding="utf-8",
    )
    result = module.patch_solution_page(path, solution_id)
    rendered = path.read_text(encoding="utf-8")
    assert result["robots"] == "index,follow"
    assert result["canonical"].endswith(f"/{solution_id}.html")
    assert 'href="/knowledge/?q=example"' in rendered
    assert 'data-research-bridge="solution_to_apply_research"' in rendered
    assert 'href="../apply-research.html"' in rendered
    assert "remains complete without a service request" in rendered
    assert "fonts.googleapis.com" not in rendered


def test_apply_research_overlay_only_localizes_fonts(tmp_path: Path) -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4_apply", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "apply-research.html"
    path.write_text(
        '<!doctype html><html><head><meta name="robots" content="index,follow">'
        '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/apply-research.html">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">'
        '</head><body><main id="content"><h1>Apply Base2026 Research</h1></main></body></html>',
        encoding="utf-8",
    )
    result = module.patch_apply_research_page(path)
    rendered = path.read_text(encoding="utf-8")
    assert result == {
        "route": "apply-research.html",
        "robots": "index,follow",
        "canonical": "https://aggressorbulkit.online/knowledge/apply-research.html",
    }
    assert "fonts.googleapis.com" not in rendered
    assert "./static/vendor/geist-local.css" in rendered
    assert "Apply Base2026 Research" in rendered


def test_font_localization_is_idempotent_for_reconciled_generator_output() -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4_local_fonts", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = (
        '<!doctype html><html><head>'
        '<link rel="stylesheet" href="./static/vendor/geist-local.css?v=old" data-base2026-local-fonts="geist-manrope">'
        '<link rel="stylesheet" href="./static/alex-v4-static-shell.css?v=old">'
        '</head><body></body></html>'
    )
    localized = module.localize_fonts(source, "./static/vendor/geist-local.css?v=current")
    assert localized.count("vendor/geist-local.css") == 1
    assert "v=current" in localized
    assert "alex-v4-static-shell-p4-local.css" in localized
    assert "fonts.googleapis.com" not in localized


def test_phase1_overlay_accepts_matching_generator_owned_bridges(tmp_path: Path) -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4_reconciled", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source = tmp_path / "tiktok-video-111.html"
    source.write_text(
        '<!doctype html><html><head><meta name="robots" content="index,follow">'
        '<link rel="canonical" href="https://example.test/knowledge/sources/tiktok-video-111.html">'
        '<link rel="stylesheet" href="../static/vendor/geist-local.css?v=current">'
        '</head><body><main id="content" class="b26-source-shell" data-admission-state="normal_public_card" '
        'data-source-item-id="tiktok-video-111"><section id="solutions">'
        '<a data-journey-action="solution_opened" data-solution-id="example-solution">Solution</a>'
        '</section></main></body></html>',
        encoding="utf-8",
    )
    mapping = {
        "item_id": "tiktok-video-111",
        "route": "sources/tiktok-video-111.html",
        "solutions": [{"id": "example-solution"}],
    }
    module.patch_source_page(source, mapping)
    assert source.read_text(encoding="utf-8").count('id="solutions"') == 1

    solution = tmp_path / "example-solution.html"
    solution.write_text(
        '<!doctype html><html><head><meta name="robots" content="index,follow">'
        '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/solutions/example-solution.html">'
        '<link rel="stylesheet" href="../static/vendor/geist-local.css?v=current">'
        '</head><body><main class="solution-page"><a data-research-bridge="solution_to_apply_research" '
        'data-origin-id="example-solution" href="../apply-research.html">Apply</a></main></body></html>',
        encoding="utf-8",
    )
    module.patch_solution_page(solution, "example-solution")
    assert solution.read_text(encoding="utf-8").count('data-research-bridge="solution_to_apply_research"') == 1


def test_active_dependency_scanner_follows_local_css_import_chain(tmp_path: Path) -> None:
    module_path = SCRIPTS / "derive-base2026-phase1-base-p4-preview.py"
    spec = importlib.util.spec_from_file_location("phase1_base_p4_css_scan", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    web = tmp_path / "web"
    static = web / "static"
    nested = static / "nested"
    nested.mkdir(parents=True)
    page = web / "index.html"
    page.write_text(
        '<!doctype html><html><head><link rel="stylesheet" href="./static/root.css"></head></html>',
        encoding="utf-8",
    )
    (static / "root.css").write_text('@import url("./nested/fonts.css");\nbody{color:#111}', encoding="utf-8")
    (nested / "fonts.css").write_text(
        '@import url("https://fonts.googleapis.com/css2?family=Geist");',
        encoding="utf-8",
    )
    assert module.active_external_resource_urls(page, web) == [
        "https://fonts.googleapis.com/css2?family=Geist",
    ]
