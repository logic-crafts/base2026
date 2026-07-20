from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-global-footer-release.py"
FOOTER = '<footer class="ay-site-footer" data-footer-contract="personal-v1">global</footer>'


def load_module():
    spec = importlib.util.spec_from_file_location("sync_global_footer_release", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_replaces_every_unique_footer_without_touching_content(tmp_path: Path) -> None:
    module = load_module()
    web = tmp_path / "web"
    (web / "nested").mkdir(parents=True)
    first = web / "index.html"
    second = web / "nested" / "source.html"
    first.write_text('<main>Search</main><footer class="old">old</footer>', encoding="utf-8")
    second.write_text('<main>Evidence</main><footer class="old">old</footer>', encoding="utf-8")

    result = module.sync(web, FOOTER)

    assert result == {"pages": 2, "changed": 2, "invalid": 0}
    assert first.read_text(encoding="utf-8") == '<main>Search</main>' + FOOTER
    assert second.read_text(encoding="utf-8") == '<main>Evidence</main>' + FOOTER


def test_sync_is_an_atomic_stop_gate_for_missing_or_duplicate_footers(tmp_path: Path) -> None:
    module = load_module()
    web = tmp_path / "web"
    web.mkdir()
    valid = web / "valid.html"
    invalid = web / "invalid.html"
    valid.write_text('<main>Keep</main><footer>old</footer>', encoding="utf-8")
    invalid.write_text('<main>Missing footer</main>', encoding="utf-8")
    before = valid.read_text(encoding="utf-8")

    try:
        module.sync(web, FOOTER)
    except ValueError as error:
        assert "invalid.html (0 footers)" in str(error)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("missing footer must block the entire release")

    assert valid.read_text(encoding="utf-8") == before


def test_sync_preserves_legacy_non_utf8_document_bytes(tmp_path: Path) -> None:
    module = load_module()
    web = tmp_path / "web"
    web.mkdir()
    page = web / "legacy.html"
    page.write_bytes(b'<main>\xa3 historical byte</main><footer class="old">old</footer>')

    result = module.sync(web, FOOTER)

    assert result == {"pages": 1, "changed": 1, "invalid": 0}
    assert b"\xa3 historical byte" in page.read_bytes()
    assert FOOTER.encode("utf-8") in page.read_bytes()
