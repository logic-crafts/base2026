import { WorkerEntrypoint } from "cloudflare:workers";
import { inspectStoredEditorialArticle, publishEditorialArticle, type EditorialOverwrite } from "./editorial";
import { handleEditorialRoute } from "./editorial-routes";
import { handleSourceCatalog } from "./source-catalog";
import { handleEvidenceGuideRoute } from "./evidence-guide-routes";
import { memberError, type MemberAuthEnv } from "./member-auth";
import { handleMemberRequest } from "./member-research";
import {
  applyPublicProjection,
  inspectPublicSource,
  rollbackPublicProjection,
  verifyPublicProjection,
} from "./public-projection";

const INDEX_UID = "base2026_public_tiktok" as const;
const OUTREACH_INDEX_UID = "base2026_public_outreach" as const;
const SEARCH_INDEXES = Object.freeze({
  [INDEX_UID]: "tiktok",
  [OUTREACH_INDEX_UID]: "outreach",
} as const);
const MAX_BODY_BYTES = 64 * 1024;
const MAX_QUERY_LENGTH = 200;
const MAX_MULTI_QUERIES = 4;
const MAX_LIMIT = 100;
const MAX_OFFSET = 10_000;
const MAX_FACET_VALUES = 100;
const DEFAULT_LIMIT = 20;
const EVIDENCE_BRIEF_CANDIDATE_LIMIT = 24;
const EVIDENCE_BRIEF_SOURCE_LIMIT = 6;
const EVIDENCE_BRIEF_V2_CANDIDATE_LIMIT = 60;
const EVIDENCE_BRIEF_V2_SOURCE_LIMIT = 5;
const EVIDENCE_BRIEF_V2_CREATOR_LIMIT = 2;
const MIN_EVIDENCE_BRIEF_QUERY_LENGTH = 3;
const EVIDENCE_BRIEF_VERSION = "base2026.evidence-brief.v2";
const EVIDENCE_BRIEF_RANKING_VERSION = "d1-fts5-bm25-and-v2";
const EVIDENCE_BRIEF_STOP_WORDS = new Set([
  "a", "about", "an", "and", "are", "as", "at", "be", "by", "do", "does", "expert", "experts", "for",
  "from", "how", "in", "is", "measure", "measuring", "of", "on", "or", "practitioner", "practitioners",
  "prioritize", "prioritise", "recommend", "recommended", "recommending", "saying", "says", "should", "support",
  "the", "to", "use", "using", "what", "when", "where", "which", "who", "why", "with",
]);
const FORM_ORIGIN = "https://base2026.dev";
const FORM_CONSENT_VERSION = "2026-08-20";
const MIN_FORM_COMPLETION_MS = 1_200;
const MAX_FORM_COMPLETION_MS = 2 * 60 * 60 * 1_000;
const PUBLIC_ORIGIN = "https://base2026.dev";
const MAX_DYNAMIC_SITEMAP_URLS = 50_000;
const DYNAMIC_SOURCE_ROUTE = /^\/sources\/tiktok-video-(\d{10,30})\/?$/u;
const SOCIAL_IMAGE_URL = `${PUBLIC_ORIGIN}/static/assets/base2026-ai-visibility-card.png`;

const PUBLIC_FIELDS = Object.freeze([
  "admission_state",
  "avatar_url",
  "body",
  "captured_at",
  "chunk_id",
  "chunk_index",
  "creator_display_name",
  "creator_handle",
  "creator_id",
  "creator_url",
  "full_transcript_public",
  "handle",
  "id",
  "item_id",
  "platform",
  "post_id",
  "public_policy",
  "public_surface",
  "published_at",
  "published_date",
  "source_id",
  "source_type",
  "source_url",
  "title",
  "title_source",
  "title_status",
  "topic_labels",
  "topics",
  "video_id",
  "year",
] as const);
type PublicField = (typeof PUBLIC_FIELDS)[number];

const OUTREACH_PUBLIC_FIELDS = Object.freeze([
  "id",
  "collection",
  "record_type",
  "source_record_id",
  "title",
  "summary",
  "tactic",
  "evidence_summary",
  "verdict",
  "source_url",
  "platform",
  "author_name",
  "author_handle",
  "observed_at",
  "score",
  "source_status",
  "topics",
  "lanes",
  "cost",
  "complexity",
  "effect_speed",
  "public_policy",
  "reviewed_at",
  "source_hash",
  "dedup_key",
  "language",
] as const);
type OutreachPublicField = (typeof OUTREACH_PUBLIC_FIELDS)[number];

const FACET_COLUMNS = Object.freeze({
  creator_id: "creator_id",
  handle: "handle",
  platform: "platform",
  published_date: "published_date",
  source_type: "source_type",
  year: "year",
} as const);
const FACET_FIELDS = Object.freeze([
  ...Object.keys(FACET_COLUMNS),
  "topics",
] as const);
type FacetField = (typeof FACET_FIELDS)[number];

const OUTREACH_FACET_COLUMNS = Object.freeze({
  platform: "platform",
  source_status: "source_status",
  cost: "cost",
  complexity: "complexity",
  effect_speed: "effect_speed",
  language: "language",
} as const);
const OUTREACH_FACET_FIELDS = Object.freeze([
  "platform",
  "source_status",
  "topics",
  "lanes",
  "cost",
  "complexity",
  "effect_speed",
  "language",
] as const);
type OutreachFacetField = (typeof OUTREACH_FACET_FIELDS)[number];
type OutreachFilterField = OutreachFacetField | "score" | "observed_at";
const OUTREACH_SEARCHABLE_FIELDS = Object.freeze([
  "title",
  "summary",
  "tactic",
  "evidence_summary",
  "verdict",
  "source_url",
  "platform",
  "author_name",
  "author_handle",
  "cost",
  "complexity",
  "effect_speed",
] as const);
const OUTREACH_ALLOWED_SORTS = Object.freeze([
  "observed_at:asc",
  "observed_at:desc",
  "score:asc",
  "score:desc",
] as const);

const SEARCHABLE_FIELDS = Object.freeze(["body", "title", "topic_labels", "handle", "creator_id", "platform"] as const);
const ALLOWED_SORTS = Object.freeze([
  "published_date:asc",
  "published_date:desc",
  "year:asc",
  "year:desc",
] as const);

const JSON_HEADERS = Object.freeze({
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
  "Cache-Control": "no-store",
});
const PUBLIC_SECURITY_HEADERS = Object.freeze({
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Frame-Options": "SAMEORIGIN",
  "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
});

type EnvWithBindings = Env & MemberAuthEnv & { INBOX_DB?: D1Database; OUTREACH_DB?: D1Database };

const MEMBER_API_PATH = /^\/api\/(?:auth|my-research)(?:\/|$)/u;
const MEMBER_PAGE_PATH = /^\/my-research(?:\/|$)/u;
const MEMBER_PAGE_CSP = [
  "default-src 'none'",
  "script-src 'self'",
  "style-src 'self' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data:",
  "connect-src 'self'",
  "base-uri 'none'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
].join("; ");

type FormKind = "support" | "partner";

interface InboxSubmission {
  id: string;
  kind: FormKind;
  name: string;
  email: string;
  organization: string;
  role: string;
  category: string;
  publicUrl: string;
  attribution: string;
  payload: Record<string, string>;
}

interface SearchQuery {
  indexUid: typeof INDEX_UID;
  q: string;
  limit: number;
  offset: number;
  facets: FacetField[];
  facetFilters: string[][];
  filter: Array<string | string[]>;
  sort: string;
  attributesToRetrieve: PublicField[] | "*";
  attributesToHighlight: string[];
  attributesToCrop: string[];
  cropMarker: string;
  highlightPreTag: string;
  highlightPostTag: string;
}

interface OutreachSearchQuery {
  indexUid: typeof OUTREACH_INDEX_UID;
  q: string;
  limit: number;
  offset: number;
  facets: OutreachFacetField[];
  facetFilters: string[][];
  filter: Array<string | string[]>;
  sort: string;
  attributesToRetrieve: OutreachPublicField[] | "*";
  attributesToHighlight: string[];
  attributesToCrop: string[];
  cropMarker: string;
  highlightPreTag: string;
  highlightPostTag: string;
}

interface SqlCondition {
  sql: string;
  params: string[];
}

interface SearchRow {
  [key: string]: unknown;
  id: string;
  topics_json: string;
  topic_labels_json: string;
  full_transcript_public: number;
}

interface EvidenceBriefCandidate {
  id: string;
  source_id: string;
  video_id: string;
  title: string;
  body: string;
  creator_handle: string;
  creator_display_name: string;
  source_url: string;
  published_date: string;
  topics_json: string;
  topic_labels_json: string;
  full_transcript_public: number;
  admission_state: string;
  claim_text: string | null;
  evidence_excerpt: string | null;
  evidence_start_seconds: number | null;
  evidence_end_seconds: number | null;
}

interface EvidenceBriefCountRow {
  matched_records: number;
}

interface EvidenceCorpusWatermarkRow {
  document_count: number;
  source_count: number;
  latest_captured_at: string | null;
}

interface ProjectedSourcePageRow {
  video_id: string;
  source_id: string;
  creator_handle: string;
  creator_url: string;
  source_url: string;
  published_date: string;
  ordinal: number;
  claim_text: string;
  suggested_action: string;
  topic_label: string;
  evidence_excerpt: string;
  evidence_start_seconds: number;
  evidence_end_seconds: number;
}

interface DynamicSitemapRow {
  video_id: string;
  lastmod: string;
}

interface OutreachSearchRow {
  [key: string]: unknown;
  id: string;
  topics_json: string;
  lanes_json: string;
}

class RequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;
  readonly allow?: string;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown>, allow?: string) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.allow = allow;
  }
}

function withPublicResponseHeaders(...headerSets: HeadersInit[]): Headers {
  const headers = new Headers();
  for (const headerSet of headerSets) {
    new Headers(headerSet).forEach((value, name) => headers.set(name, value));
  }
  for (const [name, value] of Object.entries(PUBLIC_SECURITY_HEADERS)) headers.set(name, value);
  return headers;
}

function publicRedirect(location: string, status: 301 | 308): Response {
  return new Response(null, {
    status,
    headers: withPublicResponseHeaders({ Location: location }),
  });
}

function publicAssetResponse(response: Response): Response {
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: withPublicResponseHeaders(response.headers),
  });
}

function privateMemberResponse(response: Response, page = false): Response {
  // Copy Headers directly: forEach/set would fold multiple Set-Cookie fields
  // into a single value and break OAuth state/session cookie handling.
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(PUBLIC_SECURITY_HEADERS)) headers.set(name, value);
  // Private routes must never inherit the public search API's wildcard CORS
  // or cache policy, including when authentication is disabled or fails.
  const corsHeaders: string[] = [];
  headers.forEach((_value, name) => { if (name.startsWith("access-control-")) corsHeaders.push(name); });
  for (const name of corsHeaders) headers.delete(name);
  headers.set("Cache-Control", "private, no-store");
  headers.set("X-Robots-Tag", "noindex, nofollow");
  headers.set("Referrer-Policy", "no-referrer");
  headers.set("X-Frame-Options", "DENY");
  headers.set("Cross-Origin-Resource-Policy", "same-origin");
  headers.set("Content-Security-Policy", page ? MEMBER_PAGE_CSP : "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function jsonResponse(payload: unknown, status = 200, headers: HeadersInit = {}): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: withPublicResponseHeaders(JSON_HEADERS, headers),
  });
}

