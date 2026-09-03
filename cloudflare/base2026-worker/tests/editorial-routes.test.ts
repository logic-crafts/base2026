/** Local route/renderer integration with real SQLite and public-only fixtures.
 * WorkerEntrypoint uses the package's existing test alias, not live RPC.
 * Python's standard XML parser is used only to validate generated RSS/sitemaps.
 */
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { PublicProjectionEntrypoint } from "../src/index";
import { handleEditorialRoute } from "../src/editorial-routes";
import {
  LEGACY_EDITORIAL_CATALOG, blogSchema, editorialJson, renderEditorialArticle,
  renderEditorialCard, type EditorialSummary,
} from "../src/editorial-render";
import {
  EDITORIAL_SCHEMA, getEditorialArticle, publishEditorialArticle, validateEditorialPayload,
  type EditorialListCursor, type EditorialPacket, type EditorialPayload,
} from "../src/editorial";

const NOW = "2026-08-30T20:00:00.000Z";
const PUBLISHED = "2026-08-30T12:00:00.000Z";
const REVIEWED = "2026-08-30T19:30:00.000Z";
const ORIGIN = "https://base2026.dev";
const MAX_SHELL_BYTES = 256 * 1024;
const legacyPaths = LEGACY_EDITORIAL_CATALOG.map((item) => item.path);
const migration = readFileSync(new URL("../migrations/0004_editorial_articles.sql", import.meta.url), "utf8");
const template = readFileSync(new URL("../../../templates/base2026-blog-index.html", import.meta.url), "utf8");
const header = readFileSync(new URL("../../../templates/base2026-startup-header.html", import.meta.url), "utf8");
const footer = readFileSync(new URL("../../../templates/base2026-startup-footer.html", import.meta.url), "utf8");
const databases = new Set<SqliteD1>();

function payload(overrides: Partial<EditorialPayload> = {}): EditorialPayload {
  return {
    schema_version: EDITORIAL_SCHEMA, kind: "source_based_article", slug: "fixture-source-check", revision: 1,
    title: 'A source check & a reader’s "second look"',
    description: 'A public fixture keeps attribution & "quoted wording" separate from review state.',
    lede: "A test-only research note shows the source link beside the observation.",
    category: "Research notes", tags: ["Evidence", "Public fixtures"],
    published_at: PUBLISHED, updated_at: PUBLISHED, author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: "Test fixture prepared with AI assistance; not a real research finding.",
    sources: [
      { id: "database", url: "https://developers.cloudflare.com/d1/worker-api/d1-database/?tab=one&format=summary", title: 'Database methods & "reference"', creator: "Cloudflare", checked_at: REVIEWED },
      { id: "transactions", url: "https://www.sqlite.org/lang_transaction.html", title: "Transaction reference", creator: "SQLite", published_at: "2026-08-28T10:00:00.000Z", checked_at: REVIEWED },
    ],
    sections: [
      { id: "read-the-source", heading: "Read the source & its context", blocks: [
        { type: "paragraph", text: 'The fixture pairs its wording & "quotes" with attributable references.', citation_ids: ["database", "transactions"] },
        { type: "list", items: [
          { text: "Keep an original link beside the observation.", citation_ids: ["database"] },
          { text: "Do not infer agreement from a search match.", citation_ids: [] },
        ] },
      ] },
      { id: "record-the-limit", heading: "Record the limit", blocks: [
        { type: "paragraph", text: "The fixture is not a benchmark or an endorsement.", citation_ids: ["transactions"] },
      ] },
    ],
    related_paths: ["/methodology", "/dataset", "/journal/source-diversity-check/"],
    ...overrides,
  };
}

async function reviewedPacket(article = payload()): Promise<EditorialPacket> {
  const checked = await validateEditorialPayload(article, NOW);
  if (!checked.ok) throw new Error(`Invalid public fixture: ${JSON.stringify(checked.issues)}`);
  return { payload: checked.payload, review: { reviewer: "sol-max", outcome: "pass", reviewed_at: REVIEWED, payload_sha256: checked.payload_sha256 } };
}

function sqlValue(value: unknown): SQLInputValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "bigint" || value instanceof Uint8Array) return value;
  throw new Error("Unsupported SQLite fixture parameter");
}

function d1Result<T>(results: T[], changes = 0): D1Result<T> {
  return { success: true, results, meta: { changes, duration: 0, size_after: 0, rows_read: results.length, rows_written: changes, last_row_id: 0, changed_db: changes > 0 } };
}

