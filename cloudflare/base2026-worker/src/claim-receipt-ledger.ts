/**
 * Public claim-receipt canary ledger.
 *
 * This module is intentionally the public half of the lane.  Admission is
 * callable only through the Worker service binding; the default fetch handler
 * exposes the read-only route below.  Inputs contain public projection
 * identities and bounded evidence only.  The Worker rereads every selected
 * tuple from public D1 before one atomic ten-row insert.
 */

export const CLAIM_RECEIPT_LEDGER_SCHEMA = "base2026.claim-receipt-ledger.v1" as const;
export const CLAIM_RECEIPT_SCHEMA = "base2026.claim-receipt.v1" as const;
export const CLAIM_RECEIPT_ADMISSION_SCHEMA = "base2026.claim-receipt-admission.v1" as const;
export const CLAIM_RECEIPT_READ_SCHEMA = "base2026.claim-receipt-read.v1" as const;
export const CLAIM_RECEIPT_ROLLBACK_SCHEMA = "base2026.claim-receipt-rollback.v1" as const;
export const CLAIM_RECEIPT_CANARY_ID = "base2026.internal-linking.canary.v1" as const;
export const CLAIM_RECEIPT_TOPIC = "internal-linking" as const;
export const CLAIM_RECEIPT_POLICY_VERSION = "base2026.claim-receipt-admission.v1" as const;
export const CLAIM_RECEIPT_CANARY_SIZE = 10 as const;

const SHA256_PATTERN = /^[a-f0-9]{64}$/u;
const ID_PATTERN = /^[a-f0-9]{40}$/u;
const TIKTOK_ID_PATTERN = /^[0-9]{10,30}$/u;
const TIKTOK_HANDLE_PATTERN = /^[A-Za-z0-9._-]{2,256}$/u;
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/u;
const encoder = new TextEncoder();

const EMAIL_PATTERN = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/iu;
const PHONE_PATTERN = /(?<!\d)(?:\+?\d{1,3}[\s().-])?(?:\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{10})(?!\d)/u;
const SECRET_PATTERN = /\b(?:api|access|auth|authentication|client|app|webhook)?[_\s-]*(?:key|token|secret|password|passwd|credential|cookie|session[_\s-]*id)\s*[:=]\s*\S+/iu;
const SECRET_PHRASE_PATTERN = /\b(?:api|access|auth|authentication|client|app|webhook)[_\s-]*(?:key|token|secret|password|passwd|credential)\s*(?:is\s+|[:=]\s*)\S+/iu;
const TOKEN_FORMAT_PATTERN = /\b(?:sk_(?:live|test)_[A-Z0-9]{8,}|(?:ghp|github_pat|xox[baprs])[-_][A-Z0-9-]{8,}|AIza[A-Z0-9_-]{20,})\b/iu;
const BEARER_PATTERN = /\bbearer\s+[A-Z0-9._~+/=-]{8,}\b/iu;
const PRIVATE_MARKER_PATTERN = /\b(?:private[_\s-]*(?:only|notes?|context|source|text)|not[_\s-]*for[_\s-]*public[_\s-]*export|raw[_\s-]*(?:transcript|caption|captions|asr)|transcript(?:[_\s-]*text)?|captions?|asr)\b/iu;
const LOCAL_PATH_PATTERN = /(?:^|[\s(])(?:file:\/\/|~\/|\/(?:Users|home|tmp|var|private|Volumes)\/|[A-Za-z]:\\)/u;

export interface ClaimReceiptCandidate {
  selection_rank: number;
  source_id: string;
  projection_id: string;
  card_id: string;
  search_id: string;
  card_ordinal: number;
  creator_handle: string;
  creator_display_name: string;
  creator_url: string;
  original_url: string;
  video_id: string;
  base2026_url: string;
  published_at: string;
  published_date: string;
  claim_text: string;
  suggested_action: string;
  topic_label: string;
  evidence_excerpt: string;
  evidence_start_seconds: number;
  evidence_end_seconds: number;
  public_projection_receipt_sha256: string;
}

/** Immutable, public-safe receipt fields. Mutable D1 state/timestamps are not exported. */
export interface ClaimReceipt {
  schema_version: typeof CLAIM_RECEIPT_SCHEMA;
  receipt_id: string;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  selection_rank: number;
  source_id: string;
  projection_id: string;
  card_id: string;
  search_id: string;
  card_ordinal: number;
  creator_handle: string;
  creator_display_name: string;
  creator_url: string;
  original_url: string;
  video_id: string;
  base2026_url: string;
  published_at: string;
  published_date: string;
  claim_text: string;
  suggested_action: string;
  topic_label: string;
  evidence_excerpt: string;
  evidence_start_seconds: number;
  evidence_end_seconds: number;
  public_projection_receipt_sha256: string;
  policy_version: typeof CLAIM_RECEIPT_POLICY_VERSION;
}

export interface ClaimReceiptAdmissionRequest {
  schema_version: typeof CLAIM_RECEIPT_ADMISSION_SCHEMA;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  topic: typeof CLAIM_RECEIPT_TOPIC;
  policy_version: typeof CLAIM_RECEIPT_POLICY_VERSION;
  manifest_sha256: string;
  candidates: ClaimReceiptCandidate[];
}

export interface ClaimReceiptReadRequest {
  schema_version: typeof CLAIM_RECEIPT_READ_SCHEMA;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  topic: typeof CLAIM_RECEIPT_TOPIC;
}

export interface ClaimReceiptRollbackRequest {
  schema_version: typeof CLAIM_RECEIPT_ROLLBACK_SCHEMA;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  ledger_sha256: string;
}

export interface ClaimReceiptLedgerResponse {
  schema_version: typeof CLAIM_RECEIPT_LEDGER_SCHEMA;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  topic: typeof CLAIM_RECEIPT_TOPIC;
  policy_version: typeof CLAIM_RECEIPT_POLICY_VERSION;
  count: typeof CLAIM_RECEIPT_CANARY_SIZE;
  ledger_sha256: string;
  generated_at: string;
  receipts: ClaimReceipt[];
}

export type ClaimReceiptAdmissionResult =
  | {
      status: "held";
      code: "CLAIM_RECEIPT_CANARY_NOT_READY" | "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED";
      count: number;
    }
  | {
      status: "admitted" | "replayed";
      canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
      topic: typeof CLAIM_RECEIPT_TOPIC;
      count: typeof CLAIM_RECEIPT_CANARY_SIZE;
      ledger_sha256: string;
    }
  | {
      status: "conflict";
      code: "CLAIM_RECEIPT_CANARY_CONFLICT";
    };

export type ClaimReceiptReadResult =
  | { status: "held"; code: "CLAIM_RECEIPT_CANARY_NOT_READY"; count: number }
  | { status: "ready"; payload: ClaimReceiptLedgerResponse };

export type ClaimReceiptRollbackResult = {
  schema_version: typeof CLAIM_RECEIPT_ROLLBACK_SCHEMA;
  canary_id: typeof CLAIM_RECEIPT_CANARY_ID;
  ledger_sha256: string;
  status: "rolled_back" | "already_rolled_back";
  count: typeof CLAIM_RECEIPT_CANARY_SIZE;
};

export class ClaimReceiptLedgerError extends Error {
  constructor(
    readonly status: 400 | 409 | 500,
    readonly code: string,
  ) {
    super(code);
    this.name = "ClaimReceiptLedgerError";
  }
}

type Row = Record<string, unknown>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, keys: readonly string[], code: string): void {
  const expected = new Set(keys);
  const actual = Object.keys(value);
  if (actual.length !== keys.length || actual.some((key) => !expected.has(key))) {
    throw new ClaimReceiptLedgerError(400, code);
  }
}

