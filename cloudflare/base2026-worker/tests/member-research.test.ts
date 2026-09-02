/// <reference types="@cloudflare/vitest-pool-workers/types" />
import { applyD1Migrations, env, SELF } from "cloudflare:test";
import { betterAuth } from "better-auth";
import { testUtils } from "better-auth/plugins";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { handleMemberRequest } from "../src/member-research";
// @ts-expect-error Vite supplies the ?raw transform for local migration fixtures.
import betterAuthMigration from "../migrations-members/0001_better_auth.sql?raw";
// @ts-expect-error Vite supplies the ?raw transform for local migration fixtures.
import memberResearchMigration from "../migrations-members/0002_member_research.sql?raw";

const authDb = (env as unknown as { AUTH_DB: D1Database }).AUTH_DB;
const publicDb = (env as unknown as { DB: D1Database }).DB;
const memberEnv = env as unknown as {
  AUTH_DB: D1Database;
  DB: D1Database;
  BETTER_AUTH_ENABLED?: string;
  BETTER_AUTH_SECRET: string;
  GOOGLE_CLIENT_ID: string;
  GOOGLE_CLIENT_SECRET: string;
  MEMBER_AUTH_ENABLED: string;
  MEMBER_AUTH_LOCAL_DEV: string;
};

function responseCookies(response: Response): string[] {
  const headers = response.headers as Headers & {
    getSetCookie?: () => string[];
    getAll?: (name: string) => string[];
  };
  if (typeof headers.getSetCookie === "function") return headers.getSetCookie();
  if (typeof headers.getAll === "function") return headers.getAll("Set-Cookie");
  return [];
}

function splitMigration(text: unknown): string[] {
  return String(text)
    .split(/;\s*(?=(?:PRAGMA|CREATE|INSERT|ALTER|DROP|UPDATE|DELETE)\b)/iu)
    .map((query: string) => query.trim())
    .filter(Boolean);
}

const memberMigrations = [
  { name: "0001_better_auth.sql", queries: splitMigration(betterAuthMigration) },
  { name: "0002_member_research.sql", queries: splitMigration(memberResearchMigration) },
];

const testAuth = betterAuth({
  database: authDb,
  baseURL: "https://base2026.dev",
  basePath: "/api/auth",
  secret: memberEnv.BETTER_AUTH_SECRET,
  user: {
    changeEmail: { enabled: false },
    deleteUser: { enabled: false },
  },
  session: { cookieCache: { enabled: false }, freshAge: 10 * 60 },
  advanced: { useSecureCookies: true, ipAddress: { disableIpTracking: true } },
  plugins: [testUtils()],
});

type TestAuth = typeof testAuth;

async function testLogin(userId: string): Promise<string> {
  const context = await (testAuth as TestAuth).$context;
  const login = await (context as typeof context & { test: { login(opts: { userId: string }): Promise<{ headers: Headers }> } }).test.login({ userId });
  return login.headers.get("cookie") ?? "";
}

function request(path: string, cookie: string, init: RequestInit = {}): Request {
  const headers = new Headers(init.headers);
  if (cookie) headers.set("Cookie", cookie);
  if (init.method && init.method !== "GET" && !headers.has("Origin")) headers.set("Origin", "https://base2026.dev");
  return new Request(`https://base2026.dev${path}`, { ...init, headers });
}

async function json(response: Response): Promise<any> {
  return response.json();
}

async function createTestUser(id: string, email: string, name: string): Promise<void> {
  const context = await testAuth.$context;
  const helpers = (context as typeof context & { test: { createUser(overrides: Record<string, unknown>): { id: string; email: string; name: string }; saveUser(user: unknown): Promise<unknown> } }).test;
  await helpers.saveUser(helpers.createUser({ id, email, name, emailVerified: true }));
}

