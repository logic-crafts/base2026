from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check-public-content-readiness.py"
SPEC = importlib.util.spec_from_file_location("check_public_content_readiness", MODULE_PATH)
assert SPEC and SPEC.loader
readiness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(readiness)


class PublicContentReadinessTests(unittest.TestCase):
    def test_generated_noindex_source_is_safe_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sources" / "tiktok-video-123.html"
            target.parent.mkdir(parents=True)
            target.write_text('<meta name="robots" content="noindex,follow" />', encoding="utf-8")
            self.assertTrue(readiness.generated_source_is_noindex({"item_id": "tiktok-video-123"}, root))

    def test_indexable_or_missing_source_is_not_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sources" / "tiktok-video-123.html"
            target.parent.mkdir(parents=True)
            target.write_text('<meta name="robots" content="index,follow" />', encoding="utf-8")
            self.assertFalse(readiness.generated_source_is_noindex({"item_id": "tiktok-video-123"}, root))
            self.assertFalse(readiness.generated_source_is_noindex({"item_id": "tiktok-video-404"}, root))


if __name__ == "__main__":
    unittest.main()