function errorResponse(error: RequestError): Response {
  return jsonResponse(
    {
      error: {
        code: error.code,
        message: error.message,
        ...(error.details ? { details: error.details } : {}),
      },
    },
    error.status,
    error.code === "METHOD_NOT_ALLOWED" ? { Allow: error.allow ?? "GET, POST" } : undefined,
  );
}

function methodError(method: string, allow = "GET, POST"): RequestError {
  return new RequestError(405, "METHOD_NOT_ALLOWED", `method ${method} is not allowed`, undefined, allow);
}

function contentTypeIsJson(request: Request): boolean {
  const value = request.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase();
  return value === "application/json";
}

async function readBoundedBody(request: Request): Promise<string> {
  const contentLength = request.headers.get("content-length");
  if (contentLength && /^\d+$/.test(contentLength) && Number(contentLength) > MAX_BODY_BYTES) {
    throw new RequestError(413, "BODY_TOO_LARGE", `request body exceeds ${MAX_BODY_BYTES} bytes`);
  }
  if (!request.body) return "";
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      if (!result.value) continue;
      size += result.value.byteLength;
      if (size > MAX_BODY_BYTES) {
        await reader.cancel("body too large");
        throw new RequestError(413, "BODY_TOO_LARGE", `request body exceeds ${MAX_BODY_BYTES} bytes`);
      }
      chunks.push(result.value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(body);
}

function parseJsonBody(body: string): Record<string, unknown> {
  if (!body.trim()) throw new RequestError(400, "INVALID_JSON", "request body must be a non-empty JSON object");
  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new RequestError(400, "INVALID_JSON", "request body is not valid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new RequestError(400, "INVALID_BODY", "request body must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

function ensureString(value: unknown, field: string, maxLength = MAX_QUERY_LENGTH): string {
  if (typeof value !== "string") throw new RequestError(400, "INVALID_FIELD", `${field} must be a string`);
  if (value.length > maxLength) throw new RequestError(400, "FIELD_TOO_LONG", `${field} exceeds ${maxLength} characters`);
  return value;
}

function ensureInteger(value: unknown, field: string, min: number, max: number, fallback: number): number {
  if (value === undefined) return fallback;
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < min || value > max) {
    throw new RequestError(400, "INVALID_FIELD", `${field} must be an integer between ${min} and ${max}`);
  }
  return value;
}

function ensureStringArray(value: unknown, field: string, maxItems = 32, maxLength = 100): string[] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > maxItems) {
    throw new RequestError(400, "INVALID_FIELD", `${field} must be an array of at most ${maxItems} strings`);
  }
  return value.map((item, index) => ensureString(item, `${field}[${index}]`, maxLength));
}

function validatePublicField(field: string, option: string): PublicField {
  if (!PUBLIC_FIELDS.includes(field as PublicField)) {
    throw new RequestError(400, "UNSUPPORTED_FIELD", `${option} does not support field ${field}`);
  }
  return field as PublicField;
}

function validateFacets(value: unknown): FacetField[] {
  if (value === undefined) return [];
  if (value === "*") return [...FACET_FIELDS];
  if (!Array.isArray(value) || value.length > FACET_FIELDS.length) {
    throw new RequestError(400, "INVALID_FIELD", "facets must be an array of supported fields");
  }
  if (value.includes("*")) {
    if (value.length !== 1) throw new RequestError(400, "UNSUPPORTED_FACET", "facets wildcard cannot be combined with named facets");
    return [...FACET_FIELDS];
  }
  return value.map((item, index) => {
    if (typeof item !== "string" || !FACET_FIELDS.includes(item as FacetField)) {
      throw new RequestError(400, "UNSUPPORTED_FACET", `facets[${index}] is not supported`);
    }
    return item as FacetField;
  });
}

function validateFacetFilters(value: unknown): string[][] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > 32) {
    throw new RequestError(400, "INVALID_FIELD", "facetFilters must be an array");
  }
  const groups: string[][] = [];
  for (let index = 0; index < value.length; index += 1) {
    const group = Array.isArray(value[index]) ? value[index] : [value[index]];
    if (group.length > 16) throw new RequestError(400, "INVALID_FIELD", "facetFilters groups are too large");
    groups.push(group.map((item: unknown, itemIndex: number) => ensureString(item, `facetFilters[${index}][${itemIndex}]`, 300)));
  }
  return groups;
}

function validateFilter(value: unknown): Array<string | string[]> {
  if (value === undefined) return [];
  if (typeof value === "string") return [ensureString(value, "filter", 2_000).trim()];
  if (!Array.isArray(value) || value.length > 32) {
    throw new RequestError(400, "INVALID_FIELD", "filter must be a string or an array of filter expressions");
  }
  return value.map((item, index) => {
    if (Array.isArray(item)) {
      if (item.length < 1 || item.length > 16) throw new RequestError(400, "INVALID_FIELD", `filter[${index}] group is too large`);
      return item.map((part, partIndex) => ensureString(part, `filter[${index}][${partIndex}]`, 2_000).trim());
    }
    return ensureString(item, `filter[${index}]`, 2_000).trim();
  });
}

function validateTags(value: unknown, field: string, fallback: string): string {
  if (value === undefined) return fallback;
  const tag = ensureString(value, field, 32);
  if (!/^(?:<\/?[-a-zA-Z0-9_]+>|[-a-zA-Z0-9_/-]+)$/.test(tag)) {
    throw new RequestError(400, "INVALID_TAG", `${field} must be a simple tag marker`);
  }
  return tag;
}

function parseTikTokQuery(query: Record<string, unknown>, indexUid: string): SearchQuery {
  const allowed = new Set([
    "indexUid",
    "q",
    "limit",
    "offset",
    "facets",
    "facetFilters",
    "filter",
    "sort",
    "attributesToRetrieve",
    "attributesToHighlight",
    "attributesToCrop",
    "cropMarker",
    "highlightPreTag",
    "highlightPostTag",
  ]);
  for (const key of Object.keys(query)) {
    if (!allowed.has(key)) throw new RequestError(400, "UNSUPPORTED_OPTION", `query option ${key} is not supported`);
  }
  if (indexUid !== INDEX_UID) throw new RequestError(403, "UNKNOWN_INDEX", `only ${INDEX_UID} is available`);
  const q = query.q === undefined ? "" : ensureString(query.q, "q", MAX_QUERY_LENGTH).trim();
  const facets = validateFacets(query.facets);
  const facetFilters = validateFacetFilters(query.facetFilters);
  const filter = validateFilter(query.filter);
  const sortValues = ensureStringArray(query.sort, "sort", 2, 100);
  for (const value of sortValues) {
    if (!ALLOWED_SORTS.includes(value as (typeof ALLOWED_SORTS)[number])) {
      throw new RequestError(400, "UNSUPPORTED_SORT", `sort ${value} is not supported`);
    }
  }
  const retrieveRaw = query.attributesToRetrieve;
  let attributesToRetrieve: PublicField[] | "*" = "*";
  if (retrieveRaw !== undefined) {
    if (retrieveRaw === "*") attributesToRetrieve = "*";
    else {
      const retrieve = ensureStringArray(retrieveRaw, "attributesToRetrieve", PUBLIC_FIELDS.length, 100);
      attributesToRetrieve = retrieve.map((field) => validatePublicField(field, "attributesToRetrieve"));
    }
  }
  const attributesToHighlight = query.attributesToHighlight === undefined
    ? ["body", "title", "handle"]
    : ensureStringArray(query.attributesToHighlight, "attributesToHighlight", 8, 100);
  for (const field of attributesToHighlight) {
    if (!SEARCHABLE_FIELDS.includes(field as (typeof SEARCHABLE_FIELDS)[number])) {
      throw new RequestError(400, "UNSUPPORTED_FIELD", `attributesToHighlight does not support field ${field}`);
    }
  }
  const attributesToCrop = ensureStringArray(query.attributesToCrop, "attributesToCrop", 8, 100);
  for (const value of attributesToCrop) {
    const [field, length] = value.split(":", 2);
    if (field !== "body" || !/^\d+$/.test(length ?? "") || Number(length) < 1 || Number(length) > 100) {
      throw new RequestError(400, "UNSUPPORTED_CROP", `attributesToCrop value ${value} is not supported`);
    }
  }
  return {
    indexUid,
    q,
    limit: ensureInteger(query.limit, "limit", 0, MAX_LIMIT, DEFAULT_LIMIT),
    offset: ensureInteger(query.offset, "offset", 0, MAX_OFFSET, 0),
    facets,
    facetFilters,
    filter,
    sort: sortValues[0] ?? "",
    attributesToRetrieve,
    attributesToHighlight,
    attributesToCrop,
    cropMarker: query.cropMarker === undefined ? "..." : ensureString(query.cropMarker, "cropMarker", 20),
    highlightPreTag: validateTags(query.highlightPreTag, "highlightPreTag", "<mark>"),
    highlightPostTag: validateTags(query.highlightPostTag, "highlightPostTag", "</mark>"),
  };
}

function validateOutreachPublicField(field: string, option: string): OutreachPublicField {
  if (!OUTREACH_PUBLIC_FIELDS.includes(field as OutreachPublicField)) {
    throw new RequestError(400, "UNSUPPORTED_FIELD", `${option} does not support field ${field}`);
  }
  return field as OutreachPublicField;
}

function validateOutreachFacets(value: unknown): OutreachFacetField[] {
  if (value === undefined) return [];
  if (value === "*") return [...OUTREACH_FACET_FIELDS];
  if (!Array.isArray(value) || value.length > OUTREACH_FACET_FIELDS.length) {
    throw new RequestError(400, "INVALID_FIELD", "facets must be an array of supported Outreach fields");
  }
  if (value.includes("*")) {
    if (value.length !== 1) throw new RequestError(400, "UNSUPPORTED_FACET", "facets wildcard cannot be combined with named facets");
    return [...OUTREACH_FACET_FIELDS];
  }
  return value.map((item, index) => {
    if (typeof item !== "string" || !OUTREACH_FACET_FIELDS.includes(item as OutreachFacetField)) {
      throw new RequestError(400, "UNSUPPORTED_FACET", `facets[${index}] is not supported for Outreach`);
    }
    return item as OutreachFacetField;
  });
}

