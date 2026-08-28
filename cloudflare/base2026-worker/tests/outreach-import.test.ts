import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  BUNDLE_FILES,
  COLLECTION,
  EXPORT_SCHEMA,
  LANGUAGE,
  PUBLIC_POLICY,
  PUBLIC_RECORD_FIELDS,
  REQUIRED_SOURCE_HEADERS,
  buildImport,
  buildReceipt,
  loadBundle,
  makeBatches,
  normalizePublicUrl,
  prettyStableJson,
  renderRecordSql,
  sha256Bytes,
  validateRecordUniqueness,
  writeImportOutput,
// @ts-expect-error The production importer is intentionally dependency-free ESM JavaScript.
} from "../scripts/import-public-outreach.mjs";

type PublicRecord = Record<string, unknown> & {
  id: string;
  source_record_id: string;
  source_url: string;
};

const hash = (letter: string) => letter.repeat(64);

function record(sourceRecordId = "OUT-001", overrides: Record<string, unknown> = {}): PublicRecord {
  const value: PublicRecord = {
    id: `outreach-finding:${sourceRecordId}`,
    collection: COLLECTION,
    record_type: "finding",
    source_record_id: sourceRecordId,
    title: "Техническая ясность",
    summary: "Проверяемое публичное наблюдение.",
    tactic: "Разложить проверку на короткие шаги.",
    evidence_summary: "Источник показывает последовательность действий.",
    verdict: "Рекомендуется для дальнейшего изучения",
    source_url: `https://example.com/findings/${sourceRecordId.toLowerCase()}`,
    platform: "LinkedIn",
    author_name: "Анна Петрова",
    author_handle: "@anna_public",
    observed_at: "2026-08-21",
    score: 88,
    source_status: "Одобрено",
    topics: ["AI", "SEO"],
    lanes: ["proof", "technical"],
    cost: "Низкая",
    complexity: "Средняя",
    effect_speed: "Средняя",
    public_policy: PUBLIC_POLICY,
    reviewed_at: "2026-08-21T12:00:00Z",
    source_hash: hash("a"),
    dedup_key: hash(sourceRecordId === "OUT-001" ? "b" : sourceRecordId === "OUT-002" ? "c" : "d"),
    language: LANGUAGE,
  };
  return { ...value, ...overrides };
}

function compactJsonl(rows: unknown[]): Buffer {
  return Buffer.from(rows.map((row) => JSON.stringify(row)).join("\n") + (rows.length ? "\n" : ""), "utf8");
}

function writeBundle(
  root: string,
  records: PublicRecord[] = [record()],
  rejects: Record<string, unknown>[] = [],
  manifestOverrides: Record<string, unknown> = {},
) {
  const recordsBytes = compactJsonl(records);
  const rejectsBytes = compactJsonl(rejects);
  const manifest = {
    schema: EXPORT_SCHEMA,
    collection: COLLECTION,
    tab: "01_Находки",
    deterministic: true,
    hash_algorithm: "sha256",
    input_sha256: hash("c"),
    input_hash: hash("c"),
    canonical_input_sha256: hash("d"),
    admission_sha256: hash("e"),
    records_sha256: sha256Bytes(recordsBytes),
    rejects_sha256: sha256Bytes(rejectsBytes),
    input_rows: records.length,
    admission_entries: records.length,
    record_count: records.length,
    reject_count: rejects.length,
    records: records.length,
    rejects: rejects.length,
    counts: {
      input_rows: records.length,
      admission_entries: records.length,
      records: records.length,
      rejects: rejects.length,
    },
    rejection_counts: Object.fromEntries(
      rejects.map((item) => [String(item.reason), rejects.filter((candidate) => candidate.reason === item.reason).length]),
    ),
    required_headers: [...REQUIRED_SOURCE_HEADERS],
    public_fields: [...PUBLIC_RECORD_FIELDS],
    files: [...BUNDLE_FILES],
    ...manifestOverrides,
  };
  writeFileSync(join(root, "outreach_records.jsonl"), recordsBytes);
  writeFileSync(join(root, "outreach_rejects.jsonl"), rejectsBytes);
  writeFileSync(join(root, "manifest.json"), prettyStableJson(manifest));
  return manifest;
}

function temporaryDirectory(name: string): string {
  return mkdtempSync(join(tmpdir(), `base2026-outreach-${name}-`));
}

