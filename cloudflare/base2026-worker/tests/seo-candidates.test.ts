/** Synthetic fixtures only. These tests never call the public service. */
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import { hashPublicEvidenceDocument, type PublicEvidenceDocument } from "../src/evidence-dependencies";

const moduleUrl = new URL("../scripts/seo-candidates.mjs", import.meta.url);
// Runtime import keeps the executable .mjs independently runnable in Node;
// the core TypeScript hash above remains the contract-test authority.
const scanner = await import(moduleUrl.href);
const NOW = "2026-08-30T23:00:00.000Z";
const ORIGIN = "https://base2026.dev";
const sha = (text: string) => createHash("sha256").update(text, "utf8").digest("hex");
type Row = PublicEvidenceDocument & {
  video_id: string; platform: string; source_type: string; public_policy: string; public_surface: string;
  [key: string]: unknown;
};

function row(number = 1, overrides: Record<string, unknown> = {}): Row {
  const video = (1234567890123456000n + BigInt(number)).toString();
  return {
    id: `chunk-transcript-polished-${video}-0000`, source_id: `tiktok:fixture_creator_${number}:${video}`,
    source_url: `https://www.tiktok.com/@fixture_creator_${number}/video/${video}`,
    creator_handle: `@fixture_creator_${number}`, title: "Synthetic title with e\u0301 and Café",
    body: "Synthetic public passage. Preserve spacing, punctuation and Unicode: e\u0301.\nSecond line.",
    full_transcript_public: false, admission_state: "normal_public_card", video_id: video,
    platform: "tiktok", source_type: "tiktok_video", public_policy: "search_passage", public_surface: "main_search",
    ...overrides,
  } as Row;
}

function search(rows: Row[] = [], overrides: Record<string, unknown> = {}, topic = "internal-linking") {
  const intent = scanner.RESEARCH_INTENTS.find((item: { id: string }) => item.id === topic);
  return { results: [{ indexUid: "base2026_public_tiktok", query: intent.query, limit: 100, offset: 0,
    estimatedTotalHits: rows.length, hits: rows, ...overrides }] };
}

function guide(overrides: Record<string, unknown> = {}) {
  return { slug: "internal-linking", title: "Synthetic guide title", description: "A fixture, not an outcome.",
    category: "Evidence guides", author: "Alex Yarosh", revision: 1,
    published_at: "2026-08-29T10:00:00.000Z", updated_at: "2026-08-30T10:00:00.000Z",
    public_path: "/topics/internal-linking", canonical_url: ORIGIN + "/topics/internal-linking",
    payload_sha256: "a".repeat(64), ...overrides };
}

function guideIndex(guides = [guide()], overrides: Record<string, unknown> = {}) {
  return { schema_version: "base2026.evidence-guide-index.v1",
    registered_topics: ["internal-linking", "content-freshness", "search-console-low-hanging-fruit", "schema-ai-citations", "llms-txt-risk"],
    guides, note: "Synthetic fixtures only", ...overrides };
}

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}

function queued(...responses: Response[]) {
  return vi.fn(async () => {
    const response = responses.shift();
    if (!response) throw new Error("Unexpected extra request in a synthetic test");
    return response;
  });
}

function child(args: string[]) {
  return new Promise<{ status: number; stdout: string; stderr: string }>((resolve, reject) => {
    execFile(process.execPath, args, { timeout: 10_000, maxBuffer: 32 * 1024, encoding: "utf8" }, (error, stdout, stderr) => {
      if (error && typeof error.code !== "number") { reject(error); return; }
      resolve({ status: typeof error?.code === "number" ? error.code : 0, stdout, stderr });
    });
  });
}

afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

