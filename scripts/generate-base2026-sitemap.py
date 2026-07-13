from __future__ import annotations

import argparse
import html
import json
import math
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


class HeadMetadataParser(HTMLParser):
    """Extract canonical and robots metadata regardless of attribute order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical: str | None = None
        self.robots: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): (value or "") for name, value in attrs}
        if tag.lower() == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", ""))
        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = self.canonical or values.get("href") or None


def head_metadata(path: Path) -> HeadMetadataParser:
    parser = HeadMetadataParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser


def is_indexable(path: Path) -> bool:
    metadata = head_metadata(path)
    directives = {
        directive.strip().lower()
        for content in metadata.robots
        for directive in content.split(",")
    }
    return "noindex" not in directives


def canonical_url(path: Path) -> str | None:
    canonical = head_metadata(path).canonical
    return html.unescape(canonical) if canonical else None


def url_for(web_root: Path, path: Path, base_url: str) -> str:
    rel = path.relative_to(web_root).as_posix()
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return f"{base_url.rstrip('/')}/{rel}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Base2026 sitemap from indexable public HTML files.")
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--base-url", default="https://aggressorbulkit.online/knowledge")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument(
        "--source-detail-manifest",
        type=Path,
        help="Optional immutable Source Detail V2 manifest. Archive/noindex routes are required and future/private routes are forbidden.",
    )
    args = parser.parse_args()

    web_root = args.web_root.resolve()
    out = args.out or (web_root / "sitemap.xml")
    chunk_size = max(1, args.chunk_size)
    required_archive_routes: set[str] = set()
    forbidden_future_routes: set[str] = set()
    if args.source_detail_manifest:
        manifest = json.loads(args.source_detail_manifest.resolve().read_text(encoding="utf-8"))
        required_archive_routes = {
            item["route"]
            for item in manifest["rendered"]
            if item["admission_state"] == "provenance_archive_noindex"
        }
        forbidden_future_routes = set(manifest["future_private_not_emitted"])

    html_paths = sorted(web_root.rglob("*.html"))
    emitted_routes = {path.relative_to(web_root).as_posix() for path in html_paths}
    missing_archives = sorted(required_archive_routes - emitted_routes)
    emitted_future = sorted(forbidden_future_routes & emitted_routes)
    if missing_archives or emitted_future:
        raise SystemExit(
            "Source Detail sitemap contract failed: "
            f"missing_archive={len(missing_archives)}, future_private_emitted={len(emitted_future)}"
        )

    urls = []
    for path in html_paths:
        route = path.relative_to(web_root).as_posix()
        if route in forbidden_future_routes or path.name.startswith("roadmap-dataviz-test"):
            continue
        if not is_indexable(path) and route not in required_archive_routes:
            continue
        url = url_for(web_root, path, args.base_url)
        canonical = canonical_url(path)
        if canonical and canonical.rstrip("/") != url.rstrip("/"):
            continue
        urls.append(url)
    today = date.today().isoformat()
    out.parent.mkdir(parents=True, exist_ok=True)
    sitemap_dir = out.parent / "sitemaps"
    sitemap_dir.mkdir(parents=True, exist_ok=True)

    for old_chunk in sitemap_dir.glob("base2026-*.xml"):
        old_chunk.unlink()

    chunk_paths = []
    for index in range(math.ceil(len(urls) / chunk_size)):
        chunk_urls = urls[index * chunk_size : (index + 1) * chunk_size]
        chunk_path = sitemap_dir / f"base2026-{index + 1:03d}.xml"
        chunk_body = "\n".join(
            f"  <url><loc>{html.escape(url)}</loc><lastmod>{today}</lastmod></url>" for url in chunk_urls
        )
        with chunk_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"{chunk_body}\n"
                "</urlset>\n"
            )
        chunk_paths.append(chunk_path)

    sitemap_base = args.base_url.rstrip("/")
    index_body = "\n".join(
        "  <sitemap>"
        f"<loc>{html.escape(sitemap_base + '/sitemaps/' + chunk_path.name)}</loc>"
        f"<lastmod>{today}</lastmod>"
        "</sitemap>"
        for chunk_path in chunk_paths
    )
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{index_body}\n"
            "</sitemapindex>\n"
        )
    print(
        f"sitemap_urls={len(urls)} sitemap_files={len(chunk_paths)} "
        f"required_archive={len(required_archive_routes)} forbidden_future={len(forbidden_future_routes)} out={out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
