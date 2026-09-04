from __future__ import annotations

import json
import subprocess
from pathlib import Path

from test_build_base2026_cloudflare_release import builder


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PAGE = ROOT / "templates" / "base2026-evidence-search.html"
SOURCE_PAGE = ROOT / "templates" / "base2026-source-diversity-check.html"
BRIEF_PAGE = ROOT / "templates" / "base2026-source-backed-brief.html"
EVIDENCE_SCRIPT = ROOT / "templates" / "base2026-evidence-search.js"
SOURCE_SCRIPT = ROOT / "templates" / "base2026-source-diversity-check.js"
BRIEF_SCRIPT = ROOT / "templates" / "base2026-source-backed-brief.js"
MEASUREMENT_SCRIPT = ROOT / "templates" / "base2026-activation-measurement.js"


def test_measurement_listener_is_loaded_before_all_public_tool_runtimes() -> None:
    measurement_tag = '<script src="/static/base2026-activation-measurement.js?v=20260904-activation-measurement-v1" defer></script>'
    evidence = EVIDENCE_PAGE.read_text(encoding="utf-8")
    source = SOURCE_PAGE.read_text(encoding="utf-8")
    brief = BRIEF_PAGE.read_text(encoding="utf-8")

    assert measurement_tag in evidence
    assert measurement_tag in source
    assert measurement_tag in brief
    assert evidence.index(measurement_tag) < evidence.index("base2026-evidence-search.js")
    assert source.index(measurement_tag) < source.index("base2026-source-diversity-check.js")
    assert brief.index(measurement_tag) < brief.index("base2026-source-backed-brief.js")


def test_measurement_contract_is_first_party_bounded_and_non_identifying() -> None:
    script = MEASUREMENT_SCRIPT.read_text(encoding="utf-8")

    assert 'const ENDPOINT = "/api/analytics/event";' in script
    assert "MAX_EVENTS_PER_PAGE = 24" in script
    assert 'mode: "same-origin"' in script
    assert 'credentials: "omit"' in script
    assert "keepalive: true" in script
    assert 'referrerPolicy: "no-referrer"' in script
    assert 'window.addEventListener("base2026:analytics"' in script
    assert "window.dataLayer" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert ".cookie" not in script
    assert "navigator" not in script
    assert "document.referrer" not in script
    assert "public_record_id" not in script
    assert '"/tools/evidence-search/"' in script
    assert '"/tools/source-diversity-check/"' in script
    assert '"/tools/source-backed-brief/"' in script


def test_tool_emitters_have_no_third_party_data_layer_or_raw_identifiers() -> None:
    evidence = EVIDENCE_SCRIPT.read_text(encoding="utf-8")
    source = SOURCE_SCRIPT.read_text(encoding="utf-8")
    brief = BRIEF_SCRIPT.read_text(encoding="utf-8")

    for script in (evidence, source, brief):
        assert 'new CustomEvent("base2026:analytics"' in script
        assert "window.dataLayer" not in script
        assert "localStorage" not in script
        assert "sessionStorage" not in script
        assert ".cookie" not in script
        assert "Authorization" not in script
        assert "document.referrer" not in script
    assert "public_record_id" not in evidence
    assert "referrer_class" not in evidence
    assert "http_status_bucket" not in evidence
    assert "source_type: type" not in evidence
    assert "window.dataLayer" not in brief


def test_privacy_and_analytics_copy_describes_the_candidate_without_unique_visitor_claims() -> None:
    privacy_template = (ROOT / "templates" / "base2026-privacy.html").read_text(encoding="utf-8")
    privacy_source = (ROOT / "docs" / "public-pages" / "03_PRIVACY_POLICY.md").read_text(encoding="utf-8")
    analytics_page = (ROOT / "web" / "static" / "analytics.html").read_text(encoding="utf-8")

    for document in (privacy_template, privacy_source, analytics_page):
        assert "first-party" in document or "first-party activation" in document
        assert "raw quer" in document.lower()
        assert "unique visitor" in document.lower() or "unique-visitor" in document.lower()
    assert "public_record_id" not in privacy_template
    assert "private acquisition pipeline" in privacy_template
    assert "Cloudflare Analytics Engine" in privacy_source
    assert "does not use this cookie" in analytics_page


