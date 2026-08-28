#!/usr/bin/env node

/*
 * Import the reviewed local Outreach JSONL bundle into bounded SQL files.
 *
 * This script intentionally has no D1, Wrangler, network, or workbook
 * dependency.  It validates the exporter contract, writes idempotent
 * upserts/link-table refreshes, and emits a deterministic receipt.  A caller
 * must execute the generated SQL separately in an explicitly authorised
 * local/preview database.
 */

import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { join, resolve, sep } from "node:path";
import { isIP } from "node:net";
import { createHash } from "node:crypto";
import { dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const WORKER_ROOT = resolve(SCRIPT_DIR, "..");
const MIGRATION_RELATIVE_PATH = "migrations-outreach/0001_outreach_search.sql";
const MIGRATION_PATH = resolve(WORKER_ROOT, MIGRATION_RELATIVE_PATH);

export const COLLECTION = "outreach_findings";
export const RECORD_TYPE = "finding";
export const PUBLIC_POLICY = "reviewed_outreach_excerpt_v1";
export const LANGUAGE = "ru";
export const EXPORT_SCHEMA = "base2026-outreach-jsonl-v1";
export const IMPORT_SCHEMA = "base2026-outreach-d1-import-v1";
export const RECEIPT_FILE = "receipt.json";

export const BUNDLE_FILES = Object.freeze([
  "outreach_records.jsonl",
  "outreach_rejects.jsonl",
  "manifest.json",
]);

export const PUBLIC_RECORD_FIELDS = Object.freeze([
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
]);

export const SQL_COLUMNS = Object.freeze([
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
]);

export const REQUIRED_SOURCE_HEADERS = Object.freeze([
  "source_id",
  "title",
  "summary",
  "tactic",
  "evidence",
  "verdict",
  "source_url",
  "platform",
  "author_display_name",
  "author_handle",
  "observed_at",
  "score",
  "status",
  "topics",
  "lane_tokens",
  "cost",
  "complexity",
  "effect_speed",
  "language",
]);

export const MANIFEST_FIELDS = Object.freeze([
  "schema",
  "collection",
  "tab",
  "deterministic",
  "hash_algorithm",
  "input_sha256",
  "input_hash",
  "canonical_input_sha256",
  "admission_sha256",
  "records_sha256",
  "rejects_sha256",
  "input_rows",
  "admission_entries",
  "record_count",
  "reject_count",
  "records",
  "rejects",
  "counts",
  "rejection_counts",
  "required_headers",
  "public_fields",
  "files",
]);

export const DEFAULT_BATCH_SIZE = 100;
export const DEFAULT_MAX_SQL_BYTES = 256 * 1024;
export const DEFAULT_MAX_ROWS = 10_000;
export const MAX_INPUT_BYTES = 64 * 1024 * 1024;
export const MAX_BUNDLE_BYTES = 128 * 1024 * 1024;
export const MAX_LINE_BYTES = 2 * 1024 * 1024;
export const MAX_ID_LENGTH = 256;
export const MAX_URL_LENGTH = 2_048;
export const MAX_TEXT_LENGTH = 100_000;
export const MAX_LIST_ITEMS = 32;
export const MAX_LIST_ITEM_LENGTH = 120;
export const MAX_PUBLIC_TEXT_TOTAL = 8_000;
export const MIN_SCORE = 65;

const PUBLIC_TEXT_LIMITS = Object.freeze({
  title: 300,
  summary: 1_200,
  tactic: 1_500,
  evidence_summary: 2_000,
  verdict: 1_200,
  platform: 100,
  author_name: 300,
  author_handle: 300,
  observed_at: 100,
  source_status: 100,
  cost: 200,
  complexity: 200,
  effect_speed: 200,
  language: 20,
});

const SOURCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$/u;
const SHA256_RE = /^[a-f0-9]{64}$/u;
const CONTROL_RE = /[\u0000-\u001f\u007f]/u;
const EMAIL_RE = /(?<![\p{L}\p{N}\p{M}_.+%-])[\p{L}\p{N}\p{M}_.%+-]+@(?:[\p{L}\p{N}\p{M}-]+\.)+(?=[\p{L}\p{N}\p{M}-]*\p{L})[\p{L}\p{N}\p{M}-]+(?![\p{L}\p{N}\p{M}-])/iu;
const PHONE_CANDIDATE_RE = /(?<!\w)(?:\+?\s*)?(?:\(\d{1,4}\)|\d{1,4})[\d().\s-]{4,}\d(?!\w)/gu;
const TRACKING_QUERY_RE = /^utm_/iu;
const MALFORMED_PERCENT_RE = /%(?![0-9A-Fa-f]{2})/u;
const TRACKING_QUERY_NAMES = new Set([
  "fbclid",
  "gclid",
  "dclid",
  "gbraid",
  "wbraid",
  "msclkid",
  "mc_cid",
  "mc_eid",
  "ref",
  "referrer",
  "source",
  "igshid",
  "yclid",
  "vero_id",
]);
const FORBIDDEN_FIELD_RE = /(followers?|next[_ ]?action|private|formula|contact|email|client|queue|outreach[_ ]?(status|log)|owner|internal|credential|secret|token|cookie|password)/iu;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/u;
const TIMESTAMP_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/u;

export class ImportInputError extends Error {
  constructor(message) {
    super(message);
    this.name = "ImportInputError";
  }
}

function fail(message) {
  throw new ImportInputError(message);
}

function assertObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    fail(`${label} must be an object`);
  }
}

