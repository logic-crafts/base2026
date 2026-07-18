#!/usr/bin/env python3
"""Browser fixture for the opt-in Base2026 interior and consent contracts."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = ((320, 700), (390, 780))


def fixture_html() -> str:
    styles = (ROOT / "web/static/styles.css").as_uri()
    interior = (ROOT / "web/static/base2026-interior-v1.css").as_uri()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="{styles}"><link rel="stylesheet" href="{interior}"></head>
<body class="b26-interior-v1 b26-interior-apply">
<main><h1>Apply Research fixture</h1><p>Content remains available behind the compact consent surface.</p></main>
<section class="cookie-banner" data-cookie-banner aria-label="Cookie preferences">
  <div><h2>Cookie preferences</h2><p>Optional analytics require consent.</p></div>
  <div class="cookie-actions">
    <button type="button" class="ay-button" data-cookie-accept>Accept All</button>
    <button type="button" class="ay-button-secondary" data-cookie-reject>Reject Non-Essential</button>
    <button type="button" class="ay-button-secondary" data-cookie-manage>Manage Preferences</button>
  </div>
</section></body></html>"""


def main() -> int:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="base2026-interior-browser-") as temp_name:
        fixture = Path(temp_name) / "index.html"
        fixture.write_text(fixture_html(), encoding="utf-8")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(fixture.as_uri(), wait_until="load")
                layout = page.evaluate(
                    """() => {
                      const banner = document.querySelector('.cookie-banner').getBoundingClientRect();
                      const buttons = [...document.querySelectorAll('.cookie-actions button')].map((node) => {
                        const rect = node.getBoundingClientRect();
                        return {left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, height: rect.height};
                      });
                      return {
                        banner: {left: banner.left, right: banner.right, top: banner.top, bottom: banner.bottom},
                        buttons,
                        scrollWidth: document.documentElement.scrollWidth,
                        viewportWidth: innerWidth,
                      };
                    }"""
                )
                banner = layout["banner"]
                buttons = layout["buttons"]
                failures: list[str] = []
                if banner["left"] < 0 or banner["right"] > width or banner["top"] < 0 or banner["bottom"] > height:
                    failures.append("banner escapes viewport")
                if layout["scrollWidth"] > layout["viewportWidth"]:
                    failures.append("horizontal overflow")
                if len(buttons) != 3 or any(button["height"] < 44 for button in buttons):
                    failures.append("cookie actions are not three 44px controls")
                for first, second in zip(buttons, buttons[1:]):
                    if first["right"] > second["left"] or first["bottom"] < second["top"]:
                        failures.append("cookie actions overlap or stack")
                page.locator("body").press("Tab")
                focus_order = [page.evaluate("document.activeElement?.dataset.cookieAccept !== undefined ? 'accept' : ''")]
                page.keyboard.press("Tab")
                focus_order.append(page.evaluate("document.activeElement?.dataset.cookieReject !== undefined ? 'reject' : ''"))
                page.keyboard.press("Tab")
                focus_order.append(page.evaluate("document.activeElement?.dataset.cookieManage !== undefined ? 'manage' : ''"))
                if focus_order != ["accept", "reject", "manage"]:
                    failures.append(f"keyboard order is {focus_order}")
                results.append({"viewport": width, "failures": failures, "button_heights": [round(row["height"], 2) for row in buttons]})
                page.close()
            browser.close()
    failures = [result for result in results if result["failures"]]
    print(json.dumps({"ok": not failures, "results": results}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
