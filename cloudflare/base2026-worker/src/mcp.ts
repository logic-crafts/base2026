const PUBLIC_ORIGIN = "https://base2026.dev";

export const MCP_ENDPOINT = `${PUBLIC_ORIGIN}/api/mcp`;
export const MCP_SERVER_VERSION = "0.1.0";

const MODERN_PROTOCOL_VERSION = "2026-07-28" as const;
const SUPPORTED_PROTOCOL_VERSIONS = [
  MODERN_PROTOCOL_VERSION,
  "2025-11-25",
  "2025-06-18",
  "2025-03-26",
] as const;
const DEFAULT_LEGACY_PROTOCOL_VERSION = "2025-03-26" as const;
const MAX_BODY_BYTES = 64 * 1024;
const MAX_QUERY_LENGTH = 200;
const MAX_SOURCE_ID_LENGTH = 200;
const MAX_TOPIC_ID_LENGTH = 120;
const MAX_HANDLE_LENGTH = 100;
const MAX_PLATFORM_LENGTH = 40;
const MAX_TOOL_LIMIT = 20;
const MAX_TOOL_OFFSET = 1_000;
const MAX_SOURCE_PASSAGES = 8;
const MAX_CREATOR_SOURCES = 10;
const MAX_TOPIC_SOURCES = 10;
const MAX_TOPIC_CREATORS = 10;
const MAX_CREATOR_TOPICS = 30;
const MAX_EXCERPT_LENGTH = 640;
const MAX_CARD_EXCERPT_LENGTH = 900;
const PUBLIC_BOUNDARY = Object.freeze({
  access: "public_read_only",
  raw_captions: false,
  raw_asr: false,
  media_files: false,
  private_data: false,
  writes: false,
});

export interface PublicMcpEnv {
  DB?: D1Database;
}

type JsonRpcId = string | number | null;
type JsonRecord = Record<string, unknown>;

interface JsonRpcRequest extends JsonRecord {
  jsonrpc: string;
  method: string;
  id?: JsonRpcId;
  params?: unknown;
}

interface PublicSourceRow extends JsonRecord {
  id?: string;
  item_id?: string;
  source_id?: string;
  chunk_id?: string;
  chunk_index?: number | string;
  body?: string;
  creator_display_name?: string;
  creator_handle?: string;
  creator_url?: string;
  full_transcript_public?: number | string | boolean;
  handle?: string;
  platform?: string;
  post_id?: string;
  public_policy?: string;
  published_at?: string;
  published_date?: string;
  source_type?: string;
  source_url?: string;
  title?: string;
  title_status?: string;
  video_id?: string;
  year?: string;
  topics_json?: string;
  topic_labels_json?: string;
}

interface ProjectionCardRow extends JsonRecord {
  ordinal?: number | string;
  claim_text?: string;
  suggested_action?: string;
  topic_label?: string;
  evidence_excerpt?: string;
  evidence_start_seconds?: number | string;
  evidence_end_seconds?: number | string;
}

interface SearchScope {
  from: string;
  where: string;
  params: string[];
  hasFts: boolean;
}

class PublicMcpError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly details?: JsonRecord,
  ) {
    super(message);
  }
}

class McpHttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: number,
    message: string,
  ) {
    super(message);
  }
}

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function hasOwn(value: JsonRecord, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function rowString(row: JsonRecord, key: string): string {
  return typeof row[key] === "string" ? row[key] as string : "";
}

function rowNumber(row: JsonRecord, key: string): number {
  const value = typeof row[key] === "number" ? row[key] : Number(row[key]);
  return Number.isFinite(value) ? value : 0;
}

function normalizeText(value: string): string {
  return value.replace(/\s+/gu, " ").trim();
}

function truncate(value: string, length: number): string {
  const compact = normalizeText(value);
  return compact.length <= length ? compact : `${compact.slice(0, Math.max(0, length - 1)).trimEnd()}…`;
}

function parseJsonStrings(value: unknown): string[] {
  if (typeof value !== "string") return [];
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
      : [];
  } catch {
    return [];
  }
}