def test_builder_exposes_shared_measurement_asset() -> None:
    assert builder.DEFAULT_ACTIVATION_MEASUREMENT_SCRIPT == MEASUREMENT_SCRIPT


def test_shared_listener_drops_disallowed_properties_and_caps_page_events() -> None:
    source = MEASUREMENT_SCRIPT.read_text(encoding="utf-8")
    harness = f"""
const vm = require("node:vm");
const source = {json.dumps(source)};
const listeners = {{}};
const calls = [];
const context = {{
  window: {{
    location: {{ pathname: "/tools/evidence-search/" }},
    addEventListener: (name, listener) => {{ listeners[name] = listener; }},
    fetch: (url, options) => {{ calls.push({{ url, options }}); return Promise.resolve({{ ok: true }}); }}
  }}
}};
context.globalThis = context;
vm.runInNewContext(source, context, {{ filename: "base2026-activation-measurement.js" }});
for (let index = 0; index < 30; index += 1) listeners["base2026:analytics"]({{ detail: {{
  name: "evidence_search_submitted",
  properties: {{ input_source: "typed", query_length_bucket: "1_20", query_token_bucket: "1", render_mode: "enhanced", public_record_id: "tiktok-video-7657638702864223510", referrer_class: "search" }}
}} }});
console.log(JSON.stringify(calls));
"""
    result = subprocess.run(["node", "-e", harness], cwd=ROOT, check=True, capture_output=True, text=True)
    calls = json.loads(result.stdout)
    assert len(calls) == 24
    assert calls[0]["url"] == "/api/analytics/event"
    assert calls[0]["options"]["credentials"] == "omit"
    assert calls[0]["options"]["keepalive"] is True
    body = json.loads(calls[0]["options"]["body"])
    assert body["route"] == "/tools/evidence-search/"
    assert body["properties"] == {
        "input_source": "typed",
        "query_length_bucket": "1_20",
        "query_token_bucket": "1",
        "render_mode": "enhanced",
    }


def test_shared_listener_accepts_only_coarse_source_backed_brief_properties() -> None:
    source = MEASUREMENT_SCRIPT.read_text(encoding="utf-8")
    harness = f"""
const vm = require("node:vm");
const source = {json.dumps(source)};
const listeners = {{}};
const calls = [];
const context = {{
  window: {{
    location: {{ pathname: "/tools/source-backed-brief/" }},
    addEventListener: (name, listener) => {{ listeners[name] = listener; }},
    fetch: (url, options) => {{ calls.push({{ url, options }}); return Promise.resolve({{ ok: true }}); }}
  }}
}};
context.globalThis = context;
vm.runInNewContext(source, context, {{ filename: "base2026-activation-measurement.js" }});
listeners["base2026:analytics"]({{ detail: {{
  name: "brief_preview_created",
  properties: {{ deliverable: "brief", response_class: "partial", selected_count_bucket: "6_10", resolved_count_bucket: "2_5", viewport_class: "large", question: "raw question", source_id: "tiktok:private:1" }}
}} }});
console.log(JSON.stringify(calls));
"""
    result = subprocess.run(["node", "-e", harness], cwd=ROOT, check=True, capture_output=True, text=True)
    calls = json.loads(result.stdout)
    assert len(calls) == 1
    body = json.loads(calls[0]["options"]["body"])
    assert body == {
        "event": "brief_preview_created",
        "route": "/tools/source-backed-brief/",
        "properties": {
            "deliverable": "brief",
            "resolved_count_bucket": "2_5",
            "response_class": "partial",
            "selected_count_bucket": "6_10",
            "viewport_class": "large",
        },
    }
