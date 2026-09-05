from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "wordpress" / "base2026-evidence-sidebar"
PHP = PLUGIN / "base2026-evidence-sidebar.php"
EDITOR = PLUGIN / "assets" / "editor.js"
README = PLUGIN / "readme.txt"
LICENSE = PLUGIN / "LICENSE"


def test_plugin_package_has_only_reviewable_source_surfaces() -> None:
    assert PHP.is_file()
    assert EDITOR.is_file()
    assert README.is_file()
    assert LICENSE.is_file()
    assert not list(PLUGIN.glob("*.zip"))
    assert not list(PLUGIN.glob("*.min.js"))


def test_php_header_and_editor_hooks_are_versioned_and_gpl() -> None:
    source = PHP.read_text(encoding="utf-8")

    assert "Plugin Name: Base2026 Evidence Sidebar" in source
    assert "Version: 0.1.0" in source
    assert "Requires at least: 6.5" in source
    assert "Requires PHP: 7.4" in source
    assert "License: GPLv2 or later" in source
    assert "add_action( 'rest_api_init'" in source
    assert "add_action( 'enqueue_block_editor_assets'" in source
    assert "register_rest_route(" in source
    assert "WP_REST_Server::CREATABLE" in source


def test_proxy_uses_one_fixed_excerpt_bearing_public_brief_without_transcript_fields() -> None:
    source = PHP.read_text(encoding="utf-8")

    assert "https://base2026.dev/api/evidence-brief/v2" in source
    assert "wp_safe_remote_get(" in source
    assert "self::EVIDENCE_BRIEF_ENDPOINT" in source
    assert "add_query_arg( 'q', $query, self::EVIDENCE_BRIEF_ENDPOINT )" in source
    assert "'findings'" in source
    assert "'evidence_excerpt'" in source
    assert "wp_safe_remote_post(" not in source
    assert "'body' => $upstream_body" not in source
    assert "'timeout'             => self::REQUEST_TIMEOUT_SECONDS" in source
    assert "'redirection'        => 0" in source
    assert "'limit_response_size' => self::MAX_RESPONSE_BYTES" in source
    assert "'reject_unsafe_urls'  => true" in source
    assert "wp_remote_post(" not in source.replace("wp_safe_remote_post(", "")
    assert "curl_exec" not in source


def test_rest_input_is_strictly_authenticated_and_bounded() -> None:
    source = PHP.read_text(encoding="utf-8")

    assert "current_user_can( 'edit_posts' )" in source
    assert "get_header( 'X-WP-Nonce' )" in source
    assert "wp_verify_nonce( $nonce, 'wp_rest' )" in source
    assert "MAX_QUERY_CHARS = 160" in source
    assert "MAX_REQUEST_BODY_BYTES = 8192" in source
    assert "strlen( $body ) > self::MAX_REQUEST_BODY_BYTES" in source
    assert "Only the query field is accepted." in source
    assert "'query' must be text" not in source
    assert "preg_match( '//u', $query )" in source
    assert "wp_safe_remote_get(\n\t\t\t$upstream_url" in source
    assert "$_GET" not in source
    assert "$_POST" not in source
    assert "$_REQUEST" not in source
    assert "get_option(" not in source
    assert "update_option(" not in source
    assert "setcookie(" not in source


def test_php_reduces_hits_to_short_attributed_cards_and_safe_links() -> None:
    source = PHP.read_text(encoding="utf-8")

    assert "'title'               => $title" in source
    assert "'title_kind'          => 'source_claim_label'" in source
    assert "'excerpt'             => $excerpt" in source
    assert "'excerpt_kind'        => '' !== $excerpt ? 'public_evidence_excerpt' : 'source_claim_only'" in source
    assert "'provenance'          => 'Base2026 Evidence Brief v2" in source
    assert "'original_url'        => $original_url" in source
    assert "'base2026_url'        => $base2026_url" in source
    assert "'source_quality_note'" in source
    assert "independent verification" in source
    assert "safe_base2026_url" in source
    assert "evidence_excerpt" in source
    assert "isset( $finding['claim'] ) ? $finding['claim'] : ''" in source
    assert "isset( $hit['body'] )" not in source
    assert "isset( $hit['title'] )" not in source
    assert "in_array( strtolower( $parts['scheme'] ), array( 'http', 'https' ), true )" in source
    assert "isset( $parts['user'] ) || isset( $parts['pass'] )" in source
    assert "rest_ensure_response" in source
    assert "Full transcript fields" in source