function stringValue(value: unknown, code: string, min: number, max: number): string {
  if (typeof value !== "string") throw new ClaimReceiptLedgerError(400, code);
  const result = value.trim();
  if (result.length < min || result.length > max) {
    throw new ClaimReceiptLedgerError(400, code);
  }
  return result;
}

function hashValue(value: unknown, code: string): string {
  const result = stringValue(value, code, 64, 64).toLowerCase();
  if (!SHA256_PATTERN.test(result)) throw new ClaimReceiptLedgerError(400, code);
  return result;
}

function idValue(value: unknown, code: string): string {
  const result = stringValue(value, code, 40, 40).toLowerCase();
  if (!ID_PATTERN.test(result)) throw new ClaimReceiptLedgerError(400, code);
  return result;
}

function integerValue(value: unknown, code: string, min: number, max: number): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < min || value > max) {
    throw new ClaimReceiptLedgerError(400, code);
  }
  return value;
}

function finiteNumber(value: unknown, code: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 86_400) {
    throw new ClaimReceiptLedgerError(400, code);
  }
  const milliseconds = Math.round(value * 1_000);
  if (Math.abs(milliseconds / 1_000 - value) > Number.EPSILON * Math.max(1, value)) {
    throw new ClaimReceiptLedgerError(400, code);
  }
  return milliseconds / 1_000;
}

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
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_PRIVACY_REJECTED");
  }
}

function sourceParts(value: unknown): { sourceId: string; handle: string; videoId: string } {
  const sourceId = stringValue(value, "CLAIM_RECEIPT_SOURCE_ID_INVALID", 10, 300);
  const match = sourceId.match(/^tiktok:([A-Za-z0-9._-]{2,256}):([0-9]{10,30})$/u);
  if (!match || !TIKTOK_HANDLE_PATTERN.test(match[1]) || !TIKTOK_ID_PATTERN.test(match[2])) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_SOURCE_ID_INVALID");
  }
  return { sourceId, handle: match[1], videoId: match[2] };
}

function creatorHandle(value: unknown, sourceHandle: string): string {
  const result = stringValue(value, "CLAIM_RECEIPT_CREATOR_INVALID", 3, 257);
  assertPublicText(result);
  if (!result.startsWith("@") || result.slice(1) !== sourceHandle || !TIKTOK_HANDLE_PATTERN.test(sourceHandle)) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CREATOR_INVALID");
  }
  return result;
}

function dateValue(value: unknown, code: string): string {
  const result = stringValue(value, code, 10, 10);
  if (!DATE_PATTERN.test(result)) throw new ClaimReceiptLedgerError(400, code);
  const parsed = new Date(`${result}T00:00:00.000Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== result) {
    throw new ClaimReceiptLedgerError(400, code);
  }
  return result;
}

function canonicalUrl(value: unknown, handle: string, videoId: string): string {
  const result = stringValue(value, "CLAIM_RECEIPT_ORIGINAL_URL_INVALID", 12, 2_048);
  let parsed: URL;
  try {
    parsed = new URL(result);
  } catch {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ORIGINAL_URL_INVALID");
  }
  const expectedPath = `/@${handle}/video/${videoId}`;
  if (
    parsed.protocol !== "https:"
    || !["www.tiktok.com", "tiktok.com"].includes(parsed.hostname)
    || parsed.port
    || parsed.username
    || parsed.password
    || parsed.search
    || parsed.hash
    || parsed.pathname !== expectedPath
    || parsed.toString() !== result
  ) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ORIGINAL_URL_INVALID");
  }
  return result;
}

function creatorUrl(value: unknown, handle: string): string {
  const result = stringValue(value, "CLAIM_RECEIPT_CREATOR_URL_INVALID", 12, 512);
  const expected = `https://www.tiktok.com/@${handle}`;
  if (result !== expected) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CREATOR_URL_INVALID");
  return result;
}

function baseUrl(value: unknown, videoId: string): string {
  const result = stringValue(value, "CLAIM_RECEIPT_BASE_URL_INVALID", 12, 512);
  const expected = `https://base2026.dev/sources/tiktok-video-${videoId}`;
  if (result !== expected) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_BASE_URL_INVALID");
  return result;
}

/** Slug normalization is deliberately narrow: no synonym or fuzzy inference. */
export function normalizeClaimReceiptTopic(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("en-US")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/gu, "")
    .slice(0, 160);
}

