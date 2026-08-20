#!/usr/bin/env node

import { readFileSync, statSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const WORKER_ROOT = resolve(SCRIPT_DIR, "..");
const REPO_ROOT = resolve(WORKER_ROOT, "../..");
const DEFAULT_INPUTS = [
  resolve(REPO_ROOT, "output/cloudflare-migration/source-web/static/passages.jsonl"),
  resolve(REPO_ROOT, "output/cloudflare-migration/source-web/static/chunks.jsonl"),
  resolve(REPO_ROOT, "public-data/tiktok/chunks.jsonl"),
];

const DEFAULT_BATCH_SIZE = 100;
const DEFAULT_MAX_SQL_BYTES = 256 * 1024;
const DEFAULT_MAX_ROWS = 10_000;
const MAX_INPUT_BYTES = 64 * 1024 * 1024;
const MAX_BODY_LENGTH = 1_000_000;

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
]);

const SQL_COLUMNS = Object.freeze([
  "id",
  "item_id",
  "source_id",
  "chunk_id",
  "chunk_index",
  "body",
  "captured_at",
  "creator_display_name",
  "creator_handle",
  "creator_id",
  "creator_url",
  "full_transcript_public",
  "handle",
  "platform",
  "post_id",
  "public_policy",
  "public_surface",
  "published_at",
  "published_date",
  "source_type",
  "source_url",
  "title",
  "title_source",
  "title_status",
  "video_id",
  "year",
  "avatar_url",
  "topics_json",
  "topic_labels_json",
]);

const FORBIDDEN_KEY = /(caption|transcript|asr|audio|media|secret|token|cookie|claim|private|password|credential)/i;
const SAFE_POLICY_KEYS = new Set(["full_transcript_public"]);

function parseArgs(argv) {
  const options = {
    input: "",
    output: "",
    outputDir: "",
    batchSize: DEFAULT_BATCH_SIZE,
    maxSqlBytes: DEFAULT_MAX_SQL_BYTES,
    maxRows: DEFAULT_MAX_ROWS,
    limit: null,
    dryRun: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    const [key, inlineValue] = arg.includes("=") ? arg.split(/=(.*)/s, 2) : [arg, undefined];
    const value = inlineValue ?? argv[++index];
    if (!value || value.startsWith("--")) throw new Error(`missing value for ${key}`);
    if (key === "--input") options.input = value;
    else if (key === "--output") options.output = value;
    else if (key === "--output-dir") options.outputDir = value;
    else if (key === "--batch-size") options.batchSize = parseBoundedInteger(value, key, 1, 500);
    else if (key === "--max-sql-bytes") options.maxSqlBytes = parseBoundedInteger(value, key, 1024, 1024 * 1024);
    else if (key === "--max-rows") options.maxRows = parseBoundedInteger(value, key, 1, 100_000);
    else if (key === "--limit") options.limit = parseBoundedInteger(value, key, 1, 100_000);
    else throw new Error(`unknown option ${key}`);
  }
  if (options.output && options.outputDir) throw new Error("--output and --output-dir are mutually exclusive");
  return options;
}

function parseBoundedInteger(value, name, min, max) {
  if (!/^\d+$/.test(value)) throw new Error(`${name} must be an integer`);
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number < min || number > max) {
    throw new Error(`${name} must be between ${min} and ${max}`);
  }
  return number;
}

function resolveInput(input) {
  if (input) {
    const candidate = isAbsolute(input) ? input : resolve(process.cwd(), input);
    if (!statExists(candidate)) throw new Error(`input file not found: ${candidate}`);
    return candidate;
  }
  const candidate = DEFAULT_INPUTS.find(statExists);
  if (!candidate) {
    throw new Error(`no public chunks JSONL found; tried: ${DEFAULT_INPUTS.join(", ")}`);
  }
  return candidate;
}

function statExists(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

function sqlString(value) {
  return `'${String(value).replaceAll("'", "''")}'`;
}

function sqlInteger(value) {
  return Number.isInteger(value) ? String(value) : "0";
}

function stringField(row, key, { required = false, max = MAX_BODY_LENGTH } = {}) {
  const value = row[key];
  if (value === undefined || value === null) {
    if (required) throw new Error(`row is missing required field ${key}`);
    return "";
  }
  if (typeof value !== "string") throw new Error(`${key} must be a string`);
  if (value.length > max) throw new Error(`${key} exceeds ${max} characters`);
  return value;
}

function normalizeAvatarUrl(value) {
  if (value.startsWith("/knowledge/static/")) return value.slice("/knowledge".length);
  if (value.startsWith("knowledge/static/")) return `/${value.slice("knowledge/".length)}`;
  return value;
}

function normalizePublicUrl(value) {
  const match = value.match(/^\[(https?:\/\/[^\]\s()]+)\]\((https?:\/\/[^\s()]+)\)$/i);
  return match && match[1] === match[2] ? match[1] : value;
}

