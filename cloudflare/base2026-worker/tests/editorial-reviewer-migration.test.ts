import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { convertV4MiniflareOptions, Miniflare } from "miniflare";
import { describe, expect, it } from "vitest";

const ORIGINAL = readFileSync(new URL("../migrations/0004_editorial_articles.sql", import.meta.url), "utf8");
const FORWARD = readFileSync(new URL("../migrations/0007_editorial_astra_review.sql", import.meta.url), "utf8");
const ROLLBACK = readFileSync(new URL("./fixtures/editorial-reviewer-rollback.sql", import.meta.url), "utf8");
const ARTICLE_SLUG = "migration-seed-article";
const PUBLISHED_AT = "2026-08-29T10:00:00.000Z";
const REVIEWED_AT = "2026-08-30T15:00:00.000Z";
const RECORDED_AT = "2026-08-30T16:00:00.000Z";

function statements(sql: string): string[] {
  return sql.replace(/^\s*--.*$/gmu, "").split(";").map((value) => value.trim()).filter(Boolean);
}

async function batchSql(db: D1Database, sql: string): Promise<D1Result<unknown>[]> {
  return db.batch(statements(sql).map((statement) => db.prepare(statement)));
}

async function rows(db: D1Database, sql: string, ...values: string[]): Promise<Record<string, unknown>[]> {
  return (await db.prepare(sql).bind(...values).all()).results as Record<string, unknown>[];
}

async function names(db: D1Database): Promise<string[]> {
  const result = await rows(db, "SELECT name FROM sqlite_master WHERE type IN ('table','index','trigger','view') ORDER BY name");
  return result.map((row) => String(row.name));
}

async function tableSql(db: D1Database, table: string): Promise<string> {
  const result = await db.prepare("SELECT sql FROM sqlite_master WHERE type='table' AND name=?1").bind(table).first<{ sql: string }>();
  if (!result) throw new Error(`missing table ${table}`);
  return result.sql;
}

async function pragmaRows(db: D1Database, pragma: string): Promise<Record<string, unknown>[]> {
  return (await db.prepare(pragma).all()).results as Record<string, unknown>[];
}

