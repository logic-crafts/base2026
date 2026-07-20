from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from base2026_ui_system import ASSET_FILES, SYSTEM_VERSION  # noqa: E402
from alex_design_system_v2 import apply_information_architecture  # noqa: E402


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def class_tokens(markup: str) -> set[str]:
    soup = BeautifulSoup(markup, "html.parser")
    return {
        str(class_name)
        for node in soup.select("[class]")
        for class_name in (node.get("class") or [])
    }


def assert_single_v2_stylesheet(markup: str) -> None:
    soup = BeautifulSoup(markup, "html.parser")
    hrefs = [str(node.get("href") or "") for node in soup.select('link[rel~="stylesheet"]')]
    assert len(hrefs) in {1, 1 + len(ASSET_FILES)}
    assert "alex-design-system-v2.css" in hrefs[0]
    assert "styles.css" not in hrefs[0]
    if len(hrefs) > 1:
        assert [href.rsplit("/", 1)[-1] for href in hrefs[1:]] == [
            f"{asset}?v={SYSTEM_VERSION}" for asset in ASSET_FILES
        ]
    assert "fonts.googleapis.com" not in markup


def test_governance_roadmap_and_support_component_selectors_are_closed() -> None:
    generator = load_script("visual_reset_info_family_closure", "generate-info-pages.py")
    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")

    rendered: dict[str, str] = {}
    for source_name in ("00_METHODOLOGY.md", "01_ROADMAP.md", "05_SUPPORT_PAGE.md"):
        meta = generator.PAGE_MAP[source_name]
        markdown = (ROOT / "docs/public-pages" / source_name).read_text(encoding="utf-8")
        h1, body = generator.render_markdown(markdown, meta["body_class"])
        rendered[meta["slug"]] = generator.page_shell(meta, h1, body)

    for markup in rendered.values():
        assert_single_v2_stylesheet(markup)
        assert "b26-family-governance" in class_tokens(markup)

    roadmap_classes = {
        "roadmap-experience",
        "roadmap-experience__intro",
        "summary-strip",
        "control-strip",
        "phase-tabs",
        "viz-grid",
        "roadmap-panel",
        "flow-canvas",
        "funding-grid",
        "priority-stack",
        "proof-grid",
        "proof-card",
        "roadmap-fallback",
    }
    support_classes = {
        "support-experience",
        "support-experience__intro",
        "support-lanes",
        "support-flow",
    }
    assert roadmap_classes <= class_tokens(rendered["roadmap.html"])
    assert support_classes <= class_tokens(rendered["support.html"])
    assert not {
        "base-contact-section",
        "base-contact-copy",
        "base-contact-form",
        "base-contact-form__full",
        "contact-email-link",
    } & class_tokens(rendered["support.html"])
    assert "Use the contact form below" not in rendered["support.html"]
    assert 'href="mailto:offflinerpsy@gmail.com"' in rendered["support.html"]

    roadmap_js = (ROOT / "web/static/roadmap.js").read_text(encoding="utf-8")
    dynamic_roadmap_classes = {
        "phase-tab",
        "phase-sequence",
        "sequence-step",
        "sequence-step__number",
        "sequence-step__body",
        "phase-detail-card",
        "detail-meta",
        "status-badge",
        "milestone-grid",
        "milestone-card",
        "milestone-card__head",
        "bar-row",
        "bar-track",
        "bar-fill",
        "funding-card",
        "priority-column",
        "mini-list",
    }
    for class_name in roadmap_classes | support_classes | dynamic_roadmap_classes:
        assert f".{class_name}" in css, f"missing shared selector for {class_name}"
    for class_name in dynamic_roadmap_classes:
        assert class_name in roadmap_js, f"fixture drift: roadmap.js no longer emits {class_name}"

    roadmap = apply_information_architecture(rendered["roadmap.html"], "roadmap.html")
    methodology = apply_information_architecture(rendered["methodology.html"], "methodology.html")
    roadmap_soup = BeautifulSoup(roadmap, "html.parser")
    methodology_soup = BeautifulSoup(methodology, "html.parser")
    assert roadmap_soup.select_one(".b26-k-document-layout") is None
    assert roadmap_soup.select_one(".b26-k-document-rail") is None
    assert roadmap_soup.select_one(".b26-k-document-context[role='note']")
    assert methodology_soup.select_one(".b26-k-document-layout")


def test_traffic_resource_hub_and_topic_support_components_are_closed() -> None:
    generator = load_script("visual_reset_public_family_closure", "generate-public-pages.py")
    config = json.loads((ROOT / "data/base2026_topic_traffic_pages.json").read_text(encoding="utf-8"))
    markup = generator.traffic_resources_page(config, [])
    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")

    assert_single_v2_stylesheet(markup)
    tokens = class_tokens(markup)
    required = {
        "b26-about-hero",
        "b26-about-hero-copy",
        "b26-founder-quote",
        "b26-founder-support",
        "b26-hero-figure",
        "b26-hero-person",
        "traffic-resource-intro",
        "traffic-resource-summary",
        "traffic-resource-cluster",
        "traffic-resource-grid",
        "traffic-resource-card",
        "traffic-resource-card__meta",
        "traffic-resource-cta",
        "analytics-stat-grid",
        "analytics-stat",
    }
    assert required <= tokens
    for class_name in required:
        assert f".{class_name}" in css, f"missing shared selector for {class_name}"

    for class_name in (
        "topic-answer-capsule",
        "topic-source-proof",
        "topic-source-proof__grid",
        "topic-faq",
        "topic-faq__grid",
        "topic-faq__item",
        "topic-traffic-cta",
    ):
        assert f".{class_name}" in css

    lowered = css.lower()
    for forbidden in ("#c84f07", "#ef6b13", "#f97316", "fonts.googleapis.com"):
        assert forbidden not in lowered
