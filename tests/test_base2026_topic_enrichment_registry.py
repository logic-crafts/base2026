"""Bounded preservation checks for the retired orphan enrichment entry."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "base2026_topic_traffic_pages.json"


class TopicEnrichmentRegistryTests(unittest.TestCase):
    def test_orphan_is_not_an_active_enrichment(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertNotIn("content-strategy", config)
        self.assertEqual(len(config), 59)

    def test_retirement_preserves_every_other_entry(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        canonical = json.dumps(
            config, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        # Snapshot of the other entries before this one-key retirement.
        # Preserved bytes do not certify source support or indexability.
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            "284353b0554dbd652f1978cc70001d4297b1b58a827fe3e2568bc7fadb420f17",
        )

    def test_roadmap_separates_configuration_from_publication(self) -> None:
        roadmap = (ROOT / "web" / "static" / "roadmap.js").read_text(encoding="utf-8")
        self.assertIn("a configuration entry is not proof of a published or indexed page", roadmap)
        self.assertIn("Unresolved entries remain held", roadmap)
        self.assertNotIn("60 configured", roadmap)
        self.assertNotIn("102 proof links", roadmap)
        self.assertNotIn("22 impressions", roadmap)


if __name__ == "__main__":
    unittest.main()