describe("member research CRUD on native local D1", () => {
  let userA: string;
  let userB: string;
  let cookieA = "";
  let cookieB = "";

  beforeAll(async () => {
    await applyD1Migrations(authDb, memberMigrations);
    await publicDb.prepare(`
      CREATE TABLE IF NOT EXISTS search_documents (
        id TEXT PRIMARY KEY NOT NULL,
        video_id TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        admission_state TEXT NOT NULL DEFAULT 'normal_public_card',
        public_surface TEXT NOT NULL DEFAULT 'main_search',
        full_transcript_public INTEGER NOT NULL DEFAULT 0
      )
    `).run();
    await publicDb.batch([
      publicDb.prepare("INSERT INTO search_documents (id, video_id, title, admission_state, public_surface, full_transcript_public) VALUES (?, ?, ?, ?, ?, ?)").bind("public-1", "1234567890", "Server-owned evidence title", "normal_public_card", "main_search", 0),
      publicDb.prepare("INSERT INTO search_documents (id, video_id, title, admission_state, public_surface, full_transcript_public) VALUES (?, ?, ?, ?, ?, ?)").bind("private-1", "1234567891", "Should not be saveable", "normal_public_card", "main_search", 1),
      publicDb.prepare("INSERT INTO search_documents (id, video_id, title, admission_state, public_surface, full_transcript_public) VALUES (?, ?, ?, ?, ?, ?)").bind("draft-1", "1234567892", "Draft title", "draft", "main_search", 0),
      publicDb.prepare("INSERT INTO search_documents (id, video_id, title, admission_state, public_surface, full_transcript_public) VALUES (?, ?, ?, ?, ?, ?)").bind("transcript-1", "1234567893", "Transcript-only surface", "normal_public_card", "full_transcript_public", 0),
    ]);
    userA = "member-test-user-a";
    userB = "member-test-user-b";
    await createTestUser(userA, "member-a@example.test", "Member A");
    await createTestUser(userB, "member-b@example.test", "Member B");
    cookieA = await testLogin(userA);
    cookieB = await testLogin(userB);
  });

  it("fails closed in production without a valid edge IP while accepting real IPv4 and IPv6", async () => {
    const productionEnv = { ...memberEnv, MEMBER_AUTH_LOCAL_DEV: "false" };
    const missing = await handleMemberRequest(
      new Request("https://base2026.dev/api/my-research/session"),
      productionEnv,
    );
    expect(missing?.status).toBe(503);
    for (const address of ["198.51.100.10", "2001:db8:1234:5678:abcd:ef01:2345:6789"]) {
      const response = await handleMemberRequest(
        new Request("https://base2026.dev/api/my-research/session", {
          headers: { "CF-Connecting-IP": address },
        }),
        productionEnv,
      );
      expect(response?.status).toBe(200);
    }
    for (const address of ["300.1.1.1", "198.51.100.10, 198.51.100.11"]) {
      const response = await handleMemberRequest(
        new Request("https://base2026.dev/api/my-research/session", {
          headers: { "CF-Connecting-IP": address },
        }),
        productionEnv,
      );
      expect(response?.status).toBe(503);
    }
    const localResponse = await SELF.fetch("https://base2026.dev/api/my-research/session");
    expect(localResponse.status).toBe(200);
  });

  it("runs synthetic login -> session -> save -> duplicate -> logout -> denied readback", async () => {
    const session = await SELF.fetch(request("/api/my-research/session", cookieA));
    expect(session.status).toBe(200);
    expect(await json(session)).toMatchObject({ enabled: true, user: { id: userA, email: "member-a@example.test" } });

    const collectionResponse = await SELF.fetch(request("/api/my-research/collections", cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Evidence A" }),
    }));
    expect(collectionResponse.status).toBe(201);
    const collection = (await json(collectionResponse)).collection;
    expect(collection).toMatchObject({ name: "Evidence A", itemCount: 0 });

    const itemResponse = await SELF.fetch(request(`/api/my-research/collections/${collection.id}/items`, cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: "evidence", referenceId: "1234567890", note: "First note" }),
    }));
    expect(itemResponse.status).toBe(201);
    const saved = (await json(itemResponse)).item;
    expect(saved).toMatchObject({
      collectionId: collection.id,
      kind: "evidence",
      referenceId: "1234567890",
      title: "Server-owned evidence title",
      url: "/sources/tiktok-video-1234567890",
      note: "First note",
    });

    const transcriptOnly = await SELF.fetch(request(`/api/my-research/collections/${collection.id}/items`, cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: "evidence", referenceId: "1234567893" }),
    }));
    expect(transcriptOnly.status).toBe(404);

    const duplicate = await SELF.fetch(request(`/api/my-research/collections/${collection.id}/items`, cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: "evidence", referenceId: "1234567890", note: "Attacker overwrite" }),
    }));
    expect(duplicate.status).toBe(200);
    expect(await json(duplicate)).toMatchObject({ created: false, item: { id: saved.id, note: "First note" } });

    const patchItem = await SELF.fetch(request(`/api/my-research/items/${saved.id}`, cookieA, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: "Updated note" }),
    }));
    expect(patchItem.status).toBe(200);
    expect(await json(patchItem)).toMatchObject({ item: { id: saved.id, note: "Updated note" } });
    const collectionRead = await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieA));
    expect(collectionRead.status).toBe(200);
    expect(await json(collectionRead)).toMatchObject({ collection: { id: collection.id }, items: [{ id: saved.id, note: "Updated note" }] });

    const patchCollection = await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieA, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Evidence A renamed" }),
    }));
    expect(patchCollection.status).toBe(200);
    expect(await json(patchCollection)).toMatchObject({ collection: { id: collection.id, name: "Evidence A renamed", itemCount: 1 } });
    const deleteItemResponse = await SELF.fetch(request(`/api/my-research/items/${saved.id}`, cookieA, { method: "DELETE" }));
    expect(deleteItemResponse.status).toBe(200);
    expect(await json(deleteItemResponse)).toEqual({ deleted: true });
    const emptyCollection = await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieA));
    expect(await json(emptyCollection)).toMatchObject({ collection: { itemCount: 0 }, items: [] });
    const deleteCollectionResponse = await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieA, { method: "DELETE" }));
    expect(deleteCollectionResponse.status).toBe(200);
    expect(await json(deleteCollectionResponse)).toEqual({ deleted: true });

    const logout = await SELF.fetch(request("/api/auth/sign-out", cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }));
    expect(logout.status).toBe(200);
    const denied = await SELF.fetch(request("/api/my-research/collections", cookieA));
    expect(denied.status).toBe(401);
    cookieA = await testLogin(userA);
  });

  it("keeps every collection, item, export, revoke, and delete boundary owner-scoped", async () => {
    const collectionResponse = await SELF.fetch(request("/api/my-research/collections", cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Owner boundary" }),
    }));
    const collection = (await json(collectionResponse)).collection;
    const itemResponse = await SELF.fetch(request(`/api/my-research/collections/${collection.id}/items`, cookieA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: "evidence", referenceId: "1234567890" }),
    }));
    const item = (await json(itemResponse)).item;

    expect((await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieB))).status).toBe(404);
    expect((await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieB, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: "Cross owner" }),
    }))).status).toBe(404);
    expect((await SELF.fetch(request(`/api/my-research/items/${item.id}`, cookieB, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ note: "Cross owner" }),
    }))).status).toBe(404);
    expect((await SELF.fetch(request(`/api/my-research/items/${item.id}`, cookieB, { method: "DELETE" }))).status).toBe(404);
    expect((await SELF.fetch(request(`/api/my-research/collections/${collection.id}`, cookieB, { method: "DELETE" }))).status).toBe(404);

    const exportB = await SELF.fetch(request("/api/my-research/export", cookieB));
    expect(exportB.status).toBe(200);
    const exportTextB = await exportB.text();
    expect(exportTextB).not.toContain("Owner boundary");
    expect(exportTextB).not.toContain(item.id);

    const revokeB = await SELF.fetch(request("/api/my-research/revoke-sessions", cookieB, { method: "POST", body: "{}", headers: { "Content-Type": "application/json" } }));
    expect(revokeB.status).toBe(200);
    const revokeCookies = responseCookies(revokeB);
    expect(revokeCookies.some((value) => /(?:__Secure-)?better-auth\.session_token=/u.test(value))).toBe(true);
    expect(revokeCookies.some((value) => /max-age=0/iu.test(value))).toBe(true);
    expect((await SELF.fetch(request("/api/my-research/session", cookieA))).status).toBe(200);
    expect(await json(await SELF.fetch(request("/api/my-research/session", cookieB)))).toMatchObject({ user: null, session: null });
    cookieB = await testLogin(userB);

    const stale = await authDb.prepare("UPDATE session SET createdAt = ? WHERE userId = ?").bind(Date.now() - 11 * 60 * 1_000, userA).run();
    expect(Number(stale.meta?.changes ?? 0)).toBeGreaterThan(0);
    const staleDelete = await SELF.fetch(request("/api/my-research/delete-account", cookieA, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmation: "DELETE" }),
    }));
    expect(staleDelete.status).toBe(403);
    expect(await json(staleDelete)).toMatchObject({ error: { code: "REAUTH_REQUIRED" } });
    cookieA = await testLogin(userA);
    const boundaryTimestamp = Date.now();
    await authDb.prepare("UPDATE session SET createdAt = ? WHERE userId = ?").bind(boundaryTimestamp - 10 * 60 * 1_000, userA).run();
    const clock = vi.spyOn(Date, "now").mockReturnValue(boundaryTimestamp);
    let boundaryDelete: Response | null = null;
    try {
      boundaryDelete = await handleMemberRequest(request("/api/my-research/delete-account", cookieA, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmation: "DELETE" }),
      }), memberEnv);
    } finally {
      clock.mockRestore();
    }
    expect(boundaryDelete).not.toBeNull();
    if (!boundaryDelete) throw new Error("boundary delete response missing");
    expect(boundaryDelete.status).toBe(403);
    expect(await json(boundaryDelete)).toMatchObject({ error: { code: "REAUTH_REQUIRED" } });
    cookieA = await testLogin(userA);
    const deletionTimestamp = Date.now();
    await authDb.batch([
      authDb.prepare("INSERT OR REPLACE INTO verification (id, identifier, value, expiresAt, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)").bind("delete-expired-state", "synthetic", "synthetic", deletionTimestamp - 1, deletionTimestamp - 10, deletionTimestamp - 10),
      authDb.prepare("INSERT OR REPLACE INTO verification (id, identifier, value, expiresAt, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)").bind("delete-live-state", "synthetic", "synthetic", deletionTimestamp + 60_000, deletionTimestamp, deletionTimestamp),
    ]);
    const deleteResponse = await SELF.fetch(request("/api/my-research/delete-account", cookieA, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmation: "DELETE" }),
    }));
    expect(deleteResponse.status).toBe(200);
    const deleteCookies = responseCookies(deleteResponse);
    expect(deleteCookies.some((value) => /(?:__Secure-)?better-auth\.session_token=/u.test(value))).toBe(true);
    expect(deleteCookies.some((value) => /max-age=0/iu.test(value))).toBe(true);
    expect((await SELF.fetch(request("/api/my-research/session", cookieA))).status).toBe(200);
    expect(await json(await SELF.fetch(request("/api/my-research/session", cookieA)))).toMatchObject({ user: null, session: null });
    expect((await authDb.prepare("SELECT COUNT(*) AS count FROM research_collections WHERE userId = ?").bind(userA).first<{ count: number }>())?.count).toBe(0);
    const remainingVerification = await authDb.prepare("SELECT id FROM verification WHERE id IN (?, ?) ORDER BY id").bind("delete-expired-state", "delete-live-state").all<{ id: string }>();
    expect(remainingVerification.results.map((row) => row.id)).toEqual(["delete-live-state"]);
    expect((await SELF.fetch(request("/api/my-research/session", cookieB))).status).toBe(200);
  });

  it("fails closed on malformed bodies, foreign origins, unsafe callbacks, and forbidden source rows", async () => {
    const forged = await SELF.fetch(new Request("https://base2026.dev/api/my-research/collections", {
      headers: { Cookie: "better-auth.session_token=forged-session-token" },
    }));
    expect(forged.status).toBe(401);
    await authDb.prepare("UPDATE session SET expiresAt = ? WHERE userId = ?").bind(Date.now() - 1_000, userB).run();
    const expired = await SELF.fetch(request("/api/my-research/collections", cookieB));
    expect(expired.status).toBe(401);
    cookieB = await testLogin(userB);

    const missingOrigin = await SELF.fetch(new Request("https://base2026.dev/api/my-research/collections", {
      method: "POST", headers: { "Content-Type": "application/json", Cookie: cookieB }, body: JSON.stringify({ name: "x" }),
    }));
    expect(missingOrigin.status).toBe(403);
    const foreignOrigin = await SELF.fetch(request("/api/my-research/collections", cookieB, {
      method: "POST", headers: { Origin: "https://evil.example", "Content-Type": "application/json" }, body: JSON.stringify({ name: "x" }),
    }));
    expect(foreignOrigin.status).toBe(403);
    const malformed = await SELF.fetch(request("/api/my-research/collections", cookieB, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: "x", userId: userA }),
    }));
    expect(malformed.status).toBe(400);
    const oversized = await SELF.fetch(request("/api/my-research/collections", cookieB, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "x".repeat(20_000) }),
    }));
    expect(oversized.status).toBe(400);
    const forbiddenSource = await SELF.fetch(request("/api/my-research/collections/not-a-real-collection/items", cookieB, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: "evidence", referenceId: "1234567891" }),
    }));
    expect(forbiddenSource.status).toBe(404);

    const badCallbackValues = [
      "https://evil.example/",
      "//evil.example/",
      "/workspace\\evil",
      "/workspace/../evil",
      "/workspace/\u0000",
    ];
    for (const callbackURL of badCallbackValues) {
      const response = await SELF.fetch(new Request("https://base2026.dev/api/auth/sign-in/social", {
        method: "POST",
        headers: { Origin: "https://base2026.dev", "Content-Type": "application/json" },
        body: JSON.stringify({ provider: "google", callbackURL }),
      }));
      expect(response.status).toBe(400);
    }
    const maliciousScopes = await SELF.fetch(new Request("https://base2026.dev/api/auth/sign-in/social", {
      method: "POST",
      headers: { Origin: "https://base2026.dev", "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "google", callbackURL: "/workspace/", scopes: ["https://mail.google.com/"] }),
    }));
    expect(maliciousScopes.status).toBe(400);
    const missingAuthOrigin = await SELF.fetch(new Request("https://base2026.dev/api/auth/sign-in/social", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
    }));
    expect(missingAuthOrigin.status).toBe(403);
  });

  it("returns only owned export fields and keeps provider/session metadata out", async () => {
    cookieB = await testLogin(userB);
    const account = await authDb.prepare(
      "INSERT INTO account (id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    ).bind("account-export-test", "https://accounts.google.com", "subject-export", "google", userB, "provider-access-secret", "provider-refresh-secret", "provider-id-secret", null, null, "openid email profile", null, Date.now(), Date.now()).run();
    expect(Number(account.meta?.changes ?? 0)).toBe(1);
    await authDb.prepare("UPDATE session SET ipAddress = ?, userAgent = ? WHERE userId = ?").bind("192.0.2.1", "synthetic-user-agent", userB).run();
    const response = await SELF.fetch(request("/api/my-research/export", cookieB));
    expect(response.status).toBe(200);
    expect(response.headers.get("content-disposition")).toContain("base2026-research-export.json");
    const text = await response.text();
    expect(text).toContain("member-b@example.test");
    expect(text).not.toContain("provider-access-secret");
    expect(text).not.toContain("provider-refresh-secret");
    expect(text).not.toContain("provider-id-secret");
    expect(text).not.toContain("192.0.2.1");
    expect(text).not.toContain("synthetic-user-agent");
    expect(text).not.toContain("accessToken");
    expect(text).not.toContain("refreshToken");
    expect(text).not.toContain("idToken");
  });
});
