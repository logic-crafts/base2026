from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply-alex-design-system-v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_alex_design_system_v2_scope", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_route_allowlist_changes_only_requested_document(tmp_path: Path) -> None:
    module = load_module()
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<main><h1>Search</h1></main>", encoding="utf-8")
    document = web / "methodology.html"
    untouched = web / "unrelated.html"
    document.write_text(
        '<main class="doc-page"><section class="page-hero"><h1>Method</h1><div class="hero-actions"></div></section><section><h2>Body</h2></section></main>',
        encoding="utf-8",
    )
    untouched.write_text("<main><h1>Unrelated</h1></main>", encoding="utf-8")
    before = untouched.read_bytes()

    result = module.apply_to_web_root(web, routes={"methodology.html"})

    assert result == {"scanned": 1, "changed": 1, "search_root_changed": 0}
    assert b"b26-k-document-body" in document.read_bytes()
    assert untouched.read_bytes() == before


def test_legacy_shell_upgrade_replaces_only_shell_contract(tmp_path: Path) -> None:
    module = load_module()
    legacy = """<!doctype html><html><head>
    <link rel="stylesheet" href="./static/styles.css?v=legacy">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">
    </head><body class="old"><header class="site-header">old nav</header>
    <main class="app-shell"><h1>Analytics</h1><section>Reviewed data stays here.</section></main>
    <footer class="site-footer">old footer</footer></body></html>"""

    rendered = module.apply_global_footer(module.apply_v2_shell(legacy, "analytics.html"))

    assert "static/styles.css" not in rendered
    assert "fonts.googleapis.com" not in rendered
    assert rendered.count('data-alex-design-system="v2"') == 1
    assert rendered.count('data-b26-asset="') == 3
    assert rendered.count("data-b26-product-header") == 1
    assert rendered.count('data-footer-contract="personal-v1"') == 1
    assert 'data-b26-visual-root="v2"' in rendered
    assert 'data-b26-family="analytics"' in rendered
    assert "Reviewed data stays here." in rendered
