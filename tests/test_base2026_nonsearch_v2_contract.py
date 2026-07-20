from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from base2026_product_shell import footer_html, header_html  # noqa: E402
from template_migration.source_detail import SourceDetailView, render_source_detail  # noqa: E402


def generator():
    spec = importlib.util.spec_from_file_location(
        "base2026_nonsearch_v2_contract_generator",
        SCRIPTS / "generate-public-pages.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def metadata(html: str) -> tuple[str, str, str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title
    h1 = soup.select_one("main h1")
    robots = soup.select_one('meta[name="robots"]')
    canonical = soup.select_one('link[rel="canonical"]')
    assert title and h1 and robots and canonical
    return (
        title.get_text(" ", strip=True),
        h1.get_text(" ", strip=True),
        str(robots.get("content") or ""),
        str(canonical.get("href") or ""),
    )


def assert_product_shell(soup: BeautifulSoup) -> None:
    assert soup.body and soup.body.get("data-b26-visual-root") == "v2"
    assert soup.select_one("header.b26-product-header[data-b26-product-header]")
    assert soup.select_one('footer.ay-site-footer[data-footer-contract="personal-v1"]')
    assert soup.select_one('#ay-v2-mobile-panel')
    assert soup.select_one('[aria-controls="ay-v2-mobile-panel"]')
    assert soup.select_one('footer [data-cookie-preferences]')
    assert soup.select_one('[data-cookie-dialog]')
    assert soup.select_one('script[src*="cookie-consent.js"]')
    assert "Independent consultant serving US local service businesses remotely" in soup.select_one("footer").get_text(" ", strip=True)
    assert soup.select_one("footer .ay-footer-grid")
    assert len(soup.select("footer .ay-footer-menu")) == 3
    assert len(soup.select('[data-b26-component="B26-09"]')) <= 1
    assert not soup.select_one('header a[href="/knowledge/apply-research.html"]')
    assert not soup.select_one('footer a[href="/knowledge/apply-research.html"]')
    for anchor in soup.select(
        'header[data-b26-product-header] a[href], footer[data-footer-contract="personal-v1"] a[href]'
    ):
        assert str(anchor.get("href") or "").startswith("/")


def topic_fixture() -> dict:
    return {
        "topic_id": "content-repurposing",
        "topic": "content repurposing",
        "definition": "Source-backed creator statements and evidence excerpts related to content repurposing.",
        "public": True,
        "public_insight_count": 2,
        "source_count": 2,
        "creator_count": 1,
        "top_creators": [{"handle": "@tjrobertson52", "count": 2}],
    }


def insight_fixture() -> dict:
    return {
        "source_id": "source:alpha",
        "topic_id": "content-repurposing",
        "topic": "content repurposing",
        "creator_handle": "@tjrobertson52",
        "public": True,
        "claim_text": "A source transcript can support several useful assets.",
        "evidence_excerpt": "The reviewed source describes a bounded repurposing workflow.",
        "stance": "asserts",
    }


def test_topics_and_compare_opt_in_without_metadata_or_component_role_drift() -> None:
    module = generator()
    topic = topic_fixture()
    insight = insight_fixture()
    source = {
        "source_id": "source:alpha",
        "item_id": "video-alpha",
        "creator_handle": "@tjrobertson52",
        "source_url": "https://example.com/source-alpha",
        "title": "One source record",
        "excerpt": "A reviewed public source excerpt.",
        "published_date": "2026-07-01",
        "topics": ["content-repurposing"],
    }
    passage = {
        "source_id": "source:alpha",
        "topics": ["content-repurposing"],
        "body": "A reviewed public passage with enough context for the topic evidence page.",
    }
    topic_html = module.topic_page(topic, [source], [passage], [insight])
    topic_soup = BeautifulSoup(topic_html, "html.parser")
    assert metadata(topic_html) == (
        "content repurposing creator evidence | Base2026",
        "content repurposing",
        "index,follow",
        "https://aggressorbulkit.online/knowledge/topics/content-repurposing.html",
    )
    assert_product_shell(topic_soup)
    assert not topic_soup.select_one('.topic-page-hero[data-b26-component="B26-05"]')
    assert topic_soup.select_one('[data-b26-component="B26-07"][data-b26-visual="v2"]')
    assert topic_soup.select_one('[data-b26-component="B26-09"][data-b26-visual="v2"]')

    cards = module.card(
        "content repurposing",
        topic["definition"],
        "content-repurposing.html",
        component_id="B26-05",
        component_variant="topic-card",
    )
    hub_html = module.index_page("Topic Evidence Pages", "Topic evidence directory.", cards, current="topics")
    hub_soup = BeautifulSoup(hub_html, "html.parser")
    assert_product_shell(hub_soup)
    assert hub_soup.select_one('[data-b26-component="B26-05"][data-b26-visual="v2"]')
    assert not hub_soup.select_one('.page-hero[data-b26-component="B26-05"]')

    compare_html = module.compare_page(topic, [insight])
    compare_soup = BeautifulSoup(compare_html, "html.parser")
    assert_product_shell(compare_soup)
    assert compare_soup.select_one('[data-b26-component="B26-06"][data-b26-variant="creator-viewpoint-card"]')
    assert not compare_soup.select_one('.page-hero[data-b26-component="B26-06"]')


def test_creator_analytics_and_resources_use_semantic_cards_and_metrics() -> None:
    module = generator()
    creator_html = module.creator_page(
        "@neilpatel",
        {"url": "https://www.tiktok.com/@neilpatel"},
        [],
        [{"creator_handle": "@neilpatel", "public": True, "topic_id": "ai-visibility", "topic": "AI visibility"}],
    )
    creator_soup = BeautifulSoup(creator_html, "html.parser")
    assert_product_shell(creator_soup)
    assert creator_soup.select_one('[data-b26-component="B26-07"][data-b26-variant="creator-metrics"]')
    assert not creator_soup.select_one('.creator-page-hero[data-b26-component="B26-06"]')

    creator_card = BeautifulSoup(module.creator_index_card("@neilpatel", {}, 2, 3), "html.parser")
    assert creator_card.select_one('[data-b26-component="B26-06"][data-b26-variant="creator-card"][data-b26-visual="v2"]')

    analytics_html = module.analytics_page(
        {"totals": {"source_records": 2, "passages": 3, "public_insight_cards": 4, "public_topics": 1}}
    )
    analytics_soup = BeautifulSoup(analytics_html, "html.parser")
    assert_product_shell(analytics_soup)
    assert analytics_soup.select_one('[data-b26-component="B26-07"][data-b26-variant="dataset-metrics"]')

    resources_html = module.traffic_resources_page(
        {
            "content-repurposing": {
                "target_query": "Content repurposing",
                "meta_description": "Source-backed content repurposing evidence.",
                "proof_source_ids": ["source:alpha"],
                "faq": [],
            }
        },
        [topic_fixture()],
    )
    resources_soup = BeautifulSoup(resources_html, "html.parser")
    assert_product_shell(resources_soup)
    assert resources_soup.select_one('[data-b26-component="B26-05"][data-b26-variant="topic-resource-card"]')
    assert resources_soup.select_one('[data-b26-component="B26-07"][data-b26-variant="resource-metrics"]')
    assert resources_soup.select_one('[data-b26-component="B26-09"][data-b26-variant="resource-bridge"]')
    assert len(resources_soup.select('main a[href^="/knowledge/apply-research.html"]')) == 1
    assert not resources_soup.select(
        'main a[href^="/services/"], main a[href^="/pricing/"], '
        'main a[href^="/ai-visibility-audit/"], main a[href^="/ai-visibility-diagnostic-audit/"]'
    )


def test_strict_source_detail_has_one_public_boundary_and_preserves_admission_metadata(tmp_path: Path) -> None:
    view = SourceDetailView(
        route="sources/tiktok-video-fixture.html",
        item_id="tiktok-video-fixture",
        admission_state="normal_public_card",
        language_code="en",
        head_html=(
            '<meta name="robots" content="index,follow">'
            '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/sources/tiktok-video-fixture.html">'
            '<title>Fixture source</title>'
        ),
        header_html=header_html(),
        footer_html=footer_html(),
        handle="@fixture",
        date="2026-07-18",
        avatar_src="",
        avatar_alt="",
        thesis="Attributed public fixture.",
        original_link="https://www.tiktok.com/@fixture/video/1",
        creator_link="../creators/fixture.html",
        search_link="../?source=tiktok-video-fixture",
        platform_key="tiktok",
        platform_label="TikTok",
        policy="Public excerpt",
        language="English",
        insight_count="1",
        topics=(),
        source_html="<p>Reviewed public fixture text.</p>",
        insights=(),
        questions=(),
        solutions=(),
        archive=False,
        schema_html="",
    )
    html = render_source_detail(view, "fixture-renderer")
    soup = BeautifulSoup(html, "html.parser")
    assert metadata(html) == (
        "Fixture source",
        "@fixture",
        "index,follow",
        "https://aggressorbulkit.online/knowledge/sources/tiktok-video-fixture.html",
    )
    assert_product_shell(soup)
    assert soup.select_one('[data-b26-component="B26-04"][data-b26-visual="v2"]')
    assert len(soup.select('[data-b26-component="B26-08"][data-b26-visual="v2"]')) == 1

    rendered = tmp_path / view.route
    rendered.parent.mkdir(parents=True)
    rendered.write_text(html, encoding="utf-8")
    candidate_css = tmp_path / "static/base2026/shell.css"
    candidate_css.parent.mkdir(parents=True)
    candidate_css.write_bytes((ROOT / "web/static/base2026/shell.css").read_bytes())
    spec = importlib.util.spec_from_file_location(
        "base2026_nonsearch_v2_source_validator",
        SCRIPTS / "validate-source-detail-v2-full-candidate.py",
    )
    assert spec and spec.loader
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    assert validator.validate_shared_footer_contract(tmp_path, view.route) == []


@pytest.mark.parametrize(
    "href",
    (
        "/pricing/",
        "https://aggressorbulkit.online/pricing/",
        "//aggressorbulkit.online/services/",
        "../../../pricing/",
        "..\\..\\pricing/",
        "https://aggressorbulkit.online./pricing/",
        "https://www.aggressorbulkit.online/pricing/",
        "%2e%2e/%2e%2e/%2e%2e/pricing/",
        "..%2f..%2f..%2fpricing/",
    ),
)
def test_nonsearch_generator_fails_closed_on_direct_personal_offer_link(href: str) -> None:
    module = generator()
    with pytest.raises(ValueError, match="bypasses Apply Research"):
        module.index_page(
            "Unsafe fixture",
            "A direct package jump must never survive Base generation.",
            f'<article><a href="{href}">View pricing</a></article>',
            current="topics",
        )


def test_nonsearch_generator_allows_relative_base_and_external_source_links() -> None:
    module = generator()
    rendered = module.index_page(
        "Safe fixture",
        "Base and attributed external navigation remain available.",
        (
            '<article><a href="../methodology.html">Methodology</a>'
            '<a href="https://www.aggressorbulkit.online/knowledge/source-policy.html">Source policy</a>'
            '<a href="https://www.tiktok.com/@fixture/video/123">Original source</a></article>'
        ),
        current="topics",
    )
    assert 'href="../methodology.html"' in rendered
    assert 'href="https://www.aggressorbulkit.online/knowledge/source-policy.html"' in rendered
    assert 'href="https://www.tiktok.com/@fixture/video/123"' in rendered


def test_search_stays_visual_control_and_keeps_exact_metadata() -> None:
    spec = importlib.util.spec_from_file_location(
        "base2026_nonsearch_v2_search_control",
        SCRIPTS / "generate-base2026-search-v1.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    rendered = module.transform(source)
    before = BeautifulSoup(source, "html.parser")
    after = BeautifulSoup(rendered, "html.parser")
    before_meta = (
        str(before.select_one('meta[name="robots"]').get("content")),
        str(before.select_one('link[rel="canonical"]').get("href")),
        before.title.get_text(" ", strip=True),
    )
    after_meta = (
        str(after.select_one('meta[name="robots"]').get("content")),
        str(after.select_one('link[rel="canonical"]').get("href")),
        after.title.get_text(" ", strip=True),
    )
    assert after_meta == before_meta
    assert not after.select_one('[data-b26-visual-root="v2"]')
    assert not after.select_one('[data-b26-visual="v2"]')
