(function () {
  "use strict";

  const root = document.querySelector("[data-source-diversity-check]");
  if (!root) return;

  const form = root.querySelector("[data-source-check-form]");
  const input = root.querySelector("[data-source-check-input]");
  const submit = root.querySelector("[data-source-check-submit]");
  const results = root.querySelector("[data-source-check-results]");
  const status = root.querySelector("[data-source-check-status]");
  const counts = root.querySelector("[data-source-check-counts]");
  const summary = root.querySelector("[data-source-check-summary]");
  const recordList = root.querySelector("[data-source-check-records]");
  const exports = root.querySelector("[data-source-check-exports]");
  const resultActions = root.querySelector("[data-source-check-result-actions]") || exports;
  const exportMarkdown = root.querySelector("[data-source-check-export-markdown]");
  const exportJson = root.querySelector("[data-source-check-export-json]");
  const copyMarkdown = root.querySelector("[data-source-check-copy-markdown]");
  const copyJson = root.querySelector("[data-source-check-copy-json]");
  const unresolvedSection = root.querySelector("[data-source-check-unresolved-section]");
  const unresolvedList = root.querySelector("[data-source-check-unresolved]");
  const decisionForm = root.querySelector("[data-source-diversity-decision-form]");
  const decisionSelect = root.querySelector("[data-source-diversity-decision]");
  const decisionStatus = root.querySelector("[data-source-diversity-decision-status]");
  const endpoint = safeMcpEndpoint(root.dataset.mcpEndpoint);

  if (!form || !input || !submit || !results || !status || !counts || !summary || !recordList || !exports || !resultActions || !exportMarkdown || !exportJson || !copyMarkdown || !copyJson || !unresolvedSection || !unresolvedList || !endpoint) return;

  const MCP_PROTOCOL_VERSION = "2026-07-28";
  const MAX_INPUT_CHARS = 600;
  const MAX_RECORD_IDS = 12;
  const MAX_SOURCE_ID_CHARS = 256;
  const REQUEST_TIMEOUT_MS = 12000;
  const LOOKUP_CONCURRENCY = 3;
  const UNRESOLVED_CREATOR = "Creator metadata unresolved in this public record";
  const UNRESOLVED_SOURCE = "Original source URL unresolved in this public record";
  const LIMITS = [
    "Counts are limited to the selected public Base2026 records.",
    "Record count is not source independence, consensus, truth, reach or recommendation effectiveness.",
    "No external crawl, ranking, backlink or Search Console data is used.",
    "No LLM verdict, fabricated score or full transcript is produced."
  ];
  const ALLOWED_ANALYTICS_EVENTS = new Set([
    "source_check_run",
    "source_check_completed",
    "source_check_decision_recorded",
    "source_check_card_copied"
  ]);

  let activeController = null;
  let currentSnapshot = null;
  let completedForRun = false;

  document.documentElement.classList.add("source-diversity-enhanced");

  function cleanText(value, maxLength) {
    if (typeof value !== "string") return "";
    const compact = value.replace(/\s+/gu, " ").trim();
    if (!compact) return "";
    return compact.slice(0, maxLength);
  }

  function element(tagName, className, textValue) {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (typeof textValue === "string") node.textContent = textValue;
    return node;
  }

  function safeMcpEndpoint(value) {
    const raw = cleanText(value, 300);
    if (!raw) return "";
    try {
      const parsed = new URL(raw, window.location.origin);
      if (parsed.origin !== window.location.origin || parsed.pathname !== "/api/mcp" || parsed.search || parsed.hash) return "";
      return parsed.href;
    } catch (_error) {
      return "";
    }
  }

  function canonicalRecordId(value) {
    const raw = cleanText(value, 80);
    const canonical = raw.match(/^tiktok-video-(\d{10,30})$/u);
    if (canonical) return "tiktok-video-" + canonical[1];
    if (/^\d{10,30}$/u.test(raw)) return "tiktok-video-" + raw;
    return "";
  }

  function canonicalSourceId(value) {
    const raw = cleanText(value, MAX_SOURCE_ID_CHARS);
    const canonical = raw.match(/^tiktok:([A-Za-z0-9._-]{2,256}):(\d{10,30})$/u);
    return canonical ? "tiktok:" + canonical[1] + ":" + canonical[2] : "";
  }

  function safeSourceId(value) {
    return canonicalSourceId(value);
  }

  function validInputId(value) {
    const canonical = canonicalRecordId(value);
    if (canonical) return { lookupId: canonical, acceptedId: canonical, inputKind: "record_id" };
    const sourceId = canonicalSourceId(value);
    return sourceId ? { lookupId: sourceId, acceptedId: sourceId, inputKind: "source_id" } : null;
  }

  function recordIdFromSourceId(value) {
    const canonical = canonicalSourceId(value);
    if (!canonical) return "";
    const videoId = canonical.split(":").pop();
    return canonicalRecordId(videoId);
  }

  function responseRecordId(data, input) {
    const fromInput = input && input.inputKind === "record_id" ? canonicalRecordId(input.lookupId) : "";
    if (fromInput) return fromInput;
    const candidates = [data && data.id, data && data.item_id, data && data.video_id, data && data.post_id];
    for (const candidate of candidates) {
      const recordId = canonicalRecordId(candidate);
      if (recordId) return recordId;
    }
    return recordIdFromSourceId(data && data.source_id) || recordIdFromSourceId(input && input.lookupId);
  }

  function tokensFromJson(value) {
    const raw = value.trim();
    if (!/^[\[{]/u.test(raw)) return null;
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (_error) {
      return null;
    }
    const output = [];
    const acceptedKeys = new Set(["item_id", "source_id", "video_id", "post_id", "record_id"]);
    function visit(node, depth) {
      if (depth > 5 || node === null || typeof node !== "object") return;
      if (Array.isArray(node)) {
        node.slice(0, 100).forEach(function (child) { visit(child, depth + 1); });
        return;
      }
      Object.keys(node).slice(0, 100).forEach(function (key) {
        const child = node[key];
        if (acceptedKeys.has(key) && typeof child === "string") output.push(child);
        if (child && typeof child === "object") visit(child, depth + 1);
      });
    }
    if (typeof parsed === "string") output.push(parsed);
    else visit(parsed, 0);
    return output;
  }

  function parseInput(value) {
    const raw = typeof value === "string" ? value.trim() : "";
    const truncated = raw.length > MAX_INPUT_CHARS;
    const bounded = raw.slice(0, MAX_INPUT_CHARS);
    const jsonTokens = tokensFromJson(bounded);
    const tokens = jsonTokens || bounded.split(/[\s,]+/u).filter(Boolean);
    const accepted = [];
    const seen = new Set();
    let invalidCount = truncated ? 1 : 0;
    let duplicateCount = 0;
    tokens.forEach(function (token) {
      const parsed = validInputId(cleanText(token, MAX_SOURCE_ID_CHARS));
      if (!parsed) {
        invalidCount += 1;
        return;
      }
      if (seen.has(parsed.lookupId)) {
        duplicateCount += 1;
        return;
      }
      if (accepted.length >= MAX_RECORD_IDS) {
        invalidCount += 1;
        return;
      }
      seen.add(parsed.lookupId);
      accepted.push(parsed);
    });
    return {
      accepted: accepted,
      invalidCount: invalidCount,
      duplicateCount: duplicateCount,
      inputMode: jsonTokens ? "json_records" : "delimited_ids",
      sourceIdCount: accepted.filter(function (entry) { return entry.inputKind === "source_id"; }).length,
      recordIdCount: accepted.filter(function (entry) { return entry.inputKind === "record_id"; }).length
    };
  }

  function prefilledIdsFromSearch() {
    const raw = new URLSearchParams(window.location.search).get("ids");
    if (typeof raw !== "string" || !raw.trim()) return false;
    input.value = raw.slice(0, MAX_INPUT_CHARS);
    return true;
  }

  function safeOriginalUrl(value) {
    const raw = cleanText(value, 1000);
    if (!raw) return "";
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:" || parsed.username || parsed.password) return "";
      return parsed.href;
    } catch (_error) {
      return "";
    }
  }

  function normalizedOriginalUrl(value) {
    const safe = safeOriginalUrl(value);
    if (!safe) return "";
    try {
      const parsed = new URL(safe);
      const path = (parsed.pathname || "/").replace(/\/{2,}/gu, "/").replace(/\/+$/u, "") || "/";
      const port = parsed.port ? ":" + parsed.port : "";
      return "https://" + parsed.hostname.toLowerCase().replace(/^www\./u, "") + port + path;
    } catch (_error) {
      return "";
    }
  }

  function publicBoundaryIsSafe(data) {
    const boundary = data && data.public_boundary;
    return Boolean(boundary
      && boundary.access === "public_read_only"
      && boundary.raw_captions === false
      && boundary.raw_asr === false
      && boundary.media_files === false
      && boundary.private_data === false
      && boundary.writes === false);
  }

  function unsafePublicMetadata(data) {
    if (!publicBoundaryIsSafe(data)) return true;
    if (data.full_transcript_public === true || data.public === false || data.needs_review === true) return true;
    return typeof data.public_policy === "string"
      && /(?:private|needs[_-]?review|raw|full[_-]?transcript|asr|media)/iu.test(data.public_policy);
  }

  function safeBase2026Url(value) {
    const raw = cleanText(value, 300);
    if (!raw) return "";
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:" || (parsed.hostname !== "base2026.dev" && parsed.hostname !== "www.base2026.dev")) return "";
      if (!/^\/sources\/tiktok-video-\d{10,30}$/u.test(parsed.pathname)) return "";
      return parsed.href;
    } catch (_error) {
      return "";
    }
  }

  function derivedBase2026Url(recordId) {
    const canonical = canonicalRecordId(recordId);
    return canonical ? "https://base2026.dev/sources/" + canonical : "";
  }

  function safeDate(value) {
    const raw = cleanText(value, 40);
    if (/^\d{4}-\d{2}-\d{2}(?:T|$)/u.test(raw)) return raw.slice(0, 10);
    return "";
  }

  function safeCreator(data) {
    const creator = data && data.creator && typeof data.creator === "object" ? data.creator : {};
    const rawHandle = cleanText(creator.handle || data.creator_handle || data.handle, 256);
    const handle = /^[A-Za-z0-9._-]{1,256}$/u.test(rawHandle.replace(/^@/u, ""))
      ? "@" + rawHandle.replace(/^@/u, "")
      : "";
    const displayName = cleanText(creator.display_name || data.creator_display_name, 180);
    const key = handle
      ? "handle:" + handle.slice(1).toLowerCase()
      : displayName
        ? "name:" + displayName.normalize("NFKC").toLowerCase()
        : "";
    return {
      handle: handle || null,
      display_name: displayName || null,
      key: key || null,
      label: handle || displayName || UNRESOLVED_CREATOR
    };
  }

  function safeResponseSourceIds(data, fallback) {
    const values = [data && data.source_id, data && data.sourceId, fallback]
      .map(function (value) { return safeSourceId(value); })
      .filter(Boolean);
    return Array.from(new Set(values)).sort();
  }

  function normalizeResolved(data, input) {
    if (!data || data.found !== true || unsafePublicMetadata(data)) return null;
    const sourceIds = safeResponseSourceIds(data, input.inputKind === "source_id" ? input.lookupId : "");
    const recordId = responseRecordId(data, input);
    if (!recordId) return null;
    const originalUrl = safeOriginalUrl(data.source_url || (data.attribution && data.attribution.original_source_url));
    const normalizedUrl = normalizedOriginalUrl(originalUrl);
    const creator = safeCreator(data);
    return {
      record_id: recordId,
      source_id: sourceIds[0] || null,
      source_ids: sourceIds,
      video_id: /^tiktok-video-\d{10,30}$/u.test(recordId) ? recordId.slice("tiktok-video-".length) : (cleanText(data.video_id, 40) || null),
      base2026_url: safeBase2026Url(data.source_page_url || (data.attribution && data.attribution.base2026_source_url)) || derivedBase2026Url(recordId),
      original_source_url: originalUrl || null,
      normalized_original_source_url: normalizedUrl || null,
      creator: creator,
      published_date: safeDate(data.published_date || data.published_at),
      title: cleanText(data.title, 180) || null,
      decision: null,
      lookup_status: "resolved",
      resolution_reason: "",
      metadata_resolution: creator.key && normalizedUrl ? "complete" : "partial"
    };
  }

  function unresolvedRecord(outcome) {
    const inputId = cleanText(outcome && outcome.input && outcome.input.lookupId, MAX_SOURCE_ID_CHARS);
    const recordId = canonicalRecordId(inputId) || recordIdFromSourceId(inputId);
    const sourceId = outcome && outcome.input && outcome.input.inputKind === "source_id"
      ? canonicalSourceId(inputId)
      : "";
    return {
      record_id: recordId,
      input_id: inputId,
      source_id: sourceId || null,
      source_ids: sourceId ? [sourceId] : [],
      video_id: recordId.startsWith("tiktok-video-") ? recordId.slice("tiktok-video-".length) : null,
      base2026_url: "",
      original_source_url: null,
      normalized_original_source_url: null,
      creator: { handle: null, display_name: null, key: null, label: UNRESOLVED_CREATOR },
      published_date: "",
      title: null,
      decision: null,
      metadata_resolution: "unresolved",
      lookup_status: "unresolved",
      resolution_reason: outcome && outcome.reason ? outcome.reason : "unresolved"
    };
  }

  function mcpRequestBody(requestId, input) {
    return {
      jsonrpc: "2.0",
      id: requestId,
      method: "tools/call",
      params: {
        name: "get_source",
        arguments: { source_id: input.lookupId },
        _meta: { "io.modelcontextprotocol/protocolVersion": MCP_PROTOCOL_VERSION }
      }
    };
  }

  async function resolveOne(input, requestId, signal) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS);
    const abortFromRun = function () { controller.abort(); };
    signal.addEventListener("abort", abortFromRun, { once: true });
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        cache: "no-store",
        referrerPolicy: "strict-origin-when-cross-origin",
        headers: {
          "content-type": "application/json",
          "accept": "application/json",
          "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
          "Mcp-Method": "tools/call",
          "Mcp-Name": "get_source"
        },
        body: JSON.stringify(mcpRequestBody(requestId, input)),
        signal: controller.signal
      });
      if (!response.ok) return { input: input, record: null, reason: response.status >= 500 ? "server" : "request" };
      const payload = await response.json();
      if (!payload || payload.error || !payload.result || payload.result.isError === true) {
        return { input: input, record: null, reason: "api_rejected" };
      }
      const record = normalizeResolved(payload.result.structuredContent, input);
      return record
        ? { input: input, record: record, reason: "" }
        : { input: input, record: null, reason: "not_found_or_invalid" };
    } catch (error) {
      return { input: input, record: null, reason: error && error.name === "AbortError" ? "timeout" : "network" };
    } finally {
      window.clearTimeout(timeoutId);
      signal.removeEventListener("abort", abortFromRun);
    }
  }

  async function resolveAll(inputs, signal) {
    const output = new Array(inputs.length);
    let nextIndex = 0;
    async function worker() {
      while (nextIndex < inputs.length) {
        const index = nextIndex;
        nextIndex += 1;
        output[index] = await resolveOne(inputs[index], "source-diversity-" + (index + 1), signal);
      }
    }
    const workers = Math.min(LOOKUP_CONCURRENCY, inputs.length);
    await Promise.all(Array.from({ length: workers }, worker));
    return output;
  }

  function mergeRecord(existing, next) {
    const merged = Object.assign({}, existing);
    merged.source_ids = Array.from(new Set((existing.source_ids || []).concat(next.source_ids || []))).sort();
    merged.source_id = merged.source_ids[0] || existing.source_id || next.source_id || null;
    ["video_id", "base2026_url", "original_source_url", "normalized_original_source_url", "published_date", "title"].forEach(function (field) {
      if (!merged[field] && next[field]) merged[field] = next[field];
    });
    if (!merged.creator.key && next.creator.key) merged.creator = next.creator;
    merged.metadata_resolution = merged.creator.key && merged.normalized_original_source_url ? "complete" : "partial";
    return merged;
  }

  function recordsFromOutcomes(outcomes) {
    const byId = new Map();
    outcomes.forEach(function (outcome) {
      if (!outcome || !outcome.input) return;
      const record = outcome.record || unresolvedRecord(outcome);
      const previous = byId.get(record.record_id);
      if (!previous || (previous.lookup_status === "unresolved" && record.lookup_status !== "unresolved")) {
        byId.set(record.record_id, record);
      } else if (previous.lookup_status !== "unresolved" && record.lookup_status !== "unresolved") {
        byId.set(record.record_id, mergeRecord(previous, record));
      }
    });
    return Array.from(byId.values()).sort(function (left, right) {
      return left.record_id.localeCompare(right.record_id);
    });
  }

  function groupBy(records, field) {
    const groups = new Map();
    function add(key, label, recordId, unresolved) {
      const groupKey = key || "__unresolved__";
      let group = groups.get(groupKey);
      if (!group) {
        group = { key: key || null, label: label, record_ids: [], unresolved: Boolean(unresolved) };
        groups.set(groupKey, group);
      }
      if (!group.record_ids.includes(recordId)) group.record_ids.push(recordId);
    }
    records.forEach(function (record) {
      if (field === "creator") {
        add(record.creator.key, record.creator.label, record.record_id, !record.creator.key);
      } else if (field === "source") {
        add(record.normalized_original_source_url, record.normalized_original_source_url || UNRESOLVED_SOURCE, record.record_id, !record.normalized_original_source_url);
      } else if (field === "source_ids") {
        if (!record.source_ids.length) add("", "Source ID unresolved in this public record", record.record_id, true);
        else record.source_ids.forEach(function (sourceId) { add(sourceId, sourceId, record.record_id, false); });
      }
    });
    return Array.from(groups.values()).map(function (group) {
      group.record_ids.sort();
      return group;
    }).sort(function (left, right) {
      if (left.unresolved !== right.unresolved) return left.unresolved ? 1 : -1;
      return left.label.localeCompare(right.label);
    });
  }

  function countBucket(count) {
    if (count <= 1) return "0_1";
    if (count <= 5) return "2_5";
    if (count <= 10) return "6_10";
    return "11_plus";
  }

  function viewportClass() {
    if (window.innerWidth < 640) return "small";
    if (window.innerWidth < 1024) return "medium";
    return "large";
  }

  function emitAnalytics(name, properties) {
    if (!ALLOWED_ANALYTICS_EVENTS.has(name)) return;
    const detail = { name: name, properties: Object.assign({}, properties) };
    window.dispatchEvent(new CustomEvent("base2026:analytics", { detail: detail }));
    if (Array.isArray(window.dataLayer)) window.dataLayer.push(Object.assign({ event: name }, properties));
  }

  function buildSnapshot(parsed, outcomes) {
    const records = recordsFromOutcomes(outcomes);
    const failures = outcomes.filter(function (outcome) { return outcome && !outcome.record; }).map(function (outcome) {
      return { id: outcome.input.lookupId, reason: outcome.reason || "unresolved" };
    });
    const creatorGroups = groupBy(records, "creator");
    const sourceGroups = groupBy(records, "source");
    const sourceIdGroups = groupBy(records, "source_ids");
    const recordGroups = records.map(function (record) {
      return { key: record.lookup_status === "resolved" ? record.record_id : null, label: record.record_id, record_ids: [record.record_id], unresolved: record.lookup_status !== "resolved" };
    });
    const distinctCreators = creatorGroups.filter(function (group) { return !group.unresolved; }).length;
    const distinctSources = sourceGroups.filter(function (group) { return !group.unresolved; }).length;
    const distinctSourceIds = sourceIdGroups.filter(function (group) { return !group.unresolved; }).length;
    const resolvedRecords = records.filter(function (record) { return record.lookup_status === "resolved"; });
    return {
      schema: "base2026.source-diversity-check.v1",
      status: resolvedRecords.length === 0 ? "no_resolved_records" : (failures.length || parsed.invalidCount ? "partial" : "complete"),
      contract: {
        input: "valid canonical Base2026 public record IDs or canonical public source IDs only",
        record_count_definition: "unique accepted record identities; resolved_records is the confirmed public lookup count",
        source_count_definition: "distinct normalized original source URLs; unresolved URLs are not counted as known sources",
        creator_count_definition: "distinct attributed creator handles or names; unresolved creator metadata is not counted",
        consensus_warning: "diversity is not consensus or truth"
      },
      input: {
        mode: parsed.inputMode,
        accepted_ids: parsed.accepted.map(function (entry) { return entry.acceptedId; }),
        invalid_input_count: parsed.invalidCount,
        duplicate_input_count: parsed.duplicateCount
      },
      counts: {
        submitted_ids: parsed.accepted.length,
        resolved_records: resolvedRecords.length,
        distinct_records: records.length,
        distinct_sources: distinctSources,
        distinct_creators: distinctCreators,
        distinct_source_ids: distinctSourceIds,
        unresolved_source_records: records.filter(function (record) { return !record.normalized_original_source_url; }).length,
        unresolved_creator_records: records.filter(function (record) { return !record.creator.key; }).length,
        lookup_failures: failures.length
      },
      groups: {
        records: recordGroups,
        creators: creatorGroups,
        original_source_urls: sourceGroups,
        source_ids: sourceIdGroups
      },
      records: records,
      unresolved_lookups: failures,
      limits: LIMITS.slice()
    };
  }

  function setStatus(state, message) {
    status.dataset.state = state;
    status.textContent = message;
  }

  function setLoading(loading) {
    submit.disabled = loading;
    submit.textContent = loading ? "Checking…" : "Check these records";
    input.setAttribute("aria-busy", loading ? "true" : "false");
  }

  function resetOutput() {
    counts.replaceChildren();
    summary.replaceChildren();
    recordList.replaceChildren();
    unresolvedList.replaceChildren();
    unresolvedSection.hidden = true;
    exports.hidden = true;
    resultActions.hidden = true;
    currentSnapshot = null;
  }

  function appendMetric(label, value) {
    const metric = element("div", "b26-source-diversity__metric");
    metric.appendChild(element("strong", "", String(value)));
    metric.appendChild(element("span", "", label));
    counts.appendChild(metric);
  }

  function renderCounts(snapshot) {
    appendMetric("Distinct records", snapshot.counts.distinct_records);
    appendMetric("Distinct sources", snapshot.counts.distinct_sources);
    appendMetric("Distinct creators", snapshot.counts.distinct_creators);
    const secondary = element("p", "b26-source-diversity__secondary-counts");
    secondary.textContent = "Resolved records: " + snapshot.counts.resolved_records + " · Public source IDs: " + snapshot.counts.distinct_source_ids + " · Unresolved source metadata: " + snapshot.counts.unresolved_source_records + " · Unresolved creator metadata: " + snapshot.counts.unresolved_creator_records;
    counts.appendChild(secondary);
  }

  function appendGroup(group, kind) {
    const item = element("li");
    if (group.unresolved) {
      item.textContent = group.label + " · " + group.record_ids.length + (group.record_ids.length === 1 ? " record" : " records");
    } else {
      const value = kind === "source" ? element("a") : element("code");
      if (kind === "source") {
        value.href = group.label;
        value.target = "_blank";
        value.rel = "noopener noreferrer";
      }
      value.textContent = group.label;
      item.appendChild(value);
      item.appendChild(document.createTextNode(" · " + group.record_ids.length + (group.record_ids.length === 1 ? " record" : " records")));
    }
    return item;
  }

  function renderGroup(title, groups, kind) {
    const panel = element("section", "b26-source-diversity__group");
    if (groups.some(function (group) { return group.unresolved; })) panel.classList.add("b26-source-diversity__group--unresolved");
    panel.appendChild(element("h3", "", title));
    const list = element("ul");
    groups.forEach(function (group) { list.appendChild(appendGroup(group, kind)); });
    if (!groups.length) list.appendChild(element("li", "", "No resolved groups"));
    panel.appendChild(list);
    summary.appendChild(panel);
  }

  function renderSummary(snapshot) {
    renderGroup("Exact record IDs", snapshot.groups.records, "record");
    renderGroup("Creators", snapshot.groups.creators, "creator");
    renderGroup("Normalized original sources", snapshot.groups.original_source_urls, "source");
  }

  function appendDefinition(meta, label, value, unresolved) {
    meta.appendChild(element("dt", "", label));
    const dd = element("dd", unresolved ? "is-unresolved" : "", value);
    meta.appendChild(dd);
  }

  function renderRecord(record, position) {
    const card = element("article", "b26-source-diversity__record-card");
    const top = element("div", "b26-source-diversity__record-top");
    const heading = element("div");
    heading.appendChild(element("p", "b26-source-diversity__record-index", "Record " + position));
    const title = element("h3");
    title.appendChild(element("code", "", record.record_id));
    heading.appendChild(title);
    top.appendChild(heading);
    const stateLabel = record.lookup_status === "unresolved"
      ? "Lookup unresolved"
      : (record.metadata_resolution === "complete" ? "Metadata resolved" : "Metadata partial");
    const state = element("span", "b26-source-diversity__record-state", stateLabel);
    state.dataset.state = record.metadata_resolution;
    top.appendChild(state);
    card.appendChild(top);

    const meta = element("dl", "b26-source-diversity__record-meta");
    appendDefinition(meta, "Creator", record.creator.label, !record.creator.key);
    appendDefinition(meta, "Source ID", record.source_ids.join(", ") || "Source ID unresolved in this public record", !record.source_ids.length);
    if (record.normalized_original_source_url) {
      meta.appendChild(element("dt", "", "Normalized original source URL"));
      const sourceDd = element("dd");
      const sourceLink = element("a", "", record.normalized_original_source_url);
      sourceLink.href = record.original_source_url || record.normalized_original_source_url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      sourceDd.appendChild(sourceLink);
      meta.appendChild(sourceDd);
    } else {
      appendDefinition(meta, "Original source URL", UNRESOLVED_SOURCE, true);
    }
    if (record.base2026_url) {
      meta.appendChild(element("dt", "", "Base2026 record"));
      const baseDd = element("dd");
      const baseLink = element("a", "", "Open the stable public record");
      baseLink.href = record.base2026_url;
      baseDd.appendChild(baseLink);
      meta.appendChild(baseDd);
    }
    if (record.title) appendDefinition(meta, "Public title", record.title, false);
    if (record.published_date) appendDefinition(meta, "Published", record.published_date, false);
    if (record.lookup_status === "unresolved") {
      appendDefinition(meta, "Lookup status", record.resolution_reason || "Public record could not be resolved.", true);
    }
    card.appendChild(meta);

    const actions = element("div", "b26-source-diversity__record-actions");
    const copyButton = element("button", "", "Copy card");
    copyButton.type = "button";
    copyButton.addEventListener("click", async function () {
      const originalLabel = copyButton.textContent;
      copyButton.disabled = true;
      copyButton.textContent = "Copying…";
      try {
        await copyText(recordMarkdown(record));
        copyButton.textContent = "Copied";
        emitAnalytics("source_check_card_copied", { record_position_bucket: countBucket(position), metadata_resolution: record.metadata_resolution, copy_format: "record_card" });
      } catch (_error) {
        copyButton.textContent = "Copy failed";
      } finally {
        window.setTimeout(function () { copyButton.disabled = false; copyButton.textContent = originalLabel; }, 1400);
      }
    });
    actions.appendChild(copyButton);

    const decision = element("label", "b26-source-diversity__record-decision");
    decision.appendChild(document.createTextNode("Research note"));
    const select = document.createElement("select");
    select.setAttribute("aria-label", "Research note for record " + record.record_id);
    [
      ["", "Not recorded"],
      ["use", "Use in a bounded note"],
      ["investigate", "Investigate further"],
      ["exclude", "Exclude from this note"]
    ].forEach(function (optionData) {
      const option = document.createElement("option");
      option.value = optionData[0];
      option.textContent = optionData[1];
      select.appendChild(option);
    });
    select.value = record.decision || "";
    select.addEventListener("change", function () {
      record.decision = select.value || null;
      if (record.decision) {
        emitAnalytics("source_check_decision_recorded", { decision: record.decision, record_position_bucket: countBucket(position), metadata_resolution: record.metadata_resolution, scope: "record" });
      }
    });
    decision.appendChild(select);
    actions.appendChild(decision);
    card.appendChild(actions);
    return card;
  }

  function renderRecords(snapshot) {
    snapshot.records.forEach(function (record, index) {
      recordList.appendChild(renderRecord(record, index + 1));
    });
  }

  function renderUnresolved(snapshot, parsed) {
    unresolvedList.replaceChildren();
    const entries = snapshot.unresolved_lookups.slice();
    if (parsed.invalidCount) {
      entries.push({
        id: "input",
        reason: parsed.invalidCount + " invalid or over-limit item" + (parsed.invalidCount === 1 ? " was" : "s were") + " rejected before lookup."
      });
    }
    if (!entries.length) {
      unresolvedSection.hidden = true;
      return;
    }
    unresolvedSection.hidden = false;
    const list = element("ul");
    entries.sort(function (left, right) {
      return left.id.localeCompare(right.id) || left.reason.localeCompare(right.reason);
    });
    entries.forEach(function (entry) {
      list.appendChild(element("li", "", entry.id + " — " + entry.reason));
    });
    unresolvedList.appendChild(list);
  }

  function renderSnapshot(snapshot, parsed) {
    currentSnapshot = snapshot;
    renderCounts(snapshot);
    renderSummary(snapshot);
    renderRecords(snapshot);
    renderUnresolved(snapshot, parsed);
    const hasRecords = snapshot.records.length > 0;
    exports.hidden = !hasRecords;
    resultActions.hidden = !hasRecords;
    if (!hasRecords) {
      setStatus("error", "No accepted public record resolved. Check the IDs in Evidence Search/API and try again; nothing was inferred.");
    } else if (snapshot.counts.resolved_records === 0) {
      setStatus("error", "None of the selected public records resolved. The exact IDs and unresolved lookup states remain visible below and in the export.");
    } else if (snapshot.status === "partial") {
      setStatus("partial", "The check resolved " + snapshot.counts.resolved_records + " public record" + (snapshot.counts.resolved_records === 1 ? "" : "s") + ", but " + (snapshot.counts.lookup_failures + parsed.invalidCount) + " input" + (snapshot.counts.lookup_failures + parsed.invalidCount === 1 ? " needs" : "s need") + " attention. Unresolved metadata stays visible below.");
    } else {
      setStatus("success", "The selected public records are grouped deterministically. Review the separate counts and record decisions before exporting.");
    }
    if (!completedForRun) {
      completedForRun = true;
      emitAnalytics("source_check_completed", { completion_mode: "lookup_complete", record_count_bucket: countBucket(snapshot.counts.distinct_records), response_class: snapshot.status, viewport_class: viewportClass() });
    }
  }

  function mdText(value) {
    return cleanText(value, 1000)
      .replace(/&/gu, "&amp;")
      .replace(/[<>]/gu, function (character) { return character === "<" ? "&lt;" : "&gt;"; })
      .replace(/[|]/gu, "\\|");
  }

  function mdUrl(value) {
    return "<" + String(value).replace(/[<>]/gu, "") + ">";
  }

  function groupMarkdown(groups) {
    if (!groups.length) return ["- None resolved."];
    return groups.flatMap(function (group) {
      const label = group.unresolved ? group.label : (group.key && group.key.startsWith("http") ? mdUrl(group.key) : mdText(group.label));
      return ["- " + label + " — " + group.record_ids.join(", ")];
    });
  }

  function recordMarkdown(record) {
    const lines = [
      "- Record ID: " + record.record_id,
      "  - Source ID(s): " + (record.source_ids.join(", ") || "unresolved"),
      "  - Creator: " + mdText(record.creator.label),
      "  - Original source URL: " + (record.normalized_original_source_url ? mdUrl(record.normalized_original_source_url) : "unresolved"),
      "  - Decision: " + (record.decision || "not recorded")
    ];
    if (record.input_id && record.input_id !== record.record_id) lines.push("  - Submitted ID: " + mdText(record.input_id));
    if (record.lookup_status !== "resolved") lines.push("  - Lookup status: " + mdText(record.resolution_reason || "unresolved"));
    if (record.title) lines.push("  - Public title: " + mdText(record.title));
    if (record.published_date) lines.push("  - Published: " + record.published_date);
    if (record.base2026_url) lines.push("  - Base2026 record: " + mdUrl(record.base2026_url));
    return lines.join("\n");
  }

  function markdownSnapshot(snapshot) {
    const c = snapshot.counts;
    const lines = [
      "# Base2026 Source Diversity Check",
      "",
      "> Deterministic counts for selected public records. Diversity is not consensus or truth.",
      "",
      "## Counts",
      "",
      "- Distinct records: " + c.distinct_records,
      "- Distinct sources: " + c.distinct_sources,
      "- Distinct creators: " + c.distinct_creators,
      "- Distinct public source IDs: " + c.distinct_source_ids,
      "- Unresolved source metadata: " + c.unresolved_source_records,
      "- Unresolved creator metadata: " + c.unresolved_creator_records,
      "",
      "Source means a normalized original source URL. Unresolved metadata remains unresolved and is not silently counted as a known source or creator.",
      "",
      "## Grouped record IDs",
      "",
      ...groupMarkdown(snapshot.groups.records),
      "",
      "## Grouped creators",
      "",
      ...groupMarkdown(snapshot.groups.creators),
      "",
      "## Grouped normalized original source URLs",
      "",
      ...groupMarkdown(snapshot.groups.original_source_urls),
      "",
      "## Records",
      "",
      ...snapshot.records.flatMap(function (record) { return [recordMarkdown(record), ""]; }),
      "## Limits",
      "",
      ...snapshot.limits.map(function (limit) { return "- " + limit; }),
      ""
    ];
    if (snapshot.unresolved_lookups.length) {
      const unresolved = snapshot.unresolved_lookups.slice().sort(function (left, right) {
        return left.id.localeCompare(right.id) || left.reason.localeCompare(right.reason);
      });
      lines.push(
        "",
        "## Unresolved lookups",
        "",
        ...unresolved.map(function (entry) { return "- " + mdText(entry.id) + " — " + mdText(entry.reason); }),
        ""
      );
    }
    return lines.join("\n");
  }

  function jsonSnapshot(snapshot) {
    return JSON.stringify(snapshot, null, 2) + "\n";
  }

  async function copyText(value) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(value);
      return;
    }
    const helper = document.createElement("textarea");
    helper.value = value;
    helper.setAttribute("readonly", "true");
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.appendChild(helper);
    helper.select();
    const copied = document.execCommand("copy");
    helper.remove();
    if (!copied) throw new Error("copy_unavailable");
  }

  function downloadText(filename, value, mimeType) {
    const blob = new Blob([value], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  async function copyExport(button, value, successLabel, copyFormat) {
    const originalLabel = button.textContent;
    button.disabled = true;
    try {
      await copyText(value);
      button.textContent = successLabel;
      emitAnalytics("source_check_card_copied", {
        copy_format: copyFormat,
        record_count_bucket: currentSnapshot ? countBucket(currentSnapshot.counts.distinct_records) : "0"
      });
    } catch (_error) {
      button.textContent = "Copy failed";
    } finally {
      window.setTimeout(function () { button.disabled = false; button.textContent = originalLabel; }, 1400);
    }
  }

  async function runCheck(inputSource) {
    if (activeController) activeController.abort();
    const controller = new AbortController();
    activeController = controller;
    const parsed = parseInput(input.value);
    completedForRun = false;
    results.hidden = false;
    resetOutput();
    emitAnalytics("source_check_run", {
      input_source: inputSource === "evidence_search_handoff" ? "evidence_search_handoff" : "direct",
      input_mode: parsed.inputMode,
      submitted_count_bucket: countBucket(parsed.accepted.length),
      invalid_input_bucket: countBucket(parsed.invalidCount),
      duplicate_input_bucket: countBucket(parsed.duplicateCount),
      record_id_bucket: countBucket(parsed.recordIdCount),
      source_id_bucket: countBucket(parsed.sourceIdCount),
      viewport_class: viewportClass()
    });
    if (!parsed.accepted.length) {
      setStatus("error", "Paste at least one valid Base2026 public record ID or source ID. Arbitrary URLs and prose are not accepted.");
      completedForRun = true;
      emitAnalytics("source_check_completed", {
        completion_mode: "input_rejected",
        record_count_bucket: "0_1",
        response_class: "invalid_input",
        viewport_class: viewportClass()
      });
      activeController = null;
      return;
    }
    setLoading(true);
    setStatus("loading", "Resolving the selected public records through the read-only source API…");
    try {
      const outcomes = await resolveAll(parsed.accepted, controller.signal);
      if (activeController !== controller) return;
      renderSnapshot(buildSnapshot(parsed, outcomes), parsed);
    } finally {
      if (activeController === controller) {
        activeController = null;
        setLoading(false);
      }
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    runCheck("typed");
  });
  exportMarkdown.addEventListener("click", function () {
    if (currentSnapshot) downloadText("base2026-source-diversity-check.md", markdownSnapshot(currentSnapshot), "text/markdown;charset=utf-8");
  });
  exportJson.addEventListener("click", function () {
    if (currentSnapshot) downloadText("base2026-source-diversity-check.json", jsonSnapshot(currentSnapshot), "application/json;charset=utf-8");
  });
  copyMarkdown.addEventListener("click", function () {
    if (currentSnapshot) copyExport(copyMarkdown, markdownSnapshot(currentSnapshot), "Copied Markdown", "markdown");
  });
  copyJson.addEventListener("click", function () {
    if (currentSnapshot) copyExport(copyJson, jsonSnapshot(currentSnapshot), "Copied JSON", "json");
  });
  if (decisionForm && decisionSelect && decisionStatus) {
    decisionForm.addEventListener("submit", function (event) {
      event.preventDefault();
      if (!decisionSelect.value || !currentSnapshot) {
        decisionStatus.textContent = "Run a check and choose a follow-up step first.";
        return;
      }
      emitAnalytics("source_check_decision_recorded", {
        decision: decisionSelect.value,
        scope: "record_set",
        record_count_bucket: countBucket(currentSnapshot.counts.distinct_records),
        viewport_class: viewportClass()
      });
      decisionStatus.textContent = "Follow-up step recorded locally for this browser view.";
    });
  }
  if (prefilledIdsFromSearch()) window.setTimeout(function () { runCheck("evidence_search_handoff"); }, 0);
})();
