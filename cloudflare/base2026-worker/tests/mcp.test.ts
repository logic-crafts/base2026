import { describe, expect, it } from "vitest";
import worker from "../src/index";

const MODERN_PROTOCOL_VERSION = "2026-07-28";

type PublicRow = Record<string, unknown>;

const SOURCE_ROWS: PublicRow[] = [
  {
    id: "chunk-a-0",
    item_id: "item-a",
    source_id: "source-a",
    chunk_id: "chunk-a-0",
    chunk_index: 0,
    body: "Public evidence about AI search visibility.",
    creator_display_name: "Example Creator",
    creator_handle: "@example",
    creator_url: "https://www.tiktok.com/@example",
    full_transcript_public: 0,
    handle: "@example",
    platform: "tiktok",
    post_id: "post-a",
    public_policy: "search_passage",
    published_date: "2026-08-30",
    source_url: "https://www.tiktok.com/@example/video/1234567890123",
    title: "AI search visibility",
    video_id: "1234567890123",
    topics_json: '["ai-search"]',
    topic_labels_json: '["AI search"]',
  },
  {
    id: "chunk-a-1",
    item_id: "item-a",
    source_id: "source-a",
    chunk_id: "chunk-a-1",
    chunk_index: 1,
    body: "A second bounded passage from the same public source.",
    creator_display_name: "Example Creator",
    creator_handle: "@example",
    creator_url: "https://www.tiktok.com/@example",
    full_transcript_public: 0,
    handle: "@example",
    platform: "tiktok",
    post_id: "post-a",
    public_policy: "search_passage",
    published_date: "2026-08-30",
    source_url: "https://www.tiktok.com/@example/video/1234567890123",
    title: "AI search visibility",
    video_id: "1234567890123",
    topics_json: '["ai-search"]',
    topic_labels_json: '["AI search"]',
  },
  {
    id: "chunk-b-0",
    item_id: "item-b",
    source_id: "source-b",
    chunk_id: "chunk-b-0",
    chunk_index: 0,
    body: "Another public source for deterministic test coverage.",
    creator_display_name: "Second Creator",
    creator_handle: "@second",
    creator_url: "https://www.tiktok.com/@second",
    full_transcript_public: 0,
    handle: "@second",
    platform: "tiktok",
    post_id: "post-b",
    public_policy: "search_passage",
    published_date: "2026-08-29",
    source_url: "https://www.tiktok.com/@second/video/2234567890123",
    title: "Public research source",
    video_id: "2234567890123",
    topics_json: '["research"]',
    topic_labels_json: '["Research"]',
  },
];

const PROJECTION_CARDS: PublicRow[] = [
  {
    ordinal: 0,
    claim_text: "A bounded public evidence claim.",
    suggested_action: "Cite the source and verify the context.",
    topic_label: "AI search",
    evidence_excerpt: "A short public excerpt with a timecode.",
    evidence_start_seconds: 4,
    evidence_end_seconds: 18,
  },
];

class FakeMcpStatement {
  parameters: unknown[] = [];

  constructor(private readonly sql: string, private readonly db: FakeMcpDatabase) {}

  bind(...parameters: unknown[]): FakeMcpStatement {
    this.parameters = parameters;
    return this;
  }

  async first<T>(): Promise<T | null> {
    if (this.sql.includes("AS count")) return { count: 2 } as T;
    if (this.sql.includes("AS source_count") && !this.sql.includes("public_insight_count")) return { source_count: 2 } as T;
    if (this.sql.includes("AS public_insight_count")) {
      return {
        source_count: 5,
        creator_count: 2,
        topic_label: "AI search",
        public_insight_count: 3,
      } as T;
    }
    if (this.sql.includes("AS search_documents")) {
      return {
        search_documents: 2150,
        distinct_videos: 1563,
        applied_projections: 39,
        projected_cards: 78,
        full_transcript_public_rows: 0,
      } as T;
    }
    return null;
  }

  async all<T>(): Promise<{ results: T[] }> {
    if (this.sql.includes("public_projection_cards")) return { results: PROJECTION_CARDS as T[] };
    if (this.sql.includes("SELECT st.topic_id")) {
      return { results: [{ topic_id: "ai-search", topic_label: "AI search", source_count: 2 }] as T[] };
    }
    if (this.sql.includes("SELECT d.creator_handle AS handle")) {
      return { results: [{ handle: "@example", source_count: 2 }] as T[] };
    }
    if (this.sql.includes("AND (d.source_id=?")) {
      const sourceId = String(this.parameters[0] ?? "");
      return {
        results: this.db.rows.filter((row) => ["source_id", "item_id", "video_id", "post_id"].some((key) => row[key] === sourceId)) as T[],
      };
    }
    if (this.sql.includes("WITH matched")) {
      const limit = Number(this.parameters[this.parameters.length - 2] ?? this.db.rows.length);
      const offset = Number(this.parameters[this.parameters.length - 1] ?? 0);
      return { results: this.db.rows.slice(offset, offset + limit) as T[] };
    }
    if (this.sql.includes("WITH ranked")) {
      const limit = Number(this.parameters[this.parameters.length - 1] ?? this.db.rows.length);
      return { results: this.db.rows.slice(0, limit) as T[] };
    }
    return { results: [] };
  }
}

