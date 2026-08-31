import { execFile } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, statSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { EDITORIAL_SCHEMA, validateEditorialPayload, type EditorialPayload, type EditorialReview } from "../src/editorial";

const CLI = fileURLToPath(new URL("../scripts/editorial-packet.mjs", import.meta.url));
let scratch: string;

beforeEach(() => { scratch = mkdtempSync(join(realpathSync(tmpdir()), "base2026-editorial-cli-")); });
afterEach(() => { rmSync(scratch, { recursive: true, force: true }); });

function ago(minutes: number): string { return new Date(Date.now() - minutes * 60_000).toISOString(); }

function payload(): EditorialPayload {
  return {
    schema_version: EDITORIAL_SCHEMA,
    kind: "source_based_article",
    slug: "tracing-editorial-evidence",
    revision: 1,
    title: "A careful editorial reading path",
    description: "A small public note with two cited documents and explicit review boundaries.",
    lede: "Readers can inspect the documents linked beside an editorial observation.",
    category: "Research notes",
    tags: ["Evidence"],
    published_at: ago(240),
    updated_at: ago(180),
    author: { name: "Alex Yarosh" },
    ai_assistance_disclosure: "Prepared with AI assistance and separate editorial review.",
    sources: [
      { id: "cloudflare", url: "https://developers.cloudflare.com/d1/worker-api/d1-database/", title: "D1 database methods", creator: "Cloudflare", checked_at: ago(120) },
      { id: "sqlite", url: "https://www.sqlite.org/lang_transaction.html", title: "SQLite transactions", checked_at: ago(120) },
    ],
    sections: [{ id: "reading-path", heading: "Keep the reading path visible", blocks: [
      { type: "paragraph", text: "The linked documents provide a starting point for inspecting these observations.", citation_ids: ["cloudflare", "sqlite"] },
    ] }],
    related_paths: ["/blog", "/opt-out"],
  };
}

interface ProcessResult { status: number; stdout: string; stderr: string }

function node(args: string[]): Promise<ProcessResult> {
  return new Promise((resolve, reject) => {
    execFile(process.execPath, args, { cwd: scratch, encoding: "utf8", timeout: 15_000, maxBuffer: 64 * 1024 }, (error, stdout, stderr) => {
      if (error && typeof error.code !== "number") { reject(error); return; }
      resolve({ status: typeof error?.code === "number" ? error.code : 0, stdout, stderr });
    });
  });
}

function cli(args: string[]): Promise<ProcessResult> { return node([CLI, ...args]); }

function file(name: string, value: unknown): string {
  const path = join(scratch, name);
  writeFileSync(path, JSON.stringify(value, null, 2));
  return path;
}

async function fixtures(candidate = payload()) {
  const validated = await validateEditorialPayload(candidate, new Date().toISOString());
  if (!validated.ok) throw new Error("invalid CLI test fixture");
  // Synthetic test review data, supplied as an independent input file. The
  // CLI itself must never generate these fields or infer editorial approval.
  const review: EditorialReview = { reviewer: "sol-max", outcome: "pass", reviewed_at: ago(60), payload_sha256: validated.payload_sha256 };
  return {
    candidate, review, validated,
    draftPath: file("draft.json", candidate),
    reviewPath: file("review.json", review),
    outPath: join(scratch, "reviewed-packet.json"),
  };
}

function packArgs(input: { draftPath: string; reviewPath: string; outPath: string }): string[] {
  return ["pack", "--payload", input.draftPath, "--review", input.reviewPath, "--out", input.outPath];
}

function failure(result: ProcessResult, code: string) {
  expect(result.status).toBe(1);
  expect(result.stdout).toBe("");
  const receipt = JSON.parse(result.stderr);
  expect(receipt).toMatchObject({ ok: false, code });
  expect(result.stderr.trim().split("\n")).toHaveLength(1);
  return receipt;
}