function listField(row, key, fallback = []) {
  const value = row[key];
  if (value === undefined || value === null) return fallback;
  if (!Array.isArray(value)) throw new Error(`${key} must be an array`);
  const result = [];
  const seen = new Set();
  for (const item of value) {
    if (typeof item !== "string") throw new Error(`${key} must contain only strings`);
    const normalized = item.trim();
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

function validateRow(raw, lineNumber) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error(`line ${lineNumber} must contain a JSON object`);
  }
  for (const key of Object.keys(raw)) {
    if (PUBLIC_FIELDS.includes(key)) continue;
    if (FORBIDDEN_KEY.test(key) && !SAFE_POLICY_KEYS.has(key)) {
      throw new Error(`line ${lineNumber} contains forbidden field ${key}`);
    }
    throw new Error(`line ${lineNumber} contains unknown field ${key}`);
  }
  const id = stringField(raw, "id", { required: true, max: 300 }).trim();
  const itemId = stringField(raw, "item_id", { required: true, max: 300 }).trim();
  const body = stringField(raw, "body", { required: true });
  if (!id || !itemId || !body.trim()) throw new Error(`line ${lineNumber} has an empty id, item_id or body`);
  if (raw.full_transcript_public === true) {
    throw new Error(`line ${lineNumber} sets full_transcript_public=true; public search is excerpt-only`);
  }
  if (raw.full_transcript_public !== undefined && typeof raw.full_transcript_public !== "boolean") {
    throw new Error(`line ${lineNumber} full_transcript_public must be boolean`);
  }
  if (raw.public_surface !== undefined && raw.public_surface !== "main_search") {
    throw new Error(`line ${lineNumber} is not a main_search public row`);
  }
  if (raw.admission_state !== undefined && raw.admission_state !== "normal_public_card") {
    throw new Error(`line ${lineNumber} is not a normal_public_card row`);
  }
  const topics = listField(raw, "topics");
  const topicLabels = listField(raw, "topic_labels", topics);
  const topicLabelById = new Map(topicLabels.map((label, index) => [topics[index] ?? label, label]));
  return {
    admission_state: stringField(raw, "admission_state"),
    avatar_url: normalizeAvatarUrl(stringField(raw, "avatar_url", { max: 2_000 })),
    body,
    captured_at: stringField(raw, "captured_at", { max: 100 }),
    chunk_id: stringField(raw, "chunk_id", { max: 300 }),
    chunk_index: Number.isInteger(raw.chunk_index) && raw.chunk_index >= 0 ? raw.chunk_index : 0,
    creator_display_name: stringField(raw, "creator_display_name", { max: 300 }),
    creator_handle: stringField(raw, "creator_handle", { max: 300 }),
    creator_id: stringField(raw, "creator_id", { max: 300 }),
    creator_url: normalizePublicUrl(stringField(raw, "creator_url", { max: 2_000 })),
    full_transcript_public: 0,
    handle: stringField(raw, "handle", { max: 300 }),
    id,
    item_id: itemId,
    platform: stringField(raw, "platform", { max: 100 }),
    post_id: stringField(raw, "post_id", { max: 300 }),
    public_policy: stringField(raw, "public_policy", { max: 100 }),
    public_surface: stringField(raw, "public_surface", { max: 100 }),
    published_at: stringField(raw, "published_at", { max: 100 }),
    published_date: stringField(raw, "published_date", { max: 100 }),
    source_id: stringField(raw, "source_id", { max: 300 }),
    source_type: stringField(raw, "source_type", { max: 100 }),
    source_url: normalizePublicUrl(stringField(raw, "source_url", { max: 2_000 })),
    title: stringField(raw, "title", { max: 10_000 }),
    title_source: stringField(raw, "title_source", { max: 100 }),
    title_status: stringField(raw, "title_status", { max: 100 }),
    topic_labels: topicLabels,
    topics,
    topicLabelById,
    video_id: stringField(raw, "video_id", { max: 300 }),
    year: stringField(raw, "year", { max: 20 }),
  };
}

function readRows(input, maxRows) {
  const size = statSync(input).size;
  if (size > MAX_INPUT_BYTES) throw new Error(`input exceeds ${MAX_INPUT_BYTES} bytes`);
  const rows = [];
  const seen = new Set();
  let skippedRows = 0;
  const lines = readFileSync(input, "utf8").split(/\r?\n/u);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    let raw;
    try {
      raw = JSON.parse(line);
    } catch (error) {
      throw new Error(`line ${index + 1} is not valid JSON: ${error.message}`);
    }
    if (raw && typeof raw === "object" && !Array.isArray(raw) && (
      raw.public_surface === "provenance_archive" ||
      raw.admission_state === "provenance_archive_noindex"
    )) {
      skippedRows += 1;
      continue;
    }
    const row = validateRow(raw, index + 1);
    if (seen.has(row.id)) throw new Error(`duplicate id ${row.id}`);
    seen.add(row.id);
    rows.push(row);
    if (rows.length > maxRows) throw new Error(`input exceeds max rows ${maxRows}; rerun with an explicit --limit`);
  }
  return { rows: rows.sort((left, right) => left.id.localeCompare(right.id)), skippedRows };
}

