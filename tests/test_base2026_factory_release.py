from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-base2026-cloudflare-release.py"
SPEC = importlib.util.spec_from_file_location("build_base2026_cloudflare_release_factory", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def _write_legacy_plugin_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entry = zipfile.ZipInfo(
            "base2026-evidence-sidebar/readme.txt", (2026, 9, 5, 0, 0, 0)
        )
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        archive.writestr(
            entry,
            b"legacy fixture\n",
            compress_type=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        )
    payload = buffer.getvalue()
    legacy_path = root / builder.WORDPRESS_PLUGIN_LEGACY_DOWNLOAD
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_bytes(payload)
    monkeypatch.setattr(
        builder,
        "WORDPRESS_PLUGIN_LEGACY_DOWNLOAD_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )


def _write_source_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Write the smallest public artifact accepted by a startup build."""

    (root / "static").mkdir(parents=True)
    (root / "search").mkdir()
    (root / "index.html").write_text(
        "<!doctype html><html><head><link rel=\"canonical\" href=\"https://base2026.dev/\"></head>"
        "<body><main>Public home</main></body></html>",
        encoding="utf-8",
    )
    (root / "search" / "index.html").write_text(
        '<link rel="stylesheet" href="../static/site.css">', encoding="utf-8"
    )
    (root / "search.html").write_text(
        '<title>Base2026 Search</title><main class="app-shell">Search application</main>',
        encoding="utf-8",
    )
    (root / "sitemap.xml").write_text(
        '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "</sitemapindex>\n",
        encoding="utf-8",
    )
    (root / "static" / "site.css").write_text("body{color:#111}\n", encoding="utf-8")
    for name in ("documents.jsonl", "passages.jsonl", "topic_signal_briefs.jsonl"):
        (root / "static" / name).write_text("{}\n", encoding="utf-8")
    (root / "static" / "insight_cards.jsonl").write_text(
        json.dumps(
            {
                "id": "insight:factory-fixture",
                "public": True,
                "needs_review": False,
                "public_policy": "reviewed_insight",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "static" / "manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    "documents.jsonl",
                    "insight_cards.jsonl",
                    "passages.jsonl",
                    "topic_signal_briefs.jsonl",
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_legacy_plugin_fixture(root, monkeypatch)


def _copy_reviewed_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reviewed = tmp_path / "reviewed-factory"
    shutil.copytree(ROOT / "templates" / "assets" / "factory3d", reviewed)
    monkeypatch.setattr(builder, "FACTORY_RELEASE_ROOT", reviewed)
    monkeypatch.setattr(builder, "FACTORY_RELEASE_MANIFEST", reviewed / "factory-release.json")
    return reviewed


def test_startup_release_emits_exact_reviewed_factory_snapshot_and_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    _write_source_fixture(source, monkeypatch)
    retained = source / "factory" / "assets"
    retained.mkdir(parents=True)
    (retained / "stale-bundle.js").write_text("old retained bundle", encoding="utf-8")

    output = tmp_path / "release"
    receipt = builder.build_release(
        source,
        output,
        homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
        homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
    )

    manifest = json.loads(builder.FACTORY_RELEASE_MANIFEST.read_text(encoding="utf-8"))
    expected_paths = {f"factory/{entry['path']}" for entry in manifest["files"]}
    output_paths = {
        path.relative_to(output).as_posix()
        for path in (output / "factory").rglob("*")
        if path.is_file()
    }
    assert output_paths == expected_paths
    assert not (output / "factory/assets/stale-bundle.js").exists()
    assert "factory/assets/stale-bundle.js" in receipt["excluded_source_paths"]
    for entry in manifest["files"]:
        destination = output / "factory" / entry["path"]
        payload = destination.read_bytes()
        assert len(payload) == entry["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    index = (output / "factory/index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://base2026.dev/factory/" />' in index
    assert '<header class="factory-header">' in index
    assert "b26-site-header" not in index
    assert "{{STARTUP_HEADER}}" not in index
    assert receipt["verification"]["factory_release_file_count"] == 20
    assert (
        receipt["verification"]["factory_release_manifest_sha256"]
        == builder.FACTORY_RELEASE_MANIFEST_SHA256
    )
    assert receipt["verification"]["factory_release_verified"] is True


def test_factory_manifest_tampering_fails_before_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reviewed = _copy_reviewed_factory(tmp_path, monkeypatch)
    manifest_path = reviewed / "factory-release.json"
    manifest_path.write_bytes(manifest_path.read_bytes() + b"tampered\n")

    with pytest.raises(builder.ReleaseBuildError, match="manifest hash"):
        builder._load_reviewed_factory_release()


def test_factory_asset_tampering_fails_against_pinned_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reviewed = _copy_reviewed_factory(tmp_path, monkeypatch)
    asset = reviewed / "index.html"
    asset.write_bytes(asset.read_bytes() + b"tampered")

    with pytest.raises(builder.ReleaseBuildError, match="asset hash/bytes mismatch"):
        builder._load_reviewed_factory_release()


def test_factory_symlink_and_hidden_paths_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reviewed = _copy_reviewed_factory(tmp_path, monkeypatch)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (reviewed / "assets" / "link.txt").symlink_to(outside)

    with pytest.raises(builder.ReleaseBuildError, match="symlink"):
        builder._load_reviewed_factory_release()

    reviewed = _copy_reviewed_factory(tmp_path / "hidden", monkeypatch)
    (reviewed / ".private.txt").write_text("private", encoding="utf-8")
    with pytest.raises(builder.ReleaseBuildError, match="hidden path"):
        builder._load_reviewed_factory_release()


def test_factory_manifest_rejects_traversal_and_private_adapter_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reviewed = _copy_reviewed_factory(tmp_path / "traversal", monkeypatch)
    manifest = json.loads((reviewed / "factory-release.json").read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "../escape.js"
    (reviewed / "factory-release.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        builder,
        "FACTORY_RELEASE_MANIFEST_SHA256",
        hashlib.sha256((reviewed / "factory-release.json").read_bytes()).hexdigest(),
    )
    with pytest.raises(builder.ReleaseBuildError, match="unsafe"):
        builder._load_reviewed_factory_release()

    reviewed = _copy_reviewed_factory(tmp_path / "private", monkeypatch)
    index = reviewed / "index.html"
    index.write_bytes(index.read_bytes() + b"\nPRIVATE_FACTORY_ADAPTER\n")
    manifest = json.loads((reviewed / "factory-release.json").read_text(encoding="utf-8"))
    index_entry = next(item for item in manifest["files"] if item["path"] == "index.html")
    index_entry["bytes"] = index.stat().st_size
    index_entry["sha256"] = hashlib.sha256(index.read_bytes()).hexdigest()
    manifest_path = reviewed / "factory-release.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        builder,
        "FACTORY_RELEASE_MANIFEST_SHA256",
        hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    )
    with pytest.raises(builder.ReleaseBuildError, match="private marker"):
        builder._load_reviewed_factory_release()
