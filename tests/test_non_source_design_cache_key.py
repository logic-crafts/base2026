from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import alex_design_system_v2  # noqa: E402
import alex_v4_static_shell  # noqa: E402


R4_VERSION = "20260718-visual-reset-v2-r4"
QUERY_RE = re.compile(rb"(alex-design-system-v2\.css\?v=)[^\"'&<>\s]+")


def load_hyphenated(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assigned_string(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    assert isinstance(node.value, ast.Constant)
                    assert isinstance(node.value.value, str)
                    return node.value.value
    raise AssertionError(f"{name} not found in {path}")


def test_all_non_source_generators_share_one_r4_design_version() -> None:
    ai_pages = load_hyphenated(
        "generate_ai_visibility_pages_cache_key", "generate-ai-visibility-pages.py"
    )
    public_pages = load_hyphenated(
        "generate_public_pages_cache_key", "generate-public-pages.py"
    )

    assert alex_design_system_v2.NON_SOURCE_DESIGN_VERSION == R4_VERSION
    assert alex_design_system_v2.VERSION == R4_VERSION
    assert alex_v4_static_shell.SHELL_VERSION == R4_VERSION
    assert ai_pages.STYLE_VERSION == R4_VERSION
    assert public_pages.STYLE_VERSION == R4_VERSION
    assert ai_pages.DESIGN_SYSTEM_HREF.endswith(f"?v={R4_VERSION}")


def test_source_renderer_version_remains_a_separate_unchanged_contract() -> None:
    source_renderer = assigned_string(
        SCRIPTS / "build-source-detail-v2-full-candidate.py", "RENDERER_VERSION"
    )
    assert source_renderer == "source-detail-v2-visual-reset-v2-20260718"
    assert source_renderer != R4_VERSION


def test_overlay_changes_only_non_source_stylesheet_queries_and_is_idempotent(
    tmp_path: Path,
) -> None:
    overlay = load_hyphenated(
        "apply_non_source_design_cache_key", "apply-non-source-design-cache-key.py"
    )
    web = tmp_path / "web"
    fixtures = {
        "index.html": b"<html><head></head><body>Search</body></html>",
        "search/index.html": b"<html><head></head><body>Search</body></html>",
        "search.html": b"<html><head></head><body>Search</body></html>",
        "topics/example.html": b'<link href="../static/alex-design-system-v2.css?v=old-topic"><main>Topic</main>',
        "creators/example.html": b'<link href="../static/alex-design-system-v2.css?v=old-shell"><main>Creator</main>',
        "sources/example.html": b'<link href="../static/alex-design-system-v2.css?v=source-detail-v2-visual-reset-v2-20260718"><main>Source</main>',
    }
    for relative, payload in fixtures.items():
        target = web / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    before = {relative: (web / relative).read_bytes() for relative in fixtures}

    report = overlay.apply_overlay(
        web,
        expected_html=6,
        expected_consumers=2,
        expected_source_consumers=1,
    )
    assert report["updated"] == 2
    assert report["source_rewritten"] is False
    assert report["query_only"] is True

    after = {relative: (web / relative).read_bytes() for relative in fixtures}
    for relative in fixtures:
        if relative.startswith("sources/") or relative in overlay.NO_DESIGN_SYSTEM_ALLOWLIST:
            assert after[relative] == before[relative]
        else:
            assert after[relative] != before[relative]
            assert QUERY_RE.sub(rb"\1VERSION", after[relative]) == QUERY_RE.sub(
                rb"\1VERSION", before[relative]
            )
            assert f"?v={R4_VERSION}".encode() in after[relative]

    check = overlay.apply_overlay(
        web,
        expected_html=6,
        expected_consumers=2,
        expected_source_consumers=1,
        check_only=True,
    )
    assert check["pending"] == 0
    assert check["updated"] == 0


@pytest.fixture
def r4_web_root() -> Path:
    raw = os.environ.get("BASE2026_R4_WEB_ROOT", "").strip()
    if not raw:
        pytest.skip("set BASE2026_R4_WEB_ROOT for immutable-corpus cache-key QA")
    root = Path(raw).resolve()
    assert (root / "index.html").is_file()
    return root


def test_immutable_r4_corpus_has_one_non_source_key_and_separate_source_contract(
    r4_web_root: Path,
) -> None:
    overlay = load_hyphenated(
        "apply_non_source_design_cache_key_corpus",
        "apply-non-source-design-cache-key.py",
    )
    report = overlay.apply_overlay(
        r4_web_root,
        expected_html=4124,
        expected_consumers=2428,
        expected_source_consumers=1693,
        check_only=True,
    )

    assert report["before_versions"] == {R4_VERSION: 2428}
    assert report["source_versions"] == {
        "20260718-visual-reset-v2": 1,
        "source-detail-v2-visual-reset-v2-20260718": 1692,
    }
    assert report["pending"] == 0
    assert report["source_rewritten"] is False
