#!/usr/bin/env python3
"""Build or verify the Base preview mirror of the WordPress-owned root registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_KEYS = {
    "schema_version",
    "registry_id",
    "canonical_owner",
    "canonical_owner_repository",
    "canonical_source_path",
    "scope",
    "base2026_scope_excluded",
    "observed_at",
    "observation",
    "admission_contract",
    "routes",
}
ROUTE_KEYS = {
    "path",
    "content_type",
    "family",
    "sitemap_priority",
    "approved",
    "candidate_admission",
    "observed_in_live_wordpress_sitemap",
    "owner_approved",
    "expected_status",
    "expected_indexable",
    "expected_self_canonical",
    "admission_evidence",
}


def _priority(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("sitemap_priority must be numeric")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid sitemap_priority: {value!r}") from exc
    if not 0 <= numeric <= 1:
        raise ValueError(f"sitemap_priority outside 0..1: {numeric}")
    rendered = f"{numeric:.2f}".rstrip("0")
    return rendered + "0" if rendered.endswith(".") else rendered


def build_mirror(registry_path: Path) -> dict[str, Any]:
    source = registry_path.read_bytes()
    payload = json.loads(source.decode("utf-8"))
    if set(payload) != REGISTRY_KEYS:
        raise ValueError(f"unexpected registry keys: {sorted(set(payload) ^ REGISTRY_KEYS)}")
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported root registry schema")
    if payload.get("registry_id") != "alex-personal-site-root-indexable-routes":
        raise ValueError("unexpected root registry ID")
    if payload.get("canonical_owner") != "alex-personal-site-wordpress":
        raise ValueError("root registry owner must be WordPress")
    if payload.get("canonical_source_path") != "contracts/alex-root-route-registry.json":
        raise ValueError("root registry must expose only its repository-relative source path")
    if payload.get("scope") != "root-site-only" or payload.get("base2026_scope_excluded") != "/knowledge/":
        raise ValueError("root registry scope overlaps Base2026")

    admission = payload.get("admission_contract")
    if not isinstance(admission, dict):
        raise ValueError("root registry admission contract is missing")
    candidate = admission.get("candidate_admission") is True
    owner_approved = admission.get("owner_approved") is True
    production_authorized = admission.get("production_change_authorized") is True
    approved = admission.get("approved") is True
    if not candidate:
        raise ValueError("root registry is not an observed candidate")
    if approved != owner_approved or approved != production_authorized:
        raise ValueError("approval and production authorization must transition atomically")

    routes: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in payload.get("routes") or []:
        if not isinstance(item, dict) or set(item) != ROUTE_KEYS:
            raise ValueError(f"unexpected root registry route keys: {sorted(set(item) ^ ROUTE_KEYS) if isinstance(item, dict) else item!r}")
        route = item.get("path")
        if (
            not isinstance(route, str)
            or not route.startswith("/")
            or route.startswith("//")
            or (route != "/" and not route.endswith("/"))
            or route.startswith("/knowledge/")
            or "?" in route
            or "#" in route
            or route in seen
        ):
            raise ValueError(f"invalid or duplicate root route: {route!r}")
        if item.get("candidate_admission") is not True or item.get("observed_in_live_wordpress_sitemap") is not True:
            raise ValueError(f"route is not an observed candidate: {route}")
        if item.get("approved") is not approved or item.get("owner_approved") is not owner_approved:
            raise ValueError(f"route approval state drifts from registry: {route}")
        if item.get("expected_status") != 200 or item.get("expected_indexable") is not True:
            raise ValueError(f"route fails expected sitemap semantics: {route}")
        canonical = "https://aggressorbulkit.online/" if route == "/" else f"https://aggressorbulkit.online{route}"
        if item.get("expected_self_canonical") != canonical:
            raise ValueError(f"route self-canonical expectation drifted: {route}")
        seen.add(route)
        routes.append({"path": route, "priority": _priority(item.get("sitemap_priority")), "owner": "wordpress"})

    if len(routes) != 24:
        raise ValueError(f"expected 24 observed root candidates, found {len(routes)}")
    return {
        "schema": "alex-root-sitemap-routes/v2",
        "source_registry": {
            "registry_id": payload["registry_id"],
            "schema_version": payload["schema_version"],
            "canonical_owner": payload["canonical_owner"],
            "canonical_source_path": payload["canonical_source_path"],
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "observed_at": payload["observed_at"],
            "route_count": len(routes),
            "candidate_admission": candidate,
            "owner_approved": owner_approved,
            "production_change_authorized": production_authorized,
        },
        "routes": routes,
    }


def render(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(build_mirror(args.registry))
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != expected:
            raise SystemExit("root sitemap mirror differs from the canonical registry")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(expected, encoding="utf-8")
    mirrored = json.loads(expected)
    source = mirrored["source_registry"]
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "check" if args.check else "write",
                "route_count": source["route_count"],
                "source_sha256": source["source_sha256"],
                "owner_approved": source["owner_approved"],
                "production_change_authorized": source["production_change_authorized"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
