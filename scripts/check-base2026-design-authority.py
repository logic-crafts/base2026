#!/usr/bin/env python3
"""Fail closed when the Base2026 release regains a retired design authority."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-base2026-cloudflare-release.py"
WORKER = ROOT / "cloudflare" / "base2026-worker" / "src" / "index.ts"
CANONICAL = [
    ROOT / "templates" / "base2026-core.css",
    ROOT / "templates" / "base2026-startup-shell.css",
    ROOT / "templates" / "base2026-startup-header.html",
    ROOT / "templates" / "base2026-startup-footer.html",
    ROOT / "templates" / "base2026-startup-homepage.html",
    ROOT / "templates" / "base2026-startup-homepage.css",
]
FORBIDDEN = {
    "aggressorbulkit.online": "retired personal-site origin",
    "Get My Free Roadmap": "retired personal CTA",
    "/wp-admin/": "WordPress administration route",
    "#c84f07": "retired warm palette",
    "#d9730d": "retired warm palette",
    "#ef6b13": "retired warm palette",
    "#fffaf0": "retired warm canvas",
    "#ff5a36": "retired warm dynamic-page accent",
    "ay-alex-v4-static": "retired Alex V4 shell class",
}
REQUIRED_BUILDER_MARKERS = [
    '"templates" / "base2026-core.css"',
    '"templates" / "base2026-startup-header.html"',
    '"templates" / "base2026-startup-footer.html"',
    '"templates" / "base2026-startup-homepage.html"',
]
FORBIDDEN_BUILDER_MARKERS = [
    "normalize-wordpress-v4-shell-release",
    "templates/shared/alex-home-v4",
    "alex_v4_static_shell",
]


def check() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in [*CANONICAL, BUILDER, WORKER]:
        if not path.is_file():
            failures.append({"path": str(path.relative_to(ROOT)), "reason": "missing required authority file"})

    for path in CANONICAL:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker, reason in FORBIDDEN.items():
            if marker.lower() in text.lower():
                failures.append({"path": str(path.relative_to(ROOT)), "reason": f"{reason}: {marker}"})

    if BUILDER.is_file():
        text = BUILDER.read_text(encoding="utf-8")
        for marker in REQUIRED_BUILDER_MARKERS:
            if marker not in text:
                failures.append({"path": str(BUILDER.relative_to(ROOT)), "reason": f"missing canonical marker: {marker}"})
        for marker in FORBIDDEN_BUILDER_MARKERS:
            if marker in text:
                failures.append({"path": str(BUILDER.relative_to(ROOT)), "reason": f"active legacy design dependency: {marker}"})

    if WORKER.is_file():
        text = WORKER.read_text(encoding="utf-8")
        if '/static/base2026-core.css?v=20260820-b26v1' not in text:
            failures.append({"path": str(WORKER.relative_to(ROOT)), "reason": "dynamic source page does not load Base2026 core CSS"})
        if "#ff5a36" in text:
            failures.append({"path": str(WORKER.relative_to(ROOT)), "reason": "dynamic source page retains warm legacy accent"})

    return failures


def main() -> int:
    failures = check()
    print(json.dumps({"schema": "base2026.design-authority-check/v1", "ok": not failures, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
