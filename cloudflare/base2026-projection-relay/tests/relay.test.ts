import { describe, expect, it, vi } from "vitest";
import {
  buildAuthCanonical,
  sha256Hex,
  signHmacHex,
} from "../src/crypto";
import {
  CROSS_ACCOUNT_PROJECTION_RESPONSE_SCHEMA,
  CROSS_ACCOUNT_PROJECTION_SCHEMA,
  handleRelayRequest,
  MAX_RELAY_BODY_BYTES,
  RELAY_NONCE_TTL_SECONDS,
  RELAY_PATHS,
  type ProjectionTargetRpc,
  type RelayEnvironment,
  type RelayOperation,
} from "../src/relay";
import {
  validateEditorialPacket,
  validateEditorialPayload,
  type EditorialReview,
} from "../src/editorial-contract";

type EditorialReviewer = EditorialReview["reviewer"];

const SECRET = "cross-account-relay-test-secret-cross-account-relay";
const NOW_MS = Date.parse("2026-09-04T00:00:00.000Z");
const SOURCE_ID = "tiktok:fixture:7999999999999999999";
const PROJECTION_ID = "a".repeat(40);
const MANIFEST_SHA256 = "b".repeat(64);
const CONTENT_SHA256 = "c".repeat(64);
const IMPORT_RECEIPT_SHA256 = "d".repeat(64);
const PUBLIC_RECEIPT_SHA256 = "e".repeat(64);

const APPLY_PAYLOAD = {
  schema_version: "base2026.public-projection.v1",
  projection_id: PROJECTION_ID,
  source: {
    source_id: SOURCE_ID,
    canonical_url: "https://www.tiktok.com/@fixture/video/7999999999999999999",
    creator_handle: "@fixture",
    published_at: "2026-09-04",
    title_or_description: "A practical measurement example",
    duration_seconds: 30,
  },
  manifest_sha256: MANIFEST_SHA256,
  content_sha256: CONTENT_SHA256,
  private_import_receipt_sha256: IMPORT_RECEIPT_SHA256,
  cards: [{
    ordinal: 0,
    claim_text: "A concrete measurement signal helps an operator choose a bounded next action.",
    suggested_action: "Record one baseline, compare one change, and keep the next action explicit.",
    topic_label: "measurement",
    evidence_excerpt: "Measure one baseline before changing the process, then compare the next result.",
    evidence_start_seconds: 1,
    evidence_end_seconds: 5,
  }],
};

const ROLLBACK_PAYLOAD = {
  schema_version: "base2026.public-projection-rollback.v1",
  projection_id: PROJECTION_ID,
  source_id: SOURCE_ID,
  manifest_sha256: MANIFEST_SHA256,
  content_sha256: CONTENT_SHA256,
};

const PRESENCE_PAYLOAD = {
  schema_version: "base2026.public-source-presence.v1",
  source_id: SOURCE_ID,
};

const VERIFY_PAYLOAD = {
  schema_version: "base2026.public-projection-verify.v1",
  projection_id: PROJECTION_ID,
  source_id: SOURCE_ID,
  manifest_sha256: MANIFEST_SHA256,
  content_sha256: CONTENT_SHA256,
};

const APPLY_RECEIPT = {
  schema_version: "base2026.public-projection-receipt.v1",
  projection_id: PROJECTION_ID,
  source_id: SOURCE_ID,
  manifest_sha256: MANIFEST_SHA256,
  content_sha256: CONTENT_SHA256,
  status: "applied",
  card_count: 1,
  row_count: 1,
  receipt_sha256: PUBLIC_RECEIPT_SHA256,
};

const ROLLBACK_RECEIPT = {
  ...APPLY_RECEIPT,
  status: "rolled_back",
  card_count: 0,
  row_count: 0,
};

const PRESENCE_RECEIPT = {
  schema_version: "base2026.public-source-presence-receipt.v1",
  source_id: SOURCE_ID,
  state: "absent",
  document_count: 0,
  full_transcript_public_count: 0,
  projection_id: null,
  manifest_sha256: null,
};

