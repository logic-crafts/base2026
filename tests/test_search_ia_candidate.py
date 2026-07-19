from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "derive-base2026-search-ia-candidate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("derive_search_ia_candidate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_search_ia_derivative_is_bounded_and_idempotent_for_css() -> None:
    module = load_module()
    html = f"<header>{module.HEADER_APPLY_LINK}<a href='/knowledge/'>Search</a></header>"

    derived, removed = module.derive_entrypoint(html)
    assert removed == 1
    assert "apply-research" not in derived
    assert "Search" in derived
    unchanged, removed = module.derive_entrypoint(derived)
    assert unchanged == derived
    assert removed == 0

    with pytest.raises(ValueError, match="contract drift"):
        module.derive_entrypoint(html + module.HEADER_APPLY_LINK)

    css = module.derive_css(".ay-v2-menu-toggle{display:none}\n")
    assert "min-width:44px" in css
    assert "min-height:44px" in css
    assert "display:inline-flex!important" in css
    assert module.derive_css(css) == css


def test_all_protected_search_entrypoints_have_zero_persistent_apply_after_derivation() -> None:
    module = load_module()
    source_root = ROOT / ".planning" / "master-rebuild-production-source-20260718" / "web"
    total_removed = 0

    for relative in sorted(module.SEARCH_ENTRYPOINTS):
        source = (source_root / relative).read_text(encoding="utf-8")
        derived, removed = module.derive_entrypoint(source)
        total_removed += removed
        assert module.HEADER_APPLY_LINK not in derived, relative

    assert total_removed == 1
