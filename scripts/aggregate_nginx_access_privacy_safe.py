#!/usr/bin/env python3
"""Build privacy-safe daily aggregates from Nginx combined access logs.

The output deliberately contains no IP address, raw user-agent, raw referrer,
URL query string, request body, or source text. It is suitable for a retained
operational trend, not for user/session analytics.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


LINE = re.compile(
    r'^\S+ \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<target>\S+) [^"]*" '
    r"(?P<status>\d{3}) \S+ \"(?P<referrer>[^\"]*)\" \"(?P<ua>[^\"]*)\""
)
BOT_RE = re.compile(r"bot|spider|crawler|slurp|bingpreview|facebookexternalhit|uptime", re.I)
SEARCH_HOSTS = ("google.com", "bing.com", "duckduckgo.com", "yahoo.com", "yandex.ru", "yandex.com", "baidu.com")
AI_HOSTS = ("chatgpt.com", "openai.com", "perplexity.ai", "gemini.google.com", "claude.ai", "copilot.microsoft.com")
FIELDNAMES = (
    "date_utc",
    "site_segment",
    "route_family",
    "method_class",
    "status_class",
    "user_agent_class",
    "referrer_class",
    "requests",
)


def open_log(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="replace") if path.suffix == ".gz" else path.open(
        "r", encoding="utf-8", errors="replace"
    )


def route_bucket(path: str) -> tuple[str, str]:
    if path.startswith("/knowledge/") or path == "/knowledge":
        if path.rstrip("/") == "/knowledge":
            return "base", "search"
        for family in ("topics", "compare", "creators", "sources", "solutions"):
            if path.startswith(f"/knowledge/{family}/") or path == f"/knowledge/{family}":
                return "base", family
        if path.startswith("/knowledge/ai-visibility-pages"):
            return "base", "ai_visibility_lab"
        if path.startswith("/knowledge/apply-research"):
            return "base", "apply_research"
        return "base", "other"
    if path.startswith("/pricing"):
        return "personal", "pricing"
    if path.startswith("/services"):
        return "personal", "services"
    if path.startswith("/ai-visibility-audit"):
        return "personal", "audit"
    if path.startswith("/contact"):
        return "personal", "contact"
    return "personal", "other"


def referrer_bucket(raw_referrer: str) -> str:
    if not raw_referrer or raw_referrer == "-":
        return "direct_or_unknown"
    host = (urlsplit(raw_referrer).hostname or "").lower().rstrip(".")
    if host in {"aggressorbulkit.online", "www.aggressorbulkit.online"}:
        return "internal"
    if any(host == entry or host.endswith("." + entry) for entry in SEARCH_HOSTS):
        return "search"
    if any(host == entry or host.endswith("." + entry) for entry in AI_HOSTS):
        return "ai_assistant"
    return "other_referral"


def aggregate(paths: list[Path]) -> tuple[Counter[tuple[str, ...]], int, int]:
    counts: Counter[tuple[str, ...]] = Counter()
    parsed = 0
    rejected = 0
    for path in paths:
        with open_log(path) as handle:
            for line in handle:
                match = LINE.match(line)
                if not match:
                    rejected += 1
                    continue
                parsed += 1
                timestamp = datetime.strptime(match.group("timestamp"), "%d/%b/%Y:%H:%M:%S %z")
                path_only = urlsplit(match.group("target")).path or "/"
                segment, family = route_bucket(path_only)
                method = match.group("method")
                counts[
                    (
                        timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d"),
                        segment,
                        family,
                        "page_like" if method in {"GET", "HEAD"} else "other_method",
                        f"{match.group('status')[0]}xx",
                        "bot_heuristic" if BOT_RE.search(match.group("ua")) else "nonbot_heuristic",
                        referrer_bucket(match.group("referrer")),
                    )
                ] += 1
    return counts, parsed, rejected


def write_counts(path: Path, counts: Counter[tuple[str, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for key, value in sorted(counts.items()):
            writer.writerow(dict(zip(FIELDNAMES, (*key, value))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inputs = [path.resolve() for path in args.input]
    for path in inputs:
        if not path.is_file():
            parser.error(f"input log does not exist: {path}")
    counts, parsed, rejected = aggregate(inputs)
    write_counts(args.out.resolve(), counts)
    print(
        "privacy_safe_nginx_aggregate=ok "
        f"input_files={len(inputs)} parsed={parsed} rejected={rejected} output_rows={len(counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
