#!/usr/bin/env python3
"""Derive the bounded Phase 1 Base P4 journey preview from accepted Phase 0.

The overlay adds only evidence-bound Source -> Solution discovery and the
consent-gated Product Truth runtime.  Corpus data, sitemap membership, robots,
canonicals, redirects, prices and WordPress are deliberately unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from html import escape
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from base2026_solution_journey import build_registry, read_json, read_jsonl  # noqa: E402
from public_manifest_contract import machine_local_value_issues  # noqa: E402

BASE_RELEASE = "base2026-phase0-p1-r6-preview-20260717-235500"
BASE_ZIP_SHA256 = "6ad17478944ffb14883b117dc4579b3c5099ad03fbf15ddec5760ee9ffd87087"
DERIVATION_SCHEMA = "base2026.phase1-base-p4-journey/v1"
RECEIPT_NAME = "BASE2026_PHASE1_BASE_P4_DERIVATION.json"
VALIDATION_NAME = "BASE2026_PHASE1_BASE_P4_VALIDATION.json"
RELEASE_RE = re.compile(r"^base2026-phase1-base-p4-preview-20260717-\d{6}$")
EXTERNAL_FONT_LINK_RE = re.compile(
    r'<link\b(?=[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com))[^>]*?/?>\s*',
    re.IGNORECASE,
)
LOCAL_FONT_LINK_RE = re.compile(
    r'<link\b(?=[^>]*href=["\'][^"\']*vendor/geist-local\.css[^"\']*["\'])[^>]*?/?>\s*',
    re.IGNORECASE,
)
SHELL_FONT_IMPORT_RE = re.compile(
    r"\A@import\s+url\(['\"]https://fonts\.googleapis\.com/[^'\"]+['\"]\);\s*",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\"\)\s]+)", re.IGNORECASE)
CSS_BARE_IMPORT_RE = re.compile(r"@import\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)
VENDOR_ROOT = ROOT / "web/static/vendor"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    }


def safe_extract(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            rel = Path(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if rel.is_absolute() or ".." in rel.parts or mode == stat.S_IFLNK:
                raise ValueError("Base preview contains an unsafe ZIP entry")
        archive.extractall(destination)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def deterministic_zip(root: Path, output: Path) -> None:
    fixed_time = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def solution_runtime() -> str:
    module_path = SCRIPT_DIR / "generate-ai-recommends-solutions.py"
    spec = importlib.util.spec_from_file_location("base2026_solution_generator_phase1", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load Solution generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(module.solution_js_text())


def source_bridge_html(mapping: dict[str, Any]) -> str:
    cards: list[str] = []
    for solution in mapping["solutions"]:
        cards.append(
            '<article class="b26-source-solution-card" '
            f'data-solution-id="{escape(solution["id"])}">'
            '<span class="b26-source-solution-card__role">Evidence-bound Solution</span>'
            '<h3><a '
            f'href="{escape(solution["href"])}" '
            'data-journey-action="solution_opened" data-journey-surface="source_detail" '
            f'data-solution-id="{escape(solution["id"])}">{escape(solution["title"])}</a></h3>'
            f'<p>{escape(solution["why_relevant"])}</p></article>'
        )
    return (
        '<section class="b26-source-section b26-source-solution-bridge" id="solutions" '
        f'data-source-solution-count="{len(cards)}">'
        '<div class="b26-section-heading b26-source-solution-bridge__heading">'
        '<p>Evidence → decision</p><h2>Decision playbooks using this source</h2></div>'
        '<p class="b26-source-solution-bridge__boundary">Shown only where this exact reviewed source signal '
        'contributes to an approved Base2026 Solution. Creator claims remain separate from Base2026 synthesis.</p>'
        f'<div class="b26-source-solution-list">{"".join(cards)}</div></section>'
    )


def localize_fonts(html: str, href: str) -> str:
    matches = EXTERNAL_FONT_LINK_RE.findall(html)
    if len(matches) not in {0, 3}:
        raise ValueError(f"Expected zero or three external font links, found {len(matches)}")
    localized = EXTERNAL_FONT_LINK_RE.sub("", html)
    local_matches = LOCAL_FONT_LINK_RE.findall(localized)
    if len(local_matches) > 1:
        raise ValueError(f"Expected at most one local font link, found {len(local_matches)}")
    localized = LOCAL_FONT_LINK_RE.sub("", localized)
    shell_reference_count = localized.count("alex-v4-static-shell.css")
    if shell_reference_count > 1:
        raise ValueError("Multiple shell CSS references found while localizing pilot route")
    if shell_reference_count == 1:
        localized = localized.replace(
            "alex-v4-static-shell.css",
            "alex-v4-static-shell-p4-local.css",
            1,
        )
    local_tag = f'<link rel="stylesheet" href="{href}" data-base2026-local-fonts="geist-manrope" />\n'
    if localized.count("</head>") != 1:
        raise ValueError("HTML head contract drift while localizing fonts")
    return localized.replace("</head>", local_tag + "</head>", 1)


def patch_search_dependencies(path: Path) -> None:
    html = localize_fonts(path.read_text(encoding="utf-8"), "./static/vendor/geist-local.css?v=20260717-p4")
    replacements = {
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/instantsearch.css@8/themes/reset-min.css" />':
            '<link rel="stylesheet" href="./static/vendor/instantsearch-reset-8.16.2.min.css" />',
        '<script src="https://cdn.jsdelivr.net/npm/@meilisearch/instant-meilisearch/dist/instant-meilisearch.umd.min.js"></script>':
            '<script src="./static/vendor/instant-meilisearch-1.0.0.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/instantsearch.js@4"></script>':
            '<script src="./static/vendor/instantsearch-4.106.0.min.js"></script>',
    }
    for old, new in replacements.items():
        if html.count(old) != 1:
            raise ValueError(f"Search dependency contract drift: {old}")
        html = html.replace(old, new, 1)
    path.write_text(html, encoding="utf-8")


def build_local_shell_css(source: Path, destination: Path) -> str:
    css = source.read_text(encoding="utf-8")
    localized, replacements = SHELL_FONT_IMPORT_RE.subn("", css, count=1)
    if replacements not in {0, 1}:
        raise ValueError("Accepted shell CSS font import contract drift")
    if "fonts.googleapis.com" in localized or "fonts.gstatic.com" in localized:
        raise ValueError("Localized shell CSS retains an external font dependency")
    destination.write_text(localized, encoding="utf-8")
    return sha256(destination)


def patch_source_page(path: Path, mapping: dict[str, Any]) -> dict[str, str]:
    before = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(before, "html.parser")
    robots = str((soup.select_one('meta[name="robots"]') or {}).get("content") or "").lower()
    canonical = str((soup.select_one('link[rel="canonical"]') or {}).get("href") or "")
    main = soup.select_one('main[data-admission-state="normal_public_card"]')
    if "noindex" in robots or "index" not in robots or not canonical or main is None:
        raise ValueError(f"Mapped source is not an admitted indexable Source Detail route: {path.name}")
    item_id = str(mapping["item_id"])
    existing_bridges = soup.select("#solutions")
    if existing_bridges:
        existing_ids = {
            str(node.get("data-solution-id") or "")
            for node in existing_bridges[0].select('[data-journey-action="solution_opened"]')
        }
        expected_ids = {str(row["id"]) for row in mapping["solutions"]}
        if (
            len(existing_bridges) != 1
            or str(main.get("data-source-item-id") or "") != item_id
            or existing_ids != expected_ids
        ):
            raise ValueError(f"Mapped source has a conflicting Solution bridge: {path.name}")
        after = localize_fonts(before, "../static/vendor/geist-local.css?v=20260717-p4")
        path.write_text(after, encoding="utf-8")
        return {"route": mapping["route"], "robots": robots, "canonical": canonical}
    main_open = '<main id="content" class="b26-source-shell" data-admission-state="normal_public_card">'
    main_replacement = (
        '<main id="content" class="b26-source-shell" data-admission-state="normal_public_card" '
        f'data-source-item-id="{escape(item_id)}">'
    )
    if before.count(main_open) != 1:
        raise ValueError(f"Source main contract drift: {path.name}")
    after = before.replace(main_open, main_replacement, 1)
    intelligence_start = after.find('<section class="b26-source-section b26-source-intelligence" id="intelligence">')
    if intelligence_start < 0:
        raise ValueError(f"Mapped source has no Source Intelligence section: {path.name}")
    intelligence_end = after.find("</section>", intelligence_start)
    if intelligence_end < 0:
        raise ValueError(f"Mapped source has an unclosed Source Intelligence section: {path.name}")
    intelligence_end += len("</section>")
    after = after[:intelligence_end] + source_bridge_html(mapping) + after[intelligence_end:]
    questions_link = '<a href="#questions">Questions</a>'
    if questions_link not in after:
        raise ValueError(f"Mapped source has no rail Questions link: {path.name}")
    after = after.replace(questions_link, '<a href="#solutions">Solutions</a>' + questions_link, 1)
    after = localize_fonts(after, "../static/vendor/geist-local.css?v=20260717-p4")
    path.write_text(after, encoding="utf-8")
    verified = BeautifulSoup(after, "html.parser")
    if str((verified.select_one('meta[name="robots"]') or {}).get("content") or "").lower() != robots:
        raise AssertionError("Source robots changed during journey overlay")
    if str((verified.select_one('link[rel="canonical"]') or {}).get("href") or "") != canonical:
        raise AssertionError("Source canonical changed during journey overlay")
    if len(verified.select("#solutions")) != 1 or len(verified.select('[data-journey-action="solution_opened"]')) != len(mapping["solutions"]):
        raise AssertionError("Source Solution bridge did not render exactly")
    return {"route": mapping["route"], "robots": robots, "canonical": canonical}


def patch_solution_page(path: Path, solution_id: str) -> dict[str, str]:
    before = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(before, "html.parser")
    robots = str((soup.select_one('meta[name="robots"]') or {}).get("content") or "").lower()
    canonical = str((soup.select_one('link[rel="canonical"]') or {}).get("href") or "")
    expected_canonical = f"https://aggressorbulkit.online/knowledge/solutions/{solution_id}.html"
    if "noindex" in robots or "index" not in robots or canonical != expected_canonical:
        raise ValueError(f"Approved Solution route is not indexable/self-canonical: {solution_id}")
    existing_bridges = soup.select('[data-research-bridge="solution_to_apply_research"]')
    if existing_bridges:
        if len(existing_bridges) != 1 or existing_bridges[0].get("data-origin-id") != solution_id:
            raise ValueError(f"Solution page has a conflicting Apply Research bridge: {solution_id}")
        after = localize_fonts(before, "../static/vendor/geist-local.css?v=20260717-p4")
        path.write_text(after, encoding="utf-8")
        return {"route": f"solutions/{solution_id}.html", "robots": robots, "canonical": canonical}
    section_start = before.find('<section class="content-section solution-next-action">')
    if section_start < 0:
        raise ValueError(f"Solution next-action contract drift: {solution_id}")
    section_end = before.find("</section>", section_start)
    if section_end < 0:
        raise ValueError(f"Solution next-action section is unclosed: {solution_id}")
    section = before[section_start:section_end]
    cta_start = section.find('<a class="ay-button"')
    cta_end = section.find("</a>", cta_start)
    if cta_start < 0 or cta_end < 0:
        raise ValueError(f"Solution evidence CTA contract drift: {solution_id}")
    cta_end += len("</a>")
    bridge = (
        '<div class="solution-next-action__bridge">'
        '<a class="ay-button-secondary" href="../apply-research.html" '
        'data-research-bridge="solution_to_apply_research" '
        f'data-origin-id="{escape(solution_id)}">Apply Research to a Business</a>'
        '<p class="solution-next-action__boundary">Optional: use this bridge only when public research needs '
        'business-specific diagnosis. The Base2026 research path remains complete without a service request.</p>'
        '</div>'
    )
    section = section[:cta_end] + bridge + section[cta_end:]
    after = before[:section_start] + section + before[section_end:]
    after = localize_fonts(after, "../static/vendor/geist-local.css?v=20260717-p4")
    path.write_text(after, encoding="utf-8")
    verified = BeautifulSoup(after, "html.parser")
    bridge_node = verified.select_one('[data-research-bridge="solution_to_apply_research"]')
    if not bridge_node or bridge_node.get("data-origin-id") != solution_id:
        raise AssertionError(f"Solution bridge did not render exactly: {solution_id}")
    if str((verified.select_one('meta[name="robots"]') or {}).get("content") or "").lower() != robots:
        raise AssertionError("Solution robots changed during journey overlay")
    if str((verified.select_one('link[rel="canonical"]') or {}).get("href") or "") != canonical:
        raise AssertionError("Solution canonical changed during journey overlay")
    return {"route": f"solutions/{solution_id}.html", "robots": robots, "canonical": canonical}


def patch_apply_research_page(path: Path) -> dict[str, str]:
    before = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(before, "html.parser")
    robots = str((soup.select_one('meta[name="robots"]') or {}).get("content") or "").lower()
    canonical = str((soup.select_one('link[rel="canonical"]') or {}).get("href") or "")
    expected = "https://aggressorbulkit.online/knowledge/apply-research.html"
    if "noindex" in robots or "index" not in robots or canonical != expected:
        raise ValueError("Apply Research route is not indexable/self-canonical")
    after = localize_fonts(before, "./static/vendor/geist-local.css?v=20260717-p4")
    path.write_text(after, encoding="utf-8")
    verified = BeautifulSoup(after, "html.parser")
    if str((verified.select_one('meta[name="robots"]') or {}).get("content") or "").lower() != robots:
        raise AssertionError("Apply Research robots changed during journey overlay")
    if str((verified.select_one('link[rel="canonical"]') or {}).get("href") or "") != canonical:
        raise AssertionError("Apply Research canonical changed during journey overlay")
    if not verified.select_one("main#content h1"):
        raise AssertionError("Apply Research render contract is missing")
    return {"route": "apply-research.html", "robots": robots, "canonical": canonical}


def local_asset_path(web_root: Path, owner: Path, url: str) -> Path | None:
    clean = url.split("#", 1)[0].split("?", 1)[0]
    if not clean or clean.startswith(("data:", "blob:", "mailto:", "tel:")):
        return None
    if clean.startswith("/knowledge/"):
        candidate = web_root / clean.removeprefix("/knowledge/")
    elif clean.startswith("/"):
        return None
    else:
        candidate = owner.parent / clean
    resolved = candidate.resolve()
    try:
        resolved.relative_to(web_root.resolve())
    except ValueError:
        return None
    return resolved


def css_external_resource_urls(path: Path, web_root: Path, seen: set[Path]) -> list[str]:
    resolved = path.resolve()
    if resolved in seen or not resolved.is_file():
        return []
    seen.add(resolved)
    urls: list[str] = []
    css = resolved.read_text(encoding="utf-8")
    references = CSS_URL_RE.findall(css) + CSS_BARE_IMPORT_RE.findall(css)
    for reference in references:
        if reference.startswith(("http://", "https://")):
            urls.append(reference)
            continue
        local = local_asset_path(web_root, resolved, reference)
        if local and local.suffix.lower() == ".css":
            urls.extend(css_external_resource_urls(local, web_root, seen))
    return urls


def active_external_resource_urls(path: Path, web_root: Path) -> list[str]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    urls: list[str] = []
    for tag in soup.select("script[src], img[src], iframe[src], video[src], video[poster], audio[src], source[src]"):
        for key in ("src", "poster"):
            value = str(tag.get(key) or "")
            if value.startswith(("http://", "https://")):
                urls.append(value)
    active_link_rels = {
        "stylesheet", "preload", "modulepreload", "preconnect", "dns-prefetch", "icon", "apple-touch-icon",
    }
    for tag in soup.select("link[href]"):
        rels = {str(value).lower() for value in (tag.get("rel") or [])}
        value = str(tag.get("href") or "")
        if rels & active_link_rels and value.startswith(("http://", "https://")):
            urls.append(value)
        if "stylesheet" in rels and not value.startswith(("http://", "https://")):
            local = local_asset_path(web_root, path, value)
            if local:
                urls.extend(css_external_resource_urls(local, web_root, set()))
    return sorted(set(urls))


def json_path_issues(root: Path) -> tuple[int, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    paths = sorted(root.rglob("*.json"))
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for issue in machine_local_value_issues(payload):
            issues.append({"file": path.relative_to(root).as_posix(), **issue})
    return len(paths), issues


def sitemap_snapshot(root: Path) -> dict[str, str]:
    candidates = [root / "web/sitemap.xml"]
    sitemap_dir = root / "web/sitemaps"
    if sitemap_dir.is_dir():
        candidates.extend(sorted(sitemap_dir.glob("*.xml")))
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in candidates
        if path.is_file()
    }


def build(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    base_zip = args.base_zip.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    release_root = output_dir / args.release_name
    zip_path = output_dir / f"{args.release_name}.zip"
    if not RELEASE_RE.fullmatch(args.release_name):
        raise ValueError("Release name must match the Phase 1 Base P4 preview contract")
    if not base_zip.is_file() or sha256(base_zip) != BASE_ZIP_SHA256:
        raise ValueError("Accepted Phase 0 ZIP is missing or has the wrong SHA-256")
    if release_root.exists() or zip_path.exists():
        raise FileExistsError("Refusing to overwrite an existing Phase 1 preview")
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="base2026-phase1-base-p4-", dir=output_dir) as temp_name:
        extracted = Path(temp_name) / "release"
        safe_extract(base_zip, extracted)
        before = snapshot(extracted)
        package_path = extracted / "manifest.json"
        package = read_json(package_path)
        if package.get("release_name") != BASE_RELEASE:
            raise ValueError("Phase 0 package identity mismatch")
        sitemap_before = sitemap_snapshot(extracted)

        registry = build_registry(
            read_json(ROOT / "contracts/base2026-approved-solution-ids.json"),
            read_json(ROOT / "data/base2026_ai_recommends_solutions_pilot.json"),
            read_jsonl(extracted / "web/static/documents.jsonl"),
            read_jsonl(extracted / "web/static/insight_cards.jsonl"),
        )
        registry_path = extracted / "web/static/base2026-solution-journey.json"
        write_json(registry_path, registry)
        for name in ("base2026-solution-journey.js", "base2026-solution-journey.css"):
            shutil.copy2(ROOT / "web/static" / name, extracted / "web/static" / name)
        for name in ("purify.min.js", "purify.min.js.LICENSE.txt"):
            shutil.copy2(ROOT / "web/static" / name, extracted / "web/static" / name)
        shutil.copy2(ROOT / "web/static/meili.js", extracted / "web/static/meili.js")
        shutil.copy2(ROOT / "scripts/base2026_search_v3.js", extracted / "web/static/base2026-search-v3.js")
        shutil.copy2(ROOT / "scripts/base2026_source_detail_v2.js", extracted / "web/static/source-detail-v2.js")
        (extracted / "web/static/ai-recommends-solutions.js").write_text(solution_runtime(), encoding="utf-8")
        vendor_files = sorted(path for path in VENDOR_ROOT.iterdir() if path.is_file())
        vendor_destination = extracted / "web/static/vendor"
        vendor_destination.mkdir(parents=True, exist_ok=False)
        for path in vendor_files:
            shutil.copy2(path, vendor_destination / path.name)
        local_shell_path = extracted / "web/static/alex-v4-static-shell-p4-local.css"
        local_shell_sha256 = build_local_shell_css(
            extracted / "web/static/alex-v4-static-shell.css",
            local_shell_path,
        )
        search_index = extracted / "web/index.html"
        search_html = search_index.read_text(encoding="utf-8")
        if "purify.min.js" not in search_html:
            meili_tag = '<script src="./static/meili.js?v=base2026-search-v1-derived-20260714-024003"></script>'
            if search_html.count(meili_tag) != 1:
                raise ValueError("Search runtime script contract drift")
            search_html = search_html.replace(
                meili_tag,
                '<script src="./static/purify.min.js?v=3.2.6"></script>\n    ' + meili_tag,
                1,
            )
            search_index.write_text(search_html, encoding="utf-8")
        patch_search_dependencies(search_index)

        patched_sources = [
            patch_source_page(extracted / "web" / mapping["route"], mapping)
            for mapping in registry["source_mappings"]
        ]
        patched_solutions = [
            patch_solution_page(extracted / "web/solutions" / f"{solution_id}.html", solution_id)
            for solution_id in registry["approved_solution_ids"]
        ]
        patched_apply_research = patch_apply_research_page(extracted / "web/apply-research.html")
        pilot_route_files = [search_index]
        pilot_route_files.extend(extracted / "web" / row["route"] for row in patched_sources)
        pilot_route_files.extend(extracted / "web" / row["route"] for row in patched_solutions)
        pilot_route_files.append(extracted / "web" / patched_apply_research["route"])
        external_resources: dict[str, list[str]] = {}
        for path in pilot_route_files:
            urls = active_external_resource_urls(path, extracted / "web")
            if urls:
                external_resources[path.relative_to(extracted).as_posix()] = urls
        if external_resources:
            raise AssertionError(f"Pilot routes retain active external browser dependencies: {external_resources}")
        vendor_hashes = {
            f"web/static/vendor/{path.name}": sha256(vendor_destination / path.name)
            for path in vendor_files
        }

        required_runtime = list(package.get("required_runtime_files") or [])
        for rel in (
            "web/static/base2026-solution-journey.json",
            "web/static/base2026-solution-journey.js",
            "web/static/base2026-solution-journey.css",
            "web/static/purify.min.js",
            "web/static/purify.min.js.LICENSE.txt",
            "web/static/alex-v4-static-shell-p4-local.css",
            *vendor_hashes,
        ):
            if rel not in required_runtime:
                required_runtime.append(rel)
        required_contract = list(package.get("required_contract_files") or [])
        for rel in (RECEIPT_NAME, VALIDATION_NAME):
            if rel not in required_contract:
                required_contract.append(rel)
        package.update(
            {
                "release_name": args.release_name,
                "package_mode": "data-preserving-static-derived-phase1-base-p4-preview",
                "required_runtime_files": required_runtime,
                "required_contract_files": required_contract,
                "phase1_base_p4": {
                    "schema": DERIVATION_SCHEMA,
                    "base_release": BASE_RELEASE,
                    "base_zip_sha256": BASE_ZIP_SHA256,
                    "approved_solution_count": registry["counts"]["approved_solutions"],
                    "evidence_bound_source_count": registry["counts"]["evidence_bound_sources"],
                    "evidence_link_count": registry["counts"]["evidence_links"],
                    "approved_solution_bridge_count": len(patched_solutions),
                    "apply_research_route_localized": True,
                    "local_vendor_file_count": len(vendor_hashes),
                    "local_shell_css_sha256": local_shell_sha256,
                    "active_external_dependency_count_on_pilot_routes": 0,
                    "event_ids": [
                        "product_search_submitted",
                        "source_opened",
                        "evidence_actioned",
                        "solution_opened",
                        "research_bridge_clicked",
                    ],
                    "corpus_reexported": False,
                    "meilisearch_reindexed": False,
                    "sitemap_changed": False,
                    "indexability_changed": False,
                    "canonical_changed": False,
                    "wordpress_root_mutation": False,
                    "production_mutated": False,
                },
            }
        )
        write_json(package_path, package)
        (extracted / "RELEASE.txt").write_text(
            f"{args.release_name}\nDerived from {BASE_RELEASE}\nPhase 1 Base P4 preview only; production unchanged.\n",
            encoding="utf-8",
        )

        receipt = {
            "schema": DERIVATION_SCHEMA,
            "release_name": args.release_name,
            "base_release": BASE_RELEASE,
            "base_zip_sha256": BASE_ZIP_SHA256,
            "registry": registry["counts"],
            "registry_sha256": sha256(registry_path),
            "patched_source_routes": [row["route"] for row in patched_sources],
            "patched_solution_routes": [row["route"] for row in patched_solutions],
            "patched_apply_research_route": patched_apply_research["route"],
            "vendor_files": vendor_hashes,
            "local_shell_css_sha256": local_shell_sha256,
            "active_external_dependency_count_on_pilot_routes": 0,
            "event_ids": package["phase1_base_p4"]["event_ids"],
            "measurement_policy": {
                "consent_required": True,
                "raw_query_forbidden": True,
                "pii_forbidden": True,
                "private_source_data_forbidden": True,
                "full_referrer_url_forbidden": True,
                "bridge_is_conversion": False,
            },
            "production_mutated": False,
        }
        write_json(extracted / RECEIPT_NAME, receipt)

        after_before_validation = snapshot(extracted)
        changed = sorted(
            rel for rel in set(before) | set(after_before_validation)
            if before.get(rel) != after_before_validation.get(rel)
        )
        allowed_changed = {
            "manifest.json",
            "RELEASE.txt",
            RECEIPT_NAME,
            "web/static/meili.js",
            "web/static/base2026-search-v3.js",
            "web/static/source-detail-v2.js",
            "web/static/ai-recommends-solutions.js",
            "web/static/base2026-solution-journey.json",
            "web/static/base2026-solution-journey.js",
            "web/static/base2026-solution-journey.css",
            "web/static/purify.min.js",
            "web/static/purify.min.js.LICENSE.txt",
            "web/static/alex-v4-static-shell-p4-local.css",
            "web/index.html",
            "web/apply-research.html",
            *vendor_hashes,
            *[f"web/{row['route']}" for row in registry["source_mappings"]],
            *[f"web/{row['route']}" for row in patched_solutions],
        }
        unexpected = sorted(set(changed) - allowed_changed)
        if unexpected:
            raise AssertionError(f"Phase 1 overlay changed unexpected files: {unexpected}")
        sitemap_after = sitemap_snapshot(extracted)
        if sitemap_before != sitemap_after:
            raise AssertionError("Phase 1 overlay changed sitemap bytes")
        validation = {
            "schema": "base2026.phase1-base-p4-validation/v1",
            "ok": True,
            "release_name": args.release_name,
            "changed_file_count_before_validation": len(changed),
            "changed_files_before_validation": changed,
            "sitemap_file_count": len(sitemap_after),
            "sitemap_bytes_unchanged": True,
            "source_routes_checked": len(patched_sources),
            "source_robots_and_canonicals_unchanged": True,
            "solution_routes_checked": len(patched_solutions),
            "solution_robots_and_canonicals_unchanged": True,
            "apply_research_route_checked": True,
            "apply_research_robots_and_canonical_unchanged": True,
            "active_external_dependency_count_on_pilot_routes": 0,
            "local_vendor_file_count": len(vendor_hashes),
            "local_shell_css_sha256": local_shell_sha256,
            "approved_solution_ids": registry["approved_solution_ids"],
            "package_json_files_scanned": 0,
            "package_json_machine_local_path_issue_count": 0,
            "production_mutated": False,
        }
        write_json(extracted / VALIDATION_NAME, validation)
        json_count, path_issues = json_path_issues(extracted)
        if path_issues:
            raise AssertionError(f"Package JSON contains machine-local path shapes: {path_issues}")
        validation["package_json_files_scanned"] = json_count
        write_json(extracted / VALIDATION_NAME, validation)
        shutil.move(str(extracted), release_root)
    deterministic_zip(release_root, zip_path)
    return release_root, zip_path, validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-zip", type=Path, required=True)
    parser.add_argument("--release-name", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root, zip_path, validation = build(args)
    print(json.dumps({
        "release_root": str(root),
        "zip": str(zip_path),
        "zip_sha256": sha256(zip_path),
        "validation": validation,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
