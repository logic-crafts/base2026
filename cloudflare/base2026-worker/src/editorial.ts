/**
 * Structural boundary and durable store for reviewed, first-party editorial.
 *
 * No HTTP handler, authoring model, source fetch, renderer or publication
 * authority lives here. The caller must be a separately authorized service
 * binding. A Sol review declaration binds a payload, not proof of its facts.
 */

import {
  EDITORIAL_EVIDENCE_LIMITS,
  EditorialEvidenceError,
  editorialEvidenceSnapshotGuardSql,
  isPublicEvidenceDocumentId,
  isPublicEvidenceSourceId,
  resolveEditorialEvidence,
  type EditorialEvidence,
  type EditorialEvidenceDependency,
  type EditorialEvidenceSnapshot,
} from "./evidence-dependencies";

export type { EditorialEvidence, EditorialEvidenceDependency } from "./evidence-dependencies";

export const EDITORIAL_SCHEMA = "base2026.editorial.v1" as const;
export const EDITORIAL_RECEIPT_SCHEMA = "base2026.editorial-publication-receipt.v1" as const;
export const EDITORIAL_ORIGIN = "https://base2026.dev" as const;
export const EDITORIAL_SITEMAP_PAGE_SIZE = 100;
/** Existing task canonicals only. Registration is not publication approval. */
export const EDITORIAL_EVIDENCE_GUIDE_SLUGS: readonly string[] = Object.freeze([
  "internal-linking", "search-console-low-hanging-fruit", "content-freshness", "schema-ai-citations", "llms-txt-risk",
]);
export const EDITORIAL_LIMITS = Object.freeze({
  payload_bytes: 128 * 1024,
  slug: 120,
  title: 180,
  description: 320,
  lede: 1_400,
  category: 80,
  tags: 12,
  tag: 48,
  sources: 24,
  sections: 16,
  blocks_per_section: 24,
  total_blocks: 128,
  paragraph: 2_400,
  list_items: 16,
  list_item: 800,
  citations_per_item: 8,
  related_paths: 12,
  list_page: 25,
  future_skew_ms: 5 * 60 * 1_000,
});