const EDITORIAL_PAYLOAD = {
  schema_version: "base2026.editorial.v1",
  kind: "engineering_note",
  slug: "relay-contract-note",
  revision: 1,
  title: "A bounded relay contract",
  description: "A short public engineering note about a bounded relay.",
  lede: "A relay should carry only an already-reviewed public contract.",
  category: "Engineering",
  tags: ["relay"],
  published_at: "2026-09-03T00:00:00.000Z",
  updated_at: "2026-09-03T00:00:00.000Z",
  author: { name: "Alex Yarosh" },
  ai_assistance_disclosure: "This note was prepared with bounded editorial assistance and reviewed by Sol Max.",
  first_party_context: "The target public Worker owns validation and durable publication.",
  sources: [{
    id: "base-methodology",
    url: "https://base2026.dev/methodology",
    title: "Base2026 methodology",
    checked_at: "2026-09-03T00:00:00.000Z",
  }],
  sections: [{
    id: "overview",
    heading: "Overview",
    blocks: [{
      type: "paragraph",
      text: "A fixed route, exact fields, and a replay fence keep transport narrow.",
      citation_ids: ["base-methodology"],
    }],
  }],
  related_paths: ["/methodology"],
};

function d1Result(changes = 0): D1Result {
  return {
    success: true,
    results: [],
    meta: {
      duration: 0,
      size_after: 0,
      rows_read: 0,
      rows_written: changes,
      last_row_id: 0,
      changed_db: changes > 0,
      changes,
    },
  };
}

class FakeStatement {
  readonly values: unknown[] = [];

  constructor(readonly db: FakeD1, readonly query: string) {}

  bind(...values: unknown[]): FakeStatement {
    this.values.splice(0, this.values.length, ...values);
    return this;
  }

  async run(): Promise<D1Result> {
    return this.db.run(this);
  }
}

class FakeD1 {
  readonly nonces = new Map<string, { expiresAt: number }>();
  readonly audits: FakeStatement[] = [];
  batchCalls = 0;
  prepareCalls = 0;

  prepare(query: string): D1PreparedStatement {
    this.prepareCalls += 1;
    return new FakeStatement(this, query) as unknown as D1PreparedStatement;
  }

  async run(statement: FakeStatement): Promise<D1Result> {
    if (statement.query.includes("relay_audit_receipts")) this.audits.push(statement);
    return d1Result(1);
  }

  async batch(statements: D1PreparedStatement[]): Promise<D1Result[]> {
    this.batchCalls += 1;
    const results: D1Result[] = [];
    for (const raw of statements) {
      const statement = raw as unknown as FakeStatement;
      if (statement.query.startsWith("DELETE FROM relay_nonces")) {
        const now = Number(statement.values[0]);
        for (const [hash, row] of this.nonces) {
          if (row.expiresAt <= now) this.nonces.delete(hash);
        }
        results.push(d1Result(0));
      } else if (statement.query.includes("INSERT OR IGNORE INTO relay_nonces")) {
        const hash = String(statement.values[0]);
        const now = Number(statement.values[3]);
        const expiresAt = Number(statement.values[4]);
        if (this.nonces.has(hash)) results.push(d1Result(0));
        else {
          this.nonces.set(hash, { expiresAt });
          results.push(d1Result(1));
        }
        if (!Number.isSafeInteger(now)) throw new Error("invalid test clock");
      } else {
        throw new Error("unexpected SQL in test fake");
      }
    }
    return results;
  }
}

function targetStub(overrides: Partial<ProjectionTargetRpc> = {}): ProjectionTargetRpc & { calls: Array<{ method: string; args: unknown[] }> } {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  return {
    calls,
    applyProjection: async (input) => { calls.push({ method: "applyProjection", args: [input] }); return APPLY_RECEIPT; },
    rollbackProjection: async (input) => { calls.push({ method: "rollbackProjection", args: [input] }); return ROLLBACK_RECEIPT; },
    inspectPublicSource: async (input) => { calls.push({ method: "inspectPublicSource", args: [input] }); return PRESENCE_RECEIPT; },
    verifyProjection: async (input) => { calls.push({ method: "verifyProjection", args: [input] }); return APPLY_RECEIPT; },
    publishEditorialArticle: async (input, overwrite) => {
      calls.push({ method: "publishEditorialArticle", args: [input, overwrite] });
      const checked = await validateEditorialPacket(input, new Date(NOW_MS).toISOString());
      if (!checked.ok) throw new Error("test editorial target fixture invalid");
      return {
        ok: true,
        status: "published",
        receipt: editorialReceipt(checked.payload_sha256, checked.review.reviewer, checked.payload.slug),
        diagnostics: editorialDiagnostics(),
      };
    },
    inspectEditorialArticle: async (slug) => { calls.push({ method: "inspectEditorialArticle", args: [slug] }); return { ok: false, code: "NOT_FOUND" }; },
    ...overrides,
  };
}

