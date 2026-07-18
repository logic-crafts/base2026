from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from template_migration.source_detail import SourceDetailView, render_source_detail  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_view() -> SourceDetailView:
    return SourceDetailView(
        route="sources/tiktok-video-111.html",
        item_id="tiktok-video-111",
        admission_state="normal_public_card",
        language_code="en",
        head_html='<meta name="robots" content="index,follow">',
        header_html="<header>Header</header>",
        footer_html="<footer>Footer</footer>",
        handle="@fixture",
        date="2026-07-18",
        avatar_src="",
        avatar_alt="",
        thesis="A bounded source thesis.",
        original_link="https://www.tiktok.com/@fixture/video/111",
        creator_link="../creators/fixture.html",
        search_link="../?source=tiktok-video-111",
        platform_key="tiktok",
        platform_label="TikTok",
        policy="Public reviewed source",
        language="English",
        insight_count="1",
        topics=(),
        source_html="<p>Reviewed public source text.</p>",
        insights=(),
        questions=(),
        solutions=(),
        archive=False,
        schema_html="",
    )


def test_source_detail_template_uses_shared_v2_design_and_local_fonts() -> None:
    rendered = render_source_detail(source_view(), "fixture-v1")
    assert '<body class="ayds-root ayds-mode-product b26-family-source b26-source-v2"' in rendered
    assert '../static/alex-design-system-v2.css?v=fixture-v1' in rendered
    assert 'data-alex-design-system="v2"' in rendered
    assert "base2026-interior-v1.css" not in rendered
    assert "geist-local.css" not in rendered
    assert "interior-token-pilot" not in rendered
    assert "fonts.googleapis.com" not in rendered


def test_source_detail_browser_gate_tracks_the_current_source_shell() -> None:
    gate = (ROOT / "scripts" / "source-detail-v2-browser-gate.mjs").read_text(encoding="utf-8")

    assert "ay-stitch-home-v4 body class missing" not in gate
    for class_name in ("ayds-root", "ayds-mode-product", "b26-family-source", "b26-source-v2"):
        assert f'"{class_name}"' in gate


def test_source_candidate_asset_copier_carries_v2_css_and_local_font_dependencies(tmp_path: Path) -> None:
    module = load_module("source_detail_candidate_interior", SCRIPTS / "build-source-detail-v2-full-candidate.py")
    fake_root = tmp_path / "repo"
    fake_scripts = fake_root / "scripts"
    fake_static = fake_root / "web/static"
    (fake_static / "assets").mkdir(parents=True)
    (fake_static / "assets/alex-yarosh-favicon-32.png").write_bytes(b"favicon")
    (fake_static / "assets/alex-yarosh-apple-touch.png").write_bytes(b"apple")
    (fake_static / "vendor").mkdir()
    for font_name in (
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
        (fake_static / "vendor" / font_name).write_bytes(font_name.encode("ascii"))
    (fake_static / "alex-design-system-v2.css").write_text(
        '@font-face{font-family:"Manrope";src:url("/knowledge/static/vendor/manrope-400.ttf")}\n',
        encoding="utf-8",
    )
    fake_scripts.mkdir()
    (fake_scripts / "base2026_source_detail_v2.js").write_text("// fixture\n", encoding="utf-8")
    module.ROOT = fake_root
    module.SCRIPTS = fake_scripts

    hashes = module.copy_static_assets(tmp_path / "candidate")
    assert "alex-design-system-v2.css" in hashes
    assert "alex-v4-static-shell.js" in hashes
    assert "source-detail-v2.js" in hashes
    assert "vendor/geist-400.ttf" in hashes
    assert "vendor/manrope-400.ttf" in hashes
    assert "base2026-interior-v1.css" not in hashes
    assert "vendor/geist-local.css" not in hashes
    design_css = (tmp_path / "candidate/static/alex-design-system-v2.css").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in design_css


def test_info_pages_share_v2_editorial_mode_and_apply_research_keeps_family_marker() -> None:
    module = load_module("base2026_info_interior", SCRIPTS / "generate-info-pages.py")
    apply_html = module.page_shell(module.PAGE_MAP["09_APPLY_RESEARCH.md"], "Apply Base2026 Research", "<section>Body</section>")
    assert 'class="ayds-root b26-family-governance b26-family-apply-research ayds-mode-editorial' in apply_html
    assert './static/alex-design-system-v2.css?v=' in apply_html
    assert 'data-alex-design-system="v2"' in apply_html
    assert "base2026-interior-v1.css" not in apply_html
    assert "geist-local.css" not in apply_html
    assert "fonts.googleapis.com" not in apply_html
    assert "fonts.gstatic.com" not in apply_html

    methodology_html = module.page_shell(module.PAGE_MAP["00_METHODOLOGY.md"], "Methodology", "<section>Body</section>")
    assert 'class="ayds-root b26-family-governance ayds-mode-editorial' in methodology_html
    assert "b26-family-apply-research" not in methodology_html
    assert "alex-design-system-v2.css" in methodology_html
    assert "base2026-interior-v1.css" not in methodology_html
    assert "geist-local.css" not in methodology_html
    assert "fonts.googleapis.com" not in methodology_html


def test_base_main_is_not_opted_into_the_interior_contract() -> None:
    main = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert "b26-interior-v1" not in main
    assert "base2026-interior-v1.css" not in main


def test_cookie_contract_is_three_column_44px_and_pilot_free() -> None:
    css = (ROOT / "web/static/base2026-interior-v1.css").read_text(encoding="utf-8")
    assert ".b26-interior-v1 .cookie-actions" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in css
    assert "min-height: 44px;" in css
    assert ":focus-visible" in css
    assert "interior-token-pilot" not in css
    assert "b26-pilot-" not in css
