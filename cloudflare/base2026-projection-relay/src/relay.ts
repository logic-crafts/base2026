import { buildAuthCanonical, sha256Hex, verifyHmacHex } from "./crypto";
import {
  PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA,
  parsePublicProjection,
  parsePublicProjectionReceipt,
  parsePublicProjectionRollback,
  parsePublicProjectionVerifyRequest,
  parsePublicSourcePresenceReceipt,
  parsePublicSourcePresenceRequest,
  type PublicProjectionReceipt,
  type PublicProjectionRequest,
  type PublicProjectionRollbackRequest,
  type PublicProjectionVerifyRequest,
  type PublicSourcePresenceReceipt,
  type PublicSourcePresenceRequest,
} from "./public-contract";
import {
  EDITORIAL_EVIDENCE_GUIDE_SLUGS,
  validateEditorialPacket,
  type EditorialPacketValidation,
} from "./editorial-contract";

export const CROSS_ACCOUNT_PROJECTION_SCHEMA = "base2026.cross-account-projection.v1" as const;
export const CROSS_ACCOUNT_PROJECTION_RESPONSE_SCHEMA = "base2026.cross-account-projection-response.v1" as const;
export const MAX_RELAY_BODY_BYTES = 64 * 1024;
export const MAX_CLOCK_SKEW_SECONDS = 5 * 60;
export const RELAY_NONCE_TTL_SECONDS = 2 * MAX_CLOCK_SKEW_SECONDS;

export const RELAY_PATHS = Object.freeze({
  projection_apply: "/internal/base2026/projection/apply",
  projection_rollback: "/internal/base2026/projection/rollback",
  projection_presence: "/internal/base2026/projection/presence",
  projection_verify: "/internal/base2026/projection/verify",
  editorial_publish: "/internal/base2026/editorial/publish",
  editorial_inspect: "/internal/base2026/editorial/inspect",
} as const);

export type RelayOperation = keyof typeof RELAY_PATHS;

const RELAY_OPERATIONS = Object.keys(RELAY_PATHS) as RelayOperation[];
const ID_PATTERN = /^[a-f0-9]{40}$/u;
const HASH_PATTERN = /^[a-f0-9]{64}$/iu;
const SOURCE_ID_PATTERN = /^tiktok:[A-Za-z0-9._-]{2,256}:[0-9]{10,30}$/u;
const NONCE_PATTERN = /^[A-Za-z0-9._~-]{16,128}$/u;
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const SAFE_EDITORIAL_ISSUE_CODE = /^EDITORIAL_[A-Z0-9_]{1,80}$/u;
const SAFE_EDITORIAL_ISSUE_FIELD = /^[A-Za-z0-9_.\[\]-]{1,180}$/u;
const ISO_TIMESTAMP_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/u;
const AUTH_HEADER_NAMES = new Set([
  "x-base2026-timestamp",
  "x-base2026-nonce",
  "x-base2026-content-sha256",
  "x-base2026-content-length",
  "x-base2026-signature",
]);
const FORBIDDEN_CREDENTIAL_HEADERS = new Set([
  "authorization",
  "cookie",
  "proxy-authorization",
  "x-api-key",
  "x-auth-token",
]);

const DELETE_EXPIRED_NONCES_SQL =
  "DELETE FROM relay_nonces WHERE expires_at <= ?1";
const INSERT_NONCE_SQL = `INSERT OR IGNORE INTO relay_nonces
  (nonce_sha256, operation, idempotency_key, created_at, expires_at)
  VALUES (?1, ?2, ?3, ?4, ?5)`;
const INSERT_AUDIT_SQL = `INSERT OR IGNORE INTO relay_audit_receipts
  (receipt_id, nonce_sha256, operation, idempotency_key, request_sha256, outcome, result_sha256, created_at)
  VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`;

type RelayStatus = 400 | 401 | 404 | 405 | 409 | 413 | 422 | 500 | 502 | 503;

export class RelayError extends Error {
  constructor(readonly status: RelayStatus, readonly code: string) {
    super(code);
    this.name = "RelayError";
  }
}

export interface ProjectionTargetRpc {
  applyProjection(input: unknown): Promise<unknown>;
  rollbackProjection(input: unknown): Promise<unknown>;
  inspectPublicSource(input: unknown): Promise<unknown>;
  verifyProjection(input: unknown): Promise<unknown>;
  publishEditorialArticle(input: unknown, overwrite?: unknown): Promise<unknown>;
  inspectEditorialArticle(slug: string): Promise<unknown>;
}

