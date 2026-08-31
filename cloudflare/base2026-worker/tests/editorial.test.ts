import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";
import { afterEach, describe, expect, it } from "vitest";
import {
  EDITORIAL_LIMITS,
  EDITORIAL_SCHEMA,
  EDITORIAL_SITEMAP_PAGE_SIZE,
  EditorialStoreError,
  EditorialValidationError,
  editorialArticlePath,
  getEditorialArticle,
  isEditorialRelatedPath,
  listEditorialArticles,
  listEditorialSitemapEntries,
  parseEditorialPayload,
  publishEditorialArticle,
  validateEditorialPacket,
  validateEditorialPayload,
  type EditorialDatabase,
  type EditorialPacket,
  type EditorialPayload,
} from "../src/editorial";

const NOW = "2026-08-30T16:00:00.000Z";
const PUBLISHED = "2026-08-29T10:00:00.000Z";
const REVIEWED = "2026-08-30T15:00:00.000Z";
// Explicitly non-secret pieces build credential-shaped validator fixtures at
// runtime; source files must not themselves contain apparent credentials.
const SYNTHETIC_CREDENTIAL_FIXTURES = {
  bearer: ["Bearer", ["not", "a", "real", "test", "token"].join("-")].join(" "),
  slug: ["sk", "proj", "not", "a", "real", "credential"].join("-"),
  asset: ["sk", "live", "not", "a", "real", "credential"].join("_"),
};
const migration = readFileSync(new URL("../migrations/0004_editorial_articles.sql", import.meta.url), "utf8");
const databases = new Set<SqliteD1>();

function article(overrides: Partial<EditorialPayload> = {}): EditorialPayload {
  return {
    schema_version: EDITORIAL_SCHEMA,
    kind: "source_based_article",
    slug: "tracing-evidence",
    revision: 1,
    title: "Tracing a useful evidence brief",
    description: "A bounded example of keeping editorial observations attached to public sources.",
    lede: "A source link gives readers a way to inspect the material behind an editorial observation.",
    category: "Research notes",
    tags: ["Evidence", "Editorial review"],
    published_at: PUBLISHED,
    updated_at: PUBLISHED,
    author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: "Prepared with AI assistance; linked source material remains the basis for editorial review.",
    hero: {
      path: "/static/assets/editorial/evidence-diagram.webp",
      alt: "Two source documents beside an editorial note",
      credit: "Base2026 illustration",
      ai_generated: true,
    },
    sources: [
      { id: "d1", url: "https://developers.cloudflare.com/d1/worker-api/d1-database/", title: "D1 database methods", creator: "Cloudflare", checked_at: "2026-08-30T14:00:00.000Z" },
      { id: "sqlite", url: "https://www.sqlite.org/lang_transaction.html", title: "SQLite transactions", checked_at: "2026-08-30T14:00:00.000Z" },
    ],
    sections: [{
      id: "the-reading-path", heading: "Keep the reading path visible", blocks: [
        { type: "paragraph", text: "The reader can inspect both documents before relying on the editorial interpretation.", citation_ids: ["d1", "sqlite"] },
        { type: "list", items: [{ text: "Keep a specific link beside an observation.", citation_ids: ["d1"] }, { text: "Treat the article as a starting point for further reading.", citation_ids: [] }] },
      ],
    }],
    related_paths: ["/blog", "/dataset", "/opt-out", "/journal/source-diversity-check/"],
    ...overrides,
  };
}

async function packet(payload = article()): Promise<EditorialPacket> {
  const checked = await validateEditorialPayload(payload, NOW);
  if (!checked.ok) throw new Error(`invalid test fixture: ${JSON.stringify(checked.issues)}`);
  return { payload, review: { reviewer: "sol-max", outcome: "pass", reviewed_at: REVIEWED, payload_sha256: checked.payload_sha256 } };
}

function paragraphText(payload: EditorialPayload, text: string): EditorialPayload {
  payload.sections[0].blocks[0] = { type: "paragraph", text, citation_ids: ["d1", "sqlite"] };
  return payload;
}

async function rejected(value: unknown, code?: string): Promise<void> {
  const result = await validateEditorialPayload(value, NOW);
  expect(result.ok).toBe(false);
  if (!result.ok && code) expect(result.issues[0].code).toBe(code);
}

function sqlInput(value: unknown): SQLInputValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "bigint" || value instanceof Uint8Array) return value;
  throw new Error("unsupported SQLite test input");
}

function d1Result<T>(results: T[], changes = 0): D1Result<T> {
  return { success: true, results, meta: { changes, duration: 0, size_after: 0, rows_read: results.length, rows_written: changes, last_row_id: 0, changed_db: changes > 0 } };
}

/** Real SQLite SQL with the documented D1 prepared/batch signatures. */
class SqlitePrepared implements D1PreparedStatement {
  constructor(private readonly db: SqliteD1, private readonly sql: string, private readonly parameters: SQLInputValue[] = []) {}

  bind(...values: unknown[]): D1PreparedStatement { return new SqlitePrepared(this.db, this.sql, values.map(sqlInput)); }

