import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { describe, expect, it } from "vitest";
import {
  applyPublicProjection,
  deterministicCardId,
  deterministicSearchId,
  inspectPublicSource,
  parsePublicProjectionReceipt,
  parsePublicProjection,
  parsePublicProjectionVerifyRequest,
  parsePublicSourcePresenceReceipt,
  parsePublicSourcePresenceRequest,
  PublicProjectionError,
  rollbackPublicProjection,
  type PublicProjectionRequest,
  type PublicProjectionVerifyRequest,
  type PublicSourcePresenceRequest,
  verifyPublicProjection,
} from "../src/public-projection";

type SqliteRow = Record<string, unknown>;

class SqlitePrepared {
  private parameters: unknown[] = [];

  constructor(private readonly statement: ReturnType<DatabaseSync["prepare"]>) {}

  bind(...parameters: unknown[]): SqlitePrepared {
    this.parameters = parameters;
    return this;
  }

  async first<T = SqliteRow>(): Promise<T | null> {
    return (this.statement.get(...(this.parameters as any[])) as T | undefined) ?? null;
  }

  async all<T = SqliteRow>(): Promise<{ results: T[] }> {
    return { results: this.statement.all(...(this.parameters as any[])) as T[] };
  }

  async run(): Promise<{ meta: { changes: number } }> {
    const result = this.statement.run(...(this.parameters as any[]));
    return { meta: { changes: Number(result.changes) } };
  }
}

class SqliteD1 {
  readonly sqlite = new DatabaseSync(":memory:");

  constructor() {
    for (const migration of ["0001_search.sql", "0002_align_fts_content_columns.sql", "0003_public_projection.sql"]) {
      this.sqlite.exec(readFileSync(new URL(`../migrations/${migration}`, import.meta.url), "utf8"));
    }
  }

  prepare(sql: string): SqlitePrepared {
    return new SqlitePrepared(this.sqlite.prepare(sql));
  }

  async batch(statements: SqlitePrepared[]): Promise<unknown[]> {
    this.sqlite.exec("BEGIN");
    try {
      const results = [];
      for (const statement of statements) results.push(await statement.run());
      this.sqlite.exec("COMMIT");
      return results;
    } catch (error) {
      this.sqlite.exec("ROLLBACK");
      throw error;
    }
  }

  row<T extends SqliteRow = SqliteRow>(sql: string, ...parameters: unknown[]): T | null {
    return (this.sqlite.prepare(sql).get(...(parameters as any[])) as T | undefined) ?? null;
  }

  rows<T extends SqliteRow = SqliteRow>(sql: string, ...parameters: unknown[]): T[] {
    return this.sqlite.prepare(sql).all(...(parameters as any[])) as T[];
  }
}

const HASH_A = "a".repeat(64);
const HASH_B = "b".repeat(64);
const HASH_C = "c".repeat(64);
const SOURCE_ID = "tiktok:example:7999999999999999999";
const NUMERIC_ID = "7999999999999999999";
const PROJECTION_ID = "1".repeat(40);

function request(overrides: Partial<PublicProjectionRequest> = {}): PublicProjectionRequest {
  return {
    schema_version: "base2026.public-projection.v1",
    projection_id: PROJECTION_ID,
    source: {
      source_id: SOURCE_ID,
      canonical_url: `https://www.tiktok.com/@example/video/${NUMERIC_ID}`,
      creator_handle: "@example",
      published_at: "2026-08-19",
      title_or_description: "A public source description used only for attribution metadata.",
      duration_seconds: 32.5,
    },
    manifest_sha256: HASH_A,
    content_sha256: HASH_B,
    private_import_receipt_sha256: HASH_C,
    cards: [
      {
        ordinal: 0,
        claim_text: "Useful evidence improves the quality of an answer.",
        suggested_action: "Publish the exact evidence excerpt with a clear source link.",
        topic_label: "Evidence quality",
        evidence_excerpt: "Useful evidence improves the quality of an answer when the source is clear.",
        evidence_start_seconds: 1.25,
        evidence_end_seconds: 4.5,
      },
      {
        ordinal: 1,
        claim_text: "A narrow claim is easier to verify than a broad promise.",
        suggested_action: "Keep each public card narrow and attach its source passage.",
        topic_label: "Verification",
        evidence_excerpt: "A narrow claim is easier to verify than a broad promise in public search.",
        evidence_start_seconds: 8,
        evidence_end_seconds: 12,
      },
    ],
    ...overrides,
  };
}

