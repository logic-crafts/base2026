/**
 * Public half of the owner-authorized private -> public projection RPC.
 *
 * The request is deliberately a narrow, already-admitted packet. This Worker
 * validates the packet again and writes one D1 batch. Private packet fields
 * such as public_source_text and source_questions are not part of the DTO.
 */

export const PUBLIC_PROJECTION_SCHEMA = "base2026.public-projection.v1" as const;
export const PUBLIC_PROJECTION_ROLLBACK_SCHEMA = "base2026.public-projection-rollback.v1" as const;
export const PUBLIC_PROJECTION_RECEIPT_SCHEMA = "base2026.public-projection-receipt.v1" as const;
export const PUBLIC_SOURCE_PRESENCE_SCHEMA = "base2026.public-source-presence.v1" as const;
export const PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA = "base2026.public-source-presence-receipt.v1" as const;
export const PUBLIC_PROJECTION_VERIFY_SCHEMA = "base2026.public-projection-verify.v1" as const;

const MAX_PROJECTION_CARDS = 3;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;
const ID_PATTERN = /^[a-f0-9]{40}$/;
const TIKTOK_ID_PATTERN = /^[0-9]{10,30}$/;
const TIKTOK_HANDLE_PATTERN = /^[A-Za-z0-9._-]{2,256}$/;
const EMAIL_PATTERN = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
const PHONE_PATTERN = /(?<!\d)(?:\+?\d{1,3}[\s().-])?(?:\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10})(?!\d)/u;
const SECRET_PATTERN = /\b(?:api|access|auth|authentication|client|app|webhook)?[_\s-]*(?:key|token|secret|password|passwd|credential|cookie|session[_\s-]*id)\s*[:=]\s*\S+/iu;
const SECRET_PHRASE_PATTERN = /\b(?:api|access|auth|authentication|client|app|webhook)[_\s-]*(?:key|token|secret|password|passwd|credential)\s*(?:is\s+|[:=]\s*)\S+/iu;
const TOKEN_FORMAT_PATTERN = /\b(?:sk_(?:live|test)_[A-Z0-9]{8,}|(?:ghp|github_pat|xox[baprs])[-_][A-Z0-9-]{8,}|AIza[A-Z0-9_-]{20,})\b/i;
const BEARER_PATTERN = /\bbearer\s+[A-Z0-9._~+/=-]{8,}\b/i;
const PRIVATE_MARKER_PATTERN = /\b(?:private[_\s-]*(?:only|notes?|context|source|text)|not[_\s-]*for[_\s-]*public[_\s-]*export|raw[_\s-]*(?:transcript|caption|captions|asr)|transcript(?:[_\s-]*text)?|captions?|asr)\b/iu;
const LOCAL_PATH_PATTERN = /(?:^|[\s(])(?:file:\/\/|~\/|\/(?:Users|home|tmp|var|private|Volumes)\/|[A-Za-z]:\\)/u;
const encoder = new TextEncoder();

export interface PublicProjectionSource {
  source_id: string;
  canonical_url: string;
  creator_handle: string;
  published_at: string | null;
  title_or_description: string;
  duration_seconds: number | null;
}

export interface PublicProjectionCard {
  ordinal: number;
  claim_text: string;
  suggested_action: string;
  topic_label: string;
  evidence_excerpt: string;
  evidence_start_seconds: number;
  evidence_end_seconds: number;
}

export interface PublicProjectionRequest {
  schema_version: typeof PUBLIC_PROJECTION_SCHEMA;
  projection_id: string;
  source: PublicProjectionSource;
  manifest_sha256: string;
  content_sha256: string;
  private_import_receipt_sha256: string;
  cards: PublicProjectionCard[];
}

export type PublicProjectionInput = PublicProjectionRequest;

export interface PublicProjectionRollbackRequest {
  schema_version: typeof PUBLIC_PROJECTION_ROLLBACK_SCHEMA;
  projection_id: string;
  source_id: string;
  manifest_sha256: string;
  content_sha256: string;
}

/** Exact nine-key receipt consumed by the private projection controller. */
export interface PublicProjectionReceipt {
  schema_version: typeof PUBLIC_PROJECTION_RECEIPT_SCHEMA;
  projection_id: string;
  source_id: string;
  manifest_sha256: string;
  content_sha256: string;
  status: "applied" | "rolled_back";
  card_count: number;
  row_count: number;
  receipt_sha256: string;
}

export type PublicSourcePresenceState = "absent" | "legacy_public" | "projected";

export interface PublicSourcePresenceRequest {
  schema_version: typeof PUBLIC_SOURCE_PRESENCE_SCHEMA;
  source_id: string;
}

export interface PublicSourcePresenceReceipt {
  schema_version: typeof PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA;
  source_id: string;
  state: PublicSourcePresenceState;
  document_count: number;
  full_transcript_public_count: number;
  projection_id: string | null;
  manifest_sha256: string | null;
}

export interface PublicProjectionVerifyRequest {
  schema_version: typeof PUBLIC_PROJECTION_VERIFY_SCHEMA;
  projection_id: string;
  source_id: string;
  manifest_sha256: string;
  content_sha256: string;
}

export class PublicProjectionError extends Error {
  constructor(
    readonly status: 400 | 409 | 500,
    readonly code: string,
  ) {
    // Do not include source text, URLs, IDs, or other caller-controlled data
    // in an RPC error message.
    super(code);
    this.name = "PublicProjectionError";
  }
}

interface PublicProjectionRow {
  projection_id: string;
  source_id: string;
  manifest_sha256: string;
  content_sha256: string;
  private_import_receipt_sha256: string;
  card_count: number;
  status: "applied" | "rolled_back";
  receipt_sha256: string;
}

interface PublicDocumentRow {
  id: string;
  item_id: string;
  source_id: string;
  chunk_id: string;
  chunk_index: number;
  body: string;
  captured_at: string;
  creator_display_name: string;
  creator_handle: string;
  creator_id: string;
  creator_url: string;
  full_transcript_public: 0;
  handle: string;
  platform: "tiktok";
  post_id: string;
  public_policy: "search_passage";
  public_surface: "main_search";
  published_at: string;
  published_date: string;
  source_type: "tiktok_video";
  source_url: string;
  title: string;
  title_source: "public_projection";
  title_status: "ok";
  video_id: string;
  year: string;
  avatar_url: string;
  topics_json: string;
  topic_labels_json: string;
  admission_state: "normal_public_card";
  projection_id: string;
}

interface PublicSourceDocumentAggregate {
  document_count: number;
  full_transcript_public_count: number;
  legacy_count: number;
  projected_count: number;
}

interface PublicProjectionDocumentAggregate extends PublicSourceDocumentAggregate {
  source_count: number;
  video_count: number;
  source_mismatch_count: number;
  projection_mismatch_count: number;
  video_mismatch_count: number;
}

interface PublicProjectionChildAggregate {
  count: number;
  identity_mismatch_count: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, keys: readonly string[], code: string): void {
  const actual = Object.keys(value);
  if (actual.length !== keys.length || actual.some((key) => !keys.includes(key))) {
    throw new PublicProjectionError(400, code);
  }
}

function stringValue(value: unknown, code: string, min: number, max: number, pattern?: RegExp): string {
  if (typeof value !== "string") throw new PublicProjectionError(400, code);
  const result = value.trim();
  if (result.length < min || result.length > max || (pattern && !pattern.test(result))) {
    throw new PublicProjectionError(400, code);
  }
  return result;
}

function hashValue(value: unknown, code: string): string {
  return stringValue(value, code, 64, 64, SHA256_PATTERN).toLowerCase();
}

function idValue(value: unknown, code: string): string {
  return stringValue(value, code, 40, 40, ID_PATTERN).toLowerCase();
}

function countValue(value: unknown, code: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    throw new PublicProjectionError(400, code);
  }
  return value;
}