  execute<T>(): D1Result<T> {
    const statement = this.db.sqlite.prepare(this.sql);
    if (statement.columns().length) return d1Result(statement.all(...this.parameters) as T[]);
    const result = statement.run(...this.parameters);
    return d1Result<T>([], Number(result.changes));
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

class SqliteD1 implements EditorialDatabase {
  readonly sqlite = new DatabaseSync(":memory:");
  batchCalls = 0;

  constructor() {
    for (const name of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql", "0004_editorial_articles.sql"]) {
      this.sqlite.exec(readFileSync(new URL(`../migrations/${name}`, import.meta.url), "utf8"));
    }
    databases.add(this);
  }

  prepare(sql: string): D1PreparedStatement { return new SqlitePrepared(this, sql); }

  async batch<T = unknown>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]> {
    this.batchCalls += 1;
    this.sqlite.exec("BEGIN");
    try {
      const results = statements.map((statement) => {
        if (!(statement instanceof SqlitePrepared)) throw new Error("unexpected prepared statement");
        return statement.execute<T>();
      });
      this.sqlite.exec("COMMIT");
      return results;
    } catch (error) {
      this.sqlite.exec("ROLLBACK");
      throw error;
    }
  }

  count(table: "editorial_articles" | "editorial_publication_receipts" | "search_documents" | "public_projection_receipts"): number {
    return Number(this.sqlite.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count);
  }
}

afterEach(() => {
  for (const database of databases) database.sqlite.close();
  databases.clear();
});

describe("editorial structural/public boundary", () => {
  it("creates a detached canonical payload and stable SHA-256 independent of key order", async () => {
    const input = article();
    const before = JSON.stringify(input);
    const first = await validateEditorialPayload(input, NOW);
    const reordered = Object.fromEntries(Object.entries(input).reverse());
    const second = await validateEditorialPayload(reordered, NOW);
    expect(first.ok && second.ok).toBe(true);
    if (!first.ok || !second.ok) return;
    expect(first.payload).not.toBe(input);
    expect(first.payload.sources).not.toBe(input.sources);
    expect(first.payload_sha256).toBe(second.payload_sha256);
    expect(first.payload_sha256).toBe(createHash("sha256").update(first.canonical_payload_json).digest("hex"));
    expect(JSON.stringify(input)).toBe(before);
    expect(first.diagnostics).toEqual({ source_count: 2, distinct_source_urls: 2, distinct_source_metadata: 2, known_creator_count: 1, sources_without_known_creator: 1, cited_source_count: 2, section_count: 1 });
    expect(editorialArticlePath(input.slug)).toBe("/blog/tracing-evidence/");
  });

  it("normalizes equivalent timezone-aware ISO timestamps before hashing", async () => {
    const normalized = await validateEditorialPayload(article(), NOW);
    const offset = await validateEditorialPayload(article({ published_at: "2026-08-29T06:00:00-04:00", updated_at: "2026-08-29T06:00:00-04:00" }), NOW);
    expect(normalized.ok && offset.ok).toBe(true);
    if (normalized.ok && offset.ok) expect(normalized.payload_sha256).toBe(offset.payload_sha256);
  });

  it("detaches the payload before asynchronous hashing", async () => {
    const input = article();
    const pending = validateEditorialPayload(input, NOW);
    input.sources[0].title = "Changed after validation started";
    const result = await pending;
    expect(result.ok && result.payload.sources[0].title).toBe("D1 database methods");
  });

  it("hashes array order and every public field, including revision and disclosure", async () => {
    const original = await packet();
    for (const changed of [article({ revision: 2 }), article({ ai_assistance_disclosure: "AI assisted editing of this article." }), article({ tags: [...original.payload.tags].reverse() })]) {
      const result = await validateEditorialPacket({ payload: changed, review: original.review }, NOW);
      expect(result).toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_REVIEW_HASH_MISMATCH" }] });
    }
  });

  it.each([
    ["root", () => ({ ...article(), prompt: "not public" })],
    ["author", () => article({ author: { name: "Alex Yarosh", email: "owner@example.com" } as EditorialPayload["author"] })],
    ["hero", () => article({ hero: { ...article().hero!, html: "unsafe" } as NonNullable<EditorialPayload["hero"]> })],
    ["source", () => ({ ...article(), sources: [{ ...article().sources[0], raw_transcript: "not public" }, article().sources[1]] })],
    ["section", () => ({ ...article(), sections: [{ ...article().sections[0], raw: "not public" }] })],
    ["paragraph", () => ({ ...article(), sections: [{ ...article().sections[0], blocks: [{ type: "paragraph", text: "A sentence", citation_ids: [], html: "not public" }] }] })],
    ["list item", () => ({ ...article(), sections: [{ ...article().sections[0], blocks: [{ type: "list", items: [{ text: "A sentence", citation_ids: [], prompt: "not public" }] }] }] })],
  ])("rejects unsupported fields at %s", async (_name, build) => { await rejected(build(), "EDITORIAL_UNSUPPORTED_FIELDS"); });

  it("rejects unknown packet/review fields and any missing/pass-mismatched review", async () => {
    const input = await packet();
    for (const value of [{ payload: input.payload }, { ...input, private_notes: "not public" }, { ...input, review: { ...input.review, reviewer: "other" } }, { ...input, review: { ...input.review, outcome: "hold" } }, { ...input, review: { ...input.review, prompt: "not public" } }]) {
      expect((await validateEditorialPacket(value, NOW)).ok).toBe(false);
    }
  });

  it.each(["Upper-Case", "has_underscore", "two--hyphens", "trailing-", "-leading", "../path", "café", "a/b", "x".repeat(121)])("rejects noncanonical slug %s", async (slug) => { await rejected(article({ slug })); });

  it.each([0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1, Number.NaN, Number.POSITIVE_INFINITY])("rejects revision %s", async (value) => { await rejected(article({ revision: value }), "EDITORIAL_REVISION_INVALID"); });

  it("rejects incorrect author, schema and unknown kind without adding defaults", async () => {
    for (const input of [{ ...article(), author: { name: "Someone Else" } }, { ...article(), schema_version: "v2" }, { ...article(), kind: "unreviewed_news" }, { ...article(), tags: undefined }]) await rejected(input);
  });

  it.each([
    "2026-02-30T10:00:00Z", "2025-02-29T10:00:00Z", "2026-13-01T10:00:00Z", "2026-08-29T24:00:00Z",
    "2026-08-29T10:00:60Z", "2026-08-29T10:00:00", "2026-08-29", "2026-08-29T10:00:00+25:00", "0000-01-01T00:00:00Z",
  ])("rejects invalid/non-timezone ISO %s", async (value) => { await rejected(article({ published_at: value })); });

  it("checks timestamp chronology/future skew using only the injected clock", async () => {
    await rejected(article({ updated_at: "2026-08-28T10:00:00Z" }), "EDITORIAL_TIMESTAMP_ORDER");
    await rejected(article({ updated_at: "2026-08-30T16:05:01Z" }), "EDITORIAL_TIMESTAMP_FUTURE");
    const futureSource = article();
    futureSource.sources[0].checked_at = "2027-01-01T00:00:00Z";
    await rejected(futureSource, "EDITORIAL_TIMESTAMP_FUTURE");
    const input = await packet();
    expect((await validateEditorialPacket({ ...input, review: { ...input.review, reviewed_at: "2026-08-28T10:00:00Z" } }, NOW)).ok).toBe(false);
    expect((await validateEditorialPacket({ ...input, review: { ...input.review, reviewed_at: "2026-08-30T16:06:00Z" } }, NOW)).ok).toBe(false);
    expect((await validateEditorialPayload(article({ updated_at: "2026-08-30T16:05:00Z" }), NOW)).ok).toBe(true);
  });

  it.each([
    "<script>alert(1)</script>", "&lt;img src=x onerror=alert(1)&gt;", "%253Cscript%253E", "javascript:alert(1)",
    "Contact analyst@example.com", "Contact тест@пример.рф", "Contact analyst＠example.com", "Call +1 (555) 123-4567", "Call +15551234567", "api_key=not-a-real-test-credential", "api%5fkey%3Dnot-a-real-test-credential %broken", SYNTHETIC_CREDENTIAL_FIXTURES.bearer,
    "PRIVATE_ONLY", "private_notes: test", "raw_transcript: text", "RAW TRANSCRIPT", "RAW TRANSCRIPT:\nnot public", "RAW TRANSCRIPT\nnot public", "## Raw transcript\nnot public", "Private notes\nnot public",
    "WEBVTT\n00:00:01.000 --> 00:00:03.000\nExample speech", "00:00:01,000 --> 00:00:03,000\nExample speech",
    "Read /Users/example/source.txt", "Open file:///tmp/example", "Use C:\\Users\\example\\packet.json", "access\u200b_token=example",
    "\ud800", "\u0000",
  ])("rejects private/markup/encoding material %s", async (text) => { await rejected(paragraphText(article(), text)); });

  it("allows ordinary privacy/engineering prose without calling the structural gate a fact-check", async () => {
    const prose = paragraphText(article(), "Raw transcripts stay private. API keys are not published. The API key is kept in a secret binding. Private markets and token economics require careful sources. Reader 🙂 review is useful.");
    expect((await validateEditorialPayload(prose, NOW)).ok).toBe(true);
    const unsupportedClaim = paragraphText(article(), "Every expert everywhere agrees with this claim.");
    const result = await validateEditorialPayload(unsupportedClaim, NOW);
    expect(result.ok).toBe(true); // The separate Sol reviewer must assess evidence/entailment.
    expect(result).not.toHaveProperty("fact_checked");
    expect(result).not.toHaveProperty("independent_sources");
  });

  it.each([
    "http://example.com/source", "//example.com/source", "https://localhost/source", "https://service.local/source", "https://service.localdomain/source",
    "https://internal/source", "https://service.internal/source", "https://127.0.0.1/source", "https://127.1/source",
    "https://2130706433/source", "https://0x7f000001/source", "https://10.1.2.3/source", "https://169.254.169.254/source",
    "https://[::1]/source", "https://[::ffff:127.0.0.1]/source", "https://8.8.8.8/source", "https://127.0.0.1.nip.io/source",
    "https://person:password@example.com/source", "https://example.com:8443/source", "https://example.com./source",
    "https://example.com/source#access_token=test", "https://example.com/source#plain-anchor", "https://example.com/?access_token=test",
    "https://example.com/?X-Amz-Signature=test", "https://example.com/?sessionId=test", "https://example.com/?email=person%40example.com",
    "https://example.com/?api%255Fkey=test", "https://example.com/%2e%2e/source", "https://example.com/%zz",
    "https://example.com/\\private", "https://example.com/Users/example/source", "https://example.com/secret@example.com",
  ])("rejects nonpublic/credential/ambiguous source URL %s", async (url) => {
    const input = article(); input.sources[0].url = url; await rejected(input);
  });

  it("accepts a bounded public video identifier query and keeps unknown creator metadata explicit", async () => {
    const input = article();
    input.sources[0].url = "https://www.youtube.com/watch?v=abcdefghijk";
    input.sources[0].creator = "Unknown";
    const result = await validateEditorialPayload(input, NOW);
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.diagnostics).toMatchObject({ known_creator_count: 0, sources_without_known_creator: 2 });
  });

  it("requires two distinct source URLs and metadata tuples, not invented author diversity", async () => {
    await rejected(article({ sources: article().sources.slice(0, 1) }));
    const duplicateUrl = article(); duplicateUrl.sources[1].url = duplicateUrl.sources[0].url;
    await rejected(duplicateUrl, "EDITORIAL_DUPLICATE");
    const duplicateMetadata = article();
    duplicateMetadata.sources[1] = { ...duplicateMetadata.sources[0], id: "sqlite", url: duplicateMetadata.sources[1].url };
    await rejected(duplicateMetadata, "EDITORIAL_SOURCE_METADATA_DUPLICATE");
    const oneCreator = article(); oneCreator.sources[1].creator = "Cloudflare";
    const accepted = await validateEditorialPayload(oneCreator, NOW);
    expect(accepted.ok && accepted.diagnostics.known_creator_count).toBe(1);
  });

  it("requires an explicit contextual first-party engineering exception", async () => {
    const input = article({ kind: "engineering_note", first_party_context: "A first-party note about the Base2026 implementation.", sources: [{ id: "d1", url: "https://github.com/offflinerpsy/base2026", title: "Base2026 repository", checked_at: REVIEWED }] });
    input.sections[0].blocks = [{ type: "paragraph", text: "This note describes our own implementation choices.", citation_ids: ["d1"] }];
    expect((await validateEditorialPayload(input, NOW)).ok).toBe(true);
    await rejected({ ...input, first_party_context: undefined });
    await rejected({ ...input, sources: [] });
    await rejected({ ...input, sources: [{ ...input.sources[0], url: "https://github.com/offflinerpsy/base2026-other" }] }, "EDITORIAL_FIRST_PARTY_SOURCE_REQUIRED");
    await rejected({ ...input, sources: [{ ...input.sources[0], url: "https://base2026.dev/workspace/" }] }, "EDITORIAL_FIRST_PARTY_SOURCE_REQUIRED");
    expect((await validateEditorialPayload({ ...input, sources: [{ ...input.sources[0], url: "https://base2026.dev/methodology" }] }, NOW)).ok).toBe(true);
    await rejected(article({ first_party_context: "A normal article cannot silently claim the exception." }));
  });

  it("checks citation resolution, source/section/tag uniqueness and rejects arbitrary block types", async () => {
    const unresolved = article(); unresolved.sections[0].blocks[0] = { type: "paragraph", text: "A sourced observation.", citation_ids: ["missing"] };
    await rejected(unresolved, "EDITORIAL_CITATION_UNRESOLVED");
    const duplicateCitation = article(); duplicateCitation.sections[0].blocks[0] = { type: "paragraph", text: "A sourced observation.", citation_ids: ["d1", "d1"] };
    await rejected(duplicateCitation, "EDITORIAL_DUPLICATE");
    const duplicateId = article(); duplicateId.sources[1].id = "d1"; await rejected(duplicateId, "EDITORIAL_DUPLICATE");
    const duplicateSection = article(); duplicateSection.sections.push(structuredClone(duplicateSection.sections[0])); await rejected(duplicateSection, "EDITORIAL_DUPLICATE");
    await rejected(article({ tags: ["Evidence", "evidence"] }), "EDITORIAL_DUPLICATE");
    await rejected({ ...article(), sections: [{ id: "unsafe", heading: "Unsafe", blocks: [{ type: "html", text: "An arbitrary HTML block" }] }] }, "EDITORIAL_BLOCK_TYPE_INVALID");
  });

  it("requires every bibliography source to be cited by a paragraph or list item", async () => {
    const uncited = article();
    uncited.sections[0].blocks = [{ type: "paragraph", text: "Only one source is cited in the article body.", citation_ids: ["d1"] }];
    await rejected(uncited, "EDITORIAL_SOURCE_UNCITED");
    uncited.sections[0].blocks.push({ type: "list", items: [{ text: "The other source supports this list item.", citation_ids: ["sqlite"] }] });
    expect((await validateEditorialPayload(uncited, NOW)).ok).toBe(true);
  });

  it("rejects stale review even when the payload hash matches changed content or rechecked sources", async () => {
    const changed = await packet(article({ title: "Changed content with an updated timestamp", updated_at: "2026-08-30T15:30:00.000Z" }));
    expect(await validateEditorialPacket(changed, NOW)).toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_REVIEW_STALE", field: "review.reviewed_at" }] });
    const payload = article(); payload.sources[0].checked_at = "2026-08-30T15:30:00.000Z";
    expect(await validateEditorialPacket(await packet(payload), NOW)).toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_REVIEW_STALE" }] });
    expect((await validateEditorialPacket({ ...changed, review: { ...changed.review, reviewed_at: "2026-08-30T15:30:00.000Z" } }, NOW)).ok).toBe(true);
  });

  it.each(["/blog/", "/workspace/", "/workspace/?q=private", "/session/example", "/source-policy", "//example.com/path", "https://base2026.dev/dataset", "/blog/../workspace/", "/blog/%2e%2e/", "/api?email=person", "/dataset#state", "/topics/private_notes", "/topics/call-555-123-4567"])("rejects unsafe/noncanonical related path %s", async (path) => { await rejected(article({ related_paths: [path] })); });

  it("admits only clean public related routes and keeps the two static journal paths", async () => {
    const paths = ["/blog", "/blog/tracing-evidence/", "/journal/source-backed-video-search-cloudflare/", "/journal/source-diversity-check/", "/topics/ai-visibility", "/compare/source-diversity", "/creators/tiktok-example", "/sources/tiktok-video-7999999999999999999", "/opt-out"];
    expect(paths.every(isEditorialRelatedPath)).toBe(true);
    expect((await validateEditorialPayload(article({ related_paths: paths }), NOW)).ok).toBe(true);
  });

  it.each(["https://example.com/hero.png", "/static/assets/../hero.png", "/static/assets/hero.svg", "/static/assets/hero.html", "/static/assets/hero.png?token=test", "/static/assets/%2e%2e/hero.png"])("rejects nonallowlisted hero path %s", async (path) => { await rejected(article({ hero: { ...article().hero!, path } }), "EDITORIAL_HERO_PATH_INVALID"); });

  it("requires complete hero metadata and a real boolean AI flag", async () => {
    await rejected(article({ hero: { ...article().hero!, alt: "" } }));
    await rejected({ ...article(), hero: { ...article().hero, ai_generated: "false" } });
    const noHero = article(); delete noHero.hero;
    expect((await validateEditorialPayload(noHero, NOW)).ok).toBe(true);
  });

  it("rejects credential/contact-looking identifiers and asset names without banning transcript-safety topics", async () => {
    await rejected(article({ slug: "555-123-4567" }), "EDITORIAL_PRIVACY_REJECTED");
    await rejected(article({ slug: SYNTHETIC_CREDENTIAL_FIXTURES.slug }), "EDITORIAL_PRIVACY_REJECTED");
    await rejected(article({ hero: { ...article().hero!, path: `/static/assets/${SYNTHETIC_CREDENTIAL_FIXTURES.asset}.png` } }), "EDITORIAL_PRIVACY_REJECTED");
    expect((await validateEditorialPayload(article({ slug: "keeping-raw-transcripts-private" }), NOW)).ok).toBe(true);
    expect((await validateEditorialPayload(article({ related_paths: ["/blog/keeping-raw-transcripts-private/"] }), NOW)).ok).toBe(true);
  });

  it("enforces individual, collection and total UTF-8 bounds", async () => {
    await rejected(article({ title: "x".repeat(EDITORIAL_LIMITS.title + 1) }));
    await rejected(paragraphText(article(), "x".repeat(EDITORIAL_LIMITS.paragraph + 1)));
    await rejected(article({ sections: Array.from({ length: EDITORIAL_LIMITS.sections + 1 }, (_, index) => ({ ...article().sections[0], id: `s-${index}` })) }));
    const large = article();
    large.sections = Array.from({ length: 10 }, (_, index) => ({ id: `s-${index}`, heading: "A bounded section", blocks: Array.from({ length: 12 }, () => ({ type: "paragraph" as const, text: "é".repeat(2_000), citation_ids: ["d1"] })) }));
    await rejected(large, "EDITORIAL_PAYLOAD_TOO_LARGE");
  });

  it("rejects non-JSON instances, sparse arrays, accessors and symbols without executing getters", async () => {
    await rejected(new Date());
    const sparse = article(); sparse.tags = new Array<string>(2); await rejected(sparse);
    let called = false;
    const accessor = article();
    Object.defineProperty(accessor, "title", { enumerable: true, get() { called = true; return "Hidden getter"; } });
    await rejected(accessor); expect(called).toBe(false);
    const symbol = article(); Object.defineProperty(symbol, Symbol("private"), { value: "hidden" }); await rejected(symbol);
    expect(() => parseEditorialPayload(article({ slug: "unsafe/path" }), NOW)).toThrow(EditorialValidationError);
  });
});