function parseOutreachQuery(query: Record<string, unknown>): OutreachSearchQuery {
  const allowed = new Set([
    "indexUid",
    "q",
    "limit",
    "offset",
    "facets",
    "facetFilters",
    "filter",
    "sort",
    "attributesToRetrieve",
    "attributesToHighlight",
    "attributesToCrop",
    "cropMarker",
    "highlightPreTag",
    "highlightPostTag",
  ]);
  for (const key of Object.keys(query)) {
    if (!allowed.has(key)) throw new RequestError(400, "UNSUPPORTED_OPTION", `query option ${key} is not supported`);
  }
  const q = query.q === undefined ? "" : ensureString(query.q, "q", MAX_QUERY_LENGTH).trim();
  const facets = validateOutreachFacets(query.facets);
  const facetFilters = validateFacetFilters(query.facetFilters);
  const filter = validateFilter(query.filter);
  const sortValues = ensureStringArray(query.sort, "sort", 2, 100);
  for (const value of sortValues) {
    if (!OUTREACH_ALLOWED_SORTS.includes(value as (typeof OUTREACH_ALLOWED_SORTS)[number])) {
      throw new RequestError(400, "UNSUPPORTED_SORT", `sort ${value} is not supported for Outreach`);
    }
  }
  const retrieveRaw = query.attributesToRetrieve;
  let attributesToRetrieve: OutreachPublicField[] | "*" = "*";
  if (retrieveRaw !== undefined) {
    if (retrieveRaw === "*") attributesToRetrieve = "*";
    else {
      const retrieve = ensureStringArray(retrieveRaw, "attributesToRetrieve", OUTREACH_PUBLIC_FIELDS.length, 100);
      attributesToRetrieve = retrieve.map((field) => validateOutreachPublicField(field, "attributesToRetrieve"));
    }
  }
  const attributesToHighlight = query.attributesToHighlight === undefined
    ? ["title", "summary", "evidence_summary"]
    : ensureStringArray(query.attributesToHighlight, "attributesToHighlight", 12, 100);
  for (const field of attributesToHighlight) {
    if (!OUTREACH_SEARCHABLE_FIELDS.includes(field as (typeof OUTREACH_SEARCHABLE_FIELDS)[number])) {
      throw new RequestError(400, "UNSUPPORTED_FIELD", `attributesToHighlight does not support Outreach field ${field}`);
    }
  }
  const attributesToCrop = ensureStringArray(query.attributesToCrop, "attributesToCrop", 8, 100);
  for (const value of attributesToCrop) {
    const [field, length] = value.split(":", 2);
    if (
      !["title", "summary", "tactic", "evidence_summary"].includes(field) ||
      !/^\d+$/.test(length ?? "") ||
      Number(length) < 1 ||
      Number(length) > 100
    ) {
      throw new RequestError(400, "UNSUPPORTED_CROP", `attributesToCrop value ${value} is not supported for Outreach`);
    }
  }
  return {
    indexUid: OUTREACH_INDEX_UID,
    q,
    limit: ensureInteger(query.limit, "limit", 0, MAX_LIMIT, DEFAULT_LIMIT),
    offset: ensureInteger(query.offset, "offset", 0, MAX_OFFSET, 0),
    facets,
    facetFilters,
    filter,
    sort: sortValues[0] ?? "",
    attributesToRetrieve,
    attributesToHighlight,
    attributesToCrop,
    cropMarker: query.cropMarker === undefined ? "..." : ensureString(query.cropMarker, "cropMarker", 20),
    highlightPreTag: validateTags(query.highlightPreTag, "highlightPreTag", "<mark>"),
    highlightPostTag: validateTags(query.highlightPostTag, "highlightPostTag", "</mark>"),
  };
}

function parseQuery(raw: unknown): SearchQuery | OutreachSearchQuery {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new RequestError(400, "INVALID_QUERY", "each query must be a JSON object");
  }
  const query = raw as Record<string, unknown>;
  const rawIndexUid = query.indexUid === undefined ? INDEX_UID : ensureString(query.indexUid, "indexUid", 100);
  const indexKind = Object.prototype.hasOwnProperty.call(SEARCH_INDEXES, rawIndexUid)
    ? SEARCH_INDEXES[rawIndexUid as keyof typeof SEARCH_INDEXES]
    : undefined;
  if (!indexKind) {
    throw new RequestError(403, "UNKNOWN_INDEX", `index ${rawIndexUid} is not available`);
  }
  if (indexKind === "outreach") return parseOutreachQuery(query);
  return parseTikTokQuery(query, INDEX_UID);
}

function normalizeFilterLiteral(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) throw new RequestError(400, "INVALID_FILTER", "filter value cannot be empty");
  if ((trimmed.startsWith("'") && trimmed.endsWith("'")) || (trimmed.startsWith('"') && trimmed.endsWith('"'))) {
    return trimmed.slice(1, -1);
  }
  if (!/^[\p{L}\p{N}_@.:/+%-]+$/u.test(trimmed)) {
    throw new RequestError(400, "INVALID_FILTER", `unsupported filter value ${trimmed}`);
  }
  return trimmed;
}

function splitTopLevel(input: string, operator: "AND" | "OR"): string[] {
  const pieces: string[] = [];
  let start = 0;
  let quote = "";
  let bracketDepth = 0;
  let parenthesisDepth = 0;
  const upper = input.toUpperCase();
  for (let index = 0; index < input.length; index += 1) {
    const character = input[index];
    if (quote) {
      if (character === quote && input[index - 1] !== "\\") quote = "";
      continue;
    }
    if (character === "'" || character === '"') {
      quote = character;
      continue;
    }
    if (character === "[") bracketDepth += 1;
    else if (character === "]") bracketDepth -= 1;
    else if (character === "(") parenthesisDepth += 1;
    else if (character === ")") parenthesisDepth -= 1;
    if (bracketDepth !== 0 || parenthesisDepth !== 0) continue;
    if (upper.slice(index, index + operator.length) !== operator) continue;
    const before = input[index - 1] ?? " ";
    const after = input[index + operator.length] ?? " ";
    if (!/\s/.test(before) || !/\s/.test(after)) continue;
    pieces.push(input.slice(start, index).trim());
    start = index + operator.length;
    index += operator.length - 1;
  }
  if (!pieces.length) return [input.trim()];
  pieces.push(input.slice(start).trim());
  if (pieces.some((piece) => !piece)) throw new RequestError(400, "INVALID_FILTER", "filter contains an empty expression");
  return pieces;
}

function stripOuterParentheses(value: string): string {
  let result = value.trim();
  while (result.startsWith("(") && result.endsWith(")")) {
    let depth = 0;
    let balancedAtEnd = true;
    let quote = "";
    for (let index = 0; index < result.length; index += 1) {
      const character = result[index];
      if (quote) {
        if (character === quote && result[index - 1] !== "\\") quote = "";
      } else if (character === "'" || character === '"') quote = character;
      else if (character === "(") depth += 1;
      else if (character === ")") {
        depth -= 1;
        if (depth === 0 && index !== result.length - 1) {
          balancedAtEnd = false;
          break;
        }
      }
    }
    if (!balancedAtEnd || depth !== 0) break;
    result = result.slice(1, -1).trim();
  }
  return result;
}

function fieldCondition(field: string, operator: "=" | "!=", value: string): SqlCondition {
  if (!FACET_FIELDS.includes(field as FacetField)) throw new RequestError(400, "UNSUPPORTED_FILTER", `filter field ${field} is not supported`);
  if (field === "topics") {
    return {
      sql: `${operator === "=" ? "EXISTS" : "NOT EXISTS"} (SELECT 1 FROM search_topics AS st WHERE st.document_id=d.id AND st.topic_id=?)`,
      params: [value],
    };
  }
  return { sql: `d.${FACET_COLUMNS[field as keyof typeof FACET_COLUMNS]}${operator === "=" ? "=" : "<>"}?`, params: [value] };
}

function parseFilterAtom(value: string): SqlCondition {
  const expression = stripOuterParentheses(value);
  const match = expression.match(/^(?:"([A-Za-z_][A-Za-z0-9_]*)"|([A-Za-z_][A-Za-z0-9_]*))\s*(NOT\s+IN|IN|!=|=)\s*(.+)$/i);
  if (!match) throw new RequestError(400, "INVALID_FILTER", `unsupported filter expression ${expression}`);
  const [, quotedField, bareField, rawOperator, rawValue] = match;
  const field = quotedField ?? bareField;
  const operator = rawOperator.toUpperCase().replace(/\s+/g, " ");
  if (operator === "=" || operator === "!=") return fieldCondition(field, operator, normalizeFilterLiteral(rawValue));
  const listText = rawValue.trim();
  if (!listText.startsWith("[") || !listText.endsWith("]")) {
    throw new RequestError(400, "INVALID_FILTER", "IN filters must use a bracketed list");
  }
  const list = listText.slice(1, -1).split(",").map((item) => normalizeFilterLiteral(item));
  if (!list.length || list.length > 32) throw new RequestError(400, "INVALID_FILTER", "IN filters must contain 1-32 values");
  if (!FACET_FIELDS.includes(field as FacetField)) throw new RequestError(400, "UNSUPPORTED_FILTER", `filter field ${field} is not supported`);
  const positive = operator === "IN";
  if (field === "topics") {
    return {
      sql: `${positive ? "EXISTS" : "NOT EXISTS"} (SELECT 1 FROM search_topics AS st WHERE st.document_id=d.id AND st.topic_id IN (${list.map(() => "?").join(", ")}))`,
      params: list,
    };
  }
  return {
    sql: `d.${FACET_COLUMNS[field as keyof typeof FACET_COLUMNS]} ${positive ? "IN" : "NOT IN"} (${list.map(() => "?").join(", ")})`,
    params: list,
  };
}

function combineConditions(conditions: SqlCondition[], joiner: "AND" | "OR"): SqlCondition {
  if (conditions.length === 1) return conditions[0];
  return {
    sql: `(${conditions.map((condition) => condition.sql).join(` ${joiner} `)})`,
    params: conditions.flatMap((condition) => condition.params),
  };
}

function parseFilterExpression(value: string): SqlCondition {
  const expression = stripOuterParentheses(value);
  const orParts = splitTopLevel(expression, "OR");
  if (orParts.length > 1) return combineConditions(orParts.map(parseFilterExpression), "OR");
  const andParts = splitTopLevel(expression, "AND");
  if (andParts.length > 1) return combineConditions(andParts.map(parseFilterExpression), "AND");
  return parseFilterAtom(expression);
}

function buildConditions(query: SearchQuery): SqlCondition[] {
  const conditions: SqlCondition[] = [];
  for (const group of query.facetFilters) {
    const groupConditions = group.map((facetFilter) => {
      const separator = facetFilter.indexOf(":");
      if (separator <= 0) throw new RequestError(400, "INVALID_FACET_FILTER", `facet filter ${facetFilter} must use field:value`);
      const field = facetFilter.slice(0, separator).trim();
      const value = normalizeFilterLiteral(facetFilter.slice(separator + 1));
      return fieldCondition(field, "=", value);
    });
    conditions.push(combineConditions(groupConditions, "OR"));
  }
  for (const filter of query.filter) {
    if (Array.isArray(filter)) conditions.push(combineConditions(filter.map(parseFilterExpression), "OR"));
    else conditions.push(parseFilterExpression(filter));
  }
  return conditions;
}

function buildFtsQuery(query: string): string | null {
  const tokens = query.normalize("NFKC").match(/[\p{L}\p{N}_@-]+/gu) ?? [];
  const uniqueTokens = [...new Set(tokens.map((token) => token.trim()).filter(Boolean))].slice(0, 20);
  if (!uniqueTokens.length) return null;
  return uniqueTokens.map((token) => `"${token.replaceAll('"', '""')}"*`).join(" AND ");
}

function buildScope(query: SearchQuery, conditions: SqlCondition[]): { from: string; where: string; params: string[] } {
  const ftsQuery = buildFtsQuery(query.q);
  const from = ftsQuery
    ? "FROM search_documents_fts JOIN search_documents AS d ON d.rowid=search_documents_fts.rowid"
    : "FROM search_documents AS d";
  const predicates: string[] = [];
  const params: string[] = [];
  if (query.q && !ftsQuery) predicates.push("0");
  if (ftsQuery) {
    predicates.push("search_documents_fts MATCH ?");
    params.push(ftsQuery);
  }
  predicates.push(...conditions.map((condition) => condition.sql));
  params.push(...conditions.flatMap((condition) => condition.params));
  return { from, where: predicates.length ? `WHERE ${predicates.join(" AND ")}` : "", params };
}

