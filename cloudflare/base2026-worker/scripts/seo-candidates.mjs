#!/usr/bin/env node

/** Research metadata only. No file I/O, account, publication or retry transport. */
import { createHash } from "node:crypto";

export const SCAN_SCHEMA = "base2026.seo-candidate-scan.v1";
export const PUBLIC_ORIGIN = "https://base2026.dev";
export const SCAN_LIMITS = Object.freeze({ documents: 100, response_bytes: 3 * 1024 * 1024, timeout_ms: 18_000, guides: 8 });
export const USER_AGENT = "Base2026-ReadOnly-SEO-Candidate-Scanner/1.0 (+https://base2026.dev/methodology)";
const INDEX_UID = "base2026_public_tiktok";
const ENDPOINTS = Object.freeze({ guides: "/api/guides", search: "/api/search/multi-search" });
export const RESEARCH_INTENTS = Object.freeze([
  ["internal-linking", "internal"],
  ["ai-citation-tracking", "AI citation tracking"],
  ["ai-search-reporting", "AI search reporting"],
  ["search-console-low-hanging-fruit", "Search Console"],
  ["content-freshness", "content refresh"],
  ["service-page-seo", "service pages"],
  ["technical-seo-indexing", "technical SEO"],
  ["review-strategy", "local reviews"],
  ["brand-mentions-ai-visibility", "brand mentions"],
  ["schema-ai-citations", "schema markup"],
  ["llms-txt-risk", "llms.txt"],
  ["ecommerce-seo-collection-pages", "collection pages"],
].map(([id, query]) => Object.freeze({ id, query, canonical: `${PUBLIC_ORIGIN}/topics/${id}` })));

const HEX256 = /^[a-f0-9]{64}$/u;
const VIDEO_ID = /^[0-9]{10,30}$/u;
const CHUNK_ID = /^chunk-transcript(?:-polished)?-([0-9]{10,30})-[0-9]{4}$/u;
const SOURCE_ID = /^tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})$/u;
const HANDLE = /^@[A-Za-z0-9._-]{2,256}$/u;
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const clock = () => new Date().toISOString();
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const sorted = (values) => [...new Set(values)].sort(compare);
const sha256 = (value) => createHash("sha256").update(value, "utf8").digest("hex");

export class CandidateScanError extends Error {
  constructor(code, details = {}) {
    // Never include rejected input, response content, URLs from a row or stacks.
    super(code);
    this.name = "CandidateScanError";
    this.code = code;
    this.details = details;
  }
}

function fail(code, details) { throw new CandidateScanError(code, details); }
function record(value, code) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(code);
  return value;
}
function exactString(value, maxBytes, code = "DOCUMENT_INVALID") {
  if (typeof value !== "string" || value.length > maxBytes || Buffer.byteLength(value, "utf8") > maxBytes) fail(code);
  return value;
}
function intentFor(id) {
  const intent = RESEARCH_INTENTS.find((entry) => entry.id === id);
  if (!intent) fail("ARGUMENTS_INVALID");
  return intent;
}

export function parseArguments(argv) {
  if (!Array.isArray(argv)) fail("ARGUMENTS_INVALID");
  if (argv.length === 0) return [RESEARCH_INTENTS[0].id];
  if (argv.length === 1 && argv[0] === "--all") return RESEARCH_INTENTS.map((intent) => intent.id);
  if (argv.length === 2 && argv[0] === "--topic") return [intentFor(argv[1]).id];
  fail("ARGUMENTS_INVALID");
}

/** Match hashPublicEvidenceDocument: eight alphabetical keys, exact strings;
 * only SQL 0/1 versus public false/true is normalized. Contract-tested below.
 */
export function hashCandidateDocument(value) {
  const row = record(value, "DOCUMENT_INVALID");
  const flag = row.full_transcript_public;
  if (flag !== false && flag !== true && flag !== 0 && flag !== 1) fail("DOCUMENT_INVALID");
  const fields = {
    admission_state: exactString(row.admission_state, 32),
    body: exactString(row.body, 64 * 1024),
    creator_handle: exactString(row.creator_handle, 257),
    full_transcript_public: flag === true || flag === 1,
    id: exactString(row.id, 120),
    source_id: exactString(row.source_id, 300),
    source_url: exactString(row.source_url, 2_048),
    title: exactString(row.title, 4_800),
  };
  return sha256(JSON.stringify(fields));
}

