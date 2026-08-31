import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";
import { afterEach, describe, expect, it } from "vitest";
import {
  EDITORIAL_EVIDENCE_GUIDE_SLUGS,
  EDITORIAL_SCHEMA,
  EditorialStoreError,
  editorialArticlePath,
  getEditorialArticle,
  inspectStoredEditorialArticle,
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
import {
  EDITORIAL_EVIDENCE_LIMITS,
  EditorialEvidenceError,
  editorialEvidenceSnapshotGuardSql,
  hashPublicEvidenceDocument,
  isPublicEvidenceDocumentId,
  isPublicEvidenceSourceId,
  resolveEditorialEvidence,
  type PublicEvidenceDocument,
} from "../src/evidence-dependencies";
import { applyPublicProjection } from "../src/public-projection";

const NOW = "2026-08-30T16:00:00.000Z";
const PUBLISHED = "2026-08-29T10:00:00.000Z";
const REVIEWED = "2026-08-30T15:00:00.000Z";
const QUOTE = "Inspect the destination page before adding a contextual internal link.";
const databases = new Set<SqliteD1>();

function sqlInput(value: unknown): SQLInputValue {
  if (value === null || typeof value === "string" || typeof value === "number"
    || typeof value === "bigint" || value instanceof Uint8Array) return value;
  throw new Error("unsupported SQLite test input");
}

function d1Result<T>(results: T[], changes = 0): D1Result<T> {
  return { success: true, results, meta: { changes, duration: 0, size_after: 0,
    rows_read: results.length, rows_written: changes, last_row_id: 0, changed_db: changes > 0 } };
}

/** Actual SQLite SQL/migrations with only the real prepared/batch D1 surface. */
class SqlitePrepared implements D1PreparedStatement {
  constructor(private readonly db: SqliteD1, private readonly sql: string, private readonly values: SQLInputValue[] = []) {}
  bind(...values: unknown[]): D1PreparedStatement { return new SqlitePrepared(this.db, this.sql, values.map(sqlInput)); }
  execute<T>(): D1Result<T> {
    const statement = this.db.sqlite.prepare(this.sql);
    if (statement.columns().length) return d1Result(statement.all(...this.values) as T[]);
    return d1Result<T>([], Number(statement.run(...this.values).changes));
  }
  first<T = unknown>(column: string): Promise<T | null>;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  async first<T>(column?: string): Promise<T | null> {
    const row = this.db.sqlite.prepare(this.sql).get(...this.values);
    return row ? (column ? row[column] : row) as T : null;
  }
  async all<T = Record<string, unknown>>(): Promise<D1Result<T>> {
    const result = this.execute<T>();
    if (this.sql.includes("AS projection_eligible")) {
      const hook = this.db.afterEvidenceRead;
      this.db.afterEvidenceRead = undefined;
      hook?.();
    }
    return result;
  }
  async run<T = Record<string, unknown>>(): Promise<D1Result<T>> { return this.execute<T>(); }
  raw<T = unknown[]>(options: { columnNames: true }): Promise<[string[], ...T[]]>;
  raw<T = unknown[]>(options?: { columnNames?: false }): Promise<T[]>;
  async raw<T>(options?: { columnNames?: boolean }): Promise<T[] | [string[], ...T[]]> {
    const statement = this.db.sqlite.prepare(this.sql);
    const rows = statement.all(...this.values).map(Object.values) as T[];
    return options?.columnNames ? [statement.columns().map((column) => column.name), ...rows] : rows;
  }
}

class SqliteD1 implements EditorialDatabase {
  readonly sqlite = new DatabaseSync(":memory:");
  readonly queries: string[] = [];
  batchCalls = 0;
  beforeBatch?: () => void;
  afterEvidenceRead?: () => void;
  constructor() {
    for (const name of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql", "0004_editorial_articles.sql"]) {
      this.sqlite.exec(readFileSync(new URL(`../migrations/${name}`, import.meta.url), "utf8"));
    }
    databases.add(this);
  }
  prepare(sql: string): D1PreparedStatement {
    this.queries.push(sql);
    return new SqlitePrepared(this, sql);
  }
  async batch<T = unknown>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]> {
    this.batchCalls += 1;
    const hook = this.beforeBatch;
    this.beforeBatch = undefined;
    hook?.();
    this.sqlite.exec("BEGIN");
    try {
      const result = statements.map((statement) => {
        if (!(statement instanceof SqlitePrepared)) throw new Error("unexpected prepared statement");
        return statement.execute<T>();
      });
      this.sqlite.exec("COMMIT");
      return result;
    } catch (error) {
      this.sqlite.exec("ROLLBACK");
      throw error;
    }
  }
  count(table: "editorial_articles" | "editorial_publication_receipts" | "search_documents" | "public_projection_cards"): number {
    return Number(this.sqlite.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count);
  }
}

afterEach(() => {
  for (const db of databases) db.sqlite.close();
  databases.clear();
});

interface TestDocument extends PublicEvidenceDocument {
  item_id: string;
  video_id: string;
  projection_id: string;
  chunk_id: string;
  chunk_index: number;
  platform: string;
  source_type: string;
  public_policy: string;
  public_surface: string;
}

function legacyDocument(index = 0, video = "7999999800000000001"): TestDocument {
  const id = `chunk-transcript-polished-${video}-${String(index).padStart(4, "0")}`;
  return {
    id, item_id: `tiktok-video-${video}`, source_id: `tiktok:synthetic_creator:${video}`,
    source_url: `https://www.tiktok.com/@synthetic_creator/video/${video}`,
    creator_handle: "@synthetic_creator", title: "A public internal-linking demonstration",
    body: `A demonstrator describes a reading path. ${QUOTE} Check context before treating the example as general advice.`,
    full_transcript_public: 0, admission_state: "normal_public_card",
    video_id: video, projection_id: "", chunk_id: id, chunk_index: index,
    platform: "tiktok", source_type: "tiktok_video", public_policy: "search_passage", public_surface: "main_search",
  };
}

