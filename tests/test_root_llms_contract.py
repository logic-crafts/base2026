import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_LLMS = ROOT / "web" / "static" / "llms-root.txt"
MCP_ENTRY = "- MCP for AI agents: https://base2026.dev/mcp"
INTEGRATIONS_ENTRY = "- Plugins and integrations: https://base2026.dev/integrations"


class RootLlmsContractTests(unittest.TestCase):
    def test_public_developer_routes_are_listed_without_personal_site_handoff(self):
        text = ROOT_LLMS.read_text(encoding="utf-8")

        self.assertEqual(text.count(MCP_ENTRY), 1)
        self.assertEqual(text.count(INTEGRATIONS_ENTRY), 1)
        self.assertIn("https://base2026.dev/api/mcp", text)
        self.assertNotIn("aggressorbulkit.online", text)
        self.assertNotIn("/services/", text)
        self.assertNotIn("/pricing/", text)


if __name__ == "__main__":
    unittest.main()