function candidate(row) {
  const document_sha256 = hashCandidateDocument(row);
  const chunk = CHUNK_ID.exec(row.id);
  const source = SOURCE_ID.exec(row.source_id);
  if ((!chunk && !/^[a-f0-9]{40}$/u.test(row.id)) || !source || !VIDEO_ID.test(row.video_id)
    || source[2] !== row.video_id || (chunk && chunk[1] !== row.video_id)
    || (row.creator_handle !== "" && !HANDLE.test(row.creator_handle))) fail("DOCUMENT_IDENTITY_INVALID");
  if ((row.full_transcript_public !== false && row.full_transcript_public !== 0)
    || row.admission_state !== "normal_public_card" || row.platform !== "tiktok"
    || row.source_type !== "tiktok_video" || row.public_policy !== "search_passage"
    || row.public_surface !== "main_search") fail("PUBLIC_BOUNDARY_INVALID");
  // Explicit allowlist: no title, body, quote, URL, policy, review or extra field.
  return { id: row.id, source_id: row.source_id, video_id: row.video_id,
    creator_handle: row.creator_handle, document_sha256 };
}

export function summarizeSearchResponse(value, topic) {
  const intent = intentFor(topic);
  const data = record(value, "SEARCH_RESPONSE_INVALID");
  if (!Array.isArray(data.results) || data.results.length !== 1) fail("SEARCH_RESPONSE_INVALID");
  const result = record(data.results[0], "SEARCH_RESPONSE_INVALID");
  if (result.indexUid !== INDEX_UID || result.query !== intent.query || result.limit !== SCAN_LIMITS.documents
    || result.offset !== 0 || !Array.isArray(result.hits)) fail("SEARCH_RESPONSE_INVALID");
  const total = result.estimatedTotalHits;
  if (!Number.isSafeInteger(total) || total < 0 || result.hits.length !== Math.min(total, SCAN_LIMITS.documents)) {
    fail("SEARCH_COUNT_MISMATCH");
  }
  const candidates = result.hits.map(candidate).sort((a, b) => compare(a.id, b.id));
  if (new Set(candidates.map((entry) => entry.id)).size !== candidates.length) fail("DUPLICATE_DOCUMENT_ID");
  const byBody = new Map();
  for (const row of result.hits) {
    const group = byBody.get(row.body) ?? [];
    group.push({ id: row.id, source_id: row.source_id, video_id: row.video_id });
    byBody.set(row.body, group);
  }
  const duplicate_content = [...byBody.entries()].filter(([, rows]) => rows.length > 1).map(([body, rows]) => ({
    classification: "duplicate_content", lineage: "not_verified",
    body_sha256: sha256(body), body_is_empty: body.length === 0,
    document_ids: sorted(rows.map((row) => row.id)),
    source_ids: sorted(rows.map((row) => row.source_id)), video_ids: sorted(rows.map((row) => row.video_id)),
  })).sort((a, b) => compare(a.body_sha256, b.body_sha256) || compare(a.document_ids[0], b.document_ids[0]));
  return {
    intent: intent.id, canonical: intent.canonical, query: intent.query,
    scope: "query_matches_first_page", truncated: total > candidates.length,
    total_matches: total, returned: candidates.length,
    source_count: new Set(candidates.map((entry) => entry.source_id)).size,
    video_count: new Set(candidates.map((entry) => entry.video_id)).size,
    creator_handle_count: new Set(candidates.map((entry) => entry.creator_handle).filter(Boolean)).size,
    snapshot_sha256: sha256(JSON.stringify(candidates.map((entry) => ({ document_id: entry.id, document_sha256: entry.document_sha256 })))),
    candidates, duplicate_content,
  };
}

function guideTimestamp(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/u.test(value)
    || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString() !== value) fail("GUIDE_INDEX_INVALID");
  return value;
}

