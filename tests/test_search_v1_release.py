from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_derivation_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "derive-base2026-search-v1-release.py"
    spec = importlib.util.spec_from_file_location("derive_base2026_search_v1_release", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_search_alias_preserves_query_and_fragment_without_meta_refresh_race() -> None:
    derivation = load_derivation_module()
    html = derivation.search_alias_html()

    assert '<meta name="robots" content="noindex,follow">' in html
    assert '<link rel="canonical" href="https://aggressorbulkit.online/knowledge/">' in html
    assert "location.replace('/knowledge/' + location.search + location.hash);" in html
    assert "http-equiv=\"refresh\"" not in html
    assert derivation.deterministic_release_timestamp(
        "base2026-search-v1-derived-20260713-231500"
    ) == "2026-07-13T23:15:00+00:00"


def test_canonical_search_runtime_and_generated_links_use_query_string_routes() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = (root / "web" / "static" / "meili.js").read_text(encoding="utf-8")
    assert 'return `./${query ? `?${query}` : ""}`;' in runtime
    assert 'const retainedHash = window.location.hash || "";' in runtime
    assert 'const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}${retainedHash}`;' in runtime
    assert 'const legacySearchPrefix = "#search?";' in runtime
    assert 'if (!hash.startsWith(legacySearchPrefix)) return false;' in runtime
    assert 'window.history.replaceState({}, "", nextUrl);' in runtime
    assert "function initialUiStateFromKnowledgeRoute(route = {})" in runtime
    assert "initialUiState: initialUiStateFromKnowledgeRoute(initialKnowledgeRoute)" in runtime
    assert "function safeHtmlFragment(html)" in runtime
    assert "function replaceSafeHtml(target, html)" in runtime
    assert "window.DOMPurify.sanitize" in runtime
    assert "new DOMParser" not in runtime
    assert ".innerHTML =" not in runtime
    assert 'button.append(document.createTextNode(term));' in runtime
    assert 'dismiss.textContent = "×";' in runtime
    assert "selectedTerms.replaceChildren(...buttons);" in runtime
    assert "replaceSafeHtml(\n    selectedTerms" not in runtime
    assert "replaceSafeHtml(sourceDetailPanel, renderSourceDetailShell" in runtime
    assert 'onerror="this.closest' not in runtime

    scripts_dir = root / "scripts"
    generator_path = scripts_dir / "generate-base2026-search-v1.py"
    spec = importlib.util.spec_from_file_location("generate_base2026_search_v1", generator_path)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(scripts_dir))
    try:
        spec.loader.exec_module(generator)
    finally:
        sys.path.remove(str(scripts_dir))
    source = (root / "web" / "static" / "index.html").read_text(encoding="utf-8")
    transformed = generator.transform(source)
    assert './#search?' not in transformed
    assert './?q=AI%20Overviews' in transformed
    assert transformed.index("purify.min.js") < transformed.index("meili.js")


def test_public_packager_uses_declared_build_root_for_search_overlay() -> None:
    root = Path(__file__).resolve().parents[1]
    packager = (root / "scripts" / "package-public-release.ps1").read_text(encoding="utf-8")

    assert '$BuildRoot = Join-Path $Root "output\\release-build\\$ReleaseName"' in packager
    assert '$SearchV1OverlayRoot = Join-Path $BuildRoot "_base2026-search-v1-overlay"' in packager
    assert "$StagingRoot" not in packager
    assert 'http-equiv="refresh"' not in packager