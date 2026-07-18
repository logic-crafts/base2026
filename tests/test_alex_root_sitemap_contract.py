from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from xml.etree import ElementTree


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "generate-alex-base2026-native-site.py"
SPEC = importlib.util.spec_from_file_location("generate_alex_root_site", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


EXPECTED_OBSERVED_CANDIDATE_ROUTES = {
    "/",
    "/ai-visibility-audit/",
    "/free-ai-visibility-snapshot/",
    "/sample-ai-visibility-snapshot/",
    "/services/",
    "/pricing/",
    "/ai-visibility-diagnostic-audit/",
    "/90-day-ai-search-visibility-sprint/",
    "/monthly-ai-visibility-growth/",
    "/technical-seo-geo-foundation/",
    "/answer-ready-service-pages/",
    "/entity-trust-source-intelligence/",
    "/ai-visibility-source-footprint/",
    "/what-is-ai-search-visibility/",
    "/why-chatgpt-does-not-recommend-your-business/",
    "/when-to-rebuild-website-for-seo/",
    "/ai-visibility-audit-for-dentists/",
    "/ai-visibility-audit-for-roofing-companies/",
    "/ai-visibility-audit-for-hvac-companies/",
    "/ai-visibility-audit-for-plumbing-companies/",
    "/ai-visibility-audit-for-law-firms/",
    "/about/",
    "/contact/",
    "/privacy-policy/",
}


def write_unapproved_contract(tmp_path: Path) -> Path:
    payload = json.loads(MODULE.ROOT_SITEMAP_CONTRACT.read_text(encoding="utf-8"))
    payload["source_registry"]["owner_approved"] = False
    payload["source_registry"]["production_change_authorized"] = False
    path = tmp_path / "unapproved-root-sitemap.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_root_sitemap_candidate_matches_observed_wordpress_indexable_union() -> None:
    routes = MODULE.load_root_sitemap_routes(allow_preview_candidate=True)
    paths = {item["path"] for item in routes}
    assert paths == EXPECTED_OBSERVED_CANDIDATE_ROUTES
    assert len(routes) == 24
    assert "/thank-you-ai-visibility-audit/" not in paths


def test_root_sitemap_candidate_has_digest_bound_public_shape() -> None:
    payload = json.loads(MODULE.ROOT_SITEMAP_CONTRACT.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "source_registry", "routes"}
    assert payload["schema"] == "alex-root-sitemap-routes/v2"
    source = payload["source_registry"]
    assert source["registry_id"] == "alex-personal-site-root-indexable-routes"
    assert source["canonical_owner"] == "alex-personal-site-wordpress"
    assert source["canonical_source_path"] == "contracts/alex-root-route-registry.json"
    assert len(source["source_sha256"]) == 64
    assert source["route_count"] == 24
    assert source["candidate_admission"] is True
    assert source["owner_approved"] is True
    assert source["production_change_authorized"] is True
    assert all(set(item) == {"path", "priority", "owner"} for item in payload["routes"])
    assert all(item["owner"] == "wordpress" for item in payload["routes"])


def test_owner_approved_contract_loads_without_preview_override() -> None:
    assert MODULE.load_root_sitemap_routes() == MODULE.load_root_sitemap_routes(
        allow_preview_candidate=True
    )


def test_unapproved_candidate_requires_explicit_preview_mode(tmp_path: Path) -> None:
    path = write_unapproved_contract(tmp_path)
    try:
        MODULE.load_root_sitemap_routes(path)
    except ValueError as error:
        assert "not owner-approved" in str(error)
    else:
        raise AssertionError("candidate root sitemap must fail closed without preview mode")
    assert len(MODULE.load_root_sitemap_routes(path, allow_preview_candidate=True)) == 24


def test_owner_gate_fails_before_output_mutation(tmp_path: Path) -> None:
    unapproved_contract = write_unapproved_contract(tmp_path)
    output = tmp_path / "existing-preview"
    output.mkdir()
    marker = output / "preserve.txt"
    marker.write_text("unchanged", encoding="utf-8")
    previous_out = MODULE.OUT
    previous_argv = sys.argv
    previous_loader = MODULE.load_root_sitemap_routes
    MODULE.OUT = output
    MODULE.load_root_sitemap_routes = lambda *, allow_preview_candidate=False: previous_loader(
        unapproved_contract,
        allow_preview_candidate=allow_preview_candidate,
    )
    sys.argv = [str(SCRIPT)]
    try:
        try:
            MODULE.main()
        except ValueError as error:
            assert "not owner-approved" in str(error)
        else:
            raise AssertionError("candidate generation must fail without owner approval")
    finally:
        MODULE.OUT = previous_out
        MODULE.load_root_sitemap_routes = previous_loader
        sys.argv = previous_argv
    assert marker.read_text(encoding="utf-8") == "unchanged"


def test_rendered_root_sitemap_is_exactly_the_candidate_mirror() -> None:
    routes = MODULE.load_root_sitemap_routes(allow_preview_candidate=True)
    xml = MODULE.render_root_sitemap(routes, lastmod="2026-07-17")
    root = ElementTree.fromstring(xml)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text for node in root.findall("sm:url/sm:loc", namespace)]
    assert locations == [MODULE.canonical(item["path"]) for item in routes]
    assert len(locations) == len(set(locations)) == 24


def test_root_sitemap_contract_rejects_unknown_keys_and_query_routes(tmp_path: Path) -> None:
    valid = json.loads(MODULE.ROOT_SITEMAP_CONTRACT.read_text(encoding="utf-8"))
    unknown = json.loads(json.dumps(valid))
    unknown["private_path"] = "/tmp/source"
    query_route = json.loads(json.dumps(valid))
    query_route["routes"][0]["path"] = "/pricing/?offer=snapshot"
    cases = [unknown, query_route]
    for index, payload in enumerate(cases):
        path = tmp_path / f"invalid-{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            MODULE.load_root_sitemap_routes(path, allow_preview_candidate=True)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid contract must fail closed: {payload}")
