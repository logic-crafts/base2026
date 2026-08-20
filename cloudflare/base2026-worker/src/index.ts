const INDEX_UID = "base2026_public_tiktok" as const;
const MAX_BODY_BYTES = 64 * 1024;
const MAX_QUERY_LENGTH = 200;
const MAX_MULTI_QUERIES = 4;
const MAX_LIMIT = 100;
const MAX_OFFSET = 10_000;
const MAX_FACET_VALUES = 100;
const DEFAULT_LIMIT = 20;
const FORM_ORIGIN = "https://base2026.dev";
const FORM_CONSENT_VERSION = "2026-08-20";
const MIN_FORM_COMPLETION_MS = 1_200;
const MAX_FORM_COMPLETION_MS = 2 * 60 * 60 * 1_000;

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

type EnvWithBindings = Env & { INBOX_DB?: D1Database };

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
  indexUid: string;
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

class RequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function jsonResponse(payload: unknown, status = 200, headers: HeadersInit = {}): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...JSON_HEADERS, ...headers },
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
    error.code === "METHOD_NOT_ALLOWED" ? { Allow: "GET, POST" } : undefined,
  );
}

function methodError(method: string): RequestError {
  return new RequestError(405, "METHOD_NOT_ALLOWED", `method ${method} is not allowed`);
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

function parseQuery(raw: unknown): SearchQuery {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new RequestError(400, "INVALID_QUERY", "each query must be a JSON object");
  }
  const query = raw as Record<string, unknown>;
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
  const indexUid = query.indexUid === undefined ? INDEX_UID : ensureString(query.indexUid, "indexUid", 100);
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
  for (const query of parsedQueries) results.push(await executeSearch(env, query));
  return jsonResponse({ results });
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

export default {
  async fetch(request: Request, env: EnvWithBindings, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    try {
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
        return Response.redirect(url.toString(), 301);
      }
      if (url.pathname === "/api/health") return await handleHealth(env);
      if (url.pathname === "/api/forms/support") return await handleInboxForm(request, env, "support");
      if (url.pathname === "/api/forms/partner") return await handleInboxForm(request, env, "partner");
      if (url.pathname === "/api/search/multi-search" || url.pathname === "/knowledge-search/multi-search") {
        if (!env.DB) throw new RequestError(503, "DB_NOT_CONFIGURED", "D1 binding DB is not configured");
        return await handleSearch(request, env);
      }
      if (env.ASSETS) return await env.ASSETS.fetch(request);
      throw new RequestError(404, "NOT_FOUND", "asset or API route not found");
    } catch (error) {
      if (error instanceof RequestError) return errorResponse(error);
      console.error(JSON.stringify({ event: "base2026_worker_error", path: url.pathname }));
      return errorResponse(new RequestError(500, "INTERNAL_ERROR", "request could not be completed"));
    }
  },
};