const KEBAB = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const SHA256 = /^[a-f0-9]{64}$/u;
const CONTROL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]/u;
const EMAIL = /[\p{L}\p{N}._%+-]+@[\p{L}\p{N}.-]+\.[\p{L}]{2,}/u;
const PHONE = /(?<!\d)(?:\+\d{8,15}|(?:\+?\d{1,3}[\s().-])?(?:\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10}))(?!\d)/u;
const LOCAL_PATH = /(?:file:\/\/|~\/|\/(?:Users|home|tmp|var|private|Volumes|proc|etc)\/|(?:^|[\s("'=])[A-Za-z]:[\\/]|PRIVATE_BASE2026_WORK_INBOX|\.codex\/|\.planning\/)/iu;
const SECRET = /\b(?:api|access|auth|authentication|client|app|webhook)?[_\s-]*(?:key|token|secret|password|passwd|credential|cookie|session[_\s-]*id)\s*[:=]\s*\S+/iu;
const TOKEN = /(?:\b(?:sk[-_](?:live[_-]|test[_-]|proj-)?[A-Z0-9_-]{12,}|(?:ghp|github_pat|xox[baprs])[-_][A-Z0-9_-]{8,}|AIza[A-Z0-9_-]{20,})\b|\bbearer\s+[A-Z0-9._~+/=-]{8,}\b|-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH))/iu;
const PRIVATE_MARKER = /(?:\b(?:private[_-](?:only|notes?|context|source|text)|not[_\s-]*for[_\s-]*public[_\s-]*export)\b|\bprivate\s+(?:only|notes?|context)\s*[:=]|\b(?:raw|full)[_-](?:transcripts?|captions?|asr)\b|(?:^|\n)[ \t]*(?:#{1,6}[ \t]*)?(?:(?:RAW|FULL)\s+(?:TRANSCRIPTS?|CAPTIONS|ASR)|PRIVATE\s+(?:ONLY|NOTES?|CONTEXT))[ \t]*(?:[:=]|\r?\n|$)|\b(?:raw|full)\s+(?:transcript|captions?|asr)\s*[:=])/iu;
const TRANSCRIPT_STRUCTURE = /(?:^|\n)\s*(?:WEBVTT\b|\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}\s*-->\s*\d{1,2}:\d{2})/iu;
const MARKUP = /[<>]|&(?:lt|gt|#0*60|#0*62|#x0*3c|#x0*3e);|\b(?:javascript|vbscript)\s*:|data\s*:\s*(?:text\/html|image\/svg)/iu;
const SENSITIVE_QUERY = /^(?:.*(?:token|secret|password|passwd|credential|cookie|session|signature|authorization|authentication|apikey|accesskey|privatekey|clientsecret).*|auth|key|sig|code|jwt|email|mail|phone|telephone|contact|address|ip|userid|username)$/iu;
const PRIVATE_HOST_SUFFIXES = [
  "localhost", "local", "localdomain", "internal", "intranet", "private", "test", "invalid", "example",
  "home", "lan", "corp", "onion", "alt", "arpa", "localtest.me", "lvh.me", "vcap.me",
  "nip.io", "sslip.io", "traefik.me",
];
const PUBLIC_PATHS = new Set([
  "/", "/blog", "/about", "/methodology", "/opt-out", "/dataset", "/api", "/analytics", "/roadmap",
  "/topics/", "/compare/", "/creators/", "/sources/",
  "/journal/source-backed-video-search-cloudflare/", "/journal/source-diversity-check/",
]);
const encoder = new TextEncoder();

export interface EditorialSource {
  id: string;
  url: string;
  title: string;
  creator?: string;
  published_at?: string;
  checked_at: string;
}

export interface EditorialTextItem {
  text: string;
  citation_ids: string[];
}

export type EditorialBlock = ({ type: "paragraph" } & EditorialTextItem)
  | { type: "list"; items: EditorialTextItem[] };

export interface EditorialSection {
  id: string;
  heading: string;
  blocks: EditorialBlock[];
}

export interface EditorialHero {
  path: string;
  alt: string;
  credit: string;
  ai_generated: boolean;
}

export interface EditorialPayload {
  schema_version: typeof EDITORIAL_SCHEMA;
  kind: "source_based_article" | "engineering_note" | "evidence_guide";
  slug: string;
  revision: number;
  title: string;
  description: string;
  lede: string;
  category: string;
  tags: string[];
  published_at: string;
  updated_at: string;
  author: { name: "Alex Yarosh" };
  ai_assistance_disclosure: string;
  hero?: EditorialHero;
  sources: EditorialSource[];
  sections: EditorialSection[];
  related_paths: string[];
  first_party_context?: string;
  evidence?: EditorialEvidence;
}

export interface EditorialReview {
  reviewer: "sol-max";
  outcome: "pass";
  reviewed_at: string;
  payload_sha256: string;
}

export interface EditorialPacket {
  payload: EditorialPayload;
  review: EditorialReview;
}

/** Counts describe the packet's metadata, not source independence or truth. */
export interface EditorialDiagnostics {
  source_count: number;
  distinct_source_urls: number;
  distinct_source_metadata: number;
  known_creator_count: number;
  sources_without_known_creator: number;
  cited_source_count: number;
  section_count: number;
}

export interface EditorialIssue {
  code: string;
  field: string;
}

export interface ValidatedEditorialPayload {
  ok: true;
  payload: EditorialPayload;
  payload_sha256: string;
  canonical_payload_json: string;
  diagnostics: EditorialDiagnostics;
}

export type EditorialPayloadValidation = ValidatedEditorialPayload | { ok: false; issues: EditorialIssue[] };
export type EditorialPacketValidation = (ValidatedEditorialPayload & { review: EditorialReview })
  | { ok: false; issues: EditorialIssue[] };

export class EditorialValidationError extends Error {
  readonly status = 400;

  constructor(readonly code: string, readonly field: string) {
    // A rejected field value, source URL or unknown key must never enter logs.
    super(code);
    this.name = "EditorialValidationError";
  }
}

export class EditorialStoreError extends Error {
  readonly status = 500;

  constructor(readonly code: string) {
    super(code);
    this.name = "EditorialStoreError";
  }
}

function reject(code: string, field: string): never {
  throw new EditorialValidationError(code, field);
}

function record(value: unknown, required: readonly string[], optional: readonly string[], field: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) reject("EDITORIAL_OBJECT_REQUIRED", field);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) reject("EDITORIAL_OBJECT_REQUIRED", field);
  const descriptors = Object.getOwnPropertyDescriptors(value);
  if (Object.getOwnPropertySymbols(value).length) reject("EDITORIAL_UNSUPPORTED_FIELDS", field);
  const keys = Object.keys(descriptors);
  if (keys.some((key) => !required.includes(key) && !optional.includes(key))
    || required.some((key) => !Object.hasOwn(descriptors, key))
    || keys.some((key) => !descriptors[key].enumerable || !("value" in descriptors[key]))) {
    reject("EDITORIAL_UNSUPPORTED_FIELDS", field);
  }
  return value as Record<string, unknown>;
}

function boundedString(value: unknown, field: string, max: number): string {
  if (typeof value !== "string" || value.length < 1 || value.length > max || value !== value.trim()
    || CONTROL.test(value) || /[\ud800-\udfff]/u.test(value)) reject("EDITORIAL_STRING_INVALID", field);
  return value;
}

function decodedForAudit(value: string, field: string): string {
  let decoded = value;
  for (let count = 0; count < 3; count += 1) {
    if (!/%[a-f0-9]{2}/iu.test(decoded)) return decoded;
    // A stray percent sign in prose must not hide a separately encoded key.
    const next = decoded.replace(/(?:%[a-f0-9]{2})+/giu, (part) => {
      try { return decodeURIComponent(part); }
      catch { return part.replace(/%[0-7][a-f0-9]/giu, (ascii) => String.fromCharCode(Number.parseInt(ascii.slice(1), 16))); }
    });
    if (next === decoded) return decoded;
    decoded = next;
  }
  if (/%[a-f0-9]{2}/iu.test(decoded)) reject("EDITORIAL_ENCODING_INVALID", field);
  return decoded;
}

function assertPublicText(value: string, field: string, checkPhone = true): void {
  const audited = decodedForAudit(value, field).normalize("NFKC");
  if (CONTROL.test(audited) || MARKUP.test(audited)) reject("EDITORIAL_MARKUP_REJECTED", field);
  if (EMAIL.test(audited) || (checkPhone && PHONE.test(audited)) || LOCAL_PATH.test(audited)
    || SECRET.test(audited) || TOKEN.test(audited) || PRIVATE_MARKER.test(audited)
    || TRANSCRIPT_STRUCTURE.test(audited)) reject("EDITORIAL_PRIVACY_REJECTED", field);
}

function publicText(value: unknown, field: string, max: number): string {
  const text = boundedString(value, field, max);
  assertPublicText(text, field);
  return text;
}

function id(value: unknown, field: string, max = 64): string {
  const text = boundedString(value, field, max);
  if (!KEBAB.test(text)) reject("EDITORIAL_ID_INVALID", field);
  // Identifiers cannot hold contacts/credentials either. Do not apply prose
  // topic-marker matching: a slug may legitimately discuss transcript safety.
  if (TOKEN.test(text) || PHONE.test(text)) reject("EDITORIAL_PRIVACY_REJECTED", field);
  return text;
}

function revision(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 1) reject("EDITORIAL_REVISION_INVALID", field);
  return value;
}

function hash(value: unknown, field: string): string {
  const text = boundedString(value, field, 64);
  if (!SHA256.test(text)) reject("EDITORIAL_HASH_INVALID", field);
  return text;
}

/** Strict calendar validation avoids Date.parse accepting February 30. */
function timestamp(value: unknown, field: string, nowMs?: number): string {
  const text = boundedString(value, field, 35);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|[+-]\d{2}:\d{2})$/u.exec(text);
  if (!match) reject("EDITORIAL_TIMESTAMP_INVALID", field);
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, , zone] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > monthDays[month - 1]
    || Number(hourText) > 23 || Number(minuteText) > 59 || Number(secondText) > 59
    || (zone !== "Z" && (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4)) > 59))) {
    reject("EDITORIAL_TIMESTAMP_INVALID", field);
  }
  const milliseconds = Date.parse(text);
  if (!Number.isFinite(milliseconds)) reject("EDITORIAL_TIMESTAMP_INVALID", field);
  const normalized = new Date(milliseconds).toISOString();
  if (normalized.length !== 24) reject("EDITORIAL_TIMESTAMP_INVALID", field);
  if (nowMs !== undefined && milliseconds > nowMs + EDITORIAL_LIMITS.future_skew_ms) reject("EDITORIAL_TIMESTAMP_FUTURE", field);
  return normalized;
}