function insertDocument(db: SqliteD1, row: TestDocument): TestDocument {
  const columns = Object.keys(row);
  db.sqlite.prepare(`INSERT INTO search_documents (${columns.join(",")}) VALUES (${columns.map(() => "?").join(",")})`)
    .run(...Object.values(row).map(sqlInput));
  return row;
}

function digest(value: string): string { return createHash("sha256").update(value).digest("hex"); }

function projectedDocuments(db: SqliteD1, count = 2): TestDocument[] {
  const base = legacyDocument();
  const projectionId = digest("synthetic projection").slice(0, 40);
  db.sqlite.prepare(`INSERT INTO public_projection_receipts
    (projection_id,source_id,manifest_sha256,content_sha256,private_import_receipt_sha256,card_count,status,receipt_sha256)
    VALUES (?,?,?,?,?,?,'applied',?)`)
    .run(projectionId, base.source_id, digest("manifest"), digest("content"), digest("private receipt"), count, digest("public receipt"));
  return Array.from({ length: count }, (_, ordinal) => {
    const cardId = digest(`synthetic card ${ordinal}`).slice(0, 40);
    const row = insertDocument(db, { ...base, id: digest(`synthetic search ${ordinal}`).slice(0, 40),
      projection_id: projectionId, chunk_id: cardId, chunk_index: ordinal,
      title: `Check destination context before placing an internal link, example ${ordinal}.`,
      body: `${QUOTE} The demonstrator checks one example destination, not every website.` });
    db.sqlite.prepare(`INSERT INTO public_projection_cards
      (projection_id,source_id,ordinal,card_id,search_id,claim_text,suggested_action,topic_label,evidence_excerpt,evidence_start_seconds,evidence_end_seconds)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`)
      .run(projectionId, row.source_id, ordinal, cardId, row.id, row.title,
        "Inspect a relevant destination before changing the internal link.", "Internal linking", row.body, ordinal * 5, ordinal * 5 + 4);
    return row;
  });
}

async function guide(row = legacyDocument(), quote = QUOTE): Promise<EditorialPayload> {
  return {
    schema_version: EDITORIAL_SCHEMA, kind: "evidence_guide", slug: "internal-linking", revision: 1,
    title: "Inspect a useful internal link",
    description: "A bounded reading task with an attributed public example.",
    lede: "Start by checking whether the destination helps the reader complete the task.",
    category: "Evidence guides", tags: ["Internal linking"],
    published_at: PUBLISHED, updated_at: PUBLISHED, author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: "Prepared with AI assistance and separate source review.",
    sources: [{ id: "source-one", url: `https://base2026.dev/sources/tiktok-video-${row.video_id}`,
      title: "An attributed internal-linking example", creator: row.creator_handle, checked_at: REVIEWED }],
    sections: [{ id: "inspect-context", heading: "Inspect the destination",
      blocks: [{ type: "paragraph", text: "In the cited example, the demonstrator checks destination context.", citation_ids: ["source-one"] }] }],
    related_paths: ["/topics/internal-linking", "/opt-out"],
    evidence: { user_task: "Choose a useful destination and contextual anchor for an internal link.",
      dependencies: [{ citation_id: "source-one", document_id: row.id, source_id: row.source_id,
        document_sha256: await hashPublicEvidenceDocument(row), quote, relation: "direct" }] },
  };
}

async function blog(slug = "ordinary-note"): Promise<EditorialPayload> {
  const { evidence: _unused, ...payload } = await guide();
  return { ...payload, kind: "source_based_article", slug,
    sources: [
      { id: "source-one", url: "https://developers.cloudflare.com/d1/", title: "D1 documentation", checked_at: REVIEWED },
      { id: "source-two", url: "https://www.sqlite.org/lang_transaction.html", title: "SQLite transactions", checked_at: REVIEWED },
    ],
    sections: [{ id: "read", heading: "Read the linked references",
      blocks: [{ type: "paragraph", text: "Inspect the two linked references before relying on the interpretation.", citation_ids: ["source-one", "source-two"] }] }],
  };
}

async function packet(payload: EditorialPayload): Promise<EditorialPacket> {
  const result = await validateEditorialPayload(payload, NOW);
  if (!result.ok) throw new Error(`invalid synthetic fixture: ${JSON.stringify(result.issues)}`);
  return { payload, review: { reviewer: "sol-max", outcome: "pass", reviewed_at: REVIEWED, payload_sha256: result.payload_sha256 } };
}

async function expectRejected(db: SqliteD1, payload: EditorialPayload, code: string): Promise<void> {
  const result = await publishEditorialArticle(db, await packet(payload), { now: NOW });
  expect(result).toMatchObject({ ok: false, status: "rejected", issues: [{ code }] });
  expect(db.count("editorial_articles")).toBe(0);
  expect(db.count("editorial_publication_receipts")).toBe(0);
}

