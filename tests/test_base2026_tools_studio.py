"""Static contract tests for the public Base2026 tools hub.

These checks deliberately avoid a browser, credentials, network calls and
private fixtures.  They verify the source contract that the root builder will
wire into the public shell; visual and route readback remain root-owned QA.
"""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "templates" / "base2026-tools-studio.html"
CSS_PATH = ROOT / "templates" / "base2026-tools-studio.css"
JS_PATH = ROOT / "templates" / "base2026-tools-studio.js"


class MarkupParser(HTMLParser):
    """Small HTML inventory for structural assertions without dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.links: list[tuple[str, dict[str, str]]] = []
        self.scripts: list[str] = []
        self._script_depth = 0
        self._script_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attributes))
        if tag == "a":
            self.links.append(("", attributes))
        if tag == "script":
            self._script_depth += 1
            self._script_buffer = []

    def handle_data(self, data: str) -> None:
        if self._script_depth:
            self._script_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_depth:
            self.scripts.append("".join(self._script_buffer).strip())
            self._script_depth -= 1


class ToolsStudioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.css = CSS_PATH.read_text(encoding="utf-8")
        cls.js = JS_PATH.read_text(encoding="utf-8")
        cls.parser = MarkupParser()
        cls.parser.feed(cls.html)

    def test_public_markup_has_shell_placeholders_and_indexable_seo(self) -> None:
        self.assertEqual(self.html.count("{{STARTUP_HEADER}}"), 1)
        self.assertEqual(self.html.count("{{STARTUP_FOOTER}}"), 1)
        self.assertEqual(self.html.count("<h1"), 1)
        self.assertIn("Free tools. Real next steps.", self.html)
        self.assertIn('<meta name="robots" content="index,follow">', self.html)
        self.assertIn('<link rel="canonical" href="https://base2026.dev/tools/">', self.html)
        self.assertIn("/static/base2026-startup-shell.css?v=20260820-b26v1", self.html)
        self.assertNotIn("2275", self.html)
        self.assertNotIn("1649", self.html)
        self.assertNotIn("125", self.html)
        self.assertNotIn("183", self.html)

    def test_schema_lists_only_real_hosted_tools(self) -> None:
        schemas = [json.loads(script) for script in self.parser.scripts if script.startswith("{")]
        collection = next(schema for schema in schemas if schema.get("@type") == "CollectionPage")
        self.assertEqual(collection["url"], "https://base2026.dev/tools/")
        items = collection["mainEntity"]["itemListElement"]
        self.assertEqual(collection["mainEntity"]["numberOfItems"], 4)
        self.assertEqual(len(items), 4)
        urls = [item["item"]["url"] for item in items]
        self.assertEqual(
            urls,
            [
                "https://base2026.dev/tools/evidence-search/",
                "https://base2026.dev/tools/source-diversity-check/",
                "https://base2026.dev/tools/source-backed-brief/",
                "https://base2026.dev/tools/page-readiness/",
            ],
        )
        self.assertTrue(all(item["item"]["isAccessibleForFree"] for item in items))
        readiness = items[-1]["item"]
        self.assertIn("supplied page HTML", readiness["description"])
        self.assertIn("without fetching the URL", readiness["description"])
        self.assertNotIn("Experiment Planner", json.dumps(collection))

    def test_tool_routes_and_no_js_copy_are_visible(self) -> None:
        expected_hrefs = {
            "/tools/evidence-search/",
            "/tools/source-diversity-check/",
            "/tools/source-backed-brief/",
            "/tools/page-readiness/",
            "/mcp",
            "https://github.com/offflinerpsy/base2026/blob/main/docs/BASE2026_FREE_SKILLS.md#seo-experiment-planner",
        }
        hrefs = {attrs.get("href") for _, attrs in self.parser.links}
        self.assertTrue(expected_hrefs.issubset(hrefs))
        self.assertNotRegex(self.html.lower(), r'<a[^>]+href=["\'][^"\']*download[^"\']*["\']')
        self.assertIn("Enable JavaScript to load the current collection totals.", self.html)
        self.assertIn("The output is a decision, not another tab.", self.html)
        self.assertIn("supplied public HTML with an optional HTTPS URL context", self.html)
        self.assertNotIn("public source path receives only deliberate, non-sensitive queries or IDs", self.html)

    def test_factory_has_four_accessible_stations_and_truthful_controls(self) -> None:
        station_buttons = [
            attrs
            for tag, attrs in self.parser.tags
            if tag == "button" and attrs.get("role") == "tab"
        ]
        self.assertEqual(len(station_buttons), 4)
        self.assertEqual(
            {attrs.get("data-station-button") for attrs in station_buttons},
            {"find", "extract", "attribute", "publish"},
        )
        for attrs in station_buttons:
            self.assertEqual(attrs.get("type"), "button")
            self.assertEqual(attrs.get("aria-controls"), "station-panel")
            self.assertIn(attrs.get("aria-selected"), {"true", "false"})
            self.assertIn("disabled", attrs, "static markup must keep station controls inert until JS is ready")
            self.assertNotIn("tabindex", attrs, "JS should add roving tab stops after enabling the controls")
        toggle = next(attrs for tag, attrs in self.parser.tags if attrs.get("data-factory-toggle") is not None)
        self.assertEqual(toggle.get("type"), "button")
        self.assertEqual(toggle.get("aria-pressed"), "false")
        self.assertIn("hidden", toggle, "the pause affordance should appear only after JS initializes it")
        self.assertIn("Pause illustration", self.html)
        self.assertIn("From source records to a working brief.", self.html)
        self.assertIn('data-factory-playing="true"', self.html)
        self.assertIn('data-factory-visible="false"', self.html)
        publish_button = re.search(
            r'<button[^>]+data-station-button="publish"[^>]*>.*?</button>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(publish_button)
        self.assertIn('class="b26-tools-station__name">Use</span>', publish_button.group(0))

    def test_reviewed_media_uses_real_dimensions_and_bounded_loading(self) -> None:
        images = {
            attrs.get("src"): attrs
            for tag, attrs in self.parser.tags
            if tag == "img" and attrs.get("src")
        }
        self.assertEqual(
            set(images),
            {
                "/static/assets/tools-studio/evidence-workbench.webp",
                "/static/assets/tools-studio/evidence-search-interface.webp",
            },
        )
        for src in images:
            asset_path = ROOT / "templates" / src.removeprefix("/static/")
            self.assertTrue(asset_path.is_file(), f"reviewed asset is missing: {asset_path}")
            self.assertGreater(asset_path.stat().st_size, 0, f"reviewed asset is empty: {asset_path}")
        hero = images["/static/assets/tools-studio/evidence-workbench.webp"]
        self.assertEqual((hero.get("width"), hero.get("height")), ("1200", "800"))
        self.assertTrue(hero.get("alt"), "hero image needs a meaningful alt")
        self.assertEqual(hero.get("fetchpriority"), "high")
        self.assertNotIn("loading", hero)

        search = images["/static/assets/tools-studio/evidence-search-interface.webp"]
        self.assertEqual((search.get("width"), search.get("height")), ("1203", "744"))
        self.assertTrue(search.get("alt"), "search screenshot needs a meaningful alt")
        self.assertEqual(search.get("loading"), "lazy")
        self.assertNotIn("fetchpriority", search)
        self.assertEqual(
            sum(attrs.get("fetchpriority") == "high" for attrs in images.values()),
            1,
            "only the hero asset may be high priority",
        )

    def test_cards_are_progressive_reveals_with_focus_fallback(self) -> None:
        cards = [
            attrs
            for tag, attrs in self.parser.tags
            if tag == "article" and "b26-tools-card" in attrs.get("class", "").split()
        ]
        self.assertEqual(len(cards), 6)
        self.assertTrue(all("data-reveal" in attrs for attrs in cards))
        readiness_card = next(
            attrs for attrs in cards if "b26-tools-card--readiness" in attrs.get("class", "").split()
        )
        self.assertTrue(readiness_card.get("data-reveal") is not None)
        readiness_markup = re.search(
            r'<article[^>]+b26-tools-card--readiness[^>]*>.*?</article>',
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(readiness_markup)
        self.assertIn("Page Source Check", readiness_markup.group(0))
        self.assertIn('href="/tools/page-readiness/"', readiness_markup.group(0))
        self.assertIn("does not fetch a URL", readiness_markup.group(0))
        self.assertIn("indexation or rankings", readiness_markup.group(0))
        self.assertIn(".b26-tools-card--readiness", self.css)
        self.assertIn(".b26-tools-studio.is-motion-ready [data-reveal]", self.css)
        self.assertRegex(
            self.css,
            r"\.b26-tools-studio\.is-motion-ready\s+\[data-reveal\]:focus-within\s*\{[^}]*opacity:\s*1;[^}]*transform:\s*none;",
        )

    def test_readiness_closes_desktop_grid_without_reordering_mobile(self) -> None:
        desktop = self.css.split("@media (min-width: 721px) {", 1)[1].split(
            ".b26-tools-studio__workbench-note", 1
        )[0]
        self.assertRegex(
            desktop,
            r"\.b26-tools-card--readiness\s*\{[^}]*grid-column:\s*1 / -1;[^}]*display:\s*grid;",
        )
        self.assertIn("grid-template-columns: minmax(0, .85fr) minmax(0, 1.15fr);", desktop)
        self.assertIn("> .b26-tools-card__facts { grid-column: 2;", desktop)
        self.assertIn("> .b26-tools-card__action { grid-column: 2;", desktop)
        self.assertNotIn("order:", desktop)

    def test_scripts_are_local_and_no_animation_library_is_loaded(self) -> None:
        script_srcs = [attrs.get("src") for tag, attrs in self.parser.tags if tag == "script" and attrs.get("src")]
        self.assertEqual(len(script_srcs), 1)
        self.assertTrue(script_srcs[0].startswith("/static/"))
        self.assertNotIn("gsap", (self.html + self.css + self.js).lower())

    def test_stats_markup_uses_only_current_public_contract_fields(self) -> None:
        keys = re.findall(r'data-stat-value="([^"]+)"', self.html)
        self.assertEqual(
            set(keys),
            {"documents_indexed", "distinct_sources", "public_evidence_routes", "projected_cards"},
        )
        self.assertEqual(len(keys), 4)
        self.assertIn("data-stat-generated", self.html)
        self.assertIn("generated_at", self.html)
        live_section = re.search(r'<section[^>]+data-live-stats[^>]*>.*?</section>', self.html, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(live_section)
        stat_copy = " ".join(re.findall(r'<article class="b26-tools-stat">.*?</article>', live_section.group(0), re.DOTALL | re.IGNORECASE))
        self.assertNotRegex(stat_copy.lower(), r"\b(?:users?|visits?|videos?|job running|backend health)\b")
        self.assertEqual(self.html.count('>Unavailable</strong>'), 4)

    def test_css_keeps_blueprint_motion_scoped_and_reduced_safe(self) -> None:
        self.assertIn("--b26-ease-out: cubic-bezier(0.23, 1, 0.32, 1)", self.css)
        self.assertIn("--b26-ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)", self.css)
        self.assertNotIn("transition: all", self.css)
        self.assertNotIn("scale(0)", self.css)
        self.assertNotIn("infinite", self.css)
        self.assertIn("@keyframes b26-tools-factory-signal", self.css)
        self.assertRegex(self.css, r"animation: b26-tools-factory-signal 2600ms[^;]* 2 both")
        self.assertIn("animation-play-state: paused", self.css)
        self.assertIn("data-factory-page-visible=\"true\"", self.css)
        self.assertIn(".b26-tools-studio.is-motion-ready [data-reveal]", self.css)
        self.assertIn("opacity: 1 !important", self.css)
        self.assertIn("transform: none !important", self.css)
        self.assertIn("animation: none !important", self.css)
        self.assertIn("@media (max-width: 390px)", self.css)
        self.assertIn("width: calc(100% - 28px)", self.css)
        self.assertNotRegex(self.css, r"url\(https?://")

    def test_runtime_is_bounded_same_origin_visible_only_and_keyboard_ready(self) -> None:
        self.assertEqual(self.js.count('fetch("'), 1)
        self.assertIn('fetch("/api/stats"', self.js)
        self.assertIn('credentials: "same-origin"', self.js)
        self.assertIn("new AbortController()", self.js)
        self.assertIn("controller.abort()", self.js)
        self.assertIn("window.setTimeout(function () { controller.abort(); }, 8000)", self.js)
        self.assertIn("window.setInterval(refreshStats, 60000)", self.js)
        self.assertIn("document.visibilityState", self.js)
        self.assertIn('"visibilitychange"', self.js)
        self.assertIn("statsIntersecting", self.js)
        self.assertIn('"IntersectionObserver" in window', self.js)
        self.assertIn('"(prefers-reduced-motion: reduce)"', self.js)
        self.assertIn("data-factory-visible", self.js)
        self.assertIn("data-factory-playing", self.js)
        self.assertIn('button.removeAttribute("disabled")', self.js)
        self.assertIn('factoryToggle.removeAttribute("hidden")', self.js)
        self.assertIn('factoryToggle.setAttribute("disabled", "")', self.js)
        self.assertIn('"Replay illustration"', self.js)
        self.assertIn('"Motion reduced"', self.js)
        self.assertIn('event.key === "ArrowRight"', self.js)
        self.assertIn('event.key === "Home"', self.js)
        self.assertIn('event.key === "End"', self.js)
        self.assertIn("Number.isSafeInteger(value)", self.js)
        self.assertIn('"Unavailable"', self.js)
        self.assertIn("lastGoodValues", self.js)
        self.assertIn('lastGoodValues[key].toLocaleString("en-US")', self.js)
        self.assertNotIn("Math.random", self.js)
        self.assertNotIn("localStorage", self.js)
        self.assertNotIn("sessionStorage", self.js)
        self.assertNotIn("sendBeacon", self.js)
        self.assertNotIn("document.cookie", self.js)
        self.assertNotIn("innerHTML", self.js)
        self.assertNotRegex(self.js, r"fetch\(\s*[\"']https?://")

    def test_required_contract_literals_are_not_silently_renamed(self) -> None:
        for key in ("documents_indexed", "distinct_sources", "public_evidence_routes", "projected_cards"):
            self.assertIn(f'"{key}"', self.js)
        self.assertIn('index: "04 / USE"', self.js)
        self.assertIn('title: "Build a brief. Choose the next move."', self.js)
        self.assertIn("payload.generated_at", self.js)
        self.assertIn('"Public counters stale', self.js)
        self.assertIn('"Public counters unavailable · no zero inferred."', self.js)


if __name__ == "__main__":
    unittest.main()
