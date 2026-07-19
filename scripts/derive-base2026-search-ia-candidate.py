#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


HEADER_APPLY_LINK = (
    '<a href="/knowledge/apply-research.html"><strong>Apply Research</strong>'
    '<span>Turn findings into visibility fixes.</span></a>'
)
DIRECT_PERSONAL_HANDOFFS = (
    '<a href="/ai-visibility-audit/">Check AI visibility</a>',
    '<a href="/ai-visibility-diagnostic-audit/">Diagnostic audit</a>',
)
MENU_TARGET_RULE = (
    "\n/* Base2026 Search IA review: the protected mobile control is a real 44px target. */\n"
    "@media(max-width:1024px){body.ay-alex-v4-static .ay-v2-menu-toggle{"
    "display:inline-flex!important;min-width:44px!important;min-height:44px!important;"
    "align-items:center;justify-content:center;padding:0 12px}}\n"
)

SEARCH_ENTRYPOINTS = frozenset({"index.html", "search.html", "search/index.html"})


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def tree_oracle(files: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative, payload in sorted(files):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def derive_entrypoint(source: str) -> tuple[str, int, int]:
    """Remove persistent/direct commercial links while preserving the Apply bridge."""
    count = source.count(HEADER_APPLY_LINK)
    if count > 1:
        raise ValueError("Search header Apply Research link contract drift")
    derived = source.replace(HEADER_APPLY_LINK, "", 1)
    if HEADER_APPLY_LINK in derived:
        raise ValueError("Search header Apply Research link remains")
    direct_removed = 0
    for handoff in DIRECT_PERSONAL_HANDOFFS:
        handoff_count = derived.count(handoff)
        if handoff_count > 1:
            raise ValueError("Search direct personal handoff contract drift")
        derived = derived.replace(handoff, "", 1)
        direct_removed += handoff_count
        if handoff in derived:
            raise ValueError("Search direct personal handoff remains")
    return derived, count, direct_removed


def derive_css(source: str) -> str:
    if MENU_TARGET_RULE.strip() in source:
        return source
    return source.rstrip() + MENU_TARGET_RULE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-label", default="accepted-search-snapshot")
    args = parser.parse_args()

    if args.out.exists():
        raise SystemExit("Search IA candidate output already exists")
    contract_path = Path(__file__).resolve().parents[1] / "contracts" / "base2026-search-protected-files.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    files = sorted(set(contract["files"]))
    source_entries: list[tuple[str, bytes]] = []
    candidate_entries: list[tuple[str, bytes]] = []
    persistent_apply_removed = 0
    direct_personal_handoffs_removed = 0
    args.out.mkdir(parents=True)
    for relative in files:
        source = args.source_root / relative
        target = args.out / relative
        if not source.is_file():
            raise SystemExit(f"protected Search source missing: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        source_entries.append((relative, raw))
        if relative in SEARCH_ENTRYPOINTS:
            derived, removed, handoffs_removed = derive_entrypoint(raw.decode("utf-8"))
            persistent_apply_removed += removed
            direct_personal_handoffs_removed += handoffs_removed
            output = derived.encode("utf-8")
            target.write_bytes(output)
        elif relative == "static/alex-v4-static-shell-p4-local.css":
            output = derive_css(raw.decode("utf-8")).encode("utf-8")
            target.write_bytes(output)
        else:
            shutil.copy2(source, target)
            output = raw
        candidate_entries.append((relative, output))

    if persistent_apply_removed != 1:
        raise SystemExit(
            "Search IA source drift: expected exactly one persistent header Apply Research link "
            f"across Search entrypoints, found {persistent_apply_removed}"
        )
    if direct_personal_handoffs_removed != len(DIRECT_PERSONAL_HANDOFFS):
        raise SystemExit(
            "Search IA source drift: expected exactly two direct personal audit handoffs "
            f"across Search entrypoints, found {direct_personal_handoffs_removed}"
        )

    manifest = {
        "schema": "base2026.search-ia-candidate/v1",
        "source_root": args.source_label,
        "protected_file_count": len(files),
        "source_oracle_sha256": tree_oracle(source_entries),
        "candidate_oracle_sha256": tree_oracle(candidate_entries),
        "changes": {
            "persistent_apply_research_header_links_removed": persistent_apply_removed,
            "direct_personal_audit_handoffs_removed": direct_personal_handoffs_removed,
            "apply_research_bridge_preserved": True,
            "mobile_menu_min_target_px": 44,
            "search_runtime_or_data_changed": False,
        },
        "files": {relative: sha256(payload) for relative, payload in candidate_entries},
    }
    (args.out / "search-ia-candidate.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"protected_files={len(files)} candidate_oracle_sha256={manifest['candidate_oracle_sha256']} "
        f"persistent_apply_removed={persistent_apply_removed} "
        f"direct_personal_handoffs_removed={direct_personal_handoffs_removed} menu_target_px=44"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