function documentStatement(row) {
  const values = SQL_COLUMNS.map((column) => {
    if (column === "topics_json") return sqlString(JSON.stringify(row.topics));
    if (column === "topic_labels_json") return sqlString(JSON.stringify(row.topic_labels));
    if (column === "full_transcript_public") return "0";
    if (column === "chunk_index") return sqlInteger(row.chunk_index);
    return sqlString(row[column] ?? "");
  });
  const updates = SQL_COLUMNS
    .filter((column) => column !== "id")
    .map((column) => `${column}=excluded.${column}`)
    .join(", ");
  const statements = [
    `INSERT INTO search_documents (${SQL_COLUMNS.join(", ")}) VALUES (${values.join(", ")}) ON CONFLICT(id) DO UPDATE SET ${updates};`,
    `DELETE FROM search_topics WHERE document_id=${sqlString(row.id)};`,
  ];
  for (const [index, topicId] of row.topics.entries()) {
    statements.push(
      `INSERT INTO search_topics (document_id, topic_id, topic_label) VALUES (${sqlString(row.id)}, ${sqlString(topicId)}, ${sqlString(row.topicLabelById.get(topicId) ?? row.topic_labels[index] ?? topicId)});`,
    );
  }
  return statements.join("\n");
}

function makeBatches(rows, { batchSize, maxSqlBytes }) {
  const batches = [];
  let current = [];
  let currentBytes = 0;
  for (const row of rows) {
    const statement = documentStatement(row);
    const statementBytes = Buffer.byteLength(`${statement}\n`, "utf8");
    if (statementBytes > maxSqlBytes) {
      throw new Error(`row ${row.id} exceeds --max-sql-bytes ${maxSqlBytes}`);
    }
    if (current.length && (current.length >= batchSize || currentBytes + statementBytes > maxSqlBytes)) {
      batches.push(current);
      current = [];
      currentBytes = 0;
    }
    current.push(statement);
    currentBytes += statementBytes;
  }
  if (current.length) batches.push(current);
  return batches;
}

function renderBatch(statements, batchNumber) {
  return [
    `-- Base2026 public search import batch ${String(batchNumber).padStart(4, "0")}`,
    ...statements,
    "",
  ].join("\n");
}

function writeBatches(batches, options) {
  if (options.outputDir) {
    mkdirSync(options.outputDir, { recursive: true });
    const paths = [];
    batches.forEach((batch, index) => {
      const path = join(options.outputDir, `batch-${String(index + 1).padStart(4, "0")}.sql`);
      writeFileSync(path, renderBatch(batch, index + 1), "utf8");
      paths.push(path);
    });
    return paths;
  }
  const sql = batches.map((batch, index) => renderBatch(batch, index + 1)).join("\n");
  if (options.output) writeFileSync(options.output, sql, "utf8");
  else process.stdout.write(sql);
  return options.output ? [options.output] : [];
}

export function buildImport(options = {}) {
  const input = resolveInput(options.input ?? "");
  const { rows, skippedRows } = readRows(input, options.maxRows ?? DEFAULT_MAX_ROWS);
  const limitedRows = options.limit ? rows.slice(0, options.limit) : rows;
  const batches = makeBatches(limitedRows, {
    batchSize: options.batchSize ?? DEFAULT_BATCH_SIZE,
    maxSqlBytes: options.maxSqlBytes ?? DEFAULT_MAX_SQL_BYTES,
  });
  return { input, rows, limitedRows, skippedRows, batches };
}

export function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const result = buildImport(options);
  const summary = {
    input: result.input,
    rows_read: result.rows.length,
    rows_skipped: result.skippedRows,
    rows_emitted: result.limitedRows.length,
    batches: result.batches.length,
    batch_size: options.batchSize,
    max_sql_bytes: options.maxSqlBytes,
    deterministic_order: "id_ascending",
    dry_run: options.dryRun,
  };
  if (options.dryRun) {
    process.stdout.write(`${JSON.stringify(summary)}\n`);
  } else {
    const paths = writeBatches(result.batches, options);
    if (paths.length) process.stderr.write(`wrote ${paths.length} SQL batch file(s)\n`);
  }
  return summary;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`import-public-chunks: ${error.message}\n`);
    process.exitCode = 1;
  }
}