/** Runtime bindings are optional here so a disabled/misconfigured relay fails closed. */
export interface RelayEnvironment {
  RELAY_DB?: D1Database;
  PUBLIC_PROJECTION_TARGET?: unknown;
  RELAY_HMAC_SECRET?: string;
  RELAY_ENABLED?: string;
}

interface RelayEnvelope {
  schema_version: typeof CROSS_ACCOUNT_PROJECTION_SCHEMA;
  operation: RelayOperation;
  idempotency_key: string;
  payload: Record<string, unknown>;
}

interface EditorialForwardMetadata {
  slug: string;
  kind: "source_based_article" | "engineering_note" | "evidence_guide";
  revision: number;
  payloadSha256: string;
}

interface ValidatedRelayPayload {
  payload: unknown;
  projection?: PublicProjectionRequest | PublicProjectionRollbackRequest | PublicSourcePresenceRequest | PublicProjectionVerifyRequest;
  editorial?: EditorialForwardMetadata;
}

interface EditorialReceipt {
  schema_version: "base2026.editorial-publication-receipt.v1";
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

interface EditorialPublishMetadata {
  slug: string;
  kind: EditorialForwardMetadata["kind"];
  revision: number;
  payloadSha256: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, required: readonly string[], optional: readonly string[] = [], code: string): void {
  const keys = Object.keys(value);
  if (keys.length !== required.length + optional.filter((key) => Object.hasOwn(value, key)).length
    || keys.some((key) => !required.includes(key) && !optional.includes(key))
    || required.some((key) => !Object.hasOwn(value, key))) {
    throw new RelayError(400, code);
  }
}

function header(request: Request, name: string): string {
  const value = request.headers.get(name);
  if (!value || value.trim() !== value) throw new RelayError(401, "relay_auth_headers_invalid");
  return value;
}

function parseUnsigned(value: string, code: string, max: number): number {
  if (!/^(?:0|[1-9]\d*)$/u.test(value)) throw new RelayError(400, code);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 0 || parsed > max) throw new RelayError(400, code);
  return parsed;
}

function parseTimestamp(value: string, nowMs: number): number {
  if (!/^(?:0|[1-9]\d{0,15})$/u.test(value)) throw new RelayError(401, "relay_timestamp_invalid");
  const timestamp = Number(value);
  if (!Number.isSafeInteger(timestamp) || timestamp <= 0) throw new RelayError(401, "relay_timestamp_invalid");
  const nowSeconds = Math.floor(nowMs / 1_000);
  if (!Number.isSafeInteger(nowSeconds) || Math.abs(nowSeconds - timestamp) > MAX_CLOCK_SKEW_SECONDS) {
    throw new RelayError(401, "relay_timestamp_skew");
  }
  return timestamp;
}

function validateNonce(value: string): string {
  if (!NONCE_PATTERN.test(value)) throw new RelayError(401, "relay_nonce_invalid");
  return value;
}

function validateHash(value: string, code: string): string {
  if (!HASH_PATTERN.test(value)) throw new RelayError(401, code);
  return value.toLowerCase();
}

function validateSourceId(value: string, code: string): string {
  if (!SOURCE_ID_PATTERN.test(value)) throw new RelayError(400, code);
  return value;
}

function validateSlug(value: unknown): string {
  if (typeof value !== "string" || value.length < 1 || value.length > 120
    || !SLUG_PATTERN.test(value) || /\d{8,}/u.test(value)) {
    throw new RelayError(400, "relay_editorial_slug_invalid");
  }
  return value;
}

function operationForPath(pathname: string): RelayOperation | null {
  for (const operation of RELAY_OPERATIONS) {
    if (RELAY_PATHS[operation] === pathname) return operation;
  }
  return null;
}

async function readBody(request: Request): Promise<Uint8Array> {
  const declared = request.headers.get("content-length");
  if (declared !== null) {
    const length = parseUnsigned(declared, "relay_http_content_length_invalid", Number.MAX_SAFE_INTEGER);
    if (length > MAX_RELAY_BODY_BYTES) throw new RelayError(413, "relay_body_too_large");
  }
  if (!request.body) return new Uint8Array();
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      const chunk = next.value;
      total += chunk.byteLength;
      if (total > MAX_RELAY_BODY_BYTES) {
        await reader.cancel().catch(() => undefined);
        throw new RelayError(413, "relay_body_too_large");
      }
      chunks.push(new Uint8Array(chunk));
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

function decodeUtf8(body: Uint8Array): string {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(body);
  } catch {
    throw new RelayError(400, "relay_body_encoding_invalid");
  }
}