function editorialDiagnostics() {
  return {
    source_count: 1,
    distinct_source_urls: 1,
    distinct_source_metadata: 1,
    known_creator_count: 0,
    sources_without_known_creator: 1,
    cited_source_count: 1,
    section_count: 1,
  };
}

async function editorialPacket(reviewer: EditorialReviewer = "sol-max", slug = EDITORIAL_PAYLOAD.slug): Promise<Record<string, unknown>> {
  const payload = slug === EDITORIAL_PAYLOAD.slug ? EDITORIAL_PAYLOAD : { ...EDITORIAL_PAYLOAD, slug };
  const checked = await validateEditorialPayload(payload, new Date(NOW_MS).toISOString());
  if (!checked.ok) throw new Error("test editorial fixture invalid");
  return {
    payload,
    review: {
      reviewer,
      outcome: "pass",
      reviewed_at: "2026-09-03T00:00:00.000Z",
      payload_sha256: checked.payload_sha256,
    },
  };
}

function editorialReceipt(payloadSha256 = "f".repeat(64), reviewer: EditorialReviewer = "sol-max", slug = "relay-contract-note") {
  return {
    schema_version: "base2026.editorial-publication-receipt.v1",
    slug,
    revision: 1,
    payload_sha256: payloadSha256,
    public_path: `/blog/${slug}/`,
    published_at: "2026-09-03T00:00:00.000Z",
    updated_at: "2026-09-03T00:00:00.000Z",
    reviewer,
    reviewed_at: "2026-09-03T00:00:00.000Z",
    recorded_at: "2026-09-04T00:00:00.000Z",
  };
}

function env(target = targetStub(), db = new FakeD1()): RelayEnvironment & { target: typeof target; db: FakeD1 } {
  return {
    RELAY_ENABLED: "true",
    RELAY_HMAC_SECRET: SECRET,
    RELAY_DB: db as unknown as D1Database,
    PUBLIC_PROJECTION_TARGET: target,
    target,
    db,
  };
}

async function signedRequest(
  operation: RelayOperation,
  payload: unknown,
  options: {
    nonce?: string;
    timestampMs?: number;
    method?: string;
    pathname?: string;
    query?: string;
    bodyText?: string;
    contentSha256?: string;
    contentLength?: string;
    signature?: string;
    secret?: string;
    idempotencyKey?: string;
    contentType?: string;
  } = {},
): Promise<Request> {
  const pathname = options.pathname ?? RELAY_PATHS[operation];
  const bodyText = options.bodyText ?? JSON.stringify({
    schema_version: CROSS_ACCOUNT_PROJECTION_SCHEMA,
    operation,
    idempotency_key: options.idempotencyKey ?? "1".repeat(40),
    payload,
  });
  const body = new TextEncoder().encode(bodyText);
  const contentSha256 = await sha256Hex(body);
  const timestampMs = options.timestampMs ?? NOW_MS;
  const timestamp = String(Math.floor(timestampMs / 1_000));
  const nonce = options.nonce ?? "nonce-cross-account-0001";
  const method = options.method ?? "POST";
  const signature = await signHmacHex(options.secret ?? SECRET, buildAuthCanonical({
    method,
    pathname,
    timestamp,
    nonce,
    contentSha256,
    contentLength: body.byteLength,
  }));
  const headers = new Headers({
    accept: "application/json",
    "content-type": options.contentType ?? "application/json",
    "x-base2026-timestamp": timestamp,
    "x-base2026-nonce": nonce,
    "x-base2026-content-sha256": options.contentSha256 ?? contentSha256,
    "x-base2026-content-length": options.contentLength ?? String(body.byteLength),
    "x-base2026-signature": options.signature ?? signature,
  });
  return new Request(`https://relay.example${pathname}${options.query ?? ""}`, {
    method,
    headers,
    ...(method === "GET" || method === "HEAD" ? {} : { body }),
  });
}