describe("public evidence pin and guide payload boundary", () => {
  it("hashes exactly eight sorted fields and normalizes only the public boolean discriminator", async () => {
    const row = legacyDocument();
    const expected = {
      admission_state: row.admission_state, body: row.body, creator_handle: row.creator_handle,
      full_transcript_public: false, id: row.id, source_id: row.source_id, source_url: row.source_url, title: row.title,
    };
    const hash = await hashPublicEvidenceDocument(row);
    expect(hash).toBe(digest(JSON.stringify(expected)));
    expect(await hashPublicEvidenceDocument({ ...row, full_transcript_public: false })).toBe(hash);
    expect(await hashPublicEvidenceDocument({ ...row, full_transcript_public: true }))
      .toBe(await hashPublicEvidenceDocument({ ...row, full_transcript_public: 1 }));
    expect(await hashPublicEvidenceDocument({ ...row, full_transcript_public: true })).not.toBe(hash);
    const reordered = Object.fromEntries(Object.entries(row).reverse()) as TestDocument;
    expect(await hashPublicEvidenceDocument(reordered)).toBe(hash);
    const metadataOnly = { ...row, projection_id: "different metadata" };
    expect(await hashPublicEvidenceDocument(metadataOnly)).toBe(hash);
    for (const key of ["id", "source_id", "source_url", "creator_handle", "title", "body", "admission_state"] as const) {
      expect(await hashPublicEvidenceDocument({ ...row, [key]: row[key] + " " })).not.toBe(hash);
    }
    expect(await hashPublicEvidenceDocument({ ...row, body: "é" }))
      .not.toBe(await hashPublicEvidenceDocument({ ...row, body: "e\u0301" }));
  });

  it.each([null, undefined, 2, -1, "false", "0"])("rejects non-boolean/non-SQL-boolean flag %s", async (flag) => {
    const row = { ...legacyDocument(), full_transcript_public: flag } as PublicEvidenceDocument;
    await expect(hashPublicEvidenceDocument(row)).rejects.toMatchObject({ code: "EDITORIAL_EVIDENCE_DOCUMENT_INVALID" });
  });

  it("accepts only observed chunk/card IDs and exact source identities, not generic slugs or routes", () => {
    for (const id of [legacyDocument().id, legacyDocument().id.replace("-polished", ""), "a".repeat(40)]) expect(isPublicEvidenceDocumentId(id)).toBe(true);
    for (const id of ["chunk-1", "../private", "a".repeat(64), "chunk-transcript-123-0000", legacyDocument().id + "?q=x", legacyDocument().id.toUpperCase()]) expect(isPublicEvidenceDocumentId(id)).toBe(false);
    expect(isPublicEvidenceSourceId(legacyDocument().source_id)).toBe(true);
    for (const id of ["tiktok-video-7999999800000000001", "tiktok:@synthetic_creator:7999999800000000001", "tiktok:synthetic_creator:123", "youtube:example:7999999800000000001"]) expect(isPublicEvidenceSourceId(id)).toBe(false);
  });

  it("registers only the five existing task canonicals while retaining old article paths and one-source diagnostics", async () => {
    const payload = await guide();
    const result = await validateEditorialPayload(payload, NOW);
    expect(result).toMatchObject({ ok: true, diagnostics: { source_count: 1, known_creator_count: 1 } });
    expect(EDITORIAL_EVIDENCE_GUIDE_SLUGS).toEqual([
      "internal-linking", "search-console-low-hanging-fruit", "content-freshness", "schema-ai-citations", "llms-txt-risk",
    ]);
    expect(Object.isFrozen(EDITORIAL_EVIDENCE_GUIDE_SLUGS)).toBe(true);
    expect(editorialArticlePath(payload.slug, payload.kind)).toBe("/topics/internal-linking");
    expect(editorialArticlePath("ordinary-note")).toBe("/blog/ordinary-note/");
    expect(editorialArticlePath("ordinary-note", "engineering_note")).toBe("/blog/ordinary-note/");
    for (const slug of EDITORIAL_EVIDENCE_GUIDE_SLUGS) {
      expect(editorialArticlePath(slug, "evidence_guide")).toBe(`/topics/${slug}`);
      expect((await validateEditorialPayload({ ...payload, slug }, NOW)).ok).toBe(true);
      expect(() => editorialArticlePath(slug)).toThrow();
      for (const kind of ["source_based_article", "engineering_note"]) {
        expect(await validateEditorialPayload({ ...await blog(), slug, kind }, NOW))
          .toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_SLUG_RESERVED" }] });
      }
    }
    for (const slug of ["not-a-registered-topic", "service-page-seo", "technical-seo-indexing", "review-strategy", "ai-visibility"]) {
      expect(() => editorialArticlePath(slug, "evidence_guide")).toThrow();
      expect((await validateEditorialPayload({ ...payload, slug }, NOW)).ok).toBe(false);
    }
    expect(result).not.toHaveProperty("independent_sources");
    expect(result).not.toHaveProperty("fact_checked");
  });

  it("requires evidence only for guides and rejects all unsupported evidence/dependency fields", async () => {
    const payload = await guide();
    const { evidence: _unused, ...missing } = payload;
    expect(await validateEditorialPayload(missing, NOW)).toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_EVIDENCE_REQUIRED" }] });
    expect(await validateEditorialPayload({ ...await blog(), evidence: payload.evidence }, NOW))
      .toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_EVIDENCE_NOT_ALLOWED" }] });
    expect((await validateEditorialPayload({ ...payload, first_party_context: "An unrelated exception." }, NOW)).ok).toBe(false);
    for (const extra of [
      { ...payload.evidence, approval: "automatic" },
      { ...payload.evidence, dependencies: [{ ...payload.evidence!.dependencies[0], projection_id: "not public packet metadata" }] },
      { ...payload.evidence, dependencies: [{ ...payload.evidence!.dependencies[0], arbitrary: "field" }] },
    ]) expect(await validateEditorialPayload({ ...payload, evidence: extra }, NOW)).toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_UNSUPPORTED_FIELDS" }] });
  });

  it("binds quote, dependency hash and user task into the separate exact review", async () => {
    const original = await packet(await guide());
    const changes = [structuredClone(original.payload), structuredClone(original.payload), structuredClone(original.payload)];
    changes[0].evidence!.dependencies[0].quote = "Check context";
    changes[1].evidence!.dependencies[0].document_sha256 = "b".repeat(64);
    changes[2].evidence!.user_task = "Inspect a different task.";
    for (const payload of changes) expect(await validateEditorialPacket({ payload, review: original.review }, NOW))
      .toMatchObject({ ok: false, issues: [{ code: "EDITORIAL_REVIEW_HASH_MISMATCH" }] });
    expect((await validateEditorialPacket({ payload: original.payload }, NOW)).ok).toBe(false);
  });

  it("bounds user task, quotes and dependency cardinality and requires resolvable used citations and a direct relation", async () => {
    const payload = await guide();
    const dependency = payload.evidence!.dependencies[0];
    for (const evidence of [
      { ...payload.evidence, user_task: "x".repeat(401) },
      { ...payload.evidence, dependencies: [] },
      { ...payload.evidence, dependencies: Array.from({ length: 13 }, () => dependency) },
      { ...payload.evidence, dependencies: [dependency, dependency] },
      { ...payload.evidence, dependencies: [{ ...dependency, quote: "" }] },
      { ...payload.evidence, dependencies: [{ ...dependency, quote: "x".repeat(321) }] },
      { ...payload.evidence, dependencies: [{ ...dependency, citation_id: "missing" }] },
      { ...payload.evidence, dependencies: [{ ...dependency, relation: "consensus" }] },
      { ...payload.evidence, dependencies: [{ ...dependency, relation: "prerequisite" }] },
      { ...payload.evidence, dependencies: [{ ...dependency, document_id: "ordinary-slug" }] },
      { ...payload.evidence, dependencies: [{ ...dependency, source_id: "tiktok-video-7999999800000000001" }] },
    ]) expect((await validateEditorialPayload({ ...payload, evidence }, NOW)).ok).toBe(false);
    const uncited = structuredClone(payload);
    uncited.sections[0].blocks = [{ type: "paragraph", text: "No source is referenced here.", citation_ids: [] }];
    expect((await validateEditorialPayload(uncited, NOW)).ok).toBe(false);
  });

  it.each(["quote", "user_task"])("reuses existing privacy and HTML checks for %s without overblocking ordinary prose", async (field) => {
    const payload = await guide();
    for (const value of ["<script>unsafe</script>", ["private", "notes"].join("_") + ": synthetic", "reader@example.com", "/Users/synthetic/private.txt"]) {
      const changed = structuredClone(payload);
      if (field === "quote") changed.evidence!.dependencies[0].quote = value;
      else changed.evidence!.user_task = value;
      const result = await validateEditorialPayload(changed, NOW);
      expect(result.ok).toBe(false);
      expect(JSON.stringify(result)).not.toContain(value);
    }
    payload.evidence!.user_task = "Keep raw transcripts private while reviewing contextual internal links.";
    expect((await validateEditorialPayload(payload, NOW)).ok).toBe(true);
  });

  it("rejects accessors in evidence without invoking them", async () => {
    const payload = await guide();
    let called = false;
    Object.defineProperty(payload.evidence!.dependencies[0], "quote", { enumerable: true, get() { called = true; return QUOTE; } });
    expect((await validateEditorialPayload(payload, NOW)).ok).toBe(false);
    expect(called).toBe(false);
  });
});