function exactKeys(value, expected, label) {
  assertObject(value, label);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    const unknown = actual.filter((key) => !wanted.includes(key));
    const missing = wanted.filter((key) => !actual.includes(key));
    const detail = [
      unknown.length ? `unknown=${unknown.join(",")}` : "",
      missing.length ? `missing=${missing.join(",")}` : "",
    ].filter(Boolean).join("; ");
    fail(`${label} has an invalid field allowlist${detail ? ` (${detail})` : ""}`);
  }
}

function assertSafeText(value, field, { required = true, max = MAX_TEXT_LENGTH } = {}) {
  if (typeof value !== "string") fail(`${field} must be a string`);
  if (value.length > max) fail(`${field} exceeds ${max} characters`);
  if (CONTROL_RE.test(value)) fail(`${field} contains a control character`);
  if (required && value.length === 0) fail(`${field} is required`);
  return value;
}

function assertHash(value, field) {
  assertSafeText(value, field, { max: 64 });
  if (!SHA256_RE.test(value)) fail(`${field} must be lowercase SHA-256 hexadecimal`);
  return value;
}

function assertInteger(value, field, min, max) {
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    fail(`${field} must be an integer between ${min} and ${max}`);
  }
  return value;
}

function assertFiniteScore(value) {
  if (typeof value !== "number" || typeof value === "boolean" || !Number.isFinite(value)) {
    fail("score must be a finite number");
  }
  if (value < MIN_SCORE) fail(`score must be >= ${MIN_SCORE}`);
  return value;
}

function assertValidDate(value, field, { timestamp = false } = {}) {
  assertSafeText(value, field, { max: 32 });
  if (timestamp && !TIMESTAMP_RE.test(value)) {
    fail(`${field} must be a UTC ISO timestamp with seconds`);
  }
  if (!timestamp && !DATE_RE.test(value) && !TIMESTAMP_RE.test(value)) {
    fail(`${field} must be an ISO date or UTC ISO timestamp with seconds`);
  }
  const date = new Date(`${DATE_RE.test(value) ? `${value}T00:00:00Z` : value}`);
  if (Number.isNaN(date.getTime())) fail(`${field} is not a valid calendar date`);
  if (DATE_RE.test(value)) {
    const [year, month, day] = value.split("-").map(Number);
    if (date.getUTCFullYear() !== year || date.getUTCMonth() + 1 !== month || date.getUTCDate() !== day) {
      fail(`${field} is not a valid calendar date`);
    }
  } else if (date.toISOString().replace(".000Z", "Z") !== value) {
    fail(`${field} is not a valid calendar timestamp`);
  }
  return value;
}

function publicHostname(url) {
  const hostname = url.hostname.toLowerCase().replace(/\.$/u, "");
  const ipKind = isIP(hostname.replace(/^\[|\]$/gu, ""));
  if (ipKind === 4 || ipKind === 6) return false;
  if (!hostname || !hostname.includes(".")) return false;
  if (hostname === "localhost" || hostname.endsWith(".localhost")) return false;
  if (hostname.endsWith(".local") || hostname.endsWith(".internal") || hostname.endsWith(".lan") || hostname.endsWith(".home") || hostname.endsWith(".test") || hostname.endsWith(".invalid")) return false;
  return true;
}

function whatwgFormQuote(value) {
  const safe = new Set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789*-._".split("").map((character) => character.codePointAt(0)));
  return [...new TextEncoder().encode(value)].map((byte) => {
    if (safe.has(byte)) return String.fromCodePoint(byte);
    if (byte === 0x20) return "+";
    return `%${byte.toString(16).toUpperCase().padStart(2, "0")}`;
  }).join("");
}

