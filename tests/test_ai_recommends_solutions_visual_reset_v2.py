from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-ai-recommends-solutions.py"
DESIGN_SYSTEM_VERSION = "20260718-visual-reset-v2-r4"


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_solutions_generator_uses_only_shared_visual_contract(tmp_path: Path) -> None:
    data_root = tmp_path / "public-data" / "tiktok"
    input_path = tmp_path / "solutions.json"
    output_root = tmp_path / "generated"
    report_path = tmp_path / "report.json"

    write_jsonl(
        data_root / "source_records.jsonl",
        [
            {
                "source_id": "source:alpha",
                "item_id": "item-alpha",
                "creator_handle": "@alpha",
                "source_url": "https://example.com/alpha",
                "published_at": "2026-06-01",
            },
            {
                "source_id": "source:beta",
                "item_id": "item-beta",
                "creator_handle": "@beta",
                "source_url": "https://example.com/beta",
                "published_at": "2026-06-02",
            },
        ],
    )
    write_jsonl(
        data_root / "insight_cards.jsonl",
        [
            {
                "source_id": "source:alpha",
                "claim_id": "claim:alpha",
                "creator_handle": "@alpha",
                "public": True,
                "needs_review": False,
                "claim_text": "Alpha reviewed claim.",
                "evidence_excerpt": "Alpha exact public excerpt.",
                "suggested_action": "Run the alpha bounded action.",
                "topic": "Alpha topic",
                "published_at": "2026-06-01",
            },
            {
                "source_id": "source:beta",
                "claim_id": "claim:beta",
                "creator_handle": "@beta",
                "public": True,
                "needs_review": False,
                "claim_text": "Beta reviewed claim.",
                "evidence_excerpt": "Beta exact public excerpt.",
                "suggested_action": "Run the beta bounded action.",
                "topic": "Beta topic",
                "published_at": "2026-06-02",
            },
        ],
    )

    solution = {
        "slug": "fixture-solution",
        "title": "Fixture Solution",
        "meta_description": "A reviewed fixture solution with bounded evidence and measurement.",
        "audience": "Operators with a measurable visibility problem.",
        "problem": "The current workflow cannot separate signal from noise.",
        "primary_query": "Which bounded intervention should be tested first?",
        "recommendation": "Run one evidence-bound intervention before expanding scope.",
        "decision_scope": "One workflow and one measurement window.",
        "why_now": "Two reviewed public signals support a controlled decision.",
        "evidence": [
            {
                "source_id": "source:alpha",
                "claim_id": "claim:alpha",
                "why_relevant": "Alpha establishes the first signal.",
            },
            {
                "source_id": "source:beta",
                "claim_id": "claim:beta",
                "why_relevant": "Beta supplies an independent signal.",
            },
        ],
        "authoritative_sources": [
            {
                "title": "Official measurement guide",
                "url": "https://example.com/official-guide",
                "scope": "Defines the bounded outcome metric.",
            }
        ],
        "playbook": [
            {"title": "Capture baseline", "body": "Save the verified before state."},
            {"title": "Run one test", "body": "Change only the selected intervention."},
            {"title": "Review outcome", "body": "Compare the same metric after the stable window."},
        ],
        "checklist": ["Scope", "Owner", "Baseline", "Window", "Review"],
        "decision_table": [
            {"signal": "Signal A", "decision": "Decision A", "measure": "Measure A"},
            {"signal": "Signal B", "decision": "Decision B", "measure": "Measure B"},
            {"signal": "Signal C", "decision": "Decision C", "measure": "Measure C"},
        ],
        "risks": ["The baseline is incomplete.", "More than one variable changes."],
        "kpis": ["Qualified discovery", "Evidence action", "Verified outcome"],
        "cadence": "Review after one stable measurement window.",
        "cta": {"label": "Explore fixture evidence", "href": "/knowledge/?q=fixture"},
        "related_solution_slugs": [],
        "updated_at": "2026-07-18",
        "editorial": {
            "status": "approved_local",
            "reviewer": "fixture-reviewer",
            "reviewed_at": "2026-07-18T09:00:00-04:00",
            "contract_version": "base2026-ai-recommends-solution-v1",
        },
    }
    input_path.write_text(
        json.dumps(
            {
                "contract_version": "base2026-ai-recommends-solution-v1",
                "solutions": [solution],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--input",
            str(input_path),
            "--data-root",
            str(data_root),
            "--out",
            str(output_root),
            "--report",
            str(report_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    detail = (output_root / "solutions" / "fixture-solution.html").read_text(encoding="utf-8")
    hub = (output_root / "solutions" / "index.html").read_text(encoding="utf-8")
    solution_js = (output_root / "ai-recommends-solutions.js").read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    for page in (detail, hub):
        assert page.count("alex-design-system-v2.css") == 1
        assert (
            f'../static/alex-design-system-v2.css?v={DESIGN_SYSTEM_VERSION}'
            in page
        )
        assert 'data-alex-design-system="v2"' in page
        assert page.count("alex-v4-static-shell.js") == 1
        assert 'class="ay-v2-header b26-product-header"' in page
        assert 'class="ay-site-footer" data-footer-contract="personal-v1"' in page
        assert page.count("data-b26-product-header") == 1
        assert page.count('data-footer-contract="personal-v1"') == 1
        assert 'data-b26-visual-root="v2"' in page
        assert page.count('data-b26-component="B26-09"') <= 1
        header = page.split("</header>", 1)[0]
        assert "ay-v2-mega" not in header
        assert "apply-research.html" not in header
        for shell_href in (
            "/knowledge/",
            "/knowledge/topics/",
            "/knowledge/creators/",
            "/knowledge/solutions/",
            "/knowledge/methodology.html",
        ):
            assert f'href="{shell_href}"' in header
        assert "ayds-root" in page
        assert "ayds-mode-product" in page
        for forbidden in (
            "ai-recommends-solutions.css",
            "base2026-interior-v1.css",
            "alex-v4-static-shell.css",
            "vendor/geist-local.css",
            "fonts.googleapis.com",
            "fonts.gstatic.com",
        ):
            assert forbidden not in page

    assert not (output_root / "ai-recommends-solutions.css").exists()
    assert not (output_root / "base2026-interior-v1.css").exists()
    assert not (output_root / "alex-v4-static-shell.css").exists()
    assert not (output_root / "vendor").exists()
    assert (output_root / "alex-v4-static-shell.js").is_file()

    assert '<meta name="robots" content="index,follow"' in detail
    assert (
        '<link rel="canonical" '
        'href="https://aggressorbulkit.online/knowledge/solutions/fixture-solution.html"'
        in detail
    )
    assert (
        'class="app-shell content-page solution-page ayds-page ayds-main ayds-content"'
        in detail
    )
    assert 'class="solution-hero ayds-hero"' in detail
    assert 'class="solution-hero__copy"' in detail
    assert 'class="solution-verdict ayds-card ayds-card--dark"' in detail
    assert 'class="content-section solution-fit ayds-section"' in detail
    assert (
        'class="content-section solution-operations solution-operations-grid ayds-section"'
        in detail
    )
    assert (
        'class="solution-evidence-row ayds-card ayds-card--data" '
        'id="evidence-claim:alpha"'
        in detail
    )

    for preserved_text in (
        solution["problem"],
        solution["recommendation"],
        "Alpha reviewed claim.",
        "Alpha exact public excerpt.",
        "Run the beta bounded action.",
        "Official measurement guide",
        "Review after one stable measurement window.",
    ):
        assert preserved_text in detail
    assert 'href="../sources/item-alpha.html"' in detail
    assert 'href="https://example.com/beta"' in detail
    assert 'data-copy-column="2"' in detail
    assert 'data-research-bridge="solution_to_apply_research"' in detail
    assert 'data-origin-id="fixture-solution"' in detail
    assert detail.count('data-b26-component="B26-09"') == 1
    assert detail.count('href="/knowledge/apply-research.html"') == 1
    assert hub.count('data-b26-component="B26-09"') == 0
    assert 'href="/knowledge/apply-research.html"' not in hub
    assert (
        f'../static/ai-recommends-solutions.js?v={DESIGN_SYSTEM_VERSION}'
        in detail
    )

    schemas = [
        json.loads(payload)
        for payload in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            detail,
            flags=re.DOTALL,
        )
    ]
    article = next(row for row in schemas if row.get("@type") == "Article")
    assert article["headline"] == "Fixture Solution"
    assert article["mainEntityOfPage"].endswith("/solutions/fixture-solution.html")
    assert article["citation"] == [
        "https://example.com/alpha",
        "https://example.com/beta",
        "https://example.com/official-guide",
    ]

    assert 'navigator.clipboard?.writeText' in solution_js
    assert 'join("\\n")' in solution_js
    assert "./base2026-solution-journey.js" in solution_js
    assert "dataset.base2026SolutionJourney" in solution_js
    assert report["ok"] is True
    assert report["indexable_count"] == 1
    assert report["generated_pages"] == 2