function parseEnvelope(value: unknown, pathname: string): RelayEnvelope {
  if (!isRecord(value)) throw new RelayError(400, "relay_envelope_invalid");
  exactKeys(value, ["schema_version", "operation", "idempotency_key", "payload"], [], "relay_envelope_fields_invalid");
  if (value.schema_version !== CROSS_ACCOUNT_PROJECTION_SCHEMA) {
    throw new RelayError(400, "relay_schema_invalid");
  }
  if (typeof value.operation !== "string" || !RELAY_OPERATIONS.includes(value.operation as RelayOperation)) {
    throw new RelayError(400, "relay_operation_invalid");
  }
  const operation = value.operation as RelayOperation;
  if (RELAY_PATHS[operation] !== pathname) throw new RelayError(400, "relay_operation_path_mismatch");
  if (typeof value.idempotency_key !== "string" || !ID_PATTERN.test(value.idempotency_key)) {
    throw new RelayError(400, "relay_idempotency_key_invalid");
  }
  if (!isRecord(value.payload)) throw new RelayError(400, "relay_payload_invalid");
  return {
    schema_version: CROSS_ACCOUNT_PROJECTION_SCHEMA,
    operation,
    idempotency_key: value.idempotency_key,
    payload: value.payload,
  };
}

function publicProjectionPayload(payload: Record<string, unknown>): ValidatedRelayPayload {
  try {
    const projection = parsePublicProjection(payload);
    return { payload: projection, projection };
  } catch {
    throw new RelayError(400, "relay_projection_payload_invalid");
  }
}

function publicRollbackPayload(payload: Record<string, unknown>): ValidatedRelayPayload {
  try {
    const rollback = parsePublicProjectionRollback(payload);
    validateSourceId(rollback.source_id, "relay_source_id_invalid");
    return { payload: rollback, projection: rollback };
  } catch (error) {
    if (error instanceof RelayError) throw error;
    throw new RelayError(400, "relay_rollback_payload_invalid");
  }
}

function publicPresencePayload(payload: Record<string, unknown>): ValidatedRelayPayload {
  try {
    const presence = parsePublicSourcePresenceRequest(payload);
    return { payload: presence, projection: presence };
  } catch {
    throw new RelayError(400, "relay_presence_payload_invalid");
  }
}

function publicVerifyPayload(payload: Record<string, unknown>): ValidatedRelayPayload {
  try {
    const verify = parsePublicProjectionVerifyRequest(payload);
    return { payload: verify, projection: verify };
  } catch {
    throw new RelayError(400, "relay_verify_payload_invalid");
  }
}

function validateOverwrite(value: unknown): { expected_revision: number; expected_payload_sha256: string } {
  if (!isRecord(value)) throw new RelayError(400, "relay_editorial_overwrite_invalid");
  exactKeys(value, ["expected_revision", "expected_payload_sha256"], [], "relay_editorial_overwrite_fields_invalid");
  if (typeof value.expected_revision !== "number" || !Number.isSafeInteger(value.expected_revision)
    || value.expected_revision < 1) throw new RelayError(400, "relay_editorial_overwrite_invalid");
  if (typeof value.expected_payload_sha256 !== "string" || !HASH_PATTERN.test(value.expected_payload_sha256)) {
    throw new RelayError(400, "relay_editorial_overwrite_invalid");
  }
  return {
    expected_revision: value.expected_revision,
    expected_payload_sha256: value.expected_payload_sha256.toLowerCase(),
  };
}

async function editorialPublishPayload(payload: Record<string, unknown>, nowMs: number): Promise<ValidatedRelayPayload> {
  exactKeys(payload, ["packet"], ["overwrite"], "relay_editorial_payload_fields_invalid");
  let checked: EditorialPacketValidation;
  try {
    checked = await validateEditorialPacket(payload.packet, new Date(nowMs).toISOString());
  } catch {
    throw new RelayError(400, "relay_editorial_packet_invalid");
  }
  if (!checked.ok) throw new RelayError(400, "relay_editorial_packet_invalid");
  const overwrite = Object.hasOwn(payload, "overwrite") ? validateOverwrite(payload.overwrite) : undefined;
  const packet = payload.packet;
  if (!isRecord(packet)) throw new RelayError(400, "relay_editorial_packet_invalid");
  return {
    payload: {
      packet,
      ...(overwrite === undefined ? {} : { overwrite }),
    },
    editorial: {
      slug: validateSlug(checked.payload.slug),
      kind: checked.payload.kind,
      revision: checked.payload.revision,
      payloadSha256: checked.payload_sha256,
    },
  };
}