export function normalizePublicUrl(value) {
  assertSafeText(value, "source_url", { max: MAX_URL_LENGTH });
  if (/\s/u.test(value)) fail("source_url must not contain whitespace");
  if (MALFORMED_PERCENT_RE.test(value)) fail("source_url has malformed percent encoding");
  let url;
  try {
    url = new URL(value);
  } catch {
    fail("source_url is not a valid URL");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") fail("source_url must use http or https");
  if (url.username || url.password) fail("source_url credentials are forbidden");
  if (!publicHostname(url)) fail("source_url must use a public host");

  const retained = [];
  for (const [key, queryValue] of url.searchParams.entries()) {
    const lowered = key.toLowerCase();
    if (TRACKING_QUERY_RE.test(lowered) || TRACKING_QUERY_NAMES.has(lowered)) continue;
    retained.push([key, queryValue]);
  }
  retained.sort((left, right) => {
    const leftKey = whatwgFormQuote(left[0]);
    const rightKey = whatwgFormQuote(right[0]);
    if (leftKey < rightKey) return -1;
    if (leftKey > rightKey) return 1;
    const leftValue = whatwgFormQuote(left[1]);
    const rightValue = whatwgFormQuote(right[1]);
    return leftValue < rightValue ? -1 : leftValue > rightValue ? 1 : 0;
  });
  url.search = retained.length
    ? `?${retained.map(([key, queryValue]) => `${whatwgFormQuote(key)}=${whatwgFormQuote(queryValue)}`).join("&")}`
    : "";
  url.hash = "";
  if (!url.pathname) url.pathname = "/";
  return url.toString();
}

function assertCanonicalUrl(value) {
  const normalized = normalizePublicUrl(value);
  if (normalized !== value) fail("source_url must be normalized and tracking-free");
  return value;
}

function assertList(value, field) {
  if (!Array.isArray(value)) fail(`${field} must be an array`);
  if (value.length > MAX_LIST_ITEMS) fail(`${field} exceeds ${MAX_LIST_ITEMS} items`);
  let previous = null;
  const seen = new Set();
  for (const item of value) {
    assertSafeText(item, `${field}[]`, { max: MAX_LIST_ITEM_LENGTH });
    if (!item) fail(`${field}[] entries must not be empty`);
    const folded = item.toLocaleLowerCase("und");
    if (seen.has(folded)) fail(`${field} contains duplicate values`);
    seen.add(folded);
    if (previous !== null && (previous.localeCompare(folded, "und") > 0 || (previous === folded && previous !== item))) {
      fail(`${field} must be sorted case-insensitively`);
    }
    previous = folded;
  }
  return value;
}

function containsPhoneNumber(value) {
  for (const match of value.matchAll(PHONE_CANDIDATE_RE)) {
    const candidate = match[0].trim();
    const digits = candidate.replace(/\D/gu, "");
    if (digits.length < 7 || digits.length > 15) continue;
    if (candidate.startsWith("+")) return true;
    if (/^(?:\d{1,3}[ .-]?)?\(\d{2,4}\)[ .-]?\d{3,4}[ .-]\d{3,4}$/u.test(candidate)) return true;
    if (/^(?:1[ .-])?\d{3}[ .-]\d{3}[ .-]\d{4}$/u.test(candidate)) return true;
    if (/^\d{3}[ .-]\d{4}$/u.test(candidate)) return true;
  }
  return false;
}

function decodedContactScanValue(value) {
  let decoded = value;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      // Preserve literal `+`: converting it to a form-space corrupts prose
      // and can hide an international phone prefix before validation.
      const nextValue = decodeURIComponent(decoded);
      if (nextValue === decoded) break;
      decoded = nextValue;
    } catch {
      break;
    }
  }
  return decoded;
}

function decodedQueryContactScanValue(value) {
  let decoded;
  try {
    decoded = decodeURIComponent(value.replace(/\+/gu, "%20"));
  } catch {
    return value;
  }
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const nextValue = decodeURIComponent(decoded);
      if (nextValue === decoded) break;
      decoded = nextValue;
    } catch {
      break;
    }
  }
  return decoded;
}

function phoneContactScanValue(value, field) {
  if (field !== "source_url") return decodedContactScanValue(value);
  try {
    return decodedQueryContactScanValue(new URL(value).search.replace(/^\?/u, ""));
  } catch {
    return "";
  }
}

