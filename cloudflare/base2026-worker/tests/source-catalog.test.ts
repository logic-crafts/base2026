/** Actual SQLite projection joins; synthetic inline HTML, never a corpus dump. */
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { handleSourceCatalog } from "../src/source-catalog";
import { applyPublicProjection, type PublicProjectionRequest } from "../src/public-projection";

const ORIGIN = "https://base2026.dev";
const MAX_SHELL_BYTES = 256 * 1024;
const databases = new Set<SqliteD1>();
const HEADER = '<header class="b26-site-header" data-b26-shell><a href="/">Base2026</a><nav><a href="/workspace/">Search</a><a href="/blog">Blog</a></nav></header>';
const FOOTER = '<footer class="b26-site-footer" data-b26-shell><a href="/methodology">Methodology</a><a href="/opt-out">Creator rights</a></footer>';

function shell(count = 2): string {
  const cards = Array.from({ length: count }, (_, index) => `<article class="intelligence-card"><h3>Synthetic legacy source ${index}</h3><p class="meta">@fixture_legacy</p><p>Reviewed fixture text &amp; attribution.</p><a class="button-link" href="tiktok-video-${7999999900000000000n + BigInt(index)}.html">Open</a></article>`).join("\n");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Excerpt-first source records with attribution and original links.">
    <meta name="robots" content="index,follow"><link rel="canonical" href="${ORIGIN}/sources/">
    <meta property="og:url" content="${ORIGIN}/sources/"><meta property="og:title" content="Source Records">
    <meta name="twitter:title" content="Source Records"><title>Source Records</title>
    <script type="application/ld+json">${JSON.stringify({ "@context": "https://schema.org", "@type": "WebPage", name: "Source Records", url: ORIGIN + "/sources/", isPartOf: { "@type": "WebSite", name: "Base2026", url: ORIGIN + "/" } })}</script>
    <link rel="stylesheet" href="/static/base2026-startup-shell.css"><link rel="stylesheet" href="/static/base2026-core.css">
    </head><body><a class="skip-link" href="#content">Skip to content</a>${HEADER}
    <main id="content" class="app-shell content-page"><section class="page-hero"><h1>Source Records</h1><p class="lead">Excerpt-first source records with attribution and original links.</p></section>
    <section class="content-section" aria-labelledby="source-records-list-heading"><h2 id="source-records-list-heading">Available source records</h2><div class="card-grid">${cards}</div></section>
    </main>${FOOTER}<script src="../static/share-actions.js" defer></script></body></html>`;
}

function sqlValue(value: unknown): SQLInputValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "bigint" || value instanceof Uint8Array) return value;
  throw new Error("Unsupported fixture parameter");
}
function result<T>(rows: T[], changes = 0): D1Result<T> {
  return { success: true, results: rows, meta: { changes, duration: 0, size_after: 0, rows_read: rows.length, rows_written: changes, last_row_id: 0, changed_db: changes > 0 } };
}
class Prepared implements D1PreparedStatement {
  constructor(private readonly db: SqliteD1, private readonly sql: string, private readonly parameters: SQLInputValue[] = []) {}
  bind(...values: unknown[]): D1PreparedStatement { return new Prepared(this.db, this.sql, values.map(sqlValue)); }
  execute<T>(): D1Result<T> {
    if (this.db.failReads) throw new Error("Synthetic binding error, not safe for response bodies");
    const statement = this.db.sqlite.prepare(this.sql);
    return statement.columns().length ? result(statement.all(...this.parameters) as T[]) : result([], Number(statement.run(...this.parameters).changes));
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
class SqliteD1 implements D1Database {
  readonly sqlite = new DatabaseSync(":memory:");
  readonly prepared: string[] = [];
  failReads = false;
  constructor() {
    for (const name of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql"]) {
      this.sqlite.exec(readFileSync(new URL("../migrations/" + name, import.meta.url), "utf8"));
    }
    databases.add(this);
  }
  prepare(sql: string): D1PreparedStatement { this.prepared.push(sql); return new Prepared(this, sql); }
  async batch<T = unknown>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]> {
    this.sqlite.exec("BEGIN");
    try {
      const rows = statements.map((statement) => {
        if (!(statement instanceof Prepared)) throw new Error("Unexpected fixture statement");
        return statement.execute<T>();
      });
      this.sqlite.exec("COMMIT"); return rows;
    } catch (error) { this.sqlite.exec("ROLLBACK"); throw error; }
  }
  async exec(sql: string): Promise<D1ExecResult> { this.sqlite.exec(sql); return { count: 1, duration: 0 }; }
  withSession(): D1DatabaseSession { throw new Error("Sessions not needed by catalog"); }
  async dump(): Promise<ArrayBuffer> { throw new Error("Catalog cannot dump the database"); }
}
class Assets implements Fetcher {
  readonly requests: Request[] = [];
  html = shell();
  responder: (() => Response | Promise<Response>) | null = null;
  async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const request = new Request(input, init); this.requests.push(request);
    return this.responder ? this.responder() : new Response(this.html, { headers: { "Content-Type": "text/html; charset=utf-8", ETag: '"static-only"', "Last-Modified": "Sun, 30 Aug 2026 12:00:00 GMT" } });
  }
  connect(): Socket { throw new Error("Catalog cannot open sockets"); }
}

function packet(index: number, date = "2026-08-20", cards = 2): PublicProjectionRequest {
  const video = String(7999999800000000000n + BigInt(index));
  const handle = "fixture_creator_" + index;
  return {
    schema_version: "base2026.public-projection.v1", projection_id: index.toString(16).padStart(40, "0"),
    source: { source_id: `tiktok:${handle}:${video}`, creator_handle: "@" + handle,
      canonical_url: `https://www.tiktok.com/@${handle}/video/${video}`, published_at: date || null,
      title_or_description: "A synthetic public source used only to test catalog navigation.", duration_seconds: 30 },
    manifest_sha256: "a".repeat(64), content_sha256: "b".repeat(64), private_import_receipt_sha256: "c".repeat(64),
    cards: Array.from({ length: cards }, (_, ordinal) => ({ ordinal,
      claim_text: "A fixture observation must not become a catalog assertion.",
      suggested_action: "Inspect the original source before using this fixture observation.",
      topic_label: "Public fixture", evidence_excerpt: "This synthetic observation is a fixture, not evidence of any real result.",
      evidence_start_seconds: ordinal * 5, evidence_end_seconds: ordinal * 5 + 4,
    })),
  };
}