function editorialInspectPayload(payload: Record<string, unknown>): ValidatedRelayPayload {
  exactKeys(payload, ["slug"], [], "relay_editorial_inspect_fields_invalid");
  return { payload: { slug: validateSlug(payload.slug) } };
}

async function validatePayload(operation: RelayOperation, payload: Record<string, unknown>, nowMs: number): Promise<ValidatedRelayPayload> {
  switch (operation) {
    case "projection_apply": return publicProjectionPayload(payload);
    case "projection_rollback": return publicRollbackPayload(payload);
    case "projection_presence": return publicPresencePayload(payload);
    case "projection_verify": return publicVerifyPayload(payload);
    case "editorial_publish": return editorialPublishPayload(payload, nowMs);
    case "editorial_inspect": return editorialInspectPayload(payload);
  }
}

function receiptTimestamp(value: unknown): string {
  if (typeof value !== "string" || !ISO_TIMESTAMP_PATTERN.test(value) || new Date(value).toISOString() !== value) {
    throw new RelayError(502, "relay_target_receipt_invalid");
  }
  return value;
}

function receipt(value: unknown, expected: {
  projectionId?: string;
  sourceId: string;
  manifestSha256?: string;
  contentSha256?: string;
  status?: "applied" | "rolled_back";
  cardCount?: number;
}): PublicProjectionReceipt {
  let parsed: PublicProjectionReceipt;
  try {
    parsed = parsePublicProjectionReceipt(value);
  } catch {
    throw new RelayError(502, "relay_target_receipt_invalid");
  }
  if (parsed.source_id !== expected.sourceId
    || (expected.projectionId !== undefined && parsed.projection_id !== expected.projectionId)
    || (expected.manifestSha256 !== undefined && parsed.manifest_sha256 !== expected.manifestSha256)
    || (expected.contentSha256 !== undefined && parsed.content_sha256 !== expected.contentSha256)
    || (expected.status !== undefined && parsed.status !== expected.status)
    || (expected.cardCount !== undefined && parsed.card_count !== expected.cardCount)
    || parsed.row_count !== parsed.card_count) {
    throw new RelayError(502, "relay_target_receipt_mismatch");
  }
  return parsed;
}

function validateProjectionResult(operation: RelayOperation, result: unknown, request: ValidatedRelayPayload): { result: unknown; outcome: string } {
  if (operation === "projection_apply" && request.projection && "cards" in request.projection) {
    const input = request.projection;
    const parsed = receipt(result, {
      projectionId: input.projection_id,
      sourceId: input.source.source_id,
      manifestSha256: input.manifest_sha256,
      contentSha256: input.content_sha256,
      status: "applied",
      cardCount: input.cards.length,
    });
    return { result: parsed, outcome: "applied" };
  }
  if (operation === "projection_rollback" && request.projection
    && "projection_id" in request.projection && "source_id" in request.projection
    && "manifest_sha256" in request.projection && "content_sha256" in request.projection) {
    const input = request.projection;
    const parsed = receipt(result, {
      projectionId: input.projection_id,
      sourceId: input.source_id,
      manifestSha256: input.manifest_sha256,
      contentSha256: input.content_sha256,
      status: "rolled_back",
      cardCount: 0,
    });
    return { result: parsed, outcome: "rolled_back" };
  }
  if (operation === "projection_presence" && request.projection && "source_id" in request.projection) {
    let parsed: PublicSourcePresenceReceipt;
    try { parsed = parsePublicSourcePresenceReceipt(result); }
    catch { throw new RelayError(502, "relay_target_presence_invalid"); }
    if (parsed.schema_version !== PUBLIC_SOURCE_PRESENCE_RECEIPT_SCHEMA
      || parsed.source_id !== request.projection.source_id) {
      throw new RelayError(502, "relay_target_presence_mismatch");
    }
    return { result: parsed, outcome: "presence" };
  }
  if (operation === "projection_verify" && request.projection
    && "projection_id" in request.projection && "source_id" in request.projection
    && "manifest_sha256" in request.projection && "content_sha256" in request.projection) {
    const input = request.projection;
    const parsed = receipt(result, {
      projectionId: input.projection_id,
      sourceId: input.source_id,
      manifestSha256: input.manifest_sha256,
      contentSha256: input.content_sha256,
      status: "applied",
    });
    if (parsed.card_count < 1 || parsed.card_count > 3) throw new RelayError(502, "relay_target_receipt_invalid");
    return { result: parsed, outcome: "verified" };
  }
  throw new RelayError(502, "relay_target_result_invalid");
}