export function parseGuideIndex(value) {
  const data = record(value, "GUIDE_INDEX_INVALID");
  if (data.schema_version !== "base2026.evidence-guide-index.v1" || !Array.isArray(data.guides)
    || data.guides.length > SCAN_LIMITS.guides) fail("GUIDE_INDEX_INVALID");
  let registered_topics = null;
  if (Object.hasOwn(data, "registered_topics")) {
    if (!Array.isArray(data.registered_topics) || data.registered_topics.length > SCAN_LIMITS.guides
      || data.registered_topics.some((slug) => typeof slug !== "string" || slug.length > 120 || !SLUG.test(slug))) fail("GUIDE_INDEX_INVALID");
    registered_topics = sorted(data.registered_topics);
    if (registered_topics.length !== data.registered_topics.length) fail("GUIDE_INDEX_DUPLICATE");
  }
  const guides = data.guides.map((value) => {
    const guide = record(value, "GUIDE_INDEX_INVALID");
    if (typeof guide.slug !== "string" || guide.slug.length > 120 || !SLUG.test(guide.slug)
      || !Number.isSafeInteger(guide.revision) || guide.revision < 1 || !HEX256.test(guide.payload_sha256)
      || guide.public_path !== `/topics/${guide.slug}` || guide.canonical_url !== PUBLIC_ORIGIN + guide.public_path) fail("GUIDE_INDEX_INVALID");
    if (registered_topics !== null && !registered_topics.includes(guide.slug)) fail("GUIDE_REGISTRY_MISMATCH");
    const published_at = guideTimestamp(guide.published_at);
    const updated_at = guideTimestamp(guide.updated_at);
    if (updated_at < published_at) fail("GUIDE_INDEX_INVALID");
    // Bounded metadata only; do not copy descriptions, author text or payloads.
    return { slug: guide.slug, revision: guide.revision, published_at, updated_at,
      public_path: guide.public_path, canonical_url: guide.canonical_url, payload_sha256: guide.payload_sha256 };
  }).sort((a, b) => compare(a.slug, b.slug));
  if (new Set(guides.map((guide) => guide.slug)).size !== guides.length) fail("GUIDE_INDEX_DUPLICATE");
  return { registered_topics, guides };
}