function parseJsonList(value: unknown): string[] {
  if (typeof value !== "string") return [];
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function normalizeAvatarUrl(value: string): string {
  if (value.startsWith("/knowledge/static/")) return value.slice("/knowledge".length);
  return value;
}

function rowValue(row: SearchRow, field: PublicField): unknown {
  if (field === "topics") return parseJsonList(row.topics_json);
  if (field === "topic_labels") return parseJsonList(row.topic_labels_json);
  if (field === "full_transcript_public") return Boolean(row.full_transcript_public);
  if (field === "avatar_url") return normalizeAvatarUrl(String(row.avatar_url ?? ""));
  return row[field];
}

function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function truncateText(value: string, length: number): string {
  const compact = value.replace(/\s+/gu, " ").trim();
  return compact.length <= length ? compact : `${compact.slice(0, Math.max(0, length - 1)).trimEnd()}…`;
}

function safePublicSourceUrl(value: string): string {
  try {
    const parsed = new URL(value);
    if (parsed.protocol === "https:" && (parsed.hostname === "www.tiktok.com" || parsed.hostname === "tiktok.com")) {
      return parsed.toString();
    }
  } catch {
    // Fail closed below. Public D1 projection validation should make this
    // unreachable, but rendering never trusts persisted strings blindly.
  }
  return "";
}

function secondsLabel(value: number): string {
  const seconds = Math.max(0, Math.floor(Number(value) || 0));
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
}

async function readProjectedSourceRows(db: D1Database, videoId: string): Promise<ProjectedSourcePageRow[]> {
  const result = await db.prepare(
    `SELECT d.video_id, d.source_id, d.creator_handle, d.creator_url,
            d.source_url, d.published_date, c.ordinal, c.claim_text,
            c.suggested_action, c.topic_label, c.evidence_excerpt,
            c.evidence_start_seconds, c.evidence_end_seconds
       FROM public_projection_receipts AS r
       JOIN public_projection_cards AS c ON c.projection_id=r.projection_id
       JOIN search_documents AS d ON d.id=c.search_id
      WHERE r.status='applied'
        AND d.video_id=?
        AND d.projection_id=r.projection_id
        AND d.source_id=r.source_id
        AND d.full_transcript_public=0
      ORDER BY c.ordinal ASC
      LIMIT 3`,
  ).bind(videoId).all<ProjectedSourcePageRow>();
  return result.results;
}

function renderProjectedSourcePage(videoId: string, rows: ProjectedSourcePageRow[]): string {
  const first = rows[0];
  const canonical = `${PUBLIC_ORIGIN}/sources/tiktok-video-${videoId}`;
  const sourceUrl = safePublicSourceUrl(first.source_url);
  const creator = first.creator_handle || "Original creator";
  const title = truncateText(first.claim_text || `Public source ${videoId}`, 120);
  const description = truncateText(first.evidence_excerpt || first.claim_text, 160);
  const topics = Array.from(new Set(rows.map((row) => row.topic_label).filter(Boolean)));
  const jsonLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${canonical}#webpage`,
    url: canonical,
    name: title,
    description,
    ...(first.published_date ? { datePublished: first.published_date } : {}),
    ...(sourceUrl ? { citation: sourceUrl, isBasedOn: sourceUrl } : {}),
    about: topics,
    publisher: { "@type": "Organization", name: "Base2026", url: `${PUBLIC_ORIGIN}/` },
  }).replaceAll("<", "\\u003c");
  const cards = rows.map((row) => {
    const evidenceTime = `${secondsLabel(row.evidence_start_seconds)}–${secondsLabel(row.evidence_end_seconds)}`;
    return `<article class="card"><p class="topic">${escapeHtml(row.topic_label)}</p><h2>${escapeHtml(row.claim_text)}</h2><blockquote>${escapeHtml(row.evidence_excerpt)}</blockquote><p class="time">Source excerpt ${escapeHtml(evidenceTime)}</p><h3>Suggested action</h3><p>${escapeHtml(row.suggested_action)}</p></article>`;
  }).join("");
  const topicQuery = encodeURIComponent(topics[0] || title);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(title)} | Base2026</title><meta name="description" content="${escapeHtml(description)}">
<meta name="robots" content="index,follow"><link rel="canonical" href="${canonical}">
<meta property="og:type" content="article"><meta property="og:title" content="${escapeHtml(title)}"><meta property="og:description" content="${escapeHtml(description)}"><meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SOCIAL_IMAGE_URL}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Base2026 public-source intelligence">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${escapeHtml(title)}"><meta name="twitter:description" content="${escapeHtml(description)}"><meta name="twitter:image" content="${SOCIAL_IMAGE_URL}"><meta name="twitter:image:alt" content="Base2026 public-source intelligence">
<script type="application/ld+json">${jsonLd}</script>
<link rel="stylesheet" href="/static/base2026-core.css?v=20260820-b26v1">
<style>:root{color-scheme:light;--ink:#101827;--muted:#5d6878;--line:#d8dfeb;--paper:#f7f9fc;--accent:#315eea}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit}.shell{max-width:1040px;margin:auto;padding:24px}.nav{display:flex;gap:18px;align-items:center;padding:8px 0 38px}.brand{font-weight:900;text-decoration:none}.nav a:not(.brand){color:var(--muted)}.hero{max-width:860px;padding:42px 0}.eyebrow,.topic,.time{font-size:13px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}h1{font-size:clamp(38px,7vw,72px);line-height:1.03;letter-spacing:-.04em;margin:.2em 0}.lede{font-size:19px;color:var(--muted)}.cards{display:grid;gap:18px}.card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:clamp(24px,5vw,44px)}.card h2{font-size:clamp(24px,4vw,36px);line-height:1.15}.card h3{margin-top:28px}blockquote{margin:24px 0;padding-left:18px;border-left:4px solid var(--accent);font-size:18px}.source{margin:34px 0;padding:28px;border:1px solid var(--line);border-radius:18px}.actions{display:flex;flex-wrap:wrap;gap:12px;margin:28px 0 60px}.actions a{padding:11px 18px;border:1px solid var(--ink);border-radius:999px;text-decoration:none;font-weight:800}.actions a:first-child{background:var(--ink);color:#fff}@media(max-width:620px){.nav{flex-wrap:wrap}.shell{padding:18px}}</style></head>
<body><main class="shell"><nav class="nav" aria-label="Primary"><a class="brand" href="/">Base2026</a><a href="/workspace/">Search</a><a href="/topics/">Topics</a><a href="/methodology">Methodology</a></nav>
<header class="hero"><p class="eyebrow">Public source record · ${escapeHtml(creator)}</p><h1>${escapeHtml(title)}</h1><p class="lede">Source-backed excerpt cards generated by the Base2026 public evidence pipeline. The original creator remains the canonical source.</p></header>
<section class="cards" aria-label="Public evidence cards">${cards}</section>
<section class="source"><h2>Source and attribution</h2><p>Creator: <strong>${escapeHtml(creator)}</strong>${first.published_date ? ` · Published ${escapeHtml(first.published_date)}` : ""}</p>${sourceUrl ? `<p><a href="${escapeHtml(sourceUrl)}" rel="nofollow noopener noreferrer">Open the original TikTok video</a></p>` : ""}<p>Base2026 publishes short evidence excerpts, not raw media or a full private transcript. See the <a href="/methodology">methodology</a> and <a href="/opt-out">correction policy</a>.</p></section>
<div class="actions"><a href="/workspace/?q=${topicQuery}">Find related evidence</a><a href="/sources/">Browse sources</a></div></main></body></html>`;
}

async function handleProjectedSourcePage(request: Request, env: EnvWithBindings, videoId: string): Promise<Response | null> {
  if (request.method !== "GET" && request.method !== "HEAD") throw methodError(request.method);
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 search database is unavailable");
  const rows = await readProjectedSourceRows(env.DB, videoId);
  if (!rows.length) return null;
  const body = renderProjectedSourcePage(videoId, rows);
  return new Response(request.method === "HEAD" ? null : body, {
    status: 200,
    headers: withPublicResponseHeaders({
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=300, s-maxage=900",
    }),
  });
}

async function handleDynamicSitemap(request: Request, env: EnvWithBindings): Promise<Response> {
  if (request.method !== "GET" && request.method !== "HEAD") throw methodError(request.method);
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 search database is unavailable");
  const result = await env.DB.prepare(
    `SELECT d.video_id AS video_id, MAX(r.updated_at) AS lastmod
       FROM public_projection_receipts AS r
       JOIN search_documents AS d ON d.projection_id=r.projection_id AND d.source_id=r.source_id
      WHERE r.status='applied' AND d.video_id<>'' AND d.full_transcript_public=0
      GROUP BY d.video_id
      ORDER BY d.video_id ASC
      LIMIT ?`,
  ).bind(MAX_DYNAMIC_SITEMAP_URLS).all<DynamicSitemapRow>();
  const urls = result.results.map((row) => {
    const videoId = /^\d{10,30}$/u.test(row.video_id) ? row.video_id : "";
    if (!videoId) return "";
    const lastmod = /^\d{4}-\d{2}-\d{2}/u.test(row.lastmod || "") ? `<lastmod>${escapeHtml(row.lastmod.slice(0, 10))}</lastmod>` : "";
    return `<url><loc>${PUBLIC_ORIGIN}/sources/tiktok-video-${videoId}</loc>${lastmod}</url>`;
  }).filter(Boolean).join("");
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>\n`;
  return new Response(request.method === "HEAD" ? null : body, {
    status: 200,
    headers: withPublicResponseHeaders({
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=300, s-maxage=900",
      "X-Robots-Tag": "noindex",
    }),
  });
}

function cropText(value: string, query: SearchQuery): string {
  const crop = query.attributesToCrop.find((item) => item.startsWith("body:"));
  if (!crop) return value;
  const length = Number(crop.slice("body:".length));
  const words = value.trim().split(/\s+/u);
  return words.length > length ? `${words.slice(0, length).join(" ")}${query.cropMarker}` : value;
}

function formatHighlighted(value: string, query: SearchQuery, field: string): string {
  const escaped = escapeHtml(field === "body" ? cropText(value, query) : value);
  if (!query.q || !query.attributesToHighlight.includes(field)) return escaped;
  const tokens = query.q.normalize("NFKC").match(/[\p{L}\p{N}_@-]+/gu) ?? [];
  return tokens
    .filter((token) => token.length > 0)
    .sort((left, right) => right.length - left.length)
    .reduce((result, token) => {
      const safeToken = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return result.replace(new RegExp(`(${safeToken})`, "giu"), `${query.highlightPreTag}$1${query.highlightPostTag}`);
    }, escaped);
}

function rowToHit(row: SearchRow, query: SearchQuery): Record<string, unknown> {
  const fields = query.attributesToRetrieve === "*" ? PUBLIC_FIELDS : query.attributesToRetrieve;
  const hit: Record<string, unknown> = {};
  for (const field of fields) hit[field] = rowValue(row, field);
  if (!Object.prototype.hasOwnProperty.call(hit, "id")) hit.id = row.id;
  const highlightFields = query.attributesToHighlight.filter((field) => fields.includes(field as PublicField));
  const formatted: Record<string, string> = {};
  for (const field of highlightFields) {
    const value = hit[field];
    if (typeof value === "string") formatted[field] = formatHighlighted(value, query, field);
  }
  hit._formatted = formatted;
  return hit;
}

function numericCount(value: unknown): number {
  const result = typeof value === "number" ? value : Number(value);
  return Number.isFinite(result) ? result : 0;
}