describe("local editorial packet CLI", () => {
  it("validates a guide's fixed topic canonical without minting a review or claiming live evidence health", async () => {
    const candidate = payload();
    candidate.kind = "evidence_guide";
    candidate.slug = "internal-linking";
    candidate.sources = [{
      id: "source-example", url: "https://base2026.dev/sources/tiktok-video-1234567890123456789",
      title: "Synthetic source for a structural CLI test", checked_at: ago(120),
    }];
    candidate.sections = [{ id: "inspect", heading: "Inspect the target", blocks: [{
      type: "paragraph", text: "Inspect the incoming links before making a change.", citation_ids: ["source-example"],
    }] }];
    candidate.evidence = { user_task: "Check a proposed internal link.", dependencies: [{
      citation_id: "source-example", document_id: "chunk-transcript-1234567890123456789-0000",
      source_id: "tiktok:example:1234567890123456789", document_sha256: "a".repeat(64),
      quote: "Inspect the incoming links.", relation: "direct",
    }] };
    const draftPath = file("guide.json", candidate);
    const checked = await validateEditorialPayload(candidate, new Date().toISOString());
    expect(checked.ok).toBe(true);
    if (!checked.ok) return;
    const result = await cli(["validate", "--payload", draftPath]);
    expect(result.status).toBe(0);
    expect(result.stderr).toBe("");
    expect(JSON.parse(result.stdout)).toEqual({
      ok: true, payload_sha256: checked.payload_sha256,
      public_path: "/topics/internal-linking", diagnostics: checked.diagnostics,
    });
    expect(result.stdout).not.toContain("reviewer");
    expect(result.stdout).not.toContain(candidate.evidence.dependencies[0].quote);
    expect(readdirSync(scratch)).toEqual(["guide.json"]);
  });

  it("validates from another working directory and prints only safe hash/counts/canonical path", async () => {
    const candidate = payload();
    const draftPath = file("draft.json", candidate);
    const original = readFileSync(draftPath, "utf8");
    const checked = await validateEditorialPayload(candidate, new Date().toISOString());
    const result = await cli(["validate", "--payload", draftPath]);
    expect(result.status).toBe(0);
    expect(result.stderr).toBe("");
    expect(checked.ok).toBe(true);
    if (!checked.ok) return;
    expect(JSON.parse(result.stdout)).toEqual({
      ok: true, payload_sha256: checked.payload_sha256, public_path: "/blog/tracing-editorial-evidence/", diagnostics: checked.diagnostics,
    });
    expect(result.stdout).not.toContain(candidate.title);
    expect(result.stdout).not.toContain(candidate.sources[0].url);
    expect(result.stdout).not.toContain("reviewer");
    expect(readFileSync(draftPath, "utf8")).toBe(original);
    expect(readdirSync(scratch)).toEqual(["draft.json"]);
  });

  it("packs only the normalized payload and externally supplied exact review into a new private file", async () => {
    const candidate = payload();
    candidate.published_at = candidate.published_at.replace("Z", "+00:00");
    candidate.sources[0].url = "https://DEVELOPERS.CLOUDFLARE.COM:443/d1/worker-api/d1-database/";
    const input = await fixtures(candidate);
    const reviewedAt = input.review.reviewed_at;
    input.review.reviewed_at = reviewedAt.replace("Z", "+00:00");
    file("review.json", input.review);
    const draftBefore = readFileSync(input.draftPath, "utf8");
    const reviewBefore = readFileSync(input.reviewPath, "utf8");
    const result = await cli(packArgs(input));
    expect(result.status).toBe(0);
    expect(result.stderr).toBe("");
    expect(JSON.parse(result.stdout)).toEqual({
      ok: true, status: "packed", payload_sha256: input.validated.payload_sha256,
      public_path: "/blog/tracing-editorial-evidence/", output_path: input.outPath, packet_bytes: statSync(input.outPath).size,
    });
    expect(JSON.parse(readFileSync(input.outPath, "utf8"))).toEqual({
      payload: input.validated.payload, review: { ...input.review, reviewed_at: reviewedAt },
    });
    expect(statSync(input.outPath).mode & 0o777).toBe(0o600);
    expect(readFileSync(input.draftPath, "utf8")).toBe(draftBefore);
    expect(readFileSync(input.reviewPath, "utf8")).toBe(reviewBefore);
    expect(result.stdout).not.toContain(candidate.title);
    expect(result.stdout).not.toContain("published");
    expect(readdirSync(scratch).sort()).toEqual(["draft.json", "review.json", "reviewed-packet.json"]);
  });

  it("rejects a payload changed after the supplied review hash was produced", async () => {
    const input = await fixtures();
    input.candidate.title = "A change the reviewer has not approved";
    file("draft.json", input.candidate);
    const result = await cli(packArgs(input));
    expect(failure(result, "EDITORIAL_CLI_VALIDATION_FAILED").issues).toEqual([{ code: "EDITORIAL_REVIEW_HASH_MISMATCH", field: "review.payload_sha256" }]);
    expect(result.stderr).not.toContain(input.candidate.title);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it.each(["updated_at", "checked_at"])("rejects stale review for %s even when its hash matches", async (field) => {
    const candidate = payload();
    if (field === "updated_at") candidate.updated_at = ago(30);
    else candidate.sources[0].checked_at = ago(30);
    const input = await fixtures(candidate);
    const result = await cli(packArgs(input));
    expect(failure(result, "EDITORIAL_CLI_VALIDATION_FAILED").issues).toEqual([{ code: "EDITORIAL_REVIEW_STALE", field: "review.reviewed_at" }]);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it("uses the actual clock and refuses unreasonable future review timestamps", async () => {
    const input = await fixtures();
    input.review.reviewed_at = ago(-10);
    file("review.json", input.review);
    expect(failure(await cli(packArgs(input)), "EDITORIAL_CLI_VALIDATION_FAILED").issues).toEqual([{ code: "EDITORIAL_TIMESTAMP_FUTURE", field: "review.reviewed_at" }]);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it.each([
    ["reviewer", "another-reviewer", "EDITORIAL_REVIEW_REQUIRED"],
    ["outcome", "fail", "EDITORIAL_REVIEW_REQUIRED"],
    ["payload_sha256", "a".repeat(64), "EDITORIAL_REVIEW_HASH_MISMATCH"],
    ["approval", true, "EDITORIAL_UNSUPPORTED_FIELDS"],
  ])("never replaces invalid supplied review field %s with approval", async (key, value, code) => {
    const input = await fixtures();
    file("review.json", { ...input.review, [key as string]: value });
    expect(failure(await cli(packArgs(input)), "EDITORIAL_CLI_VALIDATION_FAILED").issues[0].code).toBe(code);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it("does not fill missing review fields", async () => {
    const input = await fixtures();
    file("review.json", { payload_sha256: input.review.payload_sha256 });
    expect(failure(await cli(packArgs(input)), "EDITORIAL_CLI_VALIDATION_FAILED").issues).toEqual([{ code: "EDITORIAL_UNSUPPORTED_FIELDS", field: "review" }]);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it.each([
    [], ["publish"], ["validate", "--force"],
    ["validate", "--payload", "/abs/draft.json", "--review", "/abs/review.json"],
    ["validate", "--payload=/abs/draft.json"],
    ["pack", "--payload", "/abs/draft.json", "--out", "/abs/packet.json"],
    ["pack", "--payload", "/abs/draft.json", "--review", "/abs/review.json", "--force", "/abs/packet.json"],
    ["pack", "--payload", "/abs/draft.json", "--payload", "/abs/review.json", "--out", "/abs/packet.json"],
    ["pack", "--payload", "/abs/draft.json", "--auto-review", "/abs/review.json", "--out", "/abs/packet.json"],
    ["pack", "--payload", "/abs/draft.json", "--now", "2030-01-01T00:00:00Z", "--out", "/abs/packet.json"],
  ])("refuses incomplete commands, duplicate/unknown flags and approval shortcuts: %j", async (...args) => {
    failure(await cli(args), "EDITORIAL_CLI_ARGUMENTS_INVALID");
    expect(readdirSync(scratch)).toEqual([]);
  });

  it.each(["draft.json", "~/draft.json", "https://example.com/draft.json", "/abs/../draft.json", "/abs/draft\n.json"])("refuses unsafe or nonabsolute path %j", async (path) => {
    failure(await cli(["validate", "--payload", path]), "EDITORIAL_CLI_PATH_INVALID");
  });

  it("refuses nonexistent review input without creating review or output files", async () => {
    const draftPath = file("draft.json", payload());
    const reviewPath = join(scratch, "not-reviewed.json");
    const outPath = join(scratch, "packet.json");
    failure(await cli(packArgs({ draftPath, reviewPath, outPath })), "EDITORIAL_CLI_INPUT_UNREADABLE");
    expect(readdirSync(scratch)).toEqual(["draft.json"]);
  });

  it.each([null, [], "not an object", 42, true])("refuses a non-object payload: %j", async (value) => {
    failure(await cli(["validate", "--payload", file("draft.json", value)]), "EDITORIAL_CLI_OBJECT_REQUIRED");
  });

  it.each([null, [], "not an object", 42, true])("refuses a non-object review: %j", async (value) => {
    const input = await fixtures();
    file("review.json", value);
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_OBJECT_REQUIRED");
    expect(existsSync(input.outPath)).toBe(false);
  });

  it.each(["payload", "review"])("refuses oversized raw %s bytes before parsing", async (field) => {
    const input = await fixtures();
    writeFileSync(field === "payload" ? input.draftPath : input.reviewPath, Buffer.alloc((field === "payload" ? 256 * 1024 : 4 * 1024) + 1, 0x20));
    expect(failure(await cli(packArgs(input)), "EDITORIAL_CLI_INPUT_TOO_LARGE").field).toBe(field);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it("retains the frozen canonical 128 KiB limit despite the larger raw JSON allowance", async () => {
    const candidate = payload();
    candidate.sections = Array.from({ length: 10 }, (_, index) => ({
      id: `section-${index}`, heading: "A bounded section", blocks: Array.from({ length: 12 }, () => ({
        type: "paragraph", text: "x".repeat(1_200), citation_ids: ["cloudflare", "sqlite"],
      })),
    }));
    const draftPath = file("draft.json", candidate);
    expect(statSync(draftPath).size).toBeLessThan(256 * 1024);
    expect(failure(await cli(["validate", "--payload", draftPath]), "EDITORIAL_CLI_VALIDATION_FAILED").issues[0].code).toBe("EDITORIAL_PAYLOAD_TOO_LARGE");
  });

  it.each(["payload", "review"])("refuses malformed UTF-8 in %s", async (field) => {
    const input = await fixtures();
    writeFileSync(field === "payload" ? input.draftPath : input.reviewPath, Buffer.from([0xff, 0xfe]));
    expect(failure(await cli(packArgs(input)), "EDITORIAL_CLI_JSON_INVALID").field).toBe(field);
  });

  it.each([
    '{"title":"MUST_NOT_ECHO_PRIVATE_FRAGMENT"',
    'process.stdout.write("MUST_NOT_ECHO_PRIVATE_FRAGMENT")',
  ])("never prints parse excerpts or executes source text from an input file", async (text) => {
    const draftPath = join(scratch, "draft.json");
    writeFileSync(draftPath, text);
    const result = await cli(["validate", "--payload", draftPath]);
    failure(result, "EDITORIAL_CLI_JSON_INVALID");
    expect(result.stdout + result.stderr).not.toContain("MUST_NOT_ECHO_PRIVATE_FRAGMENT");
  });

  it("conceals private values and unknown field names in structural errors", async () => {
    const candidate = { ...payload(), "MUST_NOT_ECHO_PRIVATE_FIELD": "MUST_NOT_ECHO_PRIVATE_VALUE" };
    const result = await cli(["validate", "--payload", file("draft.json", candidate)]);
    expect(failure(result, "EDITORIAL_CLI_VALIDATION_FAILED").issues).toEqual([{ code: "EDITORIAL_UNSUPPORTED_FIELDS", field: "payload" }]);
    expect(result.stdout + result.stderr).not.toContain("MUST_NOT_ECHO");
    const privateResult = await cli(["validate", "--payload", file("private.json", { ...payload(), title: "api_key: fake_fixture_value_not_a_real_secret" })]);
    expect(failure(privateResult, "EDITORIAL_CLI_VALIDATION_FAILED").issues[0].code).toBe("EDITORIAL_PRIVACY_REJECTED");
    expect(privateResult.stdout + privateResult.stderr).not.toContain("fake_fixture_value");
  });

  it.each(["payload", "review"])("refuses a symlink %s input", async (field) => {
    const input = await fixtures();
    const target = field === "payload" ? input.draftPath : input.reviewPath;
    const alias = join(scratch, "alias.json");
    const original = readFileSync(target, "utf8");
    symlinkSync(target, alias);
    if (field === "payload") input.draftPath = alias; else input.reviewPath = alias;
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_SYMLINK_REFUSED");
    expect(readFileSync(target, "utf8")).toBe(original);
    expect(existsSync(input.outPath)).toBe(false);
  });

  it("refuses input/output parent-directory symlink aliases", async () => {
    const input = await fixtures();
    const folder = join(scratch, "real-folder");
    const alias = join(scratch, "folder-alias");
    mkdirSync(folder);
    symlinkSync(folder, alias);
    writeFileSync(join(folder, "draft.json"), JSON.stringify(input.candidate));
    failure(await cli(["validate", "--payload", join(alias, "draft.json")]), "EDITORIAL_CLI_SYMLINK_REFUSED");
    input.outPath = join(alias, "packet.json");
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_SYMLINK_REFUSED");
    expect(existsSync(join(folder, "packet.json"))).toBe(false);
  });

  it("refuses nonregular input files", async () => {
    failure(await cli(["validate", "--payload", scratch]), "EDITORIAL_CLI_INPUT_NOT_REGULAR");
  });

  it("never overwrites an existing output or either input file", async () => {
    const input = await fixtures();
    writeFileSync(input.outPath, "existing output must remain intact");
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_OUTPUT_EXISTS");
    expect(readFileSync(input.outPath, "utf8")).toBe("existing output must remain intact");
    for (const path of [input.draftPath, input.reviewPath]) {
      const original = readFileSync(path, "utf8");
      failure(await cli(packArgs({ ...input, outPath: path })), "EDITORIAL_CLI_OUTPUT_EXISTS");
      expect(readFileSync(path, "utf8")).toBe(original);
    }
  });

  it.each([true, false])("refuses a leaf output symlink with existing target=%s", async (exists) => {
    const input = await fixtures();
    const target = join(scratch, "untouched.json");
    if (exists) writeFileSync(target, "untouched");
    symlinkSync(target, input.outPath);
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_OUTPUT_EXISTS");
    if (exists) expect(readFileSync(target, "utf8")).toBe("untouched");
    else expect(existsSync(target)).toBe(false);
  });

  it("does not create missing output directories", async () => {
    const input = await fixtures();
    input.outPath = join(scratch, "missing", "packet.json");
    failure(await cli(packArgs(input)), "EDITORIAL_CLI_OUTPUT_WRITE_FAILED");
    expect(existsSync(join(scratch, "missing"))).toBe(false);
  });

  it("allows only one successful pack when two subprocesses race for the same output", async () => {
    const input = await fixtures();
    const results = await Promise.all([cli(packArgs(input)), cli(packArgs(input))]);
    expect(results.map((result) => result.status).sort()).toEqual([0, 1]);
    failure(results.find((result) => result.status === 1)!, "EDITORIAL_CLI_OUTPUT_EXISTS");
    expect(JSON.parse(readFileSync(input.outPath, "utf8"))).toEqual({ payload: input.validated.payload, review: input.review });
  });

  it("does nothing when imported, even when argv looks like a valid pack command", async () => {
    const input = await fixtures();
    const result = await node(["--input-type=module", "--eval", `
      process.argv = ${JSON.stringify([process.execPath, CLI, ...packArgs(input)])};
      await import(${JSON.stringify(pathToFileURL(CLI).href)});
      process.stdout.write("import-only\\n");
    `]);
    expect(result).toEqual({ status: 0, stdout: "import-only\n", stderr: "" });
    expect(existsSync(input.outPath)).toBe(false);
    expect(readdirSync(scratch).sort()).toEqual(["draft.json", "review.json"]);
  });
});