function assertNoEmbeddedContacts(record) {
  const exempt = new Set(["score", "observed_at", "reviewed_at", "source_hash", "dedup_key"]);
  for (const field of PUBLIC_RECORD_FIELDS) {
    if (exempt.has(field)) continue;
    const rawValues = Array.isArray(record[field]) ? record[field] : [record[field]];
    for (const rawValue of rawValues) {
      const rawText = String(rawValue);
      const value = decodedContactScanValue(rawText);
      if (EMAIL_RE.test(value)) fail(`${field} contains a forbidden email address`);
      // Stable IDs commonly carry compact dates or long platform IDs.  Keep
      // the email scan for IDs, but do not classify numeric ID segments as
      // phone numbers.
      const phoneValue = phoneContactScanValue(rawText, field);
      if (field !== "id" && field !== "source_record_id" && containsPhoneNumber(phoneValue)) {
        fail(`${field} contains a forbidden phone number`);
      }
    }
  }
}

export function validateRecord(raw, lineNumber = 1) {
  exactKeys(raw, PUBLIC_RECORD_FIELDS, `record line ${lineNumber}`);
  for (const field of PUBLIC_RECORD_FIELDS) {
    if (field === "score" || field === "topics" || field === "lanes") continue;
    const max = field === "id" || field === "source_record_id" ? MAX_ID_LENGTH : field === "source_url" ? MAX_URL_LENGTH : MAX_TEXT_LENGTH;
    assertSafeText(raw[field], `record.${field}`, { max, required: !["author_name", "author_handle", "cost", "complexity", "effect_speed"].includes(field) });
  }
  if (raw.collection !== COLLECTION) fail(`record.collection must be ${COLLECTION}`);
  if (raw.record_type !== RECORD_TYPE) fail(`record.record_type must be ${RECORD_TYPE}`);
  if (!SOURCE_ID_RE.test(raw.source_record_id)) fail("record.source_record_id is not a stable identifier");
  if (raw.id !== `outreach-finding:${raw.source_record_id}`) fail("record.id must match source_record_id");
  assertCanonicalUrl(raw.source_url);
  assertValidDate(raw.observed_at, "record.observed_at");
  assertValidDate(raw.reviewed_at, "record.reviewed_at", { timestamp: true });
  assertFiniteScore(raw.score);
  if (raw.source_status !== "Одобрено" && raw.source_status !== "Одобрено с ограничениями") fail("record.source_status is not allowed");
  if (raw.public_policy !== PUBLIC_POLICY) fail(`record.public_policy must be ${PUBLIC_POLICY}`);
  if (raw.language !== LANGUAGE) fail(`record.language must be ${LANGUAGE}`);
  assertList(raw.topics, "record.topics");
  assertList(raw.lanes, "record.lanes");
  let publicTextTotal = 0;
  for (const [field, limit] of Object.entries(PUBLIC_TEXT_LIMITS)) {
    if (raw[field].length > limit) fail(`record.${field} exceeds public limit ${limit}`);
    publicTextTotal += raw[field].length;
  }
  for (const value of [...raw.topics, ...raw.lanes]) publicTextTotal += value.length;
  if (publicTextTotal > MAX_PUBLIC_TEXT_TOTAL) {
    fail(`record exceeds public text limit ${MAX_PUBLIC_TEXT_TOTAL}`);
  }
  assertHash(raw.source_hash, "record.source_hash");
  assertHash(raw.dedup_key, "record.dedup_key");
  assertNoEmbeddedContacts(raw);
  return raw;
}

function validateReject(raw, lineNumber) {
  // Rejection receipts deliberately carry a one-way source reference rather
  // than leaking a held/private source identifier into the bundle.
  exactKeys(raw, ["source_ref", "row_index", "reason", "detail"], `reject line ${lineNumber}`);
  assertSafeText(raw.source_ref, "reject.source_ref", { required: false, max: 64 });
  if (raw.source_ref && !SHA256_RE.test(raw.source_ref)) fail("reject.source_ref must be lowercase SHA-256 hexadecimal");
  assertInteger(raw.row_index, "reject.row_index", 1, Number.MAX_SAFE_INTEGER);
  assertSafeText(raw.reason, "reject.reason", { max: 128 });
  assertSafeText(raw.detail, "reject.detail", { required: false, max: 2_000 });
  return raw;
}