let db: SqliteD1;
let assets: Assets;
async function seed(index: number, date = "2026-08-20", cards = 2): Promise<PublicProjectionRequest> {
  const value = packet(index, date, cards); await applyPublicProjection(db, value); return value;
}
async function get(path = "/sources/", method = "GET", headers: HeadersInit = {}): Promise<Response> {
  const request = new Request(ORIGIN + path, { method, headers });
  const value = await handleSourceCatalog(request, { DB: db, ASSETS: assets }, new URL(request.url));
  if (!value) throw new Error("Expected catalog response");
  return value;
}
function cloudHtml(html: string): string {
  return html.split('<section id="b26-source-catalog"')[1]?.split('<section class="content-section" aria-labelledby="source-records-list-heading">')[0] ?? "";
}
function ids(html: string): string[] { return [...new Set([...cloudHtml(html).matchAll(/href="\/sources\/tiktok-video-(\d+)"/gu)].map((m) => m[1]))]; }
function nextLink(html: string): string | null { return /rel="next" href="([^"]+)"/u.exec(cloudHtml(html))?.[1] ?? null; }
function token(date: string, video: string): string { return Buffer.from(JSON.stringify([1, date, video])).toString("base64url"); }
function schema(html: string): Record<string, unknown> {
  return JSON.parse(/<script type="application\/ld\+json">([^<]+)<\/script>/u.exec(html)?.[1] ?? "null") as Record<string, unknown>;
}

beforeEach(() => { db = new SqliteD1(); assets = new Assets(); });
afterEach(() => { vi.restoreAllMocks(); for (const item of databases) item.sqlite.close(); databases.clear(); });