describe("fixed research intent and public hash contracts", () => {
  it("has exactly the twelve owner-specified queries and a bounded topic/default/all parser", () => {
    const expected = [
      ["internal-linking", "internal"], ["ai-citation-tracking", "AI citation tracking"],
      ["ai-search-reporting", "AI search reporting"], ["search-console-low-hanging-fruit", "Search Console"],
      ["content-freshness", "content refresh"], ["service-page-seo", "service pages"],
      ["technical-seo-indexing", "technical SEO"], ["review-strategy", "local reviews"],
      ["brand-mentions-ai-visibility", "brand mentions"], ["schema-ai-citations", "schema markup"],
      ["llms-txt-risk", "llms.txt"], ["ecommerce-seo-collection-pages", "collection pages"],
    ];
    expect(scanner.RESEARCH_INTENTS.map((item: { id: string; query: string }) => [item.id, item.query])).toEqual(expected);
    expect(scanner.parseArguments([])).toEqual(["internal-linking"]);
    expect(scanner.parseArguments(["--all"])).toEqual(expected.map(([id]) => id));
    for (const [id] of expected) expect(scanner.parseArguments(["--topic", id])).toEqual([id]);
    for (const args of [["--topic"], ["--topic", "unknown"], ["--all", "--all"], ["--all", "--topic", "internal-linking"],
      ["--query", "private search"], ["--url", "https://other.example"], ["--out", "/tmp/scanner.json"],
      ["--topic=internal-linking"], ["--topic", "internal-linking", "--send"], ["--help"]]) {
      expect(() => scanner.parseArguments(args)).toThrow("ARGUMENTS_INVALID");
    }
  });

  it.each([false, true, 0, 1] as const)("matches the core eight-field hash for flag %s and exact Unicode", async (flag) => {
    const fixture = row(1, { full_transcript_public: flag, irrelevant_private_field: "never output this fixture marker" });
    expect(scanner.hashCandidateDocument(fixture)).toBe(await hashPublicEvidenceDocument(fixture));
    expect(scanner.hashCandidateDocument({ ...fixture, full_transcript_public: flag === true || flag === 1 }))
      .toBe(scanner.hashCandidateDocument(fixture));
    expect(scanner.hashCandidateDocument({ ...fixture, body: fixture.body + " " })).not.toBe(scanner.hashCandidateDocument(fixture));
    expect(scanner.hashCandidateDocument({ ...fixture, title: fixture.title.normalize("NFC") })).not.toBe(scanner.hashCandidateDocument(fixture));
    const reordered = Object.fromEntries(Object.entries(fixture).reverse());
    expect(scanner.hashCandidateDocument(reordered)).toBe(scanner.hashCandidateDocument(fixture));
  });

  it("refuses absent/coerced hash fields instead of guessing defaults", () => {
    for (const override of [{ body: null }, { title: undefined }, { source_id: 42 }, { full_transcript_public: "false" },
      { full_transcript_public: 2 }, { admission_state: null }, { body: "界".repeat(23_000) }, { title: "x".repeat(4_801) }]) {
      expect(() => scanner.hashCandidateDocument(row(1, override))).toThrow("DOCUMENT_INVALID");
    }
    expect(() => scanner.hashCandidateDocument(null)).toThrow("DOCUMENT_INVALID");
  });
});

