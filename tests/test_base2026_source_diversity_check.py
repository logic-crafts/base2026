from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from test_build_base2026_cloudflare_release import builder


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "base2026-source-diversity-check.html"
STYLESHEET = ROOT / "templates" / "base2026-source-diversity-check.css"
SCRIPT = ROOT / "templates" / "base2026-source-diversity-check.js"


def run_source_diversity_runtime() -> dict:
    script = SCRIPT.read_text(encoding="utf-8")
    marker = "  let activeController = null;"
    injection = """  globalThis.__sourceDiversityTestApi = {
    parseInput,
    publicBoundaryIsSafe,
    unsafePublicMetadata,
    normalizeResolved,
    unresolvedRecord,
    buildSnapshot,
    markdownSnapshot,
    jsonSnapshot,
    normalizedOriginalUrl,
    safeOriginalUrl
  };
  return;
  let activeController = null;"""
    assert script.count(marker) == 1
    script = script.replace(marker, injection, 1)
    harness = f"""
const vm = require("node:vm");
const source = {json.dumps(script)};
const context = {{
  window: {{ location: {{ origin: "https://base2026.dev", search: "" }}, innerWidth: 1200 }},
  document: {{ querySelector: () => ({{ dataset: {{ mcpEndpoint: "/api/mcp" }}, querySelector: () => ({{}}) }}) }},
  URL,
  URLSearchParams,
  console
}};
context.globalThis = context;
vm.runInNewContext(source, context, {{ filename: "base2026-source-diversity-check.js" }});
const api = context.__sourceDiversityTestApi;
const boundary = {{
  access: "public_read_only",
  raw_captions: false,
  raw_asr: false,
  media_files: false,
  private_data: false,
  writes: false
}};
const parsed = api.parseInput("tiktok-video-1111111111, tiktok-video-1111111111 tiktok-video-2222222222 tiktok-video-3333333333 nope");
const recordOne = api.normalizeResolved({{
  found: true,
  public_boundary: boundary,
  public_policy: "excerpt_only",
  id: "tiktok-video-1111111111",
  source_id: "tiktok:alice:1111111111",
  video_id: "1111111111",
  creator: {{ handle: "@Alice", display_name: "Alice" }},
  source_url: "https://WWW.TikTok.com/@alice/video/1111111111/?utm_source=search#clip",
  source_page_url: "https://base2026.dev/sources/tiktok-video-1111111111",
  title: "<script>alert(1)</script> & pipe |",
  published_date: "2026-09-01"
}}, parsed.accepted[0]);
const recordTwo = api.normalizeResolved({{
  found: true,
  public_boundary: boundary,
  public_policy: "excerpt_only",
  id: "tiktok-video-2222222222",
  source_id: "tiktok:alice:2222222222",
  video_id: "2222222222",
  creator: {{ handle: "alice", display_name: "Alice" }},
  source_url: "https://tiktok.com/@alice/video/1111111111/?ref=copy",
  title: "Second record",
  published_date: "2026-09-02"
}}, parsed.accepted[1]);
const sourceParsed = api.parseInput("tiktok:alice:4444444444");
const sourceRecord = api.normalizeResolved({{
  found: true,
  public_boundary: boundary,
  public_policy: "excerpt_only",
  id: "tiktok-video-4444444444",
  source_id: "tiktok:alice:4444444444",
  video_id: "4444444444",
  creator: {{ handle: "@alice", display_name: "Alice" }},
  source_url: "https://www.tiktok.com/@alice/video/4444444444",
  source_page_url: "https://base2026.dev/sources/tiktok-video-4444444444",
  title: "Source ID lookup"
}}, sourceParsed.accepted[0]);
const unresolvedOutcome = {{ input: parsed.accepted[2], record: null, reason: "not_found_or_invalid" }};
const snapshot = api.buildSnapshot(parsed, [
  {{ input: parsed.accepted[0], record: recordOne, reason: "" }},
  {{ input: parsed.accepted[1], record: recordTwo, reason: "" }},
  unresolvedOutcome
]);
const unsafeBoundary = {{ ...boundary, raw_captions: true }};
console.log(JSON.stringify({{
  parsed,
  sourceParsed,
  sourceRecord,
  snapshot,
  markdown: api.markdownSnapshot(snapshot),
  json: api.jsonSnapshot(snapshot),
  normalized: api.normalizedOriginalUrl("https://WWW.TikTok.com//@Alice/video/1111111111/?utm_source=search#clip"),
  safeUrl: api.safeOriginalUrl("javascript:alert(1)"),
  boundarySafe: api.publicBoundaryIsSafe({{ public_boundary: boundary }}),
  boundaryUnsafe: api.publicBoundaryIsSafe({{ public_boundary: unsafeBoundary }}),
  metadataUnsafe: api.unsafePublicMetadata({{ public_boundary: boundary, full_transcript_public: true }})
}}));
"""
    result = subprocess.run(["node", "-e", harness], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_source_diversity_route_is_one_indexable_public_tool() -> None:
    page = TEMPLATE.read_text(encoding="utf-8")

    assert len(re.findall(r"<h1(?:\s|>)", page)) == 1
    assert '<title>Source Diversity Check | Base2026</title>' in page
    assert '<meta name="robots" content="index,follow">' in page
    assert '<link rel="canonical" href="https://base2026.dev/tools/source-diversity-check/">' in page
    assert 'data-mcp-endpoint="/api/mcp"' in page
    assert 'method="get"' in page
    assert 'maxlength="600"' in page
    assert page.count("<button") == page.count('type="submit"') + page.count('type="button"')
    assert 'aria-live="polite"' in page
    assert "Markdown" in page and "JSON" in page
    assert "Diversity is not consensus or truth" in page
    assert "normalized original-source URL" in page
    assert "raw-transcript" in page
    assert "Search Console" in page
    assert "LLM verdict" in page
    assert page.count('href="/tools/evidence-search/"') >= 1
    assert 'href="/tools/source-backed-brief/' not in page

    payloads = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.DOTALL)
    structured_types = {json.loads(payload)["@type"] for payload in payloads}
    assert structured_types == {"WebApplication", "BreadcrumbList"}
    assert "aggregateRating" not in page


