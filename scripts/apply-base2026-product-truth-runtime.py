#!/usr/bin/env python3
"""Make the Base2026 Product Truth runtime a release-level invariant.

This deliberately changes only script order on the canonical Search workspace
and data attributes/runtime references on already-approved Solution pages. It
does not touch page copy, metadata, robots, canonicals, sitemap files, or
public data. `--check-only` makes the same invariant release-blocking without
rewriting a protected input.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PURIFY = "purify.min.js"
MEILI = "meili.js"
RUNTIME = "base2026-solution-journey.js"


def source_name(src: str) -> str:
    return Path(urlsplit(src).path).name


def script_sources(html: str) -> list[tuple[str, int]]:
    return [
        (source_name(match.group(1)), match.start())
        for match in re.finditer(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>\s*</script>', html, re.I)
    ]


def replace_search_runtime(html: str) -> str:
    """Normalize the three required local scripts around the canonical Meili runtime."""
    script_pattern = re.compile(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>\s*</script>\s*\n?', re.I)
    scripts = list(script_pattern.finditer(html))
    meili = [match for match in scripts if source_name(match.group(1)) == MEILI]
    if len(meili) != 1:
        raise ValueError(f"Search workspace must contain exactly one {MEILI} script; found {len(meili)}")

    # Rebuild only the script tags that were removed, preserving all unrelated
    # page content. Insert immediately before the one Meili tag so DOMPurify is
    # defined before the safe renderer and the Product Truth listeners attach
    # after it has registered its search-results event.
    stripped = html
    for match in reversed(scripts):
        if source_name(match.group(1)) in {PURIFY, RUNTIME}:
            stripped = stripped[:match.start()] + stripped[match.end():]
    meili_match = re.search(
        r'(?P<indent>[ \t]*)<script\b[^>]*\bsrc=["\'](?P<src>[^"\']*meili\.js)'
        r'(?:\?[^"\']*)?["\'][^>]*>\s*</script>(?:\r?\n[ \t]*)?',
        stripped,
        re.I,
    )
    if not meili_match:
        raise ValueError(f"Could not locate the canonical {MEILI} script after normalization")
    indent = meili_match.group("indent")
    meili_src = meili_match.group("src")
    static_prefix = meili_src.rsplit("/", 1)[0] if "/" in meili_src else "./static"
    block = (
        f'{indent}<script src="{static_prefix}/{PURIFY}?v=product-truth"></script>\n'
        f'{indent}<script src="{meili_src}?v=product-truth"></script>\n'
        f'{indent}<script src="{static_prefix}/{RUNTIME}?v=product-truth"></script>'
    )
    return stripped[:meili_match.start()] + block + stripped[meili_match.end():]


def bridge_pattern(solution_id: str) -> re.Pattern[str]:
    escaped = re.escape(solution_id)
    return re.compile(
        rf'(?P<attrs><a\b[^>]*\bhref=["\'][^"\']*apply-research\.html\?solution={escaped}["\'][^>]*)>',
        re.I,
    )


def replace_solution_bridge(html: str, solution_id: str) -> str:
    pattern = bridge_pattern(solution_id)
    matches = list(pattern.finditer(html))
    if len(matches) != 1:
        raise ValueError(f"Solution {solution_id} must contain exactly one matching Apply Research link; found {len(matches)}")
    match = matches[0]
    attrs = re.sub(r'\sdata-research-bridge=["\'][^"\']*["\']', "", match.group("attrs"), flags=re.I)
    attrs = re.sub(r'\sdata-origin-id=["\'][^"\']*["\']', "", attrs, flags=re.I)
    replacement = (
        f'{attrs} data-research-bridge="solution_to_apply_research" '
        f'data-origin-id="{solution_id}">'
    )
    html = html[:match.start()] + replacement + html[match.end():]
    sources = script_sources(html)
    runtime_count = sum(name == RUNTIME for name, _ in sources)
    if runtime_count > 1:
        raise ValueError(f"Solution {solution_id} includes {RUNTIME} more than once")
    if runtime_count == 0:
        if "</body>" not in html.lower():
            raise ValueError(f"Solution {solution_id} has no closing body tag for runtime injection")
        html = re.sub(
            r'</body>',
            f'<script src="../static/{RUNTIME}?v=product-truth"></script>\n</body>',
            html,
            count=1,
            flags=re.I,
        )
    return html


def check_search_runtime(html: str) -> list[str]:
    sources = script_sources(html)
    positions: dict[str, list[int]] = {name: [offset for candidate, offset in sources if candidate == name] for name in (PURIFY, MEILI, RUNTIME)}
    errors = [f"search:{name}:count={len(offsets)}" for name, offsets in positions.items() if len(offsets) != 1]
    if not errors and not (positions[PURIFY][0] < positions[MEILI][0] < positions[RUNTIME][0]):
        errors.append("search:runtime_order_invalid")
    return errors


def check_solution_bridge(html: str, solution_id: str) -> list[str]:
    marker = 'data-research-bridge="solution_to_apply_research"'
    errors: list[str] = []
    if html.count(marker) != 1:
        errors.append(f"solution:{solution_id}:bridge_count={html.count(marker)}")
    if f'data-origin-id="{solution_id}"' not in html:
        errors.append(f"solution:{solution_id}:origin_id_missing")
    runtime_count = sum(name == RUNTIME for name, _ in script_sources(html))
    if runtime_count != 1:
        errors.append(f"solution:{solution_id}:runtime_count={runtime_count}")
    return errors


def solution_ids(contract_path: Path) -> list[str]:
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "base2026.approved-solution-ids/v1":
        raise ValueError("Unexpected approved Solution contract schema")
    ids = [str(row.get("id", "")) for row in payload.get("solutions", [])]
    if not ids or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item) for item in ids):
        raise ValueError("Approved Solution contract contains an invalid ID")
    return ids


def apply_runtime_contract(web_root: Path, ids: list[str], check_only: bool) -> dict[str, object]:
    root = web_root.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise ValueError(f"Search workspace is missing: {index}")
    changed: list[str] = []
    if not check_only:
        normalized = replace_search_runtime(index.read_text(encoding="utf-8"))
        if normalized != index.read_text(encoding="utf-8"):
            index.write_text(normalized, encoding="utf-8")
            changed.append("index.html")
        for solution_id in ids:
            path = root / "solutions" / f"{solution_id}.html"
            if not path.is_file():
                raise ValueError(f"Approved Solution page is missing: {path}")
            before = path.read_text(encoding="utf-8")
            after = replace_solution_bridge(before, solution_id)
            if after != before:
                path.write_text(after, encoding="utf-8")
                changed.append(path.relative_to(root).as_posix())

    errors = check_search_runtime(index.read_text(encoding="utf-8"))
    for solution_id in ids:
        path = root / "solutions" / f"{solution_id}.html"
        if not path.is_file():
            errors.append(f"solution:{solution_id}:missing")
            continue
        errors.extend(check_solution_bridge(path.read_text(encoding="utf-8"), solution_id))
    if errors:
        raise ValueError("; ".join(errors))
    return {"web_root": str(root), "approved_solution_count": len(ids), "changed": changed, "status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", required=True)
    parser.add_argument("--contract", default=str(ROOT / "contracts" / "base2026-approved-solution-ids.json"))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    report = apply_runtime_contract(Path(args.web_root), solution_ids(Path(args.contract)), args.check_only)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