class Prepared implements D1PreparedStatement {
  constructor(private readonly db: SqliteD1, private readonly sql: string, private readonly parameters: SQLInputValue[] = []) {}
  bind(...values: unknown[]): D1PreparedStatement { return new Prepared(this.db, this.sql, values.map(sqlValue)); }
  execute<T>(): D1Result<T> {
    const statement = this.db.sqlite.prepare(this.sql);
    if (statement.columns().length) return d1Result(statement.all(...this.parameters) as T[]);
    return d1Result<T>([], Number(statement.run(...this.parameters).changes));
  }
  first<T = unknown>(column: string): Promise<T | null>;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  async first<T>(column?: string): Promise<T | null> {
    const row = this.db.sqlite.prepare(this.sql).get(...this.parameters);
    return row ? (column ? row[column] : row) as T : null;
  }
  async all<T = Record<string, unknown>>(): Promise<D1Result<T>> { return this.execute<T>(); }
  async run<T = Record<string, unknown>>(): Promise<D1Result<T>> { return this.execute<T>(); }
  raw<T = unknown[]>(options: { columnNames: true }): Promise<[string[], ...T[]]>;
  raw<T = unknown[]>(options?: { columnNames?: false }): Promise<T[]>;
  async raw<T>(options?: { columnNames?: boolean }): Promise<T[] | [string[], ...T[]]> {
    const statement = this.db.sqlite.prepare(this.sql);
    const rows = statement.all(...this.parameters).map(Object.values) as T[];
    return options?.columnNames ? [statement.columns().map((column) => column.name), ...rows] : rows;
  }
}

/** Executes production SQL; unused D1 capabilities fail loudly, not magically. */
class SqliteD1 implements D1Database {
  readonly sqlite = new DatabaseSync(":memory:");
  readonly prepared: string[] = [];
  batchCalls = 0;
  unavailable = false;
  constructor() { this.sqlite.exec(migration); databases.add(this); }
  prepare(sql: string): D1PreparedStatement {
    this.prepared.push(sql);
    if (this.unavailable) throw new Error("Synthetic D1 outage");
    return new Prepared(this, sql);
  }
  async batch<T = unknown>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]> {
    this.batchCalls += 1;
    this.sqlite.exec("BEGIN");
    try {
      const results = statements.map((statement) => {
        if (!(statement instanceof Prepared)) throw new Error("Unexpected SQLite fixture statement");
        return statement.execute<T>();
      });
      this.sqlite.exec("COMMIT");
      return results;
    } catch (error) { this.sqlite.exec("ROLLBACK"); throw error; }
  }
  async exec(sql: string): Promise<D1ExecResult> { this.sqlite.exec(sql); return { count: 1, duration: 0 }; }
  withSession(): D1DatabaseSession { throw new Error("D1 sessions are not exercised by this route fixture"); }
  async dump(): Promise<ArrayBuffer> { throw new Error("D1 dump is not exercised by this route fixture"); }
  resetCalls(): void { this.prepared.length = 0; this.batchCalls = 0; }
}

function staticShell(): string {
  const substitutions: Record<string, string> = {
    STARTUP_HEADER: header, STARTUP_FOOTER: footer,
    BLOG_FEATURED: renderEditorialCard(LEGACY_EDITORIAL_CATALOG[0], true),
    BLOG_CARDS: LEGACY_EDITORIAL_CATALOG.slice(1).map((item) => renderEditorialCard(item)).join(""),
    BLOG_TOPIC_LINKS: '<a href="/topics/">Browse source topics</a>',
    BLOG_SCHEMA: editorialJson(blogSchema(LEGACY_EDITORIAL_CATALOG)),
  };
  let html = template;
  for (const [name, value] of Object.entries(substitutions)) html = html.replace("{{" + name + "}}", value);
  // Match the builder's _ensure_social_image_meta contract; article rendering
  // must replace these exact selectors, not assume test-only metadata shapes.
  return html.replace("</head>", [
    '<meta property="og:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">',
    '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
    '<meta property="og:image:alt" content="Base2026 public-source intelligence">',
    '<meta name="twitter:image" content="https://base2026.dev/static/assets/base2026-ai-visibility-card.png">',
    '<meta name="twitter:image:alt" content="Base2026 public-source intelligence">', '</head>',
  ].join("\n"));
}

class Assets implements Fetcher {
  readonly requests: Request[] = [];
  shell = staticShell();
  responder: ((request: Request) => Response | Promise<Response>) | null = null;
  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const request = new Request(input, init);
    this.requests.push(request);
    if (this.responder) return this.responder(request);
    const path = new URL(request.url).pathname;
    if (path === "/blog") return new Response(request.method === "HEAD" ? null : this.shell, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    return new Response(request.method === "HEAD" ? null : "Static fixture not found", { status: 404, headers: { "Content-Type": "text/plain" } });
  }
  connect(): Socket { throw new Error("An editorial asset request must not open a socket"); }
}