def test_source_diversity_runtime_uses_bounded_public_record_contract() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'const MCP_PROTOCOL_VERSION = "2026-07-28";' in script
    assert 'const MAX_RECORD_IDS = 12;' in script
    assert 'method: "POST"' in script
    assert 'credentials: "omit"' in script
    assert 'name: "get_source"' in script
    assert 'arguments: { source_id: input.lookupId }' in script
    assert "tiktok-video-(\\d{10,30})" in script
    assert "function canonicalSourceId(value)" in script
    assert 'inputKind: "record_id"' in script
    assert 'inputKind: "source_id"' in script
    assert 'sourceIdCount: accepted.filter' in script
    assert "normalized_original_source_url" in script
    assert "distinct_records" in script
    assert "distinct_sources" in script
    assert "distinct_creators" in script
    assert "unresolved_lookups" in script
    assert "base2026.source-diversity-check.v1" in script
    assert '"source_check_run"' in script
    assert '"completed"' in script
    assert '"decision_recorded"' in script
    assert '"card_copied"' in script
    assert 'emitAnalytics("completed"' in script
    assert 'emitAnalytics("decision_recorded"' in script
    assert 'emitAnalytics("card_copied"' in script
    assert "downloadText" in script
    assert "markdownSnapshot" in script
    assert "jsonSnapshot" in script
    assert ".replace(/[<>]/gu" in script
    assert 'target = "_blank"' in script
    assert 'rel = "noopener noreferrer"' in script
    assert "innerHTML" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "Authorization" not in script
    assert "raw_transcript" not in script
    assert "passages" not in script


def test_source_diversity_runtime_groups_exports_and_escapes_public_metadata() -> None:
    result = run_source_diversity_runtime()
    parsed = result["parsed"]
    snapshot = result["snapshot"]

    assert [entry["acceptedId"] for entry in parsed["accepted"]] == [
        "tiktok-video-1111111111",
        "tiktok-video-2222222222",
        "tiktok-video-3333333333",
    ]
    assert result["sourceParsed"]["accepted"][0]["inputKind"] == "source_id"
    assert result["sourceParsed"]["sourceIdCount"] == 1
    assert result["sourceRecord"]["record_id"] == "tiktok-video-4444444444"
    assert result["sourceRecord"]["source_id"] == "tiktok:alice:4444444444"
    assert parsed["duplicateCount"] == 1
    assert parsed["invalidCount"] == 1
    assert snapshot["status"] == "partial"
    assert snapshot["counts"] == {
        "submitted_ids": 3,
        "resolved_records": 2,
        "distinct_records": 3,
        "distinct_sources": 1,
        "distinct_creators": 1,
        "distinct_source_ids": 2,
        "unresolved_source_records": 1,
        "unresolved_creator_records": 1,
        "lookup_failures": 1,
    }
    assert [record["record_id"] for record in snapshot["records"]] == [
        "tiktok-video-1111111111",
        "tiktok-video-2222222222",
        "tiktok-video-3333333333",
    ]
    assert snapshot["records"][1]["base2026_url"] == "https://base2026.dev/sources/tiktok-video-2222222222"
    assert len(snapshot["groups"]["records"]) == 3
    assert len(snapshot["groups"]["creators"]) == 2
    assert len(snapshot["groups"]["original_source_urls"]) == 2
    assert snapshot["unresolved_lookups"] == [{"id": "tiktok-video-3333333333", "reason": "not_found_or_invalid"}]
    assert result["normalized"] == "https://tiktok.com/@Alice/video/1111111111"
    assert result["safeUrl"] == ""
    assert result["boundarySafe"] is True
    assert result["boundaryUnsafe"] is False
    assert result["metadataUnsafe"] is True

    markdown = result["markdown"]
    assert markdown == result["markdown"]
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; pipe \\|" in markdown
    assert "<script>" not in markdown
    assert "tiktok-video-3333333333" in markdown
    assert "## Unresolved lookups" in markdown
    assert "tiktok-video-3333333333 — not_found_or_invalid" in markdown
    assert "Base2026 record: <https://base2026.dev/sources/tiktok-video-3333333333>" not in markdown
    assert result["json"].endswith("\n")
    exported = json.loads(result["json"])
    assert exported["counts"] == snapshot["counts"]
    assert exported["records"] == snapshot["records"]


def test_source_diversity_styles_stay_inside_current_design_system() -> None:
    css = STYLESHEET.read_text(encoding="utf-8")

    assert "var(--b26-canvas)" in css
    assert "var(--b26-surface)" in css
    assert "var(--b26-accent)" in css
    assert "@media (max-width: 640px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "grid-template-columns: minmax(0, 1fr)" in css
    assert ".b26-source-diversity" in css
    assert "#f" not in css.casefold().replace("#fff", "")


def test_source_diversity_has_only_the_intended_contextual_inbound_links() -> None:
    evidence_search = (ROOT / "templates" / "base2026-evidence-search.html").read_text(encoding="utf-8")
    honest_hub = (ROOT / "templates" / "base2026-ai-visibility-resources.html").read_text(encoding="utf-8")

    assert evidence_search.count('href="/tools/source-diversity-check/"') == 1
    assert honest_hub.count('href="/tools/source-diversity-check/"') == 1
    assert builder.HUB_SITEMAP_ROUTES.count("/tools/source-diversity-check/") == 1
