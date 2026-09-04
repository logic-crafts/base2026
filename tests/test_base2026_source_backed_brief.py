from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from test_build_base2026_cloudflare_release import builder, write_fixture


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "base2026-source-backed-brief.html"
STYLESHEET = ROOT / "templates" / "base2026-source-backed-brief.css"
SCRIPT = ROOT / "templates" / "base2026-source-backed-brief.js"


def run_source_backed_brief_runtime() -> dict:
    script = SCRIPT.read_text(encoding="utf-8")
    marker = "  let activeController = null;"
    injection = """  globalThis.__sourceBackedBriefTestApi = {
    parseIds,
    publicBoundaryIsSafe,
    unsafePublicMetadata,
    normalizeResolved,
    unresolvedRecord,
    buildSnapshot,
    buildBriefSnapshot,
    markdownSnapshot,
    jsonSnapshot,
    safeOriginalUrl,
    safeBase2026Url
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
vm.runInNewContext(source, context, {{ filename: "base2026-source-backed-brief.js" }});
const api = context.__sourceBackedBriefTestApi;
const boundary = {{
  access: "public_read_only",
  raw_captions: false,
  raw_asr: false,
  media_files: false,
  private_data: false,
  writes: false
}};
const parsed = api.parseIds([
  "tiktok-video-1111111111",
  "tiktok:alice:2222222222",
  "tiktok-video-3333333333",
  "tiktok-video-4444444444",
  "tiktok-video-5555555555",
  "tiktok-video-6666666666",
  "tiktok-video-7777777777",
  "tiktok-video-8888888888",
  "tiktok-video-9999999999",
  "tiktok-video-1111111111",
  "javascript:alert(1)"
].join("\\n"));
const recordOne = api.normalizeResolved({{
  found: true,
  public_boundary: boundary,
  public_policy: "excerpt_only",
  id: "tiktok-video-1111111111",
  source_id: "tiktok:alice:1111111111",
  creator: {{ handle: "@Alice", display_name: "Alice", url: "https://www.tiktok.com/@alice" }},
  source_url: "https://www.tiktok.com/@alice/video/1111111111",
  source_page_url: "https://base2026.dev/sources/tiktok-video-1111111111",
  title: "<script>alert(1)</script> & pipe |",
  published_date: "2026-09-01",
  passages: [
    {{ id: "p1", chunk_index: 0, excerpt: "A bounded <script>alert(1)</script> excerpt & pipe |" }},
    {{ id: "p2", chunk_index: 1, excerpt: "A second public excerpt" }},
    {{ id: "p3", chunk_index: 2, excerpt: "A third public excerpt" }},
    {{ id: "p4", chunk_index: 3, excerpt: "This fourth excerpt must not be included" }}
  ]
}}, parsed.accepted[0]);
const recordTwo = api.normalizeResolved({{
  found: true,
  public_boundary: boundary,
  public_policy: "excerpt_only",
  id: "tiktok-video-2222222222",
  source_id: "tiktok:alice:2222222222",
  title: "Partial source record"
}}, parsed.accepted[1]);
const outcomes = parsed.accepted.map((input, index) => {{
  if (index === 0) return {{ input, record: recordOne, reason: "" }};
  if (index === 1) return {{ input, record: recordTwo, reason: "" }};
  return {{ input, record: null, reason: index === 2 ? "not_found" : "request" }};
}});
const snapshot = api.buildSnapshot(
  {{ question: "What does this evidence say?", audience: "Content team", deliverable: "memo" }},
  parsed,
  outcomes
);
const unsafeBoundary = {{ ...boundary, raw_captions: true }};
console.log(JSON.stringify({{
  parsed,
  snapshot,
  briefSnapshot: api.buildBriefSnapshot({{ question: "Q", audience: "A", deliverable: "outline" }}, parsed, outcomes),
  markdown: api.markdownSnapshot(snapshot),
  json: api.jsonSnapshot(snapshot),
  safeUrl: api.safeOriginalUrl("javascript:alert(1)"),
  safeBase: api.safeBase2026Url("https://base2026.dev/sources/tiktok-video-1111111111"),
  boundarySafe: api.publicBoundaryIsSafe({{ public_boundary: boundary }}),
  boundaryUnsafe: api.publicBoundaryIsSafe({{ public_boundary: unsafeBoundary }}),
  metadataUnsafe: api.unsafePublicMetadata({{ public_boundary: boundary, full_transcript_public: true }})
}}));
"""
    result = subprocess.run(["node", "-e", harness], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_source_backed_brief_route_is_one_indexable_public_tool() -> None:
    page = TEMPLATE.read_text(encoding="utf-8")

    assert len(re.findall(r"<h1(?:\s|>)", page)) == 1
    assert "<title>Source-backed Brief Builder | Base2026</title>" in page
    assert '<meta name="robots" content="index,follow">' in page
    assert '<link rel="canonical" href="https://base2026.dev/tools/source-backed-brief/">' in page
    assert 'data-mcp-endpoint="/api/mcp"' in page
    assert 'action="/tools/source-backed-brief/"' in page
    assert 'name="question"' in page and 'name="audience"' in page
    assert 'name="deliverable"' in page and 'name="ids"' in page
    assert 'maxlength="240"' in page and 'maxlength="120"' in page
    assert 'maxlength="1200"' in page
    assert '<option value="brief">Brief</option>' in page
    assert '<option value="memo">Memo</option>' in page
    assert '<option value="outline">Outline</option>' in page
    assert page.count("<button") == page.count('type="submit"') + page.count('type="button"')
    assert "bounded public excerpts" in page.lower()
    assert "truth, consensus or independence" in page
    assert "unknowns" in page.lower()
    assert "Limitations" in page
    assert "Markdown" in page and "JSON" in page
    assert "the method, input limits and evidence boundaries are below" in page
    assert 'href="/tools/evidence-search/"' in page
    assert 'href="/tools/source-diversity-check/"' in page
    assert "raw-transcript" in page.lower()
    assert "private-data" in page
    assert "aggregateRating" not in page

    payloads = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.DOTALL)
    structured_types = {json.loads(payload)["@type"] for payload in payloads}
    assert structured_types == {"WebApplication", "BreadcrumbList"}