function environment(db = new SqliteD1(), assets = new Assets()): Env {
  return { DB: db, ASSETS: assets, MEMBER_AUTH_ENABLED: "false",
    get INBOX_DB(): D1Database { throw new Error("Editorial routes must not inspect Inbox"); },
    get OUTREACH_DB(): D1Database { throw new Error("Editorial routes must not inspect Outreach"); },
    get AUTH_DB(): D1Database { throw new Error("Editorial routes must not inspect member auth"); },
    get MCP_RATE_LIMIT(): RateLimit { throw new Error("Editorial routes must not inspect MCP rate limits"); },
  };
}

async function seed(db: SqliteD1, article = payload()): Promise<void> {
  const result = await publishEditorialArticle(db, await reviewedPacket(article), { now: NOW });
  expect(result).toMatchObject({ ok: true, status: "published" });
}

async function route(path: string, env: Env, method = "GET", headers: HeadersInit = {}): Promise<Response> {
  const result = await handleEditorialRoute(new Request(ORIGIN + path, { method, headers }), env, NOW);
  if (!result) throw new Error(`Expected editorial route for ${path}`);
  return result;
}

// The default fetch wrapper never uses context. The real binding transport is
// outside this Node integration test, as documented in vitest.config.ts.
const context = {} as ExecutionContext;

interface PublicIndex { schema_version: string; articles: EditorialSummary[]; next_cursor: EditorialListCursor | null; next_url: string | null; note: string }
interface XmlNode { tag: string; attrs: Record<string, string>; text: string; children: XmlNode[] }

function xml(source: string): XmlNode {
  const script = "import json,sys,xml.etree.ElementTree as E\ndef node(e):\n return {'tag':e.tag,'attrs':e.attrib,'text':e.text or '', 'children':[node(c) for c in e]}\nprint(json.dumps(node(E.fromstring(sys.stdin.read()))))";
  return JSON.parse(execFileSync("python3", ["-c", script], { input: source, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 })) as XmlNode;
}

function xmlNodes(root: XmlNode, name: string): XmlNode[] {
  return [root, ...root.children.flatMap((child) => xmlNodes(child, "*"))]
    .filter((node) => name === "*" || node.tag.split("}").at(-1) === name);
}

function blogCards(html: string): string[] {
  return [...html.matchAll(/<a class="b26-blog-card__link" href="([^"]+)"/gu)].map((match) => match[1]);
}

function headerFields(headers: Headers): Record<string, string> {
  const fields: Record<string, string> = {};
  headers.forEach((value, name) => { fields[name] = value; });
  return fields;
}

function schemaFrom(html: string): { "@graph": Array<Record<string, unknown>> } {
  const matches = [...html.matchAll(/<script type="application\/ld\+json" data-b26-blog-schema>([\s\S]*?)<\/script>/gu)];
  expect(matches).toHaveLength(1);
  return JSON.parse(matches[0][1]) as { "@graph": Array<Record<string, unknown>> };
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(NOW));
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks(); vi.useRealTimers();
  for (const db of databases) db.sqlite.close();
  databases.clear();
});

