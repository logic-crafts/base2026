from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


INFO = load_script("base2026_product_shell_info_fixture", "generate-info-pages.py")
AI_VISIBILITY = load_script(
    "base2026_product_shell_ai_visibility_fixture",
    "generate-ai-visibility-pages.py",
)
SOLUTIONS = load_script(
    "base2026_product_shell_solution_fixture",
    "generate-ai-recommends-solutions.py",
)


SERVICE_ROUTES = {
    "/ai-visibility-audit/",
    "/ai-visibility-diagnostic-audit/",
    "/services/",
    "/pricing/",
}


def metadata(markup: str) -> tuple[str, str, str]:
    soup = BeautifulSoup(markup, "html.parser")
    assert soup.title
    robots = soup.select_one('meta[name="robots"]')
    canonical = soup.select_one('link[rel="canonical"]')
    assert robots and canonical
    return (
        soup.title.get_text(" ", strip=True),
        str(robots.get("content") or ""),
        str(canonical.get("href") or ""),
    )


def assert_product_shell(markup: str) -> BeautifulSoup:
    soup = BeautifulSoup(markup, "html.parser")
    assert soup.body and soup.body.get("data-b26-visual-root") == "v2"
    header = soup.select_one("header.b26-product-header[data-b26-product-header]")
    footer = soup.select_one('footer.ay-site-footer[data-footer-contract="personal-v1"]')
    assert header and footer
    assert len(soup.select("header[data-b26-product-header]")) == 1
    assert len(soup.select('footer[data-footer-contract="personal-v1"]')) == 1
    assert not header.select_one(".ay-v2-mega")
    assert not header.select_one('a[href="/knowledge/apply-research.html"]')
    assert not footer.select_one('a[href="/knowledge/apply-research.html"]')
    for anchor in [*header.select("a[href]"), *footer.select("a[href]")]:
        assert str(anchor.get("href") or "").startswith("/")
    for route in SERVICE_ROUTES:
        assert not header.select_one(f'a[href="{route}"]')
    assert footer.select_one('a[href="/services/"]')
    assert footer.select_one('a[href="/about/"]')
    return soup


@pytest.mark.parametrize(
    ("source_name", "bridge_count", "target"),
    [
        ("00_METHODOLOGY.md", 1, "/knowledge/apply-research.html"),
        ("01_ROADMAP.md", 0, None),
        ("02_PROJECT_STORY.md", 1, "/knowledge/apply-research.html"),
        ("03_PRIVACY_POLICY.md", 0, None),
        ("04_SOURCE_AND_CONTENT_POLICY.md", 0, None),
        ("05_SUPPORT_PAGE.md", 0, None),
        ("06_SITE_STRUCTURE.md", 0, None),
        ("07_CREATOR_CORRECTION_REMOVAL.md", 0, None),
        ("08_API_ACCESS.md", 0, None),
        ("09_APPLY_RESEARCH.md", 1, "/ai-visibility-audit/"),
    ],
)
def test_info_route_shell_metadata_and_single_handoff_policy(
    source_name: str,
    bridge_count: int,
    target: str | None,
) -> None:
    meta = INFO.PAGE_MAP[source_name]
    markdown = (ROOT / "docs/public-pages" / source_name).read_text(encoding="utf-8")
    h1, body = INFO.render_markdown(markdown, meta["body_class"])
    rendered = INFO.page_shell(meta, h1, body)
    soup = assert_product_shell(rendered)

    expected_title = meta.get("seo_title", f'{meta["title"]} | Base2026')
    assert metadata(rendered) == (
        expected_title,
        "index,follow",
        f'https://aggressorbulkit.online/knowledge/{meta["slug"]}',
    )
    assert soup.select_one("main h1").get_text(" ", strip=True) == INFO.normalize_copy(h1 or meta["title"])
    bridges = soup.select('[data-b26-component="B26-09"]')
    assert len(bridges) == bridge_count
    if target:
        assert bridges[0].select_one(f'a[href="{target}"]')
    assert len(soup.select('a[href="/knowledge/apply-research.html"]')) == (
        1 if source_name in {"00_METHODOLOGY.md", "02_PROJECT_STORY.md"} else 0
    )

    service_links = [
        str(anchor.get("href") or "")
        for anchor in soup.select("main a[href]")
        if str(anchor.get("href") or "") in SERVICE_ROUTES
    ]
    assert service_links == (["/ai-visibility-audit/"] if source_name == "09_APPLY_RESEARCH.md" else [])
    if source_name == "09_APPLY_RESEARCH.md":
        text = soup.get_text(" ", strip=True)
        assert "Check My AI Visibility View Services" not in text
        assert "Search Base2026 Check My AI Visibility Request Diagnostic Audit" not in text
        assert soup.select_one('main ul a[href="/knowledge/"]')
        assert soup.select_one('main ul a[href="/knowledge/ai-visibility-pages/"]')
        assert text.count("Start the visibility check") == 1
    assert not soup.select_one('form[action="/wp-admin/admin-post.php"]')