function safeExternalUrl(value: string): string | null {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function publicBoundary(): JsonRecord {
  return { ...PUBLIC_BOUNDARY };
}

function publicTopicPairs(rows: PublicSourceRow[]): Array<{ id: string; label: string }> {
  const pairs = new Map<string, { id: string; label: string }>();
  for (const row of rows) {
    const ids = parseJsonStrings(row.topics_json);
    const labels = parseJsonStrings(row.topic_labels_json);
    ids.forEach((id, index) => {
      if (!pairs.has(id)) pairs.set(id, { id, label: labels[index] ?? id });
    });
  }
  return [...pairs.values()];
}

function sourceKeyExpression(): string {
  return "CASE WHEN d.item_id<>'' THEN d.item_id ELSE d.source_id END";
}

function sourcePageUrl(videoId: string, hasAppliedProjection: boolean): string | null {
  return hasAppliedProjection && /^\d{10,30}$/u.test(videoId)
    ? `${PUBLIC_ORIGIN}/sources/tiktok-video-${videoId}`
    : null;
}

function sourceSummary(row: PublicSourceRow, appliedProjection = false): JsonRecord {
  const videoId = rowString(row, "video_id");
  const sourcePage = sourcePageUrl(videoId, appliedProjection);
  return {
    id: rowString(row, "item_id") || rowString(row, "source_id") || rowString(row, "id"),
    source_id: rowString(row, "source_id"),
    item_id: rowString(row, "item_id"),
    video_id: videoId || null,
    platform: rowString(row, "platform") || "tiktok",
    title: rowString(row, "title") || null,
    creator: {
      handle: rowString(row, "creator_handle") || rowString(row, "handle") || null,
      display_name: rowString(row, "creator_display_name") || null,
      url: safeExternalUrl(rowString(row, "creator_url")),
    },
    published_date: rowString(row, "published_date") || rowString(row, "published_at") || null,
    source_url: safeExternalUrl(rowString(row, "source_url")),
    source_page_url: sourcePage,
    topics: publicTopicPairs([row]),
    evidence_excerpt: truncate(rowString(row, "body"), MAX_EXCERPT_LENGTH) || null,
    passage_id: rowString(row, "chunk_id") || rowString(row, "id") || null,
    chunk_index: rowNumber(row, "chunk_index"),
    public_policy: rowString(row, "public_policy") || null,
    public_boundary: publicBoundary(),
  };
}

function buildFtsQuery(query: string): string | null {
  const tokens = query.normalize("NFKC").match(/[\p{L}\p{N}_@-]+/gu) ?? [];
  const uniqueTokens = [...new Set(tokens.map((token) => token.trim()).filter(Boolean))].slice(0, 20);
  if (!uniqueTokens.length) return null;
  return uniqueTokens.map((token) => `"${token.replaceAll('"', '""')}"*`).join(" AND ");
}

function handleVariants(value: string): [string, string] {
  const normalized = value.trim().toLowerCase();
  const bare = normalized.replace(/^@/u, "");
  return [`@${bare}`, bare];
}

function handleCondition(value: string): { sql: string; params: string[] } {
  const [withAt, bare] = handleVariants(value);
  return {
    sql: "(lower(d.creator_handle) IN (lower(?), lower(?)) OR lower(d.handle) IN (lower(?), lower(?)))",
    params: [withAt, bare, withAt, bare],
  };
}

function buildSearchScope(args: JsonRecord): SearchScope {
  const query = typeof args.query === "string" ? args.query.trim() : "";
  const ftsQuery = buildFtsQuery(query);
  const from = ftsQuery
    ? "FROM search_documents_fts JOIN search_documents AS d ON d.rowid=search_documents_fts.rowid"
    : "FROM search_documents AS d";
  const predicates = ["d.full_transcript_public=0"];
  const params: string[] = [];
  if (query && !ftsQuery) predicates.push("0");
  if (ftsQuery) {
    predicates.push("search_documents_fts MATCH ?");
    params.push(ftsQuery);
  }
  if (typeof args.creator_handle === "string" && args.creator_handle.trim()) {
    const condition = handleCondition(args.creator_handle);
    predicates.push(condition.sql);
    params.push(...condition.params);
  }
  if (typeof args.topic_id === "string" && args.topic_id.trim()) {
    predicates.push("EXISTS (SELECT 1 FROM search_topics AS st WHERE st.document_id=d.id AND st.topic_id=?)");
    params.push(args.topic_id.trim());
  }
  if (typeof args.platform === "string" && args.platform.trim()) {
    predicates.push("d.platform=?");
    params.push(args.platform.trim());
  }
  return { from, where: `WHERE ${predicates.join(" AND ")}`, params, hasFts: Boolean(ftsQuery) };
}

async function searchSources(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const scope = buildSearchScope(args);
  const limit = integerArgument(args, "limit", 1, MAX_TOOL_LIMIT, 10);
  const offset = integerArgument(args, "offset", 0, MAX_TOOL_OFFSET, 0);
  const query = typeof args.query === "string" ? args.query.trim() : "";
  const count = await env.DB.prepare(
    `SELECT COUNT(DISTINCT ${sourceKeyExpression()}) AS count ${scope.from} ${scope.where}`,
  ).bind(...scope.params).first<{ count: number | string }>();
  const rankExpression = scope.hasFts ? "bm25(search_documents_fts)" : "0";
  const rows = await env.DB.prepare(
    `WITH matched AS (
       SELECT d.*, ${rankExpression} AS match_rank
         ${scope.from}
         ${scope.where}
     ), ranked AS (
       SELECT matched.*,
              ROW_NUMBER() OVER (
                PARTITION BY CASE WHEN matched.item_id<>'' THEN matched.item_id ELSE matched.source_id END
                ORDER BY matched.match_rank ASC, matched.chunk_index ASC, matched.id ASC
              ) AS source_rank
         FROM matched
     )
     SELECT * FROM ranked
      WHERE source_rank=1
      ORDER BY match_rank ASC, published_date DESC, id ASC
      LIMIT ? OFFSET ?`,
  ).bind(...scope.params, limit, offset).all<PublicSourceRow>();
  return {
    schema: "base2026.mcp.search_sources.v1",
    query,
    filters: {
      ...(typeof args.creator_handle === "string" && args.creator_handle.trim() ? { creator_handle: args.creator_handle.trim() } : {}),
      ...(typeof args.topic_id === "string" && args.topic_id.trim() ? { topic_id: args.topic_id.trim() } : {}),
      ...(typeof args.platform === "string" && args.platform.trim() ? { platform: args.platform.trim() } : {}),
    },
    total: rowNumber(count ?? {}, "count"),
    limit,
    offset,
    results: rows.results.map((row) => sourceSummary(row)),
    public_boundary: publicBoundary(),
  };
}

async function readProjectionCards(db: D1Database, sourceId: string): Promise<ProjectionCardRow[]> {
  const result = await db.prepare(
    `SELECT c.ordinal, c.claim_text, c.suggested_action, c.topic_label,
            c.evidence_excerpt, c.evidence_start_seconds, c.evidence_end_seconds
       FROM public_projection_cards AS c
       JOIN public_projection_receipts AS r ON r.projection_id=c.projection_id
      WHERE r.status='applied' AND c.source_id=?
      ORDER BY c.ordinal ASC
      LIMIT 3`,
  ).bind(sourceId).all<ProjectionCardRow>();
  return result.results;
}

function projectionCard(card: ProjectionCardRow): JsonRecord {
  return {
    ordinal: rowNumber(card, "ordinal"),
    claim: rowString(card, "claim_text"),
    suggested_action: rowString(card, "suggested_action"),
    topic: rowString(card, "topic_label"),
    evidence_excerpt: truncate(rowString(card, "evidence_excerpt"), MAX_CARD_EXCERPT_LENGTH),
    evidence_start_seconds: rowNumber(card, "evidence_start_seconds"),
    evidence_end_seconds: rowNumber(card, "evidence_end_seconds"),
    public_boundary: publicBoundary(),
  };
}

async function getSource(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const sourceId = stringArgument(args, "source_id", 1, MAX_SOURCE_ID_LENGTH, true);
  const rows = await env.DB.prepare(
    `SELECT d.*
       FROM search_documents AS d
      WHERE d.full_transcript_public=0
        AND (d.source_id=? OR d.item_id=? OR d.video_id=? OR d.post_id=?)
      ORDER BY d.chunk_index ASC, d.id ASC
      LIMIT ?`,
  ).bind(sourceId, sourceId, sourceId, sourceId, MAX_SOURCE_PASSAGES).all<PublicSourceRow>();
  if (!rows.results.length) {
    return {
      schema: "base2026.mcp.get_source.v1",
      found: false,
      source_id: sourceId,
      public_boundary: publicBoundary(),
    };
  }
  const first = rows.results[0];
  const sourceKey = rowString(first, "source_id");
  const cards = await readProjectionCards(env.DB, sourceKey);
  const pageUrl = sourcePageUrl(rowString(first, "video_id"), cards.length > 0);
  const topics = publicTopicPairs(rows.results);
  return {
    schema: "base2026.mcp.get_source.v1",
    found: true,
    id: rowString(first, "item_id") || sourceKey || rowString(first, "id"),
    source_id: sourceKey,
    item_id: rowString(first, "item_id"),
    video_id: rowString(first, "video_id") || null,
    platform: rowString(first, "platform") || "tiktok",
    title: rowString(first, "title") || null,
    creator: {
      handle: rowString(first, "creator_handle") || rowString(first, "handle") || null,
      display_name: rowString(first, "creator_display_name") || null,
      url: safeExternalUrl(rowString(first, "creator_url")),
    },
    published_date: rowString(first, "published_date") || rowString(first, "published_at") || null,
    source_url: safeExternalUrl(rowString(first, "source_url")),
    source_page_url: pageUrl,
    topics,
    passages: rows.results.map((row) => ({
      id: rowString(row, "chunk_id") || rowString(row, "id"),
      chunk_index: rowNumber(row, "chunk_index"),
      excerpt: truncate(rowString(row, "body"), MAX_EXCERPT_LENGTH),
      public_policy: rowString(row, "public_policy") || null,
      public_boundary: publicBoundary(),
    })),
    applied_projection_cards: cards.map(projectionCard),
    attribution: {
      original_source_url: safeExternalUrl(rowString(first, "source_url")),
      base2026_source_url: pageUrl,
    },
    public_boundary: publicBoundary(),
  };
}

async function distinctSourceRows(
  db: D1Database,
  where: string,
  params: string[],
  limit: number,
): Promise<PublicSourceRow[]> {
  const result = await db.prepare(
    `WITH ranked AS (
       SELECT d.*,
              ROW_NUMBER() OVER (
                PARTITION BY ${sourceKeyExpression()}
                ORDER BY d.published_date DESC, d.chunk_index ASC, d.id ASC
              ) AS source_rank
         FROM search_documents AS d
        WHERE d.full_transcript_public=0 AND ${where}
     )
     SELECT * FROM ranked
      WHERE source_rank=1
      ORDER BY published_date DESC, id ASC
      LIMIT ?`,
  ).bind(...params, limit).all<PublicSourceRow>();
  return result.results;
}

async function getCreator(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const handle = stringArgument(args, "handle", 1, MAX_HANDLE_LENGTH, true);
  const condition = handleCondition(handle);
  const count = await env.DB.prepare(
    `SELECT COUNT(DISTINCT ${sourceKeyExpression()}) AS source_count
       FROM search_documents AS d
      WHERE d.full_transcript_public=0 AND ${condition.sql}`,
  ).bind(...condition.params).first<{ source_count: number | string }>();
  const sourceCount = rowNumber(count ?? {}, "source_count");
  if (!sourceCount) {
    return {
      schema: "base2026.mcp.get_creator.v1",
      found: false,
      handle,
      public_boundary: publicBoundary(),
    };
  }
  const topicRows = await env.DB.prepare(
    `SELECT st.topic_id, MAX(st.topic_label) AS topic_label,
            COUNT(DISTINCT ${sourceKeyExpression()}) AS source_count
       FROM search_topics AS st
       JOIN search_documents AS d ON d.id=st.document_id
      WHERE d.full_transcript_public=0 AND ${condition.sql}
      GROUP BY st.topic_id
      ORDER BY source_count DESC, st.topic_id ASC
      LIMIT ?`,
  ).bind(...condition.params, MAX_CREATOR_TOPICS).all<JsonRecord>();
  const sampleRows = await distinctSourceRows(
    env.DB,
    condition.sql,
    condition.params,
    MAX_CREATOR_SOURCES,
  );
  const first = sampleRows[0] ?? {};
  return {
    schema: "base2026.mcp.get_creator.v1",
    found: true,
    handle,
    creator: {
      handle: rowString(first, "creator_handle") || rowString(first, "handle") || handle,
      display_name: rowString(first, "creator_display_name") || null,
      url: safeExternalUrl(rowString(first, "creator_url")),
    },
    source_count: sourceCount,
    topics: topicRows.results.map((row) => ({
      id: rowString(row, "topic_id"),
      label: rowString(row, "topic_label") || rowString(row, "topic_id"),
      source_count: rowNumber(row, "source_count"),
    })),
    sources: sampleRows.map((row) => sourceSummary(row)),
    public_boundary: publicBoundary(),
  };
}

async function topicMetrics(db: D1Database, topicId: string): Promise<JsonRecord | null> {
  const row = await db.prepare(
    `SELECT COUNT(DISTINCT ${sourceKeyExpression()}) AS source_count,
            COUNT(DISTINCT NULLIF(d.creator_handle, '')) AS creator_count,
            MAX(st.topic_label) AS topic_label,
            COUNT(DISTINCT CASE WHEN r.status='applied' THEN c.card_id END) AS public_insight_count
       FROM search_topics AS st
       JOIN search_documents AS d ON d.id=st.document_id
       LEFT JOIN public_projection_cards AS c ON c.search_id=d.id
       LEFT JOIN public_projection_receipts AS r ON r.projection_id=c.projection_id
      WHERE d.full_transcript_public=0 AND st.topic_id=?`,
  ).bind(topicId).first<JsonRecord>();
  if (!row || rowNumber(row, "source_count") === 0) return null;
  return {
    topic_id: topicId,
    topic_label: rowString(row, "topic_label") || topicId,
    source_count: rowNumber(row, "source_count"),
    creator_count: rowNumber(row, "creator_count"),
    public_insight_count: rowNumber(row, "public_insight_count"),
  };
}

async function getTopic(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const topicId = stringArgument(args, "topic_id", 1, MAX_TOPIC_ID_LENGTH, true);
  const metrics = await topicMetrics(env.DB, topicId);
  if (!metrics) {
    return {
      schema: "base2026.mcp.get_topic.v1",
      found: false,
      topic_id: topicId,
      public_boundary: publicBoundary(),
    };
  }
  const condition = "EXISTS (SELECT 1 FROM search_topics AS st_filter WHERE st_filter.document_id=d.id AND st_filter.topic_id=?)";
  const sampleRows = await distinctSourceRows(env.DB, condition, [topicId], MAX_TOPIC_SOURCES);
  const creatorRows = await env.DB.prepare(
    `SELECT d.creator_handle AS handle,
            COUNT(DISTINCT ${sourceKeyExpression()}) AS source_count
       FROM search_topics AS st
       JOIN search_documents AS d ON d.id=st.document_id
      WHERE d.full_transcript_public=0 AND st.topic_id=? AND d.creator_handle<>''
      GROUP BY d.creator_handle
      ORDER BY source_count DESC, d.creator_handle ASC
      LIMIT ?`,
  ).bind(topicId, MAX_TOPIC_CREATORS).all<JsonRecord>();
  return {
    schema: "base2026.mcp.get_topic.v1",
    found: true,
    ...metrics,
    creators: creatorRows.results.map((row) => ({
      handle: rowString(row, "handle"),
      source_count: rowNumber(row, "source_count"),
    })),
    sources: sampleRows.map((row) => sourceSummary(row)),
    public_boundary: publicBoundary(),
  };
}

async function getTopicSignal(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const topicId = stringArgument(args, "topic_id", 1, MAX_TOPIC_ID_LENGTH, true);
  const metrics = await topicMetrics(env.DB, topicId);
  if (!metrics) {
    return {
      schema: "base2026.mcp.get_topic_signal.v1",
      found: false,
      topic_id: topicId,
      public_boundary: publicBoundary(),
    };
  }
  const sourceCount = rowNumber(metrics, "source_count");
  const creatorCount = rowNumber(metrics, "creator_count");
  const publicInsightCount = rowNumber(metrics, "public_insight_count");
  const strong = sourceCount >= 5 && creatorCount >= 2 && publicInsightCount >= 3;
  return {
    schema: "base2026.mcp.get_topic_signal.v1",
    found: true,
    topic_id: rowString(metrics, "topic_id"),
    topic_label: rowString(metrics, "topic_label"),
    signal: {
      status: strong ? "strong" : "insufficient_evidence",
      thresholds: { source_count: 5, creator_count: 2, public_insight_count: 3 },
      observed: {
        source_count: sourceCount,
        creator_count: creatorCount,
        public_insight_count: publicInsightCount,
      },
      method: "deterministic_public_d1_counts",
    },
    public_boundary: publicBoundary(),
  };
}

async function getPublicManifest(env: PublicMcpEnv, args: JsonRecord): Promise<JsonRecord> {
  if (Object.keys(args).length) throw new PublicMcpError("UNSUPPORTED_ARGUMENT", "get_public_manifest accepts no arguments");
  if (!env.DB) throw new PublicMcpError("DB_NOT_CONFIGURED", "D1 public search database is not configured");
  const metrics = await env.DB.prepare(
    `SELECT
       (SELECT COUNT(*) FROM search_documents WHERE full_transcript_public=0) AS search_documents,
       (SELECT COUNT(DISTINCT NULLIF(video_id, '')) FROM search_documents WHERE full_transcript_public=0) AS distinct_videos,
       (SELECT COUNT(*) FROM public_projection_receipts WHERE status='applied') AS applied_projections,
       (SELECT COUNT(*) FROM public_projection_cards AS c JOIN public_projection_receipts AS r ON r.projection_id=c.projection_id WHERE r.status='applied') AS projected_cards,
       (SELECT COUNT(*) FROM search_documents WHERE full_transcript_public=1) AS full_transcript_public_rows`,
  ).first<JsonRecord>();
  return {
    schema: "base2026.public-manifest.v1",
    status: "live_d1_read_only",
    origin: PUBLIC_ORIGIN,
    counts: {
      search_documents: rowNumber(metrics ?? {}, "search_documents"),
      distinct_videos: rowNumber(metrics ?? {}, "distinct_videos"),
      applied_projections: rowNumber(metrics ?? {}, "applied_projections"),
      projected_cards: rowNumber(metrics ?? {}, "projected_cards"),
      full_transcript_public_rows: rowNumber(metrics ?? {}, "full_transcript_public_rows"),
    },
    endpoints: {
      search_api: `${PUBLIC_ORIGIN}/api/search/multi-search`,
      mcp: MCP_ENDPOINT,
      manifest: `${PUBLIC_ORIGIN}/static/manifest.json`,
      data_dictionary: `${PUBLIC_ORIGIN}/data-dictionary.json`,
      api_index: `${PUBLIC_ORIGIN}/api-index.json`,
    },
    policy: publicBoundary(),
  };
}

const TOOL_DEFINITIONS = [
  {
    name: "search_sources",
    title: "Search public sources",
    description: "Search distinct reviewed public video sources with bounded filters and attributable excerpts.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: { type: "string", description: "A short full-text query. Empty returns recent public sources.", maxLength: MAX_QUERY_LENGTH },
        creator_handle: { type: "string", description: "Optional creator handle, with or without @.", maxLength: MAX_HANDLE_LENGTH },
        topic_id: { type: "string", description: "Optional exact public topic ID.", maxLength: MAX_TOPIC_ID_LENGTH },
        platform: { type: "string", description: "Optional platform filter; the current public corpus is TikTok.", maxLength: MAX_PLATFORM_LENGTH },
        limit: { type: "integer", minimum: 1, maximum: MAX_TOOL_LIMIT, default: 10 },
        offset: { type: "integer", minimum: 0, maximum: MAX_TOOL_OFFSET, default: 0 },
      },
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: "get_source",
    title: "Get a public source",
    description: "Resolve a source_id, item_id, video_id, or post_id to bounded public passages, attribution, and applied evidence cards.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        source_id: { type: "string", description: "A public source ID or accepted source alias.", minLength: 1, maxLength: MAX_SOURCE_ID_LENGTH },
      },
      required: ["source_id"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: "get_creator",
    title: "Get a public creator",
    description: "Find a public creator profile, topic distribution, and bounded source samples by handle.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        handle: { type: "string", description: "Creator handle, with or without @.", minLength: 1, maxLength: MAX_HANDLE_LENGTH },
      },
      required: ["handle"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: "get_topic",
    title: "Get a public topic",
    description: "Resolve an exact public topic ID to counts, creator distribution, and bounded source samples.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        topic_id: { type: "string", description: "Exact public topic ID from the API facets or data files.", minLength: 1, maxLength: MAX_TOPIC_ID_LENGTH },
      },
      required: ["topic_id"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: "get_topic_signal",
    title: "Get a topic signal",
    description: "Return the deterministic strong-topic gate over current public D1 counts; it is not a ranking or real-time trend claim.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        topic_id: { type: "string", description: "Exact public topic ID.", minLength: 1, maxLength: MAX_TOPIC_ID_LENGTH },
      },
      required: ["topic_id"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: "get_public_manifest",
    title: "Get the public manifest",
    description: "Return current public D1 dimensions, public endpoint links, and the read-only privacy boundary.",
    inputSchema: { type: "object", additionalProperties: false, properties: {} },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
] as const;

function stringArgument(
  args: JsonRecord,
  field: string,
  minLength: number,
  maxLength: number,
  required: boolean,
): string {
  const value = args[field];
  if (value === undefined && !required) return "";
  if (typeof value !== "string") throw new PublicMcpError("INVALID_ARGUMENT", `${field} must be a string`);
  const trimmed = value.trim();
  if (trimmed.length < minLength) throw new PublicMcpError("INVALID_ARGUMENT", `${field} is required`);
  if (trimmed.length > maxLength) throw new PublicMcpError("INVALID_ARGUMENT", `${field} exceeds ${maxLength} characters`);
  if (/[\u0000-\u001f\u007f]/u.test(trimmed)) throw new PublicMcpError("INVALID_ARGUMENT", `${field} contains invalid characters`);
  return trimmed;
}

function integerArgument(args: JsonRecord, field: string, min: number, max: number, fallback: number): number {
  const value = args[field];
  if (value === undefined) return fallback;
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < min || value > max) {
    throw new PublicMcpError("INVALID_ARGUMENT", `${field} must be an integer between ${min} and ${max}`);
  }
  return value;
}