def test_source_backed_brief_runtime_uses_exact_bounded_public_contract() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'const MCP_PROTOCOL_VERSION = "2026-07-28";' in script
    assert "const MAX_RECORD_IDS = 8;" in script
    assert "const MAX_EXCERPT_CHARS = 360;" in script
    assert 'method: "POST"' in script
    assert 'credentials: "omit"' in script
    assert 'name: "get_source"' in script
    assert 'arguments: { source_id: input.lookupId }' in script
    assert '"brief_required_fields_completed"' in script
    assert '"brief_preview_created"' in script
    assert '"brief_exported"' in script
    assert '"brief_completed"' in script
    assert 'emitAnalytics("brief_required_fields_completed"' in script
    assert 'emitAnalytics("brief_preview_created"' in script
    assert 'emitAnalytics("brief_exported"' in script
    assert 'emitAnalytics("brief_completed"' in script
    assert '"base2026.source-backed-brief.v1"' in script
    assert "passages" in script
    assert "MAX_EXCERPTS_PER_RECORD" in script
    assert "publicBoundaryIsSafe" in script
    assert "truth_consensus_independence" in script
    assert "innerHTML" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "Authorization" not in script
    assert "raw_transcript" not in script
    assert "fetch(endpoint" in script
    assert 'method: "GET"' not in script


def test_source_backed_brief_runtime_caps_escapes_and_keeps_unresolved_records() -> None:
    result = run_source_backed_brief_runtime()
    parsed = result["parsed"]
    snapshot = result["snapshot"]

    assert len(parsed["accepted"]) == 8
    assert parsed["submittedIdCount"] == 8
    assert parsed["duplicateCount"] == 1
    assert parsed["invalidCount"] == 2
    assert parsed["sourceIdCount"] == 1
    assert parsed["recordIdCount"] == 7
    assert snapshot["schema"] == "base2026.source-backed-brief.v1"
    assert snapshot["status"] == "partial"
    assert snapshot["request"]["deliverable"] == "memo"
    assert snapshot["counts"] == {
        "submitted_ids": 8,
        "resolved_records": 2,
        "unresolved_records": 6,
        "distinct_records": 8,
        "bounded_excerpts": 3,
        "invalid_inputs": 2,
        "duplicate_inputs": 1,
    }
    assert [record["record_id"] for record in snapshot["records"]] == [
        "tiktok-video-1111111111",
        "tiktok-video-2222222222",
        "tiktok-video-3333333333",
        "tiktok-video-4444444444",
        "tiktok-video-5555555555",
        "tiktok-video-6666666666",
        "tiktok-video-7777777777",
        "tiktok-video-8888888888",
    ]
    assert snapshot["records"][0]["creator"]["handle"] == "@Alice"
    assert snapshot["records"][0]["original_source_url"].startswith("https://www.tiktok.com/")
    assert len(snapshot["records"][0]["excerpts"]) == 3
    assert snapshot["records"][1]["metadata_resolution"] == "partial"
    assert snapshot["records"][2]["lookup_status"] == "unresolved"
    assert snapshot["records"][2]["resolution_reason"] == "not_found"
    assert any(entry["record_id"] == "tiktok-video-3333333333" for entry in snapshot["unknowns"])
    assert any(entry["record_id"] is None for entry in snapshot["unknowns"])
    assert snapshot["contract"]["public_boundary"]["writes"] is False
    assert snapshot["contract"]["truth_consensus_independence"] == "not_assessed; no inference"
    assert result["briefSnapshot"]["request"]["deliverable"] == "outline"
    assert result["safeUrl"] == ""
    assert result["safeBase"].startswith("https://base2026.dev/sources/")
    assert result["boundarySafe"] is True
    assert result["boundaryUnsafe"] is False
    assert result["metadataUnsafe"] is True

    markdown = result["markdown"]
    assert "<script>" not in markdown
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in markdown
    assert "&amp; pipe \\|" in markdown
    assert "[Open original source](<https://www.tiktok.com/@alice/video/1111111111>)" in markdown
    assert "tiktok-video-3333333333" in markdown
    assert "## Unknowns" in markdown
    assert "## Limitations" in markdown
    decoded = json.loads(result["json"])
    assert decoded["schema"] == snapshot["schema"]
    assert decoded["counts"] == snapshot["counts"]