/** Fixed endpoints/methods and fixed query strings even when imported in tests. */
export async function readPublicJson(endpoint, { topic = "internal-linking", fetchImpl = globalThis.fetch, now = clock } = {}) {
  if (!Object.hasOwn(ENDPOINTS, endpoint)) fail("ENDPOINT_NOT_ALLOWED");
  const intent = endpoint === "search" ? intentFor(topic) : null;
  const url = PUBLIC_ORIGIN + ENDPOINTS[endpoint];
  const method = intent ? "POST" : "GET";
  const controller = new AbortController();
  let reader;
  let response;
  let timer;
  const details = { endpoint: ENDPOINTS[endpoint] };
  const timedOut = new Promise((_, reject) => {
    timer = setTimeout(() => { controller.abort(); reject(new CandidateScanError("REQUEST_TIMEOUT", details)); }, SCAN_LIMITS.timeout_ms);
  });
  const work = async () => {
    const headers = { Accept: "application/json", "User-Agent": USER_AGENT };
    const init = { method, headers, credentials: "omit", redirect: "error", cache: "no-store", referrerPolicy: "no-referrer", signal: controller.signal };
    if (intent) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify({ queries: [{ indexUid: INDEX_UID, q: intent.query, limit: SCAN_LIMITS.documents,
        offset: 0, attributesToRetrieve: "*", attributesToHighlight: [], attributesToCrop: [] }] });
    }
    response = await fetchImpl(url, init);
    if (!(response instanceof Response) || response.redirected || (response.url && response.url !== url)) fail("RESPONSE_ORIGIN_INVALID", details);
    if (response.status === 429) fail("RATE_LIMITED", { ...details, http_status: 429 });
    const receipt = { endpoint: ENDPOINTS[endpoint], method, http_status: response.status, response_bytes: 0, checked_at: now() };
    if (endpoint === "guides" && (response.status === 404 || response.status === 503)) return { data: null, receipt };
    if (response.status !== 200) fail("HTTP_ERROR", { ...details, http_status: response.status });
    if (!/^application\/json(?:\s*;|$)/iu.test(response.headers.get("Content-Type") ?? "")) fail("RESPONSE_NOT_JSON", details);
    const declared = response.headers.get("Content-Length");
    if (declared !== null && (!/^\d+$/u.test(declared) || !Number.isSafeInteger(Number(declared)))) fail("RESPONSE_LENGTH_INVALID", details);
    if (declared !== null && Number(declared) > SCAN_LIMITS.response_bytes) fail("RESPONSE_TOO_LARGE", details);
    if (!response.body) fail("RESPONSE_NOT_JSON", details);
    reader = response.body.getReader();
    const chunks = [];
    let size = 0;
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      if (!(chunk.value instanceof Uint8Array)) fail("RESPONSE_INVALID", details);
      size += chunk.value.byteLength;
      if (size > SCAN_LIMITS.response_bytes) fail("RESPONSE_TOO_LARGE", details);
      chunks.push(chunk.value);
    }
    let data;
    try { data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(Buffer.concat(chunks, size))); }
    catch { fail("RESPONSE_NOT_JSON", details); }
    return { data, receipt: { ...receipt, response_bytes: size, checked_at: now() } };
  };
  try { return await Promise.race([work(), timedOut]); }
  catch (error) {
    if (error instanceof CandidateScanError) throw error;
    fail("REQUEST_FAILED", details);
  } finally {
    clearTimeout(timer);
    controller.abort();
    // Never wait on an uncooperative error stream or retry it.
    try { void (reader ? reader.cancel() : response?.body?.cancel())?.catch(() => {}); } catch { /* no response content */ }
  }
}

export async function scanCandidates(argv = [], options = {}) {
  const topics = parseArguments(argv);
  const now = options.now ?? clock;
  const requests = [];
  const indexResponse = await readPublicJson("guides", options);
  requests.push(indexResponse.receipt);
  const status = indexResponse.receipt.http_status;
  const guide_index = status === 200
    ? { status: "available", ...parseGuideIndex(indexResponse.data) }
    : { status: status === 404 ? "not_deployed" : "held_or_unavailable", registered_topics: null, guides: null };
  const intents = [];
  for (const topic of topics) {
    const response = await readPublicJson("search", { ...options, topic });
    requests.push(response.receipt);
    const summary = summarizeSearchResponse(response.data, topic);
    const metadata = guide_index.guides?.find((guide) => guide.slug === topic) ?? null;
    intents.push({ ...summary, registered_guide: guide_index.registered_topics?.includes(topic) ?? null,
      current_guide: { status: guide_index.status === "available" ? (metadata ? "listed" : "not_listed") : "unknown", metadata } });
  }
  return {
    schema_version: SCAN_SCHEMA, checked_at: now(), read_only: true, purpose: "research_delta_only",
    limitations: [
      "Fixed research intents and corpus matches are not search-demand or publication authorization.",
      "Canonicals are configured topic associations; this scan does not check their indexability.",
      "Counts cover returned query matches, not the whole corpus; creator handles do not establish independence.",
      "Identical bodies mean duplicate content only, not verified work lineage or reuse rights.",
      "No semantic review, registration, publication, account access or automatic retry occurs here.",
    ],
    guide_index, intents, requests,
  };
}

// Imports perform no requests. Both successful scans and sanitized errors are
// one JSON object on stdout; callers choose whether/how to retain the receipt.
if (import.meta.main) {
  try { process.stdout.write(`${JSON.stringify(await scanCandidates(process.argv.slice(2)))}\n`); }
  catch (error) {
    process.stdout.write(`${JSON.stringify({ schema_version: SCAN_SCHEMA, checked_at: clock(), read_only: true,
      status: "error", error: error instanceof CandidateScanError
        ? { code: error.code, ...error.details } : { code: "SCAN_FAILED" } })}\n`);
    process.exitCode = 1;
  }
}