describe("editorial HTML and public DTO integration", () => {
  it("merges the two unchanged legacy journal paths with a receipted new article", async () => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    await seed(db); db.resetCalls();
    const response = await route("/blog", env, "GET", { Cookie: "fixture=value", Authorization: "fixture-authorization" });
    expect(response.status).toBe(200);
    const html = await response.text();
    expect(blogCards(html)).toEqual(["/blog/fixture-source-check/", ...legacyPaths]);
    expect(html.match(/<h1(?:\s|>)/gu)).toHaveLength(1);
    expect(html.match(/<link rel="canonical"/gu)).toHaveLength(1);
    expect(html).toContain('<link rel="canonical" href="https://base2026.dev/blog">');
    expect(html.match(/class="b26-site-header"/gu)).toHaveLength(1);
    expect(html.match(/class="b26-site-footer"/gu)).toHaveLength(1);
    expect(html).not.toContain("{{");
    expect(schemaFrom(html)["@graph"].map((node) => node["@type"])).toEqual(["CollectionPage", "Blog"]);
    expect(db.batchCalls).toBe(0);
    expect(db.prepared.every((sql) => sql.trimStart().startsWith("SELECT"))).toBe(true);
    expect(assets.requests).toHaveLength(1);
    expect(assets.requests[0].url).toBe(ORIGIN + "/blog");
    expect(headerFields(assets.requests[0].headers)).toEqual({ accept: "text/html" });
  });

  it("renders one canonical article, original-source citations, and escaped readable text", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    const response = await route("/blog/fixture-source-check/", env);
    expect(response.status).toBe(200);
    const html = await response.text();
    expect(html.match(/<h1(?:\s|>)/gu)).toHaveLength(1);
    expect(html.match(/<main(?:\s|>)/gu)).toHaveLength(1);
    expect(html.match(/<link rel="canonical"/gu)).toHaveLength(1);
    expect(html).toContain('<main id="b26-blog-main" class="b26-blog-article">');
    expect(html).toContain('href="https://base2026.dev/blog/fixture-source-check/"');
    expect(html).toContain("A source check &amp; a reader’s &quot;second look&quot;");
    expect(html).toContain('href="https://developers.cloudflare.com/d1/worker-api/d1-database/?tab=one&amp;format=summary"');
    expect(html).toContain('class="b26-article-disclosure"');
    expect(html).toContain('/static/base2026-blog-article.css');
    expect(html.match(/<script(?:\s|>)/gu)).toHaveLength(1);
    const ids = [...html.matchAll(/\bid="([^"]+)"/gu)].map((match) => match[1]);
    expect(new Set(ids).size).toBe(ids.length);
    for (const match of html.matchAll(/href="#([^"]+)"/gu)) expect(ids).toContain(match[1]);
    const graph = schemaFrom(html)["@graph"];
    const article = graph.find((node) => node["@type"] === "BlogPosting")!;
    expect(article.url).toBe(ORIGIN + "/blog/fixture-source-check/");
    expect(article.citation).toEqual(payload().sources.map((source) => source.url));
    expect(article.headline).toBe(payload().title);
    expect(article.isAccessibleForFree).toBe(true);
    expect(article.image).toBe(ORIGIN + "/static/assets/base2026-ai-visibility-card.png");
  });

  it("keeps browser titles within the search-result contract without changing the article headline", async () => {
    const longTitle = "A deliberately long public research title that should remain intact in the article heading and structured data";
    const db = new SqliteD1(); const env = environment(db); await seed(db, payload({ title: longTitle }));
    const html = await (await route("/blog/fixture-source-check/", env)).text();
    const browserTitle = html.match(/<title>([^<]+)<\/title>/u)?.[1] ?? "";
    expect(browserTitle.length).toBeLessThanOrEqual(65);
    expect(schemaFrom(html)["@graph"][0].headline).toBe(longTitle);
    expect(html).toContain(longTitle);
  });

  it("retains the approved evidence-search bridge on a rendered article", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    const html = await (await route("/blog/fixture-source-check/", env)).text();
    expect(html.includes('class="b26-blog-bridge"'), "Article must retain the shared evidence-search bridge").toBe(true);
    expect(html).toContain("Try evidence search");
    expect(html).toContain('href="/workspace/"');
  });

  it("does not duplicate heading IDs when a new blog slug matches a journal slug", async () => {
    const db = new SqliteD1(); const env = environment(db);
    await seed(db, payload({ slug: "source-backed-video-search-cloudflare", published_at: "2026-08-28T10:00:00.000Z", updated_at: "2026-08-28T10:00:00.000Z" }));
    const html = await (await route("/blog", env)).text();
    expect(blogCards(html)).toHaveLength(3);
    const ids = [...html.matchAll(/\bid="([^"]+)"/gu)].map((match) => match[1]);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("escapes script-breaking renderer inputs as a second defensive layer", async () => {
    const db = new SqliteD1(); await seed(db);
    const stored = await getEditorialArticle(db, payload().slug, NOW);
    expect(stored).not.toBeNull(); if (!stored) return;
    const adversarial = structuredClone(stored);
    adversarial.payload.title = '</script><img src=x onerror="fixture"> & quotes';
    const html = renderEditorialArticle(staticShell(), adversarial);
    expect(html).not.toContain('<img src=x');
    expect(html.match(/<script(?:\s|>)/gu)).toHaveLength(1);
    expect(schemaFrom(html)["@graph"][0].headline).toBe(adversarial.payload.title);
    expect(html).toContain("&lt;/script&gt;&lt;img");
  });

  it("serves GET and HEAD with matching metadata, and 308s only the missing article slash", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    for (const path of ["/blog", "/api/blog", "/api/blog/fixture-source-check", "/blog/fixture-source-check/", "/blog/feed.xml", "/sitemap-blog.xml", "/sitemaps/blog-1.xml"]) {
      const get = await route(path, env); const head = await route(path, env, "HEAD");
      expect(head.status, path).toBe(get.status);
      expect(headerFields(head.headers), path).toEqual(headerFields(get.headers));
      expect(await head.text(), path).toBe("");
    }
    for (const method of ["GET", "HEAD"]) {
      const response = await route("/blog/fixture-source-check?from=fixture", env, method);
      expect(response.status).toBe(308);
      expect(response.headers.get("location")).toBe(ORIGIN + "/blog/fixture-source-check/?from=fixture");
      expect(await response.text()).toBe("");
    }
    for (const path of ["/blog/", "/blog.html", "/blog/index.html"]) {
      const response = await route(path, env);
      expect(response.status).toBe(308); expect(response.headers.get("location")).toBe(ORIGIN + "/blog");
    }
  });

  it("exposes only the deliberate public DTO and never publication/SQL state", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db); db.resetCalls();
    const response = await route("/api/blog/fixture-source-check", env);
    const data = await response.json<Record<string, unknown>>();
    expect(response.status).toBe(200);
    expect(Object.keys(data).sort()).toEqual(["article", "payload_sha256", "public_path", "schema_version"]);
    expect(data.article).toEqual(payload());
    expect(data.public_path).toBe("/blog/fixture-source-check/");
    expect(data.payload_sha256).toMatch(/^[a-f0-9]{64}$/u);
    const index = await (await route("/api/blog", env)).json<PublicIndex>();
    expect(index.schema_version).toBe("base2026.editorial-index.v1");
    expect(index.articles).toHaveLength(3);
    const keys = JSON.stringify([data, index]);
    for (const field of ['"review":', '"receipt":', '"payload_json":', '"stored_at":', '"reviewer":', '"diagnostics":']) expect(keys).not.toContain(field);
    expect(db.batchCalls).toBe(0);
    expect(db.prepared.every((sql) => sql.trimStart().startsWith("SELECT"))).toBe(true);
  });
});

