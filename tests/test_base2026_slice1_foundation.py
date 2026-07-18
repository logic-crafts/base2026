from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from base2026_ui_system import ASSET_FILES, SYSTEM_VERSION  # noqa: E402
from template_migration.source_detail import SourceDetailView, render_source_detail  # noqa: E402


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} assignment not found in {path}")


def meta_contract(soup: BeautifulSoup) -> tuple[str, str]:
    robots = soup.select_one('meta[name="robots"]')
    canonical = soup.select_one('link[rel="canonical"]')
    assert robots and canonical
    return str(robots.get("content") or ""), str(canonical.get("href") or "")


def test_canonical_personal_generators_link_base2026_to_product_root() -> None:
    generators = (
        SCRIPTS / "generate-alex-base2026-native-site.py",
        SCRIPTS / "generate-alex-static-site.py",
    )
    for generator in generators:
        nav = literal_assignment(generator, "NAV")
        base_links = [href for href, label in nav if label == "Base2026"]
        assert base_links == ["/knowledge/"]
        assert ("/knowledge/ai-visibility-pages/", "Base2026") not in nav


def test_b26_assets_are_versioned_presentation_only_contract() -> None:
    asset_root = ROOT / "web/static/base2026"
    forbidden = (
        "/Users/",
        "\\Users\\",
        ".planning/",
        "public-data/",
        "source_records.jsonl",
        "raw_query",
        "email_address",
    )
    for asset in ASSET_FILES:
        path = asset_root / asset
        text = path.read_text(encoding="utf-8")
        assert f"v{SYSTEM_VERSION}" in text.splitlines()[0]
        assert not any(value in text for value in forbidden)
    tokens = (asset_root / "tokens.css").read_text(encoding="utf-8")
    for contract in (
        "--b26-color-cream-100: #f4f1e9",
        "--b26-color-paper: #ffffff",
        "--b26-color-ink-950: #0f172a",
        "--b26-color-slate-600: #5f5e58",
        "--b26-radius-control: 8px",
        "--b26-radius-nested: 12px",
        "--b26-radius-row: 18px",
        "--b26-radius-card: 24px",
        "--b26-radius-panel-mobile: 28px",
        "--b26-radius-panel: 34px",
        "--b26-radius-pill: 999px",
        "--b26-type-h1: clamp",
    ):
        assert contract in tokens
    for rejected in ("#111111", "#fffaf0", "#10231f", "--b26-interactive-accent"):
        assert rejected not in tokens.lower()

    shell = (asset_root / "shell.css").read_text(encoding="utf-8")
    components = (asset_root / "components.css").read_text(encoding="utf-8")
    assert '[data-b26-visual-root="v2"]' in shell
    assert '[data-b26-system-version="1.0.0"]' not in shell
    assert '[data-b26-visual="v2"]' in components
    assert '[data-b26-component="B26-09"][data-b26-visual="v2"]' in components
    assert "background: var(--b26-color-ink-950)" in components


def test_search_generator_wires_assets_and_b26_component_markers_without_metadata_drift() -> None:
    module = load_script("base2026_search_slice1", "generate-base2026-search-v1.py")
    source = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    before = BeautifulSoup(source, "html.parser")
    rendered = module.transform(source)
    after = BeautifulSoup(rendered, "html.parser")

    assert meta_contract(after) == meta_contract(before)
    assert after.body and after.body.get("data-b26-system-version") == SYSTEM_VERSION
    assert after.body.get("data-b26-family") == "search"
    assert [link.get("data-b26-asset") for link in after.select("link[data-b26-asset]")] == list(ASSET_FILES)
    for component_id in ("B26-01", "B26-02", "B26-03", "B26-04", "B26-07", "B26-08"):
        assert after.select_one(f'[data-b26-component="{component_id}"]')
    assert not after.select_one('[data-b26-visual="v2"]')
    assert not after.select_one('[data-b26-visual-root="v2"]')
    for selector in ("#searchbox", "#hits", "#mobile-filter-panel", "#source-detail-panel"):
        assert after.select_one(selector)