function finiteNumber(value: unknown, code: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > Number.MAX_SAFE_INTEGER) {
    throw new PublicProjectionError(400, code);
  }
  return value;
}

function nullableString(value: unknown, code: string, max: number): string | null {
  if (value === null) return null;
  return stringValue(value, code, 1, max);
}

function nullableNumber(value: unknown, code: string): number | null {
  if (value === null) return null;
  return finiteNumber(value, code);
}

interface TikTokSourceIdParts {
  sourceId: string;
  handle: string;
  numericId: string;
}

function tiktokSourceIdParts(value: unknown, code: string): TikTokSourceIdParts {
  const sourceId = stringValue(value, code, 10, 300);
  const match = sourceId.match(/^tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})$/u);
  if (!match || !TIKTOK_HANDLE_PATTERN.test(match[1]) || !TIKTOK_ID_PATTERN.test(match[2])) {
    throw new PublicProjectionError(400, code);
  }
  return { sourceId, handle: match[1], numericId: match[2] };
}

function sourceIdValue(value: unknown, code: string): string {
  return tiktokSourceIdParts(value, code).sourceId;
}

/**
 * Fail closed on bounded classes of private/contact material. This is not a
 * semantic redaction pass: it only blocks recognizable data-bearing markers,
 * leaving ordinary words such as "private markets" or "token economy" alone.
 */
function assertPublicText(value: string): void {
  if (
    EMAIL_PATTERN.test(value)
    || PHONE_PATTERN.test(value)
    || SECRET_PATTERN.test(value)
    || SECRET_PHRASE_PATTERN.test(value)
    || TOKEN_FORMAT_PATTERN.test(value)
    || BEARER_PATTERN.test(value)
    || PRIVATE_MARKER_PATTERN.test(value)
    || LOCAL_PATH_PATTERN.test(value)
  ) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_PRIVACY_REJECTED");
  }
}

function numericTikTokIdFromSourceId(sourceId: string, handle: string): string {
  const handleWithoutAt = handle.replace(/^@/u, "");
  const parsed = tiktokSourceIdParts(sourceId, "PUBLIC_PROJECTION_SOURCE_ID_INVALID");
  if (parsed.handle !== handleWithoutAt) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_SOURCE_ID_INVALID");
  }
  return parsed.numericId;
}

function validateCanonicalUrl(value: unknown, handle: string, numericId: string): string {
  const canonicalUrl = stringValue(value, "PUBLIC_PROJECTION_CANONICAL_URL_INVALID", 12, 2_048);
  let parsed: URL;
  try {
    parsed = new URL(canonicalUrl);
  } catch {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CANONICAL_URL_INVALID");
  }
  const expectedPath = `/@${handle.replace(/^@/u, "")}/video/${numericId}`;
  if (
    parsed.protocol !== "https:"
    || !["www.tiktok.com", "tiktok.com"].includes(parsed.hostname)
    || parsed.port
    || parsed.username
    || parsed.password
    || parsed.search
    || parsed.hash
    || parsed.pathname !== expectedPath
    || parsed.toString() !== canonicalUrl
  ) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CANONICAL_URL_INVALID");
  }
  return canonicalUrl;
}

function validateSource(value: unknown): PublicProjectionSource {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_SOURCE_INVALID");
  exactKeys(
    value,
    ["source_id", "canonical_url", "creator_handle", "published_at", "title_or_description", "duration_seconds"],
    "PUBLIC_PROJECTION_SOURCE_FIELDS_INVALID",
  );
  const creatorHandle = stringValue(value.creator_handle, "PUBLIC_PROJECTION_CREATOR_INVALID", 2, 256);
  assertPublicText(creatorHandle);
  const handleWithoutAt = creatorHandle.replace(/^@/u, "");
  if (!TIKTOK_HANDLE_PATTERN.test(handleWithoutAt)) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CREATOR_INVALID");
  }
  const sourceId = stringValue(value.source_id, "PUBLIC_PROJECTION_SOURCE_ID_INVALID", 10, 300);
  const numericId = numericTikTokIdFromSourceId(sourceId, creatorHandle);
  if (!TIKTOK_ID_PATTERN.test(numericId)) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_SOURCE_ID_INVALID");
  }
  const title = stringValue(value.title_or_description, "PUBLIC_PROJECTION_TITLE_INVALID", 1, 1_200);
  assertPublicText(title);
  return {
    source_id: sourceId,
    canonical_url: validateCanonicalUrl(value.canonical_url, creatorHandle, numericId),
    creator_handle: creatorHandle,
    published_at: nullableString(value.published_at, "PUBLIC_PROJECTION_PUBLISHED_AT_INVALID", 32),
    title_or_description: title,
    duration_seconds: nullableNumber(value.duration_seconds, "PUBLIC_PROJECTION_DURATION_INVALID"),
  };
}

