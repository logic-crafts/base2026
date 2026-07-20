from __future__ import annotations

import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_search_shell_is_explicitly_frozen_and_separate_from_general_v2() -> None:
    from alex_v4_static_shell import search_shell_css, shell_css

    generator = read("scripts/generate-base2026-search-v1.py")
    assert "search_shell_css" in generator
    assert "write_text(search_shell_css()" in generator
    assert hashlib.sha256(search_shell_css().encode()).hexdigest() == (
        "aadd0996560916b0cd530e7ce9e329a6138470eae19412bfc0e98db73d8925eb"
    )
    assert "Alex Design System V2" in shell_css()
    assert "fonts.googleapis.com" not in shell_css()


def test_search_solution_bridge_loads_its_frozen_component_css_only_on_search() -> None:
    journey = read("web/static/base2026-solution-journey.js")
    assert 'document.body.classList.contains("base2026-search-v1")' in journey
    assert 'new URL("base2026-solution-journey.css", assetBase)' in journey
    assert "loadAcceptedSearchBridgeStyles();" in journey


def test_packagers_and_deploy_preflight_close_v2_runtime_dependencies() -> None:
    standard = read("scripts/package-public-release.ps1")
    hotfix = read("scripts/package-public-hotfix-from-export.ps1")
    deploy = read("scripts/deploy-public-vps.ps1")

    for script in (standard, hotfix):
        assert '"./web/static/alex-design-system-v2.css"' in script
        assert '"./web/static/vendor"' in script
        assert "apply-alex-design-system-v2.py --web-root $WebRoot" in script
        assert "ai-recommends-solutions.css" not in script
    assert 'Move-Item (Join-Path $WebRoot "ai-recommends-solutions.js")' in standard

    for required in (
        "web/static/alex-design-system-v2.css",
        "web/static/alex-v4-static-shell.js",
        "web/static/base2026-solution-journey.js",
        "web/static/base2026-solution-journey.css",
        "web/static/purify.min.js",
        "web/static/vendor/manrope-800.ttf",
        "web/static/vendor/geist-800.ttf",
        "web/static/vendor/geist-mono-700.ttf",
    ):
        assert required in hotfix
        assert required in deploy


def test_source_candidate_carries_every_font_referenced_by_the_shared_css() -> None:
    builder = read("scripts/build-source-detail-v2-full-candidate.py")
    for font in (
        "manrope-400.ttf",
        "manrope-500.ttf",
        "manrope-600.ttf",
        "manrope-700.ttf",
        "manrope-800.ttf",
        "geist-400.ttf",
        "geist-500.ttf",
        "geist-600.ttf",
        "geist-700.ttf",
        "geist-800.ttf",
        "geist-mono-400.ttf",
        "geist-mono-600.ttf",
        "geist-mono-700.ttf",
    ):
        assert f'vendor/{font}' in builder
