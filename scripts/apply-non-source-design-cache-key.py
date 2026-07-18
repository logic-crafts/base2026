#!/usr/bin/env python3
"""Apply one cache-busting design key to every non-Source HTML consumer.

The overlay is deliberately byte-surgical: only the query value following
``alex-design-system-v2.css?v=`` may change. Source Detail pages retain their
independent renderer version and are verified but never rewritten.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from alex_design_system_v2 import NON_SOURCE_DESIGN_VERSION


DESIGN_QUERY_RE = re.compile(
    rb"(?P<prefix>alex-design-system-v2\.css\?v=)(?P<version>[^\"'&<>\s]+)"
)
NO_DESIGN_SYSTEM_ALLOWLIST = {
    "index.html",
    "search/index.html",
    "search.html",
}


def file_sha256(data: bytes) -> str:
    return sha256(data).hexdigest()


def ledger_sha256(changes: list[tuple[str, bytes, bytes]]) -> str:
    digest = sha256()
    for relative, before, after in sorted(changes, key=lambda row: row[0]):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(before).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_sha256(after).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def apply_overlay(
    web_root: Path,
    version: str = NON_SOURCE_DESIGN_VERSION,
    *,
    expected_html: int | None = None,
    expected_consumers: int | None = None,
    expected_source_consumers: int | None = None,
    check_only: bool = False,
) -> dict:
    root = web_root.resolve()
    if not (root / "index.html").is_file():
        raise ValueError("web root is missing index.html")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{3,95}", version):
        raise ValueError("invalid non-Source design version")

    html_paths = sorted(path for path in root.rglob("*.html") if path.is_file())
    changes: list[tuple[str, bytes, bytes]] = []
    issues: list[str] = []
    before_versions: Counter[str] = Counter()
    source_versions: Counter[str] = Counter()
    consumers = 0
    source_consumers = 0
    no_design_pages: list[str] = []

    for path in html_paths:
        relative = path.relative_to(root).as_posix()
        before = path.read_bytes()
        matches = list(DESIGN_QUERY_RE.finditer(before))
        is_source = relative.startswith("sources/")

        if is_source:
            if len(matches) != 1:
                issues.append(f"{relative}: source_design_consumer_count={len(matches)}")
                continue
            source_consumers += 1
            source_versions[matches[0].group("version").decode("ascii", "replace")] += 1
            continue

        if not matches:
            no_design_pages.append(relative)
            if relative not in NO_DESIGN_SYSTEM_ALLOWLIST:
                issues.append(f"{relative}: non_source_design_consumer_missing")
            continue
        if len(matches) != 1:
            issues.append(f"{relative}: non_source_design_consumer_count={len(matches)}")
            continue

        consumers += 1
        current = matches[0].group("version").decode("ascii", "replace")
        before_versions[current] += 1
        if current == version:
            continue
        after = DESIGN_QUERY_RE.sub(
            lambda match: match.group("prefix") + version.encode("ascii"),
            before,
            count=1,
        )
        if after == before:
            issues.append(f"{relative}: cache_key_rewrite_noop")
            continue
        changes.append((relative, before, after))

    if set(no_design_pages) != NO_DESIGN_SYSTEM_ALLOWLIST:
        issues.append(
            "non_source_no_design_allowlist_mismatch="
            + json.dumps(sorted(no_design_pages))
        )
    if expected_html is not None and len(html_paths) != expected_html:
        issues.append(f"html_count={len(html_paths)} expected={expected_html}")
    if expected_consumers is not None and consumers != expected_consumers:
        issues.append(f"consumer_count={consumers} expected={expected_consumers}")
    if expected_source_consumers is not None and source_consumers != expected_source_consumers:
        issues.append(
            f"source_consumer_count={source_consumers} expected={expected_source_consumers}"
        )
    if check_only and changes:
        issues.append(f"non_source_cache_key_mismatches={len(changes)}")
    if issues:
        raise ValueError("; ".join(issues))

    if not check_only:
        for relative, _before, after in changes:
            (root / relative).write_bytes(after)

    return {
        "schema": "base2026.non-source-design-cache-key-overlay/v1",
        "version": version,
        "html_pages": len(html_paths),
        "non_source_consumers": consumers,
        "source_consumers_preserved": source_consumers,
        "no_design_allowlist": sorted(no_design_pages),
        "before_versions": dict(sorted(before_versions.items())),
        "source_versions": dict(sorted(source_versions.items())),
        "updated": 0 if check_only else len(changes),
        "pending": len(changes),
        "change_ledger_sha256": ledger_sha256(changes),
        "query_only": True,
        "source_rewritten": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--version", default=NON_SOURCE_DESIGN_VERSION)
    parser.add_argument("--expected-html", type=int)
    parser.add_argument("--expected-consumers", type=int)
    parser.add_argument("--expected-source-consumers", type=int)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    try:
        report = apply_overlay(
            args.web_root,
            args.version,
            expected_html=args.expected_html,
            expected_consumers=args.expected_consumers,
            expected_source_consumers=args.expected_source_consumers,
            check_only=args.check_only,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, **report}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
