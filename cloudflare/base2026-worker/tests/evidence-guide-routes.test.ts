/** Synthetic public fixtures and real SQLite; no live corpus or browser QA. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { runInNewContext } from "node:vm";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  EDITORIAL_EVIDENCE_GUIDE_SLUGS, EDITORIAL_SCHEMA, getEditorialArticle, publishEditorialArticle, validateEditorialPayload,
  type EditorialPayload, type StoredEditorialArticle,
} from "../src/editorial";
import { blogSchema, editorialEscape, editorialJson, renderEditorialArticle } from "../src/editorial-render";
import { handleEvidenceGuideRoute } from "../src/evidence-guide-routes";
import { hashPublicEvidenceDocument, type PublicEvidenceDocument } from "../src/evidence-dependencies";
import { applyPublicProjection } from "../src/public-projection";
import worker from "../src/index";

const NOW = "2026-08-30T20:00:00.000Z";
const PUBLISHED = "2026-08-29T10:00:00.000Z";
const REVIEWED = "2026-08-30T19:00:00.000Z";
const ORIGIN = "https://base2026.dev";
const template = readFileSync(new URL("../../../templates/base2026-blog-index.html", import.meta.url), "utf8");
const databases = new Set<SqliteD1>();
const header = '<header class="b26-site-header" data-b26-shell><a href="/">Base2026</a></header>';
const footer = '<footer class="b26-site-footer" data-b26-shell><a href="/methodology">Methodology</a></footer>';
const guideScript = readFileSync(new URL("../../../templates/base2026-evidence-guide.js", import.meta.url), "utf8");
const guideStyle = readFileSync(new URL("../../../templates/base2026-evidence-guide.css", import.meta.url), "utf8");

function payload(overrides: Partial<EditorialPayload> = {}): EditorialPayload {
  return {
    schema_version: EDITORIAL_SCHEMA, kind: "source_based_article", slug: "fixture-context-check", revision: 1,
    title: 'Keep a source & its "context" together', description: "A public-only fixture for a bounded decision record.",
    lede: "This synthetic guide fixture is not a real research finding.", category: "Research methods", tags: ["Evidence"],
    published_at: PUBLISHED, updated_at: PUBLISHED, author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: "Synthetic test content prepared with AI assistance; not a factual recommendation.",
    sources: [
      { id: "reference", url: "https://developers.cloudflare.com/d1/?a=one&b=two", title: 'A source & "reference"', creator: "Cloudflare", checked_at: REVIEWED },
      { id: "methodology", url: "https://base2026.dev/methodology", title: "Base2026 methodology", creator: "Base2026", checked_at: REVIEWED },
    ],
    sections: [{ id: "context", heading: "Read the context", blocks: [
      { type: "paragraph", text: 'Keep the source & "quoted wording" next to the decision.', citation_ids: ["reference", "methodology"] },
      { type: "list", items: [{ text: "Record the limit of the observation.", citation_ids: [] }] },
    ] }],
    related_paths: ["/methodology", "/journal/source-diversity-check/"], ...overrides,
  };
}

function sqlValue(value: unknown): SQLInputValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "bigint" || value instanceof Uint8Array) return value;
  throw new Error("Unsupported synthetic SQLite parameter");
}

function result<T>(rows: T[], changes = 0): D1Result<T> {
  return { success: true, results: rows, meta: { duration: 0, size_after: 0, rows_read: rows.length, rows_written: changes, changes, last_row_id: 0, changed_db: changes > 0 } };
}

class Prepared implements D1PreparedStatement {
  constructor(private readonly db: SqliteD1, private readonly sql: string, private readonly values: SQLInputValue[] = []) {}
  bind(...values: unknown[]): D1PreparedStatement { return new Prepared(this.db, this.sql, values.map(sqlValue)); }
  execute<T>(): D1Result<T> {
    if (this.db.failedEvidenceResult && this.sql.includes("FROM search_documents d")) throw new Error("Synthetic evidence read failed");
    const statement = this.db.sqlite.prepare(this.sql);
    return statement.columns().length ? result(statement.all(...this.values) as T[]) : result<T>([], Number(statement.run(...this.values).changes));
  }
  first<T = unknown>(column: string): Promise<T | null>;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  async first<T>(column?: string): Promise<T | null> {
    const row = this.db.sqlite.prepare(this.sql).get(...this.values);
    return row ? (column ? row[column] : row) as T : null;
  }
  async all<T = Record<string, unknown>>(): Promise<D1Result<T>> { return this.execute<T>(); }
  async run<T = Record<string, unknown>>(): Promise<D1Result<T>> { return this.execute<T>(); }
  raw<T = unknown[]>(options: { columnNames: true }): Promise<[string[], ...T[]]>;
  raw<T = unknown[]>(options?: { columnNames?: false }): Promise<T[]>;
  async raw<T>(options?: { columnNames?: boolean }): Promise<T[] | [string[], ...T[]]> {
    const statement = this.db.sqlite.prepare(this.sql);
    const rows = statement.all(...this.values).map(Object.values) as T[];
    return options?.columnNames ? [statement.columns().map((column) => column.name), ...rows] : rows;
  }
}

class SqliteD1 implements D1Database {
  readonly sqlite = new DatabaseSync(":memory:");
  readonly calls: string[] = [];
  unavailable = false;
  failedEvidenceResult = false;
  constructor() {
    for (const file of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql", "0004_editorial_articles.sql"]) {
      this.sqlite.exec(readFileSync(new URL("../migrations/" + file, import.meta.url), "utf8"));
    }
    databases.add(this);
  }
  prepare(sql: string): D1PreparedStatement {
    this.calls.push(sql);
    if (this.unavailable) throw new Error("Synthetic database unavailable; do not expose this detail");
    return new Prepared(this, sql);
  }
  async batch<T = unknown>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]> {
    this.sqlite.exec("BEGIN");
    try {
      const rows = statements.map((statement) => {
        if (!(statement instanceof Prepared)) throw new Error("Unexpected test statement");
        return statement.execute<T>();
      });
      this.sqlite.exec("COMMIT"); return rows;
    } catch (error) { this.sqlite.exec("ROLLBACK"); throw error; }
  }
  async exec(sql: string): Promise<D1ExecResult> { this.sqlite.exec(sql); return { count: 1, duration: 0 }; }
  withSession(): D1DatabaseSession { throw new Error("Guide routes must not require D1 sessions"); }
  async dump(): Promise<ArrayBuffer> { throw new Error("Guide routes must not dump D1"); }
}

function shell(): string {
  let html = template;
  for (const [key, value] of Object.entries({ STARTUP_HEADER: header, STARTUP_FOOTER: footer,
    BLOG_FEATURED: "", BLOG_CARDS: "", BLOG_TOPIC_LINKS: '<a href="/topics/">Topics</a>', BLOG_SCHEMA: editorialJson(blogSchema([])),
  })) html = html.replace("{{" + key + "}}", value);
  return html.replace("</head>", [
    '<meta property="og:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">',
    '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
    '<meta property="og:image:alt" content="Base2026 public-source intelligence">',
    '<meta name="twitter:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">',
    '<meta name="twitter:image:alt" content="Base2026 public-source intelligence">', "</head>",
  ].join("\n"));
}

class Assets implements Fetcher {
  readonly requests: Request[] = [];
  html = shell();
  responder: (() => Response) | null = null;
  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    this.requests.push(new Request(input, init));
    return this.responder ? this.responder() : new Response(this.html, { headers: { "Content-Type": "text/html; charset=utf-8", ETag: "static-fixture", "Last-Modified": PUBLISHED } });
  }
  connect(): Socket { throw new Error("Guide routes must not open sockets"); }
}

async function seed(db: SqliteD1, item = payload()): Promise<StoredEditorialArticle> {
  const checked = await validateEditorialPayload(item, NOW);
  if (!checked.ok) throw new Error(JSON.stringify(checked.issues));
  const published = await publishEditorialArticle(db, { payload: checked.payload,
    review: { reviewer: "sol-max", outcome: "pass", reviewed_at: REVIEWED, payload_sha256: checked.payload_sha256 },
  }, { now: NOW });
  expect(published).toMatchObject({ ok: true, status: "published" });
  const article = await getEditorialArticle(db, item.slug, NOW);
  if (!article) throw new Error("Synthetic article missing after seed");
  db.calls.length = 0;
  return article;
}

const quote = 'Check the target & "link context" before recording a change.';
const otherQuote = "Check the destination before editing the link.";
const uncopiedContext = "Additional synthetic context must not be copied into the guide.";
const firstDocumentId = "chunk-transcript-polished-8000000000000000111-0000";

async function guidePayload(db: SqliteD1, slug = "internal-linking", projected = false): Promise<EditorialPayload> {
  const documents: PublicEvidenceDocument[] = [];
  for (const [video, handle, excerpt] of [
    ["8000000000000000111", "fixturealpha", quote], ["8000000000000000222", "fixturebeta", otherQuote],
  ]) {
    const document: PublicEvidenceDocument = { id: "chunk-transcript-polished-" + video + "-0000", source_id: "tiktok:" + handle + ":" + video,
      source_url: "https://www.tiktok.com/@" + handle + "/video/" + video, creator_handle: "@" + handle,
      title: "Synthetic public context example", body: excerpt + " " + uncopiedContext, full_transcript_public: 0, admission_state: "normal_public_card" };
    db.sqlite.prepare(`INSERT OR IGNORE INTO search_documents
      (id,item_id,source_id,chunk_id,chunk_index,body,title,creator_handle,source_url,video_id,platform,source_type,public_policy,public_surface,full_transcript_public,admission_state)
      VALUES (?,?,?,?,0,?,?,?,?,?,'tiktok','tiktok_video','search_passage','main_search',0,'normal_public_card')`)
      .run(document.id, document.source_id, document.source_id, document.id, document.body, document.title, document.creator_handle, document.source_url, video);
    documents.push(document);
  }
  if (projected) {
    await applyPublicProjection(db, { schema_version: "base2026.public-projection.v1", projection_id: "a".repeat(40),
      source: { source_id: "tiktok:fixturegamma:8000000000000000333", canonical_url: "https://www.tiktok.com/@fixturegamma/video/8000000000000000333",
        creator_handle: "@fixturegamma", published_at: "2026-08-28", title_or_description: "Synthetic source attribution for a route test.", duration_seconds: 20 },
      manifest_sha256: "b".repeat(64), content_sha256: "c".repeat(64), private_import_receipt_sha256: "d".repeat(64),
      cards: [{ ordinal: 0, claim_text: "A synthetic adjacent check keeps the source visible.", suggested_action: "Read the original context before recording a decision.",
        topic_label: "Source context", evidence_excerpt: "A synthetic adjacent check keeps the source visible during review.", evidence_start_seconds: 1, evidence_end_seconds: 5 }],
    });
    const document = await db.prepare("SELECT id,source_id,source_url,creator_handle,title,body,full_transcript_public,admission_state FROM search_documents WHERE projection_id=?")
      .bind("a".repeat(40)).first<PublicEvidenceDocument>();
    if (!document) throw new Error("Projected synthetic document missing");
    documents.push(document);
  }
  const sources = documents.map((document, index) => ({ id: "evidence-" + index, url: document.source_url,
    title: 'Synthetic source & "context" ' + index, creator: document.creator_handle, checked_at: REVIEWED }));
  return payload({ kind: "evidence_guide", slug, category: "Maintained guides", sources,
    sections: [{ id: "context", heading: "Read the context", blocks: [
      { type: "paragraph", text: "This synthetic example illustrates a decision record, not a measured finding.", citation_ids: sources.map((source) => source.id) },
    ] }],
    evidence: { user_task: "Choose whether a target needs a link change, and record the uncertainty.", dependencies: await Promise.all(documents.map(async (document, index) => ({
      citation_id: sources[index].id, document_id: document.id, source_id: document.source_id,
      document_sha256: await hashPublicEvidenceDocument(document), quote: index === 0 ? quote : index === 1 ? otherQuote : document.body,
      relation: index === 0 ? "direct" as const : "prerequisite" as const,
    }))) },
  });
}

function env(db = new SqliteD1(), assets = new Assets()) { return { DB: db, ASSETS: assets }; }

async function route(path: string, environment = env(), method = "GET", headers: HeadersInit = {}, now = NOW): Promise<Response> {
  const routed = await handleEvidenceGuideRoute(new Request(ORIGIN + path, { method, headers }), environment, now);
  if (!routed) throw new Error("Expected a guide response for " + path);
  return routed;
}

beforeEach(() => { vi.spyOn(console, "error").mockImplementation(() => {}); });

afterEach(() => {
  vi.restoreAllMocks(); vi.useRealTimers();
  for (const db of databases) db.sqlite.close();
  databases.clear();
});

describe("ordinary blog byte compatibility", () => {
  it.each([false, true])("preserves pre-guide rendering, updated illustration %s", async (illustrated) => {
    const item = payload(illustrated ? {
      kind: "engineering_note", updated_at: "2026-08-30T12:00:00.000Z",
      hero: { path: "/static/assets/base2026-ai-visibility-measurement.png", alt: "Synthetic illustration", credit: "AI-generated test illustration.", ai_generated: true },
      first_party_context: "This fixture is first-party test content, not a measured result.",
    } : {});
    const html = renderEditorialArticle(shell(), await seed(new SqliteD1(), item));
    const digest = createHash("sha256").update(html).digest("hex");
    // Captured from the renderer before any guide changes, not a live article.
    expect(digest).toBe(illustrated
      ? "84a53b94fcb73d16f2bb69eb7f0a4bbb879e455364372ce2566d85bed039563f"
      : "b18773436d98ec7f6b408dc8c6c711dedccbdb753e84d373e0b182a1263dae3b");
    expect(html).not.toContain("base2026-evidence-guide");
  });
});

describe("guide routes with real public SQLite fixtures", () => {
  it("uses the actual shared templates and the default Worker's public security wrapper", async () => {
    vi.useFakeTimers({ toFake: ["Date"] }); vi.setSystemTime(new Date(NOW));
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    const sharedHeader = readFileSync(new URL("../../../templates/base2026-startup-header.html", import.meta.url), "utf8");
    const sharedFooter = readFileSync(new URL("../../../templates/base2026-startup-footer.html", import.meta.url), "utf8");
    environment.ASSETS.html = shell().replace(header, sharedHeader).replace(footer, sharedFooter);
    const network = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No external fetch expected"));
    const fullEnv: Env = { ...environment,
      MEMBER_AUTH_ENABLED: "false",
      get INBOX_DB(): D1Database { throw new Error("Guide must not read Inbox"); },
      get OUTREACH_DB(): D1Database { throw new Error("Guide must not read Outreach"); },
    };
    const response = await worker.fetch(new Request(ORIGIN + "/topics/internal-linking"), fullEnv, {} as ExecutionContext);
    expect(response.status).toBe(200);
    const html = await response.text(); expect(html).toContain(sharedHeader); expect(html).toContain(sharedFooter);
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(response.headers.get("X-Frame-Options")).toBe("SAMEORIGIN");
    expect(response.headers.get("Referrer-Policy")).toBe("strict-origin-when-cross-origin");
    expect(response.headers.get("Permissions-Policy")).toContain("microphone=()");
    expect(network).not.toHaveBeenCalled();
  });

  it("renders one canonical TechArticle with escaped, attributed selected quotes and a no-JS record", async () => {
    const environment = env(); const item = await seed(environment.DB, await guidePayload(environment.DB));
    const response = await route("/topics/internal-linking", environment, "GET", { Cookie: "synthetic=value", Authorization: "synthetic", "If-None-Match": "static-fixture" });
    expect(response.status).toBe(200); expect(response.headers.get("Cache-Control")).toBe("no-store");
    const html = await response.text();
    expect(html).toContain(header); expect(html).toContain(footer);
    expect(html.match(/<h1\b/gu)).toHaveLength(1); expect(html.match(/<main\b/gu)).toHaveLength(1); expect(html.match(/rel="canonical"/gu)).toHaveLength(1);
    expect(html).toContain('<link rel="canonical" href="https://base2026.dev/topics/internal-linking">');
    expect(html).toContain('<meta property="og:url" content="https://base2026.dev/topics/internal-linking">');
    expect(html).toContain('<meta name="twitter:title" content="Keep a source &amp; its &quot;context&quot; together">');
    expect(html).toContain('<a href="/topics/">Topics</a>'); expect(html).toContain("In this guide"); expect(html).toContain("How this guide was prepared");
    expect(html).toContain("Check the target &amp; &quot;link context&quot; before recording a change.");
    expect(html).toContain("Direct support"); expect(html).toContain("Adjacent prerequisite"); expect(html).toContain("not proof votes");
    expect(html).toContain('<details><summary>Public document ID</summary><code>' + firstDocumentId);
    expect(html).not.toContain(item.payload.evidence!.dependencies[0].document_sha256); expect(html).not.toContain(item.payload.evidence!.dependencies[0].source_id);
    expect(html).not.toContain(uncopiedContext); expect(html).not.toContain("BlogPosting"); expect(html).not.toContain('rel="alternate" type="application/rss+xml"');
    expect(html).toContain("data-b26-guide-decision"); expect(html).toContain("URLs are not fetched or crawled"); expect(html).toContain("<noscript>");
    expect(html).not.toMatch(/<form\b|<input[^>]*value=/u);
    expect(html.match(/<label for="b26-guide-/gu)).toHaveLength(5); expect(html.match(/<button type="button"[^>]* hidden>/gu)).toHaveLength(2);
    expect(html).toContain('role="status" aria-live="polite" aria-atomic="true"');
    const ids = [...html.matchAll(/\bid="([^"]+)"/gu)].map((match) => match[1]);
    expect(new Set(ids).size).toBe(ids.length);
    for (const match of html.matchAll(/href="#([^"]+)"/gu)) expect(ids).toContain(match[1]);
    const schemas = [...html.matchAll(/<script type="application\/ld\+json" data-b26-blog-schema>([\s\S]*?)<\/script>/gu)];
    expect(schemas).toHaveLength(1);
    const schema = JSON.parse(schemas[0][1]);
    expect(schema["@graph"][0]).toMatchObject({ "@type": "TechArticle", url: ORIGIN + "/topics/internal-linking", dateModified: PUBLISHED, citation: item.payload.sources.map((source) => source.url) });
    expect(environment.ASSETS.requests).toHaveLength(1); expect(environment.ASSETS.requests[0].url).toBe(ORIGIN + "/blog");
    expect(environment.ASSETS.requests[0].method).toBe("GET");
    const forwardedHeaders: string[] = [];
    environment.ASSETS.requests[0].headers.forEach((_value, key) => forwardedHeaders.push(key));
    expect(forwardedHeaders).toEqual(["accept"]);
    expect(response.headers.has("ETag")).toBe(false); expect(response.headers.has("Last-Modified")).toBe(false);
    expect(environment.DB.calls.every((sql) => /^SELECT\s/u.test(sql.trim()))).toBe(true);
    expect(await (await route("/topics/internal-linking", environment, "GET", {}, "2026-08-31T20:00:00.000Z")).text()).toBe(html);
  });

  it.each(["GET", "HEAD"])("validates a healthy guide for %s and keeps HEAD bodyless", async (method) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    const response = await route("/topics/internal-linking", environment, method);
    expect(response.status).toBe(200); expect(response.headers.get("Content-Type")).toContain("text/html");
    expect(environment.ASSETS.requests).toHaveLength(1); expect(environment.DB.calls.length).toBeGreaterThan(1);
    const body = await response.text();
    if (method === "HEAD") expect(body).toBe(""); else expect(body).toContain("<h1>");
  });

  it.each(["/guides", "/guides/"])("redirects the intuitive guide hub alias %s to the canonical topics hub", async (path) => {
    const environment = env();
    for (const method of ["GET", "HEAD"]) {
      const response = await route(path + "?utm_source=fixture", environment, method);
      expect(response.status).toBe(308);
      expect(response.headers.get("Location")).toBe(ORIGIN + "/topics/?utm_source=fixture");
      expect(await response.text()).toBe("");
    }
    expect(environment.DB.calls).toHaveLength(0);
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(["/topics/internal-linking/", "/topics/internal-linking.html"])("redirects the healthy %s alias only after validation", async (path) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    for (const method of ["GET", "HEAD"]) {
      const response = await route(path + "?utm_source=fixture", environment, method);
      expect(response.status).toBe(308); expect(response.headers.get("Location")).toBe(ORIGIN + "/topics/internal-linking?utm_source=fixture");
      expect(await response.text()).toBe("");
    }
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(["", "?", "?utm_source=fixture", "?unknown=one&unknown=two", "?cursor=invalid", "?&", "?q=%3Cscript%3E"])("keeps the clean canonical for HTML query variant %s", async (query) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    const response = await route("/topics/internal-linking" + query, environment);
    const html = await response.text(); const queried = Boolean(new URL(ORIGIN + "/topics/internal-linking" + query).search);
    expect(response.status).toBe(200); expect(html).toContain('<link rel="canonical" href="' + ORIGIN + '/topics/internal-linking">');
    expect(response.headers.get("X-Robots-Tag")).toBe(queried ? "noindex, follow" : null);
    expect(html).toContain(queried ? '<meta name="robots" content="noindex,follow">' : '<meta name="robots" content="index,follow,max-image-preview:large">');
    expect(environment.ASSETS.requests[0].url).toBe(ORIGIN + "/blog");
    if (query.length > 1) expect(html).not.toContain(query);
  });

  it("separates registered topics, published guide summaries and public detail from ordinary articles", async () => {
    const environment = env(); const item = await seed(environment.DB, await guidePayload(environment.DB)); await seed(environment.DB);
    const index = await (await route("/api/guides", environment)).json<Record<string, unknown>>();
    expect(index.registered_topics).toEqual(EDITORIAL_EVIDENCE_GUIDE_SLUGS);
    expect(index.guides).toEqual([expect.objectContaining({ slug: "internal-linking", canonical_url: ORIGIN + "/topics/internal-linking", payload_sha256: item.payload_sha256 })]);
    expect(JSON.stringify(index)).not.toMatch(/document_sha256|receipt|sections|dependencies|fixture-context-check/u);
    const detail = await (await route("/api/guides/internal-linking", environment)).json();
    expect(detail).toEqual({ schema_version: "base2026.evidence-guide-public.v1", guide: item.payload, public_path: item.public_path, canonical_url: ORIGIN + item.public_path, payload_sha256: item.payload_sha256 });
    expect(JSON.stringify(detail)).not.toContain(uncopiedContext); expect(JSON.stringify(detail)).not.toMatch(/recorded_at|reviewed_at|receipt/u);
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it("retains every unpublished registered topic and its aliases without an asset call", async () => {
    const environment = env();
    for (const slug of EDITORIAL_EVIDENCE_GUIDE_SLUGS) {
      for (const suffix of ["", "/", ".html"]) expect(await handleEvidenceGuideRoute(new Request(ORIGIN + "/topics/" + slug + suffix), environment, NOW)).toBeNull();
      expect((await route("/api/guides/" + slug, environment)).status).toBe(404);
    }
    const index = await (await route("/api/guides", environment)).json<{ guides: unknown[]; registered_topics: string[] }>();
    expect(index.guides).toEqual([]); expect(index.registered_topics).toEqual(EDITORIAL_EVIDENCE_GUIDE_SLUGS);
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(EDITORIAL_EVIDENCE_GUIDE_SLUGS.filter((slug) => slug !== "internal-linking"))("does not give %s a link-specific decision form", async (slug) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB, slug));
    const response = await route("/topics/" + slug, environment); const html = await response.text();
    expect(response.status).toBe(200); expect(html).toContain("Evidence for this task"); expect(html).toContain("TechArticle");
    expect(html).not.toContain("data-b26-guide-decision"); expect(html).not.toContain("#guide-decision-record"); expect(html).not.toContain("Proposed source URL");
  });

  it("lists only healthy published canonicals in a non-nested guide sitemap with reviewed updated time", async () => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB)); await seed(environment.DB);
    const response = await route("/sitemap-guides.xml", environment); const xml = await response.text();
    expect(response.status).toBe(200); expect(response.headers.get("Content-Type")).toContain("application/xml");
    expect(xml).toContain('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">');
    expect(xml).toContain("<url><loc>https://base2026.dev/topics/internal-linking</loc><lastmod>" + PUBLISHED + "</lastmod></url>");
    expect(xml.match(/<url>/gu)).toHaveLength(1); expect(xml).not.toContain("sitemapindex"); expect(xml).not.toContain("/blog/");
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(["/api/guides", "/api/guides/internal-linking", "/sitemap-guides.xml"])("supports HEAD and rejects nonempty query state on %s", async (path) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    const response = await route(path, environment, "HEAD"); expect(response.status).toBe(200); expect(await response.text()).toBe("");
    environment.DB.calls.length = 0;
    for (const query of ["?utm_source=x", "?limit=10", "?cursor=x", "?&"]) expect((await route(path + query, environment)).status).toBe(400);
    expect(environment.DB.calls).toHaveLength(0); expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])("rejects %s on all owned routes before binding access", async (method) => {
    let reads = 0;
    const environment = { get DB(): D1Database { reads += 1; throw new Error("No DB access"); }, get ASSETS(): Fetcher { reads += 1; throw new Error("No ASSETS access"); } };
    for (const path of ["/guides", "/guides/", "/topics/internal-linking", "/topics/internal-linking.html", "/api/guides", "/api/guides/internal-linking", "/api/guides/invalid/path", "/sitemap-guides.xml"]) {
      const response = await handleEvidenceGuideRoute(new Request(ORIGIN + path, { method }), environment, NOW);
      expect(response?.status).toBe(405); expect(response?.headers.get("Allow")).toBe("GET, HEAD");
    }
    expect(reads).toBe(0);
  });

  it("does not intercept unrelated HTML, old journals, ordinary blogs or other APIs", async () => {
    const environment = env();
    for (const path of ["/", "/topics/", "/topics/not-registered", "/topics/internal-linking/extra", "/sources/", "/blog", "/blog/fixture-context-check/", "/journal/source-diversity-check/", "/api/blog", "/api/search", "/api/guides-extra", "/sitemap.xml"]) {
      expect(await handleEvidenceGuideRoute(new Request(ORIGIN + path), environment, NOW)).toBeNull();
    }
    for (const path of ["/api/guides/", "/api/guides/not-registered", "/api/guides/internal-linking/", "/api/guides/internal-linking/extra", "/api/guides/%69nternal-linking"]) expect((await route(path, environment)).status).toBe(404);
    expect(environment.DB.calls).toHaveLength(0); expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it.each(["body", "title", "source_url", "creator_handle", "full_transcript_public", "admission_state", "public_policy", "missing"])("fails closed on stale dependency %s for HTML, API and sitemap", async (field) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    if (field === "missing") environment.DB.sqlite.prepare("DELETE FROM search_documents WHERE id=?").run(firstDocumentId);
    else environment.DB.sqlite.prepare("UPDATE search_documents SET " + field + "=? WHERE id=?").run(field === "full_transcript_public" ? 1 : "Changed synthetic value", firstDocumentId);
    for (const path of ["/topics/internal-linking", "/topics/internal-linking/", "/api/guides", "/api/guides/internal-linking", "/sitemap-guides.xml"]) {
      const response = await route(path, environment); expect(response.status).toBe(503);
      expect(response.headers.get("Cache-Control")).toBe("no-store"); expect(response.headers.get("X-Robots-Tag")).toContain("noindex");
      expect(response.headers.get("Retry-After")).toBe("60"); expect(await response.text()).not.toContain("Changed synthetic value");
    }
    expect(environment.ASSETS.requests).toHaveLength(0);
  });

  it("accepts a receipt-backed excerpt, then stops serving when its projection is rolled back", async () => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB, "internal-linking", true));
    expect((await route("/topics/internal-linking", environment)).status).toBe(200);
    environment.DB.sqlite.exec("UPDATE public_projection_receipts SET status='rolled_back'");
    expect((await route("/topics/internal-linking", environment)).status).toBe(503);
    expect((await route("/sitemap-guides.xml", environment)).status).toBe(503);
  });

  it.each(["database", "result", "payload", "receipt", "wrong-kind"])("does not turn %s failure into a legacy fallback or empty 200", async (failure) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    if (failure === "database") environment.DB.unavailable = true;
    if (failure === "result") environment.DB.failedEvidenceResult = true;
    if (failure === "payload") environment.DB.sqlite.exec("UPDATE editorial_articles SET payload_json=json_set(payload_json,'$.title','Changed synthetic title')");
    if (failure === "receipt") environment.DB.sqlite.exec("DELETE FROM editorial_publication_receipts");
    if (failure === "wrong-kind") environment.DB.sqlite.exec("UPDATE editorial_articles SET payload_json=json_remove(json_set(payload_json,'$.kind','source_based_article'),'$.evidence')");
    for (const path of ["/topics/internal-linking", "/api/guides", "/api/guides/internal-linking", "/sitemap-guides.xml"]) {
      const response = await route(path, environment, "HEAD"); expect(response.status).toBe(503); expect(await response.text()).toBe("");
    }
    expect(environment.ASSETS.requests).toHaveLength(0);
  });
});

describe("guide shell and rendering boundary", () => {
  const mutations: Array<[string, (html: string) => string]> = [
    ["missing main", (html) => html.replace('id="b26-blog-main"', 'id="wrong-main"')],
    ["second main", (html) => html.replace("</body>", "<main></main></body>")],
    ["second H1", (html) => html.replace("</body>", "<h1>Wrong</h1></body>")],
    ["missing footer", (html) => html.replace(footer, "")],
    ["second shared header", (html) => html.replace(header, header + header)],
    ["wrong shared class", (html) => html.replace('class="b26-site-header"', 'class="fake-b26-site-header"')],
    ["wrong design authority", (html) => html.replace("b26-independent-v1", "unapproved-design")],
    ["unsupported closing head", (html) => html.replace("</head>", "</HEAD>")],
    ["misplaced footer", (html) => html.replace(footer, "").replace(header, header + footer)],
    ["wrong canonical", (html) => html.replace('rel="canonical" href="https://base2026.dev/blog"', 'rel="canonical" href="https://base2026.dev/"')],
    ["duplicate single-quoted canonical", (html) => html.replace("</head>", "<link rel='canonical' href='https://base2026.dev/blog'></head>")],
    ["duplicate unquoted canonical", (html) => html.replace("</head>", "<link rel=canonical href=https://base2026.dev/blog></head>")],
    ["duplicate robots", (html) => html.replace("</head>", "<meta name='ROBOTS' content='index'></head>")],
    ["unsupported robots replacement", (html) => html.replace('<meta name="robots" content="index,follow,max-image-preview:large">', "<meta name='robots' content='index,follow'>")],
    ["duplicate title metadata", (html) => html.replace("</head>", '<meta name="twitter:title" content="wrong"></head>')],
    ["duplicate single-quoted schema", (html) => html.replace("</head>", "<script type='application/ld+json'>{}</script></head>")],
    ["invalid JSON schema", (html) => html.replace(/(<script type="application\/ld\+json" data-b26-blog-schema>)[\s\S]*?<\/script>/u, "$1{broken</script>")],
    ["missing marker", (html) => html.replace("<!--B26_BLOG_FEATURED_END-->", "")],
    ["lone duplicate marker", (html) => html.replace("</main>", "<!--B26_BLOG_CARDS_START--></main>")],
    ["marker outside main", (html) => html.replace("<!--B26_BLOG_CARDS_END-->", "").replace("</body>", "<!--B26_BLOG_CARDS_END--></body>")],
    ["missing core styles", (html) => html.replace(/<link rel="stylesheet" href="\/static\/base2026-core\.css[^>]*>/u, "")],
    ["base URL override", (html) => html.replace("</head>", '<base href="https://example.com/"></head>')],
  ];

  it.each(mutations)("fails closed for %s", async (_name, mutate) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.html = mutate(environment.ASSETS.html);
    const response = await route("/topics/internal-linking?utm_source=fixture", environment);
    expect(response.status).toBe(503); expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(response.headers.get("X-Robots-Tag")).toContain("noindex");
    const html = await response.text(); expect(html).toContain("Guide temporarily unavailable"); expect(html).not.toContain(quote);
  });

  it.each([301, 404, 500])("does not accept an ASSETS %s as a usable shell", async (status) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.responder = () => new Response("synthetic asset error", { status, headers: { "Content-Type": "text/html", Location: "https://example.com/" } });
    expect((await route("/topics/internal-linking", environment)).status).toBe(503);
  });

  it.each(["application/json", "text/plain", "application/text/html"])("rejects non-HTML shell MIME %s", async (type) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.responder = () => new Response(environment.ASSETS.html, { headers: { "Content-Type": type } });
    expect((await route("/topics/internal-linking", environment)).status).toBe(503);
  });

  it.each(["262145", "invalid", "-1"])("rejects an invalid declared shell length %s", async (length) => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.responder = () => new Response(environment.ASSETS.html, { headers: { "Content-Type": "text/html", "Content-Length": length } });
    expect((await route("/topics/internal-linking", environment)).status).toBe(503);
  });

  it("caps streamed bytes even without Content-Length and cancels the reader", async () => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    const cancelled = vi.fn();
    environment.ASSETS.responder = () => new Response(new ReadableStream<Uint8Array>({
      pull(controller) { controller.enqueue(new Uint8Array(64 * 1024)); }, cancel: cancelled,
    }), { headers: { "Content-Type": "text/html" } });
    const response = await route("/topics/internal-linking", environment, "HEAD");
    expect(response.status).toBe(503); expect(await response.text()).toBe(""); expect(cancelled).toHaveBeenCalledOnce();
  });

  it("rejects invalid UTF-8 instead of silently altering the retained shell", async () => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.responder = () => new Response(new Uint8Array([0xc3, 0x28]), { headers: { "Content-Type": "text/html" } });
    expect((await route("/topics/internal-linking", environment)).status).toBe(503);
  });

  it("does not leak internal asset or dependency diagnostics", async () => {
    const environment = env(); await seed(environment.DB, await guidePayload(environment.DB));
    environment.ASSETS.responder = () => { throw new Error("Synthetic detailed internal diagnostic"); };
    const response = await route("/topics/internal-linking", environment);
    expect(response.status).toBe(503); expect(await response.text()).not.toContain("Synthetic detailed");
    expect(console.error).toHaveBeenCalledWith('{"event":"base2026_evidence_guide_unavailable"}');
    expect(JSON.stringify(vi.mocked(console.error).mock.calls)).not.toContain("Synthetic detailed");
  });

  it("escapes even deliberately unvalidated renderer inputs as text, never markup", async () => {
    const db = new SqliteD1(); const stored = await seed(db, await guidePayload(db));
    const unsafe = '</p><img src=x onerror="bad()">';
    // Bypass validation deliberately for this renderer unit assertion only.
    stored.payload.title = unsafe; stored.payload.description = unsafe; stored.payload.lede = unsafe;
    stored.payload.evidence!.user_task = unsafe; stored.payload.evidence!.dependencies[0].quote = unsafe;
    stored.payload.sources[0].url = 'https://example.com/?a=" onclick="bad()';
    const html = renderEditorialArticle(shell(), stored);
    expect(html).toContain(editorialEscape(unsafe)); expect(html).not.toContain(unsafe);
    expect(html).toContain('href="https://example.com/?a=&quot; onclick=&quot;bad()"');
    expect(html).not.toContain('<img src=x'); expect(html).not.toContain('content="</p>');
    expect(html).toContain('\\u003c/p\\u003e');
  });
});

/** Minimal event/DOM doubles execute the actual browser script. They do not
 * establish browser rendering, clipboard permissions or download behavior. */