async function facetDistribution(env: EnvWithBindings, query: SearchQuery, scope: ReturnType<typeof buildScope>): Promise<Record<string, Record<string, number>>> {
  const distribution: Record<string, Record<string, number>> = {};
  for (const facet of query.facets) {
    const statement = facet === "topics"
      ? `SELECT st.topic_id AS value, COUNT(DISTINCT d.id) AS count FROM search_topics AS st JOIN search_documents AS d ON d.id=st.document_id ${scope.from.includes("search_documents_fts") ? "JOIN search_documents_fts ON d.rowid=search_documents_fts.rowid" : ""} ${scope.where} GROUP BY st.topic_id ORDER BY count DESC, value ASC LIMIT ${MAX_FACET_VALUES}`
      : `SELECT d.${FACET_COLUMNS[facet as keyof typeof FACET_COLUMNS]} AS value, COUNT(*) AS count ${scope.from} ${scope.where} GROUP BY d.${FACET_COLUMNS[facet as keyof typeof FACET_COLUMNS]} ORDER BY count DESC, value ASC LIMIT ${MAX_FACET_VALUES}`;
    const result = await env.DB.prepare(statement).bind(...scope.params).all<{ value: string | null; count: number }>();
    const values: Record<string, number> = {};
    for (const row of result.results) {
      if (row.value !== null && row.value !== "") values[String(row.value)] = numericCount(row.count);
    }
    distribution[facet] = values;
  }
  return distribution;
}

async function executeSearch(env: EnvWithBindings, query: SearchQuery): Promise<Record<string, unknown>> {
  const started = performance.now();
  const conditions = buildConditions(query);
  const scope = buildScope(query, conditions);
  const count = await env.DB.prepare(`SELECT COUNT(*) AS count ${scope.from} ${scope.where}`).bind(...scope.params).first<{ count: number }>();
  const order = query.sort
    ? `ORDER BY d.${query.sort.split(":", 1)[0]} ${query.sort.endsWith(":asc") ? "ASC" : "DESC"}, d.id ASC`
    : scope.from.includes("search_documents_fts")
      ? "ORDER BY bm25(search_documents_fts) ASC, d.published_date DESC, d.id ASC"
      : "ORDER BY d.published_date DESC, d.id ASC";
  const rows = await env.DB
    .prepare(`SELECT d.* ${scope.from} ${scope.where} ${order} LIMIT ? OFFSET ?`)
    .bind(...scope.params, query.limit, query.offset)
    .all<SearchRow>();
  const response: Record<string, unknown> = {
    indexUid: INDEX_UID,
    hits: rows.results.map((row) => rowToHit(row, query)),
    query: query.q,
    processingTimeMs: Math.max(0, Math.round(performance.now() - started)),
    limit: query.limit,
    offset: query.offset,
    estimatedTotalHits: numericCount(count?.count),
    facetDistribution: {},
    facetStats: {},
  };
  if (query.facets.length) response.facetDistribution = await facetDistribution(env, query, scope);
  return response;
}

type OutreachFilterOperator = "=" | "!=" | "IN" | "NOT IN" | ">" | ">=" | "<" | "<=";

const OUTREACH_SQL_COLUMNS = Object.freeze([
  "id",
  "collection",
  "record_type",
  "source_record_id",
  "title",
  "summary",
  "tactic",
  "evidence_summary",
  "verdict",
  "source_url",
  "platform",
  "author_name",
  "author_handle",
  "observed_at",
  "score",
  "source_status",
  "topics_json",
  "lanes_json",
  "cost",
  "complexity",
  "effect_speed",
  "public_policy",
  "reviewed_at",
  "source_hash",
  "dedup_key",
  "language",
] as const);

function isOutreachFilterField(field: string): field is OutreachFilterField {
  return OUTREACH_FACET_FIELDS.includes(field as OutreachFacetField) || field === "score" || field === "observed_at";
}

function normalizeOutreachNumber(value: string): number {
  const trimmed = value.trim();
  const unquoted = (trimmed.startsWith("'") && trimmed.endsWith("'")) || (trimmed.startsWith('"') && trimmed.endsWith('"'))
    ? trimmed.slice(1, -1)
    : trimmed;
  if (!/^-?(?:\d+(?:\.\d+)?|\.\d+)$/u.test(unquoted)) {
    throw new RequestError(400, "INVALID_FILTER", `score filter value ${value} must be numeric`);
  }
  const parsed = Number(unquoted);
  if (!Number.isFinite(parsed)) throw new RequestError(400, "INVALID_FILTER", `score filter value ${value} must be finite`);
  return parsed;
}

function outreachListValues(value: string): string[] {
  const listText = value.trim();
  if (!listText.startsWith("[") || !listText.endsWith("]")) {
    throw new RequestError(400, "INVALID_FILTER", "IN filters must use a bracketed list");
  }
  const values = listText.slice(1, -1).split(",").map((item) => item.trim());
  if (!values.length || values.length > 32 || values.some((item) => !item)) {
    throw new RequestError(400, "INVALID_FILTER", "IN filters must contain 1-32 values");
  }
  return values;
}

function outreachFieldCondition(field: string, operator: OutreachFilterOperator, value: string | string[]): SqlCondition {
  if (!isOutreachFilterField(field)) {
    throw new RequestError(400, "UNSUPPORTED_FILTER", `filter field ${field} is not supported for Outreach`);
  }
  const values = Array.isArray(value) ? value : [value];
  if (operator === "IN" || operator === "NOT IN") {
    const positive = operator === "IN";
    const normalizedValues = field === "score" ? values.map(normalizeOutreachNumber).map(String) : values.map(normalizeFilterLiteral);
    if (field === "topics" || field === "lanes") {
      const table = field === "topics" ? "outreach_topics" : "outreach_lanes";
      const column = field === "topics" ? "topic" : "lane";
      return {
        sql: `${positive ? "EXISTS" : "NOT EXISTS"} (SELECT 1 FROM ${table} AS ol WHERE ol.finding_id=d.id AND ol.${column} IN (${normalizedValues.map(() => "?").join(", ")}))`,
        params: normalizedValues,
      };
    }
    const column = field === "score" || field === "observed_at" ? field : OUTREACH_FACET_COLUMNS[field as keyof typeof OUTREACH_FACET_COLUMNS];
    return {
      sql: `d.${column} ${positive ? "IN" : "NOT IN"} (${normalizedValues.map(() => "?").join(", ")})`,
      params: normalizedValues,
    };
  }
  if (values.length !== 1) throw new RequestError(400, "INVALID_FILTER", "scalar filters accept one value");
  if (field === "topics" || field === "lanes") {
    if (operator !== "=" && operator !== "!=") {
      throw new RequestError(400, "UNSUPPORTED_FILTER", `${field} supports only equality filters`);
    }
    const table = field === "topics" ? "outreach_topics" : "outreach_lanes";
    const column = field === "topics" ? "topic" : "lane";
    return {
      sql: `${operator === "=" ? "EXISTS" : "NOT EXISTS"} (SELECT 1 FROM ${table} AS ol WHERE ol.finding_id=d.id AND ol.${column}=?)`,
      params: [normalizeFilterLiteral(values[0])],
    };
  }
  if (field !== "score" && operator !== "=" && operator !== "!=" && field !== "observed_at") {
    throw new RequestError(400, "UNSUPPORTED_FILTER", `${field} supports only equality filters`);
  }
  const parameter = field === "score" ? normalizeOutreachNumber(values[0]) : normalizeFilterLiteral(values[0]);
  const column = field === "score" || field === "observed_at" ? field : OUTREACH_FACET_COLUMNS[field as keyof typeof OUTREACH_FACET_COLUMNS];
  const sqlOperator = operator === "!=" ? "<>" : operator;
  return { sql: `d.${column}${sqlOperator}?`, params: [String(parameter)] };
}

function parseOutreachFilterAtom(value: string): SqlCondition {
  const expression = stripOuterParentheses(value);
  const match = expression.match(/^(?:"([A-Za-z_][A-Za-z0-9_]*)"|([A-Za-z_][A-Za-z0-9_]*))\s*(NOT\s+IN|>=|<=|!=|=|>|<|IN)\s*(.+)$/i);
  if (!match) throw new RequestError(400, "INVALID_FILTER", `unsupported Outreach filter expression ${expression}`);
  const [, quotedField, bareField, rawOperator, rawValue] = match;
  const field = quotedField ?? bareField;
  const operator = rawOperator.toUpperCase().replace(/\s+/g, " ") as OutreachFilterOperator;
  if (operator === "IN" || operator === "NOT IN") return outreachFieldCondition(field, operator, outreachListValues(rawValue));
  return outreachFieldCondition(field, operator, rawValue);
}

function parseOutreachFilterExpression(value: string): SqlCondition {
  const expression = stripOuterParentheses(value);
  const orParts = splitTopLevel(expression, "OR");
  if (orParts.length > 1) return combineConditions(orParts.map(parseOutreachFilterExpression), "OR");
  const andParts = splitTopLevel(expression, "AND");
  if (andParts.length > 1) return combineConditions(andParts.map(parseOutreachFilterExpression), "AND");
  return parseOutreachFilterAtom(expression);
}

function outreachFacetEqualityCondition(field: string, value: string): SqlCondition {
  if (!OUTREACH_FACET_FIELDS.includes(field as OutreachFacetField)) {
    throw new RequestError(400, "UNSUPPORTED_FACET", `facet filter field ${field} is not supported for Outreach`);
  }
  const literal = value.trim();
  if (!literal || /[\u0000-\u001f\u007f]/u.test(literal)) {
    throw new RequestError(400, "INVALID_FACET_FILTER", `facet filter ${field} has an invalid value`);
  }
  if (field === "topics" || field === "lanes") {
    const table = field === "topics" ? "outreach_topics" : "outreach_lanes";
    const column = field === "topics" ? "topic" : "lane";
    return {
      sql: `EXISTS (SELECT 1 FROM ${table} AS ol WHERE ol.finding_id=d.id AND ol.${column}=?)`,
      params: [literal],
    };
  }
  const column = OUTREACH_FACET_COLUMNS[field as keyof typeof OUTREACH_FACET_COLUMNS];
  return { sql: `d.${column}=?`, params: [literal] };
}

function buildOutreachConditions(query: OutreachSearchQuery): SqlCondition[] {
  const conditions: SqlCondition[] = [];
  for (const group of query.facetFilters) {
    const groupConditions = group.map((facetFilter) => {
      const separator = facetFilter.indexOf(":");
      if (separator <= 0) throw new RequestError(400, "INVALID_FACET_FILTER", `facet filter ${facetFilter} must use field:value`);
      const field = facetFilter.slice(0, separator).trim();
      return outreachFacetEqualityCondition(field, facetFilter.slice(separator + 1));
    });
    conditions.push(combineConditions(groupConditions, "OR"));
  }
  for (const filter of query.filter) {
    if (Array.isArray(filter)) conditions.push(combineConditions(filter.map(parseOutreachFilterExpression), "OR"));
    else conditions.push(parseOutreachFilterExpression(filter));
  }
  return conditions;
}

function buildOutreachScope(query: OutreachSearchQuery, conditions: SqlCondition[]): { from: string; where: string; params: string[] } {
  const ftsQuery = buildFtsQuery(query.q);
  const from = ftsQuery
    ? "FROM outreach_findings_fts JOIN outreach_findings AS d ON d.rowid=outreach_findings_fts.rowid"
    : "FROM outreach_findings AS d";
  const predicates: string[] = [];
  const params: string[] = [];
  if (query.q && !ftsQuery) predicates.push("0");
  if (ftsQuery) {
    predicates.push("outreach_findings_fts MATCH ?");
    params.push(ftsQuery);
  }
  predicates.push(...conditions.map((condition) => condition.sql));
  params.push(...conditions.flatMap((condition) => condition.params));
  return { from, where: predicates.length ? `WHERE ${predicates.join(" AND ")}` : "", params };
}

