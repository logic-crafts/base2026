import { describe, expect, it } from "vitest";
import worker from "../src/index";

type FakeRow = Record<string, unknown> & {
  id: string;
  topics_json: string;
  topic_labels_json: string;
  full_transcript_public: number;
};

function fakeEvidenceRow(
  videoId = "7657638702864223510",
  creatorHandle = "@build_in_public",
  overrides: Record<string, unknown> = {},
): FakeRow {
  return {
    id: `chunk-${videoId}`,
    item_id: `tiktok-video-${videoId}`,
    source_id: `tiktok:${creatorHandle.slice(1)}:${videoId}`,
    chunk_id: `chunk-${videoId}`,
    chunk_index: 0,
    body: "AI search visibility depends on useful source evidence.",
    captured_at: "2026-08-19",
    creator_display_name: "",
    creator_handle: creatorHandle,
    creator_id: `tiktok-${creatorHandle.slice(1)}`,
    creator_url: `https://www.tiktok.com/${creatorHandle}`,
    full_transcript_public: 0,
    admission_state: "normal_public_card",
    handle: creatorHandle,
    platform: "tiktok",
    post_id: videoId,
    public_policy: "search_passage",
    public_surface: "main_search",
    published_at: "2026-08-19",
    published_date: "2026-08-19",
    source_type: "tiktok_video",
    source_url: `https://www.tiktok.com/${creatorHandle}/video/${videoId}`,
    title: "AI search visibility",
    title_source: "inventory_title",
    title_status: "raw",
    video_id: videoId,
    year: "2026",
    avatar_url: "/static/assets/creators/build-in-public.jpeg",
    topics_json: '["ai-search"]',
    topic_labels_json: '["AI search"]',
    claim_text: null,
    evidence_excerpt: null,
    evidence_start_seconds: null,
    evidence_end_seconds: null,
    ...overrides,
  };
}

class FakeStatement {
  parameters: unknown[] = [];

  constructor(private readonly sql: string, private readonly db: FakeDatabase) {}

  bind(...parameters: unknown[]): FakeStatement {
    this.parameters = parameters;
    return this;
  }

  async first<T>(): Promise<T | null> {
    if (this.sql.includes("SELECT 1 AS ok")) return { ok: 1 } as T;
    if (this.sql.includes("AS matched_records")) {
      return { matched_records: new Set(this.db.publicRows().map((row) => row.video_id || row.source_id)).size } as T;
    }
    if (this.sql.includes("AS document_count") && this.sql.includes("AS source_count")) {
      const rows = this.db.publicRows();
      const latest = rows.map((row) => String(row.captured_at ?? "")).sort().at(-1) ?? null;
      return {
        document_count: rows.length,
        source_count: new Set(rows.map((row) => row.video_id || row.source_id)).size,
        latest_captured_at: latest,
      } as T;
    }
    if (this.sql.includes("COUNT(*) AS count")) return { count: this.db.rows.length } as T;
    return null;
  }

  async all<T>(): Promise<{ results: T[] }> {
    if (this.sql.includes("LEFT JOIN public_projection_cards")) {
      const limit = Number(this.parameters.at(-1)) || this.db.rows.length;
      return { results: this.db.publicRows().slice(0, limit) as T[] };
    }
    if (this.sql.includes("GROUP BY")) {
      return { results: [{ value: "@build_in_public", count: this.db.rows.length }] as T[] };
    }
    return { results: this.db.rows as T[] };
  }
}

class FakeInboxDatabase {
  readonly rows: unknown[][] = [];

  prepare(sql: string): FakeStatement {
    return new FakeStatement(sql, new FakeDatabase());
  }

  async batch(statements: FakeStatement[]): Promise<unknown[]> {
    const insert = statements.find((statement) => statement.parameters.length > 0);
    if (insert) this.rows.push(insert.parameters);
    return statements.map(() => ({ success: true }));
  }
}

class FakeDatabase {
  readonly rows: FakeRow[];

  constructor(rows: FakeRow[] = [fakeEvidenceRow()]) {
    this.rows = rows;
  }