class Element {
  value = "";
  textContent = "";
  hidden = true;
  disabled = false;
  focused = false;
  href = "";
  download = "";
  clicked = 0;
  removed = false;
  readonly attributes = new Map<string, string>();
  readonly events = new Map<string, Array<() => void>>();
  set innerHTML(_value: string) { throw new Error("User input must never reach innerHTML"); }
  setAttribute(name: string, value: string): void { this.attributes.set(name, value); }
  removeAttribute(name: string): void { this.attributes.delete(name); }
  addEventListener(name: string, handler: () => void): void { this.events.set(name, [...(this.events.get(name) ?? []), handler]); }
  fire(name: string): void { for (const handler of this.events.get(name) ?? []) handler(); }
  focus(): void { this.focused = true; }
  click(): void { this.clicked += 1; }
  remove(): void { this.removed = true; }
}

function client(options: { clipboard?: "ok" | "denied" | "missing"; missingNode?: string; downloadError?: boolean } = {}) {
  const keys = ["target", "source", "decision", "rationale", "verification"];
  const fields = Object.fromEntries(keys.map((key) => [key, new Element()]));
  const prints = Object.fromEntries(keys.map((key) => [key, new Element()]));
  const copy = new Element(); const download = new Element(); const status = new Element(); const print = new Element();
  const nodes: Record<string, Element> = { "[data-guide-copy]": copy, "[data-guide-download]": download, "[data-guide-status]": status, "[data-guide-print]": print };
  keys.forEach((key) => { nodes["#b26-guide-" + key] = fields[key]; nodes["[data-print-" + key + "]"] = prints[key]; });
  const root = { dataset: { guideUrl: ORIGIN + "/topics/internal-linking", guideRevision: "2", guideUpdated: PUBLISHED },
    querySelector: (selector: string) => selector === options.missingNode ? null : nodes[selector] ?? null };
  const writeText = vi.fn<(text: string) => Promise<void>>().mockResolvedValue();
  if (options.clipboard === "denied") writeText.mockRejectedValue(new Error("Synthetic denial"));
  const blobs: Blob[] = [];
  const anchors: Element[] = [];
  const timers: Array<() => void> = [];
  const revoke = vi.fn();
  const network = vi.fn(() => { throw new Error("No network is allowed"); });
  class LocalURL extends URL {
    static createObjectURL(blob: Blob): string {
      if (options.downloadError) throw new Error("Synthetic download error");
      blobs.push(blob); return "blob:synthetic-guide-record";
    }
    static revokeObjectURL(url: string): void { revoke(url); }
  }
  const context = {
    document: { querySelectorAll: () => [root], body: { appendChild: (node: Element) => anchors.push(node) }, createElement: () => new Element() },
    navigator: options.clipboard === "missing" ? {} : { clipboard: { writeText }, sendBeacon: network },
    URL: LocalURL, Blob, fetch: network, XMLHttpRequest: network,
    setTimeout: (callback: () => void) => { timers.push(callback); return timers.length; },
    get localStorage(): never { throw new Error("No local storage is allowed"); },
    get sessionStorage(): never { throw new Error("No session storage is allowed"); },
    get indexedDB(): never { throw new Error("No browser database is allowed"); },
  };
  runInNewContext(guideScript, context, { timeout: 1000 });
  return { fields, prints, copy, download, status, print, root, writeText, blobs, anchors, timers, revoke, network };
}