function outreachRowValue(row: OutreachSearchRow, field: OutreachPublicField): unknown {
  if (field === "topics") return parseJsonList(row.topics_json);
  if (field === "lanes") return parseJsonList(row.lanes_json);
  if (field === "score") return numericCount(row.score);
  return row[field];
}

function cropOutreachText(value: string, query: OutreachSearchQuery, field: string): string {
  const crop = query.attributesToCrop.find((item) => item.startsWith(`${field}:`));
  if (!crop) return value;
  const length = Number(crop.slice(`${field}:`.length));
  const words = value.trim().split(/\s+/u);
  return words.length > length ? `${words.slice(0, length).join(" ")}${query.cropMarker}` : value;
}

function formatOutreachHighlighted(value: string, query: OutreachSearchQuery, field: string): string {
  const escaped = escapeHtml(cropOutreachText(value, query, field));
  if (!query.q || !query.attributesToHighlight.includes(field)) return escaped;
  const tokens = query.q.normalize("NFKC").match(/[\p{L}\p{N}_@-]+/gu) ?? [];
  return tokens
    .filter((token) => token.length > 0)
    .sort((left, right) => right.length - left.length)
    .reduce((result, token) => {
      const safeToken = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return result.replace(new RegExp(`(${safeToken})`, "giu"), `${query.highlightPreTag}$1${query.highlightPostTag}`);
    }, escaped);
}

function outreachRowToHit(row: OutreachSearchRow, query: OutreachSearchQuery): Record<string, unknown> {
  const fields = query.attributesToRetrieve === "*" ? OUTREACH_PUBLIC_FIELDS : query.attributesToRetrieve;
  const hit: Record<string, unknown> = {};
  for (const field of fields) hit[field] = outreachRowValue(row, field);
  if (!Object.prototype.hasOwnProperty.call(hit, "id")) hit.id = row.id;
  const highlightFields = query.attributesToHighlight.filter((field) => fields.includes(field as OutreachPublicField));
  const formatted: Record<string, string> = {};
  for (const field of highlightFields) {
    const value = hit[field];
    if (typeof value === "string") formatted[field] = formatOutreachHighlighted(value, query, field);
  }
  hit._formatted = formatted;
  return hit;
}

async function outreachFacetDistribution(
  env: EnvWithBindings,
  query: OutreachSearchQuery,
  scope: ReturnType<typeof buildOutreachScope>,
): Promise<Record<string, Record<string, number>>> {
  const distribution: Record<string, Record<string, number>> = {};
  const db = env.OUTREACH_DB;
  if (!db) throw new RequestError(503, "OUTREACH_DB_NOT_CONFIGURED", "D1 binding OUTREACH_DB is not configured");
  for (const facet of query.facets) {
    const statement = facet === "topics" || facet === "lanes"
      ? (() => {
        const table = facet === "topics" ? "outreach_topics" : "outreach_lanes";
        const column = facet === "topics" ? "topic" : "lane";
        return `SELECT ol.${column} AS value, COUNT(DISTINCT d.id) AS count FROM ${table} AS ol JOIN outreach_findings AS d ON d.id=ol.finding_id ${scope.from.includes("outreach_findings_fts") ? "JOIN outreach_findings_fts ON d.rowid=outreach_findings_fts.rowid" : ""} ${scope.where} GROUP BY ol.${column} ORDER BY count DESC, value ASC LIMIT ${MAX_FACET_VALUES}`;
      })()
      : `SELECT d.${OUTREACH_FACET_COLUMNS[facet as keyof typeof OUTREACH_FACET_COLUMNS]} AS value, COUNT(*) AS count ${scope.from} ${scope.where} GROUP BY d.${OUTREACH_FACET_COLUMNS[facet as keyof typeof OUTREACH_FACET_COLUMNS]} ORDER BY count DESC, value ASC LIMIT ${MAX_FACET_VALUES}`;
    const result = await db.prepare(statement).bind(...scope.params).all<{ value: string | null; count: number }>();
    const values: Record<string, number> = {};
    for (const row of result.results) {
      if (row.value !== null && row.value !== "") values[String(row.value)] = numericCount(row.count);
    }
    distribution[facet] = values;
  }
  return distribution;
}

async function executeOutreachSearch(env: EnvWithBindings, query: OutreachSearchQuery): Promise<Record<string, unknown>> {
  if (!env.OUTREACH_DB) throw new RequestError(503, "OUTREACH_DB_NOT_CONFIGURED", "D1 binding OUTREACH_DB is not configured");
  const started = performance.now();
  const conditions = buildOutreachConditions(query);
  const scope = buildOutreachScope(query, conditions);
  const db = env.OUTREACH_DB;
  const count = await db.prepare(`SELECT COUNT(*) AS count ${scope.from} ${scope.where}`).bind(...scope.params).first<{ count: number }>();
  const order = query.sort
    ? `ORDER BY d.${query.sort.split(":", 1)[0]} ${query.sort.endsWith(":asc") ? "ASC" : "DESC"}, d.id ASC`
    : scope.from.includes("outreach_findings_fts")
      ? "ORDER BY bm25(outreach_findings_fts) ASC, d.observed_at DESC, d.id ASC"
      : "ORDER BY d.observed_at DESC, d.id ASC";
  const rows = await db
    .prepare(`SELECT ${OUTREACH_SQL_COLUMNS.map((column) => `d.${column}`).join(", ")} ${scope.from} ${scope.where} ${order} LIMIT ? OFFSET ?`)
    .bind(...scope.params, query.limit, query.offset)
    .all<OutreachSearchRow>();
  const response: Record<string, unknown> = {
    indexUid: OUTREACH_INDEX_UID,
    hits: rows.results.map((row) => outreachRowToHit(row, query)),
    query: query.q,
    processingTimeMs: Math.max(0, Math.round(performance.now() - started)),
    limit: query.limit,
    offset: query.offset,
    estimatedTotalHits: numericCount(count?.count),
    facetDistribution: {},
    facetStats: {},
  };
  if (query.facets.length) response.facetDistribution = await outreachFacetDistribution(env, query, scope);
  return response;
}

async function handleSearch(request: Request, env: EnvWithBindings): Promise<Response> {
  if (request.method !== "POST") throw methodError(request.method);
  if (!contentTypeIsJson(request)) throw new RequestError(415, "UNSUPPORTED_MEDIA_TYPE", "search requests require Content-Type: application/json");
  const body = parseJsonBody(await readBoundedBody(request));
  const queries = body.queries;
  if (!Array.isArray(queries) || queries.length > MAX_MULTI_QUERIES) {
    throw new RequestError(400, "INVALID_QUERIES", `queries must contain 0-${MAX_MULTI_QUERIES} search objects`);
  }
  const parsedQueries = queries.map(parseQuery);
  const results = [];
  for (const query of parsedQueries) {
    if (query.indexUid === OUTREACH_INDEX_UID) results.push(await executeOutreachSearch(env, query));
    else results.push(await executeSearch(env, query));
  }
  return jsonResponse({ results });
}

function briefString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function briefStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string").map((item) => item.trim()).filter(Boolean);
}

function evidenceBriefSourceKey(hit: Record<string, unknown>): string {
  return briefString(hit.video_id) || briefString(hit.source_id) || briefString(hit.id);
}

async function handleEvidenceBrief(request: Request, env: EnvWithBindings, url: URL): Promise<Response> {
  if (request.method !== "GET") throw methodError(request.method);
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 search database is unavailable");
  const queryText = ensureString(url.searchParams.get("q") ?? "", "q", MAX_QUERY_LENGTH).trim();
  if (queryText.length < MIN_EVIDENCE_BRIEF_QUERY_LENGTH) {
    throw new RequestError(
      400,
      "QUERY_TOO_SHORT",
      `q must contain at least ${MIN_EVIDENCE_BRIEF_QUERY_LENGTH} characters`,
    );
  }
  const searchQuery = parseTikTokQuery({
    q: queryText,
    limit: EVIDENCE_BRIEF_CANDIDATE_LIMIT,
    attributesToRetrieve: [
      "id", "source_id", "video_id", "title", "body", "creator_handle", "creator_display_name",
      "source_url", "published_date", "topics", "topic_labels",
    ],
    attributesToHighlight: [],
    attributesToCrop: ["body:70"],
  }, INDEX_UID);
  const searchResult = await executeSearch(env, searchQuery);
  const hits = Array.isArray(searchResult.hits)
    ? searchResult.hits as Array<Record<string, unknown>>
    : [];
  const uniqueHits: Array<Record<string, unknown>> = [];
  const seenSources = new Set<string>();
  for (const hit of hits) {
    const sourceKey = evidenceBriefSourceKey(hit);
    if (!sourceKey || seenSources.has(sourceKey)) continue;
    seenSources.add(sourceKey);
    uniqueHits.push(hit);
  }
  const selectedHits = uniqueHits.slice(0, EVIDENCE_BRIEF_SOURCE_LIMIT);
  const topicCounts = new Map<string, number>();
  for (const hit of uniqueHits) {
    const labels = briefStringList(hit.topic_labels);
    const topics = labels.length ? labels : briefStringList(hit.topics);
    for (const topic of new Set(topics)) topicCounts.set(topic, (topicCounts.get(topic) ?? 0) + 1);
  }
  const topTopics = [...topicCounts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 8)
    .map(([label, sourceCount]) => ({ label, sourceCount }));
  const creators = new Set(
    selectedHits
      .map((hit) => briefString(hit.creator_handle) || briefString(hit.creator_display_name))
      .filter(Boolean),
  );
  const newestPublishedDate = selectedHits
    .map((hit) => briefString(hit.published_date))
    .filter(Boolean)
    .sort()
    .at(-1) ?? "";
  const evidence = selectedHits.map((hit) => {
    const videoId = briefString(hit.video_id);
    return {
      id: briefString(hit.id),
      sourceId: briefString(hit.source_id),
      videoId,
      title: truncateText(briefString(hit.title) || "Public expert-video evidence", 180),
      excerpt: truncateText(briefString(hit.body), 480),
      creator: briefString(hit.creator_handle) || briefString(hit.creator_display_name),
      publishedDate: briefString(hit.published_date),
      topics: briefStringList(hit.topic_labels).length ? briefStringList(hit.topic_labels) : briefStringList(hit.topics),
      sourceUrl: safePublicSourceUrl(briefString(hit.source_url)),
      sourcePageUrl: /^\d{10,30}$/u.test(videoId) ? `${PUBLIC_ORIGIN}/sources/tiktok-video-${videoId}` : "",
    };
  });
  const matchingPassages = numericCount(searchResult.estimatedTotalHits);
  const status = evidence.length >= 2 ? "ready" : evidence.length === 1 ? "limited" : "insufficient_evidence";
  return jsonResponse({
    query: queryText,
    status,
    statement: evidence.length
      ? `${matchingPassages} matching public passages found. Start with ${evidence.length} distinct attributed sources and verify each excerpt against the original.`
      : "No attributable public evidence matched this question yet.",
    coverage: {
      matchingPassages,
      selectedSources: evidence.length,
      selectedCreators: creators.size,
      newestPublishedDate,
    },
    topics: topTopics,
    evidence,
    method: {
      id: "d1-fts5-evidence-brief-v1",
      synthesis: "deterministic-retrieval",
      note: "Base2026 does not infer consensus or generate unsupported conclusions in this endpoint.",
    },
  }, 200, { "Cache-Control": "public, max-age=60, s-maxage=300" });
}

function normalizeEvidenceBriefQuestion(value: string): string {
  return value.normalize("NFKC").replace(/\s+/gu, " ").trim().toLocaleLowerCase("en-US");
}