  publicRows(): FakeRow[] {
    return this.rows.filter((row) =>
      row.full_transcript_public === 0
      && row.admission_state === "normal_public_card"
      && typeof row.creator_handle === "string"
      && row.creator_handle.length > 0
      && typeof row.source_url === "string"
      && /^https:\/\/(?:www\.)?tiktok\.com\//u.test(row.source_url)
    );
  }

  prepare(sql: string): FakeStatement {
    return new FakeStatement(sql, this);
  }
}

class FakeSeoStatement {
  parameters: unknown[] = [];

  constructor(private readonly sql: string) {}

  bind(...parameters: unknown[]): FakeSeoStatement {
    this.parameters = parameters;
    return this;
  }

  async first<T>(): Promise<T | null> {
    return null;
  }

  async all<T>(): Promise<{ results: T[] }> {
    if (this.sql.includes("MAX(r.updated_at) AS lastmod")) {
      return {
        results: [{ video_id: "7657638702864223510", lastmod: "2026-08-28 04:00:00" }] as T[],
      };
    }
    if (this.sql.includes("FROM public_projection_receipts AS r") && this.parameters[0] === "7657638702864223510") {
      return {
        results: [{
          video_id: "7657638702864223510",
          source_id: "tiktok:test_creator:7657638702864223510",
          creator_handle: "@test_creator",
          creator_url: "https://www.tiktok.com/@test_creator",
          source_url: "https://www.tiktok.com/@test_creator/video/7657638702864223510",
          published_date: "2026-08-27",
          ordinal: 0,
          claim_text: "Useful <AI> source evidence",
          suggested_action: "Publish attributable evidence.",
          topic_label: "AI search",
          evidence_excerpt: "A short & public excerpt.",
          evidence_start_seconds: 4,
          evidence_end_seconds: 18,
        }] as T[],
      };
    }
    return { results: [] };
  }
}

class FakeSeoDatabase {
  prepare(sql: string): FakeSeoStatement {
    return new FakeSeoStatement(sql);
  }
}

type OutreachFakeRow = Record<string, unknown> & {
  id: string;
  topics_json: string;
  lanes_json: string;
};

class FakeOutreachStatement {
  parameters: unknown[] = [];

  constructor(private readonly sql: string, private readonly db: FakeOutreachDatabase) {}

  bind(...parameters: unknown[]): FakeOutreachStatement {
    this.parameters = parameters;
    return this;
  }

  async first<T>(): Promise<T | null> {
    if (this.sql.includes("COUNT(*) AS count")) return { count: this.db.rows.length } as T;
    return null;
  }

  async all<T>(): Promise<{ results: T[] }> {
    if (this.sql.includes("GROUP BY")) {
      const value = this.sql.includes("outreach_topics")
        ? "AI visibility"
        : this.sql.includes("outreach_lanes")
          ? "content"
          : this.sql.includes("source_status")
            ? "Одобрено"
            : this.sql.includes("platform")
              ? "Web"
              : this.sql.includes("cost")
                ? "Низкая"
                : this.sql.includes("complexity")
                  ? "Средняя"
                  : this.sql.includes("effect_speed")
                    ? "Быстрая"
                    : "ru";
      return { results: [{ value, count: this.db.rows.length }] as T[] };
    }
    return { results: this.db.rows as T[] };
  }
}

class FakeOutreachDatabase {
  readonly rows: OutreachFakeRow[] = [
    {
      id: "outreach-finding:OUT-001",
      collection: "outreach_findings",
      record_type: "finding",
      source_record_id: "OUT-001",
      title: "AI search visibility",
      summary: "A reviewed public finding about useful evidence.",
      tactic: "Publish useful source evidence",
      evidence_summary: "The source demonstrates an evidence-first tactic.",
      verdict: "Одобрено",
      source_url: "https://example.com/findings/1",
      platform: "Web",
      author_name: "Example Author",
      author_handle: "@example",
      observed_at: "2026-08-20",
      score: 80,
      source_status: "Одобрено",
      topics_json: '["AI visibility"]',
      lanes_json: '["content"]',
      cost: "Низкая",
      complexity: "Средняя",
      effect_speed: "Быстрая",
      public_policy: "reviewed_outreach_excerpt_v1",
      reviewed_at: "2026-08-21T00:00:00Z",
      source_hash: "a".repeat(64),
      dedup_key: "b".repeat(64),
      language: "ru",
    },
  ];