function validateCard(value: unknown, expectedOrdinal: number): PublicProjectionCard {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CARD_INVALID");
  exactKeys(
    value,
    [
      "ordinal",
      "claim_text",
      "suggested_action",
      "topic_label",
      "evidence_excerpt",
      "evidence_start_seconds",
      "evidence_end_seconds",
    ],
    "PUBLIC_PROJECTION_CARD_FIELDS_INVALID",
  );
  if (value.ordinal !== expectedOrdinal) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CARD_ORDINAL_INVALID");
  }
  const start = finiteNumber(value.evidence_start_seconds, "PUBLIC_PROJECTION_EVIDENCE_START_INVALID");
  const end = finiteNumber(value.evidence_end_seconds, "PUBLIC_PROJECTION_EVIDENCE_END_INVALID");
  if (end < start) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_EVIDENCE_RANGE_INVALID");
  const claim = stringValue(value.claim_text, "PUBLIC_PROJECTION_CLAIM_INVALID", 20, 360);
  const action = stringValue(value.suggested_action, "PUBLIC_PROJECTION_ACTION_INVALID", 20, 360);
  const topic = stringValue(value.topic_label, "PUBLIC_PROJECTION_TOPIC_INVALID", 2, 120);
  const excerpt = stringValue(value.evidence_excerpt, "PUBLIC_PROJECTION_EVIDENCE_INVALID", 20, 520);
  assertPublicText(claim);
  assertPublicText(action);
  assertPublicText(topic);
  assertPublicText(excerpt);
  return {
    ordinal: expectedOrdinal,
    claim_text: claim,
    suggested_action: action,
    topic_label: topic,
    evidence_excerpt: excerpt,
    evidence_start_seconds: start,
    evidence_end_seconds: end,
  };
}

export function parsePublicProjection(value: unknown): PublicProjectionRequest {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_INVALID");
  exactKeys(
    value,
    ["schema_version", "projection_id", "source", "manifest_sha256", "content_sha256", "private_import_receipt_sha256", "cards"],
    "PUBLIC_PROJECTION_FIELDS_INVALID",
  );
  if (value.schema_version !== PUBLIC_PROJECTION_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_SCHEMA_INVALID");
  }
  if (!Array.isArray(value.cards) || value.cards.length < 1 || value.cards.length > MAX_PROJECTION_CARDS) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_CARD_COUNT_INVALID");
  }
  return {
    schema_version: PUBLIC_PROJECTION_SCHEMA,
    projection_id: idValue(value.projection_id, "PUBLIC_PROJECTION_ID_INVALID"),
    source: validateSource(value.source),
    manifest_sha256: hashValue(value.manifest_sha256, "PUBLIC_PROJECTION_MANIFEST_INVALID"),
    content_sha256: hashValue(value.content_sha256, "PUBLIC_PROJECTION_CONTENT_INVALID"),
    private_import_receipt_sha256: hashValue(value.private_import_receipt_sha256, "PUBLIC_PROJECTION_PRIVATE_IMPORT_RECEIPT_INVALID"),
    cards: value.cards.map((card, ordinal) => validateCard(card, ordinal)),
  };
}

export const parsePublicProjectionRequest = parsePublicProjection;

export function parsePublicSourcePresenceRequest(value: unknown): PublicSourcePresenceRequest {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_INVALID");
  exactKeys(value, ["schema_version", "source_id"], "PUBLIC_SOURCE_PRESENCE_FIELDS_INVALID");
  if (value.schema_version !== PUBLIC_SOURCE_PRESENCE_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_SCHEMA_INVALID");
  }
  return {
    schema_version: PUBLIC_SOURCE_PRESENCE_SCHEMA,
    source_id: sourceIdValue(value.source_id, "PUBLIC_SOURCE_PRESENCE_SOURCE_ID_INVALID"),
  };
}

export const parsePublicSourcePresence = parsePublicSourcePresenceRequest;

export function parsePublicSourcePresenceReceipt(value: unknown): PublicSourcePresenceReceipt {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_RECEIPT_INVALID");
  exactKeys(
    value,
    [
      "schema_version",
      "source_id",
      "state",
      "document_count",
      "full_transcript_public_count",
      "projection_id",
      "manifest_sha256",
    ],
    "PUBLIC_SOURCE_PRESENCE_RECEIPT_FIELDS_INVALID",
  );
  if (value.schema_version !== PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA_INVALID");
  }
  if (value.state !== "absent" && value.state !== "legacy_public" && value.state !== "projected") {
    throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_STATE_INVALID");
  }
  const projectionId = value.projection_id === null
    ? null
    : idValue(value.projection_id, "PUBLIC_SOURCE_PRESENCE_PROJECTION_ID_INVALID");
  const manifestSha256 = value.manifest_sha256 === null
    ? null
    : hashValue(value.manifest_sha256, "PUBLIC_SOURCE_PRESENCE_MANIFEST_INVALID");
  if (value.state === "projected" && (projectionId === null || manifestSha256 === null)) {
    throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_PROJECTED_FIELDS_INVALID");
  }
  if (value.state !== "projected" && (projectionId !== null || manifestSha256 !== null)) {
    throw new PublicProjectionError(400, "PUBLIC_SOURCE_PRESENCE_NON_PROJECTED_FIELDS_INVALID");
  }
  return {
    schema_version: PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA,
    source_id: sourceIdValue(value.source_id, "PUBLIC_SOURCE_PRESENCE_SOURCE_ID_INVALID"),
    state: value.state,
    document_count: countValue(value.document_count, "PUBLIC_SOURCE_PRESENCE_DOCUMENT_COUNT_INVALID"),
    full_transcript_public_count: countValue(
      value.full_transcript_public_count,
      "PUBLIC_SOURCE_PRESENCE_TRANSCRIPT_COUNT_INVALID",
    ),
    projection_id: projectionId,
    manifest_sha256: manifestSha256,
  };
}