function sha256Bytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function readUtf8File(path, label) {
  let info;
  try {
    info = statSync(path);
  } catch {
    fail(`${label} is not readable: ${path}`);
  }
  if (!info.isFile()) fail(`${label} is not a regular file: ${path}`);
  if (info.size > MAX_INPUT_BYTES) fail(`${label} exceeds ${MAX_INPUT_BYTES} bytes`);
  let bytes;
  try {
    bytes = readFileSync(path);
  } catch {
    fail(`${label} is not readable: ${path}`);
  }
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    fail(`${label} is not valid UTF-8`);
  }
  return { bytes, text };
}

function parseJsonl(text, label, validator, maxRows) {
  const rows = [];
  const lines = text.split(/\r?\n/u);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    if (Buffer.byteLength(line, "utf8") > MAX_LINE_BYTES) fail(`${label} line ${index + 1} exceeds ${MAX_LINE_BYTES} bytes`);
    let value;
    try {
      value = JSON.parse(line);
    } catch (error) {
      fail(`${label} line ${index + 1} is not valid JSON: ${error.message}`);
    }
    rows.push(validator(value, index + 1));
    if (rows.length > maxRows) fail(`${label} exceeds max rows ${maxRows}`);
  }
  return rows;
}

function manifestHashFields(manifest) {
  for (const field of [
    "input_sha256",
    "input_hash",
    "canonical_input_sha256",
    "admission_sha256",
    "records_sha256",
    "rejects_sha256",
  ]) assertHash(manifest[field], `manifest.${field}`);
  if (manifest.input_sha256 !== manifest.input_hash) fail("manifest.input_sha256 and input_hash must match");
}

function countsObject(value) {
  exactKeys(value, ["input_rows", "admission_entries", "records", "rejects"], "manifest.counts");
  for (const key of ["input_rows", "admission_entries", "records", "rejects"]) assertInteger(value[key], `manifest.counts.${key}`, 0, Number.MAX_SAFE_INTEGER);
  return value;
}

function rejectionCounts(value, rejects) {
  assertObject(value, "manifest.rejection_counts");
  for (const [key, count] of Object.entries(value)) {
    if (!/^[a-z0-9_]+$/u.test(key)) fail("manifest.rejection_counts has an invalid reason");
    assertInteger(count, `manifest.rejection_counts.${key}`, 0, Number.MAX_SAFE_INTEGER);
  }
  const actual = {};
  for (const reject of rejects) actual[reject.reason] = (actual[reject.reason] ?? 0) + 1;
  const actualKeys = Object.keys(actual).sort();
  const manifestKeys = Object.keys(value).sort();
  if (actualKeys.length !== manifestKeys.length || actualKeys.some((key, index) => key !== manifestKeys[index] || actual[key] !== value[key])) {
    fail("manifest.rejection_counts does not match outreach_rejects.jsonl");
  }
}

export function validateManifest(manifest, { recordsBytes, rejectsBytes, manifestBytes, records, rejects } = {}) {
  exactKeys(manifest, MANIFEST_FIELDS, "manifest");
  if (manifest.schema !== EXPORT_SCHEMA) fail(`manifest.schema must be ${EXPORT_SCHEMA}`);
  if (manifest.collection !== COLLECTION) fail(`manifest.collection must be ${COLLECTION}`);
  if (manifest.tab !== "01_Находки") fail("manifest.tab must be 01_Находки");
  if (manifest.deterministic !== true) fail("manifest.deterministic must be true");
  if (manifest.hash_algorithm !== "sha256") fail("manifest.hash_algorithm must be sha256");
  manifestHashFields(manifest);
  if (!Array.isArray(manifest.required_headers) || JSON.stringify(manifest.required_headers) !== JSON.stringify(REQUIRED_SOURCE_HEADERS)) fail("manifest.required_headers does not match the source contract");
  if (!Array.isArray(manifest.public_fields) || JSON.stringify(manifest.public_fields) !== JSON.stringify(PUBLIC_RECORD_FIELDS)) fail("manifest.public_fields does not match the public record contract");
  if (!Array.isArray(manifest.files) || JSON.stringify(manifest.files) !== JSON.stringify(BUNDLE_FILES)) fail("manifest.files does not match the export bundle");
  for (const key of ["input_rows", "admission_entries", "record_count", "reject_count", "records", "rejects"]) assertInteger(manifest[key], `manifest.${key}`, 0, Number.MAX_SAFE_INTEGER);
  countsObject(manifest.counts);
  if (manifest.records !== manifest.record_count || manifest.rejects !== manifest.reject_count) fail("manifest records/rejects counts disagree");
  if (manifest.counts.records !== manifest.record_count || manifest.counts.rejects !== manifest.reject_count) fail("manifest.counts records/rejects disagree");
  if (
    manifest.counts.input_rows !== manifest.input_rows ||
    manifest.counts.admission_entries !== manifest.admission_entries
  ) {
    fail("manifest.counts input/admission values disagree");
  }
  if (manifest.input_rows !== manifest.record_count + manifest.reject_count) {
    fail("manifest.input_rows must equal records plus rejects");
  }
  if (records && manifest.record_count !== records.length) fail("manifest.record_count does not match outreach_records.jsonl");
  if (rejects && manifest.reject_count !== rejects.length) fail("manifest.reject_count does not match outreach_rejects.jsonl");
  if (recordsBytes && manifest.records_sha256 !== sha256Bytes(recordsBytes)) fail("manifest.records_sha256 mismatch");
  if (rejectsBytes && manifest.rejects_sha256 !== sha256Bytes(rejectsBytes)) fail("manifest.rejects_sha256 mismatch");
  rejectionCounts(manifest.rejection_counts, rejects ?? []);
  // The manifest itself is intentionally not hashed by the exporter.  Keep
  // this argument consumed so callers can pass it when recording a receipt.
  void manifestBytes;
  return manifest;
}

