"""Static contract tests for the public WordPress Evidence Sidebar landing page."""

from __future__ import annotations

import base64
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
LANDING_PATH = ROOT / "templates" / "base2026-wordpress-evidence-sidebar.html"
STUDIO_PATH = ROOT / "templates" / "base2026-tools-studio.html"
CSS_PATH = ROOT / "templates" / "base2026-tools-studio.css"
PLAYGROUND_DEMO_URL = "https://playground.wordpress.net/?storage=temp#eyIkc2NoZW1hIjoiaHR0cHM6Ly9wbGF5Z3JvdW5kLndvcmRwcmVzcy5uZXQvYmx1ZXByaW50LXNjaGVtYS5qc29uIiwibWV0YSI6eyJ0aXRsZSI6IkFkZCBvbmUgaW5zcGVjdGFibGUgc291cmNlIG5vdGUiLCJhdXRob3IiOiJiYXNlMjAyNiIsImRlc2NyaXB0aW9uIjoiRGlzcG9zYWJsZSBHdXRlbmJlcmcgcHJhY3RpY2Ugd2l0aCB0aGUgcmVsZWFzZWQgQmFzZTIwMjYgRXZpZGVuY2UgU2lkZWJhciBiZXRhLiBTeW50aGV0aWMgZHJhZnQgb25seS4gU2VhcmNoIGFuZCBpbnNlcnQgcmVxdWlyZSB5b3VyIGV4cGxpY2l0IGNsaWNrczsgcmVzZWFyY2gsIG5vdCBmYWN0LWNoZWNraW5nLiJ9LCJwcmVmZXJyZWRWZXJzaW9ucyI6eyJwaHAiOiI4LjMiLCJ3cCI6ImxhdGVzdCJ9LCJmZWF0dXJlcyI6eyJuZXR3b3JraW5nIjp0cnVlfSwibG9naW4iOnRydWUsImxhbmRpbmdQYWdlIjoiL3dwLWFkbWluL3Bvc3QucGhwP3Bvc3Q9MTIzJmFjdGlvbj1lZGl0Iiwic2l0ZU9wdGlvbnMiOnsiYmxvZ25hbWUiOiJTb3VyY2Ugbm90ZSBwcmFjdGljZSDigJQgc3ludGhldGljIGRlbW8iLCJibG9nX3B1YmxpYyI6IjAifSwic3RlcHMiOlt7InN0ZXAiOiJpbnN0YWxsUGx1Z2luIiwicGx1Z2luRGF0YSI6eyJyZXNvdXJjZSI6InVybCIsInVybCI6Imh0dHBzOi8vYmFzZTIwMjYuZGV2L2Rvd25sb2Fkcy9iYXNlMjAyNi1ldmlkZW5jZS1zaWRlYmFyLXYwLjEuMS56aXAifSwib3B0aW9ucyI6eyJhY3RpdmF0ZSI6dHJ1ZSwidGFyZ2V0Rm9sZGVyTmFtZSI6ImJhc2UyMDI2LWV2aWRlbmNlLXNpZGViYXIifSwicHJvZ3Jlc3MiOnsiY2FwdGlvbiI6Ikluc3RhbGwgdGhlIHJlbGVhc2VkIEV2aWRlbmNlIFNpZGViYXIgYmV0YSJ9fSx7InN0ZXAiOiJydW5QSFAiLCJjb2RlIjoiPD9waHBcbnJlcXVpcmUgJy93b3JkcHJlc3Mvd3AtbG9hZC5waHAnO1xuaWYgKGdldF9wb3N0KDEyMykpIHsgdGhyb3cgbmV3IEV4Y2VwdGlvbignRGVtbyBkcmFmdCBJRCBhbHJlYWR5IGV4aXN0czsgb3BlbiBhIGZyZXNoIFBsYXlncm91bmQuJyk7IH1cbiRjb250ZW50ID0gJzwhLS0gd3A6cGFyYWdyYXBoIC0tPjxwPjxzdHJvbmc+U3ludGhldGljIHByYWN0aWNlIGRyYWZ0Ljwvc3Ryb25nPiBUaGlzIGlzIG5vdCBhIGNsaWVudCBhcnRpY2xlIG9yIGEgcmVhbCBTRU8gcmVzdWx0LiBLZWVwIHByaXZhdGUgbWF0ZXJpYWwgb3V0IG9mIHRoaXMgdGVtcG9yYXJ5IGRlbW8uPC9wPjwhLS0gL3dwOnBhcmFncmFwaCAtLT48IS0tIHdwOnBhcmFncmFwaCAtLT48cD5EcmFmdCB0byByZWZyZXNoOiBhZGQgYSByZWxhdGVkIGludGVybmFsIGxpbmsgb25seSBhZnRlciBkZWNpZGluZyB3aGF0IHRoZSByZWFkZXIgY2FuIGRvIG5leHQuIFJlcGxhY2UgdGhpcyBwcmFjdGljZSBwYXJhZ3JhcGggd2l0aCB5b3VyIG93biB3b3JkaW5nIGlmIHVzZWZ1bC48L3A+PCEtLSAvd3A6cGFyYWdyYXBoIC0tPjwhLS0gd3A6cGFyYWdyYXBoIC0tPjxwPlByYWN0aWNlOiBvcGVuIEJhc2UyMDI2IEV2aWRlbmNlIGZyb20gdGhlIGVkaXRvciBPcHRpb25zIG1lbnUsIHNlYXJjaCBpbnRlcm5hbCBsaW5raW5nLCBvcGVuIGFuIG9yaWdpbmFsIHNvdXJjZSBhbmQganVkZ2UgaXRzIHJlbGV2YW5jZS4gT25seSB0aGVuIG9wdGlvbmFsbHkgaW5zZXJ0IGEgcmVzZWFyY2ggbm90ZS4gTGVhdmUgdGhlIG9wdGlvbmFsIEJhc2UyMDI2IGxpbmsgb2ZmLCBjaG9vc2UgU2F2ZSBkcmFmdCBhbmQgcmVsb2FkLiBEbyBub3QgcHVibGlzaC4gVGhlIHNvdXJjZSBzdGF0ZW1lbnQgaXMgbm90IGEgZmFjdCBjaGVjayBvciBhIHJhbmtpbmcgcHJvbWlzZS48L3A+PCEtLSAvd3A6cGFyYWdyYXBoIC0tPic7XG4kaWQgPSB3cF9pbnNlcnRfcG9zdChhcnJheSgnaW1wb3J0X2lkJz0+MTIzLCdwb3N0X3RpdGxlJz0+J1ByYWN0aWNlIHJlZnJlc2g6IG9uZSB1c2VmdWwgaW50ZXJuYWwgbGluaycsJ3Bvc3RfY29udGVudCc9PiRjb250ZW50LCdwb3N0X3N0YXR1cyc9PidkcmFmdCcsJ3Bvc3RfdHlwZSc9Pidwb3N0JywncG9zdF9hdXRob3InPT4xKSx0cnVlKTtcbmlmIChpc193cF9lcnJvcigkaWQpIHx8ICRpZCAhPT0gMTIzKSB7IHRocm93IG5ldyBFeGNlcHRpb24oJ0NvdWxkIG5vdCBjcmVhdGUgdGhlIHN5bnRoZXRpYyBkcmFmdC4nKTsgfVxuIn1dfQ=="


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
        self.assertIn('/static/base2026-tools-studio.css?v=20260905-tools-media-v2', self.html)
        self.assertIn("Research from Gutenberg. Keep the source attached.", self.html)
        self.assertIn("Research one SEO or GEO question without leaving Gutenberg", self.html)

    def test_download_and_source_links_are_exact_and_no_fake_distribution_claims(self) -> None:
        hrefs = {attrs.get("href") for tag, attrs in self.parser.tags if tag == "a"}
        self.assertIn("/downloads/base2026-evidence-sidebar-v0.1.1.zip", hrefs)
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
            "Free WordPress beta · 0.1.1",
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

    def test_playground_demo_cta_is_explicit_and_disclosed(self) -> None:
        demo_links = [
            attrs for tag, attrs in self.parser.tags
            if tag == "a" and attrs.get("href") == PLAYGROUND_DEMO_URL
        ]
        self.assertEqual(len(PLAYGROUND_DEMO_URL), 2883)
        self.assertTrue(PLAYGROUND_DEMO_URL.startswith("https://playground.wordpress.net/?storage=temp#"))
        self.assertEqual(len(demo_links), 1)
        demo = demo_links[0]
        self.assertEqual(demo.get("target"), "_blank")
        self.assertEqual(demo.get("rel"), "noopener noreferrer")
        self.assertEqual(demo.get("aria-describedby"), "wordpress-demo-disclosure")
        blueprint = json.loads(base64.b64decode(urlsplit(PLAYGROUND_DEMO_URL).fragment))
        install_step = next(step for step in blueprint["steps"] if step["step"] == "installPlugin")
        self.assertEqual(
            install_step["pluginData"]["url"],
            "https://base2026.dev/downloads/base2026-evidence-sidebar-v0.1.1.zip",
        )
        self.assertEqual(blueprint["preferredVersions"], {"php": "8.3", "wp": "latest"})
        self.assertEqual(blueprint["features"], {"networking": True})
        for phrase in (
            "Disposable temporary WordPress.",
            "opens only when you click",
            "discarded on close",
            "does not auto-search, insert research or publish",
            "official Playground CORS proxy",
            "Supply no private material.",
            "Attribution is not a fact check.",
        ):
            self.assertIn(phrase, self.html)

    def test_schema_is_truthful_software_application_and_breadcrumb(self) -> None:
        schemas = [json.loads(script) for script in self.parser.scripts if script.startswith("{")]
        software = next(schema for schema in schemas if schema.get("@type") == "SoftwareApplication")
        breadcrumb = next(schema for schema in schemas if schema.get("@type") == "BreadcrumbList")
        self.assertEqual(software["softwareVersion"], "0.1.1")
        self.assertEqual(software["operatingSystem"], "WordPress 6.5+")
        self.assertEqual(software["softwareRequirements"], "PHP 7.4+")
        self.assertTrue(software["isAccessibleForFree"])
        self.assertEqual(software["downloadUrl"], "https://base2026.dev/downloads/base2026-evidence-sidebar-v0.1.1.zip")
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