def test_source_backed_brief_stylesheet_observes_visual_and_accessibility_contract() -> None:
    stylesheet = STYLESHEET.read_text(encoding="utf-8")

    assert ".b26-source-backed-brief" in stylesheet
    assert "var(--b26-canvas)" in stylesheet
    assert "var(--b26-surface)" in stylesheet
    assert "@media (max-width: 640px)" in stylesheet
    assert "@media (prefers-reduced-motion: reduce)" in stylesheet
    assert "overflow-x" not in stylesheet
    assert "#" not in re.sub(r"#[a-z][a-z0-9_-]*", "", stylesheet, flags=re.IGNORECASE)
    assert "warm" not in stylesheet.lower()


def test_source_backed_brief_builder_emits_route_assets_sitemap_and_public_llms_links(tmp_path: Path) -> None:
    source = tmp_path / "source-web"
    output = tmp_path / "release"
    write_fixture(source)

    receipt = builder.build_release(
        source,
        output,
        homepage_template=builder.DEFAULT_HOMEPAGE_TEMPLATE,
        homepage_stylesheet=builder.DEFAULT_HOMEPAGE_STYLESHEET,
    )

    page_path = output / "tools" / "source-backed-brief" / "index.html"
    stylesheet_path = output / "static" / "base2026-source-backed-brief.css"
    script_path = output / "static" / "base2026-source-backed-brief.js"
    assert page_path.is_file()
    assert stylesheet_path.read_bytes() == builder.DEFAULT_SOURCE_BACKED_BRIEF_STYLESHEET.read_bytes()
    assert script_path.read_bytes() == builder.DEFAULT_SOURCE_BACKED_BRIEF_SCRIPT.read_bytes()
    hub_sitemap = (output / builder.HUB_SITEMAP_FILENAME).read_text(encoding="utf-8")
    assert hub_sitemap.count("https://base2026.dev/tools/source-backed-brief/") == 1
    assert "https://base2026.dev/tools/source-backed-brief/" in (output / "root-llms.txt").read_text(encoding="utf-8")
    assert "https://base2026.dev/tools/source-backed-brief/" in (output / "llms.txt").read_text(encoding="utf-8")
    assert 'data-mcp-endpoint="/api/mcp"' in page_path.read_text(encoding="utf-8")
    assert receipt["verification"]["private_token_markers_remaining"] == 0


def test_source_backed_brief_internal_links_are_additive_and_source_diversity_is_unchanged() -> None:
    evidence_search = (ROOT / "templates" / "base2026-evidence-search.html").read_text(encoding="utf-8")
    resources = (ROOT / "templates" / "base2026-ai-visibility-resources.html").read_text(encoding="utf-8")
    source_diversity = (ROOT / "templates" / "base2026-source-diversity-check.html").read_text(encoding="utf-8")

    assert evidence_search.count('href="/tools/source-backed-brief/"') == 1
    assert resources.count('href="/tools/source-backed-brief/"') == 1
    assert 'Source-backed brief · planned' not in evidence_search
    assert 'href="/tools/source-backed-brief/"' not in source_diversity


def test_source_backed_brief_owned_delta_has_no_private_or_member_surface_changes() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    # The test runs on a working tree before commit in normal development, so
    # inspect the owned files directly as well as any committed delta.
    owned = {
        "docs/project-memory/HANDOFF_2026-09-04_SOURCE_BACKED_BRIEF.md",
        "docs/project-memory/NEXT_ACTION.md",
        "docs/project-memory/PROMPT_LOG.md",
        "scripts/audit-publication-boundary.py",
        "scripts/build-base2026-cloudflare-release.py",
        "templates/base2026-source-backed-brief.html",
        "templates/base2026-source-backed-brief.css",
        "templates/base2026-source-backed-brief.js",
        "templates/base2026-evidence-search.html",
        "templates/base2026-ai-visibility-resources.html",
        "tests/test_base2026_source_backed_brief.py",
        "tests/test_base2026_evidence_search_tool.py",
        "tests/test_build_base2026_cloudflare_release.py",
    }
    assert set(changed) <= owned or not changed
    for path in owned - {"scripts/audit-publication-boundary.py", "tests/test_base2026_source_backed_brief.py", "tests/test_base2026_evidence_search_tool.py", "tests/test_build_base2026_cloudflare_release.py"}:
        target = ROOT / path
        if target.is_file():
            text = target.read_text(encoding="utf-8")
            assert "client_secret" not in text.lower()
            assert "access_token" not in text.lower()
            if path != "scripts/build-base2026-cloudflare-release.py":
                assert "wp-admin/admin-post.php" not in text
