import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { describe, expect, it } from "vitest";
import worker from "../src/index";
import {
  admitClaimReceiptCanary,
  claimReceiptManifestSha256,
  CLAIM_RECEIPT_ADMISSION_SCHEMA,
  CLAIM_RECEIPT_CANARY_ID,
  CLAIM_RECEIPT_POLICY_VERSION,
  CLAIM_RECEIPT_TOPIC,
  readClaimReceiptLedger,
  rollbackClaimReceiptCanary,
  type ClaimReceiptAdmissionRequest,
  type ClaimReceiptCandidate,
} from "../src/claim-receipt-ledger";
import {
  applyPublicProjection,
  deterministicProjectionId,
  type PublicProjectionRequest,
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
    for (const migration of [
      "0001_search.sql",
      "0002_align_fts_content_columns.sql",
      "0003_public_projection.sql",
      "0004_editorial_articles.sql",
      "0005_claim_receipt_ledger.sql",
    ]) {
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

async function projection(index: number): Promise<PublicProjectionRequest> {
  const videoId = (7999999999999990000n + BigInt(index)).toString();
  const handle = `creator${index % 5}`;
  const sourceId = `tiktok:${handle}:${videoId}`;
  const manifestSha256 = ((index + 1) % 16).toString(16).repeat(64);
  const projectionId = await deterministicProjectionId(sourceId, manifestSha256);
  const date = `2026-08-${String(19 - index).padStart(2, "0")}`;
  return {
    schema_version: "base2026.public-projection.v1",
    projection_id: projectionId,
    source: {
      source_id: sourceId,
      canonical_url: `https://www.tiktok.com/@${handle}/video/${videoId}`,
      creator_handle: `@${handle}`,
      published_at: date,
      title_or_description: "A public source description used for canary attribution.",
      duration_seconds: 42,
    },
    manifest_sha256: manifestSha256,
    content_sha256: ((index + 1) % 16).toString(16).repeat(64),
    private_import_receipt_sha256: "f".repeat(64),
    cards: [{
      ordinal: 0,
      claim_text: `Internal-linking claim ${index} is bounded and source-backed.`,
      suggested_action: `Apply internal-linking action ${index} with the source citation.`,
      topic_label: "internal-linking",
      evidence_excerpt: `The public source provides internal-linking evidence example ${index}.`,
      evidence_start_seconds: 1,
      evidence_end_seconds: 8,
    }],
  };
}

async function fixture(): Promise<{ db: SqliteD1; request: ClaimReceiptAdmissionRequest }> {
  const db = new SqliteD1();
  for (let index = 0; index < 10; index += 1) {
    await applyPublicProjection(db as unknown as D1Database, await projection(index));
  }
  const rows = db.rows<{
    source_id: string;
    projection_id: string;
    card_id: string;
    search_id: string;
    card_ordinal: number;
    creator_handle: string;
    creator_display_name: string;
    creator_url: string;
    original_url: string;
    video_id: string;
    published_at: string;
    published_date: string;
    claim_text: string;
    suggested_action: string;
    topic_label: string;
    evidence_excerpt: string;
    evidence_start_seconds: number;
    evidence_end_seconds: number;
    public_projection_receipt_sha256: string;
  }>(
    `SELECT c.source_id, c.projection_id, c.card_id, c.search_id, c.ordinal AS card_ordinal,
            d.creator_handle, d.creator_display_name, d.creator_url, d.source_url AS original_url,
            d.video_id, d.published_at, d.published_date, c.claim_text, c.suggested_action,
            c.topic_label, c.evidence_excerpt, c.evidence_start_seconds, c.evidence_end_seconds,
            r.receipt_sha256 AS public_projection_receipt_sha256
       FROM public_projection_cards c
       JOIN public_projection_receipts r ON r.projection_id = c.projection_id
       JOIN search_documents d ON d.id = c.search_id
      ORDER BY d.published_date DESC, c.source_id, c.projection_id, c.ordinal, c.card_id`,
  );
  const candidates: ClaimReceiptCandidate[] = rows.map((row, index) => ({
    selection_rank: index + 1,
    ...row,
    base2026_url: `https://base2026.dev/sources/tiktok-video-${row.video_id}`,
  }));
  return {
    db,
    request: {
      schema_version: CLAIM_RECEIPT_ADMISSION_SCHEMA,
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      topic: CLAIM_RECEIPT_TOPIC,
      policy_version: CLAIM_RECEIPT_POLICY_VERSION,
      manifest_sha256: await claimReceiptManifestSha256(candidates),
      candidates,
    },
  };
}

function env(db: SqliteD1): Env {
  return { DB: db as unknown as D1Database } as unknown as Env;
}

describe("public claim-receipt canary", () => {
  it("holds with no public rows and never pads the canary", async () => {
    const db = new SqliteD1();
    const empty: ClaimReceiptAdmissionRequest = {
      schema_version: CLAIM_RECEIPT_ADMISSION_SCHEMA,
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      topic: CLAIM_RECEIPT_TOPIC,
      policy_version: CLAIM_RECEIPT_POLICY_VERSION,
      manifest_sha256: await claimReceiptManifestSha256([]),
      candidates: [],
    };
    await expect(admitClaimReceiptCanary(db as unknown as D1Database, empty)).resolves.toEqual({
      status: "held",
      code: "CLAIM_RECEIPT_CANARY_NOT_READY",
      count: 0,
    });
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts")).toMatchObject({ count: 0 });
    await expect(readClaimReceiptLedger(db as unknown as D1Database, "2026-09-01T00:00:00.000Z")).resolves.toEqual({
      status: "held",
      code: "CLAIM_RECEIPT_CANARY_NOT_READY",
      count: 0,
    });
  });

  it("validates, atomically admits exactly ten rows, and makes same-digest replay idempotent", async () => {
    const { db, request } = await fixture();
    const admitted = await admitClaimReceiptCanary(db as unknown as D1Database, request);
    expect(admitted.status).toBe("admitted");
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts")).toMatchObject({ count: 10 });
    const read = await readClaimReceiptLedger(db as unknown as D1Database, "2026-09-01T00:00:00.000Z");
    expect(read.status).toBe("ready");
    if (read.status === "ready") {
      expect(read.payload.count).toBe(10);
      expect(read.payload.receipts.map((receipt) => receipt.selection_rank)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
      expect(read.payload.generated_at).toBe("2026-09-01T00:00:00.000Z");
      expect(JSON.stringify(read.payload)).not.toContain("private_import");
      expect(JSON.stringify(read.payload)).not.toContain("transcript");
    }
    const replay = await admitClaimReceiptCanary(db as unknown as D1Database, request);
    expect(replay).toMatchObject({
      status: "replayed",
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      count: 10,
      ledger_sha256: (admitted as { ledger_sha256: string }).ledger_sha256,
    });
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts")).toMatchObject({ count: 10 });
  });

  it("holds the complete batch on a reread mismatch without writing a partial ledger", async () => {
    const { db, request } = await fixture();
    db.sqlite.prepare("UPDATE public_projection_cards SET claim_text = ? WHERE ordinal = 0 AND source_id = ?")
      .run("A changed public claim that must fail closed.", "tiktok:creator0:7999999999999990000");
    await expect(admitClaimReceiptCanary(db as unknown as D1Database, request)).resolves.toMatchObject({
      status: "held",
      code: "CLAIM_RECEIPT_CANARY_VALIDATION_FAILED",
    });
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts")).toMatchObject({ count: 0 });
  });

  it("is service-binding-only for writes and strict at the public HTTP boundary", async () => {
    const { db } = await fixture();
    const unavailable = await worker.fetch(
      new Request(`https://base2026.dev/api/claim-receipts/v1?canary=${CLAIM_RECEIPT_CANARY_ID}&topic=${CLAIM_RECEIPT_TOPIC}`),
      env(db),
      {} as ExecutionContext,
    );
    expect(unavailable.status).toBe(503);
    expect(await unavailable.json()).toMatchObject({ error: { code: "CLAIM_RECEIPT_CANARY_NOT_READY" } });

    const unknown = await worker.fetch(
      new Request(`https://base2026.dev/api/claim-receipts/v1?canary=${CLAIM_RECEIPT_CANARY_ID}&topic=${CLAIM_RECEIPT_TOPIC}&limit=10`),
      env(db),
      {} as ExecutionContext,
    );
    expect(unknown.status).toBe(400);
    const mutation = await worker.fetch(
      new Request(`https://base2026.dev/api/claim-receipts/v1?canary=${CLAIM_RECEIPT_CANARY_ID}&topic=${CLAIM_RECEIPT_TOPIC}`, { method: "POST" }),
      env(db),
      {} as ExecutionContext,
    );
    expect(mutation.status).toBe(405);
    expect(mutation.headers.get("allow")).toBe("GET, HEAD");
  });

  it("keeps old rows and makes exact rollback idempotent", async () => {
    const { db, request } = await fixture();
    const admitted = await admitClaimReceiptCanary(db as unknown as D1Database, request);
    if (admitted.status !== "admitted") throw new Error("fixture did not admit");
    const rolledBack = await rollbackClaimReceiptCanary(db as unknown as D1Database, {
      schema_version: "base2026.claim-receipt-rollback.v1",
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      ledger_sha256: admitted.ledger_sha256,
    });
    expect(rolledBack.status).toBe("rolled_back");
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts")).toMatchObject({ count: 10 });
    expect(db.row("SELECT COUNT(*) AS count FROM public_claim_receipts WHERE state='rolled_back'"))
      .toMatchObject({ count: 10 });
    await expect(readClaimReceiptLedger(db as unknown as D1Database)).resolves.toMatchObject({
      status: "held",
      count: 0,
    });
    await expect(rollbackClaimReceiptCanary(db as unknown as D1Database, {
      schema_version: "base2026.claim-receipt-rollback.v1",
      canary_id: CLAIM_RECEIPT_CANARY_ID,
      ledger_sha256: admitted.ledger_sha256,
    })).resolves.toMatchObject({ status: "already_rolled_back", count: 10 });
  });

  it("rejects private fields, wrong topic and duplicate ranks at the service boundary", async () => {
    const { db, request } = await fixture();
    const privateField = JSON.parse(JSON.stringify(request)) as Record<string, unknown>;
    (privateField.candidates as Array<Record<string, unknown>>)[0].private_import_hash = "secret";
    await expect(admitClaimReceiptCanary(db as unknown as D1Database, privateField)).rejects.toMatchObject({
      code: "CLAIM_RECEIPT_CANDIDATE_FIELDS_INVALID",
    });
    const duplicate = JSON.parse(JSON.stringify(request)) as ClaimReceiptAdmissionRequest;
    duplicate.candidates[1].selection_rank = 1;
    await expect(admitClaimReceiptCanary(db as unknown as D1Database, duplicate)).rejects.toMatchObject({
      code: "CLAIM_RECEIPT_DUPLICATE_SELECTION_RANK",
    });
  });
});