async function jsonBody(response: Response): Promise<Record<string, unknown>> {
  return await response.json() as Record<string, unknown>;
}

describe("base2026 target-account projection relay", () => {
  it("verifies the BASE2026-HMAC-V1 canonical and maps apply to the fixed target RPC", async () => {
    const target = targetStub();
    const runtime = env(target);
    const response = await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD), runtime, NOW_MS);
    expect(response.status).toBe(200);
    expect(await jsonBody(response)).toEqual({
      schema_version: CROSS_ACCOUNT_PROJECTION_RESPONSE_SCHEMA,
      operation: "projection_apply",
      idempotency_key: "1".repeat(40),
      result: APPLY_RECEIPT,
    });
    expect(target.calls).toEqual([{ method: "applyProjection", args: [APPLY_PAYLOAD] }]);
    expect(runtime.db.nonces.size).toBe(1);
    expect(runtime.db.audits).toHaveLength(1);
  });

  it("rejects disabled mode, methods, paths, queries, and credential headers without D1 writes", async () => {
    const target = targetStub();
    const runtime = env(target);
    runtime.RELAY_ENABLED = "false";
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD), runtime, NOW_MS)).status).toBe(404);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { method: "GET" }), env(target), NOW_MS)).status).toBe(405);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { pathname: "/internal/base2026/projection/other" }), env(target), NOW_MS)).status).toBe(404);
    const queryRuntime = env(target);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { query: "?debug=1" }), queryRuntime, NOW_MS)).status).toBe(400);
    const credentialRequest = await signedRequest("projection_apply", APPLY_PAYLOAD);
    credentialRequest.headers.set("authorization", "Bearer should-not-cross-boundary");
    const credentialRuntime = env(target);
    expect((await handleRelayRequest(credentialRequest, credentialRuntime, NOW_MS)).status).toBe(400);
    expect(target.calls).toHaveLength(0);
    expect(runtime.db.batchCalls + queryRuntime.db.batchCalls + credentialRuntime.db.batchCalls).toBe(0);
  });

  it("rejects exact-envelope, body, hash, timestamp, and payload violations before replay reservation", async () => {
    const target = targetStub();
    const runtime = env(target);
    const extraEnvelope = JSON.stringify({
      schema_version: CROSS_ACCOUNT_PROJECTION_SCHEMA,
      operation: "projection_apply",
      idempotency_key: "1".repeat(40),
      payload: APPLY_PAYLOAD,
      private_source_text: "raw transcript",
    });
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { bodyText: extraEnvelope, nonce: "nonce-cross-account-0002" }), runtime, NOW_MS)).status).toBe(400);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0003", contentSha256: "f".repeat(64) }), runtime, NOW_MS)).status).toBe(401);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0004", contentLength: "1" }), runtime, NOW_MS)).status).toBe(401);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0005", timestampMs: NOW_MS - 301_000 }), runtime, NOW_MS)).status).toBe(401);
    expect((await handleRelayRequest(await signedRequest("projection_apply", { ...APPLY_PAYLOAD, private_source_text: "raw transcript" }, { nonce: "nonce-cross-account-0006" }), runtime, NOW_MS)).status).toBe(400);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0007", signature: "0".repeat(64) }), runtime, NOW_MS)).status).toBe(401);
    expect(target.calls).toHaveLength(0);
    expect(runtime.db.batchCalls).toBe(0);
  });

  it("rejects an oversized body before parsing or D1", async () => {
    const runtime = env();
    const oversized = "x".repeat(MAX_RELAY_BODY_BYTES + 1);
    const request = await signedRequest("projection_apply", APPLY_PAYLOAD, {
      bodyText: oversized,
      nonce: "nonce-cross-account-0010",
    });
    expect((await handleRelayRequest(request, runtime, NOW_MS)).status).toBe(413);
    expect(runtime.db.batchCalls).toBe(0);
  });

  it("uses a D1-backed unique nonce replay fence and allows a duplicate idempotency key with a fresh nonce", async () => {
    const target = targetStub();
    const runtime = env(target);
    const first = await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0011" });
    const replay = await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0011" });
    expect((await handleRelayRequest(first, runtime, NOW_MS)).status).toBe(200);
    const replayResponse = await handleRelayRequest(replay, runtime, NOW_MS);
    expect(replayResponse.status).toBe(409);
    expect((await jsonBody(replayResponse)).code).toBe("relay_nonce_replay");
    expect(target.calls).toHaveLength(1);

    const duplicate = await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0012" });
    expect((await handleRelayRequest(duplicate, runtime, NOW_MS)).status).toBe(200);
    expect(target.calls).toHaveLength(2);
    expect(runtime.db.nonces.size).toBe(2);
    expect(runtime.db.audits).toHaveLength(3);
  });

  it("reclaims an expired nonce only after its TTL and keeps audit rows append-only", async () => {
    const target = targetStub();
    const runtime = env(target);
    const first = await signedRequest("projection_presence", PRESENCE_PAYLOAD, { nonce: "nonce-cross-account-0013" });
    expect((await handleRelayRequest(first, runtime, NOW_MS)).status).toBe(200);
    const laterMs = NOW_MS + (RELAY_NONCE_TTL_SECONDS + 1) * 1_000;
    const second = await signedRequest("projection_presence", PRESENCE_PAYLOAD, {
      nonce: "nonce-cross-account-0013",
      timestampMs: laterMs,
    });
    expect((await handleRelayRequest(second, runtime, laterMs)).status).toBe(200);
    expect(target.calls).toHaveLength(2);
    expect(runtime.db.nonces.size).toBe(1);
    expect(runtime.db.audits).toHaveLength(2);
  });

  it("forwards both reviewer values and preserves the original receipt across fresh-nonce replay and inspect", async () => {
    const receipts = new Map<string, ReturnType<typeof editorialReceipt>>();
    const rpcCalls: string[] = [];
    const target = targetStub({
      publishEditorialArticle: async (input) => {
        rpcCalls.push("publishEditorialArticle");
        const checked = await validateEditorialPacket(input, new Date(NOW_MS).toISOString());
        if (!checked.ok) throw new Error("test editorial target fixture invalid");
        const existing = receipts.get(checked.payload.slug);
        const stored = existing ?? editorialReceipt(checked.payload_sha256, checked.review.reviewer, checked.payload.slug);
        if (!existing) receipts.set(checked.payload.slug, stored);
        return {
          ok: true,
          status: existing ? "already_published" : "published",
          receipt: stored,
          diagnostics: editorialDiagnostics(),
        };
      },
      inspectEditorialArticle: async (slug) => {
        rpcCalls.push("inspectEditorialArticle");
        const stored = receipts.get(slug);
        return stored ? { ok: true, receipt: stored } : { ok: false, code: "NOT_FOUND" };
      },
    });
    const runtime = env(target);
    const cases: Array<{
      reviewer: EditorialReviewer;
      slug: string;
      idempotencyKey: string;
      publishNonce: string;
      replayNonce: string;
      inspectNonce: string;
    }> = [
      {
        reviewer: "sol-max",
        slug: "relay-contract-note",
        idempotencyKey: "1".repeat(40),
        publishNonce: "nonce-editorial-sol-publish-01",
        replayNonce: "nonce-editorial-sol-replay-01",
        inspectNonce: "nonce-editorial-sol-inspect-01",
      },
      {
        reviewer: "gpt-6-astra",
        slug: "relay-contract-note-astra",
        idempotencyKey: "2".repeat(40),
        publishNonce: "nonce-editorial-astra-publish-01",
        replayNonce: "nonce-editorial-astra-replay-01",
        inspectNonce: "nonce-editorial-astra-inspect-01",
      },
    ];

    let originalSolReceipt: Record<string, unknown> | undefined;
    for (const current of cases) {
      const packet = await editorialPacket(current.reviewer, current.slug);
      const published = await handleRelayRequest(await signedRequest("editorial_publish", { packet }, {
        nonce: current.publishNonce,
        idempotencyKey: current.idempotencyKey,
      }), runtime, NOW_MS);
      expect(published.status).toBe(200);
      const publishedResult = (await jsonBody(published)).result as Record<string, unknown>;
      expect(publishedResult.status).toBe("published");
      const originalReceipt = publishedResult.receipt as Record<string, unknown>;
      expect(originalReceipt.reviewer).toBe(current.reviewer);
      if (current.reviewer === "sol-max") originalSolReceipt = originalReceipt;

      const replayed = await handleRelayRequest(await signedRequest("editorial_publish", { packet }, {
        nonce: current.replayNonce,
        idempotencyKey: current.idempotencyKey,
      }), runtime, NOW_MS);
      expect(replayed.status).toBe(200);
      const replayedResult = (await jsonBody(replayed)).result as Record<string, unknown>;
      expect(replayedResult.status).toBe("already_published");
      expect(replayedResult.receipt).toEqual(originalReceipt);

      const inspected = await handleRelayRequest(await signedRequest("editorial_inspect", { slug: current.slug }, {
        nonce: current.inspectNonce,
        idempotencyKey: `${Number(current.idempotencyKey[0]) + 2}`.repeat(40),
      }), runtime, NOW_MS);
      expect(inspected.status).toBe(200);
      const inspectedResult = (await jsonBody(inspected)).result as Record<string, unknown>;
      expect(inspectedResult.receipt).toEqual(originalReceipt);
    }

    const astraPacketForSolReceipt = await editorialPacket("gpt-6-astra", "relay-contract-note");
    const astraReplayOfSol = await handleRelayRequest(await signedRequest("editorial_publish", { packet: astraPacketForSolReceipt }, {
      nonce: "nonce-editorial-sol-legacy-astra-01",
      idempotencyKey: "8".repeat(40),
    }), runtime, NOW_MS);
    expect(astraReplayOfSol.status).toBe(200);
    const astraReplayResult = (await jsonBody(astraReplayOfSol)).result as Record<string, unknown>;
    expect(astraReplayResult.status).toBe("already_published");
    expect(astraReplayResult.receipt).toEqual(originalSolReceipt);

    const legacySolPacket = await editorialPacket("sol-max", "relay-contract-note-astra");
    const legacyReplay = await handleRelayRequest(await signedRequest("editorial_publish", { packet: legacySolPacket }, {
      nonce: "nonce-editorial-astra-legacy-sol-01",
      idempotencyKey: "7".repeat(40),
    }), runtime, NOW_MS);
    expect(legacyReplay.status).toBe(200);
    const legacyResult = (await jsonBody(legacyReplay)).result as Record<string, unknown>;
    expect(legacyResult.status).toBe("already_published");
    expect((legacyResult.receipt as Record<string, unknown>).reviewer).toBe("gpt-6-astra");
    expect(rpcCalls).toEqual([
      "publishEditorialArticle", "publishEditorialArticle", "inspectEditorialArticle",
      "publishEditorialArticle", "publishEditorialArticle", "inspectEditorialArticle",
      "publishEditorialArticle",
      "publishEditorialArticle",
    ]);
    expect(runtime.db.nonces.size).toBe(8);
    expect(runtime.db.audits).toHaveLength(8);
  });

  it("rejects an unsupported packet reviewer before RPC and rejects unsupported publish and inspect receipts", async () => {
    const validPacket = await editorialPacket("sol-max");
    const unsupportedPacket = {
      ...validPacket,
      review: { ...(validPacket.review as Record<string, unknown>), reviewer: "luna-max" },
    };
    const target = targetStub();
    const runtime = env(target);
    const packetResponse = await handleRelayRequest(await signedRequest("editorial_publish", { packet: unsupportedPacket }, {
      nonce: "nonce-editorial-invalid-packet-01",
    }), runtime, NOW_MS);
    expect(packetResponse.status).toBe(400);
    expect((await jsonBody(packetResponse)).code).toBe("relay_editorial_packet_invalid");
    expect(target.calls).toHaveLength(0);
    expect(runtime.db.batchCalls).toBe(0);

    const publishCalls: unknown[] = [];
    const invalidPublishTarget = targetStub({
      publishEditorialArticle: async (input) => {
        publishCalls.push(input);
        const checked = await validateEditorialPacket(input, new Date(NOW_MS).toISOString());
        if (!checked.ok) throw new Error("test editorial target fixture invalid");
        return {
          ok: true,
          status: "published",
          receipt: { ...editorialReceipt(checked.payload_sha256), reviewer: "luna-max" },
          diagnostics: editorialDiagnostics(),
        };
      },
    });
    const invalidPublishResponse = await handleRelayRequest(await signedRequest("editorial_publish", { packet: validPacket }, {
      nonce: "nonce-editorial-invalid-publish-receipt-01",
    }), env(invalidPublishTarget), NOW_MS);
    expect(invalidPublishResponse.status).toBe(502);
    expect((await jsonBody(invalidPublishResponse)).code).toBe("relay_editorial_receipt_mismatch");
    expect(publishCalls).toHaveLength(1);

    const inspectCalls: string[] = [];
    const invalidInspectTarget = targetStub({
      inspectEditorialArticle: async (slug) => {
        inspectCalls.push(slug);
        return { ok: true, receipt: { ...editorialReceipt(), reviewer: "luna-max" } };
      },
    });
    const invalidInspectResponse = await handleRelayRequest(await signedRequest("editorial_inspect", { slug: "relay-contract-note" }, {
      nonce: "nonce-editorial-invalid-inspect-receipt-01",
    }), env(invalidInspectTarget), NOW_MS);
    expect(invalidInspectResponse.status).toBe(502);
    expect((await jsonBody(invalidInspectResponse)).code).toBe("relay_editorial_receipt_mismatch");
    expect(inspectCalls).toEqual(["relay-contract-note"]);
  });

  it("maps all four projection RPC operations and both editorial operations", async () => {
    const target = targetStub();
    const runtime = env(target);
    const requests: Array<Promise<Request>> = [
      signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0021" }),
      signedRequest("projection_rollback", ROLLBACK_PAYLOAD, { nonce: "nonce-cross-account-0022" }),
      signedRequest("projection_presence", PRESENCE_PAYLOAD, { nonce: "nonce-cross-account-0023" }),
      signedRequest("projection_verify", VERIFY_PAYLOAD, { nonce: "nonce-cross-account-0024" }),
      editorialPacket().then((packet) => signedRequest("editorial_publish", { packet }, { nonce: "nonce-cross-account-0025" })),
      signedRequest("editorial_inspect", { slug: "relay-contract-note" }, { nonce: "nonce-cross-account-0026" }),
    ];
    const responses = await Promise.all((await Promise.all(requests)).map((request) => handleRelayRequest(request, runtime, NOW_MS)));
    expect(responses.map((response) => response.status)).toEqual([200, 200, 200, 200, 200, 200]);
    expect(new Set(target.calls.map((call) => call.method))).toEqual(new Set([
      "applyProjection",
      "rollbackProjection",
      "inspectPublicSource",
      "verifyProjection",
      "publishEditorialArticle",
      "inspectEditorialArticle",
    ]));
    expect(target.calls).toHaveLength(6);
    expect(target.calls.find((call) => call.method === "publishEditorialArticle")?.args[1]).toBeUndefined();
    expect(target.calls.find((call) => call.method === "inspectEditorialArticle")?.args).toEqual(["relay-contract-note"]);
  });

  it("fails closed without writing a nonce when the target method is unavailable, and records only safe data on target failure", async () => {
    const missingTarget = targetStub();
    delete (missingTarget as Partial<ProjectionTargetRpc>).applyProjection;
    const missingRuntime = env(missingTarget);
    expect((await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0031" }), missingRuntime, NOW_MS)).status).toBe(503);
    expect(missingRuntime.db.batchCalls).toBe(0);

    const failingTarget = targetStub({ applyProjection: async () => { throw new Error("private target failure"); } });
    const failingRuntime = env(failingTarget);
    const response = await handleRelayRequest(await signedRequest("projection_apply", APPLY_PAYLOAD, { nonce: "nonce-cross-account-0032" }), failingRuntime, NOW_MS);
    expect(response.status).toBe(503);
    expect((await jsonBody(response)).code).toBe("relay_target_unconfirmed");
    expect(failingRuntime.db.nonces.size).toBe(1);
    expect(failingRuntime.db.audits).toHaveLength(1);
  });

  it("never logs payloads, headers, or query strings", async () => {
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const runtime = env();
    const request = await signedRequest("projection_apply", APPLY_PAYLOAD, { query: "?private_token=do-not-log" });
    await handleRelayRequest(request, runtime, NOW_MS);
    expect(log).not.toHaveBeenCalled();
    expect(error).not.toHaveBeenCalled();
    log.mockRestore();
    error.mockRestore();
  });
});
