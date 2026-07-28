from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "normalize_wordpress_v4_shell_release",
    ROOT / "scripts" / "normalize-wordpress-v4-shell-release.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_normalizer_removes_legacy_shell_interaction_script(tmp_path: Path, monkeypatch) -> None:
    release_root = tmp_path / "release"
    web_root = release_root / "web"
    web_root.mkdir(parents=True)
    page = web_root / "index.html"
    page.write_text(
        """<!doctype html>
<html><head><title>Fixture</title><link rel="canonical" href="https://example.test/"><meta name="robots" content="noindex"></head>
<body class="legacy"><header class="site-header"><span>Old header</span></header>
<main><h1>Preserved body</h1></main><footer class="site-footer">Old footer</footer>
<script src="./static/alex-v4-static-shell.js?v=fixture"></script></body></html>
""",
        encoding="utf-8",
    )
    report = release_root / "shell-report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "normalize-wordpress-v4-shell-release.py",
            "--release-root",
            str(release_root),
            "--expected-pages",
            "1",
            "--asset-version",
            "fixture",
            "--report",
            str(report),
        ],
    )

    assert MODULE.main() == 0
    normalized = page.read_text(encoding="utf-8")
    assert "alex-v4-static-shell.js" not in normalized
    assert normalized.count("wordpress-v4-header.js") == 1
    assert "<h1>Preserved body</h1>" in normalized


def test_canonical_header_asset_bridges_the_hover_offset() -> None:
    header_css = (ROOT / "scripts" / "wordpress-v4-header.css").read_text(encoding="utf-8")

    assert ".ay-v2-has-mega::after" in header_css
    assert "top:100%;" in header_css
    assert "height:20px;" in header_css