function editorialReceipt(value: unknown, slug: string, kind?: EditorialForwardMetadata["kind"], revision?: number, payloadSha256?: string): EditorialReceipt {
  if (!isRecord(value)) throw new RelayError(502, "relay_editorial_receipt_invalid");
  exactKeys(value, ["schema_version", "slug", "revision", "payload_sha256", "public_path", "published_at", "updated_at", "reviewer", "reviewed_at", "recorded_at"], [], "relay_editorial_receipt_invalid");
  const path = kind === "evidence_guide" ? `/topics/${slug}` : `/blog/${slug}/`;
  if (value.schema_version !== "base2026.editorial-publication-receipt.v1"
    || value.slug !== slug || value.public_path !== path || value.reviewer !== "sol-max"
    || typeof value.revision !== "number" || !Number.isSafeInteger(value.revision) || value.revision < 1
    || (revision !== undefined && value.revision !== revision)
    || typeof value.payload_sha256 !== "string" || !HASH_PATTERN.test(value.payload_sha256)
    || (payloadSha256 !== undefined && value.payload_sha256 !== payloadSha256)) {
    throw new RelayError(502, "relay_editorial_receipt_mismatch");
  }
  const publishedAt = receiptTimestamp(value.published_at);
  const updatedAt = receiptTimestamp(value.updated_at);
  const reviewedAt = receiptTimestamp(value.reviewed_at);
  const recordedAt = receiptTimestamp(value.recorded_at);
  return {
    schema_version: "base2026.editorial-publication-receipt.v1",
    slug,
    revision: value.revision,
    payload_sha256: value.payload_sha256,
    public_path: path,
    published_at: publishedAt,
    updated_at: updatedAt,
    reviewer: "sol-max",
    reviewed_at: reviewedAt,
    recorded_at: recordedAt,
  };
}

function editorialDiagnostics(value: unknown): Record<string, number> {
  if (!isRecord(value)) throw new RelayError(502, "relay_editorial_diagnostics_invalid");
  const keys = ["source_count", "distinct_source_urls", "distinct_source_metadata", "known_creator_count", "sources_without_known_creator", "cited_source_count", "section_count"] as const;
  exactKeys(value, keys, [], "relay_editorial_diagnostics_invalid");
  const result: Record<string, number> = {};
  for (const key of keys) {
    const count = value[key];
    if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 0 || count > 128) {
      throw new RelayError(502, "relay_editorial_diagnostics_invalid");
    }
    result[key] = count;
  }
  return result;
}

function editorialPublishResult(value: unknown, metadata: EditorialPublishMetadata): unknown {
  if (!isRecord(value)) throw new RelayError(502, "relay_editorial_result_invalid");
  if (value.ok === true && (value.status === "published" || value.status === "already_published")) {
    exactKeys(value, ["ok", "status", "receipt", "diagnostics"], [], "relay_editorial_result_invalid");
    return {
      ok: true,
      status: value.status,
      receipt: editorialReceipt(value.receipt, metadata.slug, metadata.kind, metadata.revision, metadata.payloadSha256),
      diagnostics: editorialDiagnostics(value.diagnostics),
    };
  }
  if (value.ok === false && value.status === "conflict") {
    exactKeys(value, ["ok", "status", "code", "current_revision", "current_payload_sha256"], [], "relay_editorial_result_invalid");
    if (value.code !== "EDITORIAL_REVISION_CONFLICT"
      || (value.current_revision !== null && (typeof value.current_revision !== "number" || !Number.isSafeInteger(value.current_revision) || value.current_revision < 1))
      || (value.current_payload_sha256 !== null && (typeof value.current_payload_sha256 !== "string" || !HASH_PATTERN.test(value.current_payload_sha256)))
      || (value.current_revision === null) !== (value.current_payload_sha256 === null)) {
      throw new RelayError(502, "relay_editorial_result_invalid");
    }
    return {
      ok: false,
      status: "conflict",
      code: "EDITORIAL_REVISION_CONFLICT",
      current_revision: value.current_revision,
      current_payload_sha256: value.current_payload_sha256,
    };
  }
  if (value.ok === false && value.status === "rejected") {
    exactKeys(value, ["ok", "status", "issues"], [], "relay_editorial_result_invalid");
    if (!Array.isArray(value.issues) || value.issues.length < 1 || value.issues.length > 8) {
      throw new RelayError(502, "relay_editorial_result_invalid");
    }
    const issues = value.issues.map((issue) => {
      if (!isRecord(issue)) throw new RelayError(502, "relay_editorial_result_invalid");
      exactKeys(issue, ["code", "field"], [], "relay_editorial_result_invalid");
      if (typeof issue.code !== "string" || !SAFE_EDITORIAL_ISSUE_CODE.test(issue.code)
        || typeof issue.field !== "string" || !SAFE_EDITORIAL_ISSUE_FIELD.test(issue.field)) {
        throw new RelayError(502, "relay_editorial_result_invalid");
      }
      return { code: issue.code, field: issue.field };
    });
    return { ok: false, status: "rejected", issues };
  }
  throw new RelayError(502, "relay_editorial_result_invalid");
}

