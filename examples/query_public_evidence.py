#!/usr/bin/env python3
"""Query the public Base2026 evidence index with Python's standard library."""

from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen


ENDPOINT = "https://base2026.dev/api/search/multi-search"
INDEX = "base2026_public_tiktok"


def search(query: str, limit: int) -> dict:
    payload = json.dumps(
        {"queries": [{"indexUid": INDEX, "q": query, "limit": limit}]}
    ).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=payload,
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "Base2026-Public-Quickstart/1.0 (+https://base2026.dev/dataset)",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search Base2026's free public expert-video evidence index."
    )
    parser.add_argument("query", nargs="?", default="AI search visibility")
    parser.add_argument("--limit", type=int, default=5, choices=range(1, 21))
    args = parser.parse_args()
    print(json.dumps(search(args.query, args.limit), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