describe("candidate summaries are deterministic research metadata", () => {
  it("sorts candidates and snapshot tuples, counts returned works/handles, and omits raw data", () => {
    const first = row(1, { body: "SYNTHETIC_BODY_NEVER_IN_OUTPUT", title: "private@example.invalid", extra_secret: "SYNTHETIC_EXTRA_MARKER" });
    const second = row(2, { body: "A different synthetic passage" });
    const third = row(3, { body: "Another synthetic passage", creator_handle: "" });
    const output = scanner.summarizeSearchResponse(search([third, second, first]), "internal-linking");
    expect(output).toMatchObject({ intent: "internal-linking", query: "internal", canonical: ORIGIN + "/topics/internal-linking",
      truncated: false, total_matches: 3, returned: 3, source_count: 3, video_count: 3, creator_handle_count: 2 });
    expect(output).toEqual(scanner.summarizeSearchResponse(search([first, third, second]), "internal-linking"));
    expect(output.snapshot_sha256).toBe(sha(JSON.stringify([first, second, third].map((item) => ({
      document_id: item.id, document_sha256: scanner.hashCandidateDocument(item),
    })))));
    for (const item of output.candidates) expect(Object.keys(item)).toEqual(["id", "source_id", "video_id", "creator_handle", "document_sha256"]);
    const serialized = JSON.stringify(output);
    for (const forbidden of [first.body, first.title, first.source_url, "SYNTHETIC_EXTRA_MARKER", '"body"', '"quote"', '"review"', '"autoPublish"']) {
      expect(serialized).not.toContain(forbidden);
    }
  });

  it("marks an over-100 window truncated and never calls it complete corpus coverage", () => {
    const fixtures = Array.from({ length: 100 }, (_, index) => row(index + 1, { body: `Synthetic passage ${index}` }));
    const output = scanner.summarizeSearchResponse(search(fixtures, { estimatedTotalHits: 101 }), "internal-linking");
    expect(output).toMatchObject({ truncated: true, total_matches: 101, returned: 100, scope: "query_matches_first_page" });
    expect(output.candidates).toHaveLength(100);
  });

  it("reports a genuine zero separately from missing or inconsistent windows", () => {
    expect(scanner.summarizeSearchResponse(search(), "internal-linking")).toMatchObject({ returned: 0, total_matches: 0, truncated: false });
    for (const override of [{ estimatedTotalHits: -1 }, { estimatedTotalHits: 0 }, { estimatedTotalHits: 1.5 },
      { estimatedTotalHits: "1" }, { estimatedTotalHits: 2 }, { estimatedTotalHits: 101 }, { estimatedTotalHits: Number.MAX_SAFE_INTEGER + 1 }]) {
      expect(() => scanner.summarizeSearchResponse(search([row()], override), "internal-linking")).toThrow("SEARCH_COUNT_MISMATCH");
    }
    const tooMany = Array.from({ length: 101 }, (_, index) => row(index + 1));
    expect(() => scanner.summarizeSearchResponse(search(tooMany), "internal-linking")).toThrow("SEARCH_COUNT_MISMATCH");
  });

  it("rejects duplicate document IDs even when their bodies match", () => {
    for (const duplicate of [row(), row(1, { body: "Conflicting synthetic body" })]) {
      expect(() => scanner.summarizeSearchResponse(search([row(), duplicate]), "internal-linking")).toThrow("DUPLICATE_DOCUMENT_ID");
    }
  });

  it("groups identical bodies across distinct documents/videos without inferring lineage", () => {
    const a = row(1, { body: "Shared synthetic passage." });
    const b = row(2, { body: a.body });
    const c = row(1, { id: a.id.replace("-0000", "-0001"), body: a.body });
    const different = row(3, { body: a.body + " " });
    const output = scanner.summarizeSearchResponse(search([different, c, b, a]), "internal-linking");
    expect(output).toMatchObject({ returned: 4, source_count: 3, creator_handle_count: 3 });
    expect(output.duplicate_content).toEqual([{ classification: "duplicate_content", lineage: "not_verified",
      body_sha256: sha(a.body), body_is_empty: false, document_ids: [a.id, c.id, b.id],
      source_ids: [a.source_id, b.source_id], video_ids: [a.video_id, b.video_id] }]);
    expect(JSON.stringify(output.duplicate_content)).not.toContain(a.body);
  });

  it("rejects unexpected result shapes, identity tuples and public-policy drift", () => {
    for (const input of [null, [], {}, { results: [] }, { results: [search().results[0], search().results[0]] },
      search([], { query: "unexpected" }), search([], { indexUid: "private" }), search([], { limit: 99 }), search([], { offset: 100 })]) {
      expect(() => scanner.summarizeSearchResponse(input, "internal-linking")).toThrow("SEARCH_RESPONSE_INVALID");
    }
    for (const override of [{ id: "unsafe@example.invalid" }, { source_id: "source-secret" },
      { video_id: "9876543210987654321" }, { creator_handle: "person@example.invalid" }]) {
      expect(() => scanner.summarizeSearchResponse(search([row(1, override)]), "internal-linking")).toThrow("DOCUMENT_IDENTITY_INVALID");
    }
    for (const override of [{ full_transcript_public: true }, { full_transcript_public: 1 }, { admission_state: "needs_review" },
      { platform: "other" }, { source_type: "raw" }, { public_policy: "raw" }, { public_surface: "private" }]) {
      expect(() => scanner.summarizeSearchResponse(search([row(1, override)]), "internal-linking")).toThrow("PUBLIC_BOUNDARY_INVALID");
    }
  });
});