function normalizeEvidenceBriefToken(token: string): string {
  if (token.length > 4 && token.endsWith("ies")) return `${token.slice(0, -3)}y`;
  if (token.length > 4 && ["sses", "shes", "ches", "xes", "zes"].some((ending) => token.endsWith(ending))) {
    return token.slice(0, -2);
  }
  if (token.length > 3 && token.endsWith("s") && !token.endsWith("ss")) return token.slice(0, -1);
  return token;
}

function buildEvidenceBriefFtsQuery(normalizedQuestion: string): string | null {
  const tokens = normalizedQuestion.match(/[\p{L}\p{N}_@-]+/gu) ?? [];
  const uniqueTokens = [...new Set(tokens.map(normalizeEvidenceBriefToken))].filter(Boolean).slice(0, 24);
  const meaningfulTokens = uniqueTokens.filter(
    (token) => token.length >= 2 && !EVIDENCE_BRIEF_STOP_WORDS.has(token),
  );
  const selectedTokens = (meaningfulTokens.length ? meaningfulTokens : uniqueTokens).slice(0, 12);
  if (!selectedTokens.length) return null;
  return selectedTokens.map((token) => `"${token.replaceAll('"', '""')}"*`).join(" AND ");
}

function evidenceCandidateTopics(candidate: EvidenceBriefCandidate): string[] {
  const labels = parseJsonList(candidate.topic_labels_json).map((value) => value.trim()).filter(Boolean);
  return labels.length
    ? [...new Set(labels)]
    : [...new Set(parseJsonList(candidate.topics_json).map((value) => value.trim()).filter(Boolean))];
}

function evidenceCandidateCreator(candidate: EvidenceBriefCandidate): string {
  return briefString(candidate.creator_handle) || briefString(candidate.creator_display_name);
}

function evidenceCandidateIsPublic(candidate: EvidenceBriefCandidate): boolean {
  return candidate.full_transcript_public === 0
    && candidate.admission_state === "normal_public_card"
    && /^\d{10,30}$/u.test(briefString(candidate.video_id))
    && Boolean(briefString(candidate.source_id))
    && Boolean(evidenceCandidateCreator(candidate))
    && Boolean(safePublicSourceUrl(briefString(candidate.source_url)));
}

function evidenceCandidateSeconds(value: number | null): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
}

async function handleEvidenceBriefV2(request: Request, env: EnvWithBindings, url: URL): Promise<Response> {
  if (request.method !== "GET" && request.method !== "HEAD") throw methodError(request.method, "GET, HEAD");
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 search database is unavailable");

  const queryText = ensureString(url.searchParams.get("q") ?? "", "q", MAX_QUERY_LENGTH).trim();
  if (queryText.length < MIN_EVIDENCE_BRIEF_QUERY_LENGTH) {
    throw new RequestError(
      400,
      "QUERY_TOO_SHORT",
      `q must contain at least ${MIN_EVIDENCE_BRIEF_QUERY_LENGTH} characters`,
    );
  }
  const normalizedQuestion = normalizeEvidenceBriefQuestion(queryText);
  const ftsQuery = buildEvidenceBriefFtsQuery(normalizedQuestion);
  if (!ftsQuery) throw new RequestError(400, "INVALID_QUERY", "q must contain searchable letters or numbers");
  const cacheHeaders = {
    "Cache-Control": "public, max-age=60, s-maxage=300",
  };
  if (request.method === "HEAD") {
    return new Response(null, { status: 200, headers: withPublicResponseHeaders(JSON_HEADERS, cacheHeaders) });
  }

  const eligibilitySql = `d.full_transcript_public=0
    AND d.admission_state='normal_public_card'
    AND d.video_id<>''
    AND d.source_id<>''
    AND (d.creator_handle<>'' OR d.creator_display_name<>'')
    AND (d.source_url LIKE 'https://www.tiktok.com/%' OR d.source_url LIKE 'https://tiktok.com/%')`;
  const countRow = await env.DB.prepare(
    `SELECT COUNT(DISTINCT CASE WHEN d.video_id<>'' THEN d.video_id ELSE d.source_id END) AS matched_records
       FROM search_documents_fts
       JOIN search_documents AS d ON d.rowid=search_documents_fts.rowid
      WHERE search_documents_fts MATCH ? AND ${eligibilitySql}`,
  ).bind(ftsQuery).first<EvidenceBriefCountRow>();
  const candidateRows = await env.DB.prepare(
    `SELECT d.id, d.source_id, d.video_id, d.title, d.body,
            d.creator_handle, d.creator_display_name, d.source_url,
            d.published_date, d.topics_json, d.topic_labels_json,
            d.full_transcript_public, d.admission_state,
            c.claim_text, c.evidence_excerpt,
            c.evidence_start_seconds, c.evidence_end_seconds
       FROM search_documents_fts
       JOIN search_documents AS d ON d.rowid=search_documents_fts.rowid
       LEFT JOIN public_projection_cards AS c ON c.search_id=d.id
      WHERE search_documents_fts MATCH ? AND ${eligibilitySql}
      ORDER BY bm25(search_documents_fts) ASC, d.published_date DESC, d.id ASC
      LIMIT ?`,
  ).bind(ftsQuery, EVIDENCE_BRIEF_V2_CANDIDATE_LIMIT).all<EvidenceBriefCandidate>();
  const corpus = await env.DB.prepare(
    `SELECT COUNT(*) AS document_count,
            COUNT(DISTINCT CASE WHEN video_id<>'' THEN video_id ELSE source_id END) AS source_count,
            MAX(captured_at) AS latest_captured_at
       FROM search_documents
      WHERE full_transcript_public=0 AND admission_state='normal_public_card'`,
  ).first<EvidenceCorpusWatermarkRow>();

  const selectedCandidates: EvidenceBriefCandidate[] = [];
  const seenSources = new Set<string>();
  const creatorCounts = new Map<string, number>();
  for (const candidate of candidateRows.results) {
    if (!evidenceCandidateIsPublic(candidate)) continue;
    const sourceKey = briefString(candidate.video_id) || briefString(candidate.source_id);
    const creatorKey = evidenceCandidateCreator(candidate).toLocaleLowerCase("en-US");
    const claim = briefString(candidate.claim_text) || briefString(candidate.title);
    const excerpt = briefString(candidate.evidence_excerpt) || briefString(candidate.body);
    if (!sourceKey || seenSources.has(sourceKey) || !claim || !excerpt) continue;
    if ((creatorCounts.get(creatorKey) ?? 0) >= EVIDENCE_BRIEF_V2_CREATOR_LIMIT) continue;
    seenSources.add(sourceKey);
    creatorCounts.set(creatorKey, (creatorCounts.get(creatorKey) ?? 0) + 1);
    selectedCandidates.push(candidate);
    if (selectedCandidates.length >= EVIDENCE_BRIEF_V2_SOURCE_LIMIT) break;
  }

  const findings = selectedCandidates.map((candidate) => {
    const videoId = briefString(candidate.video_id);
    const startSeconds = evidenceCandidateSeconds(candidate.evidence_start_seconds);
    const endSeconds = evidenceCandidateSeconds(candidate.evidence_end_seconds);
    return {
      claim: truncateText(briefString(candidate.claim_text) || briefString(candidate.title), 220),
      evidence_excerpt: truncateText(
        briefString(candidate.evidence_excerpt) || briefString(candidate.body),
        480,
      ),
      creator_handle: evidenceCandidateCreator(candidate),
      published_date: briefString(candidate.published_date) || null,
      base2026_url: `${PUBLIC_ORIGIN}/sources/tiktok-video-${videoId}`,
      original_source_url: safePublicSourceUrl(briefString(candidate.source_url)),
      evidence_start_seconds: startSeconds,
      evidence_end_seconds: startSeconds !== null && endSeconds !== null && endSeconds >= startSeconds
        ? endSeconds
        : null,
      topics: evidenceCandidateTopics(candidate),
    };
  });
  const distinctCreators = new Set(findings.map((finding) => finding.creator_handle.toLocaleLowerCase("en-US")));
  const publishedDates = findings
    .map((finding) => finding.published_date)
    .filter((value): value is string => Boolean(value))
    .sort();
  const status = findings.length === 0
    ? "no_evidence"
    : findings.length === 1 || distinctCreators.size === 1
      ? "limited"
      : "full";
  const signalCreators = new Map<string, Set<string>>();
  for (const finding of findings) {
    for (const topic of finding.topics) {
      if (!signalCreators.has(topic)) signalCreators.set(topic, new Set());
      signalCreators.get(topic)?.add(finding.creator_handle.toLocaleLowerCase("en-US"));
    }
  }
  const repeatedSignals = [...signalCreators.entries()]
    .filter(([, creatorSet]) => creatorSet.size >= 3)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([topic, creatorSet]) => ({ topic, distinct_creators: creatorSet.size }));
  const matchedRecords = numericCount(countRow?.matched_records) || seenSources.size;
  const latestCapturedAt = briefString(corpus?.latest_captured_at).slice(0, 10) || "unknown";
  const corpusVersion = `public-d1:${numericCount(corpus?.document_count)}:${numericCount(corpus?.source_count)}:${latestCapturedAt}`;
  const limits = ["This brief covers the current Base2026 public corpus, not the whole SEO industry."];
  if (status === "limited") limits.push("Only one eligible source or creator supports this brief; treat it as a lead, not consensus.");
  if (status === "no_evidence") limits.push("Not enough public evidence in Base2026 for this question.");

  return jsonResponse({
    brief_version: EVIDENCE_BRIEF_VERSION,
    question: queryText,
    normalized_question: normalizedQuestion,
    status,
    corpus_version: corpusVersion,
    ranking_version: EVIDENCE_BRIEF_RANKING_VERSION,
    generated_at: new Date().toISOString(),
    coverage: {
      matched_records: matchedRecords,
      selected_sources: findings.length,
      distinct_creators: distinctCreators.size,
      published_date_min: publishedDates[0] ?? null,
      published_date_max: publishedDates.at(-1) ?? null,
    },
    findings,
    repeated_signals: repeatedSignals,
    limits,
  }, 200, cacheHeaders);
}

async function handleHealth(env: EnvWithBindings): Promise<Response> {
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 binding DB is not configured");
  try {
    await env.DB.prepare("SELECT 1 AS ok").first<{ ok: number }>();
  } catch {
    throw new RequestError(503, "DB_UNAVAILABLE", "D1 search database is unavailable");
  }
  return jsonResponse({ ok: true, service: "base2026", search: "d1-fts5", index: INDEX_UID });
}

async function handlePublicStats(request: Request, env: EnvWithBindings): Promise<Response> {
  if (request.method !== "GET" && request.method !== "HEAD") throw methodError(request.method, "GET, HEAD");
  if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 search database is unavailable");
  const cacheHeaders = {
    "Cache-Control": "public, max-age=60, s-maxage=300",
  };
  if (request.method === "HEAD") {
    return new Response(null, { status: 200, headers: withPublicResponseHeaders(JSON_HEADERS, cacheHeaders) });
  }

  const row = await env.DB.prepare(
    `SELECT
       (SELECT COUNT(*) FROM search_documents) AS document_count,
       (SELECT COUNT(DISTINCT CASE WHEN video_id<>'' THEN video_id ELSE source_id END)
          FROM search_documents) AS source_count,
       (SELECT COALESCE(SUM(CASE WHEN full_transcript_public=1 THEN 1 ELSE 0 END), 0)
          FROM search_documents) AS full_transcript_public,
       (SELECT COUNT(*) FROM public_projection_receipts WHERE status='applied') AS public_evidence_routes,
       (SELECT COUNT(*) FROM public_projection_cards) AS projected_cards`,
  ).first<{
    document_count: number;
    source_count: number;
    full_transcript_public: number;
    public_evidence_routes: number;
    projected_cards: number;
  }>();
  if (!row) throw new RequestError(503, "DB_UNAVAILABLE", "Public dataset statistics are unavailable");

  return jsonResponse({
    ok: true,
    service: "base2026",
    generated_at: new Date().toISOString(),
    dataset: {
      documents_indexed: numericCount(row.document_count),
      distinct_sources: numericCount(row.source_count),
      public_evidence_routes: numericCount(row.public_evidence_routes),
      projected_cards: numericCount(row.projected_cards),
      full_transcripts_published: numericCount(row.full_transcript_public),
    },
  }, 200, cacheHeaders);
}