describe("source catalog navigation", () => {
  it("labels a source's extracted topic without presenting its claim as a catalog fact", async () => {
    await seed(1);
    const response = await get();
    const html = cloudHtml(await response.text());
    expect(response.status).toBe(200);
    expect(html).toContain("Extracted topic: Public fixture");
    expect(html).not.toContain("A fixture observation must not become a catalog assertion.");
  });

  it("keeps the legacy-only shell and identifies its count as a static selection", async () => {
    assets.html = shell(80);
    db.prepared.length = 0;
    const response = await get(); const html = await response.text();
    expect(response.status).toBe(200);
    expect(html).toContain(HEADER); expect(html).toContain(FOOTER);
    expect(html.match(/<h1\b/gu)).toHaveLength(1);
    expect(html).toContain("80 source records from the retained static selection");
    expect(html.match(/href="tiktok-video-\d+\.html"/gu)).toHaveLength(80);
    expect(html).toContain("No cloud-added source records are currently available");
    expect(schema(html)).toMatchObject({ "@type": "CollectionPage", url: ORIGIN + "/sources/" });
    expect(db.prepared).toHaveLength(1);
    expect(db.prepared[0]).not.toMatch(/\b(?:INSERT|UPDATE|DELETE|OFFSET)\b/iu);
    expect(response.headers.get("ETag")).toBeNull();
    expect(response.headers.get("Last-Modified")).toBeNull();
  });

  it("lists valid applied projections once per source without rendering claims or receipt details", async () => {
    const first = await seed(1, "2026-08-20", 3); await seed(2, "", 1);
    const response = await get(); const html = await response.text(); const cloud = cloudHtml(html);
    expect(response.status).toBe(200); expect(ids(html)).toHaveLength(2);
    expect(cloud).toContain("@fixture_creator_1"); expect(cloud).toContain("3 extracted notes");
    expect(cloud).toContain("1 extracted note"); expect(cloud).toContain("Publication date not supplied");
    expect(cloud).toContain(first.source.canonical_url);
    expect(cloud).toContain("not an endorsement");
    expect(cloud).not.toContain(first.cards[0].claim_text);
    expect(html).not.toContain(first.cards[0].evidence_excerpt);
    expect(html).not.toContain(first.projection_id);
    expect(html).not.toContain(first.source.source_id);
    expect(html).not.toContain(first.private_import_receipt_sha256);
    expect(html).not.toContain("receipt_sha256");
    expect(schema(html)).toMatchObject({ mainEntity: { numberOfItems: 2 } });
  });

  it("has normal href pagination, no duplicate records on tied dates, and a finite last page", async () => {
    for (let index = 1; index <= 65; index += 1) await seed(index, index <= 5 ? "" : "2026-08-20", 1);
    const pages: string[] = []; const seen: string[] = []; let path: string | null = "/sources/";
    while (path) {
      expect(pages.length).toBeLessThan(4);
      const response = await get(path); expect(response.status).toBe(200);
      const html = await response.text(); pages.push(html); seen.push(...ids(html));
      path = nextLink(html);
    }
    expect(pages.map((page) => ids(page).length)).toEqual([30, 30, 5]);
    expect(new Set(seen).size).toBe(65);
    expect(seen.slice(0, 2)).toEqual([String(7999999800000000065n), String(7999999800000000064n)]);
    const secondCanonical = /rel="canonical" href="([^"]+)"/u.exec(pages[1])?.[1];
    expect(pages[1]).toContain('name="robots" content="noindex,follow"');
    expect(pages[1]).toContain('href="/sources/#b26-source-catalog"');
    expect(schema(pages[1]).url).toBe(secondCanonical);
    expect(pages[1]).toContain(`property="og:url" content="${secondCanonical}"`);
    expect(new URL(secondCanonical!).searchParams.get("after")).toMatch(/^[A-Za-z0-9_-]+$/u);
  });

  it("does not produce a next URL when the page has exactly 30 records", async () => {
    for (let index = 1; index <= 30; index += 1) await seed(index, "2026-08-20", 1);
    const html = await (await get()).text(); expect(ids(html)).toHaveLength(30); expect(nextLink(html)).toBeNull();
  });

  it("retains the core design classes without adding a script or motion requirement", async () => {
    await seed(1);
    const html = await (await get()).text(); const cloud = cloudHtml(html);
    expect(cloud).toContain('class="card-grid"'); expect(cloud).toContain('class="intelligence-card"');
    expect(cloud).not.toMatch(/<script|onclick=/iu);
    const css = /<style data-b26-source-catalog>([\s\S]*?)<\/style>/u.exec(html)?.[1] ?? "";
    expect(css).toContain("min-width:0"); expect(css).toContain("overflow-wrap:anywhere");
    expect(css).toContain("flex-wrap:wrap"); expect(css).toContain("@media print");
    expect(css).not.toMatch(/animation:|transition:|position:sticky|@import/iu);
    expect(html).toContain('/static/base2026-core.css');
  });

  it("reflects new and rolled-back projections without changing the static asset", async () => {
    const first = await seed(1); const staticBefore = assets.html;
    expect(ids(await (await get()).text())).toHaveLength(1);
    await seed(2); expect(ids(await (await get()).text())).toHaveLength(2);
    db.sqlite.prepare("UPDATE public_projection_receipts SET status='rolled_back' WHERE projection_id=?").run(first.projection_id);
    expect(ids(await (await get()).text())).toHaveLength(1); expect(assets.html).toBe(staticBefore);
  });

  it("uses the asset binding with an uncredentialed GET and no client conditionals", async () => {
    await seed(1);
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No external fetch allowed"));
    const response = await get("/sources/", "GET", { Cookie: "fixture=not-forwarded", Authorization: "fixture-not-forwarded", "If-None-Match": '"static-only"' });
    expect(response.status).toBe(200); expect(fetchSpy).not.toHaveBeenCalled();
    expect(assets.requests).toHaveLength(1);
    const request = assets.requests[0];
    expect(request.url).toBe(ORIGIN + "/sources/"); expect(request.method).toBe("GET");
    expect(request.headers.get("Accept")).toBe("text/html");
    for (const header of ["cookie", "authorization", "if-none-match"]) expect(request.headers.get(header)).toBeNull();
  });

  it("HEAD performs the same validation and returns matching headers without a body", async () => {
    await seed(1); const response = await get(); const head = await get("/sources/", "HEAD");
    expect(head.status).toBe(200); expect(await head.text()).toBe("");
    for (const header of ["Content-Type", "Cache-Control", "X-Robots-Tag"]) expect(head.headers.get(header)).toBe(response.headers.get(header));
    expect(assets.requests.every((request) => request.method === "GET")).toBe(true);
    db.failReads = true; expect((await get("/sources/", "HEAD")).status).toBe(503);
  });

  it.each(["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])("rejects %s before accessing bindings", async (method) => {
    db.prepared.length = 0;
    const response = await get("/sources/?unexpected=1", method);
    expect(response.status).toBe(405); expect(response.headers.get("Allow")).toBe("GET, HEAD");
    expect(db.prepared).toHaveLength(0); expect(assets.requests).toHaveLength(0);
  });

  it("redirects only the no-slash catalog spelling, without an open redirect", async () => {
    const response = await get("/sources"); expect(response.status).toBe(308);
    expect(response.headers.get("Location")).toBe(ORIGIN + "/sources/");
    expect(db.prepared).toHaveLength(0); expect(assets.requests).toHaveLength(0);
  });

  it.each(["/", "/topics/", "/sources/index.html", "/sources/tiktok-video-7999999800000000001", "/api/stats", "/blog"])("does not intercept %s", async (path) => {
    const request = new Request(ORIGIN + path);
    expect(await handleSourceCatalog(request, { DB: db, ASSETS: assets }, new URL(request.url))).toBeNull();
    expect(db.prepared).toHaveLength(0); expect(assets.requests).toHaveLength(0);
  });
});