class FakeMcpDatabase {
  readonly rows = SOURCE_ROWS;
  prepareCalls = 0;

  prepare(sql: string): FakeMcpStatement {
    this.prepareCalls += 1;
    return new FakeMcpStatement(sql, this);
  }
}

class FakeMcpRateLimit {
  calls = 0;

  constructor(readonly allowed = true) {}

  async limit(_options: { key: string }): Promise<{ success: boolean }> {
    this.calls += 1;
    return { success: this.allowed };
  }
}

function env(db = new FakeMcpDatabase(), rateLimit = new FakeMcpRateLimit()): Env {
  return {
    DB: db as unknown as D1Database,
    MCP_RATE_LIMIT: rateLimit,
  } as unknown as Env;
}

function envWithoutRateLimit(db = new FakeMcpDatabase()): Env {
  return { DB: db as unknown as D1Database } as unknown as Env;
}

function modernRequest(method: string, id: string | number, params: Record<string, unknown> = {}): Request {
  const bodyParams = {
    ...params,
    _meta: {
      "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL_VERSION,
    },
  };
  const headers = new Headers({
    "Content-Type": "application/json",
    "MCP-Protocol-Version": MODERN_PROTOCOL_VERSION,
    "Mcp-Method": method,
  });
  if (method === "tools/call" && typeof params.name === "string") headers.set("Mcp-Name", params.name);
  return new Request("https://base2026.dev/api/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params: bodyParams }),
  });
}

function modernNotification(method: string, params: Record<string, unknown> = {}): Request {
  const bodyParams = {
    ...params,
    _meta: {
      "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL_VERSION,
    },
  };
  const headers = new Headers({
    "Content-Type": "application/json",
    "MCP-Protocol-Version": MODERN_PROTOCOL_VERSION,
    "Mcp-Method": method,
  });
  if (method === "tools/call" && typeof params.name === "string") headers.set("Mcp-Name", params.name);
  return new Request("https://base2026.dev/api/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", method, params: bodyParams }),
  });
}

async function responseJson(response: Response): Promise<Record<string, any>> {
  return (await response.json()) as Record<string, any>;
}