function sortedRecords(records) {
  return [...records].sort((left, right) => left.source_record_id.localeCompare(right.source_record_id, "und"));
}

export function validateRecordUniqueness(records) {
  const seen = new Map();
  for (const field of ["id", "source_record_id", "source_url", "dedup_key"]) {
    seen.clear();
    for (const record of records) {
      const value = record[field];
      if (seen.has(value)) fail(`duplicate ${field}: ${value}`);
      seen.set(value, true);
    }
  }
}

export function loadBundle(inputDir, { maxRows = DEFAULT_MAX_ROWS } = {}) {
  const directory = resolve(inputDir);
  let info;
  try {
    info = statSync(directory);
  } catch {
    fail(`input directory not found: ${directory}`);
  }
  if (!info.isDirectory()) fail(`input path is not a directory: ${directory}`);
  let names;
  try {
    names = readdirSync(directory).sort();
  } catch {
    fail(`cannot read input directory: ${directory}`);
  }
  const allowed = new Set(BUNDLE_FILES);
  const unexpected = names.filter((name) => !allowed.has(name));
  if (unexpected.length) fail(`input directory contains unexpected files: ${unexpected.join(",")}`);
  if (names.length !== BUNDLE_FILES.length) {
    fail(`input directory must contain exactly ${BUNDLE_FILES.join(", ")}`);
  }
  const files = {};
  let totalBytes = 0;
  for (const name of BUNDLE_FILES) {
    const path = join(directory, name);
    const file = readUtf8File(path, name);
    totalBytes += file.bytes.length;
    if (totalBytes > MAX_BUNDLE_BYTES) fail(`input bundle exceeds ${MAX_BUNDLE_BYTES} bytes`);
    files[name] = { path, ...file, sha256: sha256Bytes(file.bytes) };
  }
  const records = parseJsonl(files["outreach_records.jsonl"].text, "outreach_records.jsonl", validateRecord, maxRows);
  const rejects = parseJsonl(files["outreach_rejects.jsonl"].text, "outreach_rejects.jsonl", validateReject, maxRows);
  validateRecordUniqueness(records);
  const manifest = (() => {
    try {
      return JSON.parse(files["manifest.json"].text);
    } catch (error) {
      fail(`manifest.json is not valid JSON: ${error.message}`);
    }
  })();
  validateManifest(manifest, {
    recordsBytes: files["outreach_records.jsonl"].bytes,
    rejectsBytes: files["outreach_rejects.jsonl"].bytes,
    manifestBytes: files["manifest.json"].bytes,
    records,
    rejects,
  });
  return {
    inputDir: directory,
    files,
    records: sortedRecords(records),
    rejects,
    manifest,
    hashes: {
      records: files["outreach_records.jsonl"].sha256,
      rejects: files["outreach_rejects.jsonl"].sha256,
      manifest: files["manifest.json"].sha256,
    },
  };
}

export function sqlString(value) {
  return `'${String(value).replaceAll("'", "''")}'`;
}

function sqlNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) fail("score must be finite before SQL rendering");
  return Object.is(value, -0) ? "0" : String(value);
}