export function parsePublicProjectionVerifyRequest(value: unknown): PublicProjectionVerifyRequest {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_VERIFY_INVALID");
  exactKeys(
    value,
    ["schema_version", "projection_id", "source_id", "manifest_sha256", "content_sha256"],
    "PUBLIC_PROJECTION_VERIFY_FIELDS_INVALID",
  );
  if (value.schema_version !== PUBLIC_PROJECTION_VERIFY_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_VERIFY_SCHEMA_INVALID");
  }
  return {
    schema_version: PUBLIC_PROJECTION_VERIFY_SCHEMA,
    projection_id: idValue(value.projection_id, "PUBLIC_PROJECTION_VERIFY_PROJECTION_ID_INVALID"),
    source_id: sourceIdValue(value.source_id, "PUBLIC_PROJECTION_VERIFY_SOURCE_ID_INVALID"),
    manifest_sha256: hashValue(value.manifest_sha256, "PUBLIC_PROJECTION_VERIFY_MANIFEST_INVALID"),
    content_sha256: hashValue(value.content_sha256, "PUBLIC_PROJECTION_VERIFY_CONTENT_INVALID"),
  };
}

export const parsePublicProjectionVerify = parsePublicProjectionVerifyRequest;

export function parsePublicProjectionReceipt(value: unknown): PublicProjectionReceipt {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_RECEIPT_INVALID");
  exactKeys(
    value,
    [
      "schema_version",
      "projection_id",
      "source_id",
      "manifest_sha256",
      "content_sha256",
      "status",
      "card_count",
      "row_count",
      "receipt_sha256",
    ],
    "PUBLIC_PROJECTION_RECEIPT_FIELDS_INVALID",
  );
  if (value.schema_version !== PUBLIC_PROJECTION_RECEIPT_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_RECEIPT_SCHEMA_INVALID");
  }
  if (value.status !== "applied" && value.status !== "rolled_back") {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_RECEIPT_STATUS_INVALID");
  }
  const cardCount = countValue(value.card_count, "PUBLIC_PROJECTION_RECEIPT_CARD_COUNT_INVALID");
  if (cardCount > MAX_PROJECTION_CARDS || (value.status === "applied" && cardCount < 1)) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_RECEIPT_CARD_COUNT_INVALID");
  }
  return {
    schema_version: PUBLIC_PROJECTION_RECEIPT_SCHEMA,
    projection_id: idValue(value.projection_id, "PUBLIC_PROJECTION_RECEIPT_PROJECTION_ID_INVALID"),
    source_id: sourceIdValue(value.source_id, "PUBLIC_PROJECTION_RECEIPT_SOURCE_ID_INVALID"),
    manifest_sha256: hashValue(value.manifest_sha256, "PUBLIC_PROJECTION_RECEIPT_MANIFEST_INVALID"),
    content_sha256: hashValue(value.content_sha256, "PUBLIC_PROJECTION_RECEIPT_CONTENT_INVALID"),
    status: value.status,
    card_count: cardCount,
    row_count: countValue(value.row_count, "PUBLIC_PROJECTION_RECEIPT_ROW_COUNT_INVALID"),
    receipt_sha256: hashValue(value.receipt_sha256, "PUBLIC_PROJECTION_RECEIPT_HASH_INVALID"),
  };
}

export function parsePublicProjectionRollback(value: unknown): PublicProjectionRollbackRequest {
  if (!isRecord(value)) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_ROLLBACK_INVALID");
  exactKeys(
    value,
    ["schema_version", "projection_id", "source_id", "manifest_sha256", "content_sha256"],
    "PUBLIC_PROJECTION_ROLLBACK_FIELDS_INVALID",
  );
  if (value.schema_version !== PUBLIC_PROJECTION_ROLLBACK_SCHEMA) {
    throw new PublicProjectionError(400, "PUBLIC_PROJECTION_ROLLBACK_SCHEMA_INVALID");
  }
  return {
    schema_version: PUBLIC_PROJECTION_ROLLBACK_SCHEMA,
    projection_id: idValue(value.projection_id, "PUBLIC_PROJECTION_ID_INVALID"),
    source_id: stringValue(value.source_id, "PUBLIC_PROJECTION_SOURCE_ID_INVALID", 10, 300),
    manifest_sha256: hashValue(value.manifest_sha256, "PUBLIC_PROJECTION_MANIFEST_INVALID"),
    content_sha256: hashValue(value.content_sha256, "PUBLIC_PROJECTION_CONTENT_INVALID"),
  };
}

function topicSlug(value: string): string {
  const slug = value
    .normalize("NFKC")
    .toLocaleLowerCase("en-US")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/gu, "")
    .slice(0, 160);
  if (!slug) throw new PublicProjectionError(400, "PUBLIC_PROJECTION_TOPIC_INVALID");
  return slug;
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

/** Deterministic 40-character IDs used by the private control-plane style. */
export async function deterministicProjectionId(sourceId: string, manifestSha256: string): Promise<string> {
  return (await sha256Hex(["public-projection-receipt", sourceId, manifestSha256].join("\u001f"))).slice(0, 40);
}

export async function deterministicCardId(projectionId: string, ordinal: number): Promise<string> {
  return (await sha256Hex(["public-projection-card", projectionId, String(ordinal)].join("\u001f"))).slice(0, 40);
}

export async function deterministicSearchId(cardId: string): Promise<string> {
  return (await sha256Hex(["public-projection-search-document", cardId].join("\u001f"))).slice(0, 40);
}

export const publicProjectionId = deterministicProjectionId;
export const publicCardId = deterministicCardId;
export const publicSearchId = deterministicSearchId;

function sourceNumericId(source: PublicProjectionSource): string {
  return source.source_id.slice(source.source_id.lastIndexOf(":") + 1);
}

function profileUrl(source: PublicProjectionSource): string {
  return `https://www.tiktok.com/@${source.creator_handle.replace(/^@/u, "")}`;
}