function editorialInspectResult(value: unknown, slug: string): unknown {
  if (!isRecord(value)) throw new RelayError(502, "relay_editorial_inspect_invalid");
  if (value.ok === false) {
    exactKeys(value, ["ok", "code"], [], "relay_editorial_inspect_invalid");
    if (value.code !== "NOT_FOUND") throw new RelayError(502, "relay_editorial_inspect_invalid");
    return { ok: false, code: "NOT_FOUND" };
  }
  if (value.ok === true) {
    exactKeys(value, ["ok", "receipt"], [], "relay_editorial_inspect_invalid");
    if (!isRecord(value.receipt) || typeof value.receipt.public_path !== "string") {
      throw new RelayError(502, "relay_editorial_inspect_invalid");
    }
    const evidenceGuide = EDITORIAL_EVIDENCE_GUIDE_SLUGS.includes(slug);
    const expectedPath = evidenceGuide ? `/topics/${slug}` : `/blog/${slug}/`;
    if (value.receipt.public_path !== expectedPath) throw new RelayError(502, "relay_editorial_inspect_mismatch");
    const kind = evidenceGuide ? "evidence_guide" : "source_based_article";
    return { ok: true, receipt: editorialReceipt(value.receipt, slug, kind) };
  }
  throw new RelayError(502, "relay_editorial_inspect_invalid");
}

async function callTarget(target: ProjectionTargetRpc, operation: RelayOperation, payload: ValidatedRelayPayload): Promise<unknown> {
  switch (operation) {
    case "projection_apply": return target.applyProjection(payload.payload);
    case "projection_rollback": return target.rollbackProjection(payload.payload);
    case "projection_presence": return target.inspectPublicSource(payload.payload);
    case "projection_verify": return target.verifyProjection(payload.payload);
    case "editorial_publish": {
      if (!isRecord(payload.payload)) throw new RelayError(502, "relay_target_result_invalid");
      return target.publishEditorialArticle(payload.payload.packet, payload.payload.overwrite);
    }
    case "editorial_inspect": {
      if (!isRecord(payload.payload)) throw new RelayError(502, "relay_target_result_invalid");
      return target.inspectEditorialArticle(String(payload.payload.slug));
    }
  }
}

function targetSupports(target: unknown, operation: RelayOperation): target is ProjectionTargetRpc {
  if (!isRecord(target)) return false;
  switch (operation) {
    case "projection_apply": return typeof target.applyProjection === "function";
    case "projection_rollback": return typeof target.rollbackProjection === "function";
    case "projection_presence": return typeof target.inspectPublicSource === "function";
    case "projection_verify": return typeof target.verifyProjection === "function";
    case "editorial_publish": return typeof target.publishEditorialArticle === "function";
    case "editorial_inspect": return typeof target.inspectEditorialArticle === "function";
  }
}

