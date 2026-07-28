#!/usr/bin/env python3
"""Normalize every generated Base2026 shell from one frozen WordPress Personal source.

This is the only header/footer mutation seam. It runs after all page generators,
writes the two parity assets, replaces shell markup, and fails if any body/head
contract outside the approved shell boundary changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER_TEMPLATE = ROOT / "templates" / "shared" / "alex-home-v4-header.html"
FOOTER_TEMPLATE = ROOT / "templates" / "shared" / "alex-home-v4-footer.html"
SOURCE_MANIFEST = ROOT / "templates" / "shared" / "wordpress-personal-shell-sources.json"
HEADER_CSS = ROOT / "scripts" / "wordpress-v4-header.css"
FOOTER_CSS = ROOT / "scripts" / "wordpress-v4-footer.css"
HEADER_SCRIPT = ROOT / "scripts" / "wordpress-v4-header.js"
HEADER_ASSET = "wordpress-v4-header.css"
FOOTER_ASSET = "wordpress-v4-footer.css"
HEADER_SCRIPT_ASSET = "wordpress-v4-header.js"

# Generated families enter this single post-generation seam with different
# historic shell class names (`site-header`, `ay-v2-header`, etc.). Restrict
# matching to those document-level shell classes so semantic headers inside
# page content remain outside the mutation boundary.
HEADER_RE = re.compile(
    r'<header\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\b(?:ay-v2-header|site-header)\b)[^>]*>.*?</header>',
    re.I | re.S,
)
FOOTER_RE = re.compile(r'<footer\b[^>]*>.*?</footer>', re.I | re.S)
BODY_OPEN_RE = re.compile(r'<body(?P<attrs>[^>]*)>', re.I)
SHELL_ASSET_RE = re.compile(
    r'\s*<link\b[^>]*href="[^"]*\b(?:wordpress-v4-header|wordpress-v4-footer)\.css(?:\?[^" ]*)?"[^>]*>\s*',
    re.I,
)
SHELL_SCRIPT_RE = re.compile(
    r'\s*<script\b[^>]*src="[^"]*\bwordpress-v4-header\.js(?:\?[^" ]*)?"[^>]*>\s*</script>\s*',
    re.I,
)
LEGACY_SHELL_SCRIPT_RE = re.compile(
    r"\s*<script\b[^>]*src=[\"'][^\"']*\balex-v4-static-shell\.js(?:\?[^\"']*)?[\"'][^>]*>\s*</script>\s*",
    re.I,
)
HREF_RE = re.compile(r'href="([^"]+)"', re.I)
TITLE_RE = re.compile(r'<title>.*?</title>', re.I | re.S)
CANONICAL_RE = re.compile(r'<link\b[^>]*rel="canonical"[^>]*>', re.I)
ROBOTS_RE = re.compile(r'<meta\b[^>]*name="robots"[^>]*>', re.I)

REQUIRED_BODY_CLASSES = ("ay-alex-v4-static", "ay-stitch-home-v3", "ay-stitch-home-v4")
REQUIRED_FOOTER_MARKERS = (
    'class="ay-actions"',
    'class="ay-footer-socials"',
    '>Apply Base2026 Research<',
    '>Services<',
    '>Start Here<',
    '>Base2026 Pilot Project<',
    '>Legal &amp; Trust<',
)
FORBIDDEN_FOOTER_MARKERS = ('data-footer-contract="personal-v1"', 'ay-footer-brand__name')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_markup(fragment: str) -> str:
    fragment = re.sub(r"\s+", " ", fragment).strip()
    fragment = re.sub(r"\s*>\s*<", "><", fragment)
    return fragment


def canonical_url(url: str) -> str:
    value = url.strip()
    for prefix in ("https://aggressorbulkit.online", "http://aggressorbulkit.online"):
        if value.startswith(prefix):
            value = value[len(prefix) :] or "/"
            break
    if value == "/knowledge/topics.html":
        return "/knowledge/topics/"
    if value == "/knowledge/creators.html":
        return "/knowledge/creators/"
    return value


def shell_urls(fragment: str) -> list[str]:
    return [canonical_url(value) for value in HREF_RE.findall(fragment)]


def head_signature(page: str) -> dict[str, object]:
    head_match = re.search(r"<head\b[^>]*>(.*?)</head>", page, re.I | re.S)
    head = head_match.group(1) if head_match else ""
    head = SHELL_ASSET_RE.sub("", head)
    return {
        "title": canonical_markup("".join(TITLE_RE.findall(head))),
        "canonical": canonical_markup("".join(CANONICAL_RE.findall(head))),
        "robots": canonical_markup("".join(ROBOTS_RE.findall(head))),
        "analytics_markers": {
            "gtm": head.lower().count("googletagmanager"),
            "gtag": head.lower().count("gtag("),
            "data_layer": head.lower().count("datalayer"),
            "base2026_analytics": head.lower().count("base2026_analytics"),
        },
    }


def content_fingerprint(page: str) -> str:
    """Hash everything except the explicitly allowed shell/body-class/asset seam."""
    reduced = HEADER_RE.sub("", page)
    reduced = FOOTER_RE.sub("", reduced)
    reduced = SHELL_ASSET_RE.sub("", reduced)
    reduced = SHELL_SCRIPT_RE.sub("", reduced)
    reduced = LEGACY_SHELL_SCRIPT_RE.sub("", reduced)
    reduced = BODY_OPEN_RE.sub("<body>", reduced, count=1)
    # Formatting indentation around shell/asset boundaries is not page content.
    # Canonicalize inter-tag whitespace before hashing so the gate remains
    # exact for text/attributes/scripts while ignoring serializer layout only.
    reduced = re.sub(r">\s+<", "><", reduced)
    reduced = re.sub(r"\s+", " ", reduced).strip()
    return sha256_text(reduced)


def normalize_body_classes(page: str) -> str:
    match = BODY_OPEN_RE.search(page)
    if not match:
        raise ValueError("missing <body>")
    attrs = match.group("attrs") or ""
    class_match = re.search(r'class="([^"]*)"', attrs, re.I)
    classes = class_match.group(1).split() if class_match else []
    for required in REQUIRED_BODY_CLASSES:
        if required not in classes:
            classes.append(required)
    class_attr = f'class="{" ".join(classes)}"'
    if class_match:
        attrs = attrs[: class_match.start()] + class_attr + attrs[class_match.end() :]
    else:
        attrs = f" {class_attr}{attrs}"
    return page[: match.start()] + f"<body{attrs}>" + page[match.end() :]


def asset_href(page_path: Path, web_root: Path, asset: str, asset_version: str) -> str:
    static_dir = web_root / "static"
    rel = os.path.relpath(static_dir, page_path.parent).replace(os.sep, "/")
    suffix = f"?v={asset_version}" if asset_version else ""
    return f"{rel}/{asset}{suffix}"


def shell_asset_tags(page_path: Path, web_root: Path, asset_version: str) -> str:
    header = asset_href(page_path, web_root, HEADER_ASSET, asset_version)
    footer = asset_href(page_path, web_root, FOOTER_ASSET, asset_version)
    script = asset_href(page_path, web_root, HEADER_SCRIPT_ASSET, asset_version)
    return (
        f'    <link rel="stylesheet" href="{header}" data-shell-authority="wordpress-personal-v4" />\n'
        f'    <link rel="stylesheet" href="{footer}" data-shell-authority="wordpress-personal-v4" />\n'
        f'    <script src="{script}" data-shell-authority="wordpress-personal-v4" defer></script>\n'
    )


def validate_canonical_sources(header: str, footer_inner: str, manifest: dict[str, object]) -> None:
    errors: list[str] = []
    expected_header = manifest["header"]["sha256"]
    expected_footer = manifest["footer"]["sha256"]
    if sha256_text(header) != expected_header:
        errors.append("header source hash mismatch")
    if sha256_text(footer_inner) != expected_footer:
        errors.append("footer source hash mismatch")
    if any(marker not in footer_inner for marker in REQUIRED_FOOTER_MARKERS):
        errors.append("footer missing five-column/CTA/social contract marker")
    if any(marker in footer_inner for marker in FORBIDDEN_FOOTER_MARKERS):
        errors.append("compact Personal/Research registry footer is forbidden")
    if footer_inner.count("<nav ") != 4:
        errors.append(f"footer nav count={footer_inner.count('<nav ')} expected=4")
    action_count = footer_inner.count('class="ay-button')
    if action_count != 3:
        errors.append(f"footer action count={action_count} expected=3")
    if footer_inner.count('class="ay-footer-socials"') != 1:
        errors.append("footer social block count must be 1")
    if errors:
        raise ValueError("; ".join(errors))


def tracked_hashes(release_root: Path) -> dict[str, str]:
    candidates = [
        release_root / "web" / "sitemap.xml",
        release_root / "public-data" / "tiktok" / "manifest.json",
        release_root / "public-data" / "tiktok" / "documents.jsonl",
        release_root / "public-data" / "tiktok" / "passages.jsonl",
    ]
    return {str(path.relative_to(release_root)): sha256_file(path) for path in candidates if path.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--expected-pages", type=int, default=0)
    parser.add_argument("--asset-version", default="")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    release_root = args.release_root.resolve()
    web_root = release_root / "web"
    static_root = web_root / "static"
    report_path = args.report or (release_root / "wordpress-personal-shell-report.json")

    if not web_root.is_dir():
        raise SystemExit(f"missing release web root: {web_root}")

    header = HEADER_TEMPLATE.read_text(encoding="utf-8")
    footer_inner = FOOTER_TEMPLATE.read_text(encoding="utf-8")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    validate_canonical_sources(header, footer_inner, manifest)
    rendered_header = header.strip()
    rendered_footer = f'<footer class="ay-site-footer" aria-label="Site footer">\n{footer_inner.strip()}\n</footer>'

    static_root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HEADER_CSS, static_root / HEADER_ASSET)
    shutil.copyfile(FOOTER_CSS, static_root / FOOTER_ASSET)
    shutil.copyfile(HEADER_SCRIPT, static_root / HEADER_SCRIPT_ASSET)

    before_artifacts = tracked_hashes(release_root)
    failures: list[dict[str, object]] = []
    normalized = 0
    skipped_without_shell: list[str] = []
    body_fingerprints: dict[str, str] = {}

    for path in sorted(web_root.rglob("*.html")):
        relative = path.relative_to(web_root).as_posix()
        before = path.read_text(encoding="utf-8-sig")
        header_count = len(HEADER_RE.findall(before))
        footer_count = len(FOOTER_RE.findall(before))
        if header_count == 0 and footer_count == 0:
            skipped_without_shell.append(relative)
            continue
        if header_count not in (0, 1) or footer_count != 1:
            failures.append({"page": relative, "error": f"shell count header={header_count} footer={footer_count}"})
            continue

        before_content = content_fingerprint(before)
        before_head = head_signature(before)

        if header_count == 1:
            after = HEADER_RE.sub(rendered_header, before, count=1)
        elif BODY_OPEN_RE.search(before):
            after = BODY_OPEN_RE.sub(
                lambda match: f"{match.group(0)}\n{rendered_header}",
                before,
                count=1,
            )
        else:
            failures.append({"page": relative, "error": "missing body insertion point for canonical header"})
            continue
        after = FOOTER_RE.sub(rendered_footer, after, count=1)
        after = normalize_body_classes(after)
        after = SHELL_ASSET_RE.sub("\n", after)
        after = SHELL_SCRIPT_RE.sub("\n", after)
        after = LEGACY_SHELL_SCRIPT_RE.sub("\n", after)
        if "</head>" not in after:
            failures.append({"page": relative, "error": "missing </head>"})
            continue
        after = after.replace(
            "</head>",
            shell_asset_tags(path, web_root, args.asset_version) + "  </head>",
            1,
        )

        after_content = content_fingerprint(after)
        after_head = head_signature(after)
        if before_content != after_content:
            failures.append({"page": relative, "error": "body/content fingerprint changed outside shell"})
            continue
        if before_head != after_head:
            failures.append({"page": relative, "error": "title/canonical/robots/analytics head signature changed"})
            continue

        path.write_text(after, encoding="utf-8")
        normalized += 1
        body_fingerprints[relative] = before_content

    # Independent read-back of the final corpus.
    for path in sorted(web_root.rglob("*.html")):
        relative = path.relative_to(web_root).as_posix()
        page = path.read_text(encoding="utf-8-sig")
        if relative in skipped_without_shell:
            continue
        headers = HEADER_RE.findall(page)
        footers = FOOTER_RE.findall(page)
        if len(headers) != 1 or len(footers) != 1:
            failures.append({"page": relative, "error": "final shell missing or duplicated"})
            continue
        if canonical_markup(headers[0]) != canonical_markup(rendered_header):
            failures.append({"page": relative, "error": "final header markup divergence"})
        if canonical_markup(footers[0]) != canonical_markup(rendered_footer):
            failures.append({"page": relative, "error": "final footer markup divergence"})
        if shell_urls(headers[0]) != shell_urls(rendered_header):
            failures.append({"page": relative, "error": "final header URL contract divergence"})
        if shell_urls(footers[0]) != shell_urls(rendered_footer):
            failures.append({"page": relative, "error": "final footer URL contract divergence"})
        for marker in FORBIDDEN_FOOTER_MARKERS:
            if marker in footers[0]:
                failures.append({"page": relative, "error": f"forbidden footer marker: {marker}"})
        if page.count(HEADER_ASSET) != 1 or page.count(FOOTER_ASSET) != 1:
            failures.append({"page": relative, "error": "parity asset missing or duplicated"})
        if page.count(HEADER_SCRIPT_ASSET) != 1:
            failures.append({"page": relative, "error": "header interaction script missing or duplicated"})
        if LEGACY_SHELL_SCRIPT_RE.search(page):
            failures.append({"page": relative, "error": "legacy shell interaction script still present"})
        body_match = BODY_OPEN_RE.search(page)
        body_open = body_match.group(0) if body_match else ""
        for required in REQUIRED_BODY_CLASSES:
            if required not in body_open:
                failures.append({"page": relative, "error": f"missing body class {required}"})

    after_artifacts = tracked_hashes(release_root)
    if before_artifacts != after_artifacts:
        failures.append({"page": "<release>", "error": "sitemap/public dataset artifact hash changed"})
    if args.expected_pages and normalized != args.expected_pages:
        failures.append({"page": "<release>", "error": f"normalized={normalized} expected={args.expected_pages}"})

    report = {
        "contract": manifest["contract"],
        "release_root": str(release_root),
        "normalized_pages": normalized,
        "skipped_without_shell": skipped_without_shell,
        "expected_pages": args.expected_pages,
        "asset_version": args.asset_version,
        "sources": manifest,
        "assets": {
            HEADER_ASSET: sha256_file(static_root / HEADER_ASSET),
            FOOTER_ASSET: sha256_file(static_root / FOOTER_ASSET),
            HEADER_SCRIPT_ASSET: sha256_file(static_root / HEADER_SCRIPT_ASSET),
        },
        "preserved_artifacts": after_artifacts,
        "body_fingerprint_count": len(body_fingerprints),
        "failures": failures[:200],
        "failure_count": len(failures),
        "passed": not failures,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"normalized_pages": normalized, "skipped": len(skipped_without_shell), "failures": len(failures), "report": str(report_path)}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
