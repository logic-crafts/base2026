from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-base2026-cloudflare-release.py"
SPEC = importlib.util.spec_from_file_location("base2026_investor_builder", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def test_investor_page_has_the_bounded_product_and_contact_contract() -> None:
    source = builder.DEFAULT_INVESTORS_TEMPLATE.read_text(encoding="utf-8")

    assert source.count("{{STARTUP_HEADER}}") == 1
    assert source.count("{{STARTUP_FOOTER}}") == 1
    for phrase in (
        "Video knowledge, ready for your next question.",
        "selected practitioner material into attributed, searchable records",
        "It does not determine which recommendation is correct",
        "We do not accept paid creator placement or creator applications.",
        "Investor conversation",
        "repeat use, willingness to pay",
        "We built AgencyOS, a private operating environment that helps a solo founder coordinate development, research and publishing.",
    ):
        assert phrase in source
    for internal_approval_phrase in ("not a claim of traction", "current fundraising round", "complete daily relay", "raw ASR", "local databases"):
        assert internal_approval_phrase not in source
    assert "/partner" in source
    assert "/investors" in builder.HUB_SITEMAP_ROUTES
    assert builder.DEFAULT_INVESTORS_TEMPLATE.name == "base2026-investors.html"


def test_public_copy_routes_render_with_the_startup_shell_and_extensionless_canonicals() -> None:
    header = builder.DEFAULT_STARTUP_HEADER.read_text(encoding="utf-8")
    footer = builder.DEFAULT_STARTUP_FOOTER.read_text(encoding="utf-8")
    route_templates = {
        "/about": builder.DEFAULT_ABOUT_TEMPLATE,
        "/methodology": builder.DEFAULT_METHODOLOGY_PAGE,
        "/source-policy": builder.DEFAULT_SOURCE_POLICY_PAGE,
        "/roadmap": builder.DEFAULT_ROADMAP_PAGE,
    }

    for route, path in route_templates.items():
        rendered = builder._render_startup_page(path.read_text(encoding="utf-8"), header, footer).decode("utf-8")
        assert "{{STARTUP_HEADER}}" not in rendered
        assert "{{STARTUP_FOOTER}}" not in rendered
        assert "b26-site-header" in rendered
        assert "b26-site-footer" in rendered
        assert f"https://base2026.dev{route}" in rendered

    roadmap = builder._render_startup_page(
        builder.DEFAULT_ROADMAP_PAGE.read_text(encoding="utf-8"), header, footer
    ).decode("utf-8")
    assert "Now" in roadmap and "Next" in roadmap and "Exploring" in roadmap
    assert "Some processing stages still depend on review." in roadmap
    assert "private factory" not in roadmap.casefold()
    assert "roadmap-experience" not in roadmap
    assert "/static/roadmap.js" not in roadmap

    source_policy = builder.DEFAULT_SOURCE_POLICY_PAGE.read_text(encoding="utf-8")
    assert "founder and team" in source_policy
    assert "paid creator placement or creator applications" in source_policy
    assert "not an admission request" in source_policy

    methodology = builder.DEFAULT_METHODOLOGY_PAGE.read_text(encoding="utf-8")
    assert 'href="/source-policy"' in methodology

    about = builder.DEFAULT_ABOUT_TEMPLATE.read_text(encoding="utf-8")
    assert 'href="https://www.youtube.com/@base2026dev"' in about
    assert 'href="https://www.tiktok.com/@alex.yarosh3"' in about
    assert 'href="https://x.com/AleksejAros"' in about
    assert 'href="https://www.linkedin.com/in/alex-yarosh-a21842227/"' in about
    assert "original source" in about and "correction or removal" in about


def test_hub_sitemap_contains_each_new_public_route_once() -> None:
    payload = builder._hub_sitemap_payload().decode("utf-8")
    assert payload.count("https://base2026.dev/investors") == 1
    assert payload.count("https://base2026.dev/source-policy") == 1