  prepare(sql: string): FakeOutreachStatement {
    return new FakeOutreachStatement(sql, this);
  }
}

function env(db = new FakeDatabase(), inbox = new FakeInboxDatabase(), outreach?: FakeOutreachDatabase): Env {
  return {
    DB: db as unknown as D1Database,
    INBOX_DB: inbox as unknown as D1Database,
    ...(outreach ? { OUTREACH_DB: outreach as unknown as D1Database } : {}),
  } as unknown as Env;
}

async function json(response: Response): Promise<Record<string, any>> {
  return (await response.json()) as Record<string, any>;
}

describe("Base2026 search Worker", () => {
  it("redirects the apex HTTP surface to the same HTTPS URL", async () => {
    const response = await worker.fetch(
      new Request("http://base2026.dev/workspace/?q=schema"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(301);
    expect(response.headers.get("location")).toBe("https://base2026.dev/workspace/?q=schema");
  });

  it("redirects broken legacy search-page aliases to the dedicated search workspace", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/search/index.html?source=legacy"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(301);
    expect(response.headers.get("location")).toBe("https://base2026.dev/workspace/?source=legacy");
  });

  it("reports a structured error for an unavailable D1 binding", async () => {
    const response = await worker.fetch(new Request("https://base2026.dev/api/health"), {} as Env, {} as ExecutionContext);
    expect(response.status).toBe(503);
    expect(await json(response)).toMatchObject({ error: { code: "DB_NOT_CONFIGURED" } });
  });

  it("renders an indexable source page for an applied D1 projection", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/sources/tiktok-video-7657638702864223510"),
      env(new FakeSeoDatabase() as unknown as FakeDatabase),
      {} as ExecutionContext,
    );
    const html = await response.text();
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    expect(html).toContain('<link rel="canonical" href="https://base2026.dev/sources/tiktok-video-7657638702864223510">');
    expect(html).toContain("Useful &lt;AI&gt; source evidence");
    expect(html).toContain("A short &amp; public excerpt.");
    expect(html).toContain("https://www.tiktok.com/@test_creator/video/7657638702864223510");
    expect(html).toContain('property="og:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png"');
    expect(html).toContain('name="twitter:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png"');
    expect(html).not.toContain("Useful <AI> source evidence");
  });

  it("exposes applied D1 projections through the dynamic sitemap", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/sitemap-dynamic.xml"),
      env(new FakeSeoDatabase() as unknown as FakeDatabase),
      {} as ExecutionContext,
    );
    const xml = await response.text();
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/xml");
    expect(xml).toContain("https://base2026.dev/sources/tiktok-video-7657638702864223510");
    expect(xml).toContain("<lastmod>2026-08-28</lastmod>");
  });

  it("returns an empty multi-search envelope for an empty query list", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ queries: [] }),
      }),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect(await json(response)).toEqual({ results: [] });
  });

  it("preserves the deployed evidence-brief v1 response contract", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief?q=AI%20search"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect(await json(response)).toMatchObject({
      query: "AI search",
      status: "limited",
      statement: expect.stringContaining("distinct attributed sources"),
      coverage: {
        matchingPassages: 1,
        selectedSources: 1,
        selectedCreators: 1,
        newestPublishedDate: "2026-08-19",
      },
      evidence: [{
        creator: "@build_in_public",
        sourceUrl: "https://www.tiktok.com/@build_in_public/video/7657638702864223510",
        sourcePageUrl: "https://base2026.dev/sources/tiktok-video-7657638702864223510",
      }],
      method: { id: "d1-fts5-evidence-brief-v1", synthesis: "deterministic-retrieval" },
    });
  });

  it("builds a deterministic evidence brief v2 from distinct public D1 sources", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=AI%20search"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toContain("s-maxage=300");
    expect(await json(response)).toMatchObject({
      brief_version: "base2026.evidence-brief.v2",
      question: "AI search",
      normalized_question: "ai search",
      status: "limited",
      corpus_version: "public-d1:1:1:2026-08-19",
      ranking_version: "d1-fts5-bm25-and-v2",
      generated_at: expect.any(String),
      coverage: {
        matched_records: 1,
        selected_sources: 1,
        distinct_creators: 1,
        published_date_min: "2026-08-19",
        published_date_max: "2026-08-19",
      },
      findings: [{
        claim: "AI search visibility",
        evidence_excerpt: "AI search visibility depends on useful source evidence.",
        creator_handle: "@build_in_public",
        base2026_url: "https://base2026.dev/sources/tiktok-video-7657638702864223510",
        original_source_url: "https://www.tiktok.com/@build_in_public/video/7657638702864223510",
        topics: ["AI search"],
      }],
      repeated_signals: [],
      limits: expect.arrayContaining([expect.stringContaining("not consensus")]),
    });
  });

  it("enforces five findings, two per creator, and reports repeated signals without synthesis", async () => {
    const rows = [
      fakeEvidenceRow("7657638702864223510", "@alpha"),
      fakeEvidenceRow("7657638702864223511", "@alpha"),
      fakeEvidenceRow("7657638702864223512", "@alpha"),
      fakeEvidenceRow("7657638702864223513", "@beta"),
      fakeEvidenceRow("7657638702864223514", "@beta"),
      fakeEvidenceRow("7657638702864223515", "@gamma"),
      fakeEvidenceRow("7657638702864223516", "@delta"),
    ];
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=What%20are%20experts%20saying%20about%20AI%20search%3F"),
      env(new FakeDatabase(rows)),
      {} as ExecutionContext,
    );
    const payload = await json(response);
    expect(response.status).toBe(200);
    expect(payload.status).toBe("full");
    expect(payload.findings).toHaveLength(5);
    expect(payload.findings.filter((finding: Record<string, unknown>) => finding.creator_handle === "@alpha")).toHaveLength(2);
    expect(payload.coverage).toMatchObject({ selected_sources: 5, distinct_creators: 3 });
    expect(payload.repeated_signals).toEqual([{ topic: "AI search", distinct_creators: 3 }]);
  });

  it("returns no_evidence when public attribution and privacy gates exclude every row", async () => {
    const rows = [
      fakeEvidenceRow("7657638702864223510", "@private", { full_transcript_public: 1 }),
      fakeEvidenceRow("7657638702864223511", "@held", { admission_state: "held_private" }),
      fakeEvidenceRow("7657638702864223512", "@invalid", { source_url: "https://example.com/video/1" }),
    ];
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=AI%20search%20visibility"),
      env(new FakeDatabase(rows)),
      {} as ExecutionContext,
    );
    const payload = await json(response);
    expect(response.status).toBe(200);
    expect(payload.status).toBe("no_evidence");
    expect(payload.findings).toEqual([]);
    expect(payload.limits).toContain("Not enough public evidence in Base2026 for this question.");
  });

  it("normalizes evidence questions and exposes accurate method semantics", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=%20HOW%20%20should%20schema%20support%20AI%20search%3F%20"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect((await json(response)).normalized_question).toBe("how should schema support ai search?");

    const head = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=AI%20search", { method: "HEAD" }),
      env(),
      {} as ExecutionContext,
    );
    expect(head.status).toBe(200);
    expect(await head.text()).toBe("");

    const post = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=AI%20search", { method: "POST" }),
      env(),
      {} as ExecutionContext,
    );
    expect(post.status).toBe(405);
    expect(post.headers.get("allow")).toBe("GET, HEAD");
  });

  it("rejects evidence-brief requests without a useful question", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/evidence-brief/v2?q=AI"),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(400);
    expect(await json(response)).toMatchObject({ error: { code: "QUERY_TOO_SHORT" } });
  });

  it("supports the legacy path, nested quoted filters and Meilisearch response fields", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/knowledge-search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          queries: [
            {
              indexUid: "base2026_public_tiktok",
              q: "AI search",
              limit: 5,
              facets: ["handle", "source_type", "year"],
              filter: [['"handle"="@build_in_public"']],
              attributesToHighlight: ["body", "title", "handle"],
              highlightPreTag: "__ais-highlight__",
              highlightPostTag: "__/ais-highlight__",
            },
          ],
        }),
      }),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    const payload = await json(response);
    const result = payload.results[0];
    expect(result).toMatchObject({
      indexUid: "base2026_public_tiktok",
      limit: 5,
      offset: 0,
      query: "AI search",
      estimatedTotalHits: 1,
      facetDistribution: expect.any(Object),
      facetStats: {},
      processingTimeMs: expect.any(Number),
    });
    expect(result.hits[0]._formatted).toMatchObject({
      body: expect.stringContaining("__ais-highlight__"),
      title: expect.any(String),
      handle: expect.any(String),
    });
    expect(result.hits[0].avatar_url).toBe("/static/assets/creators/build-in-public.jpeg");
  });

  it("searches the isolated Outreach collection with strict fields, highlights, facets, and bounded sort", async () => {
    const outreach = new FakeOutreachDatabase();
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          queries: [{
            indexUid: "base2026_public_outreach",
            q: "AI search",
            sort: ["score:desc"],
            facets: ["platform", "source_status", "topics", "lanes", "cost", "complexity", "effect_speed", "language"],
            facetFilters: [["topics:AI visibility", "platform:Web", "source_status:Одобрено с ограничениями"]],
            filter: ["score >= 70", "source_status = \"Одобрено с ограничениями\""],
            attributesToHighlight: ["title", "summary"],
            highlightPreTag: "<mark>",
            highlightPostTag: "</mark>",
          }],
        }),
      }),
      env(new FakeDatabase(), new FakeInboxDatabase(), outreach),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    const result = (await json(response)).results[0];
    expect(result).toMatchObject({
      indexUid: "base2026_public_outreach",
      query: "AI search",
      estimatedTotalHits: 1,
      facetStats: {},
      facetDistribution: expect.objectContaining({
        platform: expect.any(Object),
        source_status: expect.any(Object),
        topics: expect.any(Object),
        lanes: expect.any(Object),
        cost: expect.any(Object),
        complexity: expect.any(Object),
        effect_speed: expect.any(Object),
        language: expect.any(Object),
      }),
    });
    expect(result.hits[0]).toMatchObject({
      id: "outreach-finding:OUT-001",
      collection: "outreach_findings",
      topics: ["AI visibility"],
      lanes: ["content"],
      score: 80,
    });
    expect(result.hits[0]._formatted.title).toContain("<mark>AI</mark>");
  });

  it("preserves input ordering for a labelled two-index envelope", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          queries: [
            { indexUid: "base2026_public_outreach", q: "AI" },
            { indexUid: "base2026_public_tiktok", q: "AI" },
          ],
        }),
      }),
      env(new FakeDatabase(), new FakeInboxDatabase(), new FakeOutreachDatabase()),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect((await json(response)).results.map((result: Record<string, unknown>) => result.indexUid)).toEqual([
      "base2026_public_outreach",
      "base2026_public_tiktok",
    ]);
  });

  it("fails closed with a clear 503 when the optional Outreach binding is absent", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ queries: [{ indexUid: "base2026_public_outreach", q: "AI" }] }),
      }),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(503);
    expect(await json(response)).toMatchObject({ error: { code: "OUTREACH_DB_NOT_CONFIGURED" } });
  });

  it("rejects Outreach filters that are outside the server-owned field map", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          queries: [{ indexUid: "base2026_public_outreach", filter: "title = AI OR 1=1" }],
        }),
      }),
      env(new FakeDatabase(), new FakeInboxDatabase(), new FakeOutreachDatabase()),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(400);
    expect(await json(response)).toMatchObject({ error: { code: "UNSUPPORTED_FILTER" } });
  });

  it("rejects unknown indexes with a structured forbidden response", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ queries: [{ indexUid: "private-index", q: "secret" }] }),
      }),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(403);
    expect(await json(response)).toMatchObject({ error: { code: "UNKNOWN_INDEX" } });
  });

  it("accepts the mark tags configured by the generated search UI", async () => {
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          queries: [{
            indexUid: "base2026_public_tiktok",
            q: "AI",
            attributesToHighlight: ["body"],
            highlightPreTag: "<mark>",
            highlightPostTag: "</mark>",
          }],
        }),
      }),
      env(),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(200);
    expect((await json(response)).results[0].hits[0]._formatted.body).toContain("<mark>AI</mark>");
  });

  it("validates method and content type before touching the database", async () => {
    const db = new FakeDatabase();
    const getResponse = await worker.fetch(new Request("https://base2026.dev/api/search/multi-search"), env(db), {} as ExecutionContext);
    expect(getResponse.status).toBe(405);
    const contentTypeResponse = await worker.fetch(
      new Request("https://base2026.dev/api/search/multi-search", { method: "POST", body: "{}" }),
      env(db),
      {} as ExecutionContext,
    );
    expect(contentTypeResponse.status).toBe(415);
  });

  it("stores a valid support proposal in the private inbox", async () => {
    const inbox = new FakeInboxDatabase();
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/forms/support", {
        method: "POST",
        headers: { "content-type": "application/json", origin: "https://base2026.dev" },
        body: JSON.stringify({
          startedAt: Date.now() - 5_000,
          name: "Program lead",
          email: "lead@example.com",
          organization: "Example Cloud",
          role: "Startup programs",
          supportPath: "credits",
          publicUrl: "https://example.com/startups",
          offer: "Infrastructure credits",
          outcome: "Run the public search layer",
          constraints: "Open-source use only",
          attribution: "discuss",
          consent: "yes",
          companySite: "",
        }),
      }),
      env(new FakeDatabase(), inbox),
      {} as ExecutionContext,
    );
    expect(response.status).toBe(201);
    expect(await json(response)).toMatchObject({ ok: true, reference: expect.any(String) });
    expect(inbox.rows).toHaveLength(1);
    expect(inbox.rows[0]).toContain("lead@example.com");
  });

  it("rejects cross-origin and implausibly fast form submissions", async () => {
    const payload = {
      startedAt: Date.now(), name: "A", email: "a@example.com", organization: "Org",
      supportPath: "credits", offer: "Credits", outcome: "Search", consent: "yes",
    };
    const crossOrigin = await worker.fetch(
      new Request("https://base2026.dev/api/forms/support", {
        method: "POST", headers: { "content-type": "application/json", origin: "https://example.com" }, body: JSON.stringify(payload),
      }),
      env(), {} as ExecutionContext,
    );
    expect(crossOrigin.status).toBe(403);
    const fast = await worker.fetch(
      new Request("https://base2026.dev/api/forms/support", {
        method: "POST", headers: { "content-type": "application/json", origin: "https://base2026.dev" }, body: JSON.stringify(payload),
      }),
      env(), {} as ExecutionContext,
    );
    expect(fast.status).toBe(400);
  });

  it("accepts honeypot submissions without storing them", async () => {
    const inbox = new FakeInboxDatabase();
    const response = await worker.fetch(
      new Request("https://base2026.dev/api/forms/partner", {
        method: "POST",
        headers: { "content-type": "application/json", origin: "https://base2026.dev" },
        body: JSON.stringify({ companySite: "https://spam.example", startedAt: Date.now() - 4_000 }),
      }),
      env(new FakeDatabase(), inbox), {} as ExecutionContext,
    );
    expect(response.status).toBe(202);
    expect(inbox.rows).toHaveLength(0);
  });
});
