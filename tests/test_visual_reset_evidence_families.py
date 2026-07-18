from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from alex_design_system_v2 import ASSET_NAME, VERSION, apply_component_classes  # noqa: E402


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def stylesheet_hrefs(page: str) -> list[str]:
    soup = BeautifulSoup(page, "html.parser")
    return [str(node.get("href") or "") for node in soup.select('link[rel~="stylesheet"]')]


def assert_one_design_system(page: str) -> None:
    hrefs = stylesheet_hrefs(page)
    assert sum(ASSET_NAME in href for href in hrefs) == 1
    assert all("styles.css" not in href for href in hrefs)
    assert all("alex-v4-static-shell.css" not in href for href in hrefs)
    assert all("base2026-interior-v1.css" not in href for href in hrefs)
    assert "fonts.googleapis.com" not in page
    assert "fonts.gstatic.com" not in page


def test_component_registry_is_versioned_and_idempotent() -> None:
    assert VERSION == "20260718-visual-reset-v2-r4"
    source = '<main class="app-shell content-page"><a class="ay-button">Open</a></main>'
    once = apply_component_classes(source)
    twice = apply_component_classes(once)
    assert once == twice
    assert 'class="app-shell content-page ayds-page ayds-main ayds-content"' in once
    assert 'class="ay-button ayds-btn ayds-btn--primary"' in once


def test_public_family_shell_uses_product_mode_and_brand_root() -> None:
    module = load_script("base_public_visual_reset", "generate-public-pages.py")
    page = module.page_shell(
        "Creator | Base2026",
        '<section class="page-hero"><p class="eyebrow">Creator</p><h1>@creator</h1></section>',
        relative_root="..",
        current="creators",
        description="Creator source record.",
        canonical_path="creators/creator.html",
    )
    assert_one_design_system(page)
    soup = BeautifulSoup(page, "html.parser")
    body_classes = soup.body.get("class") or []
    assert body_classes.count("ayds-mode-product") == 1
    assert "ayds-mode-editorial" not in body_classes
    assert soup.select_one('.ay-v2-base-trigger > a[href="/knowledge/"]')
    assert soup.select_one('.ay-v2-base-mega a[href="/knowledge/ai-visibility-pages/"]')


def test_governance_shell_uses_editorial_mode_and_shared_form() -> None:
    module = load_script("base_info_visual_reset", "generate-info-pages.py")
    meta = dict(module.PAGE_MAP["05_SUPPORT_PAGE.md"])
    page = module.page_shell(meta, "Support Base2026", '<section class="doc-section"><h2>Support</h2></section>')
    assert_one_design_system(page)
    soup = BeautifulSoup(page, "html.parser")
    body_classes = soup.body.get("class") or []
    assert body_classes.count("ayds-mode-editorial") == 1
    assert "ayds-mode-product" not in body_classes
    assert soup.select_one("form.ayds-form .ayds-field")
    assert soup.select_one('button.ayds-btn--primary[type="submit"]')


def test_source_template_has_one_visual_authority() -> None:
    template = (SCRIPTS / "template_migration/templates/base_page.html.j2").read_text(encoding="utf-8")
    assert "alex-design-system-v2.css" in template
    for legacy in (
        "styles.css",
        "alex-v4-static-shell.css",
        "source-detail-v2.css",
        "base2026-interior-v1.css",
        "vendor/geist-local.css",
    ):
        assert legacy not in template
    family = (SCRIPTS / "template_migration/templates/families/source_detail.html.j2").read_text(encoding="utf-8")
    assert "ayds-card--data" in family
    assert "ayds-disclosure" in family
    assert "ayds-btn--primary" in family
    assert 'b26-intelligence-panel ayds-stack' in family
    assert 'b26-source-solution-list ayds-stack' in family
    assert 'b26-intelligence-panel ayds-grid' not in family
    assert 'b26-source-solution-list ayds-grid' not in family
    for behavior_hook in (
        'data-insight-index=',
        'data-source-solution-count=',
        'data-solution-id=',
        'data-journey-action="solution_opened"',
        'data-journey-surface="source_detail"',
    ):
        assert behavior_hook in family

    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")
    assert """.ayds-stack {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 20px;
}""" in css