describe("guide index metadata and registration", () => {
  it("keeps revision/hash/canonical metadata but strips free text and never invents registration", () => {
    const parsed = scanner.parseGuideIndex(guideIndex([guide({ title: "DO_NOT_COPY_TITLE", extra: "DO_NOT_COPY_EXTRA" })]));
    expect(parsed.guides[0]).toEqual({ slug: "internal-linking", revision: 1,
      published_at: "2026-08-29T10:00:00.000Z", updated_at: "2026-08-30T10:00:00.000Z",
      public_path: "/topics/internal-linking", canonical_url: ORIGIN + "/topics/internal-linking", payload_sha256: "a".repeat(64) });
    expect(parsed.registered_topics).toEqual(["content-freshness", "internal-linking", "llms-txt-risk", "schema-ai-citations", "search-console-low-hanging-fruit"]);
    expect(JSON.stringify(parsed)).not.toContain("DO_NOT_COPY");
    const noRegistry = guideIndex();
    delete (noRegistry as Record<string, unknown>).registered_topics;
    expect(scanner.parseGuideIndex(noRegistry).registered_topics).toBeNull();
  });

  it("rejects duplicate/malformed metadata, foreign canonicals and registry mismatches", () => {
    expect(() => scanner.parseGuideIndex(guideIndex([guide(), guide()]))).toThrow("GUIDE_INDEX_DUPLICATE");
    expect(() => scanner.parseGuideIndex(guideIndex([], { registered_topics: ["internal-linking", "internal-linking"] }))).toThrow("GUIDE_INDEX_DUPLICATE");
    expect(() => scanner.parseGuideIndex(guideIndex([guide()], { registered_topics: [] }))).toThrow("GUIDE_REGISTRY_MISMATCH");
    for (const override of [{ canonical_url: "https://other.example/topics/internal-linking" }, { public_path: "/blog/internal-linking/" },
      { revision: 0 }, { payload_sha256: "broken" }, { published_at: "2026-02-30T10:00:00.000Z" }, { updated_at: "2026-08-28T10:00:00.000Z" }]) {
      expect(() => scanner.parseGuideIndex(guideIndex([guide(override)]))).toThrow("GUIDE_INDEX_INVALID");
    }
    expect(() => scanner.parseGuideIndex({ schema_version: "unknown", guides: [] })).toThrow("GUIDE_INDEX_INVALID");
  });
});