describe("editorial D1 durability and current-live idempotency", () => {
  it("writes only editorial tables and returns a durable exact receipt", async () => {
    const db = new SqliteD1();
    db.sqlite.prepare("INSERT INTO search_documents (id,item_id,source_id,chunk_id,body) VALUES (?,?,?,?,?)").run("existing", "existing", "existing", "existing", "Existing public evidence");
    const input = await packet();
    const result = await publishEditorialArticle(db, input, { now: NOW });
    expect(result).toMatchObject({ ok: true, status: "published", receipt: { slug: input.payload.slug, revision: 1, payload_sha256: input.review.payload_sha256, public_path: "/blog/tracing-evidence/", reviewer: "sol-max", reviewed_at: REVIEWED, recorded_at: NOW } });
    expect(db.count("editorial_articles")).toBe(1);
    expect(db.count("editorial_publication_receipts")).toBe(1);
    expect(db.count("search_documents")).toBe(1);
    expect(db.count("public_projection_receipts")).toBe(0);
    const stored = await getEditorialArticle(db, input.payload.slug, NOW);
    expect(stored?.payload).toEqual(input.payload);
    expect(stored?.payload).not.toHaveProperty("review");
    expect(await getEditorialArticle(db, "absent", NOW)).toBeNull();
  });

  it("replays the exact current tuple without mutating its timestamps or receipt", async () => {
    const db = new SqliteD1();
    const input = await packet();
    const initial = await publishEditorialArticle(db, input, { now: NOW });
    const replay = await publishEditorialArticle(db, { ...input, review: { ...input.review, reviewed_at: NOW } }, { now: "2026-08-30T16:01:00.000Z" });
    expect(replay).toMatchObject({ ok: true, status: "already_published" });
    if (initial.ok && replay.ok) expect(replay.receipt).toEqual(initial.receipt);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("returns conflict for same/lower payload revisions or higher revisions without explicit CAS", async () => {
    const db = new SqliteD1();
    const input = await packet(article({ revision: 3 }));
    await publishEditorialArticle(db, input, { now: NOW });
    for (const payload of [article({ revision: 3, title: "Conflicting content" }), article({ revision: 2 }), article({ revision: 4 })]) {
      const result = await publishEditorialArticle(db, await packet(payload), { now: NOW });
      expect(result).toMatchObject({ ok: false, status: "conflict", current_revision: 3, current_payload_sha256: input.review.payload_sha256 });
    }
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("requires an existing exact CAS tuple and cannot publish a missing article as an overwrite", async () => {
    const db = new SqliteD1();
    const input = await packet(article({ revision: 2 }));
    const result = await publishEditorialArticle(db, input, { now: NOW, overwrite: { expected_revision: 1, expected_payload_sha256: "a".repeat(64) } });
    expect(result).toMatchObject({ status: "conflict", current_revision: null });
    expect(db.count("editorial_articles")).toBe(0);
    expect(db.count("editorial_publication_receipts")).toBe(0);
  });

  it("applies a higher revision only on exact CAS, preserving original publication time and receipt history", async () => {
    const db = new SqliteD1();
    const first = await packet();
    await publishEditorialArticle(db, first, { now: NOW });
    const revised = await packet(article({ revision: 2, title: "A revised evidence note", updated_at: REVIEWED }));
    const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
    expect(await publishEditorialArticle(db, revised, { now: NOW, overwrite: { ...overwrite, expected_payload_sha256: "a".repeat(64) } })).toMatchObject({ status: "conflict" });
    expect(await publishEditorialArticle(db, revised, { now: NOW, overwrite })).toMatchObject({ ok: true, status: "published", receipt: { revision: 2, published_at: PUBLISHED } });
    expect(await publishEditorialArticle(db, revised, { now: NOW, overwrite })).toMatchObject({ status: "already_published" });
    expect(await publishEditorialArticle(db, first, { now: NOW })).toMatchObject({ status: "conflict", current_revision: 2 });
    expect(db.count("editorial_publication_receipts")).toBe(2);
    expect(db.sqlite.prepare("SELECT revision,payload_sha256 FROM editorial_publication_receipts ORDER BY revision").all()).toEqual([{ revision: 1, payload_sha256: first.review.payload_sha256 }, { revision: 2, payload_sha256: revised.review.payload_sha256 }]);
  });

  it("rejects publication-time rewrites, update-time regressions and stale publication clocks atomically", async () => {
    const db = new SqliteD1();
    const first = await packet(article({ updated_at: REVIEWED }));
    await publishEditorialArticle(db, first, { now: NOW });
    const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
    for (const candidate of [article({ revision: 2, published_at: "2026-08-28T10:00:00.000Z", updated_at: REVIEWED }), article({ revision: 2 })]) {
      expect(await publishEditorialArticle(db, await packet(candidate), { now: NOW, overwrite })).toMatchObject({ status: "conflict" });
    }
    expect(await publishEditorialArticle(db, await packet(article({ revision: 2, updated_at: REVIEWED })), { now: "2026-08-30T15:59:00.000Z", overwrite })).toMatchObject({ status: "conflict" });
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("collapses simultaneous exact requests and fences conflicting simultaneous requests", async () => {
    const db = new SqliteD1();
    const first = await packet();
    const duplicates = await Promise.all([publishEditorialArticle(db, first, { now: NOW }), publishEditorialArticle(db, first, { now: NOW })]);
    expect(duplicates.map((item) => item.status).sort()).toEqual(["already_published", "published"]);
    expect(db.count("editorial_publication_receipts")).toBe(1);
    const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
    const [second, third] = await Promise.all([packet(article({ revision: 2, title: "Second revision" })), packet(article({ revision: 3, title: "Competing revision" }))]);
    const race = await Promise.all([publishEditorialArticle(db, second, { now: NOW, overwrite }), publishEditorialArticle(db, third, { now: NOW, overwrite })]);
    expect(race.map((item) => item.status).sort()).toEqual(["conflict", "published"]);
    expect(db.count("editorial_publication_receipts")).toBe(2);
  });

  it("fences concurrent conflicting first publications at the same slug/revision", async () => {
    const db = new SqliteD1();
    const [first, other] = await Promise.all([packet(), packet(article({ title: "Another candidate at the same revision" }))]);
    const results = await Promise.all([publishEditorialArticle(db, first, { now: NOW }), publishEditorialArticle(db, other, { now: NOW })]);
    expect(results.map((item) => item.status).sort()).toEqual(["conflict", "published"]);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("rolls back the article when receipt insertion fails; a later retry is safe", async () => {
    const db = new SqliteD1();
    db.sqlite.exec("CREATE TRIGGER reject_editorial_receipt BEFORE INSERT ON editorial_publication_receipts BEGIN SELECT RAISE(ABORT, 'test receipt failure'); END;");
    const input = await packet();
    await expect(publishEditorialArticle(db, input, { now: NOW })).rejects.toMatchObject({ code: "EDITORIAL_WRITE_FAILED", message: "EDITORIAL_WRITE_FAILED" });
    expect(db.count("editorial_articles")).toBe(0);
    expect(db.count("editorial_publication_receipts")).toBe(0);
    db.sqlite.exec("DROP TRIGGER reject_editorial_receipt");
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "published" });
  });

  it("rolls back a revision update on receipt failure and preserves the previous exact article", async () => {
    const db = new SqliteD1();
    const first = await packet();
    await publishEditorialArticle(db, first, { now: NOW });
    db.sqlite.exec("CREATE TRIGGER reject_editorial_receipt BEFORE INSERT ON editorial_publication_receipts BEGIN SELECT RAISE(ABORT, 'test receipt failure'); END;");
    const candidate = await packet(article({ revision: 2 }));
    await expect(publishEditorialArticle(db, candidate, { now: NOW, overwrite: { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 } })).rejects.toBeInstanceOf(EditorialStoreError);
    expect((await getEditorialArticle(db, first.payload.slug, NOW))?.payload_sha256).toBe(first.review.payload_sha256);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("rejects malformed/hash-mismatched packets before any D1 call and uses opaque errors", async () => {
    const db = new SqliteD1();
    const input = await packet();
    input.payload.title = "An unreviewed change";
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_REVIEW_HASH_MISMATCH" }] });
    expect(db.batchCalls).toBe(0);
    const privateTitle = article({ title: "owner@example.com" });
    const result = await publishEditorialArticle(db, { ...input, payload: privateTitle }, { now: NOW });
    expect(result.status).toBe("rejected");
    expect(JSON.stringify(result)).not.toContain("owner@example.com");
    expect(JSON.stringify(result)).not.toContain("An unreviewed change");
  });

  it("holds future reviews before D1 until the publication clock catches up", async () => {
    const db = new SqliteD1();
    const input = await packet();
    input.review.reviewed_at = "2026-08-30T16:01:00.000Z";
    expect((await validateEditorialPacket(input, NOW)).ok).toBe(true);
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_REVIEW_AFTER_PUBLICATION_CLOCK" }] });
    expect(db.batchCalls).toBe(0);
    expect(await publishEditorialArticle(db, input, { now: "2026-08-30T16:01:00.000Z" })).toMatchObject({ status: "published" });
  });

  it("revalidates stored review against article update and source-check timestamps", async () => {
    const db = new SqliteD1();
    const input = await packet(article({ updated_at: REVIEWED }));
    await publishEditorialArticle(db, input, { now: NOW });
    db.sqlite.prepare("UPDATE editorial_publication_receipts SET reviewed_at=? WHERE slug=?").run("2026-08-30T14:30:00.000Z", input.payload.slug);
    await expect(getEditorialArticle(db, input.payload.slug, NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
    db.sqlite.prepare("UPDATE editorial_publication_receipts SET reviewed_at=? WHERE slug=?").run(REVIEWED, input.payload.slug);
    db.sqlite.prepare("UPDATE editorial_articles SET stored_at=? WHERE slug=?").run("2026-08-30T16:02:00.000Z", input.payload.slug);
    await expect(getEditorialArticle(db, input.payload.slug, NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
  });

  it("does not silently repair missing receipts or render tampered persisted payloads", async () => {
    const db = new SqliteD1();
    const input = await packet();
    await publishEditorialArticle(db, input, { now: NOW });
    const changed = { ...input.payload, title: "A persisted but unreviewed title" };
    db.sqlite.prepare("UPDATE editorial_articles SET payload_json=? WHERE slug=?").run(JSON.stringify(changed), input.payload.slug);
    await expect(getEditorialArticle(db, input.payload.slug, NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
    await expect(listEditorialArticles(db, { now: NOW })).rejects.toBeInstanceOf(EditorialStoreError);
    db.sqlite.prepare("DELETE FROM editorial_publication_receipts WHERE slug=?").run(input.payload.slug);
    await expect(publishEditorialArticle(db, input, { now: NOW })).rejects.toBeInstanceOf(EditorialStoreError);
    expect(db.count("editorial_publication_receipts")).toBe(0);
  });

  it("lists bounded deterministic pages with a stable publication-time/slug cursor", async () => {
    const db = new SqliteD1();
    for (const slug of ["charlie", "alpha", "bravo"]) await publishEditorialArticle(db, await packet(article({ slug })), { now: NOW });
    const first = await listEditorialArticles(db, { now: NOW, limit: 2 });
    expect(first.articles.map((item) => item.payload.slug)).toEqual(["alpha", "bravo"]);
    expect(first.next_cursor).toEqual({ published_at: PUBLISHED, slug: "bravo" });
    const second = await listEditorialArticles(db, { now: NOW, limit: 2, cursor: first.next_cursor! });
    expect(second.articles.map((item) => item.payload.slug)).toEqual(["charlie"]);
    expect(second.next_cursor).toBeNull();
    await expect(listEditorialArticles(db, { now: NOW, limit: 26 })).rejects.toBeInstanceOf(EditorialValidationError);
    await expect(listEditorialArticles(db, { now: NOW, limit: 0 })).rejects.toBeInstanceOf(EditorialValidationError);
    await expect(getEditorialArticle(db, "../private", NOW)).rejects.toBeInstanceOf(EditorialValidationError);
  });

  it("does not hide a corrupt missing kind as an empty healthy blog or sitemap", async () => {
    const db = new SqliteD1();
    await publishEditorialArticle(db, await packet(), { now: NOW });
    const row = db.sqlite.prepare("SELECT payload_json FROM editorial_articles").get();
    const payload: Record<string, unknown> = JSON.parse(String(row?.payload_json));
    delete payload.kind;
    db.sqlite.prepare("UPDATE editorial_articles SET payload_json=?").run(JSON.stringify(payload));
    await expect(listEditorialArticles(db, { now: NOW })).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
    await expect(listEditorialSitemapEntries(db, 1, NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
  });

  it("returns only validated sitemap metadata in fixed 100-entry publication/slug pages", async () => {
    const db = new SqliteD1();
    for (let index = 100; index >= 0; index -= 1) {
      await publishEditorialArticle(db, await packet(article({ slug: `entry-${String(index).padStart(3, "0")}` })), { now: NOW });
    }
    const laterDate = "2026-08-30T10:00:00.000Z";
    await publishEditorialArticle(db, await packet(article({ slug: "z-newest", published_at: laterDate, updated_at: laterDate })), { now: NOW });
    const writes = db.batchCalls;
    const first = await listEditorialSitemapEntries(db, 1, NOW);
    expect(EDITORIAL_SITEMAP_PAGE_SIZE).toBe(100);
    expect(first).toHaveLength(100);
    expect(first[0]).toEqual({ slug: "z-newest", updated_at: laterDate });
    expect(first[1]).toEqual({ slug: "entry-000", updated_at: PUBLISHED });
    expect(first.at(-1)).toEqual({ slug: "entry-098", updated_at: PUBLISHED });
    expect(await listEditorialSitemapEntries(db, 2, NOW)).toEqual([
      { slug: "entry-099", updated_at: PUBLISHED }, { slug: "entry-100", updated_at: PUBLISHED },
    ]);
    expect(await listEditorialSitemapEntries(db, 3, NOW)).toEqual([]);
    expect(await listEditorialSitemapEntries(db, 50_000, NOW)).toEqual([]);
    expect(db.batchCalls).toBe(writes);
  });

  it.each(["payload-json", "payload-hash", "missing-receipt", "receipt-tuple"])("rejects a sitemap page with %s corruption using an opaque store error", async (corruption) => {
    const db = new SqliteD1();
    const input = await packet();
    await publishEditorialArticle(db, input, { now: NOW });
    if (corruption === "payload-json") {
      const changed = await validateEditorialPayload(article({ title: "Changed stored article without renewed review" }), NOW);
      if (!changed.ok) throw new Error("invalid test fixture");
      db.sqlite.prepare("UPDATE editorial_articles SET payload_json=?").run(changed.canonical_payload_json);
    } else if (corruption === "payload-hash") {
      db.sqlite.prepare("UPDATE editorial_articles SET payload_sha256=?").run("a".repeat(64));
    } else if (corruption === "missing-receipt") {
      db.sqlite.exec("DELETE FROM editorial_publication_receipts");
    } else {
      db.sqlite.prepare("UPDATE editorial_publication_receipts SET updated_at=?").run(REVIEWED);
    }
    const error = await listEditorialSitemapEntries(db, 1, NOW).catch((value: unknown) => value);
    expect(error).toBeInstanceOf(EditorialStoreError);
    expect(error).toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID", message: "EDITORIAL_PERSISTED_STATE_INVALID" });
  });

  it.each([0, -1, 1.5, 50_001, NaN, Infinity, "1", null, true])("rejects invalid sitemap page %s before database access", async (page) => {
    const db: EditorialDatabase = {
      prepare() { throw new Error("unexpected database access"); },
      async batch() { throw new Error("unexpected database access"); },
    };
    await expect(listEditorialSitemapEntries(db, page as number, NOW)).rejects.toMatchObject({ code: "EDITORIAL_SITEMAP_PAGE_INVALID", field: "page" });
  });

  it("rejects an oversized database page without attempting to parse rows", async () => {
    const statement = {
      bind() { return statement; },
      async all() { return d1Result(Array.from({ length: 101 }, () => null)); },
    } as unknown as D1PreparedStatement;
    const db: EditorialDatabase = { prepare() { return statement; }, async batch() { throw new Error("unexpected write"); } };
    await expect(listEditorialSitemapEntries(db, 1, NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
  });

  it("conceals sitemap database errors", async () => {
    const db: EditorialDatabase = {
      prepare() { throw new Error("untrusted database detail must stay private"); },
      async batch() { throw new Error("unexpected write"); },
    };
    await expect(listEditorialSitemapEntries(db, 1, NOW)).rejects.toMatchObject({ code: "EDITORIAL_READ_FAILED", message: "EDITORIAL_READ_FAILED" });
  });

  it("verifies the conditional mutation/changes()/receipt strategy against actual local D1", async () => {
    const runtime = new Miniflare(convertV4MiniflareOptions({ modules: true, script: "export default { fetch() { return new Response('local test'); } };", compatibilityDate: "2026-08-19", d1Databases: ["DB"], cf: false }));
    try {
      const db = await runtime.getD1Database("DB");
      const statements = migration.replace(/^\s*--.*$/gmu, "").split(";").map((sql) => sql.trim()).filter(Boolean).map((sql) => db.prepare(sql));
      await db.batch(statements);
      const first = await packet();
      const results = await Promise.all([publishEditorialArticle(db, first, { now: NOW }), publishEditorialArticle(db, first, { now: NOW })]);
      expect(results.map((item) => item.status).sort()).toEqual(["already_published", "published"]);
      const second = await packet(article({ revision: 2, updated_at: REVIEWED }));
      const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
      expect(await publishEditorialArticle(db, second, { now: NOW, overwrite: { ...overwrite, expected_payload_sha256: "b".repeat(64) } })).toMatchObject({ status: "conflict" });
      expect(await db.prepare("SELECT COUNT(*) AS count FROM editorial_publication_receipts").first("count")).toBe(1);
      expect(await publishEditorialArticle(db, second, { now: NOW, overwrite })).toMatchObject({ status: "published" });
      expect(await db.prepare("SELECT COUNT(*) AS count FROM editorial_publication_receipts").first("count")).toBe(2);
      expect((await getEditorialArticle(db, first.payload.slug, NOW))?.payload.revision).toBe(2);
      await db.prepare("CREATE TRIGGER reject_editorial_receipt BEFORE INSERT ON editorial_publication_receipts BEGIN SELECT RAISE(ABORT, 'local receipt failure'); END").run();
      const third = await packet(article({ revision: 3, updated_at: REVIEWED }));
      await expect(publishEditorialArticle(db, third, { now: NOW, overwrite: { expected_revision: 2, expected_payload_sha256: second.review.payload_sha256 } })).rejects.toMatchObject({ code: "EDITORIAL_WRITE_FAILED" });
      expect((await getEditorialArticle(db, first.payload.slug, NOW))?.payload.revision).toBe(2);
      expect(await db.prepare("SELECT COUNT(*) AS count FROM editorial_publication_receipts").first("count")).toBe(2);
    } finally { await runtime.dispose(); }
  }, 30_000);
});