function buildDocument(
  request: PublicProjectionRequest,
  card: PublicProjectionCard,
  cardId: string,
  searchId: string,
): PublicDocumentRow {
  const source = request.source;
  const numericId = sourceNumericId(source);
  const publishedDate = source.published_at?.slice(0, 10) ?? "";
  return {
    id: searchId,
    item_id: `tiktok-video-${numericId}`,
    source_id: source.source_id,
    chunk_id: cardId,
    chunk_index: card.ordinal,
    body: card.evidence_excerpt,
    captured_at: publishedDate,
    creator_display_name: "",
    creator_handle: source.creator_handle,
    creator_id: `tiktok-${source.creator_handle.replace(/^@/u, "")}`,
    creator_url: profileUrl(source),
    full_transcript_public: 0,
    handle: source.creator_handle,
    platform: "tiktok",
    post_id: numericId,
    public_policy: "search_passage",
    public_surface: "main_search",
    published_at: publishedDate,
    published_date: publishedDate,
    source_type: "tiktok_video",
    source_url: source.canonical_url,
    title: card.claim_text,
    title_source: "public_projection",
    title_status: "ok",
    video_id: numericId,
    year: publishedDate.slice(0, 4),
    avatar_url: "",
    topics_json: JSON.stringify([topicSlug(card.topic_label)]),
    topic_labels_json: JSON.stringify([card.topic_label]),
    admission_state: "normal_public_card",
    projection_id: request.projection_id,
  };
}

function documentSql(db: D1Database, row: PublicDocumentRow): D1PreparedStatement {
  return db.prepare(
    `INSERT INTO search_documents
      (id, item_id, source_id, chunk_id, chunk_index, body, captured_at,
       creator_display_name, creator_handle, creator_id, creator_url,
       full_transcript_public, handle, platform, post_id, public_policy,
       public_surface, published_at, published_date, source_type, source_url,
       title, title_source, title_status, video_id, year, avatar_url,
       topics_json, topic_labels_json, admission_state, projection_id)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).bind(
    row.id,
    row.item_id,
    row.source_id,
    row.chunk_id,
    row.chunk_index,
    row.body,
    row.captured_at,
    row.creator_display_name,
    row.creator_handle,
    row.creator_id,
    row.creator_url,
    row.full_transcript_public,
    row.handle,
    row.platform,
    row.post_id,
    row.public_policy,
    row.public_surface,
    row.published_at,
    row.published_date,
    row.source_type,
    row.source_url,
    row.title,
    row.title_source,
    row.title_status,
    row.video_id,
    row.year,
    row.avatar_url,
    row.topics_json,
    row.topic_labels_json,
    row.admission_state,
    row.projection_id,
  );
}

function cardSql(db: D1Database, request: PublicProjectionRequest, card: PublicProjectionCard, cardId: string, searchId: string): D1PreparedStatement {
  return db.prepare(
    `INSERT INTO public_projection_cards
      (projection_id, source_id, ordinal, card_id, search_id, claim_text,
       suggested_action, topic_label, evidence_excerpt,
       evidence_start_seconds, evidence_end_seconds)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).bind(
    request.projection_id,
    request.source.source_id,
    card.ordinal,
    cardId,
    searchId,
    card.claim_text,
    card.suggested_action,
    card.topic_label,
    card.evidence_excerpt,
    card.evidence_start_seconds,
    card.evidence_end_seconds,
  );
}

function topicSql(db: D1Database, row: PublicDocumentRow, label: string): D1PreparedStatement {
  return db.prepare(
    `INSERT INTO search_topics (document_id, topic_id, topic_label) VALUES (?, ?, ?)`,
  ).bind(row.id, JSON.parse(row.topics_json)[0], label);
}

async function receiptSha256(
  request: Pick<PublicProjectionRequest, "projection_id" | "source" | "manifest_sha256" | "content_sha256" | "private_import_receipt_sha256">,
  status: "applied" | "rolled_back",
  rowCount: number,
): Promise<string> {
  return sha256Hex([
    "base2026.public-projection-receipt.v1",
    request.projection_id,
    request.source.source_id,
    request.manifest_sha256,
    request.content_sha256,
    request.private_import_receipt_sha256,
    status,
    String(rowCount),
  ].join("\u001f"));
}

function exactReceipt(
  request: Pick<PublicProjectionRequest, "projection_id" | "source" | "manifest_sha256" | "content_sha256">,
  status: "applied" | "rolled_back",
  cardCount: number,
  rowCount: number,
  receiptHash: string,
): PublicProjectionReceipt {
  return {
    schema_version: PUBLIC_PROJECTION_RECEIPT_SCHEMA,
    projection_id: request.projection_id,
    source_id: request.source.source_id,
    manifest_sha256: request.manifest_sha256,
    content_sha256: request.content_sha256,
    status,
    card_count: cardCount,
    row_count: rowCount,
    receipt_sha256: receiptHash,
  };
}

function opaquePresenceMismatch(): never {
  throw new PublicProjectionError(500, "PUBLIC_SOURCE_PRESENCE_MISMATCH");
}

function opaqueVerifyMismatch(): never {
  throw new PublicProjectionError(500, "PUBLIC_PROJECTION_VERIFY_MISMATCH");
}

function persistedProjectionRow(row: PublicProjectionRow, code: string): PublicProjectionRow {
  try {
    if (row.status !== "applied" && row.status !== "rolled_back") throw new Error("status");
    if (tiktokSourceIdParts(row.source_id, code).sourceId !== row.source_id) throw new Error("source");
    if (idValue(row.projection_id, code) !== row.projection_id) throw new Error("projection");
    if (hashValue(row.manifest_sha256, code) !== row.manifest_sha256) throw new Error("manifest");
    if (hashValue(row.content_sha256, code) !== row.content_sha256) throw new Error("content");
    if (hashValue(row.private_import_receipt_sha256, code) !== row.private_import_receipt_sha256) throw new Error("private receipt");
    if (countValue(row.card_count, code) < 1 || row.card_count > MAX_PROJECTION_CARDS) throw new Error("cards");
    if (hashValue(row.receipt_sha256, code) !== row.receipt_sha256) throw new Error("receipt");
  } catch {
    throw new PublicProjectionError(500, code);
  }
  return row;
}