function array(value: unknown, field: string, min: number, max: number): unknown[] {
  if (!Array.isArray(value) || value.length < min || value.length > max) reject("EDITORIAL_ARRAY_INVALID", field);
  // Sparse arrays, properties and accessors are not a JSON packet.
  const keys = Reflect.ownKeys(value);
  if (keys.length !== value.length + 1 || keys.some((key) => key !== "length"
    && (typeof key !== "string" || !/^(?:0|[1-9]\d*)$/u.test(key)
      || !Object.hasOwn(Object.getOwnPropertyDescriptor(value, key) ?? {}, "value")))) {
    reject("EDITORIAL_ARRAY_INVALID", field);
  }
  return value;
}

function unique(values: string[], field: string): void {
  if (new Set(values).size !== values.length) reject("EDITORIAL_DUPLICATE", field);
}

function normalizedMetadata(value: string): string {
  return value.normalize("NFKC").replace(/\s+/gu, " ").trim().toLocaleLowerCase("en-US");
}

function knownCreator(source: EditorialSource): string | null {
  if (!source.creator) return null;
  const creator = normalizedMetadata(source.creator);
  return /^(?:unknown(?: creator)?|not (?:stated|provided|known)|unspecified|unattributed|n\/a)$/u.test(creator) ? null : creator;
}

function sourceMetadataKey(source: EditorialSource): string {
  return JSON.stringify([normalizedMetadata(source.title), knownCreator(source), source.published_at ?? null]);
}

