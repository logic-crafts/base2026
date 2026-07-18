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


def test_source_detail_template_carries_permanent_interior_and_local_fonts() -> None:
    rendered = render_source_detail(source_view(), "fixture-v1")
    assert "b26-interior-v1 b26-interior-source" in rendered
    assert '../static/base2026-interior-v1.css?v=fixture-v1' in rendered
    assert '../static/vendor/geist-local.css?v=fixture-v1' in rendered
    assert "interior-token-pilot" not in rendered
    assert "fonts.googleapis.com" not in rendered


def test_source_candidate_asset_copier_carries_css_and_local_font_dependencies(tmp_path: Path) -> None:
    module = load_module("source_detail_candidate_interior", SCRIPTS / "build-source-detail-v2-full-candidate.py")
    fake_root = tmp_path / "repo"
    fake_scripts = fake_root / "scripts"
    fake_static = fake_root / "web/static"
    (fake_static / "assets").mkdir(parents=True)
    (fake_static / "assets/alex-yarosh-favicon-32.png").write_bytes(b"favicon")
    (fake_static / "assets/alex-yarosh-apple-touch.png").write_bytes(b"apple")
    (fake_static / "vendor").mkdir()
    (fake_static / "vendor/geist-local.css").write_text("@font-face{}\n", encoding="utf-8")
    (fake_static / "vendor/geist-400.ttf").write_bytes(b"geist")
    (fake_static / "vendor/manrope-400.ttf").write_bytes(b"manrope")
    (fake_static / "base2026-interior-v1.css").write_text("body.b26-interior-v1{}\n", encoding="utf-8")
    fake_scripts.mkdir()
    (fake_scripts / "base2026_source_detail_v2.css").write_text(".b26-source-v2{}\n", encoding="utf-8")
    (fake_scripts / "base2026_source_detail_v2.js").write_text("// fixture\n", encoding="utf-8")
    module.ROOT = fake_root
    module.SCRIPTS = fake_scripts

    hashes = module.copy_static_assets(tmp_path / "candidate")
    assert "base2026-interior-v1.css" in hashes
    assert "vendor/geist-local.css" in hashes
    assert "vendor/geist-400.ttf" in hashes
    assert "vendor/manrope-400.ttf" in hashes
    shell = (tmp_path / "candidate/static/alex-v4-static-shell.css").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in shell


def test_apply_research_generator_is_opted_in_but_other_info_pages_are_not() -> None:
    module = load_module("base2026_info_interior", SCRIPTS / "generate-info-pages.py")
    apply_html = module.page_shell(module.PAGE_MAP["09_APPLY_RESEARCH.md"], "Apply Base2026 Research", "<section>Body</section>")
    assert '<body class="b26-interior-v1 b26-interior-apply">' in apply_html
    assert './static/base2026-interior-v1.css?v=' in apply_html
    assert './static/vendor/geist-local.css?v=' in apply_html
    assert "fonts.googleapis.com" not in apply_html
    assert "fonts.gstatic.com" not in apply_html
    assert apply_html.index("static/styles.css") < apply_html.index("base2026-interior-v1.css")

    methodology_html = module.page_shell(module.PAGE_MAP["00_METHODOLOGY.md"], "Methodology", "<section>Body</section>")
    assert "b26-interior-v1" not in methodology_html
    assert "base2026-interior-v1.css" not in methodology_html
    assert "fonts.googleapis.com" in methodology_html


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