function formString(body: Record<string, unknown>, field: string, maxLength: number, required = false): string {
  const raw = body[field];
  if (raw === undefined || raw === null) {
    if (required) throw new RequestError(400, "INVALID_FORM", `${field} is required`);
    return "";
  }
  if (typeof raw !== "string") throw new RequestError(400, "INVALID_FORM", `${field} must be text`);
  const value = raw.trim();
  if (required && !value) throw new RequestError(400, "INVALID_FORM", `${field} is required`);
  if (value.length > maxLength) throw new RequestError(400, "INVALID_FORM", `${field} is too long`);
  if (/\0/u.test(value)) throw new RequestError(400, "INVALID_FORM", `${field} contains invalid characters`);
  return value;
}

function formChoice(body: Record<string, unknown>, field: string, choices: readonly string[], required = false): string {
  const value = formString(body, field, 80, required);
  if (value && !choices.includes(value)) throw new RequestError(400, "INVALID_FORM", `${field} is not supported`);
  return value;
}

function validatePublicUrl(value: string): string {
  if (!value) return "";
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new RequestError(400, "INVALID_FORM", "publicUrl must be a valid URL");
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new RequestError(400, "INVALID_FORM", "publicUrl must use http or https");
  }
  return url.toString();
}

function parseInboxSubmission(kind: FormKind, body: Record<string, unknown>): InboxSubmission | null {
  if (formString(body, "companySite", 500)) return null;
  const startedAt = body.startedAt;
  if (typeof startedAt !== "number" || !Number.isFinite(startedAt)) {
    throw new RequestError(400, "INVALID_FORM", "form timing is missing");
  }
  const elapsed = Date.now() - startedAt;
  if (elapsed < MIN_FORM_COMPLETION_MS || elapsed > MAX_FORM_COMPLETION_MS) {
    throw new RequestError(400, "INVALID_FORM", "form timing is invalid; please reload and try again");
  }
  if (body.consent !== "yes") throw new RequestError(400, "INVALID_FORM", "consent is required");

  const email = formString(body, "email", 254, true).toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(email)) {
    throw new RequestError(400, "INVALID_FORM", "email must be valid");
  }
  const attribution = formChoice(body, "attribution", ["discuss", "yes", "no"], false) || "discuss";
  const common = {
    name: formString(body, "name", 100, true),
    email,
    organization: formString(body, "organization", 140, true),
    role: formString(body, "role", 100),
    publicUrl: validatePublicUrl(formString(body, "publicUrl", 500)),
    constraints: formString(body, "constraints", 1200),
    attribution,
  };

  let category: string;
  let payload: Record<string, string>;
  if (kind === "support") {
    category = formChoice(body, "supportPath", ["credits", "tooling", "data", "mentorship", "other"], true);
    payload = {
      offer: formString(body, "offer", 2000, true),
      outcome: formString(body, "outcome", 2000, true),
      constraints: common.constraints,
    };
  } else {
    category = formChoice(body, "partnerType", ["infrastructure", "data", "research", "rights", "community", "other"], true);
    payload = {
      summary: formString(body, "summary", 2000, true),
      contribution: formString(body, "contribution", 1600, true),
      request: formString(body, "request", 1600, true),
      firstStep: formString(body, "firstStep", 500, true),
      constraints: common.constraints,
    };
  }
  return {
    id: crypto.randomUUID(),
    kind,
    name: common.name,
    email: common.email,
    organization: common.organization,
    role: common.role,
    category,
    publicUrl: common.publicUrl,
    attribution,
    payload,
  };
}

async function handleInboxForm(request: Request, env: EnvWithBindings, kind: FormKind): Promise<Response> {
  if (request.method !== "POST") throw methodError(request.method);
  if (request.headers.get("origin") !== FORM_ORIGIN) {
    throw new RequestError(403, "INVALID_ORIGIN", "form submissions must come from base2026.dev");
  }
  if (!contentTypeIsJson(request)) throw new RequestError(415, "UNSUPPORTED_MEDIA_TYPE", "form requests require Content-Type: application/json");
  if (!env.INBOX_DB) throw new RequestError(503, "INBOX_NOT_CONFIGURED", "project inbox is not configured");
  const submission = parseInboxSubmission(kind, parseJsonBody(await readBoundedBody(request)));
  if (!submission) {
    return jsonResponse({ ok: true, reference: "received" }, 202, { "Access-Control-Allow-Origin": FORM_ORIGIN, Vary: "Origin" });
  }
  const cleanup = env.INBOX_DB.prepare(
    "DELETE FROM project_inbox WHERE status = 'new' AND submitted_at < datetime('now', '-90 days')",
  );
  const insert = env.INBOX_DB.prepare(
    "INSERT INTO project_inbox (id, kind, submitted_at, name, email, organization, role, category, public_url, proposal_json, attribution, consent_version, status) VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')",
  ).bind(
    submission.id,
    submission.kind,
    submission.name,
    submission.email,
    submission.organization,
    submission.role,
    submission.category,
    submission.publicUrl,
    JSON.stringify(submission.payload),
    submission.attribution,
    FORM_CONSENT_VERSION,
  );
  await env.INBOX_DB.batch([cleanup, insert]);
  return jsonResponse(
    { ok: true, reference: submission.id },
    201,
    { "Access-Control-Allow-Origin": FORM_ORIGIN, Vary: "Origin" },
  );
}

/**
 * Service-binding/RPC entrypoint for the separately authorized public
 * projection lane.  The default export below remains the existing public
 * fetch/static-assets Worker; this class is not a new HTTP publication route.
 */
export class PublicProjectionEntrypoint extends WorkerEntrypoint<Env> {
  async publishEditorialArticle(input: unknown, overwrite?: EditorialOverwrite) {
    return publishEditorialArticle(this.env.DB, input, {
      now: new Date().toISOString(),
      ...(overwrite === undefined ? {} : { overwrite }),
    });
  }

  async inspectEditorialArticle(slug: string) {
    // Repair must be able to inspect the current CAS receipt even while public
    // guide reads are held by a changed/withdrawn evidence dependency.
    const article = await inspectStoredEditorialArticle(this.env.DB, slug, new Date().toISOString());
    return article ? { ok: true, receipt: article.receipt } : { ok: false, code: "NOT_FOUND" };
  }

  async applyProjection(input: unknown) {
    return applyPublicProjection(this.env.DB, input);
  }

  async inspectPublicSource(input: unknown) {
    return inspectPublicSource(this.env.DB, input);
  }

  async verifyProjection(input: unknown) {
    return verifyPublicProjection(this.env.DB, input);
  }

  async rollbackProjection(input: unknown) {
    return rollbackPublicProjection(this.env.DB, input);
  }
}

export default {
  async fetch(request: Request, env: EnvWithBindings, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (MEMBER_API_PATH.test(url.pathname)) {
      // Keep auth failures outside the public API error/CORS path. The member
      // handler enforces canonical HTTPS and the explicit local-test exception.
      try {
        const member = await handleMemberRequest(request, env);
        return privateMemberResponse(member ?? memberError(404, "NOT_FOUND", "Not found."));
      } catch {
        // Do not log request URLs or provider errors: callbacks contain codes.
        return privateMemberResponse(memberError(503, "AUTH_UNAVAILABLE", "Private research is temporarily unavailable."));
      }
    }
    try {
      if (url.protocol !== "https:") {
        url.protocol = "https:";
        return publicRedirect(url.toString(), 301);
      }
      if (MEMBER_PAGE_PATH.test(url.pathname)) {
        if (request.method !== "GET" && request.method !== "HEAD") {
          return privateMemberResponse(memberError(405, "METHOD_NOT_ALLOWED", "Method is not allowed."));
        }
        if (url.pathname === "/my-research" || url.pathname === "/my-research/index.html") {
          url.pathname = "/my-research/";
          return privateMemberResponse(new Response(null, { status: 308, headers: { Location: url.toString() } }), true);
        }
        if (url.pathname !== "/my-research/" || !env.ASSETS) {
          return privateMemberResponse(memberError(404, "NOT_FOUND", "Not found."));
        }
        try {
          return privateMemberResponse(await env.ASSETS.fetch(request), true);
        } catch {
          return privateMemberResponse(memberError(503, "ASSET_UNAVAILABLE", "Private research is temporarily unavailable."));
        }
      }
      const guide = await handleEvidenceGuideRoute(request, env);
      if (guide) return publicAssetResponse(guide);
      const editorial = await handleEditorialRoute(request, env);
      if (editorial) return publicAssetResponse(editorial);
      const sourceCatalog = await handleSourceCatalog(request, env, url);
      if (sourceCatalog) return publicAssetResponse(sourceCatalog);
      if (
        request.method === "GET" &&
        (url.pathname === "/search" ||
          url.pathname === "/search/" ||
          url.pathname === "/search/index.html" ||
          url.pathname === "/search.html" ||
          url.pathname === "/meili.html")
      ) {
        url.pathname = "/workspace/";
        url.hash = "";
        return publicRedirect(url.toString(), 301);
      }
      if (url.pathname === "/api/health") return await handleHealth(env);
      if (url.pathname === "/api/stats") return await handlePublicStats(request, env);
      if (url.pathname === "/api/evidence-brief") return await handleEvidenceBrief(request, env, url);
      if (url.pathname === "/api/evidence-brief/v2") return await handleEvidenceBriefV2(request, env, url);
      if (url.pathname === "/sitemap-dynamic.xml") return await handleDynamicSitemap(request, env);
      if (url.pathname === "/api/forms/support") return await handleInboxForm(request, env, "support");
      if (url.pathname === "/api/forms/partner") return await handleInboxForm(request, env, "partner");
      if (url.pathname === "/api/search/multi-search" || url.pathname === "/knowledge-search/multi-search") {
        if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 binding DB is not configured");
        return await handleSearch(request, env);
      }
      if (request.method === "GET" || request.method === "HEAD") {
        const sourceMatch = url.pathname.match(DYNAMIC_SOURCE_ROUTE);
        if (sourceMatch) {
          if (url.pathname.endsWith("/")) {
            url.pathname = url.pathname.slice(0, -1);
            return publicRedirect(url.toString(), 308);
          }
          const response = await handleProjectedSourcePage(request, env, sourceMatch[1]);
          if (response) return response;
        }
      }
      if (env.ASSETS) return publicAssetResponse(await env.ASSETS.fetch(request));
      throw new RequestError(404, "NOT_FOUND", "asset or API route not found");
    } catch (error) {
      if (error instanceof RequestError) return errorResponse(error);
      console.error(JSON.stringify({ event: "base2026_worker_error", path: url.pathname }));
      return errorResponse(new RequestError(500, "INTERNAL_ERROR", "request could not be completed"));
    }
  },
};