function fill(clientState: ReturnType<typeof client>): void {
  Object.assign(clientState.fields.target, { value: "https://example.com/target" });
  Object.assign(clientState.fields.source, { value: "https://example.com/source" });
  Object.assign(clientState.fields.decision, { value: "no-change" });
  Object.assign(clientState.fields.rationale, { value: "The reader already has the relevant link." });
  Object.assign(clientState.fields.verification, { value: "Context checked; live destination still needs checking." });
  clientState.fields.verification.fire("input");
}

async function settle(): Promise<void> { for (let i = 0; i < 5; i += 1) await Promise.resolve(); }

describe("tab-only decision record script", () => {
  it("enhances only complete markup without copying, downloading, requests or storage on load", () => {
    const ui = client();
    expect(ui.copy.hidden).toBe(false); expect(ui.download.hidden).toBe(false); expect(ui.print.hidden).toBe(false);
    expect(ui.prints.target.textContent).toBe("Not entered"); expect(ui.prints.decision.textContent).toBe("Not selected");
    expect(ui.writeText).not.toHaveBeenCalled(); expect(ui.blobs).toEqual([]); expect(ui.network).not.toHaveBeenCalled();
  });

  it("leaves the no-JS fallback intact if a required node is missing", () => {
    const ui = client({ missingNode: "#b26-guide-target" });
    expect(ui.copy.hidden).toBe(true); expect(ui.download.hidden).toBe(true); expect(ui.copy.events.size).toBe(0);
  });

  it("copies an explicit assessment with the guide revision, not a pretend automatic audit", async () => {
    const ui = client(); fill(ui); ui.copy.fire("click"); await settle();
    expect(ui.writeText).toHaveBeenCalledOnce();
    expect(ui.writeText.mock.calls[0][0]).toContain("Guide: https://base2026.dev/topics/internal-linking\nGuide revision: 2\nGuide updated: " + PUBLISHED);
    expect(ui.writeText.mock.calls[0][0]).toContain("Decision: Make no change");
    expect(ui.status.textContent).toContain("Record copied"); expect(ui.copy.disabled).toBe(false);
    expect(ui.network).not.toHaveBeenCalled(); expect(ui.blobs).toHaveLength(0);
  });

  it.each(["add", "context", "repair", "no-change"])("retains the explicit %s decision", async (decision) => {
    const ui = client(); fill(ui); ui.fields.decision.value = decision; ui.fields.decision.fire("change"); ui.copy.fire("click"); await settle();
    expect(ui.writeText).toHaveBeenCalledOnce(); expect(ui.prints.decision.textContent).not.toBe("Not selected");
    expect(ui.writeText.mock.calls[0][0]).toContain("Decision: " + ui.prints.decision.textContent);
  });

  it.each(["denied", "missing"] as const)("reports clipboard %s without a false success", async (clipboard) => {
    const ui = client({ clipboard }); fill(ui); ui.copy.fire("click"); await settle();
    expect(ui.status.textContent).toMatch(/unavailable or denied/u); expect(ui.status.textContent).toContain("Download CSV");
    expect(ui.copy.disabled).toBe(false); expect(ui.network).not.toHaveBeenCalled();
  });

  it.each(["", "javascript:alert(1)", "data:text/html,hello", "file:///local", "https://person:pass@example.com/", "https://example.com/" + "x".repeat(2048)])("rejects a non-public-form URL before any copy gesture action", async (url) => {
    const ui = client(); fill(ui); ui.fields.target.value = url; ui.copy.fire("click"); await settle();
    expect(ui.writeText).not.toHaveBeenCalled(); expect(ui.fields.target.focused).toBe(true);
    expect(ui.fields.target.attributes.get("aria-invalid")).toBe("true"); expect(ui.status.textContent).toContain("will not be visited");
  });

  it.each(["source", "decision", "rationale", "verification"])("requires an explicit %s before export", (field) => {
    const ui = client(); fill(ui); ui.fields[field].value = ""; ui.download.fire("click");
    expect(ui.blobs).toHaveLength(0); expect(ui.fields[field].focused).toBe(true); expect(ui.status.textContent).not.toBe("");
    ui.fields[field].fire("input"); expect(ui.fields[field].attributes.has("aria-invalid")).toBe(false); expect(ui.status.textContent).toBe("");
  });

  it("uses textContent for printable input and preserves long, multiline notes", () => {
    const ui = client(); fill(ui);
    ui.fields.rationale.value = '<img src=x onerror="bad()">\n' + "A".repeat(1400);
    ui.fields.rationale.fire("input");
    expect(ui.prints.rationale.textContent).toBe(ui.fields.rationale.value);
    expect(ui.network).not.toHaveBeenCalled(); expect(ui.anchors).toEqual([]);
  });

  it("creates one local CSV only after a download click and revokes its object URL", async () => {
    const ui = client(); fill(ui); expect(ui.blobs).toHaveLength(0);
    ui.fields.rationale.value = 'Reader context, with "quotes"\nand a second line.';
    ui.download.fire("click");
    expect(ui.blobs).toHaveLength(1); expect(ui.anchors).toHaveLength(1);
    expect(ui.anchors[0]).toMatchObject({ href: "blob:synthetic-guide-record", download: "base2026-decision-record.csv", clicked: 1, removed: true });
    const csv = await ui.blobs[0].text();
    expect(csv).toContain('"guide_url","guide_revision","guide_updated_at","target_url","proposed_source_url","decision","rationale","verification"\r\n');
    expect(csv).toContain('"Reader context, with ""quotes""\nand a second line."');
    expect(ui.status.textContent).toContain("download requested");
    expect(ui.revoke).not.toHaveBeenCalled(); ui.timers.forEach((timer) => timer());
    expect(ui.revoke).toHaveBeenCalledWith("blob:synthetic-guide-record"); expect(ui.network).not.toHaveBeenCalled();
  });

  it.each(["=SUM(A1,1)", "+SUM(A1,1)", "-SUM(A1,1)", "@SUM(A1,1)", " \t=SUM(A1,1)", "\u0001=SUM(A1,1)"])("protects CSV formula prefix %j", async (value) => {
    const ui = client(); fill(ui); ui.fields.rationale.value = value; ui.download.fire("click");
    expect(await ui.blobs[0].text()).toContain('"\'' + value.trim() + '"');
  });

  it("reports a download creation error without pretending a file was saved", () => {
    const ui = client({ downloadError: true }); fill(ui); ui.download.fire("click");
    expect(ui.status.textContent).toContain("could not be created"); expect(ui.anchors).toHaveLength(0); expect(ui.network).not.toHaveBeenCalled();
  });

  it("keeps new CSS scoped, wrapping, keyboard and print-safe without animation dependencies", () => {
    const css = guideStyle.replace(/\/\*[\s\S]*?\*\//gu, "");
    const selectors = [...css.matchAll(/(?:^|[{}])\s*([^{}]+)\{/gu)].map((match) => match[1].trim()).filter((selector) => !selector.startsWith("@"));
    expect(selectors.length).toBeGreaterThan(20);
    for (const selector of selectors) expect(selector).toMatch(/^\.b26-evidence-guide\b/u);
    expect(css).toContain("minmax(0, 1fr)"); expect(css).toContain("overflow-wrap: anywhere"); expect(css).toContain("min-width: 0");
    expect(css).toContain("@media (max-width: 600px)"); expect(css).toContain("@media print"); expect(css).toContain("white-space: pre-wrap");
    expect(css).toContain("prefers-reduced-motion"); expect(css).toContain(":focus-visible");
    expect(css).not.toMatch(/@import|@font-face|@keyframes|position:\s*fixed/iu);
    expect(guideScript).not.toMatch(/\.innerHTML\s*=|\bfetch\s*\(|localStorage|sessionStorage|indexedDB|sendBeacon|requestSubmit|\.submit\s*\(/u);
  });
});