def test_support_keeps_a_visible_contact_path_without_promising_a_removed_form() -> None:
    meta = INFO.PAGE_MAP["05_SUPPORT_PAGE.md"]
    markdown = (ROOT / "docs/public-pages/05_SUPPORT_PAGE.md").read_text(encoding="utf-8")
    h1, body = INFO.render_markdown(markdown, meta["body_class"])
    rendered = INFO.page_shell(meta, h1, body)
    soup = BeautifulSoup(rendered, "html.parser")

    assert soup.select_one('main a[href="mailto:offflinerpsy@gmail.com"]')
    assert "Use the contact form below" not in soup.get_text(" ", strip=True)
    assert not soup.select_one('main form[action="/wp-admin/admin-post.php"]')


def ai_fixture() -> dict[str, str]:
    return {
        "title": "Fixture AI Visibility",
        "slug": "nested/fixture-ai-visibility",
        "meta_description": "A bounded fixture description that must survive shell migration.",
        "type": "main_ai_visibility_hub",
        "body_markdown": (
            "# Fixture AI Visibility\n\n"
            "Preserved research introduction.\n\n"
            "## Evidence\n\n"
            "Preserved source-backed research body."
        ),
    }


@pytest.mark.parametrize("collection", [False, True])
def test_ai_visibility_generators_preserve_content_and_use_one_absolute_bridge(collection: bool) -> None:
    fixture = ai_fixture()
    if collection:
        rendered = AI_VISIBILITY.index_html([fixture], noindex=False)
        expected = (
            "AI Visibility Lab | Base2026",
            "index,follow",
            "https://aggressorbulkit.online/knowledge/ai-visibility-pages/",
        )
        preserved = "Fixture AI Visibility"
    else:
        rendered = AI_VISIBILITY.page_html(fixture, noindex=False, related_groups=[])
        expected = (
            "Fixture AI Visibility | Base2026",
            "index,follow",
            "https://aggressorbulkit.online/knowledge/nested/fixture-ai-visibility/",
        )
        preserved = "Preserved source-backed research body."

    soup = assert_product_shell(rendered)
    assert metadata(rendered) == expected
    assert preserved in soup.get_text(" ", strip=True)
    assert len(soup.select('[data-b26-component="B26-09"]')) == 1
    assert len(soup.select('a[href="/knowledge/apply-research.html"]')) == 1
    assert not soup.select_one('form[action="/wp-admin/admin-post.php"]')
    main = soup.select_one("main")
    assert main
    for route in SERVICE_ROUTES:
        assert not main.select_one(f'a[href="{route}"]')


def solution_fixture() -> dict[str, object]:
    return {
        "slug": "fixture-solution",
        "title": "Fixture Solution",
        "meta_description": "A bounded solution description that must survive shell migration.",
        "audience": "Operators with a measured problem.",
        "problem": "Preserved fixture problem.",
        "primary_query": "Which bounded action should be tested?",
        "recommendation": "Run one controlled intervention.",
        "decision_scope": "One workflow.",
        "why_now": "The evidence is ready for a bounded decision.",
        "authoritative_sources": [],
        "playbook": [{"title": "Baseline", "body": "Save the before state."}],
        "checklist": ["Owner", "Baseline"],
        "decision_table": [{"signal": "A", "decision": "Do A", "measure": "Measure A"}],
        "risks": ["The baseline is incomplete."],
        "kpis": ["Verified outcome"],
        "cadence": "Review after one stable window.",
        "cta": {"label": "Explore fixture evidence", "href": "/knowledge/?q=fixture"},
        "related_solution_slugs": [],
        "updated_at": "2026-07-18",
    }


def test_solution_generator_uses_one_absolute_optional_bridge_and_preserves_metadata() -> None:
    fixture = solution_fixture()
    rendered = SOLUTIONS.solution_page(fixture, {"resolved_evidence": [], "indexable": True})
    soup = assert_product_shell(rendered)

    assert metadata(rendered) == (
        "Fixture Solution | Base2026",
        "index,follow",
        "https://aggressorbulkit.online/knowledge/solutions/fixture-solution.html",
    )
    assert "Preserved fixture problem." in soup.get_text(" ", strip=True)
    assert len(soup.select('[data-b26-component="B26-09"]')) == 1
    assert len(soup.select('a[href="/knowledge/apply-research.html"]')) == 1
    assert soup.select_one('a[href="/knowledge/?q=fixture"]')
    main = soup.select_one("main")
    assert main
    for route in SERVICE_ROUTES:
        assert not main.select_one(f'a[href="{route}"]')