def test_topic_fixture_uses_compact_component_contract_without_route_contract_changes() -> None:
    module = load_script("base2026_public_pages_slice1", "generate-public-pages.py")
    rendered = module.topic_page(
        {
            "topic_id": "content-repurposing",
            "topic": "Content Repurposing",
            "definition": "Public evidence connected to content repurposing.",
            "public_insight_count": 0,
            "source_count": 0,
            "top_creators": [],
        },
        [],
        [],
        [],
        {},
        {},
    )
    soup = BeautifulSoup(rendered, "html.parser")

    assert meta_contract(soup) == (
        "noindex,follow",
        "https://aggressorbulkit.online/knowledge/topics/content-repurposing.html",
    )
    assert soup.body and soup.body.get("data-b26-system-version") == SYSTEM_VERSION
    assert soup.body.get("data-b26-family") == "topics"
    assert soup.select_one('[data-b26-section="topic-detail-hero"]')
    assert not soup.select_one('[data-b26-component="B26-05"]')
    assert soup.select_one('[data-b26-component="B26-07"][data-b26-variant="topic-metrics"]')
    assert soup.select_one('[data-b26-component="B26-09"][data-b26-variant="topic-bridge"]')
    assert not soup.select_one('[data-b26-visual="v2"]')
    assert [link.get("data-b26-asset") for link in soup.select("link[data-b26-asset]")] == list(ASSET_FILES)

    topic_card = BeautifulSoup(
        module.card(
            "Content Repurposing",
            "Public evidence connected to content repurposing.",
            "content-repurposing.html",
            "12 public insights",
            component_id="B26-05",
            component_variant="topic-card",
        ),
        "html.parser",
    )
    assert topic_card.select_one('[data-b26-component="B26-05"][data-b26-variant="topic-card"]')
    assert not topic_card.select_one('[data-b26-visual="v2"]')


def test_source_detail_fixture_preserves_admission_metadata_and_loads_shared_assets() -> None:
    view = SourceDetailView(
        route="sources/tiktok-video-fixture.html",
        item_id="tiktok-video-fixture",
        admission_state="provenance_archive_noindex",
        language_code="en",
        head_html=(
            '<meta name="robots" content="noindex,follow">'
            '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/sources/tiktok-video-fixture.html">'
            '<title>Fixture source</title>'
        ),
        header_html="<header>Header</header>",
        footer_html="<footer>Footer</footer>",
        handle="@fixture",
        date="2026-07-18",
        avatar_src="",
        avatar_alt="",
        thesis="Attributed archive fixture.",
        original_link="https://www.tiktok.com/@fixture/video/1",
        creator_link="",
        search_link="",
        platform_key="tiktok",
        platform_label="TikTok",
        policy="Public provenance archive",
        language="English",
        insight_count="",
        topics=(),
        source_html="<p>Reviewed public fixture text.</p>",
        insights=(),
        questions=(),
        solutions=(),
        archive=True,
        schema_html="",
    )
    soup = BeautifulSoup(render_source_detail(view, "fixture-renderer"), "html.parser")

    assert meta_contract(soup) == (
        "noindex,follow",
        "https://aggressorbulkit.online/knowledge/sources/tiktok-video-fixture.html",
    )
    assert soup.body and soup.body.get("data-b26-system-version") == SYSTEM_VERSION
    assert soup.body.get("data-b26-family") == "source"
    assert soup.select_one('[data-b26-component="B26-04"][data-b26-variant="source-detail"]')
    assert soup.select_one('[data-admission-state="provenance_archive_noindex"]')
    assert [link.get("data-b26-asset") for link in soup.select("link[data-b26-asset]")] == list(ASSET_FILES)


def test_release_and_source_candidate_paths_copy_the_complete_b26_asset_set() -> None:
    for script_name in ("package-public-release.ps1", "package-public-hotfix-from-export.ps1"):
        text = (SCRIPTS / script_name).read_text(encoding="utf-8")
        assert 'Copy-Item "./web/static/base2026" (Join-Path $StaticRoot "base2026") -Recurse -Force' in text

    candidate = (SCRIPTS / "build-source-detail-v2-full-candidate.py").read_text(encoding="utf-8")
    assert 'shutil.copytree(source_b26_system, static_out / "base2026", dirs_exist_ok=True)' in candidate
    for asset in ASSET_FILES:
        assert f'"base2026/{asset}"' in candidate