async function reserveNonce(db: D1Database, nonceSha256: string, operation: RelayOperation, idempotencyKey: string, nowSeconds: number): Promise<boolean> {
  let results: D1Result[];
  try {
    results = await db.batch([
      db.prepare(DELETE_EXPIRED_NONCES_SQL).bind(nowSeconds),
      db.prepare(INSERT_NONCE_SQL).bind(nonceSha256, operation, idempotencyKey, nowSeconds, nowSeconds + RELAY_NONCE_TTL_SECONDS),
    ]);
  } catch {
    throw new RelayError(503, "relay_replay_store_unavailable");
  }
  if (!Array.isArray(results) || results.length !== 2 || !results[1]?.success) {
    throw new RelayError(503, "relay_replay_store_unavailable");
  }
  return Number(results[1].meta?.changes ?? 0) === 1;
}

async function audit(db: D1Database, input: {
  nonceSha256: string;
  operation: RelayOperation;
  idempotencyKey: string;
  requestSha256: string;
  outcome: string;
  resultSha256: string | null;
  nowSeconds: number;
}): Promise<void> {
  const receiptId = await sha256Hex([
    "base2026-projection-relay-audit",
    input.nonceSha256,
    input.operation,
    input.idempotencyKey,
    input.outcome,
    input.resultSha256 ?? "",
    String(input.nowSeconds),
  ].join("\u001f"));
  try {
    const result = await db.prepare(INSERT_AUDIT_SQL).bind(
      receiptId,
      input.nonceSha256,
      input.operation,
      input.idempotencyKey,
      input.requestSha256,
      input.outcome,
      input.resultSha256,
      input.nowSeconds,
    ).run();
    if (!result.success) throw new Error("audit");
  } catch {
    throw new RelayError(503, "relay_audit_unavailable");
  }
}

