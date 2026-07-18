#!/usr/bin/env python3
"""Apply the shared Visual Reset V2 information architecture to a package.

Generators own page content. This bounded integration pass restores the accepted
page-local navigation, document rail and progressive disclosures after every
data-changing package build. The frozen Search root is deliberately excluded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from alex_design_system_v2 import apply_information_architecture


def apply_to_web_root(web_root: Path) -> dict[str, int]:
    root = web_root.resolve()
    if not root.is_dir() or not (root / "index.html").is_file():
        raise FileNotFoundError(f"Base2026 web root is incomplete: {root}")
    scanned = 0
    changed = 0
    for page in sorted(root.rglob("*.html")):
        route = page.relative_to(root).as_posix()
        if route == "index.html":
            continue
        scanned += 1
        source = page.read_text(encoding="utf-8")
        rendered = apply_information_architecture(source, route)
        if rendered != source:
            page.write_text(rendered, encoding="utf-8")
            changed += 1
    return {"scanned": scanned, "changed": changed, "search_root_changed": 0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", type=Path, required=True)
    result = apply_to_web_root(parser.parse_args().web_root)
    print(
        f"visual_reset_v2_scanned={result['scanned']} "
        f"changed={result['changed']} search_root_changed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