function presenceRequest(overrides: Partial<PublicSourcePresenceRequest> = {}): PublicSourcePresenceRequest {
  return {
    schema_version: "base2026.public-source-presence.v1",
    source_id: SOURCE_ID,
    ...overrides,
  };
}

function verifyRequest(overrides: Partial<PublicProjectionVerifyRequest> = {}): PublicProjectionVerifyRequest {
  return {
    schema_version: "base2026.public-projection-verify.v1",
    projection_id: PROJECTION_ID,
    source_id: SOURCE_ID,
    manifest_sha256: HASH_A,
    content_sha256: HASH_B,
    ...overrides,
  };
}

async function expectProjectionError(action: () => unknown, code: string): Promise<void> {
  try {
    await action();
    throw new Error("expected projection error");
  } catch (error) {
    expect(error).toBeInstanceOf(PublicProjectionError);
    expect((error as PublicProjectionError).code).toBe(code);
  }
}

describe("public projection DTO and D1 lane", () => {
  it("rejects private fields and non-canonical TikTok identities", () => {
    const privateField = JSON.parse(JSON.stringify(request())) as Record<string, unknown>;
    privateField.public_source_text = "private transcript text";
    expect(() => parsePublicProjection(privateField)).toThrow(PublicProjectionError);

    const privateNestedField = JSON.parse(JSON.stringify(request())) as Record<string, unknown>;
    (privateNestedField.cards as Array<Record<string, unknown>>)[0].source_questions = ["private question"];
    expect(() => parsePublicProjection(privateNestedField)).toThrow(PublicProjectionError);

    const nonCanonical = request({
      source: {
        ...request().source,
        source_id: "tiktok:other:7999999999999999999",
      },
    });
    expect(() => parsePublicProjection(nonCanonical)).toThrow(PublicProjectionError);
  });

  it("fails closed on bounded private/contact markers without rejecting harmless words", () => {
    const email = request({
      source: { ...request().source, title_or_description: "Contact analyst@example.com for the private review." },
    });
    expect(() => parsePublicProjection(email)).toThrow(PublicProjectionError);

    const phone = request({
      cards: request().cards.map((card, index) => index === 0 ? { ...card, claim_text: "Call +1 (555) 123-4567 for the public evidence review." } : card),
    });
    expect(() => parsePublicProjection(phone)).toThrow(PublicProjectionError);

    const secret = request({
      cards: request().cards.map((card, index) => index === 0 ? { ...card, suggested_action: "Review api_key=sk_live_123456789 before public release." } : card),
    });
    expect(() => parsePublicProjection(secret)).toThrow(PublicProjectionError);

    const rawMarker = request({
      cards: request().cards.map((card, index) => index === 0 ? { ...card, topic_label: "Raw transcript" } : card),
    });
    expect(() => parsePublicProjection(rawMarker)).toThrow(PublicProjectionError);

    const localPath = request({
      cards: request().cards.map((card, index) => index === 0 ? { ...card, evidence_excerpt: "Read /Users/alex/private/source.txt before publishing this passage." } : card),
    });
    expect(() => parsePublicProjection(localPath)).toThrow(PublicProjectionError);

    const harmless = request({
      source: { ...request().source, title_or_description: "Private markets and token economy use public evidence; API key concepts are documented." },
      cards: request().cards.map((card, index) => index === 0 ? { ...card, topic_label: "Private markets" } : card),
    });
    expect(parsePublicProjection(harmless).source.title_or_description).toContain("Private markets");
  });

  it("parses exact presence and verification contracts", () => {
    expect(parsePublicSourcePresenceRequest(presenceRequest())).toEqual(presenceRequest());
    expect(parsePublicProjectionVerifyRequest(verifyRequest())).toEqual(verifyRequest());
    expect(parsePublicSourcePresenceReceipt({
      schema_version: "base2026.public-source-presence-receipt.v1",
      source_id: SOURCE_ID,
      state: "absent",
      document_count: 0,
      full_transcript_public_count: 0,
      projection_id: null,
      manifest_sha256: null,
    })).toMatchObject({ state: "absent", source_id: SOURCE_ID });
    expect(parsePublicProjectionReceipt({
      schema_version: "base2026.public-projection-receipt.v1",
      projection_id: PROJECTION_ID,
      source_id: SOURCE_ID,
      manifest_sha256: HASH_A,
      content_sha256: HASH_B,
      status: "applied",
      card_count: 2,
      row_count: 2,
      receipt_sha256: HASH_C,
    })).toMatchObject({ status: "applied", card_count: 2, row_count: 2 });

    expect(() => parsePublicSourcePresenceRequest({ ...presenceRequest(), extra: "reject" })).toThrow(PublicProjectionError);
    expect(() => parsePublicProjectionVerifyRequest({ ...verifyRequest(), extra: "reject" })).toThrow(PublicProjectionError);
  });

  it("reports absent, legacy_public and projected states without private fields", async () => {
    const absentDb = new SqliteD1();
    const absent = await inspectPublicSource(absentDb as unknown as D1Database, presenceRequest());
    expect(absent).toEqual({
      schema_version: "base2026.public-source-presence-receipt.v1",
      source_id: SOURCE_ID,
      state: "absent",
      document_count: 0,
      full_transcript_public_count: 0,
      projection_id: null,
      manifest_sha256: null,
    });

    const legacyDb = new SqliteD1();
    legacyDb.sqlite.prepare(
      `INSERT INTO search_documents
        (id, item_id, source_id, chunk_id, body, title, full_transcript_public)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
    ).run("legacy-row-1", "legacy-item-1", SOURCE_ID, "legacy-chunk-1", "legacy evidence", "legacy title", 1);
    const legacy = await inspectPublicSource(legacyDb as unknown as D1Database, presenceRequest());
    expect(legacy).toMatchObject({
      state: "legacy_public",
      document_count: 1,
      full_transcript_public_count: 1,
      projection_id: null,
      manifest_sha256: null,
    });

    const projectedDb = new SqliteD1();
    const applied = await applyPublicProjection(projectedDb as unknown as D1Database, request());
    const projected = await inspectPublicSource(projectedDb as unknown as D1Database, presenceRequest());
    expect(projected).toMatchObject({
      schema_version: "base2026.public-source-presence-receipt.v1",
      source_id: SOURCE_ID,
      state: "projected",
      document_count: 2,
      full_transcript_public_count: 0,
      projection_id: PROJECTION_ID,
      manifest_sha256: HASH_A,
    });
    expect(Object.keys(projected).sort()).toEqual([
      "document_count",
      "full_transcript_public_count",
      "manifest_sha256",
      "projection_id",
      "schema_version",
      "source_id",
      "state",
    ]);
    expect(JSON.stringify(projected)).not.toContain("tiktok.com");
    expect(JSON.stringify(projected)).not.toContain("private_import_receipt_sha256");

    const verified = await verifyPublicProjection(
      projectedDb as unknown as D1Database,
      verifyRequest(),
    );
    expect(verified).toEqual(applied);
    expect(Object.keys(verified).sort()).toEqual([
      "card_count",
      "content_sha256",
      "manifest_sha256",
      "projection_id",
      "receipt_sha256",
      "row_count",
      "schema_version",
      "source_id",
      "status",
    ]);
    expect(JSON.stringify(verified)).not.toContain("tiktok.com");
    expect(JSON.stringify(verified)).not.toContain("private_import_receipt_sha256");
  });

  it("rejects mixed legacy/applied presence and wrong verification tuples", async () => {
    const mixedDb = new SqliteD1();
    await applyPublicProjection(mixedDb as unknown as D1Database, request());
    mixedDb.sqlite.prepare(
      `INSERT INTO search_documents (id, item_id, source_id, chunk_id, body, title)
       VALUES (?, ?, ?, ?, ?, ?)`,
    ).run("legacy-after-projection", "legacy-item", SOURCE_ID, "legacy-chunk", "legacy evidence", "legacy title");
    await expectProjectionError(
      () => inspectPublicSource(mixedDb as unknown as D1Database, presenceRequest()),
      "PUBLIC_SOURCE_PRESENCE_MIXED_STATE",
    );

    const verifyDb = new SqliteD1();
    await applyPublicProjection(verifyDb as unknown as D1Database, request());
    await expectProjectionError(
      () => verifyPublicProjection(verifyDb as unknown as D1Database, verifyRequest({ content_sha256: "d".repeat(64) })),
      "PUBLIC_PROJECTION_VERIFY_MISMATCH",
    );
  });

  it("fails verification on document, card/topic and full-transcript mismatches", async () => {
    const documentDb = new SqliteD1();
    await applyPublicProjection(documentDb as unknown as D1Database, request());
    documentDb.sqlite.prepare("DELETE FROM search_documents WHERE projection_id=?").run(PROJECTION_ID);
    await expectProjectionError(
      () => verifyPublicProjection(documentDb as unknown as D1Database, verifyRequest()),
      "PUBLIC_PROJECTION_VERIFY_MISMATCH",
    );

    const topicDb = new SqliteD1();
    await applyPublicProjection(topicDb as unknown as D1Database, request());
    topicDb.sqlite.prepare(
      "DELETE FROM search_topics WHERE document_id=(SELECT id FROM search_documents WHERE projection_id=? LIMIT 1)",
    ).run(PROJECTION_ID);
    await expectProjectionError(
      () => verifyPublicProjection(topicDb as unknown as D1Database, verifyRequest()),
      "PUBLIC_PROJECTION_VERIFY_MISMATCH",
    );

    const transcriptDb = new SqliteD1();
    await applyPublicProjection(transcriptDb as unknown as D1Database, request());
    transcriptDb.sqlite.prepare(
      "UPDATE search_documents SET full_transcript_public=1 WHERE id=(SELECT id FROM search_documents WHERE projection_id=? LIMIT 1)",
    ).run(PROJECTION_ID);
    await expectProjectionError(
      () => verifyPublicProjection(transcriptDb as unknown as D1Database, verifyRequest()),
      "PUBLIC_PROJECTION_VERIFY_MISMATCH",
    );
  });

  it("applies the private RPC contract atomically, is idempotent, and rejects a new manifest", async () => {
    const db = new SqliteD1();
    const input = request();
    const applied = await applyPublicProjection(db as unknown as D1Database, input);
    const cardId = await deterministicCardId(PROJECTION_ID, 0);
    const searchId = await deterministicSearchId(cardId);

    expect(Object.keys(applied).sort()).toEqual([
      "card_count",
      "content_sha256",
      "manifest_sha256",
      "projection_id",
      "receipt_sha256",
      "row_count",
      "schema_version",
      "source_id",
      "status",
    ]);
    expect(applied).toMatchObject({
      schema_version: "base2026.public-projection-receipt.v1",
      status: "applied",
      projection_id: PROJECTION_ID,
      source_id: SOURCE_ID,
      manifest_sha256: HASH_A,
      content_sha256: HASH_B,
      card_count: 2,
      row_count: 2,
    });
    expect(db.row("SELECT COUNT(*) AS count FROM public_projection_receipts")).toMatchObject({ count: 1 });
    expect(db.row("SELECT private_import_receipt_sha256 FROM public_projection_receipts")).toMatchObject({ private_import_receipt_sha256: HASH_C });
    expect(db.row("SELECT COUNT(*) AS count FROM public_projection_cards")).toMatchObject({ count: 2 });
    expect(db.row("SELECT COUNT(*) AS count FROM search_documents")).toMatchObject({ count: 2 });
    expect(db.row("SELECT COUNT(*) AS count FROM search_topics")).toMatchObject({ count: 2 });

    const card = db.row<{
      ordinal: number;
      card_id: string;
      search_id: string;
      claim_text: string;
      suggested_action: string;
      topic_label: string;
      evidence_excerpt: string;
      evidence_start_seconds: number;
      evidence_end_seconds: number;
    }>("SELECT * FROM public_projection_cards WHERE ordinal=0");
    expect(card).toMatchObject({
      ordinal: 0,
      card_id: cardId,
      search_id: searchId,
      claim_text: input.cards[0].claim_text,
      suggested_action: input.cards[0].suggested_action,
      topic_label: input.cards[0].topic_label,
      evidence_excerpt: input.cards[0].evidence_excerpt,
      evidence_start_seconds: 1.25,
      evidence_end_seconds: 4.5,
    });

    const rows = db.rows<{
      source_id: string;
      post_id: string;
      video_id: string;
      body: string;
      title: string;
      full_transcript_public: number;
      public_surface: string;
      public_policy: string;
      admission_state: string;
    }>(
      `SELECT source_id, post_id, video_id, body, title, full_transcript_public,
              public_surface, public_policy, admission_state
         FROM search_documents ORDER BY chunk_index`,
    );
    expect(rows[0]).toMatchObject({
      source_id: SOURCE_ID,
      post_id: NUMERIC_ID,
      video_id: NUMERIC_ID,
      body: input.cards[0].evidence_excerpt,
      title: input.cards[0].claim_text,
      full_transcript_public: 0,
      public_surface: "main_search",
      public_policy: "search_passage",
      admission_state: "normal_public_card",
    });
    expect(rows[0]).not.toHaveProperty("public_source_text");

    const ftsRows = db.rows<{ id: string }>(
      `SELECT d.id
         FROM search_documents_fts
         JOIN search_documents AS d ON d.rowid=search_documents_fts.rowid
        WHERE search_documents_fts MATCH ?`,
      "evidence OR public",
    );
    expect(ftsRows).toHaveLength(2);

    const replay = await applyPublicProjection(db as unknown as D1Database, input);
    expect(replay).toEqual(applied);
    expect(db.row("SELECT COUNT(*) AS count FROM search_documents")).toMatchObject({ count: 2 });

    await expectProjectionError(
      () => applyPublicProjection(db as unknown as D1Database, request({ manifest_sha256: "d".repeat(64) })),
      "PUBLIC_PROJECTION_MANIFEST_CONFLICT",
    );
  });

  it("rejects a legacy public source before writing a projection", async () => {
    const db = new SqliteD1();
    db.sqlite.prepare(
      `INSERT INTO search_documents (id, item_id, source_id, chunk_id, body, title)
       VALUES (?, ?, ?, ?, ?, ?)`,
    ).run("legacy-public-row", "legacy-item", SOURCE_ID, "legacy-chunk", "legacy evidence", "legacy title");
    await expectProjectionError(
      () => applyPublicProjection(db as unknown as D1Database, request()),
      "PUBLIC_PROJECTION_SOURCE_ALREADY_PUBLIC",
    );
    expect(db.row("SELECT COUNT(*) AS count FROM public_projection_receipts")).toMatchObject({ count: 0 });
  });

  it("binds the applied receipt hash to the actual private importer hash", async () => {
    const firstDb = new SqliteD1();
    const secondDb = new SqliteD1();
    const first = await applyPublicProjection(firstDb as unknown as D1Database, request({ private_import_receipt_sha256: HASH_C }));
    const second = await applyPublicProjection(secondDb as unknown as D1Database, request({ private_import_receipt_sha256: "d".repeat(64) }));

    expect(first.receipt_sha256).not.toBe(second.receipt_sha256);
    expect(firstDb.row("SELECT private_import_receipt_sha256 FROM public_projection_receipts")).toMatchObject({ private_import_receipt_sha256: HASH_C });
    expect(secondDb.row("SELECT private_import_receipt_sha256 FROM public_projection_receipts")).toMatchObject({ private_import_receipt_sha256: "d".repeat(64) });
  });

  it("rolls back only the exact projection and manifest, preserving unrelated rows", async () => {
    const db = new SqliteD1();
    const input = request();
    const applied = await applyPublicProjection(db as unknown as D1Database, input);
    const unrelatedId = "legacy-public-row";
    db.sqlite.prepare(
      `INSERT INTO search_documents (id, item_id, source_id, chunk_id, body, title)
       VALUES (?, ?, ?, ?, ?, ?)`,
    ).run(unrelatedId, "legacy-item", "legacy-source", "legacy-chunk", "unrelated evidence", "legacy title");

    await expectProjectionError(
      () => rollbackPublicProjection(
        db as unknown as D1Database,
        {
          schema_version: "base2026.public-projection-rollback.v1",
          projection_id: applied.projection_id,
          source_id: SOURCE_ID,
          manifest_sha256: "e".repeat(64),
          content_sha256: HASH_B,
        },
      ),
      "PUBLIC_PROJECTION_ROLLBACK_MISMATCH",
    );

    const rollback = await rollbackPublicProjection(
      db as unknown as D1Database,
      {
        schema_version: "base2026.public-projection-rollback.v1",
        projection_id: applied.projection_id,
        source_id: SOURCE_ID,
        manifest_sha256: input.manifest_sha256,
        content_sha256: input.content_sha256,
      },
    );
    expect(rollback).toMatchObject({
      schema_version: "base2026.public-projection-receipt.v1",
      status: "rolled_back",
      projection_id: PROJECTION_ID,
      source_id: SOURCE_ID,
      card_count: 0,
      row_count: 0,
    });
    expect(Object.keys(rollback).sort()).toEqual(Object.keys(applied).sort());
    expect(db.row("SELECT COUNT(*) AS count FROM search_documents")).toMatchObject({ count: 1 });
    expect(db.row("SELECT COUNT(*) AS count FROM public_projection_cards")).toMatchObject({ count: 0 });
    expect(db.row("SELECT id FROM search_documents WHERE id=?", unrelatedId)).toMatchObject({ id: unrelatedId });
    expect(db.row("SELECT status FROM public_projection_receipts WHERE projection_id=?", PROJECTION_ID)).toMatchObject({ status: "rolled_back" });

    const corrected = request({
      projection_id: "2".repeat(40),
      manifest_sha256: "d".repeat(64),
      content_sha256: "e".repeat(64),
      private_import_receipt_sha256: "f".repeat(64),
    });
    const correctedApplied = await applyPublicProjection(db as unknown as D1Database, corrected);
    expect(correctedApplied).toMatchObject({
      status: "applied",
      projection_id: "2".repeat(40),
      manifest_sha256: "d".repeat(64),
      content_sha256: "e".repeat(64),
      card_count: 2,
      row_count: 2,
    });
    expect(db.row("SELECT COUNT(*) AS count FROM public_projection_receipts")).toMatchObject({ count: 2 });
    expect(db.row("SELECT COUNT(*) AS count FROM search_documents")).toMatchObject({ count: 3 });

    const replay = await rollbackPublicProjection(
      db as unknown as D1Database,
      {
        schema_version: "base2026.public-projection-rollback.v1",
        projection_id: applied.projection_id,
        source_id: SOURCE_ID,
        manifest_sha256: input.manifest_sha256,
        content_sha256: input.content_sha256,
      },
    );
    expect(replay).toEqual(rollback);
  });
});