/** No DNS lookup: accepted syntax is not proof that a source is public/live. */
function sourceUrl(value: unknown, field: string): string {
  const raw = boundedString(value, field, 2_048);
  if (!raw.startsWith("https://") || /[\s\\]/u.test(raw) || /%(?![a-f0-9]{2})/iu.test(raw)) reject("EDITORIAL_URL_INVALID", field);
  let url: URL;
  try { url = new URL(raw); } catch { reject("EDITORIAL_URL_INVALID", field); }
  if (url.protocol !== "https:" || url.username || url.password || url.hash || raw.includes("#") || url.port
    || url.hostname.endsWith(".") || url.hostname.length > 253
    || !url.hostname.includes(".") || /^[\d.]+$/u.test(url.hostname)
    || url.hostname.split(".").some((label) => !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/u.test(label))
    || PRIVATE_HOST_SUFFIXES.some((suffix) => url.hostname === suffix || url.hostname.endsWith(`.${suffix}`))) {
    reject("EDITORIAL_URL_INVALID", field);
  }
  const decoded = decodedForAudit(raw, field);
  assertPublicText(decoded, field, false);
  if (/\\|[\u0000-\u0020]|(?:^|\/)\.{1,2}(?:\/|$|[?#])/u.test(decoded)) reject("EDITORIAL_URL_INVALID", field);
  const params = [...url.searchParams];
  if (params.length > 16) reject("EDITORIAL_URL_INVALID", field);
  for (const [key, parameter] of params) {
    const normalizedKey = decodedForAudit(key, field).normalize("NFKC").replace(/[^a-z0-9]/giu, "");
    if (key.length > 64 || parameter.length > 256 || SENSITIVE_QUERY.test(normalizedKey)) reject("EDITORIAL_URL_PRIVATE", field);
    assertPublicText(decodedForAudit(parameter, field), field);
  }
  return url.href;
}

export function isEditorialRelatedPath(value: string): boolean {
  if (value.length > 220 || /[?#%\\\s]/u.test(value)) return false;
  if (PUBLIC_PATHS.has(value)) return true;
  const blog = /^\/blog\/([a-z0-9]+(?:-[a-z0-9]+)*)\/$/u.exec(value);
  if (blog) return blog[1].length <= EDITORIAL_LIMITS.slug;
  return /^\/(?:topics|compare|creators)\/(?=[a-z0-9-]*[a-z])[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(value)
    || /^\/sources\/tiktok-video-\d{10,30}$/u.test(value);
}

function relatedPath(value: unknown, field: string): string {
  const path = boundedString(value, field, 220);
  if (!isEditorialRelatedPath(path)) reject("EDITORIAL_RELATED_PATH_INVALID", field);
  // The route allowlist already excludes private/stateful paths. A public
  // article or topic slug about transcript privacy is not a private packet.
  if (TOKEN.test(path) || (!path.startsWith("/sources/tiktok-video-") && PHONE.test(path))) reject("EDITORIAL_PRIVACY_REJECTED", field);
  return path;
}

function hero(value: unknown): EditorialHero {
  const input = record(value, ["path", "alt", "credit", "ai_generated"], [], "payload.hero");
  const path = boundedString(input.path, "payload.hero.path", 240);
  if (!/^\/static\/assets\/(?:[a-z0-9]+(?:[-_][a-z0-9]+)*\/)*[a-z0-9]+(?:[-_][a-z0-9]+)*\.(?:png|jpe?g|webp|avif|gif)$/u.test(path)) {
    reject("EDITORIAL_HERO_PATH_INVALID", "payload.hero.path");
  }
  if (TOKEN.test(path)) reject("EDITORIAL_PRIVACY_REJECTED", "payload.hero.path");
  if (typeof input.ai_generated !== "boolean") reject("EDITORIAL_BOOLEAN_REQUIRED", "payload.hero.ai_generated");
  return { path, alt: publicText(input.alt, "payload.hero.alt", 240), credit: publicText(input.credit, "payload.hero.credit", 240), ai_generated: input.ai_generated };
}

function source(value: unknown, index: number, nowMs: number): EditorialSource {
  const field = `payload.sources[${index}]`;
  const input = record(value, ["id", "url", "title", "checked_at"], ["creator", "published_at"], field);
  return {
    id: id(input.id, `${field}.id`),
    url: sourceUrl(input.url, `${field}.url`),
    title: publicText(input.title, `${field}.title`, 240),
    ...(Object.hasOwn(input, "creator") ? { creator: publicText(input.creator, `${field}.creator`, 120) } : {}),
    ...(Object.hasOwn(input, "published_at") ? { published_at: timestamp(input.published_at, `${field}.published_at`, nowMs) } : {}),
    checked_at: timestamp(input.checked_at, `${field}.checked_at`, nowMs),
  };
}

function textItem(value: unknown, field: string, max: number, sourceIds: Set<string>, paragraph = false): EditorialTextItem {
  const input = record(value, paragraph ? ["type", "text", "citation_ids"] : ["text", "citation_ids"], [], field);
  const citations = array(input.citation_ids, `${field}.citation_ids`, 0, EDITORIAL_LIMITS.citations_per_item)
    .map((item) => id(item, `${field}.citation_ids`));
  unique(citations, `${field}.citation_ids`);
  if (citations.some((citation) => !sourceIds.has(citation))) reject("EDITORIAL_CITATION_UNRESOLVED", `${field}.citation_ids`);
  return { text: publicText(input.text, `${field}.text`, max), citation_ids: citations };
}

function section(value: unknown, index: number, sourceIds: Set<string>): EditorialSection {
  const field = `payload.sections[${index}]`;
  const input = record(value, ["id", "heading", "blocks"], [], field);
  const blocks = array(input.blocks, `${field}.blocks`, 1, EDITORIAL_LIMITS.blocks_per_section).map((item, blockIndex): EditorialBlock => {
    const blockField = `${field}.blocks[${blockIndex}]`;
    const block = record(item, ["type"], ["text", "citation_ids", "items"], blockField);
    if (block.type === "paragraph") return { type: "paragraph", ...textItem(block, blockField, EDITORIAL_LIMITS.paragraph, sourceIds, true) };
    if (block.type !== "list") reject("EDITORIAL_BLOCK_TYPE_INVALID", blockField);
    const list = record(block, ["type", "items"], [], blockField);
    return { type: "list", items: array(list.items, `${blockField}.items`, 1, EDITORIAL_LIMITS.list_items)
      .map((listItem, itemIndex) => textItem(listItem, `${blockField}.items[${itemIndex}]`, EDITORIAL_LIMITS.list_item, sourceIds)) };
  });
  return { id: id(input.id, `${field}.id`), heading: publicText(input.heading, `${field}.heading`, 180), blocks };
}

function isFirstPartySource(source: EditorialSource): boolean {
  const url = new URL(source.url);
  if (url.origin === EDITORIAL_ORIGIN) return !url.search && isEditorialRelatedPath(url.pathname);
  return url.origin === "https://github.com"
    && (url.pathname === "/offflinerpsy/base2026" || url.pathname.startsWith("/offflinerpsy/base2026/"));
}

function evidence(value: unknown, sourceIds: Set<string>, citedSources: Set<string>): EditorialEvidence {
  const input = record(value, ["user_task", "dependencies"], [], "payload.evidence");
  const dependencies = array(input.dependencies, "payload.evidence.dependencies", 1, EDITORIAL_EVIDENCE_LIMITS.dependencies)
    .map((value, index): EditorialEvidenceDependency => {
      const field = `payload.evidence.dependencies[${index}]`;
      const item = record(value, ["citation_id", "document_id", "source_id", "document_sha256", "quote", "relation"], [], field);
      const citationId = id(item.citation_id, `${field}.citation_id`);
      if (!sourceIds.has(citationId) || !citedSources.has(citationId)) reject("EDITORIAL_EVIDENCE_CITATION_UNRESOLVED", `${field}.citation_id`);
      const documentId = boundedString(item.document_id, `${field}.document_id`, EDITORIAL_EVIDENCE_LIMITS.document_id);
      if (!isPublicEvidenceDocumentId(documentId)) reject("EDITORIAL_EVIDENCE_DOCUMENT_ID_INVALID", `${field}.document_id`);
      const sourceId = boundedString(item.source_id, `${field}.source_id`, EDITORIAL_EVIDENCE_LIMITS.source_id);
      if (!isPublicEvidenceSourceId(sourceId)) reject("EDITORIAL_EVIDENCE_SOURCE_ID_INVALID", `${field}.source_id`);
      // Numeric platform IDs are not phone numbers; all other existing
      // privacy/markup checks still apply to these dedicated ID syntaxes.
      assertPublicText(documentId, `${field}.document_id`, false);
      assertPublicText(sourceId, `${field}.source_id`, false);
      if (item.relation !== "direct" && item.relation !== "prerequisite") reject("EDITORIAL_EVIDENCE_RELATION_INVALID", `${field}.relation`);
      return {
        citation_id: citationId, document_id: documentId, source_id: sourceId,
        document_sha256: hash(item.document_sha256, `${field}.document_sha256`),
        quote: publicText(item.quote, `${field}.quote`, EDITORIAL_EVIDENCE_LIMITS.quote),
        relation: item.relation,
      };
    });
  unique(dependencies.map((item) => item.document_id), "payload.evidence.dependencies");
  if (!dependencies.some((item) => item.relation === "direct")) reject("EDITORIAL_EVIDENCE_DIRECT_REQUIRED", "payload.evidence.dependencies");
  return { user_task: publicText(input.user_task, "payload.evidence.user_task", EDITORIAL_EVIDENCE_LIMITS.user_task), dependencies };
}

/** Returns a detached, normalized public DTO; it never modifies its input. */
export function parseEditorialPayload(value: unknown, now: string): EditorialPayload {
  const nowMs = Date.parse(timestamp(now, "now"));
  const input = record(value, [
    "schema_version", "kind", "slug", "revision", "title", "description", "lede", "category", "tags",
    "published_at", "updated_at", "author", "ai_assistance_disclosure", "sources", "sections", "related_paths",
  ], ["hero", "first_party_context", "evidence"], "payload");
  if (input.schema_version !== EDITORIAL_SCHEMA) reject("EDITORIAL_SCHEMA_INVALID", "payload.schema_version");
  if (input.kind !== "source_based_article" && input.kind !== "engineering_note" && input.kind !== "evidence_guide") reject("EDITORIAL_KIND_INVALID", "payload.kind");
  if (input.kind === "evidence_guide" && !Object.hasOwn(input, "evidence")) reject("EDITORIAL_EVIDENCE_REQUIRED", "payload.evidence");
  if (input.kind !== "evidence_guide" && Object.hasOwn(input, "evidence")) reject("EDITORIAL_EVIDENCE_NOT_ALLOWED", "payload.evidence");
  const slug = id(input.slug, "payload.slug", EDITORIAL_LIMITS.slug);
  if (input.kind === "evidence_guide" && !EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(slug)) reject("EDITORIAL_EVIDENCE_GUIDE_SLUG_INVALID", "payload.slug");
  if (input.kind !== "evidence_guide" && EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(slug)) reject("EDITORIAL_SLUG_RESERVED", "payload.slug");
  const author = record(input.author, ["name"], [], "payload.author");
  if (author.name !== "Alex Yarosh") reject("EDITORIAL_AUTHOR_INVALID", "payload.author.name");
  const sources = array(input.sources, "payload.sources", input.kind === "source_based_article" ? 2 : 1, EDITORIAL_LIMITS.sources)
    .map((item, index) => source(item, index, nowMs));
  unique(sources.map((item) => item.id), "payload.sources");
  unique(sources.map((item) => item.url), "payload.sources");
  if (input.kind === "source_based_article" && new Set(sources.map(sourceMetadataKey)).size < 2) reject("EDITORIAL_SOURCE_METADATA_DUPLICATE", "payload.sources");
  let context: string | undefined;
  if (input.kind === "engineering_note") {
    context = publicText(input.first_party_context, "payload.first_party_context", 1_200);
    if (!sources.some(isFirstPartySource)) reject("EDITORIAL_FIRST_PARTY_SOURCE_REQUIRED", "payload.sources");
  } else if (Object.hasOwn(input, "first_party_context")) reject("EDITORIAL_UNSUPPORTED_FIELDS", "payload.first_party_context");
  let totalBlocks = 0;
  let sectionBytes = 0;
  const sourceIds = new Set(sources.map((entry) => entry.id));
  const sections = array(input.sections, "payload.sections", 1, EDITORIAL_LIMITS.sections).map((item, index) => {
    const parsed = section(item, index, sourceIds);
    totalBlocks += parsed.blocks.length;
    if (totalBlocks > EDITORIAL_LIMITS.total_blocks) reject("EDITORIAL_BLOCK_LIMIT", "payload.sections");
    sectionBytes += encoder.encode(canonicalJson(parsed)).byteLength;
    if (sectionBytes > EDITORIAL_LIMITS.payload_bytes) reject("EDITORIAL_PAYLOAD_TOO_LARGE", "payload");
    return parsed;
  });
  unique(sections.map((item) => item.id), "payload.sections");
  const citedSources = new Set(sections.flatMap((item) => item.blocks.flatMap((block) => block.type === "paragraph"
    ? block.citation_ids : block.items.flatMap((entry) => entry.citation_ids))));
  if (sources.some((item) => !citedSources.has(item.id))) reject("EDITORIAL_SOURCE_UNCITED", "payload.sources");
  const tags = array(input.tags, "payload.tags", 0, EDITORIAL_LIMITS.tags).map((item) => publicText(item, "payload.tags", EDITORIAL_LIMITS.tag));
  unique(tags.map(normalizedMetadata), "payload.tags");
  const paths = array(input.related_paths, "payload.related_paths", 0, EDITORIAL_LIMITS.related_paths).map((item) => relatedPath(item, "payload.related_paths"));
  unique(paths, "payload.related_paths");
  const publishedAt = timestamp(input.published_at, "payload.published_at", nowMs);
  const updatedAt = timestamp(input.updated_at, "payload.updated_at", nowMs);
  if (updatedAt < publishedAt) reject("EDITORIAL_TIMESTAMP_ORDER", "payload.updated_at");
  const payload: EditorialPayload = {
    schema_version: EDITORIAL_SCHEMA,
    kind: input.kind,
    slug,
    revision: revision(input.revision, "payload.revision"),
    title: publicText(input.title, "payload.title", EDITORIAL_LIMITS.title),
    description: publicText(input.description, "payload.description", EDITORIAL_LIMITS.description),
    lede: publicText(input.lede, "payload.lede", EDITORIAL_LIMITS.lede),
    category: publicText(input.category, "payload.category", EDITORIAL_LIMITS.category),
    tags,
    published_at: publishedAt,
    updated_at: updatedAt,
    author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: publicText(input.ai_assistance_disclosure, "payload.ai_assistance_disclosure", 800),
    ...(Object.hasOwn(input, "hero") ? { hero: hero(input.hero) } : {}),
    sources, sections, related_paths: paths,
    ...(context === undefined ? {} : { first_party_context: context }),
    ...(input.kind === "evidence_guide" ? { evidence: evidence(input.evidence, sourceIds, citedSources) } : {}),
  };
  if (encoder.encode(canonicalJson(payload)).byteLength > EDITORIAL_LIMITS.payload_bytes) reject("EDITORIAL_PAYLOAD_TOO_LARGE", "payload");
  return payload;
}

function canonicalJson(value: unknown): string {
  if (value === null || typeof value === "string" || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (typeof value === "object") {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(object[key])}`).join(",")}}`;
  }
  throw new EditorialValidationError("EDITORIAL_JSON_INVALID", "payload");
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function diagnostics(payload: EditorialPayload): EditorialDiagnostics {
  const citations = payload.sections.flatMap((item) => item.blocks.flatMap((block) => block.type === "paragraph"
    ? block.citation_ids : block.items.flatMap((entry) => entry.citation_ids)));
  return {
    source_count: payload.sources.length,
    distinct_source_urls: new Set(payload.sources.map((item) => item.url)).size,
    distinct_source_metadata: new Set(payload.sources.map(sourceMetadataKey)).size,
    known_creator_count: new Set(payload.sources.map(knownCreator).filter((item) => item !== null)).size,
    sources_without_known_creator: payload.sources.filter((item) => knownCreator(item) === null).length,
    cited_source_count: new Set(citations).size,
    section_count: payload.sections.length,
  };
}

function validationFailure(error: unknown): { ok: false; issues: EditorialIssue[] } {
  if (!(error instanceof EditorialValidationError)) throw error;
  return { ok: false, issues: [{ code: error.code, field: error.field }] };
}

async function validatedPayload(payload: EditorialPayload): Promise<ValidatedEditorialPayload> {
  const json = canonicalJson(payload);
  return { ok: true, payload, canonical_payload_json: json, payload_sha256: await sha256(json), diagnostics: diagnostics(payload) };
}

/** Use the returned canonical hash when preparing the separate review packet. */
export async function validateEditorialPayload(value: unknown, now: string): Promise<EditorialPayloadValidation> {
  try { return await validatedPayload(parseEditorialPayload(value, now)); } catch (error) { return validationFailure(error); }
}

function review(value: unknown, payload: EditorialPayload, now: string): EditorialReview {
  const input = record(value, ["reviewer", "outcome", "reviewed_at", "payload_sha256"], [], "review");
  if (input.reviewer !== "sol-max" || input.outcome !== "pass") reject("EDITORIAL_REVIEW_REQUIRED", "review");
  const reviewedAt = timestamp(input.reviewed_at, "review.reviewed_at", Date.parse(timestamp(now, "now")));
  if (reviewedAt < payload.published_at) reject("EDITORIAL_TIMESTAMP_ORDER", "review.reviewed_at");
  if (reviewedAt < payload.updated_at || payload.sources.some((item) => reviewedAt < item.checked_at)) {
    reject("EDITORIAL_REVIEW_STALE", "review.reviewed_at");
  }
  return { reviewer: "sol-max", outcome: "pass", reviewed_at: reviewedAt, payload_sha256: hash(input.payload_sha256, "review.payload_sha256") };
}

export async function validateEditorialPacket(value: unknown, now: string): Promise<EditorialPacketValidation> {
  try {
    const packet = record(value, ["payload", "review"], [], "packet");
    const payload = parseEditorialPayload(packet.payload, now);
    const reviewed = review(packet.review, payload, now);
    const result = await validatedPayload(payload);
    if (reviewed.payload_sha256 !== result.payload_sha256) reject("EDITORIAL_REVIEW_HASH_MISMATCH", "review.payload_sha256");
    return { ...result, review: reviewed };
  } catch (error) { return validationFailure(error); }
}

export function editorialArticlePath(slug: string, kind: EditorialPayload["kind"] = "source_based_article"): string {
  const key = id(slug, "slug", EDITORIAL_LIMITS.slug);
  if (kind === "evidence_guide") {
    if (!EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(key)) reject("EDITORIAL_EVIDENCE_GUIDE_SLUG_INVALID", "slug");
    return `/topics/${key}`;
  }
  if (kind !== "source_based_article" && kind !== "engineering_note") reject("EDITORIAL_KIND_INVALID", "kind");
  if (EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(key)) reject("EDITORIAL_SLUG_RESERVED", "slug");
  return `/blog/${key}/`;
}

/** The real D1 API subset used here; no simulated transaction interface. */
export type EditorialDatabase = Pick<D1Database, "prepare" | "batch">;

export interface EditorialOverwrite {
  expected_revision: number;
  expected_payload_sha256: string;
}

export interface EditorialPublishOptions {
  now: string;
  overwrite?: EditorialOverwrite;
}

export interface EditorialPublicationReceipt {
  schema_version: typeof EDITORIAL_RECEIPT_SCHEMA;
  slug: string;
  revision: number;
  payload_sha256: string;
  public_path: string;
  published_at: string;
  updated_at: string;
  reviewer: "sol-max";
  reviewed_at: string;
  recorded_at: string;
}

export interface StoredEditorialArticle {
  payload: EditorialPayload;
  payload_sha256: string;
  public_path: string;
  receipt: EditorialPublicationReceipt;
}

export type EditorialPublishResult = {
  ok: true;
  status: "published" | "already_published";
  receipt: EditorialPublicationReceipt;
  diagnostics: EditorialDiagnostics;
} | {
  ok: false;
  status: "conflict";
  code: "EDITORIAL_REVISION_CONFLICT";
  current_revision: number | null;
  current_payload_sha256: string | null;
} | { ok: false; status: "rejected"; issues: EditorialIssue[] };

interface StoredRow {
  slug: string;
  revision: number;
  payload_sha256: string;
  payload_json: string;
  published_at: string;
  updated_at: string;
  created_at: string;
  stored_at: string;
  receipt_hash: string | null;
  receipt_published_at: string | null;
  receipt_updated_at: string | null;
  reviewer: string | null;
  reviewed_at: string | null;
  recorded_at: string | null;
}

const READ_COLUMNS = `a.slug, a.revision, a.payload_sha256, a.payload_json,
  a.published_at, a.updated_at, a.created_at, a.stored_at,
  r.payload_sha256 AS receipt_hash, r.published_at AS receipt_published_at,
  r.updated_at AS receipt_updated_at, r.reviewer, r.reviewed_at, r.recorded_at`;
const READ_FROM = `FROM editorial_articles AS a
  LEFT JOIN editorial_publication_receipts AS r
    ON r.slug=a.slug AND r.revision=a.revision AND r.payload_sha256=a.payload_sha256`;
const BLOG_ONLY = "COALESCE(json_extract(a.payload_json, '$.kind'),'')<>'evidence_guide'";

async function storedArticle(row: StoredRow, now: string): Promise<StoredEditorialArticle> {
  try {
    if (typeof row.payload_json !== "string" || row.payload_json.length > EDITORIAL_LIMITS.payload_bytes) throw new Error("shape");
    const result = await validateEditorialPayload(JSON.parse(row.payload_json), now);
    if (!result.ok || result.canonical_payload_json !== row.payload_json
      || result.payload_sha256 !== row.payload_sha256 || result.payload_sha256 !== row.receipt_hash
      || result.payload.slug !== row.slug || result.payload.revision !== row.revision
      || result.payload.published_at !== row.published_at || result.payload.updated_at !== row.updated_at
      || row.receipt_published_at !== row.published_at || row.receipt_updated_at !== row.updated_at
      || row.reviewer !== "sol-max" || row.stored_at !== row.recorded_at) throw new Error("tuple");
    const reviewed = review({ reviewer: row.reviewer, outcome: "pass", reviewed_at: row.reviewed_at, payload_sha256: row.receipt_hash }, result.payload, now);
    const storedAt = timestamp(row.stored_at, "stored_at", Date.parse(timestamp(now, "now")));
    if (storedAt !== row.stored_at || timestamp(row.created_at, "created_at") > storedAt || storedAt < reviewed.reviewed_at) throw new Error("stored time");
    const path = editorialArticlePath(row.slug, result.payload.kind);
    return {
      payload: result.payload, payload_sha256: result.payload_sha256, public_path: path,
      receipt: {
        schema_version: EDITORIAL_RECEIPT_SCHEMA, slug: row.slug, revision: row.revision,
        payload_sha256: result.payload_sha256, public_path: path, published_at: row.published_at,
        updated_at: row.updated_at, reviewer: "sol-max", reviewed_at: reviewed.reviewed_at, recorded_at: storedAt,
      },
    };
  } catch { throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID"); }
}

async function evidenceSnapshot(db: EditorialDatabase, payload: EditorialPayload): Promise<EditorialEvidenceSnapshot> {
  if (!payload.evidence) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
  return resolveEditorialEvidence(db, payload.evidence, payload.sources,
    (value) => assertPublicText(value, "payload.evidence.dependencies"));
}

function evidenceRejection(error: unknown): Extract<EditorialPublishResult, { status: "rejected" }> {
  if (!(error instanceof EditorialEvidenceError) || error.code === "EDITORIAL_EVIDENCE_READ_FAILED") {
    throw new EditorialStoreError("EDITORIAL_EVIDENCE_READ_FAILED");
  }
  return { ok: false, status: "rejected", issues: [{ code: error.code, field: error.field }] };
}

type PublicationBatchRow = StoredRow | { evidence_matches: number };

/**
 * All decisions and the receipt readback are within one D1 batch transaction.
 * A failed CAS changes zero rows and cannot mint an applied receipt. An exact
 * current replay is a no-op. A receipt write failure rolls back its article.
 */
export async function publishEditorialArticle(db: EditorialDatabase, value: unknown, options: EditorialPublishOptions): Promise<EditorialPublishResult> {
  let now: string;
  let overwrite: EditorialOverwrite | undefined;
  try {
    const config = record(options, ["now"], ["overwrite"], "options");
    now = timestamp(config.now, "now");
    if (Object.hasOwn(config, "overwrite")) {
      const expected = record(config.overwrite, ["expected_revision", "expected_payload_sha256"], [], "options.overwrite");
      overwrite = { expected_revision: revision(expected.expected_revision, "options.overwrite.expected_revision"), expected_payload_sha256: hash(expected.expected_payload_sha256, "options.overwrite.expected_payload_sha256") };
    }
  } catch (error) { return { ...validationFailure(error), status: "rejected" }; }
  const checked = await validateEditorialPacket(value, now);
  if (!checked.ok) return { ...checked, status: "rejected" };
  if (checked.review.reviewed_at > now) return {
    ok: false, status: "rejected", issues: [{ code: "EDITORIAL_REVIEW_AFTER_PUBLICATION_CLOCK", field: "review.reviewed_at" }],
  };
  const payload = checked.payload;
  let snapshot: EditorialEvidenceSnapshot | undefined;
  if (payload.kind === "evidence_guide") {
    try { snapshot = await evidenceSnapshot(db, payload); }
    catch (error) { return evidenceRejection(error); }
  }
  let results: D1Result<PublicationBatchRow>[];
  try {
    const mutate = db.prepare(
      `INSERT INTO editorial_articles
       (slug, revision, payload_sha256, payload_json, published_at, updated_at, created_at, stored_at)
     SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?7
      WHERE (?8=0 OR EXISTS (SELECT 1 FROM editorial_articles WHERE slug=?1 AND revision=?9 AND payload_sha256=?10))
        ${snapshot ? `AND ${editorialEvidenceSnapshotGuardSql(11)}` : ""}
     ON CONFLICT(slug) DO UPDATE SET
       revision=excluded.revision, payload_sha256=excluded.payload_sha256, payload_json=excluded.payload_json,
       updated_at=excluded.updated_at, stored_at=excluded.stored_at
     WHERE ?8=1 AND editorial_articles.revision=?9 AND editorial_articles.payload_sha256=?10
       AND excluded.revision>editorial_articles.revision
       AND excluded.published_at=editorial_articles.published_at
       AND excluded.updated_at>=editorial_articles.updated_at
       AND excluded.stored_at>=editorial_articles.stored_at
       AND (json_extract(editorial_articles.payload_json, '$.kind')='evidence_guide')
         =(json_extract(excluded.payload_json, '$.kind')='evidence_guide')`,
    ).bind(payload.slug, payload.revision, checked.payload_sha256, checked.canonical_payload_json,
      payload.published_at, payload.updated_at, now, overwrite ? 1 : 0, overwrite?.expected_revision ?? 0, overwrite?.expected_payload_sha256 ?? "",
      ...(snapshot ? [snapshot.expected_json] : []));
    const receipt = db.prepare(
      `INSERT INTO editorial_publication_receipts
       (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
     SELECT slug, revision, payload_sha256, published_at, updated_at, 'sol-max', ?4, stored_at
       FROM editorial_articles
      WHERE slug=?1 AND revision=?2 AND payload_sha256=?3 AND changes()=1`,
    ).bind(payload.slug, payload.revision, checked.payload_sha256, checked.review.reviewed_at);
    const readback = db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM} WHERE a.slug=?1 LIMIT 1`).bind(payload.slug);
    const statements = [mutate, receipt, readback];
    // Keep receipt directly after mutation: changes() must describe that write.
    // This final check also fences an exact replay whose mutation is a no-op.
    if (snapshot) statements.push(db.prepare(`SELECT CASE WHEN ${editorialEvidenceSnapshotGuardSql(1)}
      THEN 1 ELSE 0 END AS evidence_matches`).bind(snapshot.expected_json));
    results = await db.batch<PublicationBatchRow>(statements);
  }
  catch { throw new EditorialStoreError("EDITORIAL_WRITE_FAILED"); }
  if (results.length !== (snapshot ? 4 : 3) || results.some((result) => !result.success)) throw new EditorialStoreError("EDITORIAL_WRITE_FAILED");
  const changed = results[0].meta.changes;
  const receiptChanged = results[1].meta.changes;
  const row = results[2].results[0];
  if ((changed !== 0 && changed !== 1) || receiptChanged !== changed || results[2].results.length > 1) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
  if (snapshot) {
    const guard = results[3].results[0];
    if (results[3].results.length !== 1 || !guard || !("evidence_matches" in guard)
      || (guard.evidence_matches !== 0 && guard.evidence_matches !== 1)) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
    if (guard.evidence_matches !== 1) {
      if (changed !== 0) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
      return evidenceRejection(new EditorialEvidenceError("EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED"));
    }
  }
  if (row && !("slug" in row)) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
  const stored = row ? await storedArticle(row, now) : null;
  const exact = stored?.payload.revision === payload.revision && stored.payload_sha256 === checked.payload_sha256;
  if (changed === 1 && !exact) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
  if (stored && exact) return { ok: true, status: changed === 1 ? "published" : "already_published", receipt: stored.receipt, diagnostics: checked.diagnostics };
  return { ok: false, status: "conflict", code: "EDITORIAL_REVISION_CONFLICT", current_revision: stored?.payload.revision ?? null, current_payload_sha256: stored?.payload_sha256 ?? null };
}

/**
 * Receipt/payload inspection for authorized repair CAS only. This deliberately
 * does not certify dependency health and must not back a public guide route.
 */
export async function inspectStoredEditorialArticle(db: EditorialDatabase, slug: string, now: string): Promise<StoredEditorialArticle | null> {
  const key = id(slug, "slug", EDITORIAL_LIMITS.slug);
  const checkedNow = timestamp(now, "now");
  let row: StoredRow | null;
  try { row = await db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM} WHERE a.slug=?1 LIMIT 1`).bind(key).first<StoredRow>(); }
  catch { throw new EditorialStoreError("EDITORIAL_READ_FAILED"); }
  return row ? storedArticle(row, checkedNow) : null;
}

export async function getEditorialArticle(db: EditorialDatabase, slug: string, now: string): Promise<StoredEditorialArticle | null> {
  const stored = await inspectStoredEditorialArticle(db, slug, now);
  if (!stored || stored.payload.kind !== "evidence_guide") return stored;
  let snapshot: EditorialEvidenceSnapshot;
  try { snapshot = await evidenceSnapshot(db, stored.payload); }
  catch (error) {
    throw new EditorialStoreError(error instanceof EditorialEvidenceError ? error.code : "EDITORIAL_EVIDENCE_READ_FAILED");
  }
  // Hashing is asynchronous. Recheck both the article identity and all source
  // snapshots together, so an intervening edit/withdrawal cannot be served.
  let current: StoredRow | null;
  try {
    current = await db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM}
      WHERE a.slug=?1 AND a.revision=?2 AND a.payload_sha256=?3
        AND ${editorialEvidenceSnapshotGuardSql(4)} LIMIT 1`)
      .bind(stored.payload.slug, stored.payload.revision, stored.payload_sha256, snapshot.expected_json).first<StoredRow>();
  } catch { throw new EditorialStoreError("EDITORIAL_EVIDENCE_READ_FAILED"); }
  if (!current) throw new EditorialStoreError("EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED");
  return storedArticle(current, timestamp(now, "now"));
}

export interface EditorialListCursor { published_at: string; slug: string }
export interface EditorialListOptions { now: string; limit?: number; cursor?: EditorialListCursor }
export interface EditorialArticlePage { articles: StoredEditorialArticle[]; next_cursor: EditorialListCursor | null }

/** Stable keyset pagination; original publication time cannot change on edits. */
export async function listEditorialArticles(db: EditorialDatabase, options: EditorialListOptions): Promise<EditorialArticlePage> {
  const config = record(options, ["now"], ["limit", "cursor"], "options");
  const now = timestamp(config.now, "now");
  const limit = config.limit === undefined ? 20 : revision(config.limit, "options.limit");
  if (limit > EDITORIAL_LIMITS.list_page) reject("EDITORIAL_LIST_LIMIT", "options.limit");
  let cursor: EditorialListCursor | undefined;
  if (Object.hasOwn(config, "cursor")) {
    const input = record(config.cursor, ["published_at", "slug"], [], "options.cursor");
    cursor = { published_at: timestamp(input.published_at, "options.cursor.published_at"), slug: id(input.slug, "options.cursor.slug", EDITORIAL_LIMITS.slug) };
  }
  const statement = cursor
    ? db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM}
        WHERE ${BLOG_ONLY} AND (a.published_at<?1 OR (a.published_at=?1 AND a.slug>?2))
        ORDER BY a.published_at DESC, a.slug ASC LIMIT ?3`).bind(cursor.published_at, cursor.slug, limit + 1)
    : db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM} WHERE ${BLOG_ONLY} ORDER BY a.published_at DESC, a.slug ASC LIMIT ?1`).bind(limit + 1);
  let rows: StoredRow[];
  try { rows = (await statement.all<StoredRow>()).results; }
  catch { throw new EditorialStoreError("EDITORIAL_READ_FAILED"); }
  const articles = await Promise.all(rows.slice(0, limit).map((row) => storedArticle(row, now)));
  const last = articles.at(-1);
  return { articles, next_cursor: rows.length > limit && last ? { published_at: last.payload.published_at, slug: last.payload.slug } : null };
}

export interface EditorialSitemapEntry { slug: string; updated_at: string }

/** Fixed 100-row sitemap pages still revalidate every public packet/receipt. */
export async function listEditorialSitemapEntries(db: EditorialDatabase, page: number, now: string): Promise<EditorialSitemapEntry[]> {
  if (!Number.isSafeInteger(page) || page < 1 || page > 50_000) reject("EDITORIAL_SITEMAP_PAGE_INVALID", "page");
  const checkedNow = timestamp(now, "now");
  let rows: StoredRow[];
  try {
    const result = await db.prepare(`SELECT ${READ_COLUMNS} ${READ_FROM}
      WHERE ${BLOG_ONLY} ORDER BY a.published_at DESC, a.slug ASC LIMIT ${EDITORIAL_SITEMAP_PAGE_SIZE} OFFSET ?1`)
      .bind((page - 1) * EDITORIAL_SITEMAP_PAGE_SIZE).all<StoredRow>();
    if (!result.success) throw new Error("read");
    rows = result.results;
  } catch { throw new EditorialStoreError("EDITORIAL_READ_FAILED"); }
  if (!Array.isArray(rows) || rows.length > EDITORIAL_SITEMAP_PAGE_SIZE) throw new EditorialStoreError("EDITORIAL_PERSISTED_STATE_INVALID");
  const entries: EditorialSitemapEntry[] = [];
  // Do not retain 100 parsed article bodies, or validate them all concurrently.
  for (const row of rows) {
    const stored = await storedArticle(row, checkedNow);
    entries.push({ slug: stored.payload.slug, updated_at: stored.payload.updated_at });
  }
  return entries;
}