function validateToolArguments(name: string, value: unknown): JsonRecord {
  const args = value === undefined ? {} : value;
  if (!isRecord(args)) throw new PublicMcpError("INVALID_ARGUMENT", "tool arguments must be a JSON object");
  const allowed = new Set<string>(
    name === "search_sources"
      ? ["query", "creator_handle", "topic_id", "platform", "limit", "offset"]
      : name === "get_source"
        ? ["source_id"]
        : name === "get_creator"
          ? ["handle"]
          : name === "get_topic" || name === "get_topic_signal"
            ? ["topic_id"]
            : [],
  );
  for (const key of Object.keys(args)) {
    if (!allowed.has(key)) throw new PublicMcpError("UNSUPPORTED_ARGUMENT", `${name} does not accept ${key}`);
  }
  if (name === "search_sources") {
    stringArgument(args, "query", 0, MAX_QUERY_LENGTH, false);
    stringArgument(args, "creator_handle", 0, MAX_HANDLE_LENGTH, false);
    stringArgument(args, "topic_id", 0, MAX_TOPIC_ID_LENGTH, false);
    stringArgument(args, "platform", 0, MAX_PLATFORM_LENGTH, false);
    integerArgument(args, "limit", 1, MAX_TOOL_LIMIT, 10);
    integerArgument(args, "offset", 0, MAX_TOOL_OFFSET, 0);
  }
  if (name === "get_source") stringArgument(args, "source_id", 1, MAX_SOURCE_ID_LENGTH, true);
  if (name === "get_creator") {
    const handle = stringArgument(args, "handle", 1, MAX_HANDLE_LENGTH, true);
    if (!/^@?[A-Za-z0-9_.-]+$/u.test(handle)) throw new PublicMcpError("INVALID_ARGUMENT", "handle has an unsupported format");
  }
  if (name === "get_topic" || name === "get_topic_signal") stringArgument(args, "topic_id", 1, MAX_TOPIC_ID_LENGTH, true);
  return args;
}