function findingStatements(record) {
  const values = SQL_COLUMNS.map((column) => {
    if (column === "topics_json") return sqlString(JSON.stringify(record.topics));
    if (column === "lanes_json") return sqlString(JSON.stringify(record.lanes));
    if (column === "score") return sqlNumber(record.score);
    return sqlString(record[column] ?? "");
  });
  const updates = SQL_COLUMNS.filter((column) => column !== "id")
    .map((column) => `${column}=excluded.${column}`)
    .join(", ");
  const statements = [
    `INSERT INTO outreach_findings (${SQL_COLUMNS.join(", ")}) VALUES (${values.join(", ")}) ON CONFLICT(id) DO UPDATE SET ${updates};`,
    `DELETE FROM outreach_topics WHERE finding_id=${sqlString(record.id)};`,
  ];
  for (const topic of record.topics) {
    statements.push(`INSERT INTO outreach_topics (finding_id, topic) VALUES (${sqlString(record.id)}, ${sqlString(topic)});`);
  }
  statements.push(`DELETE FROM outreach_lanes WHERE finding_id=${sqlString(record.id)};`);
  for (const lane of record.lanes) {
    statements.push(`INSERT INTO outreach_lanes (finding_id, lane) VALUES (${sqlString(record.id)}, ${sqlString(lane)});`);
  }
  return statements;
}

export function renderRecordSql(record) {
  validateRecord(record);
  return findingStatements(record).join("\n");
}

export function renderBatch(statements, batchNumber) {
  return [
    `-- Base2026 Outreach import batch ${String(batchNumber).padStart(4, "0")}`,
    ...statements,
    "",
  ].join("\n");
}

export function makeBatches(records, { batchSize = DEFAULT_BATCH_SIZE, maxSqlBytes = DEFAULT_MAX_SQL_BYTES } = {}) {
  assertInteger(batchSize, "batchSize", 1, 500);
  assertInteger(maxSqlBytes, "maxSqlBytes", 1_024, 1_024 * 1_024);
  const batches = [];
  let current = [];
  let currentBytes = 0;
  for (const record of sortedRecords(records)) {
    const statements = findingStatements(record);
    const statement = statements.join("\n");
    const single = renderBatch([statement], batches.length + 1);
    const singleBytes = Buffer.byteLength(single, "utf8");
    if (singleBytes > maxSqlBytes) fail(`record ${record.id} exceeds max SQL batch size ${maxSqlBytes}`);
    const candidate = [...current, statement];
    const candidateText = renderBatch(candidate, batches.length + 1);
    const candidateBytes = Buffer.byteLength(candidateText, "utf8");
    if (current.length && (current.length >= batchSize || candidateBytes > maxSqlBytes)) {
      const finished = renderBatch(current, batches.length + 1);
      batches.push({ statements: current, text: finished, bytes: Buffer.byteLength(finished, "utf8"), rowCount: current.length });
      current = [];
      currentBytes = 0;
    }
    current.push(statement);
    currentBytes = Buffer.byteLength(renderBatch(current, batches.length + 1), "utf8");
  }
  if (current.length) {
    const text = renderBatch(current, batches.length + 1);
    batches.push({ statements: current, text, bytes: Buffer.byteLength(text, "utf8"), rowCount: current.length });
  }
  void currentBytes;
  return batches;
}

