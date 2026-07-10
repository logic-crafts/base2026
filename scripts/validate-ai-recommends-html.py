from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.links: list[str] = []
        self.assets: list[str] = []
        self.robots = ""
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag in {"link", "script", "img"}:
            url = values.get("href") or values.get("src")
            if url:
                self.assets.append(url)
        if tag == "meta" and values.get("name") == "robots":
            self.robots = values.get("content") or ""
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href") or ""


def fetch_status(url: str) -> tuple[int, str, int]:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read()
        return response.status, response.headers.get_content_type(), len(body)


def local_target(out: Path, page: Path, href: str) -> Path | None:
    clean = urllib.parse.urlparse(href)
    if clean.scheme or href.startswith("mailto:") or href.startswith("#"):
        return None
    path = clean.path
    if path.startswith("/knowledge/"):
        relative = path[len("/knowledge/") :]
        target = out / relative
    elif path == "/knowledge" or path == "/knowledge/":
        target = out / "index.html"
    elif path.startswith("/"):
        return None
    else:
        target = (page.parent / path).resolve()
    if target.is_dir() or str(target).endswith("/"):
        target = target / "index.html"
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Base2026 AI Recommends HTML.")
    parser.add_argument("--out", type=Path, default=Path("web/static"))
    parser.add_argument("--generation-report", type=Path, default=Path(".planning/tiktok-pipeline-v2/ai-recommends-solutions-generation.json"))
    parser.add_argument("--preview-base", default="")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    generation = json.loads(args.generation_report.read_text(encoding="utf-8"))
    pages = [args.out / "solutions" / "index.html"] + [args.out / path for path in generation["solution_urls"]]
    errors: list[str] = []
    page_reports: list[dict[str, object]] = []

    for page in pages:
        relative = page.relative_to(args.out).as_posix()
        if not page.exists():
            errors.append(f"missing page: {relative}")
            continue
        text = page.read_text(encoding="utf-8")
        html = PageParser()
        html.feed(text)
        page_errors: list[str] = []
        if html.h1_count != 1:
            page_errors.append(f"expected one h1, got {html.h1_count}")
        if html.robots != "index,follow":
            page_errors.append(f"expected index,follow, got {html.robots!r}")
        if not html.canonical.startswith("https://aggressorbulkit.online/knowledge/solutions"):
            page_errors.append(f"unexpected canonical: {html.canonical}")
        if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
            page_errors.append("placeholder marker present")

        checked_internal = 0
        for href in html.links:
            target = local_target(args.out.resolve(), page.resolve(), href)
            if target is None:
                continue
            checked_internal += 1
            if not target.exists():
                page_errors.append(f"broken internal link: {href} -> {target}")

        preview_assets: list[dict[str, object]] = []
        if args.preview_base:
            page_url = urllib.parse.urljoin(args.preview_base.rstrip("/") + "/", relative)
            for asset in html.assets:
                if asset.startswith("http://") or asset.startswith("https://") or asset.startswith("data:"):
                    continue
                url = urllib.parse.urljoin(page_url, asset)
                try:
                    status, content_type, size = fetch_status(url)
                    preview_assets.append({"url": url, "status": status, "content_type": content_type, "bytes": size})
                    if status != 200 or size < 200:
                        page_errors.append(f"bad asset response: {status} {size} {url}")
                except (urllib.error.URLError, TimeoutError) as exc:
                    page_errors.append(f"asset request failed: {url}: {exc}")

        errors.extend(f"{relative}: {error}" for error in page_errors)
        page_reports.append({
            "page": relative,
            "ok": not page_errors,
            "h1_count": html.h1_count,
            "robots": html.robots,
            "canonical": html.canonical,
            "internal_links_checked": checked_internal,
            "preview_assets": preview_assets,
            "errors": page_errors,
        })

    report = {
        "ok": not errors,
        "page_count": len(pages),
        "pages_passed": sum(1 for row in page_reports if row["ok"]),
        "errors": errors,
        "pages": page_reports,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
