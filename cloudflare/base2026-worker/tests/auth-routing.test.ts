import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import worker from "../src/index";
import * as members from "../src/member-research";

type WorkerEnv = Parameters<typeof worker.fetch>[1];

function fetchWorker(path: string, options: RequestInit = {}, overrides: Record<string, unknown> = {}) {
  return worker.fetch(
    new Request(`https://base2026.dev${path}`, options),
    overrides as unknown as WorkerEnv,
    {} as ExecutionContext,
  );
}

function expectPrivate(response: Response) {
  expect(response.headers.get("cache-control")).toBe("private, no-store");
  expect(response.headers.get("x-robots-tag")).toBe("noindex, nofollow");
  expect(response.headers.get("access-control-allow-origin")).toBeNull();
  expect(response.headers.get("access-control-allow-credentials")).toBeNull();
  expect(response.headers.get("referrer-policy")).toBe("no-referrer");
  expect(response.headers.get("x-frame-options")).toBe("DENY");
  expect(response.headers.get("content-security-policy")).toContain("frame-ancestors 'none'");
}

afterEach(() => vi.restoreAllMocks());

describe("member routing isolation in the public Worker", () => {
  it.each([
    "/api/auth/sign-in/social",
    "/api/auth/callback/google?code=synthetic-private-code&state=synthetic-state",
    "/api/auth/unlisted",
    "/api/my-research/session",
    "/api/my-research/collections",
  ])("fails closed without the private auth configuration: %s", async (path) => {
    const assetFetch = vi.fn();
    const response = await fetchWorker(path, {}, { ASSETS: { fetch: assetFetch } });
    expect(response.status).toBe(503);
    expectPrivate(response);
    expect(assetFetch).not.toHaveBeenCalled();
  });

  it("keeps unexpected private errors out of public CORS and request logs", async () => {
    vi.spyOn(members, "handleMemberRequest").mockRejectedValueOnce(new Error("synthetic-secret-do-not-log"));
    const errorLog = vi.spyOn(console, "error").mockImplementation(() => {});
    const response = await fetchWorker("/api/auth/callback/google?code=synthetic-secret-do-not-log");
    expect(response.status).toBe(503);
    expectPrivate(response);
    expect(await response.text()).not.toContain("synthetic-secret-do-not-log");
    expect(errorLog).not.toHaveBeenCalled();
  });

  it("preserves multiple auth cookies while overriding unsafe response headers", async () => {
    const headers = new Headers({
      "Cache-Control": "public, max-age=3600",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Credentials": "true",
    });
    headers.append("Set-Cookie", "synthetic-a=one; Secure; HttpOnly; SameSite=Lax; Path=/");
    headers.append("Set-Cookie", "synthetic-b=two; Secure; HttpOnly; SameSite=Lax; Path=/");
    vi.spyOn(members, "handleMemberRequest").mockResolvedValueOnce(new Response("{}", { headers }));
    const response = await fetchWorker("/api/auth/sign-in/social");
    expectPrivate(response);
    expect(response.headers.getSetCookie()).toHaveLength(2);
  });

  it("serves the private workspace with noindex, no-store and a same-origin script policy", async () => {
    const assetFetch = vi.fn(async () => new Response("<!doctype html><h1>My Research</h1>", {
      headers: { "Content-Type": "text/html", "Cache-Control": "public, max-age=60" },
    }));
    const response = await fetchWorker("/my-research/", {}, { ASSETS: { fetch: assetFetch } });
    expect(response.status).toBe(200);
    expectPrivate(response);
    expect(response.headers.get("content-security-policy")).toContain("script-src 'self'");
    expect(response.headers.get("content-security-policy")).not.toContain("unsafe-inline");
    expect(await response.text()).toContain("My Research");
    expect(assetFetch).toHaveBeenCalledOnce();
  });

  it.each(["/my-research", "/my-research/index.html"])("canonicalizes %s without caching", async (path) => {
    const response = await fetchWorker(`${path}?view=saved`);
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe("https://base2026.dev/my-research/?view=saved");
    expectPrivate(response);
  });

  it.each([
    ["/my-research/", "POST", 405],
    ["/my-research/unlisted", "GET", 404],
  ])("denies invalid private page requests %s %s", async (path, method, status) => {
    const assetFetch = vi.fn();
    const response = await fetchWorker(String(path), { method: String(method) }, { ASSETS: { fetch: assetFetch } });
    expect(response.status).toBe(status);
    expectPrivate(response);
    expect(assetFetch).not.toHaveBeenCalled();
  });

  it("keeps failed private asset loads private", async () => {
    const response = await fetchWorker("/my-research/", {}, {
      ASSETS: { fetch: async () => { throw new Error("synthetic-private-asset-error"); } },
    });
    expect(response.status).toBe(503);
    expectPrivate(response);
    expect(await response.text()).not.toContain("synthetic-private-asset-error");
  });

  it("does not change the public static asset response or fetch it through auth", async () => {
    const memberHandler = vi.spyOn(members, "handleMemberRequest");
    const response = await fetchWorker("/workspace/", {}, {
      ASSETS: { fetch: async () => new Response("protected-public-workspace", { headers: { "Cache-Control": "public, max-age=60" } }) },
    });
    expect(response.status).toBe(200);
    expect(await response.text()).toBe("protected-public-workspace");
    expect(response.headers.get("cache-control")).toBe("public, max-age=60");
    expect(response.headers.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    expect(response.headers.get("x-robots-tag")).toBeNull();
    expect(memberHandler).not.toHaveBeenCalled();
  });

  it("pins the reviewed production auth binding and keeps OAuth callback URLs out of invocation logs", () => {
    const config = JSON.parse(readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8"));
    expect(config.vars.MEMBER_AUTH_ENABLED).toBe("true");
    expect(config.d1_databases).toEqual(expect.arrayContaining([
      expect.objectContaining({
        binding: "AUTH_DB",
        database_name: "base2026-member-auth",
        migrations_dir: "migrations-members",
      }),
    ]));
    expect(config.observability.logs.invocation_logs).toBe(false);
    expect(config.assets.run_worker_first).toEqual(expect.arrayContaining(["/api/*", "/my-research", "/my-research/*"]));
  });
});
