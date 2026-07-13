#!/usr/bin/env python3
"""Fail-closed live contract gate for the immutable Source Detail v2 release."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlsplit

USER_AGENT = "Base2026ReleaseGate/1.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, timeout: int = 25, attempts: int = 2) -> tuple[int, bytes, str]:
    last_error = ""
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), response.read(), ""
        except urllib.error.HTTPError as exc:
            return int(exc.code), exc.read(), ""
        except Exception as exc:  # noqa: BLE001 - report exact network failure
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt + 1 < attempts:
                time.sleep(0.35 * (attempt + 1))
    return 0, b"", last_error


def expected_file(web_root: Path, relative_path: str) -> Path:
    path = (web_root / relative_path).resolve()
    if web_root.resolve() not in path.parents and path != web_root.resolve():
        raise ValueError(f"Unsafe relative path: {relative_path}")
    return path


def check_exact_route(base_url: str, web_root: Path, route: str) -> dict:
    local_path = expected_file(web_root, route)
    expected = local_path.read_bytes()
    status, body, error = fetch(urljoin(base_url, route))
    actual_hash = sha256_bytes(body) if body else ""
    expected_hash = sha256_bytes(expected)
    failures: list[str] = []
    if error:
        failures.append(error)
    if status != 200:
        failures.append(f"status={status}, expected=200")
    if status == 200 and actual_hash != expected_hash:
        failures.append(f"sha256={actual_hash}, expected={expected_hash}")
    return {
        "route": route,
        "status": status,
        "bytes": len(body),
        "actual_sha256": actual_hash,
        "expected_sha256": expected_hash,
        "failures": failures,
    }


def check_future_route(base_url: str, route: str) -> dict:
    status, body, error = fetch(urljoin(base_url, route))
    failures: list[str] = []
    if error:
        failures.append(error)
    if status != 404:
        failures.append(f"status={status}, expected=404")
    return {"route": route, "status": status, "bytes": len(body), "failures": failures}


def digest_route_hashes(results: list[dict], hash_key: str) -> str:
    payload = "\n".join(f"{item['route']}:{item.get(hash_key, '')}" for item in sorted(results, key=lambda item: item["route"]))
    return sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--web-root", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/") + "/"
    manifest_path = Path(args.manifest).resolve()
    web_root = Path(args.web_root).resolve()
    report_path = Path(args.report).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rendered = list(manifest["rendered"])
    future = list(manifest["future_private_not_emitted"])
    normal_routes = sorted(item["route"] for item in rendered if item["admission_state"] == "normal_public_card")
    archive_routes = sorted(item["route"] for item in rendered if item["admission_state"] == "provenance_archive_noindex")
    rendered_routes = sorted(item["route"] for item in rendered)

    missing_local = [route for route in rendered_routes if not expected_file(web_root, route).is_file()]
    future_emitted = [route for route in future if expected_file(web_root, route).exists()]
    if missing_local or future_emitted:
        raise SystemExit(f"Invalid local web root: missing={len(missing_local)}, future_emitted={len(future_emitted)}")

    sitemap_files = ["sitemap.xml"] + sorted(
        path.relative_to(web_root).as_posix() for path in (web_root / "sitemaps").glob("*.xml")
    )
    exact_targets = ["index.html", "sources/index.html"] + sitemap_files + rendered_routes
    for asset in manifest["asset_sha256"]:
        exact_targets.append(f"static/{asset}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        exact_results = list(executor.map(lambda route: check_exact_route(base_url, web_root, route), exact_targets))
        future_results = list(executor.map(lambda route: check_future_route(base_url, route), future))

    exact_failures = [item for item in exact_results if item["failures"]]
    future_failures = [item for item in future_results if item["failures"]]

    sitemap_results = {item["route"]: item for item in exact_results if item["route"] in sitemap_files}
    sitemap_routes: set[str] = set()
    sitemap_parse_error = ""
    if all(not sitemap_results[path]["failures"] for path in sitemap_files):
        try:
            # Every live sitemap byte stream already matched its immutable local file above.
            # Extracting <loc> text directly avoids invoking a general-purpose XML parser.
            for sitemap_file in sitemap_files:
                sitemap_body = expected_file(web_root, sitemap_file).read_bytes()
                for match in re.findall(rb"<loc>\s*(.*?)\s*</loc>", sitemap_body, flags=re.DOTALL):
                    loc = html.unescape(match.decode("utf-8").strip())
                    path = urlsplit(loc).path
                    if "/knowledge/" in path:
                        path = path.split("/knowledge/", 1)[1]
                    else:
                        path = path.lstrip("/")
                    if not path.startswith("sitemaps/") and path != "sitemap.xml":
                        sitemap_routes.add(path)
        except Exception as exc:  # noqa: BLE001
            sitemap_parse_error = f"{type(exc).__name__}: {exc}"

    expected_normal_routes = set(normal_routes)
    archive_route_set = set(archive_routes)
    forbidden_routes = set(future)
    sitemap_missing_normal = sorted(expected_normal_routes - sitemap_routes)
    sitemap_missing_archive = sorted(archive_route_set - sitemap_routes)
    sitemap_forbidden_present = sorted(forbidden_routes & sitemap_routes)
    sitemap_failures: list[str] = []
    if sitemap_parse_error:
        sitemap_failures.append(sitemap_parse_error)
    if sitemap_missing_normal:
        sitemap_failures.append(f"missing_normal={len(sitemap_missing_normal)}")
    if sitemap_missing_archive:
        sitemap_failures.append(f"missing_archive_noindex={len(sitemap_missing_archive)}")
    if sitemap_forbidden_present:
        sitemap_failures.append(f"future_private_present={len(sitemap_forbidden_present)}")

    failures = {
        "exact_route_or_hash": exact_failures,
        "future_404": future_failures,
        "sitemap": sitemap_failures,
    }
    passed = not exact_failures and not future_failures and not sitemap_failures
    report = {
        "schema": "base2026.source-detail-v2-live-contract-gate/v3",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": base_url,
        "manifest": str(manifest_path),
        "web_root": str(web_root),
        "coverage": {
            "exact_200_and_byte_hash": len(exact_results),
            "rendered_routes": len(rendered_routes),
            "normal_public": len(normal_routes),
            "archive_noindex": len(archive_routes),
            "future_private_404": len(future_results),
            "sitemap_urls": len(sitemap_routes),
        },
        "status_counts": {
            "exact": dict(Counter(str(item["status"]) for item in exact_results)),
            "future": dict(Counter(str(item["status"]) for item in future_results)),
        },
        "route_hash_digests": {
            "expected": digest_route_hashes(exact_results, "expected_sha256"),
            "actual": digest_route_hashes(exact_results, "actual_sha256"),
        },
        "sitemap": {
            "missing_normal_count": len(sitemap_missing_normal),
            "missing_normal_sample": sitemap_missing_normal[:20],
            "missing_archive_noindex_count": len(sitemap_missing_archive),
            "missing_archive_noindex_sample": sitemap_missing_archive[:20],
            "future_private_present_count": len(sitemap_forbidden_present),
            "future_private_present_sample": sitemap_forbidden_present[:20],
        },
        "failures": failures,
        "passed": passed,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"report={report_path}")
    print(f"exact_checks={len(exact_results)}")
    print(f"future_checks={len(future_results)}")
    print(f"failures={len(exact_failures) + len(future_failures) + len(sitemap_failures)}")
    print(f"passed={str(passed).lower()}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
