from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "source-detail-v2-contract-gate.py"
SPEC = importlib.util.spec_from_file_location("source_detail_v2_contract_gate", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sitemap_route_file_mapping() -> None:
    assert MODULE.sitemap_file_route("") == "index.html"
    assert MODULE.sitemap_file_route("solutions/") == "solutions/index.html"
    assert MODULE.sitemap_file_route("methodology.html") == "methodology.html"


def test_x_robots_tag_fails_closed_for_noindex_and_none() -> None:
    assert MODULE.x_robots_blocks_indexing(["index, follow"]) is False
    assert MODULE.x_robots_blocks_indexing(["all"]) is False
    assert MODULE.x_robots_blocks_indexing(["googlebot: noindex, follow"]) is True
    assert MODULE.x_robots_blocks_indexing(["none"]) is True