describe("editorial pagination, RSS and sitemap discovery", () => {
  it("returns exact first/continuation cardinality without repeating either legacy article", async () => {
    const db = new SqliteD1(); const env = environment(db);
    for (let i = 0; i < 26; i += 1) await seed(db, payload({ slug: `fixture-page-${String(i).padStart(2, "0")}`, published_at: "2026-08-28T10:00:00.000Z", updated_at: "2026-08-28T10:00:00.000Z" }));
    const first = await (await route("/api/blog", env)).json<PublicIndex>();
    expect(first.articles).toHaveLength(27); // 25 D1 articles + two fallback journal entries.
    expect(first.next_cursor).toEqual({ published_at: "2026-08-28T10:00:00.000Z", slug: "fixture-page-24" });
    expect(first.next_url).toBe("/blog?cursor=" + encodeURIComponent("2026-08-28T10:00:00.000Z|fixture-page-24"));
    const continuation = first.next_url!.replace("/blog?", "/api/blog?");
    const last = await (await route(continuation, env)).json<PublicIndex>();
    expect(last.articles.map((article) => article.path)).toEqual(["/blog/fixture-page-25/"]);
    expect(last.next_cursor).toBeNull(); expect(last.next_url).toBeNull();
    const all = [...first.articles, ...last.articles].map((article) => article.path);
    expect(new Set(all).size).toBe(28);
    for (const path of legacyPaths) expect(all.filter((value) => value === path)).toHaveLength(1);
    const cursorPage = await route(first.next_url!, env);
    expect(cursorPage.headers.get("x-robots-tag")).toBe("noindex, follow");
    const html = await cursorPage.text();
    expect(blogCards(html)).toEqual(["/blog/fixture-page-25/"]);
    expect(html).toContain('<link rel="canonical" href="https://base2026.dev/blog">');
    const firstHtml = await (await route("/blog", env)).text();
    expect(firstHtml).toContain('rel="next"');
    expect(blogCards(firstHtml)).toHaveLength(27);
  });

  it.each(["", "bad", "2026-02-30T12:00:00.000Z|fixture", "2026-08-30T12:00:00.000Z|UPPER", "x".repeat(151)])("rejects bad cursor %s before preparing SQL", async (cursor) => {
    const db = new SqliteD1(); const env = environment(db);
    const response = await route("/api/blog?cursor=" + encodeURIComponent(cursor), env);
    expect(response.status).toBe(400); expect(response.headers.get("cache-control")).toBe("no-store");
    expect(db.prepared).toHaveLength(0);
  });

  it("rejects duplicated cursor parameters", async () => {
    const db = new SqliteD1(); const env = environment(db);
    const value = encodeURIComponent(PUBLISHED + "|fixture-source-check");
    expect((await route(`/blog?cursor=${value}&cursor=${value}`, env)).status).toBe(400);
    expect(db.prepared).toHaveLength(0);
  });

  it("produces parseable escaped RSS with stable canonical GUIDs and self URL", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    const response = await route("/blog/feed.xml", env);
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("application/rss+xml; charset=utf-8");
    const body = await response.text(); const tree = xml(body);
    expect(tree.tag).toBe("rss"); expect(tree.attrs.version).toBe("2.0");
    expect(xmlNodes(tree, "item")).toHaveLength(3);
    expect(xmlNodes(tree, "guid").map((node) => node.text)).toEqual([ORIGIN + "/blog/fixture-source-check/", ...legacyPaths.map((path) => ORIGIN + path)]);
    expect(xmlNodes(tree, "guid").every((node) => node.attrs.isPermaLink === "true")).toBe(true);
    expect(xmlNodes(tree, "title").map((node) => node.text)).toContain(payload().title);
    expect(xmlNodes(tree, "link").some((node) => node.attrs.rel === "self" && node.attrs.href === ORIGIN + "/blog/feed.xml")).toBe(true);
    expect(xmlNodes(tree, "pubDate").every((node) => Number.isFinite(Date.parse(node.text)))).toBe(true);
    expect(body).toContain("&amp;"); expect(body).not.toContain("<![CDATA[");
  });

  it("bounds RSS to 25 entries even when the merged catalog is larger", async () => {
    const db = new SqliteD1(); const env = environment(db);
    for (let i = 0; i < 26; i += 1) await seed(db, payload({ slug: `fixture-feed-${i}` }));
    const tree = xml(await (await route("/blog/feed.xml", env)).text());
    expect(xmlNodes(tree, "item")).toHaveLength(25);
    expect(new Set(xmlNodes(tree, "guid").map((node) => node.text)).size).toBe(25);
  });

  it("uses a sitemap index pointing to bounded child urlsets, never a nested main index", async () => {
    const db = new SqliteD1(); const env = environment(db);
    for (let i = 0; i < 101; i += 1) await seed(db, payload({ slug: `fixture-map-${String(i).padStart(4, "0")}` }));
    const index = xml(await (await route("/sitemap-blog.xml", env)).text());
    expect(index.tag).toBe("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex");
    expect(xmlNodes(index, "loc").map((node) => node.text)).toEqual([ORIGIN + "/sitemaps/blog-1.xml", ORIGIN + "/sitemaps/blog-2.xml"]);
    const first = xml(await (await route("/sitemaps/blog-1.xml", env)).text());
    const second = xml(await (await route("/sitemaps/blog-2.xml", env)).text());
    expect(first.tag).toBe("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset");
    expect(second.tag).toBe(first.tag);
    expect(xmlNodes(first, "url")).toHaveLength(100); expect(xmlNodes(second, "url")).toHaveLength(1);
    const urls = [...xmlNodes(first, "loc"), ...xmlNodes(second, "loc")].map((node) => node.text);
    expect(new Set(urls).size).toBe(101);
    expect(urls.every((url) => /^https:\/\/base2026\.dev\/blog\/fixture-map-\d{4}\/$/u.test(url))).toBe(true);
    expect((await route("/sitemaps/blog-3.xml", env)).status).toBe(404);
    expect((await route("/sitemaps/blog-50001.xml", env)).status).toBe(404);
    expect(await handleEditorialRoute(new Request(ORIGIN + "/sitemap.xml"), env, NOW)).toBeNull();
    const builder = readFileSync(new URL("../../../scripts/build-base2026-cloudflare-release.py", import.meta.url), "utf8");
    const indexFunction = builder.match(/def _add_hub_sitemap_to_index\([\s\S]*?(?=\n\ndef )/u)?.[0];
    expect(indexFunction).toBeTruthy(); expect(indexFunction).not.toContain("sitemap-blog.xml");
  }, 20_000);

  it("serves an empty child urlset for a valid empty database, not invented legacy D1 rows", async () => {
    const env = environment();
    expect(xmlNodes(xml(await (await route("/sitemaps/blog-1.xml", env)).text()), "url")).toHaveLength(0);
    expect(xmlNodes(xml(await (await route("/sitemap-blog.xml", env)).text()), "loc").map((node) => node.text)).toEqual([ORIGIN + "/sitemaps/blog-1.xml"]);
  });

  it.each([null, { total: -1 }, { total: 1.5 }, { total: "1" }, { total: 5_000_001 }])("rejects invalid or over-capacity sitemap count %j", async (count) => {
    const db = new SqliteD1(); const env = environment(db);
    const prepare = db.prepare.bind(db);
    // The SQLite engine supplies real counts; isolate a malformed D1 result
    // here to test the count-only manifest's failure boundary independently.
    vi.spyOn(db, "prepare").mockImplementation((sql) => {
      const statement = prepare(sql);
      if (sql.startsWith("SELECT COUNT(*) AS total")) vi.spyOn(statement, "first").mockResolvedValue(count);
      return statement;
    });
    const response = await route("/sitemap-blog.xml", env);
    expect(response.status).toBe(503);
    expect(response.headers.get("cache-control")).toBe("no-store");
  });
});

