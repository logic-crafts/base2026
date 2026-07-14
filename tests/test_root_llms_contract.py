import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_LLMS = ROOT / "web" / "static" / "llms-root.txt"
CONTACT_ENTRY = "- Contact: https://aggressorbulkit.online/contact/"


class RootLlmsContractTests(unittest.TestCase):
    def test_contact_page_is_listed_exactly_once(self):
        text = ROOT_LLMS.read_text(encoding="utf-8")

        self.assertEqual(text.count(CONTACT_ENTRY), 1)
        self.assertLess(text.index("- About:"), text.index(CONTACT_ENTRY))
        self.assertLess(text.index(CONTACT_ENTRY), text.index("- Base2026 knowledge library:"))


if __name__ == "__main__":
    unittest.main()
