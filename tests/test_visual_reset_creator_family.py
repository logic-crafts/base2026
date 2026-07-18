from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "visual_reset_creator_family", SCRIPTS / "generate-public-pages.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def declaration_block(css: str, selector: str) -> str:
    match = re.search(rf"(?m)^{re.escape(selector)}\s*\{{([^}}]+)\}}", css)
    assert match, f"missing CSS selector: {selector}"
    return match.group(1)


def test_creator_profile_identity_tools_and_metrics_are_visual_reset_components() -> None:
    generator = load_generator()
    page = generator.creator_page(
        "neilpatel",
        {"url": "https://www.tiktok.com/@neilpatel"},
        [],
        [
            {
                "creator_handle": "neilpatel",
                "public": True,
                "topic_id": "ai-visibility",
                "topic": "AI visibility",
            }
        ],
    )
    soup = BeautifulSoup(page, "html.parser")

    assert "b26-family-creators" in (soup.body.get("class") or [])
    assert soup.select_one(".creator-page-hero .creator-page-avatar")
    assert soup.select_one(".creator-page-hero .platform-icon-only .platform-logo")
    assert len(soup.select(".source-share-actions .source-share-action")) == 4
    assert all(button.select_one("svg") for button in soup.select(".source-share-action"))
    assert [node.get_text(" ", strip=True) for node in soup.select(".source-hero-meta .source-meta-chip")] == [
        "0 records",
        "1 insights",
        "1 topics",
    ]

    stylesheets = [str(node.get("href") or "") for node in soup.select('link[rel~="stylesheet"]')]
    assert len(stylesheets) == 1
    assert "alex-design-system-v2.css" in stylesheets[0]
    assert "styles.css" not in stylesheets[0]
    assert soup.select_one('link[rel="canonical"]')["href"].endswith(
        "/knowledge/creators/neilpatel.html"
    )


def test_creator_profile_visual_primitives_are_bounded_on_desktop_and_mobile() -> None:
    css = (ROOT / "web/static/alex-design-system-v2.css").read_text(encoding="utf-8")

    platform = declaration_block(css, ".platform-logo")
    assert "width: 18px" in platform
    assert "height: 18px" in platform

    share_icon = declaration_block(css, ".source-share-action svg")
    assert "width: 16px" in share_icon
    assert "height: 16px" in share_icon

    avatar = declaration_block(css, ".b26-family-creators .creator-page-avatar")
    assert "width: 64px" in avatar
    assert "height: 64px" in avatar
    assert "overflow: hidden" in avatar
    assert "border-radius: 50%" in avatar

    metrics = declaration_block(css, ".b26-family-creators .source-hero-meta")
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in metrics
    assert "overflow: hidden" in metrics

    assert "@media (max-width: 900px)" in css
    assert ".b26-family-creators .creator-page-hero { grid-template-columns: 1fr;" in css
    assert ".b26-family-creators .creator-page-avatar { width: 50px; height: 50px;" in css

    lowered = css.lower()
    for forbidden in ("#c84f07", "#ef6b13", "#f97316", "fonts.googleapis.com"):
        assert forbidden not in lowered