describe("editorial fail-closed and HTTP/RPC boundaries", () => {
  it.each(["POST", "PUT", "DELETE", "PATCH", "OPTIONS"])("rejects public %s before even reading bindings", async (method) => {
    let bindingReads = 0;
    const env: Env = {
      MEMBER_AUTH_ENABLED: "false",
      get DB(): D1Database { bindingReads += 1; throw new Error("Unexpected DB access"); },
      get ASSETS(): Fetcher { bindingReads += 1; throw new Error("Unexpected asset access"); },
      get INBOX_DB(): D1Database { throw new Error("Unexpected Inbox access"); },
      get OUTREACH_DB(): D1Database { throw new Error("Unexpected Outreach access"); },
      get AUTH_DB(): D1Database { throw new Error("Unexpected member auth access"); },
      get MCP_RATE_LIMIT(): RateLimit { throw new Error("Unexpected MCP rate-limit access"); },
    };
    for (const path of ["/blog", "/blog/", "/blog/fixture-source-check/", "/api/blog", "/api/blog/fixture-source-check", "/api/blog/publish", "/blog/feed.xml", "/sitemap-blog.xml", "/sitemaps/blog-1.xml"]) {
      const response = await route(path, env, method);
      expect(response.status, path).toBe(405); expect(response.headers.get("allow")).toBe("GET, HEAD");
    }
    expect(bindingReads).toBe(0);
  });

  it("returns 503, no-store, and a sanitized error when D1 is unavailable", async () => {
    const db = new SqliteD1(); const env = environment(db); db.unavailable = true;
    for (const path of ["/blog", "/api/blog", "/blog/fixture-source-check/", "/blog/feed.xml", "/sitemap-blog.xml", "/sitemaps/blog-1.xml"]) {
      const response = await route(path, env);
      expect(response.status, path).toBe(503);
      expect(response.headers.get("cache-control")).toBe("no-store");
      expect(response.headers.get("retry-after")).toBe("60");
      expect(await response.json()).toEqual({ ok: false, code: "EDITORIAL_TEMPORARILY_UNAVAILABLE" });
    }
    expect(console.error).toHaveBeenCalledWith('{"event":"base2026_editorial_unavailable"}');
  });

  it("rejects hash-invalid persisted payloads on HTML, JSON and RSS reads", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    db.sqlite.prepare("UPDATE editorial_articles SET payload_json=json_set(payload_json,'$.title','Changed fixture title') WHERE slug=?").run(payload().slug);
    for (const path of ["/blog", "/api/blog", "/api/blog/fixture-source-check", "/blog/fixture-source-check/", "/blog/feed.xml"]) {
      expect((await route(path, env)).status, path).toBe(503);
    }
  });

  it("keeps the count-only sitemap manifest but rejects hash-invalid child URL entries", async () => {
    const db = new SqliteD1(); const env = environment(db); await seed(db);
    db.sqlite.prepare("UPDATE editorial_articles SET payload_json=json_set(payload_json,'$.title','Changed fixture title') WHERE slug=?").run(payload().slug);
    expect((await route("/blog/fixture-source-check/", env)).status).toBe(503);
    // The index claims only fixed child endpoints, not article contents or
    // current article health. Root explicitly retains this count-only contract.
    const index = await route("/sitemap-blog.xml", env);
    expect(index.status).toBe(200);
    expect(xmlNodes(xml(await index.text()), "loc").map((node) => node.text)).toEqual([ORIGIN + "/sitemaps/blog-1.xml"]);
    expect((await route("/sitemaps/blog-1.xml", env)).status).toBe(503);
  });

  it("returns 404 for missing/invalid article paths without fetching a fake success shell", async () => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    for (const path of ["/blog/missing/", "/blog/missing", "/api/blog/missing", "/blog/UPPER/", "/blog/bad_slug/", "/blog/" + "a".repeat(121) + "/"]) {
      expect((await route(path, env)).status, path).toBe(404);
    }
    expect(assets.requests).toHaveLength(0);
  });

  it.each(["declared", "streamed"])("rejects an oversized %s shell and cancels its body", async (kind) => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    const cancel = vi.fn(); let pulls = 0;
    assets.responder = () => new Response(new ReadableStream<Uint8Array>({
      pull(controller) { pulls += 1; controller.enqueue(new Uint8Array(MAX_SHELL_BYTES + 1)); }, cancel,
    }), { headers: { "Content-Type": "text/html", ...(kind === "declared" ? { "Content-Length": String(MAX_SHELL_BYTES + 1) } : {}) } });
    expect((await route("/blog", env)).status).toBe(503);
    expect(cancel).toHaveBeenCalled(); expect(pulls).toBeLessThanOrEqual(2);
  });

  it.each(["missing-marker", "duplicate-region", "duplicate-schema", "duplicate-start", "duplicate-end"])("fails closed for %s in the compiled shell", async (mode) => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    const start = "<!--B26_BLOG_CARDS_START-->"; const end = "<!--B26_BLOG_CARDS_END-->";
    if (mode === "missing-marker") assets.shell = assets.shell.replace(start, "");
    if (mode === "duplicate-region") assets.shell = assets.shell.replace(end, end + start + end);
    if (mode === "duplicate-schema") assets.shell = assets.shell.replace("</head>", '<script type="application/ld+json" data-b26-blog-schema>{}</script></head>');
    if (mode === "duplicate-start") assets.shell = assets.shell.replace(start, start + start);
    if (mode === "duplicate-end") assets.shell = assets.shell.replace(end, end + end);
    expect((await route("/blog", env)).status).toBe(503);
  });

  it.each(["wrong-type", "non-200", "invalid-utf8"])("fails closed on an unusable %s shell", async (mode) => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    assets.responder = () => mode === "invalid-utf8"
      ? new Response(new Uint8Array([0xc3, 0x28]), { headers: { "Content-Type": "text/html" } })
      : new Response("Asset fixture", { status: mode === "non-200" ? 404 : 200, headers: { "Content-Type": mode === "wrong-type" ? "application/json" : "text/html" } });
    expect((await route("/blog", env)).status).toBe(503);
  });

  it("leaves homepage and both existing journal articles to the original asset route", async () => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    for (const path of ["/", ...legacyPaths]) {
      const file = path === "/" ? "base2026-startup-homepage.html" : path.includes("source-diversity") ? "base2026-journal-source-diversity.html" : "base2026-journal-cloudflare.html";
      const original = readFileSync(new URL("../../../templates/" + file, import.meta.url), "utf8").replace("{{STARTUP_HEADER}}", header).replace("{{STARTUP_FOOTER}}", footer);
      assets.responder = (request) => new Response(request.method === "HEAD" ? null : original, { headers: { "Content-Type": "text/html" } });
      expect(await handleEditorialRoute(new Request(ORIGIN + path), env, NOW)).toBeNull();
      const response = await worker.fetch(new Request(ORIGIN + path), env, context);
      expect(response.status).toBe(200); expect(await response.text()).toBe(original);
      expect(assets.requests.at(-1)?.url).toBe(ORIGIN + path);
    }
    expect(db.prepared).toHaveLength(0); expect(db.batchCalls).toBe(0);
  });

  it("applies default Worker security headers to success, redirect, validation and error responses", async () => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets); await seed(db);
    for (const [path, method, status] of [
      ["/blog", "GET", 200], ["/api/blog", "GET", 200], ["/blog/feed.xml", "HEAD", 200],
      ["/blog/fixture-source-check", "GET", 308], ["/api/blog?cursor=bad", "GET", 400],
      ["/blog/missing/", "GET", 404], ["/api/blog", "POST", 405],
    ] as const) {
      const response = await worker.fetch(new Request(ORIGIN + path, { method }), env, context);
      expect(response.status, path).toBe(status);
      expect(response.headers.get("x-content-type-options")).toBe("nosniff");
      expect(response.headers.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
      expect(response.headers.get("x-frame-options")).toBe("SAMEORIGIN");
      expect(response.headers.get("permissions-policy")).toContain("camera=()");
    }
    db.unavailable = true;
    const unavailable = await worker.fetch(new Request(ORIGIN + "/blog"), env, context);
    expect(unavailable.status).toBe(503); expect(unavailable.headers.get("x-frame-options")).toBe("SAMEORIGIN");
  });

  it("keeps publication and inspection as service-entrypoint methods, not public HTTP actuators", async () => {
    const db = new SqliteD1(); const assets = new Assets(); const env = environment(db, assets);
    const service = new PublicProjectionEntrypoint(context, env);
    expect(Object.getOwnPropertyNames(PublicProjectionEntrypoint.prototype)).toEqual(expect.arrayContaining(["publishEditorialArticle", "inspectEditorialArticle", "applyProjection", "verifyProjection", "rollbackProjection"]));
    expect(worker).not.toHaveProperty("publishEditorialArticle"); expect(worker).not.toHaveProperty("inspectEditorialArticle");
    expect(await service.publishEditorialArticle(await reviewedPacket())).toMatchObject({ ok: true, status: "published" });
    const inspect = await service.inspectEditorialArticle(payload().slug);
    expect(inspect).toMatchObject({ ok: true, receipt: { slug: payload().slug } });
    expect(inspect).not.toHaveProperty("article");
    expect(await service.inspectEditorialArticle("missing")).toEqual({ ok: false, code: "NOT_FOUND" });
    db.resetCalls();
    for (const path of ["/api/blog/publish", "/api/blog/publishEditorialArticle", "/api/blog/inspectEditorialArticle", "/publishEditorialArticle", "/inspectEditorialArticle"]) {
      const response = await worker.fetch(new Request(ORIGIN + path, { method: "POST" }), env, context);
      expect([404, 405]).toContain(response.status);
    }
    expect(db.batchCalls).toBe(0);
    expect(db.prepared).toHaveLength(0);
  });
});