function topicValue(value: unknown): string {
  const result = stringValue(value, "CLAIM_RECEIPT_TOPIC_INVALID", 2, 120);
  assertPublicText(result);
  const normalized = normalizeClaimReceiptTopic(result);
  if (!/^internal-linking(?:-[a-z0-9]+)*$/u.test(normalized)) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_TOPIC_INVALID");
  }
  return result;
}

const CANDIDATE_KEYS = [
  "selection_rank",
  "source_id",
  "projection_id",
  "card_id",
  "search_id",
  "card_ordinal",
  "creator_handle",
  "creator_display_name",
  "creator_url",
  "original_url",
  "video_id",
  "base2026_url",
  "published_at",
  "published_date",
  "claim_text",
  "suggested_action",
  "topic_label",
  "evidence_excerpt",
  "evidence_start_seconds",
  "evidence_end_seconds",
  "public_projection_receipt_sha256",
] as const;

function parseCandidate(value: unknown): ClaimReceiptCandidate {
  if (!isRecord(value)) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CANDIDATE_INVALID");
  exactKeys(value, CANDIDATE_KEYS, "CLAIM_RECEIPT_CANDIDATE_FIELDS_INVALID");
  const source = sourceParts(value.source_id);
  const handle = creatorHandle(value.creator_handle, source.handle);
  const videoId = stringValue(value.video_id, "CLAIM_RECEIPT_VIDEO_ID_INVALID", 10, 30);
  if (!TIKTOK_ID_PATTERN.test(videoId) || videoId !== source.videoId) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_VIDEO_ID_INVALID");
  }
  const publishedAt = dateValue(value.published_at, "CLAIM_RECEIPT_PUBLISHED_AT_INVALID");
  const publishedDate = dateValue(value.published_date, "CLAIM_RECEIPT_PUBLISHED_DATE_INVALID");
  if (publishedDate !== publishedAt) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_PUBLISHED_DATE_INVALID");
  const displayName = stringValue(value.creator_display_name, "CLAIM_RECEIPT_CREATOR_NAME_INVALID", 0, 256);
  const claim = stringValue(value.claim_text, "CLAIM_RECEIPT_CLAIM_INVALID", 20, 360);
  const action = stringValue(value.suggested_action, "CLAIM_RECEIPT_ACTION_INVALID", 20, 360);
  const topic = topicValue(value.topic_label);
  const excerpt = stringValue(value.evidence_excerpt, "CLAIM_RECEIPT_EVIDENCE_INVALID", 20, 520);
  for (const text of [displayName, claim, action, excerpt]) assertPublicText(text);
  const start = finiteNumber(value.evidence_start_seconds, "CLAIM_RECEIPT_EVIDENCE_START_INVALID");
  const end = finiteNumber(value.evidence_end_seconds, "CLAIM_RECEIPT_EVIDENCE_END_INVALID");
  if (end < start) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_EVIDENCE_RANGE_INVALID");
  return {
    selection_rank: integerValue(value.selection_rank, "CLAIM_RECEIPT_SELECTION_RANK_INVALID", 1, CLAIM_RECEIPT_CANARY_SIZE),
    source_id: source.sourceId,
    projection_id: idValue(value.projection_id, "CLAIM_RECEIPT_PROJECTION_ID_INVALID"),
    card_id: idValue(value.card_id, "CLAIM_RECEIPT_CARD_ID_INVALID"),
    search_id: idValue(value.search_id, "CLAIM_RECEIPT_SEARCH_ID_INVALID"),
    card_ordinal: integerValue(value.card_ordinal, "CLAIM_RECEIPT_CARD_ORDINAL_INVALID", 0, 2),
    creator_handle: handle,
    creator_display_name: displayName,
    creator_url: creatorUrl(value.creator_url, source.handle),
    original_url: canonicalUrl(value.original_url, source.handle, videoId),
    video_id: videoId,
    base2026_url: baseUrl(value.base2026_url, videoId),
    published_at: publishedAt,
    published_date: publishedDate,
    claim_text: claim,
    suggested_action: action,
    topic_label: topic,
    evidence_excerpt: excerpt,
    evidence_start_seconds: start,
    evidence_end_seconds: end,
    public_projection_receipt_sha256: hashValue(
      value.public_projection_receipt_sha256,
      "CLAIM_RECEIPT_PUBLIC_PROJECTION_HASH_INVALID",
    ),
  };
}