async function runTool(env: PublicMcpEnv, name: string, rawArguments: unknown): Promise<JsonRecord> {
  const args = validateToolArguments(name, rawArguments);
  switch (name) {
    case "search_sources": return searchSources(env, args);
    case "get_source": return getSource(env, args);
    case "get_creator": return getCreator(env, args);
    case "get_topic": return getTopic(env, args);
    case "get_topic_signal": return getTopicSignal(env, args);
    case "get_public_manifest": return getPublicManifest(env, args);
    default: throw new PublicMcpError("UNKNOWN_TOOL", `tool ${name} is not available`);
  }
}

function jsonRpcResult(id: JsonRpcId, result: unknown): JsonRecord {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(id: JsonRpcId, code: number, message: string, data?: unknown): JsonRecord {
  return {
    jsonrpc: "2.0",
    id,
    error: { code, message, ...(data === undefined ? {} : { data }) },
  };
}

function mcpOriginAllowed(origin: string | null): boolean {
  if (!origin) return true;
  try {
    const parsed = new URL(origin);
    if (
      parsed.protocol === "https:"
      && parsed.port === ""
      && (parsed.hostname === "base2026.dev" || parsed.hostname === "www.base2026.dev")
    ) return true;
    return parsed.protocol === "http:" && (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1");
  } catch {
    return false;
  }
}

function decodeMcpHeader(value: string): string {
  if (/^=\?base64\?.+\?=$/u.test(value)) {
    const encoded = value.slice("=?base64?".length, -2);
    try {
      const binary = atob(encoded);
      const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
      return new TextDecoder().decode(bytes);
    } catch {
      throw new McpHttpError(400, -32020, "MCP header contains invalid base64 encoding");
    }
  }
  if (/[\u0000-\u001f\u007f-\u009f]/u.test(value)) {
    throw new McpHttpError(400, -32020, "MCP header contains invalid characters");
  }
  return value;
}

function requestId(message: JsonRecord): JsonRpcId {
  if (!hasOwn(message, "id")) return null;
  const value = message.id;
  if (value === null || typeof value === "string") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  throw new McpHttpError(400, -32600, "JSON-RPC id must be a string, number, or null");
}

function requestMeta(message: JsonRpcRequest): { params: JsonRecord; meta: JsonRecord; version?: string } {
  const params = message.params === undefined ? {} : message.params;
  if (!isRecord(params)) throw new McpHttpError(400, -32602, "JSON-RPC params must be an object");
  const meta = isRecord(params._meta)
    ? params._meta
    : isRecord(message._meta)
      ? message._meta
      : {};
  const version = typeof meta["io.modelcontextprotocol/protocolVersion"] === "string"
    ? meta["io.modelcontextprotocol/protocolVersion"]
    : undefined;
  return { params, meta, version };
}

function resolveProtocolVersion(request: Request, message: JsonRpcRequest): string {
  const { params, version: bodyVersion } = requestMeta(message);
  const headerVersion = request.headers.get("MCP-Protocol-Version");
  const legacyVersion = message.method === "initialize" && typeof params.protocolVersion === "string"
    ? params.protocolVersion
    : undefined;
  if (headerVersion && bodyVersion && headerVersion !== bodyVersion) {
    throw new McpHttpError(400, -32020, "MCP-Protocol-Version does not match request metadata");
  }
  const requested = headerVersion ?? bodyVersion ?? legacyVersion ?? DEFAULT_LEGACY_PROTOCOL_VERSION;
  if (!(SUPPORTED_PROTOCOL_VERSIONS as readonly string[]).includes(requested)) {
    throw new McpHttpError(400, -32022, "Unsupported MCP protocol version");
  }
  if (requested === MODERN_PROTOCOL_VERSION && (!headerVersion || !bodyVersion)) {
    throw new McpHttpError(400, -32020, "modern MCP requests require MCP-Protocol-Version and request metadata");
  }
  return requested;
}

function validateRequestHeaders(request: Request, message: JsonRpcRequest, version: string): void {
  const methodHeader = request.headers.get("Mcp-Method");
  if (methodHeader && decodeMcpHeader(methodHeader) !== message.method) {
    throw new McpHttpError(400, -32020, "Mcp-Method does not match the JSON-RPC method");
  }
  const { params } = requestMeta(message);
  const nameHeader = request.headers.get("Mcp-Name");
  if (nameHeader) {
    const decodedName = decodeMcpHeader(nameHeader);
    if (message.method !== "tools/call" || typeof params.name !== "string" || decodedName !== params.name) {
      throw new McpHttpError(400, -32020, "Mcp-Name does not match the tool name");
    }
  }
  if (version === MODERN_PROTOCOL_VERSION) {
    if (!methodHeader) throw new McpHttpError(400, -32020, "modern MCP requests require Mcp-Method");
    if (message.method === "tools/call" && !nameHeader) throw new McpHttpError(400, -32020, "tools/call requires Mcp-Name");
  }
}

function mcpHeaders(request: Request, extra: HeadersInit = {}): Headers {
  const origin = request.headers.get("Origin");
  const allowOrigin = origin && mcpOriginAllowed(origin) ? origin : origin ? null : "*";
  const headers = new Headers({
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id",
    "Access-Control-Expose-Headers": "MCP-Protocol-Version",
    Vary: "Origin, Accept",
    ...(allowOrigin ? { "Access-Control-Allow-Origin": allowOrigin } : {}),
    ...extra,
  });
  return headers;
}

function mcpResponse(request: Request, payload: JsonRecord | null, status = 200, extra: HeadersInit = {}): Response {
  return new Response(payload === null ? null : JSON.stringify(payload), {
    status,
    headers: mcpHeaders(request, extra),
  });
}

function httpErrorResponse(request: Request, id: JsonRpcId, error: McpHttpError): Response {
  const data = error.code === -32022
    ? { supported: [...SUPPORTED_PROTOCOL_VERSIONS] }
    : undefined;
  const requestedVersion = request.headers.get("MCP-Protocol-Version");
  const responseVersion = requestedVersion && (SUPPORTED_PROTOCOL_VERSIONS as readonly string[]).includes(requestedVersion)
    ? requestedVersion
    : undefined;
  return mcpResponse(request, jsonRpcError(id, error.code, error.message, data), error.status, {
    ...(responseVersion ? { "MCP-Protocol-Version": responseVersion } : {}),
  });
}

async function readBoundedBody(request: Request): Promise<string> {
  const contentLength = request.headers.get("content-length");
  if (contentLength && /^\d+$/u.test(contentLength) && Number(contentLength) > MAX_BODY_BYTES) {
    throw new McpHttpError(413, -32600, `request body exceeds ${MAX_BODY_BYTES} bytes`);
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
        throw new McpHttpError(413, -32600, `request body exceeds ${MAX_BODY_BYTES} bytes`);
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

function toolResult(payload: JsonRecord, isError = false): JsonRecord {
  return {
    resultType: "complete",
    content: [{ type: "text", text: JSON.stringify(payload) }],
    structuredContent: payload,
    isError,
  };
}

function toolFailure(error: unknown): JsonRecord {
  if (error instanceof PublicMcpError) {
    return {
      schema: "base2026.mcp.tool-error.v1",
      found: false,
      error: { code: error.code, message: error.message, ...(error.details ? { details: error.details } : {}) },
      public_boundary: publicBoundary(),
    };
  }
  return {
    schema: "base2026.mcp.tool-error.v1",
    found: false,
    error: { code: "PUBLIC_DATA_UNAVAILABLE", message: "public data could not be read" },
    public_boundary: publicBoundary(),
  };
}

function discoverResult(): JsonRecord {
  return {
    resultType: "complete",
    supportedVersions: [...SUPPORTED_PROTOCOL_VERSIONS],
    capabilities: { tools: {} },
    _meta: { "io.modelcontextprotocol/serverInfo": { name: "base2026-public-mcp", version: MCP_SERVER_VERSION } },
    instructions: "Use only the read-only public evidence tools. Preserve original source URLs and Base2026 source pages when citing results. Do not infer private data, raw transcripts, real-time coverage, or rankings.",
    ttlMs: 300_000,
    cacheScope: "public",
  };
}

function initializeResult(version: string): JsonRecord {
  return {
    protocolVersion: version,
    capabilities: { tools: { listChanged: false } },
    serverInfo: { name: "base2026-public-mcp", version: MCP_SERVER_VERSION },
    instructions: "This is a public read-only Base2026 evidence surface. Cite original source URLs and any returned Base2026 source pages; no write, private, raw-transcript, or media tools are available.",
  };
}

function toolsListResult(): JsonRecord {
  return {
    resultType: "complete",
    tools: TOOL_DEFINITIONS,
    ttlMs: 300_000,
    cacheScope: "public",
  };
}

export async function handlePublicMcp(request: Request, env: PublicMcpEnv): Promise<Response> {
  if (!mcpOriginAllowed(request.headers.get("Origin"))) {
    return mcpResponse(request, jsonRpcError(null, -32000, "Origin is not allowed for the public MCP endpoint"), 403);
  }
  if (request.method === "OPTIONS") return mcpResponse(request, null, 204);
  if (request.method !== "POST") {
    return mcpResponse(request, jsonRpcError(null, -32600, "MCP endpoint accepts POST requests only"), 405, { Allow: "POST, OPTIONS" });
  }
  const contentType = request.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase();
  if (contentType !== "application/json") {
    return mcpResponse(request, jsonRpcError(null, -32600, "MCP requests require Content-Type: application/json"), 415);
  }

  let message: JsonRpcRequest;
  try {
    const body = await readBoundedBody(request);
    if (!body.trim()) throw new McpHttpError(400, -32700, "MCP request body must be valid JSON");
    const parsed: unknown = JSON.parse(body);
    if (!isRecord(parsed) || typeof parsed.jsonrpc !== "string" || typeof parsed.method !== "string") {
      throw new McpHttpError(400, -32600, "MCP request must be one JSON-RPC 2.0 request object");
    }
    message = parsed as JsonRpcRequest;
    if (message.jsonrpc !== "2.0") throw new McpHttpError(400, -32600, "MCP requests must use JSON-RPC 2.0");
  } catch (error) {
    if (error instanceof SyntaxError) return mcpResponse(request, jsonRpcError(null, -32700, "MCP request body must be valid JSON"), 400);
    if (error instanceof McpHttpError) return httpErrorResponse(request, null, error);
    return mcpResponse(request, jsonRpcError(null, -32600, "MCP request could not be parsed"), 400);
  }

  let id: JsonRpcId = null;
  try {
    id = requestId(message);
    const version = resolveProtocolVersion(request, message);
    validateRequestHeaders(request, message, version);
    const { params } = requestMeta(message);
    const responseHeaders = { "MCP-Protocol-Version": version };

    if (message.method === "notifications/initialized" || message.method === "notifications/cancelled") {
      return mcpResponse(request, null, 202, responseHeaders);
    }
    if (message.method === "server/discover") return mcpResponse(request, jsonRpcResult(id, discoverResult()), 200, responseHeaders);
    if (message.method === "initialize") return mcpResponse(request, jsonRpcResult(id, initializeResult(version)), 200, responseHeaders);
    if (message.method === "ping") return mcpResponse(request, jsonRpcResult(id, {}), 200, responseHeaders);
    if (message.method === "tools/list") return mcpResponse(request, jsonRpcResult(id, toolsListResult()), 200, responseHeaders);
    if (message.method === "tools/call") {
      if (typeof params.name !== "string" || !params.name) {
        return mcpResponse(request, jsonRpcError(id, -32602, "tools/call requires params.name"), 200, responseHeaders);
      }
      const tool = TOOL_DEFINITIONS.find((definition) => definition.name === params.name);
      if (!tool) {
        return mcpResponse(request, jsonRpcError(id, -32602, `tool ${params.name} is not available`), 200, responseHeaders);
      }
      try {
        const payload = await runTool(env, params.name, params.arguments);
        return mcpResponse(request, jsonRpcResult(id, toolResult(payload)), 200, responseHeaders);
      } catch (error) {
        if (!(error instanceof PublicMcpError)) console.error(JSON.stringify({ event: "base2026_mcp_tool_error", tool: params.name }));
        return mcpResponse(request, jsonRpcResult(id, toolResult(toolFailure(error), true)), 200, responseHeaders);
      }
    }
    return mcpResponse(
      request,
      jsonRpcError(id, -32601, `MCP method ${message.method} is not available`, { supported: ["server/discover", "tools/list", "tools/call", "ping"] }),
      404,
      responseHeaders,
    );
  } catch (error) {
    if (error instanceof McpHttpError) return httpErrorResponse(request, id ?? null, error);
    if (error instanceof PublicMcpError) {
      return mcpResponse(request, jsonRpcResult(id ?? null, toolResult(toolFailure(error), true)), 200);
    }
    console.error(JSON.stringify({ event: "base2026_mcp_request_error" }));
    return mcpResponse(request, jsonRpcError(id ?? null, -32603, "MCP request could not be completed"), 500);
  }
}
