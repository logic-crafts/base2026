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


def test_sitemap_result_reuses_exact_body_and_fails_closed_for_noindex() -> None:
    exact = {
        "route": "solutions/index.html",
        "status": 200,
        "bytes": 42,
        "actual_sha256": "a" * 64,
        "expected_sha256": "a" * 64,
        "x_robots_blocks_indexing": True,
        "failures": [],
    }

    reused = MODULE.sitemap_result_from_exact("solutions/", exact)

    assert reused["route"] == "solutions/"
    assert reused["status"] == 200
    assert reused["actual_sha256"] == reused["expected_sha256"]
    assert reused["x_robots_blocks_indexing"] is True
    assert reused["failures"] == ["x_robots_tag_blocks_indexing"]


def test_sitemap_result_preserves_exact_route_failures() -> None:
    exact = {
        "route": "sources/example.html",
        "status": 0,
        "bytes": 0,
        "actual_sha256": "",
        "expected_sha256": "b" * 64,
        "x_robots_blocks_indexing": False,
        "failures": ["status=0, expected=200"],
    }

    reused = MODULE.sitemap_result_from_exact("sources/example.html", exact)

    assert reused["failures"] == ["status=0, expected=200"]


def test_sitemap_reuse_preserves_directory_url_identity() -> None:
    exact_by_route = {
        "index.html": {"route": "index.html"},
        "sources/index.html": {"route": "sources/index.html"},
        "sources/example.html": {"route": "sources/example.html"},
    }

    assert MODULE.reusable_exact_result("", exact_by_route) is None
    assert MODULE.reusable_exact_result("sources/", exact_by_route) is None
    assert MODULE.reusable_exact_result("sources/example.html", exact_by_route) == {
        "route": "sources/example.html"
    }