async function seedLegacy(db: D1Database): Promise<{ article: Record<string, unknown>; receipt: Record<string, unknown> }> {
  const payload = JSON.stringify({
    schema_version: "base2026.editorial.v1", kind: "source_based_article", slug: ARTICLE_SLUG,
    revision: 1, published_at: PUBLISHED_AT, updated_at: PUBLISHED_AT,
  });
  const payloadSha256 = createHash("sha256").update(payload).digest("hex");
  await db.prepare(`INSERT INTO editorial_articles
    (slug, revision, payload_sha256, payload_json, published_at, updated_at, created_at, stored_at)
    VALUES (?1, 1, ?2, ?3, ?4, ?4, ?4, ?5)`)
    .bind(ARTICLE_SLUG, payloadSha256, payload, PUBLISHED_AT, RECORDED_AT).run();
  await db.prepare(`INSERT INTO editorial_publication_receipts
    (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
    VALUES (?1, 1, ?2, ?3, ?3, 'sol-max', ?4, ?5)`)
    .bind(ARTICLE_SLUG, payloadSha256, PUBLISHED_AT, REVIEWED_AT, RECORDED_AT).run();
  const article = (await rows(db, "SELECT slug,revision,payload_sha256,payload_json,published_at,updated_at,created_at,stored_at FROM editorial_articles"))[0];
  const receipt = (await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts"))[0];
  return { article, receipt };
}

async function freshDatabase(): Promise<{ runtime: Miniflare; db: D1Database }> {
  const runtime = new Miniflare(convertV4MiniflareOptions({
    modules: true,
    script: "export default { fetch() { return new Response('migration test'); } };",
    compatibilityDate: "2026-08-19",
    d1Databases: ["DB"],
    cf: false,
  }));
  const db = await runtime.getD1Database("DB");
  // D1 exec rejects a leading comment-only line; the legacy schema is setup
  // data here, so apply its executable statements as one setup batch.
  await db.batch(statements(ORIGINAL).map((statement) => db.prepare(statement)));
  return { runtime, db };
}

describe("editorial reviewer migration and rollback", () => {
  it("keeps the forward and rollback artifacts as three-statement D1 batches without manual transactions or destructive SQL", () => {
    for (const sql of [FORWARD, ROLLBACK]) {
      expect(statements(sql)).toHaveLength(3);
      const executable = statements(sql).join(";");
      expect(executable).not.toMatch(/\b(?:BEGIN|COMMIT|ROLLBACK)\b/iu);
      expect(executable).not.toMatch(/\b(?:DROP|DELETE|REPLACE)\b/iu);
      expect(executable).not.toMatch(/CREATE TABLE IF NOT EXISTS/iu);
    }
    expect(FORWARD).toContain("ALTER TABLE editorial_publication_receipts\n  RENAME TO editorial_publication_receipts_legacy_0007");
    expect(FORWARD).toContain("reviewer IN ('sol-max', 'gpt-6-astra')");
    expect(ROLLBACK).toContain("ALTER TABLE editorial_publication_receipts\n  RENAME TO editorial_publication_receipts_astra_rollback_0007");
    expect(ROLLBACK).toContain("reviewer = 'sol-max'");
  });

  it("atomically preserves legacy rows and active PK/FK behavior while widening the reviewer check", async () => {
    const { runtime, db } = await freshDatabase();
    try {
      const seeded = await seedLegacy(db);
      const beforeArticle = await rows(db, "SELECT * FROM editorial_articles");
      const beforeIndexes = await pragmaRows(db, "PRAGMA index_list('editorial_publication_receipts')");
      const beforeForeignKeys = await pragmaRows(db, "PRAGMA foreign_key_list('editorial_publication_receipts')");
      const result = await batchSql(db, FORWARD);
      expect(result).toHaveLength(3);
      expect(result.every((item) => item.success)).toBe(true);
      expect(await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts")).toEqual([seeded.receipt]);
      expect(await rows(db, "SELECT * FROM editorial_publication_receipts_legacy_0007")).toEqual([seeded.receipt]);
      expect(await rows(db, "SELECT * FROM editorial_articles")).toEqual(beforeArticle);
      expect(await tableSql(db, "editorial_publication_receipts")).toContain("reviewer IN ('sol-max', 'gpt-6-astra')");
      expect(await tableSql(db, "editorial_publication_receipts_legacy_0007")).toContain("reviewer = 'sol-max'");
      const afterIndexes = await pragmaRows(db, "PRAGMA index_list('editorial_publication_receipts')");
      const afterForeignKeys = await pragmaRows(db, "PRAGMA foreign_key_list('editorial_publication_receipts')");
      expect(afterIndexes.map(({ seq: _seq, name: _name, ...row }) => row)).toEqual(beforeIndexes.map(({ seq: _seq, name: _name, ...row }) => row));
      expect(afterForeignKeys.map(({ id: _id, seq: _seq, ...row }) => row)).toEqual(beforeForeignKeys.map(({ id: _id, seq: _seq, ...row }) => row));
      await db.prepare(`INSERT INTO editorial_publication_receipts
        (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
        VALUES (?1, 2, ?2, ?3, ?3, 'gpt-6-astra', ?4, ?5)`)
        .bind(ARTICLE_SLUG, "b".repeat(64), PUBLISHED_AT, REVIEWED_AT, RECORDED_AT).run();
      expect((await rows(db, "SELECT reviewer FROM editorial_publication_receipts WHERE revision=2"))[0]).toEqual({ reviewer: "gpt-6-astra" });
    } finally {
      await runtime.dispose();
    }
  }, 30_000);

  it("rolls back before Astra publication by copying every current Sol row and retaining both backups", async () => {
    const { runtime, db } = await freshDatabase();
    try {
      await seedLegacy(db);
      await batchSql(db, FORWARD);
      await db.prepare(`INSERT INTO editorial_publication_receipts
        (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
        VALUES (?1, 2, ?2, ?3, ?3, 'sol-max', ?4, ?5)`)
        .bind(ARTICLE_SLUG, "c".repeat(64), PUBLISHED_AT, REVIEWED_AT, RECORDED_AT).run();
      const currentRows = await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts ORDER BY revision");
      expect((await batchSql(db, ROLLBACK)).every((item) => item.success)).toBe(true);
      expect(await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts ORDER BY revision")).toEqual(currentRows);
      expect(await tableSql(db, "editorial_publication_receipts")).toContain("reviewer = 'sol-max'");
      expect(await rows(db, "SELECT * FROM editorial_publication_receipts_legacy_0007 ORDER BY revision")).toHaveLength(1);
      expect((await names(db)).filter((name) => name.startsWith("editorial_publication_receipts")).sort()).toEqual([
        "editorial_publication_receipts", "editorial_publication_receipts_astra_rollback_0007", "editorial_publication_receipts_legacy_0007",
      ]);
    } finally {
      await runtime.dispose();
    }
  }, 30_000);

  it("atomically rejects a late forward failure without leaving a half-renamed receipt table", async () => {
    const { runtime, db } = await freshDatabase();
    try {
      const seeded = await seedLegacy(db);
      const forwardStatements = statements(FORWARD).map((statement) => db.prepare(statement));
      forwardStatements.push(db.prepare(`INSERT INTO editorial_publication_receipts
        (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
        VALUES ('${ARTICLE_SLUG}', 99, '${"e".repeat(64)}', '${PUBLISHED_AT}', '${PUBLISHED_AT}', 'luna-max', '${REVIEWED_AT}', '${RECORDED_AT}')`));
      await expect(db.batch(forwardStatements)).rejects.toBeTruthy();
      expect(await rows(db, "SELECT * FROM editorial_publication_receipts")).toEqual([seeded.receipt]);
      expect((await names(db)).some((name) => name === "editorial_publication_receipts_legacy_0007")).toBe(false);
      expect((await names(db)).some((name) => name === "editorial_publication_receipts")).toBe(true);
    } finally {
      await runtime.dispose();
    }
  }, 30_000);

  it("atomically refuses legacy rollback after an Astra receipt appears and leaves all rows/schema unchanged", async () => {
    const { runtime, db } = await freshDatabase();
    try {
      await seedLegacy(db);
      await batchSql(db, FORWARD);
      await db.prepare(`INSERT INTO editorial_publication_receipts
        (slug, revision, payload_sha256, published_at, updated_at, reviewer, reviewed_at, recorded_at)
        VALUES (?1, 2, ?2, ?3, ?3, 'gpt-6-astra', ?4, ?5)`)
        .bind(ARTICLE_SLUG, "d".repeat(64), PUBLISHED_AT, REVIEWED_AT, RECORDED_AT).run();
      const activeRows = await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts ORDER BY revision");
      const beforeNames = await names(db);
      await expect(batchSql(db, ROLLBACK)).rejects.toBeTruthy();
      expect(await rows(db, "SELECT slug,revision,payload_sha256,published_at,updated_at,reviewer,reviewed_at,recorded_at FROM editorial_publication_receipts ORDER BY revision")).toEqual(activeRows);
      expect(await names(db)).toEqual(beforeNames);
      expect(await tableSql(db, "editorial_publication_receipts")).toContain("reviewer IN ('sol-max', 'gpt-6-astra')");
      expect((await names(db)).some((name) => name === "editorial_publication_receipts_astra_rollback_0007")).toBe(false);
    } finally {
      await runtime.dispose();
    }
  }, 30_000);
});