describe("bounded public networking with synthetic fetch", () => {
  it("uses exactly the fixed GET and read-only POST, with no credentials, crop or redirects", async () => {
    const fetchImpl = vi.fn(async (url: string, init: RequestInit) => {
      expect(url === ORIGIN + "/api/guides" || url === ORIGIN + "/api/search/multi-search").toBe(true);
      expect(init).toMatchObject({ credentials: "omit", redirect: "error", cache: "no-store", referrerPolicy: "no-referrer" });
      expect(new Headers(init.headers).get("User-Agent")).toBe(scanner.USER_AGENT);
      expect(new Headers(init.headers).has("Authorization")).toBe(false);
      expect(new Headers(init.headers).has("Cookie")).toBe(false);
      expect(init.signal).toBeInstanceOf(AbortSignal);
      if (url.endsWith("/api/guides")) {
        expect(init.method).toBe("GET"); expect(init.body).toBeUndefined(); return json(guideIndex());
      }
      expect(init.method).toBe("POST");
      expect(JSON.parse(init.body as string)).toEqual({ queries: [{ indexUid: "base2026_public_tiktok", q: "internal",
        limit: 100, offset: 0, attributesToRetrieve: "*", attributesToHighlight: [], attributesToCrop: [] }] });
      return json(search([row()]));
    });
    const output = await scanner.scanCandidates([], { fetchImpl, now: () => NOW });
    expect(fetchImpl).toHaveBeenCalledTimes(2);
    expect(output).toMatchObject({ schema_version: scanner.SCAN_SCHEMA, checked_at: NOW, read_only: true, purpose: "research_delta_only" });
    expect(output.intents[0]).toMatchObject({ registered_guide: true, current_guide: { status: "listed", metadata: { revision: 1, payload_sha256: "a".repeat(64) } } });
    expect(output.requests.map((entry: { method: string }) => entry.method)).toEqual(["GET", "POST"]);
  });

  it("all is sequential, reads the index once and does not promote unregistered intents", async () => {
    let active = 0;
    let maximum = 0;
    const fetchImpl = vi.fn(async (url: string, init: RequestInit) => {
      active++; maximum = Math.max(maximum, active);
      await Promise.resolve();
      let response;
      if (url.endsWith("/api/guides")) response = json(guideIndex([]));
      else {
        const query = JSON.parse(init.body as string).queries[0].q;
        response = json(search([], { query }));
      }
      active--; return response;
    });
    const output = await scanner.scanCandidates(["--all"], { fetchImpl, now: () => NOW });
    expect(fetchImpl).toHaveBeenCalledTimes(13); expect(maximum).toBe(1);
    expect(output.intents).toHaveLength(12);
    expect(output.intents.find((entry: { intent: string }) => entry.intent === "content-freshness").registered_guide).toBe(true);
    expect(output.intents.find((entry: { intent: string }) => entry.intent === "ai-search-reporting")).toMatchObject({ registered_guide: false, current_guide: { status: "not_listed", metadata: null } });
  });

  it.each([[404, "not_deployed"], [503, "held_or_unavailable"]] as const)("guide HTTP%s is %s, not an empty healthy registry", async (status, label) => {
    const fetchImpl = queued(new Response("untrusted error body", { status }), json(search()));
    const output = await scanner.scanCandidates([], { fetchImpl, now: () => NOW });
    expect(fetchImpl).toHaveBeenCalledTimes(2);
    expect(output.guide_index).toEqual({ status: label, registered_topics: null, guides: null });
    expect(output.intents[0]).toMatchObject({ registered_guide: null, current_guide: { status: "unknown", metadata: null } });
    expect(output.requests[0]).toMatchObject({ http_status: status, response_bytes: 0 });
    expect(JSON.stringify(output)).not.toContain("untrusted error body");
  });

  it("stops on 429 without retrying the index or another intent", async () => {
    const limitedIndex = queued(new Response("retry-secret", { status: 429 }));
    await expect(scanner.scanCandidates(["--all"], { fetchImpl: limitedIndex })).rejects.toMatchObject({ code: "RATE_LIMITED", details: { http_status: 429 } });
    expect(limitedIndex).toHaveBeenCalledTimes(1);
    const limitedSearch = queued(json(guideIndex()), new Response("retry-secret", { status: 429 }));
    await expect(scanner.scanCandidates(["--all"], { fetchImpl: limitedSearch })).rejects.toMatchObject({ code: "RATE_LIMITED" });
    expect(limitedSearch).toHaveBeenCalledTimes(2);
  });

  it("makes other HTTP errors explicit, including an unavailable search response", async () => {
    for (const status of [400, 403, 404, 500, 503]) {
      const fetchImpl = queued(new Response("private provider detail", { status }));
      await expect(scanner.readPublicJson("search", { fetchImpl })).rejects.toMatchObject({ code: "HTTP_ERROR", details: { http_status: status } });
      expect(fetchImpl).toHaveBeenCalledTimes(1);
    }
    await expect(scanner.readPublicJson("guides", { fetchImpl: queued(new Response("failure", { status: 500 })) })).rejects.toMatchObject({ code: "HTTP_ERROR" });
  });

  it("refuses unauthorized endpoints/topics before fetch and refuses redirects or foreign responses", async () => {
    const fetchImpl = vi.fn();
    for (const endpoint of ["https://other.example", "/api/guides", "../private", "__proto__"]) {
      await expect(scanner.readPublicJson(endpoint, { fetchImpl })).rejects.toMatchObject({ code: "ENDPOINT_NOT_ALLOWED" });
    }
    await expect(scanner.readPublicJson("search", { topic: "private query", fetchImpl })).rejects.toMatchObject({ code: "ARGUMENTS_INVALID" });
    await expect(scanner.scanCandidates(["--url", "https://other.example"], { fetchImpl })).rejects.toMatchObject({ code: "ARGUMENTS_INVALID" });
    expect(fetchImpl).not.toHaveBeenCalled();
    const foreign = json(search()); Object.defineProperty(foreign, "url", { value: "https://other.example/private" });
    await expect(scanner.readPublicJson("search", { fetchImpl: queued(foreign) })).rejects.toMatchObject({ code: "RESPONSE_ORIGIN_INVALID" });
    const redirected = json(search()); Object.defineProperty(redirected, "redirected", { value: true });
    await expect(scanner.readPublicJson("search", { fetchImpl: queued(redirected) })).rejects.toMatchObject({ code: "RESPONSE_ORIGIN_INVALID" });
  });

  it("bounds both declared and streamed bytes, even without Content-Length", async () => {
    const declared = json(search()); declared.headers.set("Content-Length", String(scanner.SCAN_LIMITS.response_bytes + 1));
    await expect(scanner.readPublicJson("search", { fetchImpl: queued(declared) })).rejects.toMatchObject({ code: "RESPONSE_TOO_LARGE" });
    const large = new Response(new Uint8Array(scanner.SCAN_LIMITS.response_bytes + 1), { headers: { "Content-Type": "application/json" } });
    await expect(scanner.readPublicJson("search", { fetchImpl: queued(large) })).rejects.toMatchObject({ code: "RESPONSE_TOO_LARGE" });
    const badLength = json(search()); badLength.headers.set("Content-Length", "not-a-count");
    await expect(scanner.readPublicJson("search", { fetchImpl: queued(badLength) })).rejects.toMatchObject({ code: "RESPONSE_LENGTH_INVALID" });
  });

  it("rejects non-JSON and invalid UTF-8 without echoing parser/source details", async () => {
    const responses = [new Response("<html>SECRET_FIXTURE</html>"),
      new Response('{"SECRET_FIXTURE":', { headers: { "Content-Type": "application/json" } }),
      new Response(new Uint8Array([0xc3, 0x28]), { headers: { "Content-Type": "application/json" } })];
    for (const response of responses) {
      const failure = await scanner.readPublicJson("search", { fetchImpl: queued(response) }).catch((error: unknown) => error);
      expect(failure).toMatchObject({ code: "RESPONSE_NOT_JSON" });
      expect(JSON.stringify(failure)).not.toContain("SECRET_FIXTURE");
    }
    const failure = await scanner.readPublicJson("search", { fetchImpl: async () => { throw new Error("SECRET_FIXTURE"); } }).catch((error: unknown) => error);
    expect(failure).toMatchObject({ code: "REQUEST_FAILED" }); expect(JSON.stringify(failure)).not.toContain("SECRET_FIXTURE");
  });

  it.each(["fetch", "body"])("times out an uncooperative %s after exactly 18 seconds and does not retry", async (stage) => {
    vi.useFakeTimers();
    let signal: AbortSignal | null | undefined;
    const fetchImpl = vi.fn(async (_url: string, init: RequestInit) => {
      signal = init.signal;
      if (stage === "fetch") return new Promise<Response>(() => {});
      return new Response(new ReadableStream({ pull: () => new Promise(() => {}) }), { headers: { "Content-Type": "application/json" } });
    });
    const pending = scanner.readPublicJson("search", { fetchImpl });
    const assertion = expect(pending).rejects.toMatchObject({ code: "REQUEST_TIMEOUT" });
    await vi.advanceTimersByTimeAsync(18_000);
    await assertion;
    expect(signal?.aborted).toBe(true); expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
});

describe("explicit-main CLI boundary", () => {
  it("does no network or output when imported", async () => {
    const result = await child(["--input-type=module", "-e",
      `globalThis.fetch = () => { throw new Error('IMPORT_MUST_NOT_FETCH'); }; await import(${JSON.stringify(moduleUrl.href)});`]);
    expect(result).toEqual({ status: 0, stdout: "", stderr: "" });
    const source = readFileSync(moduleUrl, "utf8");
    expect(source).not.toMatch(/from\s+["']node:(?:fs|child_process|http|https|net)["']/u);
    expect(source).not.toContain("process.env");
    expect(source).toContain("if (import.meta.main)");
  });

  it("rejects unsafe CLI options with one sanitized stdout JSON receipt and no requests", async () => {
    const result = await child([fileURLToPath(moduleUrl), "--url", "https://other.example/?token=SECRET_FIXTURE"]);
    expect(result.status).toBe(1); expect(result.stderr).toBe("");
    expect(result.stdout.trim().split("\n")).toHaveLength(1);
    expect(JSON.parse(result.stdout)).toMatchObject({ schema_version: scanner.SCAN_SCHEMA, read_only: true,
      status: "error", error: { code: "ARGUMENTS_INVALID" } });
    expect(result.stdout).not.toContain("SECRET_FIXTURE");
  });
});
