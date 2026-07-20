#!/usr/bin/env python3
"""Synchronize a reviewed global footer across a complete static release.

The source checkout deliberately contains only the maintained static families,
while a production release also carries admitted Source, Topic and Creator
documents. This release-stage tool makes the shared footer contract explicit
for that whole public corpus without touching document content or data.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.IGNORECASE | re.DOTALL)
NOINDEX_RE = re.compile(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^"\']*\bnoindex\b', re.IGNORECASE)
REDIRECT_RE = re.compile(r"location\.replace\(\s*['\"]/knowledge/", re.IGNORECASE)


def normalized_fragment(markup: str) -> str:
    """Compare the generated footer semantically without formatting churn."""

    return re.sub(r">\s+<", "><", markup.strip())


def is_noindex_search_redirect(source: str) -> bool:
    """Allow only the historic noindex `/knowledge/search` redirect shell."""

    return bool(NOINDEX_RE.search(source) and REDIRECT_RE.search(source))


def sync(web_root: Path, footer: str, *, check: bool = False) -> dict[str, int]:
    """Validate then optionally replace the unique footer on every HTML file."""

    all_html = sorted(web_root.rglob("*.html"))
    # macOS AppleDouble metadata can accompany a transfer as `._page.html`.
    # It is not public content and must neither be admitted nor block the real
    # release corpus.
    pages = [page for page in all_html if not page.name.startswith("._")]
    skipped_metadata = len(all_html) - len(pages)
    if not pages:
        raise ValueError(f"No HTML pages found below {web_root}")

    updates: list[tuple[Path, str]] = []
    invalid: list[str] = []
    skipped_redirects = 0
    for page in pages:
        # A small number of historical admitted documents carry legacy bytes in
        # otherwise valid HTML. Surrogate escaping preserves those bytes exactly
        # while allowing the structural footer replacement to stay UTF-8.
        source = page.read_text(encoding="utf-8", errors="surrogateescape")
        footer_count = len(FOOTER_RE.findall(source))
        if footer_count == 0 and is_noindex_search_redirect(source):
            skipped_redirects += 1
            continue
        if footer_count != 1:
            invalid.append(f"{page.relative_to(web_root)} ({footer_count} footers)")
            continue
        existing = FOOTER_RE.search(source)
        assert existing is not None  # count above is exactly one
        if normalized_fragment(existing.group(0)) != normalized_fragment(footer):
            updates.append((page, FOOTER_RE.sub(footer, source, count=1)))

    # Never write a partly normalized release. A malformed document is a hard
    # stop-gate so it can be admitted or repaired deliberately.
    if invalid:
        sample = ", ".join(invalid[:10])
        raise ValueError(f"Footer admission failed for {len(invalid)} page(s): {sample}")

    if not check:
        for page, rendered in updates:
            page.write_text(rendered, encoding="utf-8", errors="surrogateescape")

    return {
        "pages": len(pages),
        "changed": len(updates),
        "invalid": 0,
        "skipped_metadata": skipped_metadata,
        "skipped_redirects": skipped_redirects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--footer-file", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Validate only; fail when any page drifts.")
    args = parser.parse_args()

    web_root = args.web_root.resolve()
    footer_file = args.footer_file.resolve()
    if not web_root.is_dir():
        parser.error(f"--web-root is not a directory: {web_root}")
    if not footer_file.is_file():
        parser.error(f"--footer-file is not a file: {footer_file}")
    footer = footer_file.read_text(encoding="utf-8").strip()
    if not footer.startswith("<footer") or 'data-footer-contract="personal-v1"' not in footer:
        parser.error("--footer-file must be the reviewed global personal footer contract")

    try:
        result = sync(web_root, footer, check=args.check)
    except ValueError as error:
        print(f"global_footer_release_sync=blocked reason={error}", file=sys.stderr)
        return 2

    if args.check and result["changed"]:
        print(
            "global_footer_release_sync=drift "
            f"pages={result['pages']} changed={result['changed']} invalid=0 "
            f"skipped_metadata={result['skipped_metadata']} skipped_redirects={result['skipped_redirects']}",
            file=sys.stderr,
        )
        return 3
    print(
        "global_footer_release_sync=ok "
        f"pages={result['pages']} changed={result['changed']} invalid=0 "
        f"skipped_metadata={result['skipped_metadata']} skipped_redirects={result['skipped_redirects']} "
        f"check={str(args.check).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