async function readSourceDocumentAggregate(
  db: D1Database,
  sourceId: string,
): Promise<PublicSourceDocumentAggregate> {
  const row = await db.prepare(
    `SELECT COUNT(*) AS document_count,
            COALESCE(SUM(CASE WHEN full_transcript_public <> 0 THEN 1 ELSE 0 END), 0) AS full_transcript_public_count,
            COALESCE(SUM(CASE WHEN projection_id IS NULL OR projection_id='' THEN 1 ELSE 0 END), 0) AS legacy_count,
            COALESCE(SUM(CASE WHEN projection_id IS NOT NULL AND projection_id<>'' THEN 1 ELSE 0 END), 0) AS projected_count
       FROM search_documents
      WHERE source_id=?`,
  ).bind(sourceId).first<PublicSourceDocumentAggregate>();
  if (!row) return { document_count: 0, full_transcript_public_count: 0, legacy_count: 0, projected_count: 0 };
  try {
    return {
      document_count: countValue(row.document_count, "PUBLIC_SOURCE_PRESENCE_DATABASE_INVALID"),
      full_transcript_public_count: countValue(row.full_transcript_public_count, "PUBLIC_SOURCE_PRESENCE_DATABASE_INVALID"),
      legacy_count: countValue(row.legacy_count, "PUBLIC_SOURCE_PRESENCE_DATABASE_INVALID"),
      projected_count: countValue(row.projected_count, "PUBLIC_SOURCE_PRESENCE_DATABASE_INVALID"),
    };
  } catch {
    throw new PublicProjectionError(500, "PUBLIC_SOURCE_PRESENCE_DATABASE_INVALID");
  }
}

