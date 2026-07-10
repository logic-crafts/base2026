#!/usr/bin/env python3
"""Prepare and optionally submit a safe IndexNow payload for Base2026/Alex URLs.

The script is intentionally conservative:
- fetches every candidate URL live before including it;
- includes only HTTP 200, indexable, self-canonical URLs;
- skips noindex pages, canonical mismatches, non-aggressorbulkit hosts, and duplicates;
- defaults to dry-run file output; network submission requires --submit and a real key.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_HOST = "aggressorbulkit.online"
USER_AGENT = "Base2026-IndexNow-Prep/1.0 (+https://aggressorbulkit.online/knowledge/)"


@dataclass
class UrlCheck:
    url: str
    status: int | None
    final_url: str | None
    canonical: str | None
    robots: str | None
    title: str | None
    eligible: bool
    reason: str


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    parsed = urllib.parse.urlsplit(raw)
    if not parsed.scheme:
        raw = "https://" + raw.lstrip("/")
        parsed = urllib.parse.urlsplit(raw)
    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    # Preserve trailing slash policy exactly except collapse empty path to '/'.
    return urllib.parse.urlunsplit((scheme, netloc, path, parsed.query, ""))


def canonical_equivalent(a: str, b: str) -> bool:
    def clean(u: str) -> str:
        p = urllib.parse.urlsplit(u.strip())
        scheme = p.scheme.lower() or "https"
        netloc = p.netloc.lower()
        path = p.path or "/"
        # Compare without fragments and query state; query URLs should be skipped separately.
        return urllib.parse.urlunsplit((scheme, netloc, path, "", ""))
    return clean(a) == clean(b)


def extract_attr(html: str, tag_pattern: str, attr: str) -> str | None:
    m = re.search(tag_pattern, html, flags=re.I | re.S)
    if not m:
        return None
    tag = m.group(0)
    am = re.search(rf"\b{re.escape(attr)}\s*=\s*['\"]([^'\"]+)['\"]", tag, flags=re.I)
    return am.group(1).strip() if am else None


def fetch_check(url: str, host: str, timeout: int = 15) -> UrlCheck:
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc.lower() != host.lower():
        return UrlCheck(url, None, None, None, None, None, False, "wrong_host")
    if parsed.query:
        return UrlCheck(url, None, None, None, None, None, False, "query_url_not_for_indexnow")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            final_url = resp.geturl()
            content_type = resp.headers.get("content-type", "")
            body = resp.read(512_000).decode("utf-8", "ignore") if "text/html" in content_type else ""
    except urllib.error.HTTPError as exc:
        return UrlCheck(url, int(exc.code), exc.geturl(), None, None, None, False, f"http_{exc.code}")
    except Exception as exc:  # noqa: BLE001 - report exact blocker in CSV/JSON
        return UrlCheck(url, None, None, None, None, None, False, f"fetch_error:{type(exc).__name__}:{exc}")

    title_match = re.search(r"<title>(.*?)</title>", body, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
    canonical = extract_attr(body, r"<link\b(?=[^>]*\brel\s*=\s*['\"]canonical['\"])[^>]*>", "href")
    robots = extract_attr(body, r"<meta\b(?=[^>]*\bname\s*=\s*['\"]robots['\"])[^>]*>", "content")

    if status != 200:
        return UrlCheck(url, status, final_url, canonical, robots, title, False, f"status_{status}")
    if final_url and not canonical_equivalent(url, final_url):
        return UrlCheck(url, status, final_url, canonical, robots, title, False, "redirect_or_final_url_mismatch")
    if robots and "noindex" in robots.lower():
        return UrlCheck(url, status, final_url, canonical, robots, title, False, "noindex")
    if not canonical:
        return UrlCheck(url, status, final_url, canonical, robots, title, False, "missing_canonical")
    if not canonical_equivalent(url, canonical):
        return UrlCheck(url, status, final_url, canonical, robots, title, False, "canonical_mismatch")
    return UrlCheck(url, status, final_url, canonical, robots, title, True, "eligible")


def read_urls(paths: Iterable[Path]) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix.lower() == ".csv":
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    continue
                url_field = "url" if "url" in reader.fieldnames else reader.fieldnames[0]
                for row in reader:
                    url = normalize_url(row.get(url_field, ""))
                    if url and url not in seen:
                        seen.add(url)
                        urls.append(url)
        else:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                url = normalize_url(line.split(",")[0])
                if url and url not in seen:
                    seen.add(url)
                    urls.append(url)
    return urls


def write_checks_csv(path: Path, checks: list[UrlCheck]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(checks[0]).keys()) if checks else ["url"])
        writer.writeheader()
        for check in checks:
            writer.writerow(asdict(check))


def submit_indexnow(payload: dict, endpoint: str) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return int(resp.status), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", "ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, help="CSV with url column or text file with one URL per line. Repeatable.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--key", default="", help="IndexNow key. Required only for --submit or full payload output.")
    parser.add_argument("--key-location", default="", help="Public URL of the IndexNow key file.")
    parser.add_argument("--out", default="output/indexnow/base2026-indexnow-payload.json")
    parser.add_argument("--checks-out", default="output/indexnow/base2026-indexnow-checks.csv")
    parser.add_argument("--endpoint", default="https://api.indexnow.org/IndexNow")
    parser.add_argument("--limit", type=int, default=0, help="Optional max URLs to process.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay between URL checks.")
    parser.add_argument("--submit", action="store_true", help="Actually submit to IndexNow. Dry-run by default.")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input]
    urls = read_urls(input_paths)
    if args.limit:
        urls = urls[: args.limit]
    if not urls:
        print("No URLs found", file=sys.stderr)
        return 2

    checks: list[UrlCheck] = []
    for i, url in enumerate(urls, 1):
        check = fetch_check(url, args.host)
        checks.append(check)
        print(f"[{i}/{len(urls)}] {url} -> {check.reason}")
        if args.sleep:
            time.sleep(args.sleep)

    eligible_urls = [c.url for c in checks if c.eligible]
    checks_out = Path(args.checks_out)
    write_checks_csv(checks_out, checks)

    payload = {
        "host": args.host,
        "key": args.key or "REPLACE_WITH_INDEXNOW_KEY",
        "keyLocation": args.key_location or f"https://{args.host}/REPLACE_WITH_INDEXNOW_KEY.txt",
        "urlList": eligible_urls,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "input_urls": len(urls),
        "eligible_urls": len(eligible_urls),
        "skipped_urls": len(urls) - len(eligible_urls),
        "payload": str(out),
        "checks": str(checks_out),
        "submitted": bool(args.submit),
    }, indent=2))

    if args.submit:
        if not args.key or "REPLACE" in payload["key"]:
            print("--submit requires --key", file=sys.stderr)
            return 2
        if not args.key_location or "REPLACE" in payload["keyLocation"]:
            print("--submit requires --key-location", file=sys.stderr)
            return 2
        status, body = submit_indexnow(payload, args.endpoint)
        print(json.dumps({"indexnow_status": status, "body": body}, indent=2))
        # IndexNow returns 200 for successful real-time submission and may return
        # 202 when the request is accepted for later processing.
        return 0 if status in {200, 202} else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
