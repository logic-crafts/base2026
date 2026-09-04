(function () {
  "use strict";

  const root = document.querySelector("[data-source-backed-brief]");
  if (!root) return;

  const form = root.querySelector("[data-brief-form]");
  const questionInput = root.querySelector("[data-brief-question]");
  const audienceInput = root.querySelector("[data-brief-audience]");
  const deliverableInput = root.querySelector("[data-brief-deliverable]");
  const idsInput = root.querySelector("[data-brief-ids]");
  const submit = root.querySelector("[data-brief-submit]");
  const results = root.querySelector("[data-brief-results]");
  const resultTitle = root.querySelector("[data-brief-result-title]");
  const status = root.querySelector("[data-brief-status]");
  const requestOutput = root.querySelector("[data-brief-request]");
  const countsOutput = root.querySelector("[data-brief-counts]");
  const exportPanel = root.querySelector("[data-brief-export]");
  const recordList = root.querySelector("[data-brief-records]");
  const unknownsOutput = root.querySelector("[data-brief-unknowns]");
  const limitationsOutput = root.querySelector("[data-brief-limitations]");
  const copyMarkdown = root.querySelector("[data-brief-copy-markdown]");
  const downloadMarkdown = root.querySelector("[data-brief-download-markdown]");
  const copyJson = root.querySelector("[data-brief-copy-json]");
  const downloadJson = root.querySelector("[data-brief-download-json]");
  const exportStatus = root.querySelector("[data-brief-export-status]");
  const endpoint = safeMcpEndpoint(root.dataset.mcpEndpoint);

  if (!form || !questionInput || !audienceInput || !deliverableInput || !idsInput || !submit || !results || !resultTitle || !status || !requestOutput || !countsOutput || !exportPanel || !recordList || !unknownsOutput || !limitationsOutput || !copyMarkdown || !downloadMarkdown || !copyJson || !downloadJson || !exportStatus || !endpoint) return;

  const MCP_PROTOCOL_VERSION = "2026-07-28";
  const MAX_QUESTION_CHARS = 240;
  const MAX_AUDIENCE_CHARS = 120;
  const MAX_INPUT_CHARS = 1200;
  const MAX_RECORD_IDS = 8;
  const MAX_SOURCE_ID_CHARS = 200;
  const PASSAGE_PUBLIC_POLICY = "search_passage";
  const MAX_EXCERPT_CHARS = 360;
  const MAX_EXCERPTS_PER_RECORD = 3;
  const REQUEST_TIMEOUT_MS = 12000;
  const LOOKUP_CONCURRENCY = 3;
  const DELIVERABLES = new Set(["brief", "memo", "outline"]);
  const DELIVERABLE_LABELS = { brief: "Brief", memo: "Memo", outline: "Outline" };
  const LIMITATIONS = [
    "This preview uses only the selected public Base2026 records and bounded public fields returned by get_source.",
    "A missing or partial lookup is not evidence that no relevant source exists elsewhere.",
    "The builder does not infer truth, consensus, independence, quality, effectiveness or agreement.",
    "No external crawl, ranking, backlink, Search Console or popularity data is used.",
    "Raw captions, raw ASR, media, private data, writes and LLM answers are outside this public read-only path."
  ];
  const ALLOWED_ANALYTICS_EVENTS = new Set([
    "brief_required_fields_completed",
    "brief_preview_created",
    "brief_exported",
    "brief_completed"
  ]);
  const PUBLIC_BOUNDARY = Object.freeze({
    access: "public_read_only",
    raw_captions: false,
    raw_asr: false,
    media_files: false,
    private_data: false,
    writes: false
  });

  let activeController = null;
  let currentSnapshot = null;
  let completedForRun = false;

  function cleanText(value, maxLength) {
    if (typeof value !== "string") return "";
    const compact = value.replace(/\s+/gu, " ").trim();
    if (!compact) return "";
    return compact.slice(0, maxLength);
  }

  function boundedText(value, maxLength) {
    const compact = cleanText(value, maxLength + 1);
    if (!compact || compact.length <= maxLength) return compact;
    return compact.slice(0, Math.max(1, maxLength - 1)).trimEnd() + "…";
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
    const raw = cleanText(value, MAX_SOURCE_ID_CHARS + 1);
    if (raw.length > MAX_SOURCE_ID_CHARS) return "";
    const canonical = raw.match(/^tiktok-video-(\d{10,30})$/u);
    if (canonical) return "tiktok-video-" + canonical[1];
    if (/^\d{10,30}$/u.test(raw)) return "tiktok-video-" + raw;
    return "";
  }

  function canonicalSourceId(value) {
    const raw = cleanText(value, MAX_SOURCE_ID_CHARS + 1);
    if (raw.length > MAX_SOURCE_ID_CHARS) return "";
    const canonical = raw.match(/^tiktok:([A-Za-z0-9._-]{2,200}):(\d{10,30})$/u);
    return canonical ? "tiktok:" + canonical[1] + ":" + canonical[2] : "";
  }

  function validInputId(value) {
    const candidate = typeof value === "string" ? value.replace(/\s+/gu, " ").trim() : "";
    if (!candidate || candidate.length > MAX_SOURCE_ID_CHARS) return null;
    const recordId = canonicalRecordId(candidate);
    if (recordId) return { lookupId: recordId, acceptedId: recordId, inputKind: "record_id" };
    const sourceId = canonicalSourceId(candidate);
    return sourceId ? { lookupId: sourceId, acceptedId: sourceId, inputKind: "source_id" } : null;
  }

  function recordIdFromSourceId(value) {
    const sourceId = canonicalSourceId(value);
    if (!sourceId) return "";
    return canonicalRecordId(sourceId.split(":").pop());
  }

  function responseRecordId(data, input) {
    if (input && input.inputKind === "record_id") return canonicalRecordId(input.lookupId);
    const candidates = [
      data && data.id,
      data && data.item_id,
      data && data.record_id,
      data && data.video_id,
      data && data.post_id,
      data && data.source_id
    ];
    for (const candidate of candidates) {
      const recordId = canonicalRecordId(candidate);
      if (recordId) return recordId;
    }
    return recordIdFromSourceId(data && (data.source_id || data.sourceId)) || recordIdFromSourceId(input && input.lookupId);
  }

  function tokensFromJson(value) {
    if (typeof value !== "string") return null;
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

  function parseIds(value) {
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
      const parsed = validInputId(token);
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
      truncated: truncated,
      inputMode: jsonTokens ? "json_records" : "delimited_ids",
      submittedIdCount: accepted.length,
      sourceIdCount: accepted.filter(function (entry) { return entry.inputKind === "source_id"; }).length,
      recordIdCount: accepted.filter(function (entry) { return entry.inputKind === "record_id"; }).length
    };
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

  function firstSafeUrl(values) {
    for (const value of values) {
      const safe = safeOriginalUrl(value);
      if (safe) return safe;
    }
    return "";
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

  function safeBase2026Url(value) {
    const raw = cleanText(value, 300);
    if (!raw) return "";
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:" || (parsed.hostname !== "base2026.dev" && parsed.hostname !== "www.base2026.dev")) return "";
      if (!/^\/sources\/tiktok-video-\d{10,30}\/?$/u.test(parsed.pathname)) return "";
      return parsed.href;
    } catch (_error) {
      return "";
    }
  }

  function safeDate(value) {
    const raw = cleanText(value, 40);
    return /^\d{4}-\d{2}-\d{2}(?:T|$)/u.test(raw) ? raw.slice(0, 10) : "";
  }

  function publicBoundaryIsSafe(data) {
    const boundary = data && data.public_boundary;
    return Boolean(boundary
      && boundary.access === PUBLIC_BOUNDARY.access
      && boundary.raw_captions === false
      && boundary.raw_asr === false
      && boundary.media_files === false
      && boundary.private_data === false
      && boundary.writes === false);
  }

  function unsafePublicMetadata(data) {
    if (!publicBoundaryIsSafe(data)) return true;
    if (publicFalseSignal(data.public) || publicSignalIsUnsafe(data.full_transcript_public) || publicSignalIsUnsafe(data.needs_review)) return true;
    const policyFields = [data.public_policy, data.policy, data.visibility].filter(function (value) { return typeof value === "string"; });
    if (policyFields.some(function (value) {
      return /(?:private|needs[_-]?review|raw|full[_-]?transcript|asr|media)/iu.test(value);
    })) return true;
    return ["raw", "private", "private_data", "raw_captions", "raw_asr", "media", "media_files", "raw_transcript", "full_transcript", "transcript", "captions"].some(function (field) {
      return publicSignalIsUnsafe(data[field]);
    });
  }

  function publicSignalIsUnsafe(value) {
    if (value === true || value === 1) return true;
    if (value && typeof value === "object") return true;
    if (typeof value !== "string") return false;
    const normalized = value.trim().toLowerCase();
    return Boolean(normalized && !/^(?:0|false|no)$/u.test(normalized));
  }

  function publicFalseSignal(value) {
    if (value === false || value === 0) return true;
    return typeof value === "string" && /^(?:0|false|no)$/iu.test(value.trim());
  }

  function passagePublicMetadataIsSafe(passage) {
    if (!passage || typeof passage !== "object") return false;
    if (!publicBoundaryIsSafe(passage)) return false;
    if (passage.public_policy !== PASSAGE_PUBLIC_POLICY) return false;
    for (const field of ["policy", "visibility"]) {
      if (passage[field] !== undefined && passage[field] !== null && passage[field] !== PASSAGE_PUBLIC_POLICY) return false;
    }
    if (publicFalseSignal(passage.public) || publicSignalIsUnsafe(passage.needs_review) || publicSignalIsUnsafe(passage.full_transcript_public)) return false;
    for (const field of [
      "raw",
      "private",
      "private_data",
      "raw_captions",
      "raw_asr",
      "media",
      "media_files",
      "raw_transcript",
      "full_transcript",
      "transcript",
      "captions"
    ]) {
      if (publicSignalIsUnsafe(passage[field])) return false;
    }
    for (const key of Object.keys(passage)) {
      if (/(?:^|_)(?:raw|private)(?:_|$)/iu.test(key) && publicSignalIsUnsafe(passage[key])) return false;
    }
    return true;
  }

  function safeCreator(data) {
    const creator = data && data.creator && typeof data.creator === "object" ? data.creator : {};
    const rawHandle = cleanText(creator.handle || data.creator_handle || data.handle, 256).replace(/^@/u, "");
    const handle = /^[A-Za-z0-9._-]{1,256}$/u.test(rawHandle) ? "@" + rawHandle : "";
    const displayName = cleanText(creator.display_name || creator.name || data.creator_display_name, 180);
    const url = firstSafeUrl([
      creator.url,
      creator.profile_url,
      data.creator_url,
      data.attribution && data.attribution.creator_url,
      data.attribution && data.attribution.creator_profile_url
    ]);
    const key = handle
      ? "handle:" + handle.slice(1).toLowerCase()
      : displayName
        ? "name:" + displayName.normalize("NFKC").toLowerCase()
        : "";
    return {
      handle: handle || null,
      display_name: displayName || null,
      url: url || null,
      key: key || null,
      label: handle || displayName || "Creator attribution unavailable in this public record"
    };
  }

  function safePassages(data) {
    const passages = Array.isArray(data && data.passages) ? data.passages : [];
    const seen = new Set();
    const output = [];
    passages.slice(0, 8).forEach(function (passage) {
      if (!passagePublicMetadataIsSafe(passage)) return;
      const excerpt = boundedText(passage.excerpt, MAX_EXCERPT_CHARS);
      if (!excerpt) return;
      const passageId = cleanText(passage.id || passage.passage_id, 120);
      const key = passageId || excerpt;
      if (seen.has(key)) return;
      seen.add(key);
      output.push({
        passage_id: passageId || null,
        chunk_index: Number.isFinite(Number(passage.chunk_index)) ? Math.max(0, Math.floor(Number(passage.chunk_index))) : null,
        excerpt: excerpt
      });
    });
    return output.slice(0, MAX_EXCERPTS_PER_RECORD);
  }

  function safeResponseSourceIds(data, fallback) {
    return Array.from(new Set([
      data && data.source_id,
      data && data.sourceId,
      fallback
    ].map(function (value) { return canonicalSourceId(value); }).filter(Boolean))).sort();
  }

  function normalizeResolved(data, input) {
    if (!data || data.found !== true || unsafePublicMetadata(data)) return null;
    const sourceIds = safeResponseSourceIds(data, input && input.inputKind === "source_id" ? input.lookupId : "");
    const recordId = responseRecordId(data, input);
    if (!recordId) return null;
    const originalUrl = firstSafeUrl([
      data.source_url,
      data.original_source_url,
      data.attribution && data.attribution.original_source_url
    ]);
    const creator = safeCreator(data);
    const baseUrl = firstSafeUrl([
      data.source_page_url,
      data.attribution && data.attribution.base2026_source_url
    ]);
    const excerpts = safePassages(data);
    const publishedDate = safeDate(data.published_date || data.published_at);
    const title = boundedText(data.title, 180) || null;
    const unknowns = [];
    if (!sourceIds.length) unknowns.push("Public source ID was not returned by this bounded public response.");
    if (!creator.key) unknowns.push("Creator attribution was not returned by this bounded public response.");
    if (!originalUrl) unknowns.push("Original source URL was not returned by this bounded public response.");
    if (!baseUrl) unknowns.push("Base2026 source page URL was not returned by this bounded public response.");
    if (!publishedDate) unknowns.push("Published date was not returned by this bounded public response.");
    if (!title) unknowns.push("Record title was not returned by this bounded public response.");
    if (!excerpts.length) unknowns.push("No bounded public excerpt was returned by this bounded public response.");
    return {
      record_id: recordId,
      input_id: input && input.lookupId ? input.lookupId : recordId,
      source_id: sourceIds[0] || null,
      source_ids: sourceIds,
      video_id: recordId.slice("tiktok-video-".length),
      base2026_url: safeBase2026Url(baseUrl) || null,
      original_source_url: originalUrl || null,
      normalized_original_source_url: normalizedOriginalUrl(originalUrl) || null,
      creator: creator,
      published_date: publishedDate,
      title: title,
      excerpts: excerpts,
      unknowns: unknowns,
      lookup_status: "resolved",
      resolution_reason: "",
      metadata_resolution: creator.key && originalUrl ? "complete" : "partial"
    };
  }

  function unresolvedRecord(outcome) {
    const input = outcome && outcome.input ? outcome.input : {};
    const inputId = cleanText(input.lookupId, MAX_SOURCE_ID_CHARS);
    const recordId = canonicalRecordId(inputId) || recordIdFromSourceId(inputId);
    const sourceId = input.inputKind === "source_id" ? canonicalSourceId(inputId) : "";
    const reason = cleanText(outcome && outcome.reason, 80) || "unresolved";
    return {
      record_id: recordId || inputId,
      input_id: inputId,
      source_id: sourceId || null,
      source_ids: sourceId ? [sourceId] : [],
      video_id: recordId.startsWith("tiktok-video-") ? recordId.slice("tiktok-video-".length) : null,
      base2026_url: null,
      original_source_url: null,
      normalized_original_source_url: null,
      creator: { handle: null, display_name: null, url: null, key: null, label: "Creator attribution unresolved in this public lookup" },
      published_date: "",
      title: null,
      excerpts: [],
      unknowns: ["Public get_source lookup did not resolve this submitted ID."],
      lookup_status: "unresolved",
      resolution_reason: reason,
      metadata_resolution: "unresolved"
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

  function structuredResult(payload) {
    if (!payload || !payload.result || payload.error || payload.result.isError === true) return null;
    if (payload.result.structuredContent && typeof payload.result.structuredContent === "object") return payload.result.structuredContent;
    const content = Array.isArray(payload.result.content) ? payload.result.content : [];
    for (const item of content) {
      if (!item || item.type !== "text" || typeof item.text !== "string") continue;
      try {
        const parsed = JSON.parse(item.text);
        if (parsed && typeof parsed === "object") return parsed;
      } catch (_error) {
        continue;
      }
    }
    return null;
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
      const record = normalizeResolved(structuredResult(await response.json()), input);
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
        output[index] = await resolveOne(inputs[index], "source-backed-brief-" + (index + 1), signal);
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
    merged.excerpts = (existing.excerpts || []).concat(next.excerpts || []).filter(function (passage, index, all) {
      const key = passage.passage_id || passage.excerpt;
      return all.findIndex(function (candidate) { return (candidate.passage_id || candidate.excerpt) === key; }) === index;
    }).slice(0, MAX_EXCERPTS_PER_RECORD);
    merged.unknowns = Array.from(new Set((existing.unknowns || []).concat(next.unknowns || [])));
    ["video_id", "base2026_url", "original_source_url", "normalized_original_source_url", "published_date", "title"].forEach(function (field) {
      if (!merged[field] && next[field]) merged[field] = next[field];
    });
    if ((!merged.creator || !merged.creator.key) && next.creator && next.creator.key) merged.creator = next.creator;
    merged.metadata_resolution = merged.creator && merged.creator.key && merged.original_source_url ? "complete" : "partial";
    return merged;
  }

  function recordsFromOutcomes(outcomes) {
    const byId = new Map();
    (Array.isArray(outcomes) ? outcomes : []).forEach(function (outcome) {
      if (!outcome || !outcome.input) return;
      const record = outcome.record || unresolvedRecord(outcome);
      const key = record.record_id || record.input_id;
      const previous = byId.get(key);
      if (!previous || (previous.lookup_status === "unresolved" && record.lookup_status !== "unresolved")) {
        byId.set(key, record);
      } else if (previous.lookup_status !== "unresolved" && record.lookup_status !== "unresolved") {
        byId.set(key, mergeRecord(previous, record));
      }
    });
    return Array.from(byId.values());
  }

  function countBucket(count) {
    if (count <= 1) return "0_1";
    if (count <= 5) return "2_5";
    return "6_10";
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
  }

  function buildSnapshot(request, parsed, outcomes) {
    if (Array.isArray(parsed) && outcomes === undefined) {
      outcomes = parsed;
      parsed = request;
      request = {};
    }
    parsed = parsed || { accepted: [], inputMode: "delimited_ids", submittedIdCount: 0, invalidCount: 0, duplicateCount: 0, truncated: false };
    const records = recordsFromOutcomes(outcomes);
    const safeRequest = {
      question: cleanText(request && request.question, MAX_QUESTION_CHARS),
      audience: cleanText(request && request.audience, MAX_AUDIENCE_CHARS),
      deliverable: DELIVERABLES.has(request && request.deliverable) ? request.deliverable : "brief"
    };
    const unresolvedLookups = (Array.isArray(outcomes) ? outcomes : []).filter(function (outcome) {
      return outcome && !outcome.record;
    }).map(function (outcome) {
      return { id: outcome.input.lookupId, reason: outcome.reason || "unresolved" };
    });
    const resolvedRecords = records.filter(function (record) { return record.lookup_status === "resolved"; });
    const unknowns = [];
    records.forEach(function (record) {
      (record.unknowns || []).forEach(function (detail) {
        const entry = { record_id: record.record_id, detail: detail };
        if (!unknowns.some(function (existing) { return existing.record_id === entry.record_id && existing.detail === entry.detail; })) unknowns.push(entry);
      });
    });
    if (parsed && parsed.invalidCount) unknowns.push({ record_id: null, detail: String(parsed.invalidCount) + " submitted ID or input item(s) were rejected; only canonical public IDs are accepted." });
    if (parsed && parsed.duplicateCount) unknowns.push({ record_id: null, detail: String(parsed.duplicateCount) + " duplicate submitted ID(s) were collapsed before lookup." });
    unresolvedLookups.forEach(function (lookup) {
      if (!unknowns.some(function (entry) { return entry.record_id === lookup.id; })) unknowns.push({ record_id: lookup.id, detail: "Lookup status: " + lookup.reason + "." });
    });
    return {
      schema: "base2026.source-backed-brief.v1",
      status: resolvedRecords.length === 0 ? "no_resolved_records" : (unresolvedLookups.length || (parsed && parsed.invalidCount) ? "partial" : "complete"),
      contract: {
        input: "valid canonical Base2026 public record IDs or canonical public source IDs only",
        excerpt_definition: "up to 3 public passages per resolved record, each bounded to 360 characters",
        truth_consensus_independence: "not_assessed; no inference",
        public_boundary: Object.assign({}, PUBLIC_BOUNDARY)
      },
      request: {
        question: safeRequest.question,
        audience: safeRequest.audience,
        deliverable: safeRequest.deliverable,
        deliverable_label: DELIVERABLE_LABELS[safeRequest.deliverable]
      },
      input: {
        mode: parsed && parsed.inputMode ? parsed.inputMode : "delimited_ids",
        accepted_ids: parsed ? parsed.accepted.map(function (entry) { return entry.acceptedId; }) : [],
        submitted_id_count: parsed ? parsed.submittedIdCount : 0,
        invalid_input_count: parsed ? parsed.invalidCount : 0,
        duplicate_input_count: parsed ? parsed.duplicateCount : 0,
        truncated: Boolean(parsed && parsed.truncated)
      },
      counts: {
        submitted_ids: parsed ? parsed.submittedIdCount : 0,
        resolved_records: resolvedRecords.length,
        unresolved_records: records.filter(function (record) { return record.lookup_status !== "resolved"; }).length,
        distinct_records: records.length,
        bounded_excerpts: records.reduce(function (total, record) { return total + (record.excerpts || []).length; }, 0),
        invalid_inputs: parsed ? parsed.invalidCount : 0,
        duplicate_inputs: parsed ? parsed.duplicateCount : 0
      },
      records: records,
      unresolved_lookups: unresolvedLookups,
      unknowns: unknowns,
      limitations: LIMITATIONS.slice()
    };
  }

  function buildBriefSnapshot(request, parsed, outcomes) {
    return buildSnapshot(request, parsed, outcomes);
  }

  function setStatus(state, message) {
    status.dataset.state = state;
    status.textContent = message;
  }

  function setLoading(loading) {
    submit.disabled = loading;
    submit.textContent = loading ? "Resolving records…" : "Build the preview";
    form.setAttribute("aria-busy", loading ? "true" : "false");
  }

  function resetOutput() {
    requestOutput.replaceChildren();
    countsOutput.replaceChildren();
    recordList.replaceChildren();
    unknownsOutput.replaceChildren();
    limitationsOutput.replaceChildren();
    exportPanel.hidden = true;
    currentSnapshot = null;
    exportStatus.textContent = "";
  }

  function appendDefinition(parent, label, value, unresolved) {
    parent.appendChild(element("dt", "", label));
    parent.appendChild(element("dd", unresolved ? "is-unresolved" : "", value));
  }

  function renderRequest(snapshot) {
    appendDefinition(requestOutput, "Question", snapshot.request.question || "Not supplied", !snapshot.request.question);
    appendDefinition(requestOutput, "Audience", snapshot.request.audience || "Not supplied", !snapshot.request.audience);
    appendDefinition(requestOutput, "Format", snapshot.request.deliverable_label, false);
    appendDefinition(requestOutput, "Selected IDs", String(snapshot.counts.submitted_ids) + " / " + MAX_RECORD_IDS, false);
  }

  function appendMetric(label, value) {
    const metric = element("div", "b26-source-backed-brief__metric");
    metric.appendChild(element("strong", "", String(value)));
    metric.appendChild(element("span", "", label));
    countsOutput.appendChild(metric);
  }

  function renderCounts(snapshot) {
    appendMetric("Resolved records", snapshot.counts.resolved_records);
    appendMetric("Unresolved records", snapshot.counts.unresolved_records);
    appendMetric("Bounded excerpts", snapshot.counts.bounded_excerpts);
    const note = element("p", "b26-source-backed-brief__count-note");
    note.textContent = "Submitted: " + snapshot.counts.submitted_ids + " · Rejected: " + snapshot.counts.invalid_inputs + " · Duplicates collapsed: " + snapshot.counts.duplicate_inputs;
    countsOutput.appendChild(note);
  }

  function appendLink(parent, label, url) {
    const safeUrl = safeOriginalUrl(url) || safeBase2026Url(url);
    if (!safeUrl) {
      parent.appendChild(element("span", "is-unresolved", label + " unavailable"));
      return;
    }
    const link = element("a", "", label);
    link.href = safeUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    parent.appendChild(link);
  }

  function renderRecord(record, index) {
    const card = element("article", "b26-source-backed-brief__record-card");
    const top = element("div", "b26-source-backed-brief__record-top");
    const heading = element("div");
    heading.appendChild(element("p", "b26-source-backed-brief__record-index", "Record " + String(index + 1).padStart(2, "0")));
    const title = record.title || (record.lookup_status === "resolved" ? "Resolved public record" : "Unresolved submitted ID");
    const headingTitle = element("h3");
    headingTitle.appendChild(document.createTextNode(title + " "));
    const idCode = element("code", "", record.record_id);
    headingTitle.appendChild(idCode);
    heading.appendChild(headingTitle);
    top.appendChild(heading);
    top.appendChild(element("span", "b26-source-backed-brief__record-state", record.lookup_status === "resolved" ? "Resolved" : "Unresolved"));
    top.lastChild.dataset.state = record.lookup_status === "resolved" ? "complete" : "unresolved";
    card.appendChild(top);

    const meta = element("dl", "b26-source-backed-brief__record-meta");
    const creatorDd = element("dd", record.creator && record.creator.key ? "" : "is-unresolved");
    if (record.creator && record.creator.url) appendLink(creatorDd, record.creator.label, record.creator.url);
    else creatorDd.textContent = record.creator && record.creator.label ? record.creator.label : "Creator attribution unavailable";
    appendDefinition(meta, "Creator", creatorDd.textContent || record.creator.label, !(record.creator && record.creator.key));
    const originalDd = element("dd", record.original_source_url ? "" : "is-unresolved");
    if (record.original_source_url) appendLink(originalDd, "Open original source", record.original_source_url);
    else originalDd.textContent = "Original source URL unavailable";
    appendDefinition(meta, "Original source", originalDd.textContent || "Original source URL unavailable", !record.original_source_url);
    appendDefinition(meta, "Published", record.published_date || "Published date unavailable", !record.published_date);
    appendDefinition(meta, "Source ID", record.source_id || "Source ID unavailable", !record.source_id);
    card.appendChild(meta);

    const excerptsSection = element("section", "b26-source-backed-brief__record-excerpts");
    excerptsSection.appendChild(element("h4", "", "Bounded public excerpts"));
    if (record.excerpts && record.excerpts.length) {
      const list = element("ul", "b26-source-backed-brief__excerpt-list");
      record.excerpts.forEach(function (passage) {
        const item = element("li");
        item.appendChild(element("p", "b26-source-backed-brief__excerpt", passage.excerpt));
        const passageMeta = [];
        if (passage.passage_id) passageMeta.push(passage.passage_id);
        if (passage.chunk_index !== null && passage.chunk_index !== undefined) passageMeta.push("chunk " + passage.chunk_index);
        if (passageMeta.length) item.appendChild(element("span", "b26-source-backed-brief__excerpt-meta", passageMeta.join(" · ")));
        list.appendChild(item);
      });
      excerptsSection.appendChild(list);
    } else {
      excerptsSection.appendChild(element("p", "b26-source-backed-brief__record-unknowns", "No bounded public excerpt was returned."));
    }
    card.appendChild(excerptsSection);

    const unknowns = Array.isArray(record.unknowns) ? record.unknowns : [];
    if (unknowns.length || record.resolution_reason) {
      const unknownPanel = element("div", "b26-source-backed-brief__record-unknowns");
      unknownPanel.appendChild(element("strong", "", record.lookup_status === "resolved" ? "Known gaps" : "Lookup note"));
      const list = element("ul");
      unknowns.forEach(function (detail) { list.appendChild(element("li", "", detail)); });
      if (record.resolution_reason) list.appendChild(element("li", "", "Resolution reason: " + record.resolution_reason));
      unknownPanel.appendChild(list);
      card.appendChild(unknownPanel);
    }

    const actions = element("div", "b26-source-backed-brief__record-actions");
    if (record.base2026_url) {
      const link = element("a", "", "Open Base2026 record");
      link.href = safeBase2026Url(record.base2026_url);
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      if (link.href) actions.appendChild(link);
    }
    if (record.original_source_url) {
      const link = element("a", "", "Open original source");
      link.href = safeOriginalUrl(record.original_source_url);
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      if (link.href) actions.appendChild(link);
    }
    if (actions.childNodes.length) card.appendChild(actions);
    return card;
  }

  function renderUnknowns(snapshot) {
    if (!snapshot.unknowns.length) {
      unknownsOutput.appendChild(element("p", "", "No additional unknowns were recorded for this bounded response."));
      return;
    }
    const list = element("ul");
    snapshot.unknowns.forEach(function (entry) {
      const item = element("li");
      const prefix = entry.record_id ? entry.record_id + " — " : "Input — ";
      item.textContent = prefix + entry.detail;
      list.appendChild(item);
    });
    unknownsOutput.appendChild(list);
  }

  function renderLimitations(snapshot) {
    snapshot.limitations.forEach(function (limitation) {
      limitationsOutput.appendChild(element("li", "", limitation));
    });
  }

  function renderSnapshot(snapshot) {
    currentSnapshot = snapshot;
    resultTitle.textContent = "Inspectable source-backed " + snapshot.request.deliverable_label.toLowerCase();
    renderRequest(snapshot);
    renderCounts(snapshot);
    snapshot.records.forEach(function (record, index) { recordList.appendChild(renderRecord(record, index)); });
    if (!snapshot.records.length) recordList.appendChild(element("p", "", "No accepted public record IDs were available for preview."));
    renderUnknowns(snapshot);
    renderLimitations(snapshot);
    exportPanel.hidden = snapshot.records.length === 0;
    results.hidden = false;
    const statusMessage = snapshot.status === "complete"
      ? "Preview ready: every accepted ID resolved through the public read-only lookup."
      : snapshot.status === "partial"
        ? "Partial preview: unresolved records or rejected input remain visible below."
        : "No accepted record resolved through the public read-only lookup; inspect the unresolved IDs below.";
    setStatus(snapshot.status === "complete" ? "success" : snapshot.status === "partial" ? "partial" : "error", statusMessage);
    emitAnalytics("brief_preview_created", {
      deliverable: snapshot.request.deliverable,
      response_class: snapshot.status,
      selected_count_bucket: countBucket(snapshot.counts.submitted_ids),
      resolved_count_bucket: countBucket(snapshot.counts.resolved_records),
      viewport_class: viewportClass()
    });
    if (!completedForRun) {
      completedForRun = true;
      emitAnalytics("brief_completed", {
        response_class: snapshot.status,
        deliverable: snapshot.request.deliverable,
        selected_count_bucket: countBucket(snapshot.counts.submitted_ids),
        viewport_class: viewportClass()
      });
    }
  }

  function mdText(value) {
    return cleanText(String(value === null || value === undefined ? "" : value), 2000)
      .replace(/\\/gu, "\\\\")
      .replace(/[\[\]`]/gu, "\\$&")
      .replace(/&/gu, "&amp;")
      .replace(/</gu, "&lt;")
      .replace(/>/gu, "&gt;")
      .replace(/\|/gu, "\\|");
  }

  function mdUrl(value) {
    const safe = safeOriginalUrl(value) || safeBase2026Url(value);
    if (!safe) return "";
    return "<" + safe.replace(/[<>\s]/gu, "") + ">";
  }

  function mdLink(label, url, fallback) {
    const safeUrl = mdUrl(url);
    return safeUrl ? "[" + mdText(label) + "](" + safeUrl + ")" : mdText(fallback || label + " unavailable");
  }

  function markdownSnapshot(snapshot) {
    const lines = [
      "# Base2026 Source-backed Brief",
      "",
      "This deterministic export is a reading scaffold. It does not infer truth, consensus or independence, and it does not synthesize a conclusion.",
      "",
      "## Request",
      "",
      "- Question: " + mdText(snapshot.request.question || "Not supplied"),
      "- Audience: " + mdText(snapshot.request.audience || "Not supplied"),
      "- Deliverable: " + mdText(snapshot.request.deliverable_label),
      "- Status: " + mdText(snapshot.status),
      "- Selected IDs: " + snapshot.counts.submitted_ids + " / " + MAX_RECORD_IDS,
      "",
      "## Inspectable records",
      ""
    ];
    if (!snapshot.records.length) lines.push("No accepted records were available.", "");
    snapshot.records.forEach(function (record, index) {
      lines.push("### " + (index + 1) + ". " + mdText(record.record_id), "");
      lines.push("- Lookup status: " + mdText(record.lookup_status));
      lines.push("- Creator: " + (record.creator && record.creator.url ? mdLink(record.creator.label, record.creator.url, record.creator.label) : mdText(record.creator && record.creator.label ? record.creator.label : "Creator attribution unavailable")));
      lines.push("- Original source: " + (record.original_source_url ? mdLink("Open original source", record.original_source_url, "Original source unavailable") : "Original source unavailable"));
      lines.push("- Base2026 record: " + (record.base2026_url ? mdLink("Open Base2026 record", record.base2026_url, "Base2026 record unavailable") : "Base2026 record unavailable"));
      lines.push("- Source ID: " + mdText(record.source_id || "Source ID unavailable"));
      lines.push("- Published: " + mdText(record.published_date || "Published date unavailable"), "");
      lines.push("#### Bounded public excerpts", "");
      if (record.excerpts && record.excerpts.length) {
        record.excerpts.forEach(function (passage) {
          const suffix = passage.passage_id ? " (`" + mdText(passage.passage_id) + "`)" : "";
          lines.push("> " + mdText(passage.excerpt) + suffix);
        });
      } else {
        lines.push("No bounded public excerpt was returned.");
      }
      lines.push("", "#### Unknowns", "");
      if (record.unknowns && record.unknowns.length) record.unknowns.forEach(function (unknown) { lines.push("- " + mdText(unknown)); });
      else lines.push("- None recorded for this record.");
      if (record.resolution_reason) lines.push("- Resolution reason: " + mdText(record.resolution_reason));
      lines.push("");
    });
    lines.push("## Unknowns", "");
    if (snapshot.unknowns.length) snapshot.unknowns.forEach(function (entry) { lines.push("- " + mdText(entry.record_id ? entry.record_id + " — " + entry.detail : entry.detail)); });
    else lines.push("- No additional unknowns were recorded.");
    lines.push("", "## Limitations", "");
    snapshot.limitations.forEach(function (limitation) { lines.push("- " + mdText(limitation)); });
    lines.push("", "## Public boundary", "", "- Read-only public Base2026 fields only.", "- Raw captions, raw ASR, media files, private data and writes are excluded.", "- Truth, consensus and independence are not assessed.", "");
    return lines.join("\n");
  }

  function jsonSnapshot(snapshot) {
    return JSON.stringify(snapshot, null, 2) + "\n";
  }

  function downloadText(filename, textValue, mimeType) {
    const blob = new Blob([textValue], { type: mimeType + ";charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = element("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  async function copyText(textValue) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(textValue);
      return true;
    }
    const textarea = element("textarea");
    textarea.value = textValue;
    textarea.setAttribute("readonly", "true");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    let copied = false;
    try { copied = document.execCommand("copy"); } catch (_error) { copied = false; }
    textarea.remove();
    return copied;
  }

  async function exportSnapshot(format, action) {
    if (!currentSnapshot) return;
    const isMarkdown = format === "markdown";
    const textValue = isMarkdown ? markdownSnapshot(currentSnapshot) : jsonSnapshot(currentSnapshot);
    try {
      if (action === "copy") {
        const copied = await copyText(textValue);
        if (!copied) throw new Error("copy_unavailable");
        exportStatus.textContent = format.toUpperCase() + " copied to the clipboard.";
      } else {
        downloadText("base2026-source-backed-brief." + (isMarkdown ? "md" : "json"), textValue, isMarkdown ? "text/markdown" : "application/json");
        exportStatus.textContent = format.toUpperCase() + " download prepared in your browser.";
      }
      emitAnalytics("brief_exported", {
        export_format: format,
        export_action: action,
        selected_count_bucket: countBucket(currentSnapshot.counts.submitted_ids),
        resolved_count_bucket: countBucket(currentSnapshot.counts.resolved_records),
        viewport_class: viewportClass()
      });
    } catch (_error) {
      exportStatus.textContent = "The browser did not permit that export action; the preview remains available for manual selection.";
    }
  }

  function readRequest() {
    const questionRaw = typeof questionInput.value === "string" ? questionInput.value.trim() : "";
    const audienceRaw = typeof audienceInput.value === "string" ? audienceInput.value.trim() : "";
    const deliverable = cleanText(deliverableInput.value, 20).toLowerCase();
    const question = cleanText(questionRaw, MAX_QUESTION_CHARS);
    const audience = cleanText(audienceRaw, MAX_AUDIENCE_CHARS);
    const parsed = parseIds(idsInput.value);
    const invalidFields = [];
    if (questionRaw.length > MAX_QUESTION_CHARS || question.length < 3) invalidFields.push("question");
    if (audienceRaw.length > MAX_AUDIENCE_CHARS || audience.length < 2) invalidFields.push("audience");
    if (!DELIVERABLES.has(deliverable)) invalidFields.push("deliverable");
    if (!parsed.accepted.length) invalidFields.push("ids");
    return {
      request: { question: question, audience: audience, deliverable: DELIVERABLES.has(deliverable) ? deliverable : "brief" },
      parsed: parsed,
      invalidFields: invalidFields
    };
  }

  async function runBrief(inputSource) {
    if (activeController) activeController.abort();
    completedForRun = false;
    const requestData = readRequest();
    resetOutput();
    results.hidden = false;
    resultTitle.textContent = "Inspectable source-backed preview";
    if (requestData.invalidFields.length) {
      setStatus("error", "Complete the required fields and add at least one canonical public record/source ID.");
      emitAnalytics("brief_completed", { response_class: "invalid_input", invalid_field_bucket: countBucket(requestData.invalidFields.length), input_source: inputSource || "typed", viewport_class: viewportClass() });
      completedForRun = true;
      return;
    }
    emitAnalytics("brief_required_fields_completed", {
      deliverable: requestData.request.deliverable,
      selected_count_bucket: countBucket(requestData.parsed.submittedIdCount),
      input_source: inputSource || "typed",
      viewport_class: viewportClass()
    });
    setLoading(true);
    setStatus("loading", "Resolving selected public records…");
    const controller = new AbortController();
    activeController = controller;
    try {
      const outcomes = await resolveAll(requestData.parsed.accepted, controller.signal);
      if (controller.signal.aborted || activeController !== controller) return;
      renderSnapshot(buildSnapshot(requestData.request, requestData.parsed, outcomes));
    } finally {
      if (activeController === controller) {
        activeController = null;
        setLoading(false);
      }
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    runBrief("typed");
  });
  copyMarkdown.addEventListener("click", function () { exportSnapshot("markdown", "copy"); });
  downloadMarkdown.addEventListener("click", function () { exportSnapshot("markdown", "download"); });
  copyJson.addEventListener("click", function () { exportSnapshot("json", "copy"); });
  downloadJson.addEventListener("click", function () { exportSnapshot("json", "download"); });

  document.documentElement.classList.add("source-backed-brief-enhanced");

  /* Test-only exports can be enabled by a harness before this runtime starts. */
  if (globalThis.__sourceBackedBriefTestApi) {
    globalThis.__sourceBackedBriefTestApi = {
      parseIds: parseIds,
      publicBoundaryIsSafe: publicBoundaryIsSafe,
      unsafePublicMetadata: unsafePublicMetadata,
      passagePublicMetadataIsSafe: passagePublicMetadataIsSafe,
      safePassages: safePassages,
      normalizeResolved: normalizeResolved,
      unresolvedRecord: unresolvedRecord,
      buildSnapshot: buildSnapshot,
      buildBriefSnapshot: buildBriefSnapshot,
      markdownSnapshot: markdownSnapshot,
      jsonSnapshot: jsonSnapshot,
      safeOriginalUrl: safeOriginalUrl,
      safeBase2026Url: safeBase2026Url
    };
  }
}());
