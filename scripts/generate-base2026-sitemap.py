from __future__ import annotations

import argparse
import html
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, urlunsplit


SOURCE_CANDIDATE_SCHEMA = "base2026.source-detail-v2-full-candidate/v1"
STATIC_ADMISSION_SCHEMA = "base2026.sitemap-static-admission/v1"
NORMAL_PUBLIC_CARD = "normal_public_card"
PROVENANCE_ARCHIVE_NOINDEX = "provenance_archive_noindex"
FUTURE_PRIVATE_BACKLOG = "future_private_backlog"
ROBOTS_NAMES = {"robots", "googlebot", "bingbot"}
EXPLICIT_NOINDEX_TOKENS = {"noindex", "none"}
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


class HeadMetadataParser(HTMLParser):
    """Extract head metadata regardless of attribute order and stop at </head>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self._in_head = False
        self._done = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag == "head":
            self._in_head = True
            return
        if self._done or not self._in_head:
            return
        values = {name.casefold(): (value or "") for name, value in attrs}
        if tag == "meta" and values.get("name", "").casefold() in ROBOTS_NAMES:
            self.robots.append(values.get("content", ""))
        if tag == "link":
            rel_tokens = {token for token in re.split(r"\s+", values.get("rel", "").casefold()) if token}
            if "canonical" in rel_tokens:
                self.canonicals.append(html.unescape(values.get("href", "")).strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "head":
            self._in_head = False
            self._done = True


@dataclass(frozen=True)
class SourceAdmission:
    normal: frozenset[str] = frozenset()
    archive: frozenset[str] = frozenset()
    future: frozenset[str] = frozenset()
    mode: str = "absent"


def head_metadata(path: Path) -> HeadMetadataParser:
    parser = HeadMetadataParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser


def robots_tokens(metadata: HeadMetadataParser) -> set[str]:
    return {
        directive.casefold()
        for content in metadata.robots
        for directive in re.split(r"[\s,;]+", content.strip())
        if directive
    }


def metadata_is_indexable(metadata: HeadMetadataParser) -> bool:
    return not (robots_tokens(metadata) & EXPLICIT_NOINDEX_TOKENS)


def is_indexable(path: Path) -> bool:
    return metadata_is_indexable(head_metadata(path))


def canonical_url(path: Path) -> str | None:
    canonicals = head_metadata(path).canonicals
    return canonicals[0] if len(canonicals) == 1 and canonicals[0] else None


def url_for(web_root: Path, path: Path, base_url: str) -> str:
    rel = path.relative_to(web_root).as_posix()
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return f"{base_url.rstrip('/')}/{rel}"


def normalized_absolute_url(value: str) -> str | None:
    try:
        parsed = urlsplit(html.unescape(value).strip())
    except ValueError:
        return None
    if parsed.scheme.casefold() != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    hostname = parsed.hostname.casefold()
    netloc = hostname if port in (None, 443) else f"{hostname}:{port}"
    path = parsed.path or "/"
    return urlunsplit(("https", netloc, path, "", ""))


def canonical_is_exactly_self(metadata: HeadMetadataParser, expected_url: str) -> bool:
    if len(metadata.canonicals) != 1 or not metadata.canonicals[0]:
        return False
    return normalized_absolute_url(metadata.canonicals[0]) == normalized_absolute_url(expected_url)


def safe_source_route(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("source route must be a string")
    route = PurePosixPath(value)
    if (
        route.is_absolute()
        or route.as_posix() != value
        or ".." in route.parts
        or not value.startswith("sources/tiktok-video-")
        or not value.endswith(".html")
    ):
        raise ValueError("source route is not a normalized Source Detail route")
    return value


def load_source_admission(path: Path | None) -> SourceAdmission:
    if path is None:
        return SourceAdmission()
    manifest = json.loads(path.resolve().read_text(encoding="utf-8"))
    if manifest.get("schema") != SOURCE_CANDIDATE_SCHEMA:
        raise ValueError("unsupported Source Detail candidate schema")
    rendered = manifest.get("rendered")
    future_rows = manifest.get("future_private_not_emitted")
    if not isinstance(rendered, list) or not isinstance(future_rows, list):
        raise ValueError("invalid Source Detail candidate membership")

    normal: set[str] = set()
    archive: set[str] = set()
    seen: set[str] = set()
    for item in rendered:
        if not isinstance(item, dict):
            raise ValueError("invalid rendered Source Detail row")
        route = safe_source_route(item.get("route"))
        if route in seen:
            raise ValueError("duplicate Source Detail route")
        seen.add(route)
        state = item.get("admission_state")
        if state == NORMAL_PUBLIC_CARD:
            normal.add(route)
        elif state == PROVENANCE_ARCHIVE_NOINDEX:
            archive.add(route)
        else:
            raise ValueError("unsupported rendered Source Detail admission state")

    future = {safe_source_route(route) for route in future_rows}
    if len(future) != len(future_rows) or seen & future:
        raise ValueError("duplicate or conflicting future/private Source Detail route")
    return SourceAdmission(frozenset(normal), frozenset(archive), frozenset(future), "candidate_manifest")


def load_source_records_admission(path: Path | None) -> SourceAdmission:
    if path is None:
        return SourceAdmission()
    normal: set[str] = set()
    archive: set[str] = set()
    seen: set[str] = set()
    for line in path.resolve().read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError("invalid public source-record row")
        item_id = row.get("item_id")
        route = safe_source_route(f"sources/{item_id}.html")
        if route in seen:
            raise ValueError("duplicate public source-record route")
        seen.add(route)
        state = row.get("admission_state")
        if state == NORMAL_PUBLIC_CARD:
            normal.add(route)
        elif state == PROVENANCE_ARCHIVE_NOINDEX:
            archive.add(route)
        else:
            raise ValueError("unsupported public source-record admission state")
    if not normal:
        raise ValueError("public source-record admission has no normal routes")
    return SourceAdmission(frozenset(normal), frozenset(archive), frozenset(), "public_source_records")


def safe_static_route(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("static admission route must be a string")
    route = PurePosixPath(value)
    if (
        route.is_absolute()
        or route.as_posix() != value
        or ".." in route.parts
        or not value.endswith(".html")
        or value.startswith("sources/tiktok-video-")
    ):
        raise ValueError("static admission route is not a normalized non-source HTML route")
    return value


def load_static_admission(path: Path, base_url: str) -> frozenset[str]:
    payload = json.loads(path.resolve().read_text(encoding="utf-8"))
    expected_keys = {
        "schema",
        "base_url",
        "source_release",
        "source_release_zip_sha256",
        "evidence",
        "routes",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ValueError("invalid static sitemap admission shape")
    if payload.get("schema") != STATIC_ADMISSION_SCHEMA:
        raise ValueError("unsupported static sitemap admission schema")
    if normalized_absolute_url(str(payload.get("base_url") or "")) != normalized_absolute_url(base_url):
        raise ValueError("static sitemap admission base URL mismatch")
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise ValueError("static sitemap admission routes must be an array")
    admitted = {safe_static_route(route) for route in routes}
    if len(admitted) != len(routes):
        raise ValueError("static sitemap admission routes are duplicated")
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("approved_static_routes") != len(admitted):
        raise ValueError("static sitemap admission evidence count mismatch")
    return frozenset(admitted)


def validate_source_file_membership(web_root: Path, admission: SourceAdmission) -> None:
    emitted = {
        path.relative_to(web_root).as_posix()
        for path in (web_root / "sources").glob("tiktok-video-*.html")
    }
    if not (admission.normal or admission.archive or admission.future):
        if emitted:
            raise ValueError("Source Detail HTML exists without an exact source admission input")
        return
    expected_public = set(admission.normal | admission.archive)
    missing_public = expected_public - emitted
    unexpected_public = emitted - expected_public
    future_emitted = emitted & set(admission.future)
    if missing_public or unexpected_public or future_emitted:
        raise ValueError(
            "Source Detail cohort mismatch: "
            f"missing_public={len(missing_public)}, unexpected_public={len(unexpected_public)}, "
            f"future_private_emitted={len(future_emitted)}"
        )


def admitted_sitemap_urls(
    web_root: Path, base_url: str, admission: SourceAdmission, static_admission: frozenset[str]
) -> tuple[list[str], dict[str, int | bool | str]]:
    validate_source_file_membership(web_root, admission)
    if (admission.normal | admission.archive | admission.future) & static_admission:
        raise ValueError("source and static admission routes overlap")
    urls: list[str] = []
    admitted_normal: set[str] = set()
    admitted_static: set[str] = set()
    metadata_failures = 0
    archive_indexability_failures = 0
    unapproved_indexable = 0

    for path in sorted(web_root.rglob("*.html")):
        route = path.relative_to(web_root).as_posix()
        expected_url = url_for(web_root, path, base_url)
        metadata = head_metadata(path)
        indexable = metadata_is_indexable(metadata)

        if route in admission.future:
            raise ValueError("future/private Source Detail route was emitted")
        if route in admission.archive:
            if indexable:
                archive_indexability_failures += 1
            if not canonical_is_exactly_self(metadata, expected_url):
                metadata_failures += 1
            continue
        if path.name.startswith("roadmap-dataviz-test"):
            if indexable:
                metadata_failures += 1
            continue
        if route in admission.normal:
            if not indexable or not canonical_is_exactly_self(metadata, expected_url):
                metadata_failures += 1
                continue
            urls.append(expected_url)
            admitted_normal.add(route)
            continue
        if route in static_admission:
            if not indexable or not canonical_is_exactly_self(metadata, expected_url):
                metadata_failures += 1
                continue
            urls.append(expected_url)
            admitted_static.add(route)
            continue
        if indexable:
            unapproved_indexable += 1

    missing_normal = set(admission.normal) - admitted_normal
    missing_static = set(static_admission) - admitted_static
    if metadata_failures or archive_indexability_failures or missing_normal or missing_static or unapproved_indexable:
        raise ValueError(
            "Sitemap metadata/admission contract failed: "
            f"metadata={metadata_failures}, archive_indexable={archive_indexability_failures}, "
            f"missing_normal={len(missing_normal)}, missing_static={len(missing_static)}, "
            f"unapproved_indexable={unapproved_indexable}"
        )
    if len(urls) != len(set(urls)):
        raise ValueError("duplicate canonical URL in admitted sitemap set")

    source_exact = bool(admission.normal or admission.archive or admission.future) or not any(
        (web_root / "sources").glob("tiktok-video-*.html")
    )
    return urls, {
        "source_cohort_exact": source_exact,
        "source_admission_mode": admission.mode,
        "normal_included": len(admission.normal),
        "archive_excluded": len(admission.archive),
        "future_excluded": len(admission.future),
        "static_exact_admission": len(admitted_static),
        "global_exact_admission": source_exact and admitted_static == set(static_admission),
        "global_exact_admission_status": "verified",
    }


def sitemap_chunk_paths(out: Path, url_count: int, chunk_size: int) -> list[Path]:
    return [
        out.parent / "sitemaps" / f"base2026-{index + 1:03d}.xml"
        for index in range(math.ceil(url_count / chunk_size))
    ]


def write_sitemaps(out: Path, base_url: str, urls: list[str], chunk_size: int, lastmod: str) -> list[Path]:
    out.parent.mkdir(parents=True, exist_ok=True)
    sitemap_dir = out.parent / "sitemaps"
    sitemap_dir.mkdir(parents=True, exist_ok=True)
    for old_chunk in sitemap_dir.glob("base2026-*.xml"):
        old_chunk.unlink()

    chunk_paths = sitemap_chunk_paths(out, len(urls), chunk_size)
    for index, chunk_path in enumerate(chunk_paths):
        chunk_urls = urls[index * chunk_size : (index + 1) * chunk_size]
        chunk_body = "\n".join(
            f"  <url><loc>{html.escape(url)}</loc><lastmod>{lastmod}</lastmod></url>" for url in chunk_urls
        )
        with chunk_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<urlset xmlns="{SITEMAP_NAMESPACE}">\n'
                f"{chunk_body}\n"
                "</urlset>\n"
            )

    sitemap_base = base_url.rstrip("/")
    index_body = "\n".join(
        "  <sitemap>"
        f"<loc>{html.escape(sitemap_base + '/sitemaps/' + chunk_path.name)}</loc>"
        f"<lastmod>{lastmod}</lastmod>"
        "</sitemap>"
        for chunk_path in chunk_paths
    )
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<sitemapindex xmlns="{SITEMAP_NAMESPACE}">\n'
            f"{index_body}\n"
            "</sitemapindex>\n"
        )
    return chunk_paths


def read_existing_sitemaps(out: Path, base_url: str) -> tuple[list[str], list[str]]:
    if not out.is_file():
        raise ValueError("sitemap index is missing")
    root = ET.parse(out).getroot()
    index_locations = [
        (element.text or "").strip()
        for element in root.findall(f"{{{SITEMAP_NAMESPACE}}}sitemap/{{{SITEMAP_NAMESPACE}}}loc")
    ]
    urls: list[str] = []
    expected_prefix = base_url.rstrip("/") + "/sitemaps/"
    for location in index_locations:
        if not location.startswith(expected_prefix):
            raise ValueError("sitemap index contains an unapproved child URL")
        name = location[len(expected_prefix) :]
        if not re.fullmatch(r"base2026-\d{3}\.xml", name):
            raise ValueError("sitemap index contains an invalid child name")
        chunk_path = out.parent / "sitemaps" / name
        if not chunk_path.is_file():
            raise ValueError("sitemap child is missing")
        chunk_root = ET.parse(chunk_path).getroot()
        urls.extend(
            (element.text or "").strip()
            for element in chunk_root.findall(f"{{{SITEMAP_NAMESPACE}}}url/{{{SITEMAP_NAMESPACE}}}loc")
        )
    return urls, index_locations


def check_existing_sitemaps(
    out: Path, base_url: str, expected_urls: list[str], chunk_size: int
) -> int:
    observed_urls, observed_chunks = read_existing_sitemaps(out, base_url)
    expected_chunks = [
        base_url.rstrip("/") + "/sitemaps/" + path.name
        for path in sitemap_chunk_paths(out, len(expected_urls), chunk_size)
    ]
    duplicate_count = len(observed_urls) - len(set(observed_urls))
    missing = set(expected_urls) - set(observed_urls)
    unexpected = set(observed_urls) - set(expected_urls)
    if duplicate_count or missing or unexpected or observed_chunks != expected_chunks:
        raise ValueError(
            "Existing sitemap contract failed: "
            f"duplicates={duplicate_count}, missing={len(missing)}, unexpected={len(unexpected)}, "
            f"chunk_index_match={observed_chunks == expected_chunks}"
        )
    return len(observed_chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate Base2026 sitemaps from public HTML metadata.")
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--base-url", default="https://aggressorbulkit.online/knowledge")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--lastmod", default=date.today().isoformat())
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--static-admission-manifest", type=Path, required=True)
    parser.add_argument(
        "--source-detail-manifest",
        type=Path,
        help=(
            "Optional immutable Source Detail V2 manifest. Normal routes are exact sitemap admissions; "
            "archive/noindex routes must remain public but are excluded; future/private routes are forbidden."
        ),
    )
    parser.add_argument(
        "--source-records",
        type=Path,
        help="Public source_records.jsonl used as exact source admission when no Source Detail candidate is supplied.",
    )
    args = parser.parse_args()

    web_root = args.web_root.resolve()
    if not web_root.is_dir():
        raise SystemExit("Web root is missing")
    out = args.out.resolve() if args.out else (web_root / "sitemap.xml")
    chunk_size = max(1, args.chunk_size)
    try:
        date.fromisoformat(args.lastmod)
        base = urlsplit(args.base_url)
        if base.scheme.casefold() != "https" or not base.hostname or base.query or base.fragment:
            raise ValueError("base URL must be an HTTPS origin path without query or fragment")
        if args.source_detail_manifest and args.source_records:
            raise ValueError("choose one source admission input")
        admission = (
            load_source_admission(args.source_detail_manifest)
            if args.source_detail_manifest
            else load_source_records_admission(args.source_records)
        )
        static_admission = load_static_admission(args.static_admission_manifest, args.base_url)
        urls, contract = admitted_sitemap_urls(web_root, args.base_url, admission, static_admission)
        if not contract["global_exact_admission"]:
            raise ValueError("global exact sitemap admission was not verified")
        if args.check_only:
            chunk_count = check_existing_sitemaps(out, args.base_url, urls, chunk_size)
        else:
            chunk_count = len(write_sitemaps(out, args.base_url, urls, chunk_size, args.lastmod))
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    print(
        " ".join(
            [
                f"sitemap_urls={len(urls)}",
                f"sitemap_files={chunk_count}",
                f"source_cohort_exact={str(contract['source_cohort_exact']).lower()}",
                f"source_admission_mode={contract['source_admission_mode']}",
                f"normal_included={contract['normal_included']}",
                f"archive_excluded={contract['archive_excluded']}",
                f"future_excluded={contract['future_excluded']}",
                f"static_exact_admission={contract['static_exact_admission']}",
                "global_exact_admission=true",
                "global_exact_admission_status=verified",
                f"mode={'check' if args.check_only else 'write'}",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