describe("guide dependency admission against migrations 0001–0004", () => {
  it("publishes a separately reviewed legacy guide with quote/hash only and no source mutation", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const input = await packet(await guide(row));
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({
      ok: true, status: "published", receipt: { public_path: "/topics/internal-linking", payload_sha256: input.review.payload_sha256 },
    });
    const stored = await getEditorialArticle(db, "internal-linking", NOW);
    expect(stored?.payload).toEqual(input.payload);
    expect(stored?.receipt.public_path).toBe("/topics/internal-linking");
    expect(db.count("search_documents")).toBe(1);
    expect(db.count("public_projection_cards")).toBe(0);
    const json = String(db.sqlite.prepare("SELECT payload_json FROM editorial_articles").get()?.payload_json);
    expect(json).toContain(QUOTE);
    expect(json).not.toContain(row.body);
    expect(json).not.toContain("expected_json");
    expect(json).not.toContain("projection_id");
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "already_published" });
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("accepts the exact original source URL as a citation and both observed chunk ID forms", async () => {
    const db = new SqliteD1();
    const row = legacyDocument();
    row.id = row.id.replace("-polished", "");
    row.chunk_id = row.id;
    insertDocument(db, row);
    const payload = await guide(row);
    payload.sources[0].url = row.source_url;
    expect(await publishEditorialArticle(db, await packet(payload), { now: NOW })).toMatchObject({ status: "published" });
  });

  it("admits a valid projected dependency only with a whole eligible cohort", async () => {
    const db = new SqliteD1();
    const rows = projectedDocuments(db);
    const input = await packet(await guide(rows[0]));
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "published" });
    expect((await getEditorialArticle(db, input.payload.slug, NOW))?.payload_sha256).toBe(input.review.payload_sha256);
    expect(db.count("search_documents")).toBe(2);
    expect(db.count("public_projection_cards")).toBe(2);
  });

  it("documents the observed semantic negative fixture without pretending structural pins reject its meaning", async () => {
    const db = new SqliteD1();
    // Observed bad title/span pairing on public source 7402026836600851717.
    // The original video is not declared false. A real semantic review must
    // HOLD this unsupported pairing; a matching substring cannot approve it.
    const row = legacyDocument();
    row.title = "Jab, jab, jab, right hook is a book about social media marketing.";
    row.body = "[2.980s-5.340s] I posted for six months on social media. [5.460s-5.660s] Yes?";
    insertDocument(db, row);
    const payload = await guide(row, "I posted for six months on social media.");
    payload.sections[0].blocks = [{ type: "paragraph", text: row.title, citation_ids: ["source-one"] }];
    expect((await validateEditorialPayload(payload, NOW)).ok).toBe(true);
    expect((await validateEditorialPacket({ payload }, NOW)).ok).toBe(false);
    // No test-generated Sol approval and no publication of this negative pair.
    expect(await resolveEditorialEvidence(db, payload.evidence!, payload.sources, () => {})).toHaveProperty("expected_json");
    expect(db.count("editorial_articles")).toBe(0);
  });

  it("rejects mismatched quote/hash/source/citation before any publication batch", async () => {
    for (const failure of ["quote", "hash", "source", "citation"] as const) {
      const db = new SqliteD1();
      const row = insertDocument(db, legacyDocument());
      const payload = await guide(row);
      const expected = {
        quote: "EDITORIAL_EVIDENCE_QUOTE_MISMATCH", hash: "EDITORIAL_EVIDENCE_HASH_MISMATCH",
        source: "EDITORIAL_EVIDENCE_SOURCE_MISMATCH", citation: "EDITORIAL_EVIDENCE_SOURCE_MISMATCH",
      };
      if (failure === "quote") payload.evidence!.dependencies[0].quote = "A statement absent from the public document.";
      if (failure === "hash") payload.evidence!.dependencies[0].document_sha256 = "a".repeat(64);
      if (failure === "source") payload.evidence!.dependencies[0].source_id = "tiktok:another_creator:7999999800000000001";
      if (failure === "citation") payload.sources[0].url = "https://base2026.dev/sources/tiktok-video-7999999800000000002";
      await expectRejected(db, payload, expected[failure]);
      expect(db.batchCalls).toBe(0);
    }
  });

  it.each([
    ["missing", "DELETE FROM search_documents", "EDITORIAL_EVIDENCE_DOCUMENT_MISSING"],
    ["full flag", "UPDATE search_documents SET full_transcript_public=1", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["admission", "UPDATE search_documents SET admission_state='held'", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["policy", "UPDATE search_documents SET public_policy='held'", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["surface", "UPDATE search_documents SET public_surface='private'", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["platform", "UPDATE search_documents SET platform='other'", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["source type", "UPDATE search_documents SET source_type='other'", "EDITORIAL_EVIDENCE_NOT_PUBLIC"],
    ["video", "UPDATE search_documents SET video_id='7999999800000000002'", "EDITORIAL_EVIDENCE_SOURCE_MISMATCH"],
    ["source URL", "UPDATE search_documents SET source_url='https://www.tiktok.com/@other/video/7999999800000000001'", "EDITORIAL_EVIDENCE_SOURCE_MISMATCH"],
    ["chunk identity", "UPDATE search_documents SET chunk_index=1", "EDITORIAL_EVIDENCE_DOCUMENT_INVALID"],
  ])("rejects a legacy dependency after %s change", async (_name, sql, code) => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const payload = await guide(row);
    db.sqlite.exec(sql);
    await expectRejected(db, payload, code);
    expect(db.batchCalls).toBe(0);
  });

  it.each([
    ["missing receipt", "DELETE FROM public_projection_receipts"],
    ["rolled-back receipt", "UPDATE public_projection_receipts SET status='rolled_back'"],
    ["partial cards", "DELETE FROM public_projection_cards WHERE ordinal=1"],
    ["partial documents", "DELETE FROM search_documents WHERE chunk_index=1"],
    ["wrong sibling source", "UPDATE search_documents SET source_id='tiktok:other:7999999800000000001' WHERE chunk_index=1"],
    ["wrong sibling projection", "UPDATE search_documents SET projection_id='' WHERE chunk_index=1"],
    ["wrong card source", "UPDATE public_projection_cards SET source_id='tiktok:other:7999999800000000001' WHERE ordinal=1"],
    ["drifted sibling title", "UPDATE search_documents SET title='Another sufficiently long title.' WHERE chunk_index=1"],
    ["drifted sibling body", "UPDATE search_documents SET body='An entirely different supporting excerpt.' WHERE chunk_index=1"],
    ["unsafe sibling", "UPDATE search_documents SET full_transcript_public=1 WHERE chunk_index=1"],
    ["hidden sibling", "UPDATE search_documents SET public_surface='private' WHERE chunk_index=1"],
    ["missing time range", "UPDATE public_projection_cards SET evidence_end_seconds=evidence_start_seconds WHERE ordinal=1"],
    ["bad receipt digest", "UPDATE public_projection_receipts SET receipt_sha256='invalid'"],
    ["fake legacy demotion", "DELETE FROM public_projection_cards; DELETE FROM public_projection_receipts; UPDATE search_documents SET projection_id=''"],
  ])("rejects the whole projected cohort for %s, including uncited siblings", async (_name, sql) => {
    const db = new SqliteD1();
    const rows = projectedDocuments(db);
    const payload = await guide(rows[0]);
    db.sqlite.exec(sql);
    await expectRejected(db, payload, "EDITORIAL_EVIDENCE_PROJECTION_INVALID");
    expect(db.batchCalls).toBe(0);
  });

  it("rejects extra projected documents/cards rather than accepting a surviving joined subset", async () => {
    for (const extra of ["document", "card"]) {
      const db = new SqliteD1();
      const rows = projectedDocuments(db);
      const payload = await guide(rows[0]);
      if (extra === "document") insertDocument(db, { ...rows[0], id: digest("extra search").slice(0, 40), chunk_index: 2 });
      else db.sqlite.prepare(`INSERT INTO public_projection_cards
        (projection_id,source_id,ordinal,card_id,search_id,claim_text,suggested_action,topic_label,evidence_excerpt,evidence_start_seconds,evidence_end_seconds)
        SELECT projection_id,source_id,2,?,?,claim_text,suggested_action,topic_label,evidence_excerpt,10,14
        FROM public_projection_cards WHERE ordinal=0`).run(digest("extra card").slice(0, 40), digest("extra search").slice(0, 40));
      await expectRejected(db, payload, "EDITORIAL_EVIDENCE_PROJECTION_INVALID");
    }
  });

  it("rejects private document material even when an unchanged quote and a new pin are supplied", async () => {
    const db = new SqliteD1();
    const row = legacyDocument();
    row.body += " " + ["private", "notes"].join("_") + ": synthetic marker";
    insertDocument(db, row);
    const payload = await guide(row);
    const result = await publishEditorialArticle(db, await packet(payload), { now: NOW });
    expect(result).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_EVIDENCE_PRIVACY_REJECTED" }] });
    expect(JSON.stringify(result)).not.toContain("synthetic marker");
    expect(db.batchCalls).toBe(0);
  });

  it("reads at most twelve exact-ID rows and caps a body before it crosses the binding", async () => {
    const db = new SqliteD1();
    const rows = Array.from({ length: 12 }, (_, index) => insertDocument(db, legacyDocument(index)));
    const payload = await guide(rows[0]);
    payload.evidence!.dependencies = await Promise.all(rows.map(async (row, index) => ({
      citation_id: "source-one", document_id: row.id, source_id: row.source_id,
      document_sha256: await hashPublicEvidenceDocument(row), quote: QUOTE, relation: index ? "prerequisite" as const : "direct" as const,
    })));
    const input = await packet(payload);
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "published" });
    const readQuery = db.queries.find((sql) => sql.includes("AS projection_eligible"))!;
    expect(readQuery).toContain("WHERE d.id IN (SELECT value FROM json_each(?1))");
    expect(readQuery).toContain("LIMIT 12");
    expect(readQuery).toContain("length(CAST(d.body AS BLOB))<=65536");
    db.sqlite.prepare("UPDATE search_documents SET body=? WHERE id=?").run("x".repeat(EDITORIAL_EVIDENCE_LIMITS.document_body_bytes + 1), rows[0].id);
    await expect(getEditorialArticle(db, "internal-linking", NOW)).rejects.toBeInstanceOf(EditorialStoreError);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("caps the serialized snapshot before binding highly escaped document bodies", async () => {
    const db = new SqliteD1();
    const rows = Array.from({ length: 12 }, (_, index) => {
      const row = legacyDocument(index);
      row.body = QUOTE + "\\".repeat(EDITORIAL_EVIDENCE_LIMITS.document_body_bytes - QUOTE.length);
      return insertDocument(db, row);
    });
    const payload = await guide(rows[0]);
    payload.evidence!.dependencies = await Promise.all(rows.map(async (row) => ({
      citation_id: "source-one", document_id: row.id, source_id: row.source_id,
      document_sha256: await hashPublicEvidenceDocument(row), quote: QUOTE, relation: "direct" as const,
    })));
    await expectRejected(db, payload, "EDITORIAL_EVIDENCE_TOO_LARGE");
    expect(db.batchCalls).toBe(0);
  });
});

describe("guide atomic publication, drift reads and repair", () => {
  it.each([
    ["body", "UPDATE search_documents SET body=body||' A changed context.'"],
    ["title", "UPDATE search_documents SET title=title||' Changed.'"],
    ["policy", "UPDATE search_documents SET public_policy='held'"],
    ["surface", "UPDATE search_documents SET public_surface='private'"],
    ["admission", "UPDATE search_documents SET admission_state='held'"],
    ["full flag", "UPDATE search_documents SET full_transcript_public=1"],
    ["removal", "DELETE FROM search_documents"],
  ])("blocks a %s race after hashing and before INSERT without issuing a receipt", async (_name, sql) => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const payload = await guide(row);
    db.beforeBatch = () => { db.sqlite.exec(sql); };
    await expectRejected(db, payload, "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED");
    expect(db.batchCalls).toBe(1);
  });

  it("blocks projection withdrawal after snapshot read in the same conditional transaction", async () => {
    const db = new SqliteD1();
    const rows = projectedDocuments(db);
    const payload = await guide(rows[0]);
    db.beforeBatch = () => { db.sqlite.exec("UPDATE public_projection_receipts SET status='rolled_back'"); };
    await expectRejected(db, payload, "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED");
  });

  it("does not call an exact stale replay healthy, before or during its transaction", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const input = await packet(await guide(row));
    await publishEditorialArticle(db, input, { now: NOW });
    db.beforeBatch = () => { db.sqlite.exec("UPDATE search_documents SET body=body||' Changed context.'"); };
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED" }] });
    const batches = db.batchCalls;
    expect(await publishEditorialArticle(db, input, { now: NOW })).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_EVIDENCE_HASH_MISMATCH" }] });
    expect(db.batchCalls).toBe(batches);
    expect(db.count("editorial_articles")).toBe(1);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it.each([
    ["body", "UPDATE search_documents SET body=body||' Changed context.'"],
    ["policy", "UPDATE search_documents SET public_policy='held'"],
    ["surface", "UPDATE search_documents SET public_surface='private'"],
  ])("fails closed on stored %s drift while preserving authorized repair inspection", async (_name, sql) => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const input = await packet(await guide(row));
    await publishEditorialArticle(db, input, { now: NOW });
    db.sqlite.exec(sql);
    await expect(getEditorialArticle(db, "internal-linking", NOW)).rejects.toBeInstanceOf(EditorialStoreError);
    expect((await inspectStoredEditorialArticle(db, "internal-linking", NOW))?.payload_sha256).toBe(input.review.payload_sha256);
  });

  it("fences a withdrawal during asynchronous read validation and rechecks current receipts", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const input = await packet(await guide(row));
    await publishEditorialArticle(db, input, { now: NOW });
    db.afterEvidenceRead = () => { db.sqlite.exec("UPDATE search_documents SET public_surface='private'"); };
    await expect(getEditorialArticle(db, "internal-linking", NOW)).rejects.toMatchObject({ code: "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED" });
    db.sqlite.exec("UPDATE search_documents SET public_surface='main_search'");
    db.afterEvidenceRead = () => { db.sqlite.exec("DELETE FROM editorial_publication_receipts"); };
    await expect(getEditorialArticle(db, "internal-linking", NOW)).rejects.toMatchObject({ code: "EDITORIAL_PERSISTED_STATE_INVALID" });
  });

  it("repairs changed dependencies only through a new reviewed revision and explicit previous CAS", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const first = await packet(await guide(row));
    await publishEditorialArticle(db, first, { now: NOW });
    const changed = { ...row, body: row.body + " The example has been corrected." };
    db.sqlite.prepare("UPDATE search_documents SET body=? WHERE id=?").run(changed.body, row.id);
    const second = await packet({ ...await guide(changed), revision: 2, updated_at: REVIEWED });
    const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
    expect(await publishEditorialArticle(db, second, { now: NOW })).toMatchObject({ status: "conflict" });
    expect(await publishEditorialArticle(db, second, { now: NOW, overwrite })).toMatchObject({
      status: "published", receipt: { revision: 2, published_at: PUBLISHED, public_path: "/topics/internal-linking" },
    });
    expect(await publishEditorialArticle(db, second, { now: NOW, overwrite })).toMatchObject({ status: "already_published" });
    expect((await getEditorialArticle(db, "internal-linking", NOW))?.payload.revision).toBe(2);
    expect(db.count("editorial_publication_receipts")).toBe(2);
  });

  it("fences competing guide revisions and rolls back a guide on receipt insertion failure", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const first = await packet(await guide(row));
    await publishEditorialArticle(db, first, { now: NOW });
    const second = await packet({ ...first.payload, revision: 2, title: "A second reviewed task" });
    const third = await packet({ ...first.payload, revision: 3, title: "A competing reviewed task" });
    const overwrite = { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 };
    const results = await Promise.all([publishEditorialArticle(db, second, { now: NOW, overwrite }), publishEditorialArticle(db, third, { now: NOW, overwrite })]);
    expect(results.map((result) => result.status).sort()).toEqual(["conflict", "published"]);
    expect(db.count("editorial_publication_receipts")).toBe(2);
    const current = await inspectStoredEditorialArticle(db, "internal-linking", NOW);
    db.sqlite.exec("CREATE TRIGGER fail_editorial_receipt BEFORE INSERT ON editorial_publication_receipts BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END");
    const next = await packet({ ...first.payload, revision: 4 });
    await expect(publishEditorialArticle(db, next, { now: NOW, overwrite: {
      expected_revision: current!.payload.revision, expected_payload_sha256: current!.payload_sha256,
    } })).rejects.toMatchObject({ code: "EDITORIAL_WRITE_FAILED" });
    expect(db.count("editorial_publication_receipts")).toBe(2);
    expect((await inspectStoredEditorialArticle(db, "internal-linking", NOW))?.payload_sha256).toBe(current?.payload_sha256);
  });

  it.each(["guide-to-blog", "blog-to-guide"])("rejects %s canonical-family changes even with exact CAS", async (direction) => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const firstPayload = direction === "guide-to-blog" ? await guide(row) : await blog("ordinary-note");
    const nextPayload = direction === "guide-to-blog" ? await blog("internal-linking")
      : { ...await guide(row), slug: "ordinary-note" };
    const first = await packet(firstPayload);
    await publishEditorialArticle(db, first, { now: NOW });
    const second = { payload: { ...nextPayload, revision: 2 }, review: first.review };
    expect(await publishEditorialArticle(db, second, { now: NOW, overwrite: { expected_revision: 1, expected_payload_sha256: first.review.payload_sha256 } }))
      .toMatchObject({ status: "rejected", issues: [{ code: direction === "guide-to-blog" ? "EDITORIAL_SLUG_RESERVED" : "EDITORIAL_EVIDENCE_GUIDE_SLUG_INVALID" }] });
    expect((await inspectStoredEditorialArticle(db, firstPayload.slug, NOW))?.payload.kind).toBe(firstPayload.kind);
    expect(db.count("editorial_publication_receipts")).toBe(1);
  });

  it("excludes guides before blog keyset and fixed sitemap pagination, including stale guides", async () => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const newer = "2026-08-30T10:00:00.000Z";
    await publishEditorialArticle(db, await packet({ ...await guide(row), published_at: newer, updated_at: newer }), { now: NOW });
    for (let index = 0; index <= 100; index += 1) {
      await publishEditorialArticle(db, await packet(await blog(`blog-${String(index).padStart(3, "0")}`)), { now: NOW });
    }
    db.sqlite.exec("DELETE FROM search_documents");
    const first = await listEditorialArticles(db, { now: NOW, limit: 1 });
    expect(first.articles.map((item) => item.payload.slug)).toEqual(["blog-000"]);
    const second = await listEditorialArticles(db, { now: NOW, limit: 1, cursor: first.next_cursor! });
    expect(second.articles.map((item) => item.payload.slug)).toEqual(["blog-001"]);
    const sitemap = await listEditorialSitemapEntries(db, 1, NOW);
    expect(sitemap).toHaveLength(100);
    expect(sitemap[0].slug).toBe("blog-000");
    expect(sitemap.at(-1)?.slug).toBe("blog-099");
    expect(await listEditorialSitemapEntries(db, 2, NOW)).toEqual([{ slug: "blog-100", updated_at: PUBLISHED }]);
    expect(await listEditorialSitemapEntries(db, 3, NOW)).toEqual([]);
  });

  it.each(["search_documents", "public_projection_cards", "public_projection_receipts"])("conceals missing %s schema errors before writing", async (table) => {
    const db = new SqliteD1();
    const row = insertDocument(db, legacyDocument());
    const input = await packet(await guide(row));
    db.sqlite.exec(`DROP TABLE ${table}`);
    await expect(publishEditorialArticle(db, input, { now: NOW })).rejects.toMatchObject({
      code: "EDITORIAL_EVIDENCE_READ_FAILED", message: "EDITORIAL_EVIDENCE_READ_FAILED",
    });
    expect(db.count("editorial_articles")).toBe(0);
    expect(db.batchCalls).toBe(0);
  });

  it("validates pure payloads without a database and refuses invalid SQL binding indexes", async () => {
    expect(parseEditorialPayload(await guide(), NOW).kind).toBe("evidence_guide");
    for (const index of [0, -1, 101, 1.5, NaN]) expect(() => editorialEvidenceSnapshotGuardSql(index)).toThrow(EditorialEvidenceError);
  });

  it.each(["legacy", "projected"])("stays within real D1 depth 100 with twelve %s pins through publish/get/replay/CAS", async (lane) => {
    const runtime = new Miniflare(convertV4MiniflareOptions({
      modules: true, script: "export default { fetch() { return new Response('local test'); } };",
      compatibilityDate: "2026-08-19", d1Databases: ["DB"], cf: false,
    }));
    try {
      const db = await runtime.getD1Database("DB");
      const statements: D1PreparedStatement[] = [];
      // Split only the four known migration files, preserving trigger bodies.
      // This is test setup, not a general SQL/transaction API in production.
      for (const name of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql", "0004_editorial_articles.sql"]) {
        const migration = readFileSync(new URL(`../migrations/${name}`, import.meta.url), "utf8").replace(/^\s*--.*$/gmu, "");
        let pending = "";
        let trigger = false;
        for (const line of migration.split("\n")) {
          pending += line + "\n";
          if (/^\s*CREATE TRIGGER\b/u.test(line)) trigger = true;
          if ((trigger ? /^\s*END;\s*$/u : /;\s*$/u).test(line)) {
            statements.push(db.prepare(pending.trim()));
            pending = "";
            trigger = false;
          }
        }
        if (pending.trim()) throw new Error("unexpected migration remainder");
      }
      await db.batch(statements);
      if (lane === "legacy") {
        const documents = Array.from({ length: 12 }, (_, index) => legacyDocument(index));
        await db.batch(documents.map((row) => {
          const columns = Object.keys(row);
          return db.prepare(`INSERT INTO search_documents (${columns.join(",")}) VALUES (${columns.map(() => "?").join(",")})`)
            .bind(...Object.values(row));
        }));
      } else {
        for (let cohort = 0; cohort < 4; cohort += 1) {
          const source = legacyDocument(0, (7999999800000000001n + BigInt(cohort)).toString());
          await applyPublicProjection(db, {
            schema_version: "base2026.public-projection.v1", projection_id: digest(`local D1 projection ${cohort}`).slice(0, 40),
            source: { source_id: source.source_id, canonical_url: source.source_url, creator_handle: source.creator_handle,
              published_at: "2026-08-29", title_or_description: source.title, duration_seconds: 30 },
            manifest_sha256: digest(`local manifest ${cohort}`), content_sha256: digest(`local content ${cohort}`),
            private_import_receipt_sha256: digest(`local private receipt ${cohort}`),
            cards: Array.from({ length: 3 }, (_, ordinal) => ({
              ordinal, claim_text: source.title + `, example ${ordinal}.`,
              suggested_action: "Inspect the destination and its surrounding context.", topic_label: "Internal linking",
              evidence_excerpt: source.body, evidence_start_seconds: ordinal * 5 + 1, evidence_end_seconds: ordinal * 5 + 4,
            })),
          });
        }
      }
      const rows: TestDocument[] = (await db.prepare("SELECT * FROM search_documents ORDER BY source_id,chunk_index LIMIT 12").all<TestDocument>()).results;
      expect(rows).toHaveLength(12);
      const sources = [...new Map(rows.map((row) => [row.source_id, row])).values()];
      const citationIds = new Map(sources.map((source, index) => [source.source_id, `source-${index}`]));
      const payload = await guide(rows[0]);
      payload.sources = sources.map((source) => ({ id: citationIds.get(source.source_id)!,
        url: `https://base2026.dev/sources/tiktok-video-${source.video_id}`,
        title: "A synthetic local D1 example", creator: source.creator_handle, checked_at: REVIEWED }));
      payload.sections[0].blocks = [{ type: "paragraph", text: "Check these attributed examples before using the task guide.",
        citation_ids: payload.sources.map((source) => source.id) }];
      payload.evidence!.dependencies = await Promise.all(rows.map(async (row, index) => ({
        citation_id: citationIds.get(row.source_id)!, document_id: row.id, source_id: row.source_id,
        document_sha256: await hashPublicEvidenceDocument(row), quote: QUOTE,
        relation: index ? "prerequisite" as const : "direct" as const,
      })));
      const first = await packet(payload);
      expect(await publishEditorialArticle(db, first, { now: NOW })).toMatchObject({ status: "published" });
      expect((await getEditorialArticle(db, first.payload.slug, NOW))?.payload_sha256).toBe(first.review.payload_sha256);
      expect(await publishEditorialArticle(db, first, { now: NOW })).toMatchObject({ status: "already_published" });
      const second = await packet({ ...first.payload, revision: 2, updated_at: REVIEWED });
      expect(await publishEditorialArticle(db, second, { now: NOW, overwrite: {
        expected_revision: 1, expected_payload_sha256: first.review.payload_sha256,
      } })).toMatchObject({ status: "published", receipt: { revision: 2 } });
      expect((await getEditorialArticle(db, second.payload.slug, NOW))?.payload_sha256).toBe(second.review.payload_sha256);
      expect(await publishEditorialArticle(db, second, { now: NOW })).toMatchObject({ status: "already_published" });
      const racing: EditorialDatabase = {
        prepare(sql) { return db.prepare(sql); },
        async batch<T = unknown>(prepared: D1PreparedStatement[]): Promise<D1Result<T>[]> {
          await db.prepare("UPDATE search_documents SET public_policy='held' WHERE id=?1").bind(rows[0].id).run();
          return db.batch<T>(prepared);
        },
      };
      const third = await packet({ ...second.payload, revision: 3 });
      expect(await publishEditorialArticle(racing, third, { now: NOW, overwrite: {
        expected_revision: 2, expected_payload_sha256: second.review.payload_sha256,
      } })).toMatchObject({ status: "rejected", issues: [{ code: "EDITORIAL_EVIDENCE_SNAPSHOT_CHANGED" }] });
      expect(await db.prepare("SELECT COUNT(*) AS count FROM editorial_publication_receipts").first("count")).toBe(2);
      expect((await inspectStoredEditorialArticle(db, first.payload.slug, NOW))?.payload.revision).toBe(2);
      await expect(getEditorialArticle(db, first.payload.slug, NOW)).rejects.toMatchObject({ code: "EDITORIAL_EVIDENCE_NOT_PUBLIC" });
    } finally { await runtime.dispose(); }
  }, 30_000);
});