describe("catalog integrity gates", () => {
  it.each([
    ["rolled back", "UPDATE public_projection_receipts SET status='rolled_back'"],
    ["missing card", "DELETE FROM public_projection_cards WHERE ordinal=1"],
    ["missing search row", "DELETE FROM search_documents WHERE chunk_index=1"],
    ["wrong card source", "UPDATE public_projection_cards SET source_id='tiktok:other:7999999800000000001' WHERE ordinal=1"],
    ["wrong document source", "UPDATE search_documents SET source_id='tiktok:other:7999999800000000001' WHERE chunk_index=1"],
    ["wrong search id", "UPDATE public_projection_cards SET search_id='missing-search-id' WHERE ordinal=1"],
    ["wrong document projection", "UPDATE search_documents SET projection_id='other' WHERE chunk_index=1"],
    ["wrong document card", "UPDATE search_documents SET chunk_id='other' WHERE chunk_index=1"],
    ["wrong ordinal", "UPDATE search_documents SET chunk_index=2 WHERE chunk_index=1"],
    ["partial public flag", "UPDATE search_documents SET full_transcript_public=1 WHERE chunk_index=1"],
    ["partial held state", "UPDATE search_documents SET admission_state='held' WHERE chunk_index=1"],
    ["wrong public policy", "UPDATE search_documents SET public_policy='other' WHERE chunk_index=1"],
    ["mismatched date", "UPDATE search_documents SET published_date='2026-08-21' WHERE chunk_index=1"],
    ["invalid receipt shape", "UPDATE public_projection_receipts SET receipt_sha256=''"],
    ["non-contiguous card ordinals", "UPDATE public_projection_cards SET ordinal=2 WHERE ordinal=1"],
    ["unsafe creator", "UPDATE search_documents SET creator_handle='@fixture<script>'"],
    ["unsafe source URL", "UPDATE search_documents SET source_url='https://evil.example/collect'"],
    ["non-numeric video", "UPDATE search_documents SET video_id='799999980<script>'"],
  ])("omits the whole projection when %s", async (_label, change) => {
    await seed(1); db.sqlite.exec(change);
    const response = await get(); expect(response.status).toBe(200);
    expect(ids(await response.text())).toHaveLength(0);
  });

  it("rejects extra unmatched child rows rather than passing a matching subset", async () => {
    const item = await seed(1);
    db.sqlite.prepare(`INSERT INTO public_projection_cards
      (projection_id,source_id,ordinal,card_id,search_id,claim_text,suggested_action,topic_label,evidence_excerpt,evidence_start_seconds,evidence_end_seconds)
      VALUES (?,?,2,'extra-card','extra-search','unused','unused','unused','unused',0,1)`).run(item.projection_id, item.source.source_id);
    expect(ids(await (await get()).text())).toHaveLength(0);
  });

  it("rejects extra search rows even when the receipt's expected rows still match", async () => {
    const item = await seed(1);
    db.sqlite.prepare(`INSERT INTO search_documents (id,item_id,source_id,chunk_id,body,projection_id)
      VALUES ('extra','extra',?,'extra','unused',?)`).run(item.source.source_id, item.projection_id);
    expect(ids(await (await get()).text())).toHaveLength(0);
  });

  it("does not confuse unrelated legacy rows with cloud-added records", async () => {
    db.sqlite.prepare("INSERT INTO search_documents (id,item_id,source_id,chunk_id,body) VALUES ('legacy','legacy','legacy','legacy','Legacy fixture')").run();
    expect(ids(await (await get()).text())).toHaveLength(0);
    await seed(1); expect(ids(await (await get()).text())).toHaveLength(1);
  });

  it("rejects a source that also has a legacy row outside its active projection", async () => {
    const item = await seed(1);
    db.sqlite.prepare("INSERT INTO search_documents (id,item_id,source_id,chunk_id,body) VALUES ('legacy','legacy',?,'legacy','Legacy fixture')").run(item.source.source_id);
    expect(ids(await (await get()).text())).toHaveLength(0);
  });

  it("fails closed for invalid persisted date metadata and database errors", async () => {
    await seed(1); db.sqlite.exec("UPDATE search_documents SET published_date='2026-02-31'");
    expect((await get()).status).toBe(503);
    db.failReads = true; const response = await get();
    expect(response.status).toBe(503); expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(await response.text()).not.toContain("Synthetic binding error");
  });

  it("never reflects injected claim, body or metadata markup", async () => {
    await seed(1);
    db.sqlite.exec("UPDATE search_documents SET title='<script>alert(1)</script>', body='<img onerror=alert(1)>'");
    const response = await get(); const html = await response.text();
    expect(response.status).toBe(200); expect(html).not.toContain("alert(1)");
    expect(html).toContain("Reviewed fixture text &amp; attribution");
    expect(html).not.toContain("<img onerror");
  });
});