describe("local Outreach D1 importer", () => {
  it("validates the bundle and emits deterministic bounded SQL and receipt output", () => {
    const firstInput = temporaryDirectory("input-a");
    const secondInput = temporaryDirectory("input-b");
    writeBundle(firstInput, [record("OUT-002"), record("OUT-001")]);
    writeBundle(secondInput, [record("OUT-002"), record("OUT-001")]);

    const first = buildImport({ inputDir: firstInput, batchSize: 1, maxSqlBytes: 32_768 });
    const second = buildImport({ inputDir: secondInput, batchSize: 1, maxSqlBytes: 32_768 });
    expect(first.records.map((item: PublicRecord) => item.source_record_id)).toEqual(["OUT-001", "OUT-002"]);
    expect(first.batches).toHaveLength(2);
    expect(first.receipt).toEqual(second.receipt);
    expect(first.receipt.migration).toMatchObject({
      file: "migrations-outreach/0001_outreach_search.sql",
      sha256: expect.stringMatching(/^[a-f0-9]{64}$/),
    });
    expect(first.batches.map((batch: { text: string }) => batch.text)).toEqual(
      second.batches.map((batch: { text: string }) => batch.text),
    );

    const firstOutput = temporaryDirectory("output-a");
    const secondOutput = temporaryDirectory("output-b");
    const firstTarget = join(firstOutput, "bundle");
    const secondTarget = join(secondOutput, "bundle");
    writeImportOutput(first, firstTarget);
    writeImportOutput(second, secondTarget);
    for (const file of ["batch-0001.sql", "batch-0002.sql", "receipt.json"]) {
      expect(readFileSync(join(firstTarget, file))).toEqual(readFileSync(join(secondTarget, file)));
    }
    expect(readFileSync(join(firstTarget, "batch-0001.sql"), "utf8")).toContain("ON CONFLICT(id) DO UPDATE");
    expect(readFileSync(join(firstTarget, "batch-0001.sql"), "utf8")).toContain("outreach_topics");
    expect(readFileSync(join(firstTarget, "batch-0001.sql"), "utf8")).toContain("outreach_lanes");
  });

  it("fails closed when a manifest hash or count does not match the bundle", () => {
    const hashInput = temporaryDirectory("bad-hash");
    writeBundle(hashInput, [record()], [], { records_sha256: hash("f") });
    expect(() => loadBundle(hashInput)).toThrow(/records_sha256 mismatch/);

    const countInput = temporaryDirectory("bad-count");
    writeBundle(countInput, [record()], [], { record_count: 2 });
    expect(() => loadBundle(countInput)).toThrow(/records\/rejects counts disagree/);

    const inputCount = temporaryDirectory("bad-input-count");
    writeBundle(inputCount, [record()], [], { input_rows: 2 });
    expect(() => loadBundle(inputCount)).toThrow(/input\/admission values disagree/);
  });

  it("rejects unknown or private record fields before SQL generation", () => {
    const input = temporaryDirectory("unknown-field");
    const privateRecord = { ...record(), private_notes: "do not publish" };
    writeBundle(input, [privateRecord]);
    expect(() => loadBundle(input)).toThrow(/invalid field allowlist/);
    expect(() => loadBundle(input)).toThrow(/private_notes/);
  });

  it("fails closed for duplicate IDs, source IDs, URLs, and semantic keys", () => {
    const duplicateId = temporaryDirectory("duplicate-id");
    writeBundle(duplicateId, [record(), record()]);
    expect(() => loadBundle(duplicateId)).toThrow(/duplicate id/);

    expect(() => validateRecordUniqueness([
      record("OUT-001"),
      { ...record("OUT-002"), id: "outreach-finding:OUT-002", source_record_id: "OUT-001" },
    ])).toThrow(/duplicate source_record_id/);

    const duplicateUrl = temporaryDirectory("duplicate-url");
    writeBundle(duplicateUrl, [record("OUT-001"), record("OUT-002", { source_url: record().source_url })]);
    expect(() => loadBundle(duplicateUrl)).toThrow(/duplicate source_url/);

    const duplicateSemantic = temporaryDirectory("duplicate-semantic");
    writeBundle(duplicateSemantic, [record(), record("OUT-002", { source_url: "https://example.com/findings/two", dedup_key: record().dedup_key })]);
    expect(() => loadBundle(duplicateSemantic)).toThrow(/duplicate dedup_key/);
  });

  it("escapes apostrophes and JSON list values in SQL", () => {
    const escaped = record("OUT-003", {
      title: "O'Reilly's finding",
      summary: "Apostrophe in the reviewed summary.",
      topics: ["AI", "Owner's proof"],
      lanes: ["growth", "O'Reilly"],
    });
    const sql = renderRecordSql(escaped);
    expect(sql).toContain("O''Reilly''s finding");
    expect(sql).toContain("Owner''s proof");
    expect(sql).toContain("O''Reilly");
    expect(sql).not.toContain("undefined");
  });

  it("enforces SQL batch bounds and refuses an existing output directory", () => {
    const input = temporaryDirectory("bounds");
    writeBundle(input, [record()]);
    const result = buildImport({ inputDir: input, batchSize: 1, maxSqlBytes: 32_768 });
    expect(makeBatches(result.records, { batchSize: 1, maxSqlBytes: 32_768 })[0].bytes).toBeLessThanOrEqual(32_768);

    const outputParent = temporaryDirectory("fail-closed");
    const target = join(outputParent, "output");
    writeImportOutput(result, target);
    const receiptBefore = readFileSync(join(target, "receipt.json"));
    expect(() => writeImportOutput(result, target)).toThrow(/must not already exist/);
    expect(readFileSync(join(target, "receipt.json"))).toEqual(receiptBefore);
  });

  it("supports dry-run parsing without creating an output bundle", () => {
    const input = temporaryDirectory("dry-run");
    writeBundle(input, [record()]);
    const result = buildImport({ inputDir: input });
    expect(result.receipt.deterministic).toBe(true);
    expect(result.batches).toHaveLength(1);
  });

  it("rejects malformed timestamps, oversized public excerpts, and literal IP URLs", () => {
    const badTimestamp = temporaryDirectory("bad-timestamp");
    writeBundle(badTimestamp, [record("OUT-001", { reviewed_at: "2026-02-30T12:00:00Z" })]);
    expect(() => loadBundle(badTimestamp)).toThrow(/valid calendar timestamp/);

    const longExcerpt = temporaryDirectory("long-excerpt");
    writeBundle(longExcerpt, [record("OUT-001", { evidence_summary: "x".repeat(2_001) })]);
    expect(() => loadBundle(longExcerpt)).toThrow(/evidence_summary exceeds public limit/);

    const literalIp = temporaryDirectory("literal-ip");
    writeBundle(literalIp, [record("OUT-001", { source_url: "https://8.8.8.8/finding" })]);
    expect(() => loadBundle(literalIp)).toThrow(/public host/);
  });

  it("rejects contact data from every public record surface", () => {
    const candidates = [
      record("private@example.com"),
      record("OUT-001", { author_handle: "private@example.com" }),
      record("OUT-001", { platform: "private@example.com" }),
      record("OUT-001", { topics: ["AI", "private@example.com"] }),
      record("OUT-001", { lanes: ["growth", "private@example.com"] }),
      record("OUT-001", { source_url: "https://example.com/finding?contact=private%40example.com" }),
      record("OUT-001", { source_url: "https://example.com/finding?phone=%2B1+212+555+0123" }),
      record("OUT-001", { source_url: "https://example.com/finding?contact=user%2540example.com" }),
      record("OUT-001", { source_url: "https://example.com/finding?phone=%252B1%2520212%2520555%25200123" }),
      record("OUT-001", { summary: "Call +1 212 555 0123 for private details." }),
      record("OUT-001", { summary: "Call 555-1234 for private details." }),
      record("OUT-001", { summary: "Call (212) 555-0123 for private details." }),
      record("OUT-001", { summary: "Call 1 (212) 555-0123 for private details." }),
      record("OUT-001", { summary: "Call +44 20 7946 0958 for private details." }),
      record("OUT-001", { author_handle: "user@пример.рф" }),
      record("OUT-001", { summary: "Скрытый адрес: пользователь@example.com" }),
    ];
    for (const candidate of candidates) {
      expect(() => renderRecordSql(candidate)).toThrow(/forbidden (email address|phone number)/);
    }

    expect(() => renderRecordSql(record("OUT-001", {
      author_handle: "@anna.public",
      source_url: "https://www.tiktok.com/@anna.public/video/1234567890123456789",
    }))).not.toThrow();
    expect(() => renderRecordSql(record("XGS-20260725-001"))).not.toThrow();
    expect(() => renderRecordSql(record("OUT-001", {
      summary: "Pin geodaddy-mcp@0.2.2 for the test.",
    }))).not.toThrow();
    expect(() => renderRecordSql(record("OUT-001", {
      summary: "Checked 2026-08-02 19:50; Codex 0.147.0; issue 30377; issue #36373 (2026-07-31); v2.2.4 (2026-07-20); ratio 0.1005 (-5.74%).",
    }))).not.toThrow();
  });

  it("uses the exporter-compatible WHATWG URL normalization contract", () => {
    expect(normalizePublicUrl("https://example.com/a/../b")).toBe("https://example.com/b");
    expect(normalizePublicUrl("https://example.com/a/%2e%2e/b")).toBe("https://example.com/b");
    expect(normalizePublicUrl("https://example.com/?x=%7e")).toBe("https://example.com/?x=%7E");
    expect(normalizePublicUrl("https://example.com/?x=~")).toBe("https://example.com/?x=%7E");
    expect(normalizePublicUrl("https://example.com/?z=2&a=1")).toBe("https://example.com/?a=1&z=2");
  });
});
