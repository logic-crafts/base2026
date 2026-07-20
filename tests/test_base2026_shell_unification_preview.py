from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from alex_v4_static_shell import footer_html, header_html as global_header_html  # noqa: E402


SPEC = importlib.util.spec_from_file_location(
    "base2026_shell_unification_preview", SCRIPTS / "build-base2026-shell-unification-preview.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def index_markup() -> str:
    return """<!doctype html><html><head><meta name=\"robots\" content=\"index,follow\" /><link rel=\"canonical\" href=\"https://aggressorbulkit.online/knowledge/\" /><link rel=\"stylesheet\" href=\"./static/base2026/tokens.css?v=old\" data-b26-asset=\"tokens.css\" /><link rel=\"stylesheet\" href=\"./static/base2026/shell.css?v=old\" /></head><body><header class=\"site-header\"><a href=\"/knowledge/\">Old header</a></header><main><nav aria-label=\"Breadcrumb\">Base2026 / Search</nav><section data-research-bridge=\"library_to_apply_research\">Bridge</section></main><footer class=\"site-footer\">Old footer</footer></body></html>"""


def redirect_markup() -> str:
    return """<!doctype html><html><head><meta name=\"robots\" content=\"noindex,follow\" /><meta http-equiv=\"refresh\" content=\"0;url=/knowledge/\" /></head><body>Redirecting</body></html>"""


def test_preview_consolidates_shells_and_preserves_body_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text(index_markup(), encoding="utf-8")
    (source / "search.html").write_text(redirect_markup(), encoding="utf-8")
    (source / "static" / "base2026").mkdir(parents=True)
    for asset in ("tokens.css", "shell.css", "components.css"):
        (source / "static" / "base2026" / asset).write_text("/* fixture */", encoding="utf-8")

    output = tmp_path / "preview"
    receipt = MODULE.build_preview(source, output)

    index = BeautifulSoup((output / "index.html").read_text(encoding="utf-8"), "html.parser")
    assert str(index.select_one("header")).strip() == str(BeautifulSoup(global_header_html(), "html.parser").header).strip()
    assert index.select_one("[data-b26-context-nav]")
    assert not index.select_one(".b26-product-header")
    assert str(index.select_one("footer")).strip() == str(BeautifulSoup(footer_html(), "html.parser").footer).strip()
    assert index.select_one('meta[name="robots"]')['content'] == "index,follow"
    assert index.select_one('link[rel="canonical"]')['href'] == "https://aggressorbulkit.online/knowledge/"
    assert index.select_one('[data-research-bridge="library_to_apply_research"]')
    assert index.select_one('link[data-b26-asset="context-nav.css"]')
    base_assets = index.select('link[data-b26-asset]')
    assert [node["data-b26-asset"] for node in base_assets] == [
        "tokens.css", "shell.css", "components.css", "context-nav.css"
    ]
    assert all(node["href"].endswith("?v=1.1.5") for node in base_assets)
    assert not index.select_one('link[href*="base2026/shell.css?v=old"]')
    for asset in ("tokens.css", "shell.css", "components.css", "context-nav.css"):
        assert (output / "static/base2026" / asset).read_text(encoding="utf-8") == (
            ROOT / "web/static/base2026" / asset
        ).read_text(encoding="utf-8")

    redirect = (output / "search.html").read_text(encoding="utf-8")
    assert "data-ay-v2-header" not in redirect
    assert "data-footer-contract" not in redirect
    assert receipt["rendered_routes"] == ["index.html"]
    assert receipt["redirect_shells_preserved"] == ["search.html"]
    persisted = json.loads((output / "shell-unification-preview.json").read_text(encoding="utf-8"))
    assert persisted == receipt