def test_editor_is_native_gutenberg_click_to_search_and_click_to_insert() -> None:
    source = EDITOR.read_text(encoding="utf-8")

    assert "PluginSidebar" in source
    assert "PluginSidebarMoreMenuItem" in source
    assert 'plugins.registerPlugin("base2026-evidence-sidebar"' in source
    assert 'data.select("core/block-editor")' in source
    assert "getSelectedBlock()" in source
    assert "Use selected block text" in source
    assert "Search Base2026" in source
    assert 'method: "POST"' in source
    assert '"X-WP-Nonce"' in source
    assert 'credentials: "same-origin"' in source
    assert "JSON.stringify({query: normalized})" in source
    assert "Insert research note" in source
    assert "makeResearchNoteBlocks" in source
    assert 'blocks.createBlock("core/paragraph"' in source
    assert 'data.dispatch("core/block-editor").insertBlocks(blocksToInsert)' in source
    assert "includeBase2026" in source
    assert "optional Base2026 source link" in source
    assert "Source: " in source
    assert "Original source" in source
    assert "not a verbatim quotation" in source
    assert "core/quote" not in source
    assert "What the source says" not in source
    assert "before you search" in source.lower()
    assert "not whole-web verification" in source


def test_editor_has_no_background_collection_or_arbitrary_network_surface() -> None:
    source = EDITOR.read_text(encoding="utf-8")

    assert source.count("global.fetch(") == 1
    assert "localStorage" not in source
    assert "sessionStorage" not in source
    assert ".cookie" not in source
    assert "sendBeacon" not in source
    assert "document.referrer" not in source
    assert "navigator" not in source
    assert "getEditedPostContent" not in source
    assert "getCurrentPost" not in source
    assert "postId" not in source
    assert "record_id" not in source
    assert "Authorization" not in source
    assert "window.location" not in source
    assert "isAllowedRestEndpoint(config.restUrl)" in source
    assert 'endpoint.origin !== current.origin' in source
    assert 'endpoint.pathname !== configured.pathname || endpoint.search !== configured.search' in source
    assert 'var prettyPath = sitePrefix + "/wp-json/base2026/v1/search"' in source
    assert 'endpoint.searchParams.get("rest_route") === "/base2026/v1/search"' in source
    assert 'endpoint.search === ""' in source
    assert "queryKeys.length === 1" in source
    assert "pending.current" in source
    assert "inserted[card.key]" in source
    assert "AbortController" in source


def test_editor_escapes_inserted_values_and_validates_display_links() -> None:
    source = EDITOR.read_text(encoding="utf-8")

    assert "function escapeHtml" in source
    assert "escapeHtml(card.excerpt)" in source
    assert "escapeHtml(card.originalUrl)" in source
    assert "safeHttpUrl" in source
    assert "safeBase2026Url" in source
    assert 'parsed.protocol !== "http:"' in source
    assert 'parsed.protocol !== "https:"' in source
    assert "parsed.username || parsed.password" in source
    assert "disabled: !canInsert || props.inserted" in source


def test_readme_documents_external_service_boundaries_and_release_state() -> None:
    source = README.read_text(encoding="utf-8")

    for required in (
        "GPLv2 or later",
        "https://base2026.dev/privacy",
        "https://base2026.dev/api",
        "https://base2026.dev/source-policy",
        "up to 160 characters",
        "does not send the full post",
        "does not use cookies",
        "not a whole-web search",
        "not proof that a recommendation works",
        "evidence_excerpt",
        "claim that the excerpt is verbatim",
        "When no excerpt is returned",
        "optional and is never inserted",
        "0.1.0",
        "== Changelog ==",
        "manual-install beta",
        "Only the short topic you submit is sent",
    ):
        assert required in source

    assert "API key" in source
    assert "raw media or full private transcripts" in source
    assert "automatic rewrite" in source


def test_license_is_gplv2_text() -> None:
    source = LICENSE.read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in source
    assert "Version 2, June 1991" in source
    assert "NO WARRANTY" in source