function stableJson(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new RelayError(502, "relay_result_invalid");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map((item) => stableJson(item)).join(",")}]`;
  if (isRecord(value)) {
    return `{${Object.keys(value).sort().map((key) => {
      if (value[key] === undefined) throw new RelayError(502, "relay_result_invalid");
      return `${JSON.stringify(key)}:${stableJson(value[key])}`;
    }).join(",")}}`;
  }
  throw new RelayError(502, "relay_result_invalid");
}

function errorResponse(error: RelayError): Response {
  return Response.json({ code: error.code }, {
    status: error.status,
    headers: {
      "cache-control": "no-store",
      "content-type": "application/json; charset=utf-8",
      "x-content-type-options": "nosniff",
    },
  });
}

function successResponse(operation: RelayOperation, idempotencyKey: string, result: unknown): Response {
  return Response.json({
    schema_version: CROSS_ACCOUNT_PROJECTION_RESPONSE_SCHEMA,
    operation,
    idempotency_key: idempotencyKey,
    result,
  }, {
    status: 200,
    headers: {
      "cache-control": "no-store",
      "content-type": "application/json; charset=utf-8",
      "x-content-type-options": "nosniff",
    },
  });
}

function asRelayError(error: unknown): RelayError {
  return error instanceof RelayError ? error : new RelayError(503, "relay_unavailable");
}

/**
 * Authenticated target-account ingress. It never logs request data and never
 * constructs a URL or SQL statement from caller-controlled input.
 */
export async function handleRelayRequest(request: Request, env: RelayEnvironment, nowMs = Date.now()): Promise<Response> {
  try {
    if (env.RELAY_ENABLED !== "true") throw new RelayError(404, "relay_disabled");
    const url = new URL(request.url);
    if (url.search) throw new RelayError(400, "relay_query_not_allowed");
    const operation = operationForPath(url.pathname);
    if (!operation) throw new RelayError(404, "relay_path_not_found");
    if (request.method !== "POST") throw new RelayError(405, "relay_method_not_allowed");
    if (request.headers.get("content-type") !== "application/json") {
      throw new RelayError(400, "relay_content_type_invalid");
    }
    request.headers.forEach((_value, name) => {
      if (FORBIDDEN_CREDENTIAL_HEADERS.has(name)
        || (name.startsWith("x-base2026-") && !AUTH_HEADER_NAMES.has(name))) {
        throw new RelayError(400, "relay_headers_invalid");
      }
    });

    const body = await readBody(request);
    if (body.byteLength < 1) throw new RelayError(400, "relay_body_empty");
    const bodyText = decodeUtf8(body);
    const contentSha256 = await sha256Hex(body);
    const declaredSha256 = validateHash(header(request, "x-base2026-content-sha256"), "relay_content_hash_invalid");
    if (declaredSha256 !== contentSha256) throw new RelayError(401, "relay_content_hash_mismatch");
    const declaredLength = parseUnsigned(header(request, "x-base2026-content-length"), "relay_content_length_invalid", MAX_RELAY_BODY_BYTES);
    if (declaredLength !== body.byteLength) throw new RelayError(401, "relay_content_length_mismatch");
    const timestampHeader = header(request, "x-base2026-timestamp");
    parseTimestamp(timestampHeader, nowMs);
    const nonce = validateNonce(header(request, "x-base2026-nonce"));
    const signature = header(request, "x-base2026-signature");
    const secret = env.RELAY_HMAC_SECRET;
    if (typeof secret !== "string" || secret.length < 32) throw new RelayError(503, "relay_secret_unavailable");
    const canonical = buildAuthCanonical({
      method: request.method,
      pathname: url.pathname,
      timestamp: timestampHeader,
      nonce,
      contentSha256,
      contentLength: body.byteLength,
    });
    if (!await verifyHmacHex(secret, canonical, signature)) throw new RelayError(401, "relay_signature_invalid");

    let decoded: unknown;
    try { decoded = JSON.parse(bodyText) as unknown; }
    catch { throw new RelayError(400, "relay_json_invalid"); }
    const envelope = parseEnvelope(decoded, url.pathname);
    const validated = await validatePayload(envelope.operation, envelope.payload, nowMs);
    if (!targetSupports(env.PUBLIC_PROJECTION_TARGET, envelope.operation)) {
      throw new RelayError(503, "relay_target_unavailable");
    }
    if (!env.RELAY_DB) throw new RelayError(503, "relay_replay_store_unavailable");
    const nowSeconds = Math.floor(nowMs / 1_000);
    if (!Number.isSafeInteger(nowSeconds) || nowSeconds < 1) throw new RelayError(503, "relay_clock_unavailable");
    const nonceSha256 = await sha256Hex(nonce);
    const reserved = await reserveNonce(env.RELAY_DB, nonceSha256, envelope.operation, envelope.idempotency_key, nowSeconds);
    if (!reserved) {
      await audit(env.RELAY_DB, {
        nonceSha256, operation: envelope.operation, idempotencyKey: envelope.idempotency_key,
        requestSha256: contentSha256, outcome: "replay_rejected", resultSha256: null, nowSeconds,
      }).catch(() => undefined);
      throw new RelayError(409, "relay_nonce_replay");
    }

    let targetResult: unknown;
    try { targetResult = await callTarget(env.PUBLIC_PROJECTION_TARGET, envelope.operation, validated); }
    catch {
      await audit(env.RELAY_DB, {
        nonceSha256, operation: envelope.operation, idempotencyKey: envelope.idempotency_key,
        requestSha256: contentSha256, outcome: "target_unconfirmed", resultSha256: null, nowSeconds,
      }).catch(() => undefined);
      throw new RelayError(503, "relay_target_unconfirmed");
    }

    let checked: { result: unknown; outcome: string };
    try {
      if (envelope.operation.startsWith("projection_")) {
        checked = validateProjectionResult(envelope.operation, targetResult, validated);
      } else if (envelope.operation === "editorial_publish" && validated.editorial) {
        checked = {
          result: editorialPublishResult(targetResult, validated.editorial),
          outcome: "editorial_published",
        };
      } else if (envelope.operation === "editorial_inspect") {
        if (!isRecord(validated.payload) || typeof validated.payload.slug !== "string") {
          throw new RelayError(502, "relay_target_result_invalid");
        }
        checked = { result: editorialInspectResult(targetResult, validated.payload.slug), outcome: "editorial_inspected" };
      } else {
        throw new RelayError(502, "relay_target_result_invalid");
      }
    } catch (error) {
      await audit(env.RELAY_DB, {
        nonceSha256, operation: envelope.operation, idempotencyKey: envelope.idempotency_key,
        requestSha256: contentSha256, outcome: "target_rejected", resultSha256: null, nowSeconds,
      }).catch(() => undefined);
      throw asRelayError(error);
    }

    const resultSha256 = await sha256Hex(stableJson(checked.result));
    await audit(env.RELAY_DB, {
      nonceSha256, operation: envelope.operation, idempotencyKey: envelope.idempotency_key,
      requestSha256: contentSha256, outcome: checked.outcome, resultSha256, nowSeconds,
    });
    return successResponse(envelope.operation, envelope.idempotency_key, checked.result);
  } catch (error) {
    return errorResponse(asRelayError(error));
  }
}

export {
  DELETE_EXPIRED_NONCES_SQL,
  INSERT_AUDIT_SQL,
  INSERT_NONCE_SQL,
};