export function parseClaimReceiptAdmissionRequest(value: unknown): ClaimReceiptAdmissionRequest {
  if (!isRecord(value)) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ADMISSION_INVALID");
  exactKeys(
    value,
    ["schema_version", "canary_id", "topic", "policy_version", "manifest_sha256", "candidates"],
    "CLAIM_RECEIPT_ADMISSION_FIELDS_INVALID",
  );
  if (value.schema_version !== CLAIM_RECEIPT_ADMISSION_SCHEMA) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ADMISSION_SCHEMA_INVALID");
  }
  if (value.canary_id !== CLAIM_RECEIPT_CANARY_ID || value.topic !== CLAIM_RECEIPT_TOPIC) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CANARY_INVALID");
  }
  if (value.policy_version !== CLAIM_RECEIPT_POLICY_VERSION) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_POLICY_INVALID");
  }
  if (!Array.isArray(value.candidates) || value.candidates.length > CLAIM_RECEIPT_CANARY_SIZE) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CANDIDATE_COUNT_INVALID");
  }
  const candidates = value.candidates.map(parseCandidate);
  const ranks = candidates.map((candidate) => candidate.selection_rank);
  if (new Set(ranks).size !== ranks.length) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_DUPLICATE_SELECTION_RANK");
  }
  return {
    schema_version: CLAIM_RECEIPT_ADMISSION_SCHEMA,
    canary_id: CLAIM_RECEIPT_CANARY_ID,
    topic: CLAIM_RECEIPT_TOPIC,
    policy_version: CLAIM_RECEIPT_POLICY_VERSION,
    manifest_sha256: hashValue(value.manifest_sha256, "CLAIM_RECEIPT_MANIFEST_INVALID"),
    candidates,
  };
}

export function parseClaimReceiptReadRequest(value: unknown): ClaimReceiptReadRequest {
  if (!isRecord(value)) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_READ_INVALID");
  exactKeys(value, ["schema_version", "canary_id", "topic"], "CLAIM_RECEIPT_READ_FIELDS_INVALID");
  if (value.schema_version !== CLAIM_RECEIPT_READ_SCHEMA) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_READ_SCHEMA_INVALID");
  }
  if (value.canary_id !== CLAIM_RECEIPT_CANARY_ID || value.topic !== CLAIM_RECEIPT_TOPIC) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CANARY_INVALID");
  }
  return { schema_version: CLAIM_RECEIPT_READ_SCHEMA, canary_id: CLAIM_RECEIPT_CANARY_ID, topic: CLAIM_RECEIPT_TOPIC };
}

export function parseClaimReceiptRollbackRequest(value: unknown): ClaimReceiptRollbackRequest {
  if (!isRecord(value)) throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ROLLBACK_INVALID");
  exactKeys(value, ["schema_version", "canary_id", "ledger_sha256"], "CLAIM_RECEIPT_ROLLBACK_FIELDS_INVALID");
  if (value.schema_version !== CLAIM_RECEIPT_ROLLBACK_SCHEMA) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_ROLLBACK_SCHEMA_INVALID");
  }
  if (value.canary_id !== CLAIM_RECEIPT_CANARY_ID) {
    throw new ClaimReceiptLedgerError(400, "CLAIM_RECEIPT_CANARY_INVALID");
  }
  return {
    schema_version: CLAIM_RECEIPT_ROLLBACK_SCHEMA,
    canary_id: CLAIM_RECEIPT_CANARY_ID,
    ledger_sha256: hashValue(value.ledger_sha256, "CLAIM_RECEIPT_LEDGER_HASH_INVALID"),
  };
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