def _run_editor_behavior_harness() -> dict:
    source = EDITOR.read_text(encoding="utf-8")
    harness = f"""
const vm = require("node:vm");
const {{ URL }} = require("node:url");
const source = {json.dumps(source)};

function component() {{ return function () {{}}; }}
function findAll(node, predicate, output) {{
  output = output || [];
  if (Array.isArray(node)) {{ node.forEach(function (child) {{ findAll(child, predicate, output); }}); return output; }}
  if (!node || typeof node !== "object") return output;
  if (predicate(node)) output.push(node);
  (node.children || []).forEach(function (child) {{ findAll(child, predicate, output); }});
  if (typeof node.type === "function" && (node.type.name === "ResultCard" || node.type.name === "Link" || node.type.name === "PolicyNotice")) {{
    findAll(node.type(node.props), predicate, output);
  }}
  return output;
}}

async function scenario(payload, restUrl) {{
  const calls = [];
  const inserted = [];
  const state = [];
  const refs = [];
  let cursor = 0;
  let registered = null;
  const Button = component();
  const CheckboxControl = component();
  const Notice = component();
  const PanelBody = component();
  const Spinner = component();
  const TextControl = component();
  const PluginSidebar = component();
  const PluginSidebarMoreMenuItem = component();
  const createElement = function (type, props) {{
    return {{type: type, props: props || {{}}, children: Array.prototype.slice.call(arguments, 2)}};
  }};
  const wp = {{
    element: {{
      createElement: createElement,
      Fragment: component(),
      useRef: function (initial) {{ const index = cursor++; if (!(index in refs)) refs[index] = {{current: initial}}; return refs[index]; }},
      useState: function (initial) {{ const index = cursor++; if (!(index in state)) state[index] = initial; return [state[index], function (value) {{ state[index] = typeof value === "function" ? value(state[index]) : value; }}]; }}
    }},
    components: {{Button, CheckboxControl, Notice, PanelBody, Spinner, TextControl}},
    data: {{
      select: function () {{ return {{getSelectedBlock: function () {{ return null; }} }}; }},
      dispatch: function () {{ return {{insertBlocks: function (blocks) {{ inserted.push(blocks); }} }}; }}
    }},
    blocks: {{createBlock: function (name, attributes, innerBlocks) {{ return {{name: name, attributes: attributes || {{}}, innerBlocks: innerBlocks || []}}; }} }},
    plugins: {{registerPlugin: function (_name, options) {{ registered = options; }}}},
    editPost: {{PluginSidebar, PluginSidebarMoreMenuItem}}
  }};
  const win = {{
    wp: wp,
    URL: URL,
    AbortController: AbortController,
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    location: {{href: "https://wp.test/wp-admin/post.php"}},
    Base2026EvidenceSidebarConfig: {{
      restUrl: restUrl,
      nonce: "nonce",
      maxQueryChars: 160,
      privacyUrl: "https://base2026.dev/privacy",
      serviceLimitsUrl: "https://base2026.dev/api",
      sourcePolicyUrl: "https://base2026.dev/source-policy"
    }}
  }};
  win.fetch = function (url, options) {{
    calls.push({{url: url, options: options}});
    return Promise.resolve({{ok: true, status: 200, text: function () {{ return Promise.resolve(JSON.stringify(payload)); }}}});
  }};
  const context = {{window: win}};
  vm.runInNewContext(source, context, {{filename: "base2026-evidence-sidebar-editor.js"}});
  function render() {{ cursor = 0; return registered.render(); }}
  let tree = render();
  const input = findAll(tree, function (node) {{ return node.type === TextControl; }})[0];
  input.props.onChange("internal linking");
  if (calls.length !== 0) throw new Error("query input caused a network request");
  tree = render();
  const searchButton = findAll(tree, function (node) {{ return node.type === Button && node.children[0] === "Search Base2026"; }})[0];
  if (!searchButton || searchButton.props.disabled) throw new Error("search button unavailable");
  searchButton.props.onClick();
  await new Promise(function (resolve) {{ setTimeout(resolve, 0); }});
  tree = render();
  const insertButtons = findAll(tree, function (node) {{ return node.type === Button && (node.children[0] === "Insert research note" || node.children[0] === "No excerpt to insert"); }});
  return {{
    callCount: calls.length,
    requestUrl: calls[0] ? calls[0].url : null,
    requestBody: calls[0] ? JSON.parse(calls[0].options.body) : null,
    insertLabel: insertButtons[0] ? insertButtons[0].children[0] : null,
    insertDisabled: insertButtons[0] ? Boolean(insertButtons[0].props.disabled) : null,
    insertedBeforeClick: inserted.length,
    clickInsert: function () {{ if (insertButtons[0]) insertButtons[0].props.onClick(); return inserted; }}
  }};
}}

(async function () {{
  const titleOnly = await scenario({{results: [{{title: "A source claim label", excerpt: "", excerpt_kind: "source_claim_only", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "https://www.tiktok.com/@creator/video/1234567890123", base2026_url: "https://base2026.dev/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/wp-json/base2026/v1/search");
  const titleOnlyInserted = titleOnly.clickInsert().length;
  const excerpt = await scenario({{results: [{{title: "A source claim label", excerpt: "A bounded source excerpt with a useful research detail.", excerpt_kind: "public_evidence_excerpt", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "https://www.tiktok.com/@creator/video/1234567890123", base2026_url: "https://base2026.dev/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/wp-json/base2026/v1/search");
  const excerptInserted = excerpt.clickInsert();
  const malformed = await scenario({{results: [{{title: "A source claim label", excerpt: "A bounded source excerpt.", excerpt_kind: "public_evidence_excerpt", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "javascript:alert(1)", base2026_url: "https://evil.example/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/wp-json/base2026/v1/search");
  const plainPermalink = await scenario({{results: [{{title: "A source claim label", excerpt: "", excerpt_kind: "source_claim_only", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "https://www.tiktok.com/@creator/video/1234567890123", base2026_url: "https://base2026.dev/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/?rest_route=%2Fbase2026%2Fv1%2Fsearch");
  const proxyPath = await scenario({{results: [{{title: "A source claim label", excerpt: "A bounded source excerpt.", excerpt_kind: "public_evidence_excerpt", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "https://www.tiktok.com/@creator/video/1234567890123", base2026_url: "https://base2026.dev/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/proxy/base2026/v1/search");
  const extraQuery = await scenario({{results: [{{title: "A source claim label", excerpt: "A bounded source excerpt.", excerpt_kind: "public_evidence_excerpt", provenance: "Base2026 Evidence Brief v2 · public source finding", creator: "@creator", original_url: "https://www.tiktok.com/@creator/video/1234567890123", base2026_url: "https://base2026.dev/sources/tiktok-video-1234567890123"}}]}}, "https://wp.test/?rest_route=%2Fbase2026%2Fv1%2Fsearch&proxy=https%3A%2F%2Fevil.example");
  console.log(JSON.stringify({{
    titleOnly: {{calls: titleOnly.callCount, body: titleOnly.requestBody, label: titleOnly.insertLabel, disabled: titleOnly.insertDisabled, inserted: titleOnlyInserted}},
    excerpt: {{calls: excerpt.callCount, body: excerpt.requestBody, label: excerpt.insertLabel, disabled: excerpt.insertDisabled, blocks: excerptInserted}},
    malformed: {{calls: malformed.callCount, label: malformed.insertLabel, disabled: malformed.insertDisabled, body: malformed.requestBody}},
    plainPermalink: {{calls: plainPermalink.callCount, url: plainPermalink.requestUrl, body: plainPermalink.requestBody}},
    proxyPath: {{calls: proxyPath.callCount, url: proxyPath.requestUrl, body: proxyPath.requestBody}},
    extraQuery: {{calls: extraQuery.callCount, url: extraQuery.requestUrl, body: extraQuery.requestBody}}
  }}));
}})().catch(function (error) {{ console.error(error.stack || error); process.exit(1); }});
"""
    result = subprocess.run(
        ["node", "-e", harness],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_editor_behavior_rejects_title_only_and_malformed_links_and_inserts_note_for_excerpt() -> None:
    behavior = _run_editor_behavior_harness()

    assert behavior["titleOnly"] == {
        "calls": 1,
        "body": {"query": "internal linking"},
        "label": "No excerpt to insert",
        "disabled": True,
        "inserted": 0,
    }
    assert behavior["excerpt"]["calls"] == 1
    assert behavior["excerpt"]["body"] == {"query": "internal linking"}
    assert behavior["excerpt"]["label"] == "Insert research note"
    assert behavior["excerpt"]["disabled"] is False
    assert len(behavior["excerpt"]["blocks"]) == 1
    inserted_blocks = behavior["excerpt"]["blocks"][0]
    assert [block["name"] for block in inserted_blocks] == ["core/paragraph", "core/paragraph"]
    assert "Base2026 research note" in inserted_blocks[0]["attributes"]["content"]
    assert "not a verbatim quotation" in inserted_blocks[0]["attributes"]["content"]
    assert "Original source" in inserted_blocks[1]["attributes"]["content"]
    assert "core/quote" not in {block["name"] for block in inserted_blocks}
    assert behavior["malformed"] == {
        "calls": 1,
        "label": "No excerpt to insert",
        "disabled": True,
        "body": {"query": "internal linking"},
    }


def test_editor_behavior_accepts_pretty_and_plain_permalink_rest_routes_only() -> None:
    behavior = _run_editor_behavior_harness()

    assert behavior["plainPermalink"] == {
        "calls": 1,
        "url": "https://wp.test/?rest_route=%2Fbase2026%2Fv1%2Fsearch",
        "body": {"query": "internal linking"},
    }
    assert behavior["proxyPath"] == {
        "calls": 0,
        "url": None,
        "body": None,
    }
    assert behavior["extraQuery"] == {
        "calls": 0,
        "url": None,
        "body": None,
    }