describe("catalog cursor and shell boundaries", () => {
  it.each([
    "?q=anything", "?page=2", "?limit=100", "?&&", "?after=", "?after=bad", "?after=a&after=b", "?after=a&sort=newest",
    "?after=" + "A".repeat(129), "?after=" + Buffer.from('[2,"2026-08-20","7999999800000000001"]').toString("base64url"),
    "?after=" + token("2026-02-31", "7999999800000000001"), "?after=" + token("2026-08-20", "not-numeric"),
    "?after=" + Buffer.from('[1, "2026-08-20", "7999999800000000001"]').toString("base64url"),
  ])("rejects malformed or unsupported query %s before D1/assets", async (query) => {
    const response = await get("/sources/" + query); expect(response.status).toBe(400);
    expect(db.prepared).toHaveLength(0); expect(assets.requests).toHaveLength(0);
  });

  it("rejects invented anchors and terminal cursors instead of making empty query pages", async () => {
    expect((await get("/sources/?after=" + token("2026-08-20", "7999999800000000001"))).status).toBe(400);
    await seed(1);
    expect((await get("/sources/?after=" + token("2026-08-20", "7999999800000000001"))).status).toBe(404);
  });

  it.each([
    ["extra main", (html: string) => html.replace("</main>", "</main><main></main>")],
    ["missing main", (html: string) => html.replace('<main id="content" class="app-shell content-page">', "<div>")],
    ["missing legacy seam", (html: string) => html.replace('id="source-records-list-heading"', 'id="different"')],
    ["duplicate legacy heading", (html: string) => html.replace("</main>", '<h2 id="source-records-list-heading">Available source records</h2></main>')],
    ["missing footer", (html: string) => html.replace(FOOTER, "")],
    ["misordered header closure", (html: string) => html.replace("</header>", "").replace("</main>", "</main></header>")],
    ["extra H1", (html: string) => html.replace("</main>", "<h1>Other page</h1></main>")],
    ["extra canonical", (html: string) => html.replace("</head>", `<link rel="canonical" href="${ORIGIN}/sources/"></head>`)],
    ["single-quoted duplicate canonical", (html: string) => html.replace("</head>", `<link rel='canonical' href='${ORIGIN}/sources/'></head>`)],
    ["unquoted duplicate robots", (html: string) => html.replace("</head>", '<meta name=robots content=noindex></head>')],
    ["wrong canonical", (html: string) => html.replace('href="https://base2026.dev/sources/"', 'href="https://example.com/other"')],
    ["duplicate schema", (html: string) => html.replace("</head>", '<script type="application/ld+json">{}</script></head>')],
    ["single-quoted duplicate schema", (html: string) => html.replace("</head>", "<script type='application/ld+json'>{}</script></head>")],
    ["invalid schema", (html: string) => html.replace('"@type":"WebPage"', '"@type":"Other"')],
    ["duplicate legacy target", (html: string) => html.replace("7999999900000000001.html", "7999999900000000000.html")],
    ["unexpected base", (html: string) => html.replace("</head>", '<base href="/elsewhere/"></head>')],
  ])("fails closed for %s", async (_label, change) => {
    assets.html = change(shell()); const response = await get();
    expect(response.status).toBe(503); expect(await response.text()).not.toContain("Cloud-added source records");
  });

  it.each([301, 404, 500])("does not follow or pass through an asset response %s", async (status) => {
    assets.responder = () => new Response("bad asset", { status, headers: { "Content-Type": "text/html", Location: ORIGIN + "/" } });
    expect((await get()).status).toBe(503); expect(assets.requests).toHaveLength(1);
  });

  it("rejects wrong MIME, oversized declared/streamed bodies, and malformed UTF-8", async () => {
    assets.responder = () => new Response(shell(), { headers: { "Content-Type": "application/json" } });
    expect((await get()).status).toBe(503);
    assets.responder = () => new Response(shell(), { headers: { "Content-Type": "text/html", "Content-Length": String(MAX_SHELL_BYTES + 1) } });
    expect((await get()).status).toBe(503);
    assets.responder = () => new Response("x".repeat(MAX_SHELL_BYTES + 1), { headers: { "Content-Type": "text/html" } });
    expect((await get()).status).toBe(503);
    assets.responder = () => new Response(new Uint8Array([0xc3, 0x28]), { headers: { "Content-Type": "text/html" } });
    expect((await get()).status).toBe(503);
  });
});