export function canonicalClaimReceiptJson(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function claimReceiptManifestSha256(candidates: ClaimReceiptCandidate[]): Promise<string> {
  return sha256Hex(canonicalClaimReceiptJson(candidates));
}

function immutableReceiptFields(candidate: ClaimReceiptCandidate): Omit<ClaimReceipt, "receipt_id"> {
  return {
    schema_version: CLAIM_RECEIPT_SCHEMA,
    canary_id: CLAIM_RECEIPT_CANARY_ID,
    selection_rank: candidate.selection_rank,
    source_id: candidate.source_id,
    projection_id: candidate.projection_id,
    card_id: candidate.card_id,
    search_id: candidate.search_id,
    card_ordinal: candidate.card_ordinal,
    creator_handle: candidate.creator_handle,
    creator_display_name: candidate.creator_display_name,
    creator_url: candidate.creator_url,
    original_url: candidate.original_url,
    video_id: candidate.video_id,
    base2026_url: candidate.base2026_url,
    published_at: candidate.published_at,
    published_date: candidate.published_date,
    claim_text: candidate.claim_text,
    suggested_action: candidate.suggested_action,
    topic_label: candidate.topic_label,
    evidence_excerpt: candidate.evidence_excerpt,
    evidence_start_seconds: candidate.evidence_start_seconds,
    evidence_end_seconds: candidate.evidence_end_seconds,
    public_projection_receipt_sha256: candidate.public_projection_receipt_sha256,
    policy_version: CLAIM_RECEIPT_POLICY_VERSION,
  };
}

async function receiptFromCandidate(candidate: ClaimReceiptCandidate): Promise<ClaimReceipt> {
  const immutable = immutableReceiptFields(candidate);
  return { ...immutable, receipt_id: await sha256Hex(canonicalClaimReceiptJson(immutable)) };
}

export async function claimReceiptLedgerSha256(receipts: ClaimReceipt[]): Promise<string> {
  return sha256Hex(`${receipts.map(canonicalClaimReceiptJson).join("\n")}\n`);
}

function candidateComparable(value: ClaimReceiptCandidate): string {
  return canonicalClaimReceiptJson(value);
}

function sortCandidates(a: ClaimReceiptCandidate, b: ClaimReceiptCandidate): number {
  return b.published_date.localeCompare(a.published_date)
    || a.source_id.localeCompare(b.source_id)
    || a.projection_id.localeCompare(b.projection_id)
    || a.card_ordinal - b.card_ordinal
    || a.card_id.localeCompare(b.card_id);
}

function candidateFromRow(row: Row, selectionRank: number): ClaimReceiptCandidate {
  return parseCandidate({
    selection_rank: selectionRank,
    source_id: row.source_id,
    projection_id: row.projection_id,
    card_id: row.card_id,
    search_id: row.search_id,
    card_ordinal: row.card_ordinal,
    creator_handle: row.creator_handle,
    creator_display_name: row.creator_display_name,
    creator_url: row.creator_url,
    original_url: row.original_url,
    video_id: row.video_id,
    base2026_url: row.base2026_url,
    published_at: row.published_at,
    published_date: row.published_date,
    claim_text: row.claim_text,
    suggested_action: row.suggested_action,
    topic_label: row.topic_label,
    evidence_excerpt: row.evidence_excerpt,
    evidence_start_seconds: row.evidence_start_seconds,
    evidence_end_seconds: row.evidence_end_seconds,
    public_projection_receipt_sha256: row.public_projection_receipt_sha256,
  });
}

async function rowMatchesCandidate(row: Row, candidate: ClaimReceiptCandidate): Promise<boolean> {
  try {
    const reread = candidateFromRow(row, candidate.selection_rank);
    const expectedProjectionId = (await sha256Hex(
      ["public-projection-receipt", candidate.source_id, String(row.projection_manifest_sha256)].join("\u001f"),
    )).slice(0, 40);
    const expectedCardId = (await sha256Hex(
      ["public-projection-card", candidate.projection_id, String(candidate.card_ordinal)].join("\u001f"),
    )).slice(0, 40);
    const expectedSearchId = (await sha256Hex(
      ["public-projection-search-document", candidate.card_id].join("\u001f"),
    )).slice(0, 40);
    return candidateComparable(reread) === candidateComparable(candidate)
      && candidate.projection_id === expectedProjectionId
      && candidate.card_id === expectedCardId
      && candidate.search_id === expectedSearchId
      && row.source_id === row.receipt_source_id
      && row.projection_id === row.receipt_projection_id
      && row.search_id === row.document_id
      && row.card_source_id === row.source_id
      && row.card_projection_id === row.projection_id
      && row.card_search_id === row.search_id
      && row.card_ordinal === row.document_chunk_index
      && row.document_item_id === `tiktok-video-${candidate.video_id}`
      && row.document_chunk_id === candidate.card_id
      && row.document_post_id === candidate.video_id
      && row.document_video_id === candidate.video_id
      && row.document_creator_handle === candidate.creator_handle
      && row.document_handle === candidate.creator_handle
      && row.document_creator_url === candidate.creator_url
      && row.document_source_url === candidate.original_url
      && row.document_body === candidate.evidence_excerpt
      && row.document_title === candidate.claim_text
      && row.document_platform === "tiktok"
      && row.document_source_type === "tiktok_video"
      && row.document_title_source === "public_projection"
      && row.document_full_transcript_public === 0
      && row.document_public_policy === "search_passage"
      && row.document_public_surface === "main_search"
      && row.document_admission_state === "normal_public_card"
      && row.projection_status === "applied"
      && Number(row.projection_card_count) === Number(row.projection_card_rows)
      && Number(row.projection_document_rows) === Number(row.projection_card_rows)
      && Number(row.matching_topic_rows) === 1;
  } catch {
    return false;
  }
}

async function queryRows(db: D1Database, sql: string, ...parameters: unknown[]): Promise<Row[]> {
  const result = await db.prepare(sql).bind(...parameters).all<Row>();
  return result.results;
}

async function claimReceiptLedgerTableReady(db: D1Database): Promise<boolean> {
  const rows = await queryRows(
    db,
    "SELECT COUNT(*) AS count FROM sqlite_master WHERE type='table' AND name='public_claim_receipts'",
  );
  return Number(rows[0]?.count ?? 0) === 1;
}

const PROJECTION_CANDIDATE_SQL = `
  SELECT
    c.source_id AS source_id,
    c.projection_id AS projection_id,
    c.card_id AS card_id,
    c.search_id AS search_id,
    c.ordinal AS card_ordinal,
    c.claim_text AS claim_text,
    c.suggested_action AS suggested_action,
    c.topic_label AS topic_label,
    c.evidence_excerpt AS evidence_excerpt,
    c.evidence_start_seconds AS evidence_start_seconds,
    c.evidence_end_seconds AS evidence_end_seconds,
    r.source_id AS receipt_source_id,
    r.projection_id AS receipt_projection_id,
    r.manifest_sha256 AS projection_manifest_sha256,
    r.receipt_sha256 AS public_projection_receipt_sha256,
    r.status AS projection_status,
    r.card_count AS projection_card_count,
    (SELECT COUNT(*) FROM public_projection_cards c2 WHERE c2.projection_id = c.projection_id) AS projection_card_rows,
    (SELECT COUNT(*) FROM search_documents d2 WHERE d2.projection_id = c.projection_id) AS projection_document_rows,
    d.id AS document_id,
    d.item_id AS document_item_id,
    d.chunk_id AS document_chunk_id,
    d.chunk_index AS document_chunk_index,
    d.source_id AS card_source_id,
    d.projection_id AS card_projection_id,
    d.id AS card_search_id,
    d.post_id AS document_post_id,
    d.video_id AS document_video_id,
    d.creator_handle AS document_creator_handle,
    d.handle AS document_handle,
    d.creator_url AS document_creator_url,
    d.source_url AS document_source_url,
    d.body AS document_body,
    d.title AS document_title,
    d.platform AS document_platform,
    d.source_type AS document_source_type,
    d.title_source AS document_title_source,
    d.full_transcript_public AS document_full_transcript_public,
    d.public_policy AS document_public_policy,
    d.public_surface AS document_public_surface,
    d.admission_state AS document_admission_state,
    d.creator_display_name AS creator_display_name,
    d.creator_handle AS creator_handle,
    d.creator_url AS creator_url,
    d.source_url AS original_url,
    d.video_id AS video_id,
    'https://base2026.dev/sources/tiktok-video-' || d.video_id AS base2026_url,
    d.published_at AS published_at,
    d.published_date AS published_date,
    (SELECT COUNT(*) FROM search_topics st WHERE st.document_id = d.id) AS topic_rows,
    (SELECT COUNT(*) FROM search_topics st WHERE st.document_id = d.id AND st.topic_label = c.topic_label) AS matching_topic_rows
  FROM public_projection_cards c
  JOIN public_projection_receipts r ON r.projection_id = c.projection_id
  JOIN search_documents d ON d.id = c.search_id
  WHERE r.status = 'applied'
    AND d.full_transcript_public = 0
    AND d.public_policy = 'search_passage'
    AND d.public_surface = 'main_search'
    AND d.admission_state = 'normal_public_card'
    AND d.platform = 'tiktok'
    AND d.source_type = 'tiktok_video'
  ORDER BY d.published_date DESC, c.source_id ASC, c.projection_id ASC, c.ordinal ASC, c.card_id ASC
`;

async function sourceHasNoLegacyRows(db: D1Database, sourceId: string, projectionId: string, expectedRows: number): Promise<boolean> {
  const rows = await queryRows(
    db,
    `SELECT
       COUNT(*) AS total_rows,
       SUM(CASE WHEN projection_id = ? AND admission_state = 'normal_public_card'
                     AND full_transcript_public = 0 THEN 1 ELSE 0 END) AS projected_rows
       FROM search_documents WHERE source_id = ?`,
    projectionId,
    sourceId,
  );
  const row = rows[0];
  return Number(row?.total_rows ?? -1) === expectedRows
    && Number(row?.projected_rows ?? -1) === expectedRows;
}

async function deterministicEligibleCandidates(db: D1Database): Promise<ClaimReceiptCandidate[]> {
  const rows = await queryRows(db, PROJECTION_CANDIDATE_SQL);
  const parsed: ClaimReceiptCandidate[] = [];
  const seenSources = new Set<string>();
  const seenCreators = new Map<string, number>();
  for (const row of rows) {
    let normalizedTopic = "";
    try {
      normalizedTopic = normalizeClaimReceiptTopic(String(row.topic_label ?? ""));
    } catch {
      continue;
    }
    if (!/^internal-linking(?:-[a-z0-9]+)*$/u.test(normalizedTopic)) continue;
    let candidate: ClaimReceiptCandidate;
    try {
      candidate = candidateFromRow(row, 1);
    } catch {
      throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED");
    }
    if (!await rowMatchesCandidate(row, { ...candidate, selection_rank: 1 })) {
      throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED");
    }
    if (!await sourceHasNoLegacyRows(db, candidate.source_id, candidate.projection_id, Number(row.projection_card_rows))) {
      throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED");
    }
    parsed.push(candidate);
  }
  parsed.sort(sortCandidates);
  const selected: ClaimReceiptCandidate[] = [];
  for (const candidate of parsed) {
    if (seenSources.has(candidate.source_id)) continue;
    const creatorCount = seenCreators.get(candidate.creator_handle) ?? 0;
    if (creatorCount >= 2) continue;
    seenSources.add(candidate.source_id);
    seenCreators.set(candidate.creator_handle, creatorCount + 1);
    selected.push({ ...candidate, selection_rank: selected.length + 1 });
    if (selected.length === CLAIM_RECEIPT_CANARY_SIZE) break;
  }
  return selected;
}

async function activeRows(db: D1Database, canaryId: string): Promise<Row[]> {
  return queryRows(
    db,
    `SELECT receipt_id, canary_id, selection_rank, source_id, projection_id, card_id,
            search_id, card_ordinal, creator_handle, creator_display_name, creator_url, original_url,
            video_id, base2026_url, published_at, published_date, claim_text,
            suggested_action, topic_label, evidence_excerpt, evidence_start_seconds,
            evidence_end_seconds, public_projection_receipt_sha256, policy_version,
            ledger_sha256, state
       FROM public_claim_receipts
      WHERE canary_id = ? AND state = 'active'
      ORDER BY selection_rank ASC`,
    canaryId,
  );
}

async function allLedgerRows(db: D1Database, canaryId: string): Promise<Row[]> {
  return queryRows(
    db,
    `SELECT receipt_id, canary_id, selection_rank, source_id, projection_id, card_id,
            search_id, card_ordinal, creator_handle, creator_display_name, creator_url, original_url,
            video_id, base2026_url, published_at, published_date, claim_text,
            suggested_action, topic_label, evidence_excerpt, evidence_start_seconds,
            evidence_end_seconds, public_projection_receipt_sha256, policy_version,
            ledger_sha256, state
       FROM public_claim_receipts
      WHERE canary_id = ?
      ORDER BY selection_rank ASC`,
    canaryId,
  );
}

async function receiptFromStoredRow(row: Row): Promise<ClaimReceipt> {
  const candidate = parseCandidate({
    selection_rank: row.selection_rank,
    source_id: row.source_id,
    projection_id: row.projection_id,
    card_id: row.card_id,
    search_id: row.search_id,
    card_ordinal: row.card_ordinal,
    creator_handle: row.creator_handle,
    creator_display_name: row.creator_display_name,
    creator_url: row.creator_url,
    original_url: row.original_url,
    video_id: row.video_id,
    base2026_url: row.base2026_url,
    published_at: row.published_at,
    published_date: row.published_date,
    claim_text: row.claim_text,
    suggested_action: row.suggested_action,
    topic_label: row.topic_label,
    evidence_excerpt: row.evidence_excerpt,
    evidence_start_seconds: row.evidence_start_seconds,
    evidence_end_seconds: row.evidence_end_seconds,
    public_projection_receipt_sha256: row.public_projection_receipt_sha256,
  });
  const receipt = await receiptFromCandidate(candidate);
  if (row.receipt_id !== receipt.receipt_id || row.canary_id !== CLAIM_RECEIPT_CANARY_ID || row.policy_version !== CLAIM_RECEIPT_POLICY_VERSION) {
    throw new ClaimReceiptLedgerError(500, "CLAIM_RECEIPT_LEDGER_CORRUPT");
  }
  return receipt;
}

async function makeLedgerResponse(db: D1Database, generatedAt: string): Promise<ClaimReceiptReadResult> {
  const rows = await activeRows(db, CLAIM_RECEIPT_CANARY_ID);
  if (rows.length !== CLAIM_RECEIPT_CANARY_SIZE) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_NOT_READY", count: rows.length };
  }
  const receipts: ClaimReceipt[] = [];
  for (const row of rows) receipts.push(await receiptFromStoredRow(row));
  const ledgerSha256 = await claimReceiptLedgerSha256(receipts);
  if (rows.some((row) => row.ledger_sha256 !== ledgerSha256)) {
    throw new ClaimReceiptLedgerError(500, "CLAIM_RECEIPT_LEDGER_CORRUPT");
  }
  return {
    status: "ready",
    payload: {
      schema_version: CLAIM_RECEIPT_LEDGER_SCHEMA,
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      topic: CLAIM_RECEIPT_TOPIC,
      policy_version: CLAIM_RECEIPT_POLICY_VERSION,
      count: CLAIM_RECEIPT_CANARY_SIZE,
      ledger_sha256: ledgerSha256,
      generated_at: generatedAt,
      receipts,
    },
  };
}

