"""Static contract tests for the public WordPress Evidence Sidebar landing page."""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING_PATH = ROOT / "templates" / "base2026-wordpress-evidence-sidebar.html"
STUDIO_PATH = ROOT / "templates" / "base2026-tools-studio.html"
CSS_PATH = ROOT / "templates" / "base2026-tools-studio.css"


class LandingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.scripts: list[str] = []
        self._script_depth = 0
        self._script_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attributes))
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


class WordPressLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = LANDING_PATH.read_text(encoding="utf-8")
        cls.studio = STUDIO_PATH.read_text(encoding="utf-8")
        cls.css = CSS_PATH.read_text(encoding="utf-8")
        cls.parser = LandingParser()
        cls.parser.feed(cls.html)

    def test_indexable_page_uses_shell_and_exact_public_route(self) -> None:
        self.assertEqual(self.html.count("{{STARTUP_HEADER}}"), 1)
        self.assertEqual(self.html.count("{{STARTUP_FOOTER}}"), 1)
        self.assertEqual(self.html.count("<h1"), 1)
        self.assertIn("<title>Free WordPress Evidence Research Plugin | Base2026</title>", self.html)
        self.assertIn('<meta name="robots" content="index,follow">', self.html)
        self.assertIn('<link rel="canonical" href="https://base2026.dev/tools/wordpress-evidence-sidebar/">', self.html)
        self.assertIn('/static/base2026-startup-shell.css?v=20260820-b26v1', self.html)
        self.assertIn('/static/base2026-tools-studio.css?v=20260905-tools-studio-v1', self.html)
        self.assertIn("Research from Gutenberg. Keep the source attached.", self.html)
        self.assertIn("Research one SEO or GEO question without leaving Gutenberg", self.html)

    def test_download_and_source_links_are_exact_and_no_fake_distribution_claims(self) -> None:
        hrefs = {attrs.get("href") for tag, attrs in self.parser.tags if tag == "a"}
        self.assertIn("/downloads/base2026-evidence-sidebar-v0.1.0.zip", hrefs)
        self.assertIn("/tools/evidence-search/", hrefs)
        self.assertIn("/privacy", hrefs)
        self.assertIn("/source-policy", hrefs)
        self.assertIn("/api", hrefs)
        self.assertIn(
            "https://github.com/offflinerpsy/base2026/tree/main/plugins/wordpress/base2026-evidence-sidebar",
            hrefs,
        )
        self.assertNotRegex(self.html, r"(?i)wordpress\.org")
        self.assertNotRegex(self.html, r"(?i)\b(?:download|traffic)\s+(?:count|counts|numbers|results|stats)\b")
        self.assertNotIn("PUBLISHED_VERIFIED", self.html)

    def test_beta_contract_and_human_owned_flow_are_explicit(self) -> None:
        required_copy = (
            "Free WordPress beta · 0.1.0",
            "Manual ZIP install.",
            "WordPress 6.5+",
            "PHP 7.4+",
            "GPL-2.0-or-later",
            "No signup, API key or paid AI service is required.",
            "The text goes to Search only when you choose Search",
            "read-only public lookup",
            "nothing is autosent from a post",
            "optionally insert an attributed, editable research note",
            "optional Base2026 link is opt-in rather than forced",
            "not a guaranteed direct quotation and not a fact check",
        )
        for phrase in required_copy:
            self.assertIn(phrase, self.html)

        self.assertIn("Install the ZIP", self.html)
        self.assertIn("Activate it", self.html)
        self.assertIn("Open Base2026 Evidence", self.html)
        self.assertGreaterEqual(len(re.findall("internal linking", self.html, flags=re.IGNORECASE)), 3)
        self.assertIn("This is a product flow example, not a Base2026 result.", self.html)
        self.assertIn("Illustrative preview · search results depend on your question.", self.html)
        self.assertIn("Example structure · review and edit your note before publishing.", self.html)

    def test_schema_is_truthful_software_application_and_breadcrumb(self) -> None:
        schemas = [json.loads(script) for script in self.parser.scripts if script.startswith("{")]
        software = next(schema for schema in schemas if schema.get("@type") == "SoftwareApplication")
        breadcrumb = next(schema for schema in schemas if schema.get("@type") == "BreadcrumbList")
        self.assertEqual(software["softwareVersion"], "0.1.0")
        self.assertEqual(software["operatingSystem"], "WordPress 6.5+")
        self.assertEqual(software["softwareRequirements"], "PHP 7.4+")
        self.assertTrue(software["isAccessibleForFree"])
        self.assertEqual(software["downloadUrl"], "https://base2026.dev/downloads/base2026-evidence-sidebar-v0.1.0.zip")
        self.assertEqual(software["license"], "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html")
        self.assertEqual(software["offers"]["price"], "0")
        self.assertEqual(len(breadcrumb["itemListElement"]), 3)
        self.assertEqual(
            breadcrumb["itemListElement"][-1]["item"],
            "https://base2026.dev/tools/wordpress-evidence-sidebar/",
        )
        self.assertNotIn("WordPress.org", json.dumps(software))

    def test_no_js_markup_and_scoped_visual_rules_are_present(self) -> None:
        # This landing page has no runtime script; the visible flow is useful
        # before any JavaScript or ZIP download is wired by the builder.
        self.assertNotRegex(self.html, r"<script\s+src=")
        self.assertIn("b26-wordpress-sidebar", self.html)
        self.assertIn("b26-wordpress-sidebar", self.css)
        self.assertIn("b26-tools-card--wordpress", self.studio)
        self.assertIn('href="/tools/wordpress-evidence-sidebar/"', self.studio)
        self.assertNotIn("fetch(", self.html)
        self.assertNotIn("Math.random", self.html)


if __name__ == "__main__":
    unittest.main()
