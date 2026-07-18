from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate-base2026-sitemap.py"
SPEC = importlib.util.spec_from_file_location("generate_base2026_sitemap", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BASE = "https://aggressorbulkit.online/knowledge"
STATIC_CONTRACT = Path(__file__).parents[1] / "contracts" / "base2026-sitemap-static-routes.json"


def write_html(path: Path, head: str, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<!doctype html><html><head>{head}</head><body>{body}</body></html>\n", encoding="utf-8")


def head(route: str, robots: str = "index,follow", canonical: str | None = None) -> str:
    canonical = canonical or f"{BASE}/{route}"
    return f'<meta content="{robots}" name="robots"><link href="{canonical}" rel="canonical">'


def candidate_manifest(path: Path, rendered: list[dict], future: list[str]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": MODULE.SOURCE_CANDIDATE_SCHEMA,
                "rendered": rendered,
                "future_private_not_emitted": future,
            }
        ),
        encoding="utf-8",
    )
    return path


def run_main(
    monkeypatch: pytest.MonkeyPatch, *args: str, static_routes: list[str] | None = None
) -> int:
    arg_list = list(args)
    web_root = Path(arg_list[arg_list.index("--web-root") + 1])
    if static_routes is None:
        static_routes = sorted(
            path.relative_to(web_root).as_posix()
            for path in web_root.rglob("*.html")
            if not path.relative_to(web_root).as_posix().startswith("sources/tiktok-video-")
            and not path.name.startswith("roadmap-dataviz-test")
        )
    static_manifest = web_root.parent / "static-admission.json"
    static_manifest.write_text(
        json.dumps(
            {
                "schema": MODULE.STATIC_ADMISSION_SCHEMA,
                "base_url": BASE,
                "source_release": "fixture",
                "source_release_zip_sha256": "0" * 64,
                "evidence": {"approved_static_routes": len(static_routes)},
                "routes": static_routes,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            *arg_list,
            "--static-admission-manifest",
            str(static_manifest),
            "--lastmod",
            "2026-07-17",
        ],
    )
    return MODULE.main()


def test_noindex_detection_is_attribute_order_independent(tmp_path: Path) -> None:
    first = tmp_path / "first.html"
    second = tmp_path / "second.html"
    write_html(first, '<meta name="robots" content="noindex,follow">')
    write_html(second, '<meta content="noindex follow" name="robots">')

    assert MODULE.is_indexable(first) is False
    assert MODULE.is_indexable(second) is False


def test_robots_none_is_not_indexable_and_body_metadata_is_ignored(tmp_path: Path) -> None:
    none = tmp_path / "none.html"
    body_only = tmp_path / "body-only.html"
    write_html(none, '<meta content="none" name="robots">')
    write_html(body_only, "", '<meta content="noindex" name="robots">')

    assert MODULE.is_indexable(none) is False
    assert MODULE.is_indexable(body_only) is True


def test_indexable_page_and_canonical_are_attribute_order_independent(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    write_html(
        page,
        '<meta content="index,follow" name="robots">'
        f'<link href="{BASE}/page.html" rel="canonical">',
    )

    assert MODULE.is_indexable(page) is True
    assert MODULE.canonical_url(page) == f"{BASE}/page.html"


def test_noindex_token_is_exact_not_substring(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    write_html(page, '<meta content="noindex-preview,follow" name="robots">')

    assert MODULE.is_indexable(page) is True


def test_source_manifest_includes_normal_and_excludes_archive_and_future(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    normal = "sources/tiktok-video-normal.html"
    archive = "sources/tiktok-video-archive.html"
    future = "sources/tiktok-video-future.html"
    write_html(web_root / normal, head(normal))
    write_html(web_root / archive, head(archive, robots="noindex,follow"))
    write_html(web_root / "methodology.html", head("methodology.html"))
    manifest = candidate_manifest(
        tmp_path / "candidate-manifest.json",
        [
            {"route": normal, "admission_state": MODULE.NORMAL_PUBLIC_CARD},
            {"route": archive, "admission_state": MODULE.PROVENANCE_ARCHIVE_NOINDEX},
        ],
        [future],
    )

    assert run_main(
        monkeypatch,
        "--web-root",
        str(web_root),
        "--source-detail-manifest",
        str(manifest),
        "--chunk-size",
        "10",
    ) == 0
    chunk = (web_root / "sitemaps" / "base2026-001.xml").read_text(encoding="utf-8")
    locations = set(re.findall(r"<loc>(.*?)</loc>", chunk))
    assert f"{BASE}/{normal}" in locations
    assert f"{BASE}/methodology.html" in locations
    assert f"{BASE}/{archive}" not in locations
    assert all("future.html" not in location for location in locations)


def test_source_manifest_fails_closed_if_future_route_is_emitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    future = "sources/tiktok-video-future.html"
    write_html(web_root / future, head(future, robots="noindex,follow"))
    manifest = candidate_manifest(tmp_path / "candidate-manifest.json", [], [future])

    with pytest.raises(SystemExit, match="future_private_emitted=1"):
        run_main(
            monkeypatch,
            "--web-root",
            str(web_root),
            "--source-detail-manifest",
            str(manifest),
        )


def test_public_source_records_are_an_exact_source_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    normal = "sources/tiktok-video-normal.html"
    archive = "sources/tiktok-video-archive.html"
    write_html(web_root / normal, head(normal))
    write_html(web_root / archive, head(archive, robots="noindex,follow"))
    records = tmp_path / "source_records.jsonl"
    records.write_text(
        "\n".join(
            [
                json.dumps({"item_id": "tiktok-video-normal", "admission_state": MODULE.NORMAL_PUBLIC_CARD}),
                json.dumps(
                    {"item_id": "tiktok-video-archive", "admission_state": MODULE.PROVENANCE_ARCHIVE_NOINDEX}
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert run_main(
        monkeypatch,
        "--web-root",
        str(web_root),
        "--source-records",
        str(records),
    ) == 0
    chunk = (web_root / "sitemaps" / "base2026-001.xml").read_text(encoding="utf-8")
    assert f"{BASE}/{normal}" in chunk
    assert f"{BASE}/{archive}" not in chunk


@pytest.mark.parametrize(
    "page_head",
    [
        '<meta content="index,follow" name="robots">',
        '<meta content="index,follow" name="robots"><link rel="canonical" href="https://example.com/wrong">',
        (
            '<meta content="index,follow" name="robots">'
            f'<link rel="canonical" href="{BASE}/page.html">'
            f'<link rel="canonical" href="{BASE}/page.html">'
        ),
    ],
)
def test_indexable_page_requires_exactly_one_self_canonical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, page_head: str
) -> None:
    web_root = tmp_path / "web"
    write_html(web_root / "page.html", page_head)

    with pytest.raises(SystemExit, match="metadata=1"):
        run_main(monkeypatch, "--web-root", str(web_root))


def test_archive_requires_noindex_even_though_it_is_excluded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    archive = "sources/tiktok-video-archive.html"
    write_html(web_root / archive, head(archive, robots="index,follow"))
    manifest = candidate_manifest(
        tmp_path / "candidate-manifest.json",
        [{"route": archive, "admission_state": MODULE.PROVENANCE_ARCHIVE_NOINDEX}],
        [],
    )

    with pytest.raises(SystemExit, match="archive_indexable=1"):
        run_main(
            monkeypatch,
            "--web-root",
            str(web_root),
            "--source-detail-manifest",
            str(manifest),
        )


def test_unapproved_indexable_static_route_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    write_html(web_root / "page.html", head("page.html"))

    with pytest.raises(SystemExit, match="unapproved_indexable=1"):
        run_main(monkeypatch, "--web-root", str(web_root), static_routes=[])


def test_missing_approved_static_route_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    web_root.mkdir()

    with pytest.raises(SystemExit, match="missing_static=1"):
        run_main(monkeypatch, "--web-root", str(web_root), static_routes=["missing.html"])


def test_check_only_rejects_an_archive_url_in_existing_sitemap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_root = tmp_path / "web"
    normal = "sources/tiktok-video-normal.html"
    archive = "sources/tiktok-video-archive.html"
    write_html(web_root / normal, head(normal))
    write_html(web_root / archive, head(archive, robots="noindex,follow"))
    manifest = candidate_manifest(
        tmp_path / "candidate-manifest.json",
        [
            {"route": normal, "admission_state": MODULE.NORMAL_PUBLIC_CARD},
            {"route": archive, "admission_state": MODULE.PROVENANCE_ARCHIVE_NOINDEX},
        ],
        [],
    )
    assert run_main(
        monkeypatch,
        "--web-root",
        str(web_root),
        "--source-detail-manifest",
        str(manifest),
    ) == 0
    chunk_path = web_root / "sitemaps" / "base2026-001.xml"
    chunk = chunk_path.read_text(encoding="utf-8").replace(
        "</urlset>", f"  <url><loc>{BASE}/{archive}</loc></url>\n</urlset>"
    )
    chunk_path.write_text(chunk, encoding="utf-8")

    with pytest.raises(SystemExit, match="unexpected=1"):
        run_main(
            monkeypatch,
            "--web-root",
            str(web_root),
            "--source-detail-manifest",
            str(manifest),
            "--check-only",
        )


def test_frozen_r6_static_admission_contract_is_exact_and_source_free() -> None:
    payload = json.loads(STATIC_CONTRACT.read_text(encoding="utf-8"))

    assert payload["schema"] == MODULE.STATIC_ADMISSION_SCHEMA
    assert payload["base_url"] == BASE
    assert len(payload["routes"]) == 241
    assert len(set(payload["routes"])) == 241
    assert payload["evidence"]["approved_static_routes"] == 241
    assert all(MODULE.safe_static_route(route) == route for route in payload["routes"])