describe("Base2026 public MCP", () => {
  it("discovers the modern stateless server contract", async () => {
    const response = await worker.fetch(modernRequest("server/discover", "discover"), env(), {} as ExecutionContext);
    const payload = await responseJson(response);

    expect(response.status).toBe(200);
    expect(response.headers.get("MCP-Protocol-Version")).toBe(MODERN_PROTOCOL_VERSION);
    expect(payload.result.supportedVersions).toContain(MODERN_PROTOCOL_VERSION);
    expect(payload.result.capabilities).toEqual({ tools: {} });
  });

  it("lists only read-only public tools", async () => {
    const response = await worker.fetch(modernRequest("tools/list", "list"), env(), {} as ExecutionContext);
    const payload = await responseJson(response);
    const tools = payload.result.tools as Array<Record<string, any>>;

    expect(tools.map((tool) => tool.name)).toEqual([
      "search_sources",
      "get_source",
      "get_creator",
      "get_topic",
      "get_topic_signal",
      "get_public_manifest",
    ]);
    expect(tools.every((tool) => tool.annotations.readOnlyHint === true && tool.annotations.destructiveHint === false)).toBe(true);
  });

  it("runs bounded source search without private fields", async () => {
    const response = await worker.fetch(
      modernRequest("tools/call", "search", { name: "search_sources", arguments: { query: "AI evidence", limit: 1 } }),
      env(),
      {} as ExecutionContext,
    );
    const payload = await responseJson(response);
    const structured = payload.result.structuredContent as Record<string, any>;

    expect(response.status).toBe(200);
    expect(payload.result.isError).toBe(false);
    expect(structured.limit).toBe(1);
    expect(structured.results).toHaveLength(1);
    expect(JSON.stringify(structured.results)).not.toContain("raw_transcript");
    expect(JSON.stringify(structured.results)).not.toContain("private_payload");
    expect(structured.public_boundary).toMatchObject({ access: "public_read_only", writes: false });
  });

  it("resolves a source with bounded passages and applied public cards", async () => {
    const response = await worker.fetch(
      modernRequest("tools/call", "source", { name: "get_source", arguments: { source_id: "source-a" } }),
      env(),
      {} as ExecutionContext,
    );
    const payload = await responseJson(response);
    const source = payload.result.structuredContent as Record<string, any>;

    expect(source.found).toBe(true);
    expect(source.passages).toHaveLength(2);
    expect(source.applied_projection_cards).toHaveLength(1);
    expect(source.source_page_url).toBe("https://base2026.dev/sources/tiktok-video-1234567890123");
    expect(source.passages[0]).not.toHaveProperty("body");
    expect(source.applied_projection_cards[0]).not.toHaveProperty("raw_transcript");
  });

  it("returns live public dimensions through the manifest tool", async () => {
    const response = await worker.fetch(
      modernRequest("tools/call", "manifest", { name: "get_public_manifest", arguments: {} }),
      env(),
      {} as ExecutionContext,
    );
    const payload = await responseJson(response);
    const manifest = payload.result.structuredContent as Record<string, any>;

    expect(manifest.status).toBe("live_d1_read_only");
    expect(manifest.counts).toMatchObject({ search_documents: 2150, distinct_videos: 1563 });
    expect(manifest.endpoints.mcp).toBe("https://base2026.dev/api/mcp");
  });

  it("keeps legacy initialize compatibility without creating sessions", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/mcp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } },
        }),
      }),
      env(),
      {} as ExecutionContext,
    );
    const payload = await responseJson(response);

    expect(response.status).toBe(200);
    expect(response.headers.get("MCP-Protocol-Version")).toBe("2025-06-18");
    expect(payload.result.protocolVersion).toBe("2025-06-18");
  });

  it("rejects modern initialize while returning the complete modern ping result", async () => {
    const initialize = await worker.fetch(
      modernRequest("initialize", "modern-init", { capabilities: {}, clientInfo: { name: "test", version: "1" } }),
      env(),
      {} as ExecutionContext,
    );
    const ping = await worker.fetch(modernRequest("ping", "modern-ping"), env(), {} as ExecutionContext);
    const initializePayload = await responseJson(initialize);
    const pingPayload = await responseJson(ping);

    expect(initialize.status).toBe(404);
    expect(initializePayload.error.code).toBe(-32601);
    expect(ping.status).toBe(200);
    expect(pingPayload.result).toEqual({ resultType: "complete" });
  });

  it("accepts no-id tool notifications without touching D1", async () => {
    const db = new FakeMcpDatabase();
    const response = await worker.fetch(
      modernNotification("tools/call", { name: "search_sources", arguments: { query: "AI evidence" } }),
      env(db),
      {} as ExecutionContext,
    );

    expect(response.status).toBe(202);
    expect(await response.text()).toBe("");
    expect(db.prepareCalls).toBe(0);
  });

  it("fails closed when abuse protection is unavailable or exhausted", async () => {
    const missingBindingDb = new FakeMcpDatabase();
    const missingBinding = await worker.fetch(
      modernRequest("server/discover", "missing-binding"),
      envWithoutRateLimit(missingBindingDb),
      {} as ExecutionContext,
    );
    const limited = new FakeMcpRateLimit(false);
    const rateLimited = await worker.fetch(
      modernRequest("server/discover", "rate-limited"),
      env(new FakeMcpDatabase(), limited),
      {} as ExecutionContext,
    );
    const missingPayload = await responseJson(missingBinding);
    const limitedPayload = await responseJson(rateLimited);

    expect(missingBinding.status).toBe(503);
    expect(missingPayload.error.code).toBe(-32030);
    expect(missingBindingDb.prepareCalls).toBe(0);
    expect(rateLimited.status).toBe(429);
    expect(rateLimited.headers.get("Retry-After")).toBe("60");
    expect(limitedPayload.error.code).toBe(-32029);
    expect(limited.calls).toBe(1);
  });

  it("rejects protocol/header mismatches and non-POST transport", async () => {
    const mismatch = await worker.fetch(
      new Request("https://base2026.dev/api/mcp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "MCP-Protocol-Version": MODERN_PROTOCOL_VERSION,
          "Mcp-Method": "ping",
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: "mismatch",
          method: "ping",
          params: { _meta: { "io.modelcontextprotocol/protocolVersion": "2025-06-18" } },
        }),
      }),
      env(),
      {} as ExecutionContext,
    );
    const getResponse = await worker.fetch(new Request("https://base2026.dev/api/mcp"), env(), {} as ExecutionContext);
    const mismatchPayload = await responseJson(mismatch);
    const getPayload = await responseJson(getResponse);

    expect(mismatch.status).toBe(400);
    expect(mismatchPayload.error.code).toBe(-32020);
    expect(getResponse.status).toBe(405);
    expect(getPayload.error.message).toContain("POST");
  });

  it("accepts a notification without returning a JSON-RPC body", async () => {
    const response = await worker.fetch(
      modernRequest("notifications/initialized", "ignored"),
      env(),
      {} as ExecutionContext,
    );

    expect(response.status).toBe(202);
    expect(await response.text()).toBe("");
  });
});