export async function readClaimReceiptLedger(
  db: D1Database,
  generatedAt = new Date().toISOString(),
): Promise<ClaimReceiptReadResult> {
  if (!await claimReceiptLedgerTableReady(db)) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_NOT_READY", count: 0 };
  }
  return makeLedgerResponse(db, generatedAt);
}

export async function admitClaimReceiptCanary(
  db: D1Database,
  value: unknown,
): Promise<ClaimReceiptAdmissionResult> {
  const request = parseClaimReceiptAdmissionRequest(value);
  if (!await claimReceiptLedgerTableReady(db)) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_NOT_READY", count: 0 };
  }
  let selected: ClaimReceiptCandidate[];
  try {
    selected = await deterministicEligibleCandidates(db);
  } catch (error) {
    if (error instanceof ClaimReceiptLedgerError && error.code === "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED") {
      return { status: "held", code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED", count: 0 };
    }
    throw error;
  }
  if (selected.length !== CLAIM_RECEIPT_CANARY_SIZE) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_NOT_READY", count: selected.length };
  }
  if (request.candidates.length !== CLAIM_RECEIPT_CANARY_SIZE) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_NOT_READY", count: request.candidates.length };
  }
  const supplied = [...request.candidates].sort((a, b) => a.selection_rank - b.selection_rank);
  const manifestSha256 = await claimReceiptManifestSha256(supplied);
  if (manifestSha256 !== request.manifest_sha256) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED", count: supplied.length };
  }
  if (supplied.some((candidate, index) => candidate.selection_rank !== index + 1)) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED", count: supplied.length };
  }
  if (supplied.some((candidate, index) => candidateComparable(candidate) !== candidateComparable(selected[index]))) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED", count: supplied.length };
  }
  const sourceSet = new Set(supplied.map((candidate) => candidate.source_id));
  const creatorCounts = new Map<string, number>();
  for (const candidate of supplied) creatorCounts.set(candidate.creator_handle, (creatorCounts.get(candidate.creator_handle) ?? 0) + 1);
  if (sourceSet.size !== CLAIM_RECEIPT_CANARY_SIZE || [...creatorCounts.values()].some((count) => count > 2)) {
    return { status: "held", code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED", count: supplied.length };
  }
  const receipts: ClaimReceipt[] = [];
  for (const candidate of supplied) receipts.push(await receiptFromCandidate(candidate));
  const ledgerSha256 = await claimReceiptLedgerSha256(receipts);
  const existing = await allLedgerRows(db, CLAIM_RECEIPT_CANARY_ID);
  if (existing.length > 0) {
    if (existing.length === CLAIM_RECEIPT_CANARY_SIZE && existing.every((row) => row.ledger_sha256 === ledgerSha256)) {
      const existingReceipts: ClaimReceipt[] = [];
      for (const row of existing) existingReceipts.push(await receiptFromStoredRow(row));
      if (await claimReceiptLedgerSha256(existingReceipts) === ledgerSha256) {
        if (existing.every((row) => row.state === "active")) {
          return {
            status: "replayed",
            canary_id: CLAIM_RECEIPT_CANARY_ID,
            topic: CLAIM_RECEIPT_TOPIC,
            count: CLAIM_RECEIPT_CANARY_SIZE,
            ledger_sha256: ledgerSha256,
          };
        }
        return { status: "conflict", code: "CLAIM_RECEIPT_CANARY_CONFLICT" };
      }
    }
    return { status: "conflict", code: "CLAIM_RECEIPT_CANARY_CONFLICT" };
  }
  const now = new Date().toISOString();
  const statements = receipts.map((receipt) => db.prepare(
    `INSERT INTO public_claim_receipts
      (receipt_id, canary_id, selection_rank, source_id, projection_id, card_id, search_id, card_ordinal,
       creator_handle, creator_display_name, creator_url, original_url, video_id,
       base2026_url, published_at, published_date, claim_text, suggested_action,
       topic_label, evidence_excerpt, evidence_start_seconds, evidence_end_seconds,
       public_projection_receipt_sha256, policy_version, ledger_sha256, state, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)`
  ).bind(
    receipt.receipt_id,
    receipt.canary_id,
    receipt.selection_rank,
    receipt.source_id,
    receipt.projection_id,
    receipt.card_id,
    receipt.search_id,
    receipt.card_ordinal,
    receipt.creator_handle,
    receipt.creator_display_name,
    receipt.creator_url,
    receipt.original_url,
    receipt.video_id,
    receipt.base2026_url,
    receipt.published_at,
    receipt.published_date,
    receipt.claim_text,
    receipt.suggested_action,
    receipt.topic_label,
    receipt.evidence_excerpt,
    receipt.evidence_start_seconds,
    receipt.evidence_end_seconds,
    receipt.public_projection_receipt_sha256,
    receipt.policy_version,
    ledgerSha256,
    now,
    now,
  ));
  try {
    await db.batch(statements);
  } catch {
    // D1 batch is atomic.  Do not expose SQL details or return a partial
    // admission receipt if a concurrent/conflicting write wins the race.
    const replayRows = await allLedgerRows(db, CLAIM_RECEIPT_CANARY_ID);
    if (replayRows.length === CLAIM_RECEIPT_CANARY_SIZE && replayRows.every((row) => row.ledger_sha256 === ledgerSha256 && row.state === "active")) {
      return {
        status: "replayed",
        canary_id: CLAIM_RECEIPT_CANARY_ID,
        topic: CLAIM_RECEIPT_TOPIC,
        count: CLAIM_RECEIPT_CANARY_SIZE,
        ledger_sha256: ledgerSha256,
      };
    }
    return { status: "conflict", code: "CLAIM_RECEIPT_CANARY_CONFLICT" };
  }
  return {
    status: "admitted",
    canary_id: CLAIM_RECEIPT_CANARY_ID,
    topic: CLAIM_RECEIPT_TOPIC,
    count: CLAIM_RECEIPT_CANARY_SIZE,
    ledger_sha256: ledgerSha256,
  };
}