function stableValue(value) {
  if (Array.isArray(value)) return `[${value.map(stableValue).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableValue(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function prettyStableJson(value) {
  return `${JSON.stringify(JSON.parse(stableValue(value)), null, 2)}\n`;
}

export function buildReceipt(bundle, batches, { batchSize = DEFAULT_BATCH_SIZE, maxSqlBytes = DEFAULT_MAX_SQL_BYTES } = {}) {
  const batchFiles = batches.map((_batch, index) => `batch-${String(index + 1).padStart(4, "0")}.sql`);
  const migrationBytes = readFileSync(MIGRATION_PATH);
  return {
    schema: IMPORT_SCHEMA,
    collection: COLLECTION,
    deterministic: true,
    hash_algorithm: "sha256",
    source_bundle: {
      schema: bundle.manifest.schema,
      manifest_sha256: bundle.hashes.manifest,
      records_sha256: bundle.hashes.records,
      rejects_sha256: bundle.hashes.rejects,
      record_count: bundle.records.length,
      reject_count: bundle.rejects.length,
    },
    migration: {
      file: MIGRATION_RELATIVE_PATH,
      sha256: sha256Bytes(migrationBytes),
    },
    options: {
      batch_size: batchSize,
      max_sql_bytes: maxSqlBytes,
    },
    batches: batches.map((batch, index) => ({
      file: batchFiles[index],
      number: index + 1,
      rows: batch.rowCount,
      bytes: batch.bytes,
      sha256: sha256Bytes(Buffer.from(batch.text, "utf8")),
    })),
    files: [...batchFiles, RECEIPT_FILE],
  };
}

export function buildImport(options = {}) {
  if (typeof options === "string") options = { inputDir: options };
  const inputDir = options.inputDir ?? options.input ?? options.sourceDir;
  if (!inputDir) fail("--input-dir is required");
  const maxRows = options.maxRows ?? DEFAULT_MAX_ROWS;
  assertInteger(maxRows, "maxRows", 1, 100_000);
  const bundle = loadBundle(inputDir, { maxRows });
  const batchSize = options.batchSize ?? DEFAULT_BATCH_SIZE;
  const maxSqlBytes = options.maxSqlBytes ?? DEFAULT_MAX_SQL_BYTES;
  const batches = makeBatches(bundle.records, { batchSize, maxSqlBytes });
  return {
    ...bundle,
    batches,
    batchSize,
    maxSqlBytes,
    receipt: buildReceipt(bundle, batches, { batchSize, maxSqlBytes }),
  };
}

export function writeImportOutput(result, outputDir) {
  if (!outputDir) fail("--output-dir is required unless --dry-run is used");
  const target = resolve(outputDir);
  if (existsSync(target)) fail(`output directory must not already exist: ${target}`);
  const parent = dirname(target);
  mkdirSync(parent, { recursive: true });
  const staging = mkdtempSync(join(parent, `.${target.split(sep).pop()}.tmp-`));
  try {
    for (const [index, batch] of result.batches.entries()) {
      writeFileSync(join(staging, `batch-${String(index + 1).padStart(4, "0")}.sql`), batch.text, "utf8");
    }
    writeFileSync(join(staging, RECEIPT_FILE), prettyStableJson(result.receipt), "utf8");
    renameSync(staging, target);
  } catch (error) {
    rmSync(staging, { recursive: true, force: true });
    throw error;
  }
  return target;
}

function parseBoundedInteger(value, name, min, max) {
  if (!/^\d+$/u.test(value)) fail(`${name} must be an integer`);
  const number = Number(value);
  return assertInteger(number, name, min, max);
}

export function parseArgs(argv) {
  const options = {
    inputDir: "",
    outputDir: "",
    batchSize: DEFAULT_BATCH_SIZE,
    maxSqlBytes: DEFAULT_MAX_SQL_BYTES,
    maxRows: DEFAULT_MAX_ROWS,
    dryRun: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    const [key, inlineValue] = argument.includes("=") ? argument.split(/=(.*)/su, 2) : [argument, undefined];
    const value = inlineValue ?? argv[++index];
    if (!value || value.startsWith("--")) fail(`missing value for ${key}`);
    if (key === "--input-dir" || key === "--input") options.inputDir = value;
    else if (key === "--output-dir" || key === "--out" || key === "--output") options.outputDir = value;
    else if (key === "--batch-size") options.batchSize = parseBoundedInteger(value, key, 1, 500);
    else if (key === "--max-sql-bytes") options.maxSqlBytes = parseBoundedInteger(value, key, 1_024, 1_024 * 1_024);
    else if (key === "--max-rows") options.maxRows = parseBoundedInteger(value, key, 1, 100_000);
    else throw new ImportInputError(`unknown option ${key}`);
  }
  if (!options.inputDir) fail("--input-dir is required");
  if (options.outputDir && options.dryRun) fail("--output-dir cannot be used with --dry-run");
  return options;
}

export function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const result = buildImport(options);
  const summary = {
    ok: true,
    input_dir: result.inputDir,
    records: result.records.length,
    rejects: result.rejects.length,
    batches: result.batches.length,
    batch_size: result.batchSize,
    max_sql_bytes: result.maxSqlBytes,
    dry_run: options.dryRun,
  };
  if (!options.dryRun) {
    const output = writeImportOutput(result, options.outputDir);
    summary.output_dir = output;
  }
  process.stdout.write(`${JSON.stringify(summary)}\n`);
  return summary;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`import-public-outreach: ${error.message}\n`);
    process.exitCode = 1;
  }
}

// Keep these references intentionally exported through the module surface for
// focused tests and future local orchestration without adding a runtime
// dependency on the CLI.
export { findingStatements, sha256Bytes, prettyStableJson, WORKER_ROOT };
