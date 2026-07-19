from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_ai_generator():
    path = ROOT / "scripts" / "generate-ai-visibility-pages.py"
    spec = importlib.util.spec_from_file_location("generate_ai_visibility_pages_visual_reset", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_design_system_is_local_single_source_and_exposes_required_api() -> None:
    css = (ROOT / "web" / "static" / "alex-design-system-v2.css").read_text(encoding="utf-8")

    assert "@import" not in css
    assert "fonts.googleapis.com" not in css
    assert "https://" not in css
    assert "/knowledge/static/vendor/manrope-400.ttf" in css
    assert "/knowledge/static/vendor/geist-400.ttf" in css
    assert "/knowledge/static/vendor/geist-mono-400.ttf" in css
    assert "--ayds-color-canvas: #f4f1e9" in css
    assert "--ayds-color-ink: #0f172a" in css

    for selector in (
        ".ayds-page",
        ".ayds-section",
        ".ayds-hero",
        ".ayds-eyebrow",
        ".ayds-lead",
        ".ayds-actions",
        ".ayds-btn",
        ".ayds-btn--primary",
        ".ayds-btn--secondary",
        ".ayds-btn--small",
        ".ayds-card",
        ".ayds-card--feature",
        ".ayds-card--data",
        ".ayds-card--dark",
        ".ayds-grid",
        ".ayds-field",
        ".ayds-chip",
        ".ayds-disclosure",
        ".ayds-contact",
    ):
        assert selector in css

    for forbidden_accent in ("#ff6b18", "#d9730d", "#c84f07", "--solution-orange"):
        assert forbidden_accent not in css.lower()


def test_design_system_covers_source_and_solution_compatibility_contracts() -> None:
    css = (ROOT / "web" / "static" / "alex-design-system-v2.css").read_text(encoding="utf-8")
    for selector in (
        ".page-hero",
        ".content-section",
        ".card-grid",
        ".intelligence-card",
        ".passage-card",
        ".comparison-group",
        ".topic-chip",
        ".ay-button",
        ".ay-button-secondary",
        ".b26-source-shell",
        ".b26-arrival-nav",
        ".b26-source-intro",
        ".b26-creator-row",
        ".b26-source-actions",
        ".b26-source-layout",
        ".b26-intelligence-panel",
        ".b26-question",
        ".b26-source-provenance",
        ".b26-source-solution-bridge",
        ".solution-page",
        ".solution-hero",
        ".solution-fit",
        ".solution-steps",
        ".solution-step__title",
        ".solution-decision-table",
        ".solution-operations",
        ".solution-operations__group",
        ".solution-cadence",
        ".solution-completion-card",
        ".solution-measurement-card",
        ".solution-evidence-grid",
        ".solution-authority",
        ".solution-next-action",
        ".solution-hub-grid",
        ".button-link--quiet",
    ):
        assert selector in css


def test_shared_shell_has_canonical_base_destination_named_lab_child_and_is_idempotent() -> None:
    from alex_v4_static_shell import apply_alex_v4_shell, header_html, search_shell_css, shell_css

    header = header_html()
    assert '<a href="/knowledge/">Base2026</a>' in header
    assert '<a href="/knowledge/ai-visibility-pages/"><strong>AI Visibility Lab</strong>' in header
    assert '/knowledge/ai-visibility-pages/">AI Visibility Lab</a>' in header
    assert "fonts.googleapis.com" not in shell_css()
    assert hashlib.sha256(search_shell_css().encode()).hexdigest() == "aadd0996560916b0cd530e7ce9e329a6138470eae19412bfc0e98db73d8925eb"

    source = """<!doctype html><html><head>  </head><body><header class="site-header"></header><main></main><footer class="site-footer"></footer></body></html>"""
    once = apply_alex_v4_shell(source)
    twice = apply_alex_v4_shell(once)
    assert once.count("alex-design-system-v2.css") == 1
    assert twice.count("alex-design-system-v2.css") == 1
    assert twice.count("alex-v4-static-shell.js") == 1
    assert "alex-v4-static-shell.css" not in twice


def test_shared_shell_fails_safe_when_legacy_shell_is_missing() -> None:
    from alex_v4_static_shell import apply_alex_v4_shell

    source = """<!doctype html><html><head></head><body class="roadmap-test"><a class="skip-link" href="#content">Skip</a><main id="content"></main></body></html>"""
    once = apply_alex_v4_shell(source)
    twice = apply_alex_v4_shell(once)

    assert once.index('class="skip-link"') < once.index('class="ay-v2-header"') < once.index('<main id="content">')
    assert once.index('<main id="content">') < once.index('class="ay-site-footer"') < once.index("</body>")
    assert twice.count('class="ay-v2-header"') == 1
    assert twice.count('class="ay-site-footer"') == 1
    assert twice.count("alex-design-system-v2.css") == 1
    assert twice.count("alex-v4-static-shell.js") == 1
    for body_class in (
        "roadmap-test",
        "ayds-root",
        "ayds-mode-editorial",
        "ay-alex-v4-static",
        "ay-stitch-home-v3",
        "ay-stitch-home-v4",
    ):
        assert twice.count(body_class) == 1


def test_shared_shell_normalizes_to_one_requested_page_mode() -> None:
    from alex_v4_static_shell import apply_alex_v4_shell

    source = """<!doctype html><html><head></head><body class="ayds-root ayds-mode-editorial ayds-mode-product legacy"><main></main></body></html>"""
    rendered = apply_alex_v4_shell(source, mode="product")

    body_start = rendered.index("<body")
    body_open = rendered[body_start : rendered.index(">", body_start)]
    assert body_open.count("ayds-root") == 1
    assert body_open.count("ayds-mode-product") == 1
    assert "ayds-mode-editorial" not in body_open


def test_every_master_ai_visibility_page_renders_only_the_v2_system() -> None:
    generator = load_ai_generator()
    payload = json.loads((ROOT / "data" / "ai_visibility_pages_master.json").read_text(encoding="utf-8"))
    pages = payload["pages"]
    assert len(pages) >= 64

    for page in pages:
        rendered = generator.page_html(page, noindex=False, related_groups=[])
        expected_canonical = f"https://aggressorbulkit.online/knowledge/{page['slug'].strip('/')}/"
        assert rendered.count("alex-design-system-v2.css") == 1
        assert "alex-v4-static-shell.css" not in rendered
        assert "/knowledge/static/styles.css" not in rendered
        assert "fonts.googleapis.com" not in rendered
        assert 'class="ayds-root ayds-mode-editorial' in rendered
        assert 'data-b26-visual-root="v2"' in rendered
        assert rendered.count("data-b26-product-header") == 1
        assert rendered.count("data-b26-product-footer") == 1
        assert 'class="b26-money-hero ayds-hero"' in rendered
        assert rendered.count('data-b26-component="B26-09"') == 1
        assert rendered.count('href="/knowledge/apply-research.html"') == 1
        assert "ay-v2-mega" not in rendered
        assert "Send a message" not in rendered
        assert "Prefer a call" not in rendered
        assert 'action="/wp-admin/admin-post.php"' not in rendered
        assert 'href="/ai-visibility-audit/"' not in rendered
        assert 'href="/ai-visibility-diagnostic-audit/"' not in rendered
        assert 'href="/services/"' not in rendered
        assert 'href="/pricing/"' not in rendered
        assert rendered.count("<h1") == 1
        assert f'<link rel="canonical" href="{expected_canonical}"' in rendered
        assert 'meta name="robots" content="index,follow"' in rendered
        assert 'type="application/ld+json"' in rendered


def test_ai_visibility_collection_preserves_search_hooks_and_product_mode() -> None:
    generator = load_ai_generator()
    pages = json.loads((ROOT / "data" / "ai_visibility_pages_master.json").read_text(encoding="utf-8"))["pages"]
    rendered = generator.index_html(pages, noindex=False)

    assert rendered.count("alex-design-system-v2.css") == 1
    assert "/knowledge/static/styles.css" not in rendered
    assert "fonts.googleapis.com" not in rendered
    assert 'class="ayds-root ayds-mode-product' in rendered
    assert 'data-b26-visual-root="v2"' in rendered
    assert rendered.count("data-b26-product-header") == 1
    assert rendered.count("data-b26-product-footer") == 1
    assert rendered.count('data-b26-component="B26-09"') == 1
    assert rendered.count('href="/knowledge/apply-research.html"') == 1
    assert "ay-v2-mega" not in rendered
    assert 'action="/wp-admin/admin-post.php"' not in rendered
    assert 'id="ai-lab-search-input"' in rendered
    assert "data-lab-card" in rendered
    assert "data-lab-grid" in rendered
    assert "data-lab-count" in rendered
    assert rendered.count("<h1") == 1
    assert 'href="/knowledge/">Base2026</a>' in rendered


def test_ai_visibility_lab_and_detail_geometry_match_accepted_site_scale() -> None:
    css = (ROOT / "web" / "static" / "alex-design-system-v2.css").read_text(encoding="utf-8")

    assert "padding: clamp(40px, 6vw, 72px) 0 clamp(48px, 6.5vw, 80px);" in css
    assert "font: 800 clamp(40px, 4.5vw, 64px)/1 var(--ayds-font-body);" in css
    assert "padding-top: clamp(38px, 5vw, 60px);" in css
    assert "font: 800 clamp(42px, 5vw, 60px)/1 var(--ayds-font-body);" in css
    assert ".b26-money-hero h1 { font-size: clamp(38px, 10.5vw, 48px); line-height: 1.02; }" in css
    assert ".ai-pages-intro h1 { font-size: clamp(38px, 10.5vw, 46px); line-height: 1.02; }" in css
    assert ".b26-money-hero { padding: 32px 0 48px; }" in css
    assert ".ai-lab-search { grid-template-columns: 1fr; margin-top: 22px; padding: 18px; }" in css