async function readProjectionDocumentAggregate(
  db: D1Database,
  sourceId: string,
  projectionId: string,
  numericId: string,
): Promise<PublicProjectionDocumentAggregate> {
  const row = await db.prepare(
    `SELECT COUNT(*) AS document_count,
            COUNT(DISTINCT source_id) AS source_count,
            COUNT(DISTINCT video_id) AS video_count,
            COALESCE(SUM(CASE WHEN full_transcript_public <> 0 THEN 1 ELSE 0 END), 0) AS full_transcript_public_count,
            COALESCE(SUM(CASE WHEN projection_id IS NULL OR projection_id='' THEN 1 ELSE 0 END), 0) AS legacy_count,
            COALESCE(SUM(CASE WHEN projection_id IS NOT NULL AND projection_id<>'' THEN 1 ELSE 0 END), 0) AS projected_count,
            COALESCE(SUM(CASE WHEN source_id IS NULL OR source_id<>? THEN 1 ELSE 0 END), 0) AS source_mismatch_count,
            COALESCE(SUM(CASE WHEN projection_id IS NULL OR projection_id<>? THEN 1 ELSE 0 END), 0) AS projection_mismatch_count,
            COALESCE(SUM(CASE WHEN video_id IS NULL OR video_id<>? THEN 1 ELSE 0 END), 0) AS video_mismatch_count
       FROM search_documents
      WHERE source_id=? OR projection_id=?`,
  ).bind(sourceId, projectionId, numericId, sourceId, projectionId).first<PublicProjectionDocumentAggregate>();
  if (!row) return {
    document_count: 0,
    source_count: 0,
    video_count: 0,
    full_transcript_public_count: 0,
    legacy_count: 0,
    projected_count: 0,
    source_mismatch_count: 0,
    projection_mismatch_count: 0,
    video_mismatch_count: 0,
  };
  try {
    return {
      document_count: countValue(row.document_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      source_count: countValue(row.source_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      video_count: countValue(row.video_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      full_transcript_public_count: countValue(row.full_transcript_public_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      legacy_count: countValue(row.legacy_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      projected_count: countValue(row.projected_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      source_mismatch_count: countValue(row.source_mismatch_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      projection_mismatch_count: countValue(row.projection_mismatch_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      video_mismatch_count: countValue(row.video_mismatch_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
    };
  } catch {
    throw new PublicProjectionError(500, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID");
  }
}

async function readProjectionCards(
  db: D1Database,
  sourceId: string,
  projectionId: string,
): Promise<PublicProjectionChildAggregate> {
  const row = await db.prepare(
    `SELECT COUNT(*) AS count,
            COALESCE(SUM(CASE WHEN projection_id=? AND source_id=? THEN 0 ELSE 1 END), 0) AS identity_mismatch_count
       FROM public_projection_cards
      WHERE projection_id=? OR source_id=?`,
  ).bind(projectionId, sourceId, projectionId, sourceId).first<PublicProjectionChildAggregate>();
  if (!row) return { count: 0, identity_mismatch_count: 0 };
  try {
    return {
      count: countValue(row.count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      identity_mismatch_count: countValue(row.identity_mismatch_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
    };
  } catch {
    throw new PublicProjectionError(500, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID");
  }
}

async function readProjectionTopics(
  db: D1Database,
  sourceId: string,
  projectionId: string,
): Promise<PublicProjectionChildAggregate> {
  const row = await db.prepare(
    `SELECT COUNT(*) AS count,
            COALESCE(SUM(CASE WHEN d.source_id=? AND d.projection_id=? THEN 0 ELSE 1 END), 0) AS identity_mismatch_count
       FROM search_topics AS st
       JOIN search_documents AS d ON d.id=st.document_id
      WHERE d.source_id=? OR d.projection_id=?`,
  ).bind(sourceId, projectionId, sourceId, projectionId).first<PublicProjectionChildAggregate>();
  if (!row) return { count: 0, identity_mismatch_count: 0 };
  try {
    return {
      count: countValue(row.count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
      identity_mismatch_count: countValue(row.identity_mismatch_count, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID"),
    };
  } catch {
    throw new PublicProjectionError(500, "PUBLIC_PROJECTION_VERIFY_DATABASE_INVALID");
  }
}

async function persistedReceiptHash(row: PublicProjectionRow, rowCount: number): Promise<string> {
  return sha256Hex([
    PUBLIC_PROJECTION_RECEIPT_SCHEMA,
    row.projection_id,
    row.source_id,
    row.manifest_sha256,
    row.content_sha256,
    row.private_import_receipt_sha256,
    row.status,
    String(rowCount),
  ].join("\u001f"));
}

function presenceReceipt(
  sourceId: string,
  state: PublicSourcePresenceState,
  documentCount: number,
  fullTranscriptPublicCount: number,
  projectionId: string | null,
  manifestSha256: string | null,
): PublicSourcePresenceReceipt {
  return parsePublicSourcePresenceReceipt({
    schema_version: PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA,
    source_id: sourceId,
    state,
    document_count: documentCount,
    full_transcript_public_count: fullTranscriptPublicCount,
    projection_id: projectionId,
    manifest_sha256: manifestSha256,
  });
}

export async function inspectPublicSource(db: D1Database, value: unknown): Promise<PublicSourcePresenceReceipt> {
  const request = parsePublicSourcePresenceRequest(value);
  const documents = await readSourceDocumentAggregate(db, request.source_id);
  const appliedResult = await db.prepare(
    `SELECT projection_id, source_id, manifest_sha256, content_sha256,
            private_import_receipt_sha256, card_count, status, receipt_sha256
       FROM public_projection_receipts
      WHERE source_id=? AND status='applied'`,
  ).bind(request.source_id).all<PublicProjectionRow>();
  const appliedRows = appliedResult.results ?? [];

  if (appliedRows.length > 1) opaquePresenceMismatch();
  if (documents.legacy_count > 0 && (appliedRows.length > 0 || documents.projected_count > 0)) {
    throw new PublicProjectionError(409, "PUBLIC_SOURCE_PRESENCE_MIXED_STATE");
  }
  if (appliedRows.length === 1) {
    const receipt = persistedProjectionRow(appliedRows[0], "PUBLIC_SOURCE_PRESENCE_MISMATCH");
    const numericId = tiktokSourceIdParts(request.source_id, "PUBLIC_SOURCE_PRESENCE_MISMATCH").numericId;
    const projectedDocuments = await readProjectionDocumentAggregate(db, request.source_id, receipt.projection_id, numericId);
    if (
      projectedDocuments.document_count !== receipt.card_count
      || projectedDocuments.source_count !== 1
      || projectedDocuments.video_count !== 1
      || projectedDocuments.source_mismatch_count !== 0
      || projectedDocuments.projection_mismatch_count !== 0
      || projectedDocuments.video_mismatch_count !== 0
      || projectedDocuments.legacy_count !== 0
    ) {
      opaquePresenceMismatch();
    }
    return presenceReceipt(
      request.source_id,
      "projected",
      projectedDocuments.document_count,
      projectedDocuments.full_transcript_public_count,
      receipt.projection_id,
      receipt.manifest_sha256,
    );
  }
  if (documents.projected_count > 0) opaquePresenceMismatch();
  if (documents.legacy_count > 0) {
    return presenceReceipt(
      request.source_id,
      "legacy_public",
      documents.document_count,
      documents.full_transcript_public_count,
      null,
      null,
    );
  }
  return presenceReceipt(request.source_id, "absent", 0, 0, null, null);
}

export async function verifyPublicProjection(db: D1Database, value: unknown): Promise<PublicProjectionReceipt> {
  const request = parsePublicProjectionVerifyRequest(value);
  const row = await db.prepare(
    `SELECT projection_id, source_id, manifest_sha256, content_sha256,
            private_import_receipt_sha256, card_count, status, receipt_sha256
       FROM public_projection_receipts
      WHERE projection_id=?
      LIMIT 1`,
  ).bind(request.projection_id).first<PublicProjectionRow>();
  if (!row) opaqueVerifyMismatch();
  const receipt = persistedProjectionRow(row, "PUBLIC_PROJECTION_VERIFY_MISMATCH");
  if (
    receipt.status !== "applied"
    || receipt.projection_id !== request.projection_id
    || receipt.source_id !== request.source_id
    || receipt.manifest_sha256 !== request.manifest_sha256
    || receipt.content_sha256 !== request.content_sha256
  ) {
    opaqueVerifyMismatch();
  }

  const numericId = tiktokSourceIdParts(request.source_id, "PUBLIC_PROJECTION_VERIFY_MISMATCH").numericId;
  const documents = await readProjectionDocumentAggregate(db, request.source_id, request.projection_id, numericId);
  const cards = await readProjectionCards(db, request.source_id, request.projection_id);
  const topics = await readProjectionTopics(db, request.source_id, request.projection_id);
  const expectedReceiptHash = await persistedReceiptHash(receipt, receipt.card_count);
  if (
    documents.document_count !== receipt.card_count
    || cards.count !== receipt.card_count
    || topics.count !== receipt.card_count
    || documents.source_count !== 1
    || documents.video_count !== 1
    || documents.full_transcript_public_count !== 0
    || documents.source_mismatch_count !== 0
    || documents.projection_mismatch_count !== 0
    || documents.video_mismatch_count !== 0
    || documents.legacy_count !== 0
    || cards.identity_mismatch_count !== 0
    || topics.identity_mismatch_count !== 0
    || receipt.receipt_sha256 !== expectedReceiptHash
  ) {
    opaqueVerifyMismatch();
  }
  return parsePublicProjectionReceipt({
    schema_version: PUBLIC_PROJECTION_RECEIPT_SCHEMA,
    projection_id: receipt.projection_id,
    source_id: receipt.source_id,
    manifest_sha256: receipt.manifest_sha256,
    content_sha256: receipt.content_sha256,
    status: "applied",
    card_count: receipt.card_count,
    row_count: documents.document_count,
    receipt_sha256: receipt.receipt_sha256,
  });
}

export async function applyPublicProjection(db: D1Database, value: unknown): Promise<PublicProjectionReceipt> {
  const request = parsePublicProjection(value);
  // Do not project over one of the legacy public rows for the same source.
  const legacy = await db.prepare(
    `SELECT 1 AS found
       FROM search_documents
      WHERE source_id=? AND (projection_id IS NULL OR projection_id='')
      LIMIT 1`,
  ).bind(request.source.source_id).first<{ found: number }>();
  if (legacy) throw new PublicProjectionError(409, "PUBLIC_PROJECTION_SOURCE_ALREADY_PUBLIC");

  // A replay is keyed by the exact source + manifest pair. Older manifests
  // remain immutable receipts after rollback, while a new manifest is only
  // eligible if there is no active projection for this source.
  const existing = await db.prepare(
    `SELECT projection_id, source_id, manifest_sha256, content_sha256,
            private_import_receipt_sha256, card_count, status, receipt_sha256
       FROM public_projection_receipts
      WHERE source_id=? AND manifest_sha256=?
      LIMIT 1`,
  ).bind(request.source.source_id, request.manifest_sha256).first<PublicProjectionRow>();

  if (existing) {
    if (
      existing.projection_id !== request.projection_id
      || existing.content_sha256 !== request.content_sha256
      || existing.private_import_receipt_sha256 !== request.private_import_receipt_sha256
      || existing.card_count !== request.cards.length
    ) {
      throw new PublicProjectionError(409, "PUBLIC_PROJECTION_INPUT_CONFLICT");
    }
    const count = await db.prepare(
      `SELECT COUNT(*) AS count FROM search_documents WHERE projection_id=?`,
    ).bind(request.projection_id).first<{ count: number }>();
    const rowCount = count?.count ?? 0;
    const hash = existing.receipt_sha256 || await receiptSha256(request, existing.status, rowCount);
    return exactReceipt(request, existing.status, existing.status === "rolled_back" ? 0 : existing.card_count, rowCount, hash);
  }

  const active = await db.prepare(
    `SELECT 1 AS found
       FROM public_projection_receipts
      WHERE source_id=? AND status='applied'
      LIMIT 1`,
  ).bind(request.source.source_id).first<{ found: number }>();
  if (active) throw new PublicProjectionError(409, "PUBLIC_PROJECTION_MANIFEST_CONFLICT");

  const cards = await Promise.all(request.cards.map(async (card) => {
    const cardId = await deterministicCardId(request.projection_id, card.ordinal);
    const searchId = await deterministicSearchId(cardId);
    const row = buildDocument(request, card, cardId, searchId);
    return { card, cardId, searchId, row };
  }));
  const applyReceiptHash = await receiptSha256(request, "applied", cards.length);
  const statements: D1PreparedStatement[] = [
    db.prepare(
      `INSERT INTO public_projection_receipts
        (projection_id, source_id, manifest_sha256, content_sha256,
         private_import_receipt_sha256, card_count, status, receipt_sha256)
       VALUES (?, ?, ?, ?, ?, ?, 'applied', ?)`,
    ).bind(
      request.projection_id,
      request.source.source_id,
      request.manifest_sha256,
      request.content_sha256,
      request.private_import_receipt_sha256,
      cards.length,
      applyReceiptHash,
    ),
  ];
  for (const entry of cards) {
    statements.push(
      cardSql(db, request, entry.card, entry.cardId, entry.searchId),
      documentSql(db, entry.row),
      topicSql(db, entry.row, entry.card.topic_label),
    );
  }
  try {
    await db.batch(statements);
  } catch {
    throw new PublicProjectionError(409, "PUBLIC_PROJECTION_WRITE_CONFLICT");
  }
  return exactReceipt(request, "applied", cards.length, cards.length, applyReceiptHash);
}

export async function rollbackPublicProjection(db: D1Database, value: unknown): Promise<PublicProjectionReceipt> {
  const request = parsePublicProjectionRollback(value);
  const existing = await db.prepare(
    `SELECT projection_id, source_id, manifest_sha256, content_sha256,
            private_import_receipt_sha256, card_count, status, receipt_sha256
       FROM public_projection_receipts
      WHERE projection_id=? AND manifest_sha256=?
      LIMIT 1`,
  ).bind(request.projection_id, request.manifest_sha256).first<PublicProjectionRow>();
  if (!existing || existing.source_id !== request.source_id || existing.content_sha256 !== request.content_sha256) {
    throw new PublicProjectionError(409, "PUBLIC_PROJECTION_ROLLBACK_MISMATCH");
  }

  if (existing.status === "rolled_back") {
    return {
      schema_version: PUBLIC_PROJECTION_RECEIPT_SCHEMA,
      projection_id: existing.projection_id,
      source_id: existing.source_id,
      manifest_sha256: existing.manifest_sha256,
      content_sha256: existing.content_sha256,
      status: "rolled_back",
      card_count: 0,
      row_count: 0,
      receipt_sha256: existing.receipt_sha256,
    };
  }

  const rollbackHash = await sha256Hex([
    "base2026.public-projection-receipt.v1",
    request.projection_id,
    request.source_id,
    request.manifest_sha256,
    request.content_sha256,
    existing.private_import_receipt_sha256,
    "rolled_back",
    "0",
  ].join("\u001f"));
  const statements: D1PreparedStatement[] = [
    db.prepare(
      `DELETE FROM search_topics
        WHERE document_id IN (SELECT id FROM search_documents WHERE projection_id=?)`,
    ).bind(request.projection_id),
    db.prepare(`DELETE FROM search_documents WHERE projection_id=?`).bind(request.projection_id),
    db.prepare(`DELETE FROM public_projection_cards WHERE projection_id=?`).bind(request.projection_id),
    db.prepare(
      `UPDATE public_projection_receipts
          SET status='rolled_back', receipt_sha256=?, updated_at=CURRENT_TIMESTAMP
        WHERE projection_id=? AND source_id=? AND manifest_sha256=?
          AND content_sha256=? AND status='applied'`,
    ).bind(rollbackHash, request.projection_id, request.source_id, request.manifest_sha256, request.content_sha256),
  ];
  try {
    await db.batch(statements);
  } catch {
    throw new PublicProjectionError(409, "PUBLIC_PROJECTION_ROLLBACK_CONFLICT");
  }
  return {
    schema_version: PUBLIC_PROJECTION_RECEIPT_SCHEMA,
    projection_id: request.projection_id,
    source_id: request.source_id,
    manifest_sha256: request.manifest_sha256,
    content_sha256: request.content_sha256,
    status: "rolled_back",
    card_count: 0,
    row_count: 0,
    receipt_sha256: rollbackHash,
  };
}

export const rollbackPublicProjectionById = rollbackPublicProjection;