export async function rollbackClaimReceiptCanary(
  db: D1Database,
  value: unknown,
): Promise<ClaimReceiptRollbackResult> {
  const request = parseClaimReceiptRollbackRequest(value);
  if (!await claimReceiptLedgerTableReady(db)) {
    throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_CONFLICT");
  }
  const rows = await allLedgerRows(db, request.canary_id);
  if (rows.length !== CLAIM_RECEIPT_CANARY_SIZE || rows.some((row) => row.ledger_sha256 !== request.ledger_sha256)) {
    throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_CONFLICT");
  }
  if (rows.every((row) => row.state === "rolled_back")) {
    return {
      schema_version: CLAIM_RECEIPT_ROLLBACK_SCHEMA,
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      ledger_sha256: request.ledger_sha256,
      status: "already_rolled_back",
      count: CLAIM_RECEIPT_CANARY_SIZE,
    };
  }
  if (rows.some((row) => row.state !== "active")) {
    throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_CONFLICT");
  }
  const updatedAt = new Date().toISOString();
  const [updateResult] = await db.batch([
    db.prepare(
      `UPDATE public_claim_receipts
          SET state = 'rolled_back', updated_at = ?
        WHERE canary_id = ? AND ledger_sha256 = ? AND state = 'active'`,
    ).bind(updatedAt, request.canary_id, request.ledger_sha256),
  ]);
  const changed = Number((updateResult as D1Result).meta?.changes ?? 0);
  if (changed === 0) {
    const replayRows = await allLedgerRows(db, request.canary_id);
    if (
      replayRows.length === CLAIM_RECEIPT_CANARY_SIZE
      && replayRows.every((row) => row.ledger_sha256 === request.ledger_sha256 && row.state === "rolled_back")
    ) {
      return {
        schema_version: CLAIM_RECEIPT_ROLLBACK_SCHEMA,
        canary_id: CLAIM_RECEIPT_CANARY_ID,
        ledger_sha256: request.ledger_sha256,
        status: "already_rolled_back",
        count: CLAIM_RECEIPT_CANARY_SIZE,
      };
    }
    throw new ClaimReceiptLedgerError(409, "CLAIM_RECEIPT_CANARY_CONFLICT");
  }
  if (changed !== CLAIM_RECEIPT_CANARY_SIZE) {
    throw new ClaimReceiptLedgerError(500, "CLAIM_RECEIPT_LEDGER_CORRUPT");
  }
  return {
    schema_version: CLAIM_RECEIPT_ROLLBACK_SCHEMA,
    canary_id: CLAIM_RECEIPT_CANARY_ID,
    ledger_sha256: request.ledger_sha256,
    status: "rolled_back",
    count: CLAIM_RECEIPT_CANARY_SIZE,
  };
}
