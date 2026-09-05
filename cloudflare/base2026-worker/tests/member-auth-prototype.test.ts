/// <reference types="@cloudflare/vitest-pool-workers/types" />
import { applyD1Migrations, env, SELF } from "cloudflare:test";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { memberSessionRateKey } from "../src/member-research";
import { cleanupExpiredMemberVerification } from "../src/member-auth";
// @ts-expect-error Vite supplies the ?raw transform for local migration fixtures.
import betterAuthMigration from "../migrations-members/0001_better_auth.sql?raw";
// @ts-expect-error Vite supplies the ?raw transform for local migration fixtures.
import memberResearchMigration from "../migrations-members/0002_member_research.sql?raw";

const authDb = (env as unknown as { AUTH_DB: D1Database }).AUTH_DB;

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

interface SyntheticGoogleProfile {
  sub: string;
  email: string;
  name: string;
}

async function seedSavedResearch(userId: string, timestamp: number): Promise<void> {
  await authDb.batch([
    authDb.prepare(
      "INSERT INTO research_collections (id, userId, name, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
    ).bind(`${userId}-collection`, userId, "Existing research", timestamp, timestamp),
    authDb.prepare(
      "INSERT INTO research_items (id, userId, collectionId, kind, referenceId, title, url, note, createdAt, updatedAt) VALUES (?, ?, ?, 'evidence', ?, ?, ?, ?, ?, ?)",
    ).bind(`${userId}-item`, userId, `${userId}-collection`, "synthetic-public-reference", "Saved source", "https://base2026.dev/sources/synthetic", "Keep this private note", timestamp, timestamp),
  ]);
}

async function readSavedResearch(userId: string): Promise<unknown> {
  const collections = await authDb.prepare("SELECT * FROM research_collections WHERE userId = ? ORDER BY id").bind(userId).all();
  const items = await authDb.prepare("SELECT * FROM research_items WHERE userId = ? ORDER BY id").bind(userId).all();
  return { collections: collections.results, items: items.results };
}

async function completeSyntheticGoogleCallback(profile: SyntheticGoogleProfile, ip: string): Promise<{
  callback: Response;
  sessionCookie: string | undefined;
}> {
  const payload = {
    iss: "https://accounts.google.com",
    aud: "synthetic-google-client-id.apps.googleusercontent.com",
    sub: profile.sub,
    email: profile.email,
    email_verified: true,
    name: profile.name,
    picture: "https://example.test/avatar.svg",
  };
  const base64Url = (value: string): string => {
    const bytes = new TextEncoder().encode(value);
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/gu, "-").replace(/\//gu, "_").replace(/=+$/u, "");
  };
  const idToken = `${base64Url(JSON.stringify({ alg: "none", typ: "JWT" }))}.${base64Url(JSON.stringify(payload))}.synthetic-signature`;
  const originalFetch = globalThis.fetch;
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const target = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    if (target === "https://oauth2.googleapis.com/token") {
      expect(init?.method).toBe("POST");
      return new Response(JSON.stringify({
        access_token: "synthetic-access-token",
        refresh_token: "synthetic-refresh-token",
        id_token: idToken,
        token_type: "Bearer",
        scope: "openid email profile",
      }), { headers: { "Content-Type": "application/json" } });
    }
    return originalFetch(input, init);
  });

  try {
    const signIn = await SELF.fetch("https://base2026.dev/api/auth/sign-in/social", {
      method: "POST",
      headers: {
        Origin: "https://base2026.dev",
        "Content-Type": "application/json",
        "CF-Connecting-IP": ip,
      },
      body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
      redirect: "manual",
    });
    expect(signIn.status).toBe(200);
    const signInBody = await signIn.json() as { url?: string };
    const authorization = new URL(signInBody.url ?? "");
    const state = authorization.searchParams.get("state");
    expect(state).toBeTruthy();
    const signInCookies = responseCookies(signIn);
    const stateCookie = signInCookies.find((value) => /(?:__Secure-)?better-auth\.state=/u.test(value))?.match(/((?:__Secure-)?better-auth\.state=[^;]+)/u)?.[1];
    expect(stateCookie).toBeTruthy();

    const callback = await SELF.fetch(
      `https://base2026.dev/api/auth/callback/google?code=synthetic-code&state=${encodeURIComponent(state!)}`,
      { headers: { Cookie: stateCookie! }, redirect: "manual" },
    );
    const callbackCookies = responseCookies(callback);
    const sessionCookie = callbackCookies.find((value) => /(?:__Secure-)?better-auth\.session_token=/u.test(value))?.match(/((?:__Secure-)?better-auth\.session_token=[^;]+)/u)?.[1];
    return { callback, sessionCookie };
  } finally {
    fetchMock.mockRestore();
  }
}

beforeAll(async () => {
  await applyD1Migrations(authDb, memberMigrations);
});

describe("native D1 member auth prototype", () => {
  it("mounts Better Auth on the private D1 schema and returns a safe unauthenticated session", async () => {
    const response = await SELF.fetch("https://base2026.dev/api/my-research/session");
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toContain("private, no-store");
    expect(response.headers.get("x-robots-tag")).toBe("noindex, nofollow");
    await expect(response.json()).resolves.toEqual({
      enabled: true,
      user: null,
      session: null,
    });
  });

  it("produces a Google authorization redirect with the narrow online scope", async () => {
    const response = await SELF.fetch("https://base2026.dev/api/auth/sign-in/social", {
      method: "POST",
      headers: {
        Origin: "https://base2026.dev",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
      redirect: "manual",
    });
    // Better Auth returns the authorization URL as JSON while also setting a
    // Location header; clients may follow either representation.
    expect(response.status).toBe(200);
    const location = response.headers.get("location");
    expect(location).toBeTruthy();
    const authorization = new URL(location!);
    expect(authorization.origin).toBe("https://accounts.google.com");
    expect(authorization.pathname).toBe("/o/oauth2/v2/auth");
    expect(authorization.searchParams.get("scope")).toBe("openid email profile");
    expect(authorization.searchParams.get("access_type")).toBe("online");
    expect(authorization.searchParams.get("redirect_uri")).toBe("https://base2026.dev/api/auth/callback/google");
    expect(authorization.searchParams.get("state")).toBeTruthy();
    expect(authorization.searchParams.get("code_challenge")).toBeTruthy();
    expect(authorization.searchParams.get("code_challenge_method")).toBe("S256");
    expect(authorization.searchParams.get("include_granted_scopes")).toBeNull();
    expect(authorization.searchParams.toString()).not.toMatch(/gmail|drive|offline|id_token|access_token/iu);
  });

  it("uses native D1 rate storage for IPv6 auth requests without persisting the address", async () => {
    const headers = {
      Origin: "https://base2026.dev",
      "CF-Connecting-IP": "2001:db8:1234:5678:abcd:ef01:2345:6789",
      "Content-Type": "application/json",
    };
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const response = await SELF.fetch("https://base2026.dev/api/auth/sign-in/social", {
        method: "POST",
        headers,
        body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
        redirect: "manual",
      });
      expect(response.status).toBe(200);
    }
    const limited = await SELF.fetch("https://base2026.dev/api/auth/sign-in/social", {
      method: "POST",
      headers,
      body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
      redirect: "manual",
    });
    expect(limited.status).toBe(429);
    const keys = await authDb.prepare("SELECT key FROM member_rate_limits").all<{ key: string }>();
    expect(keys.results.length).toBeGreaterThan(0);
    expect(keys.results.map((row) => row.key).join(" ")).not.toContain("2001:db8:1234");
  });

  it("partitions session checks by coarse address for the 60-second window", () => {
    const first = new Request("https://base2026.dev/api/my-research/session", {
      headers: { "CF-Connecting-IP": "198.51.100.10" },
    });
    const sameNetwork = new Request("https://base2026.dev/api/my-research/session", {
      headers: { "CF-Connecting-IP": "198.51.100.240" },
    });
    const nextMinute = new Request("https://base2026.dev/api/my-research/session", {
      headers: { "CF-Connecting-IP": "198.51.100.10" },
    });
    expect(memberSessionRateKey(first)).toBe(memberSessionRateKey(sameNetwork));
    expect(memberSessionRateKey(first)).toBe(memberSessionRateKey(nextMinute));
    expect(memberSessionRateKey(first)).toContain("198.51.100.0/24");
    expect(memberSessionRateKey(first)).not.toContain("198.51.100.10");
    expect(memberSessionRateKey(new Request("https://base2026.dev/api/my-research/session"))).toBeNull();
  });

  it("denies an OAuth callback that has no Better Auth state", async () => {
    const response = await SELF.fetch(
      "https://base2026.dev/api/auth/callback/google?code=synthetic-code-without-state",
      { redirect: "manual" },
    );
    expect(response.status).toBeGreaterThanOrEqual(300);
    expect(response.status).toBeLessThan(400);
    expect(response.headers.get("location")).toContain("state_not_found");
    expect(response.headers.get("set-cookie") ?? "").not.toMatch(/session_token/iu);
  });

  it("cleans expired OAuth state in a bounded native-D1 batch", async () => {
    const timestamp = 18_000;
    await authDb.batch([
      authDb.prepare("INSERT OR REPLACE INTO verification (id, identifier, value, expiresAt, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)").bind("expired-state-fixture", "synthetic", "synthetic", timestamp - 1, timestamp - 10, timestamp - 10),
      authDb.prepare("INSERT OR REPLACE INTO verification (id, identifier, value, expiresAt, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?)").bind("live-state-fixture", "synthetic", "synthetic", timestamp + 60_000, timestamp, timestamp),
    ]);
    await cleanupExpiredMemberVerification(authDb, timestamp);
    const opportunisticRows = await authDb.prepare("SELECT id FROM verification WHERE id = ?").bind("expired-state-fixture").all<{ id: string }>();
    expect(opportunisticRows.results.map((row) => row.id)).toEqual(["expired-state-fixture"]);
    await cleanupExpiredMemberVerification(authDb, timestamp, true);
    const rows = await authDb.prepare("SELECT id FROM verification WHERE id IN (?, ?) ORDER BY id").bind("expired-state-fixture", "live-state-fixture").all<{ id: string }>();
    expect(rows.results.map((row) => row.id)).toEqual(["live-state-fixture"]);
  });

  it("completes a synthetic Google callback in Worker runtime without persisting provider tokens", async () => {
    const payload = {
      iss: "https://accounts.google.com",
      aud: "synthetic-google-client-id.apps.googleusercontent.com",
      sub: "synthetic-google-subject",
      email: "synthetic-google-user@example.test",
      email_verified: true,
      name: "Synthetic Google User",
      picture: "https://example.test/avatar.svg",
    };
    const base64Url = (value: string): string => {
      const bytes = new TextEncoder().encode(value);
      let binary = "";
      for (const byte of bytes) binary += String.fromCharCode(byte);
      return btoa(binary).replace(/\+/gu, "-").replace(/\//gu, "_").replace(/=+$/u, "");
    };
    const idToken = `${base64Url(JSON.stringify({ alg: "none", typ: "JWT" }))}.${base64Url(JSON.stringify(payload))}.synthetic-signature`;
    const originalFetch = globalThis.fetch;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const target = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (target === "https://oauth2.googleapis.com/token") {
        expect(init?.method).toBe("POST");
        return new Response(JSON.stringify({
          access_token: "synthetic-access-token",
          refresh_token: "synthetic-refresh-token",
          id_token: idToken,
          token_type: "Bearer",
          scope: "openid email profile",
        }), { headers: { "Content-Type": "application/json" } });
      }
      return originalFetch(input, init);
    });

    try {
      const signIn = await SELF.fetch("https://base2026.dev/api/auth/sign-in/social", {
        method: "POST",
        headers: { Origin: "https://base2026.dev", "Content-Type": "application/json" },
        body: JSON.stringify({ provider: "google", callbackURL: "/workspace/" }),
        redirect: "manual",
      });
      expect(signIn.status).toBe(200);
      const signInBody = await signIn.json() as { url?: string };
      const authorization = new URL(signInBody.url ?? "");
      const state = authorization.searchParams.get("state");
      expect(state).toBeTruthy();
      const signInCookies = responseCookies(signIn);
      const stateCookie = signInCookies.find((value) => /(?:__Secure-)?better-auth\.state=/u.test(value))?.match(/((?:__Secure-)?better-auth\.state=[^;]+)/u)?.[1];
      expect(stateCookie).toBeTruthy();

      const callback = await SELF.fetch(
        `https://base2026.dev/api/auth/callback/google?code=synthetic-code&state=${encodeURIComponent(state!)}`,
        { headers: { Cookie: stateCookie! }, redirect: "manual" },
      );
      expect(callback.status).toBeGreaterThanOrEqual(300);
      expect(callback.status).toBeLessThan(400);
      expect(callback.headers.get("location")).toBe("/workspace/");
      const callbackCookies = responseCookies(callback);
      expect(callbackCookies.length).toBeGreaterThan(1);
      expect(callbackCookies.some((value) => /(?:__Secure-)?better-auth\.state=/u.test(value) && /max-age=0/iu.test(value))).toBe(true);
      const sessionCookie = callbackCookies.find((value) => /(?:__Secure-)?better-auth\.session_token=/u.test(value))?.match(/((?:__Secure-)?better-auth\.session_token=[^;]+)/u)?.[1];
      expect(sessionCookie).toBeTruthy();

      const session = await SELF.fetch("https://base2026.dev/api/my-research/session", { headers: { Cookie: sessionCookie! } });
      expect(session.status).toBe(200);
      expect(await session.json()).toMatchObject({
        enabled: true,
        user: { email: "synthetic-google-user@example.test", name: "Synthetic Google User" },
      });
      const account = await authDb.prepare("SELECT accessToken, refreshToken, idToken FROM account WHERE accountId = ?").bind("synthetic-google-subject").first<{ accessToken: string | null; refreshToken: string | null; idToken: string | null }>();
      expect(account).toEqual({ accessToken: null, refreshToken: null, idToken: null });
      const storedUser = await authDb.prepare("SELECT id FROM user WHERE email = ?").bind("synthetic-google-user@example.test").first<{ id: string }>();
      const storedSession = await authDb.prepare("SELECT ipAddress, userAgent FROM session WHERE userId = ? ORDER BY createdAt DESC LIMIT 1").bind(storedUser?.id ?? "").first<{ ipAddress: string | null; userAgent: string | null }>();
      expect(storedSession).toEqual({ ipAddress: null, userAgent: null });
    } finally {
      fetchMock.mockRestore();
    }
  });

  it("reuses an exact existing Google account key without changing its user or binding tuple", async () => {
    const userId = "synthetic-returning-user";
    // Google subjects are opaque strings, including values beyond JS's safe
    // integer range. Numeric coercion must never change the binding key.
    const accountId = "123456789012345678901";
    const email = "synthetic-returning-user@example.test";
    const timestamp = Date.now();
    await authDb.batch([
      authDb.prepare(
        "INSERT INTO user (id, name, email, emailVerified, image, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
      ).bind(userId, "Returning Synthetic User", email, 1, null, timestamp, timestamp),
      authDb.prepare(
        "INSERT INTO account (id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      ).bind("synthetic-returning-account", "https://accounts.google.com", accountId, "google", userId, null, null, null, null, null, "openid email profile", null, timestamp, timestamp),
    ]);
    await seedSavedResearch(userId, timestamp);
    const beforeResearch = await readSavedResearch(userId);
    const beforeUser = await authDb.prepare(
      "SELECT id, name, email, emailVerified, image, createdAt, updatedAt FROM user WHERE id = ?",
    ).bind(userId).first();
    const beforeAccount = await authDb.prepare(
      "SELECT id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt FROM account WHERE id = ?",
    ).bind("synthetic-returning-account").first();

    const result = await completeSyntheticGoogleCallback({ sub: accountId, email, name: "Provider Returned Name" }, "198.51.100.201");
    expect(result.callback.status).toBeGreaterThanOrEqual(300);
    expect(result.callback.status).toBeLessThan(400);
    expect(result.callback.headers.get("location")).toBe("/workspace/");
    expect(result.sessionCookie).toBeTruthy();
    const session = await SELF.fetch("https://base2026.dev/api/my-research/session", {
      headers: { Cookie: result.sessionCookie! },
    });
    expect(session.status).toBe(200);
    expect(await session.json()).toMatchObject({
      enabled: true,
      user: { id: userId, email, name: "Returning Synthetic User" },
    });

    const afterUser = await authDb.prepare(
      "SELECT id, name, email, emailVerified, image, createdAt, updatedAt FROM user WHERE id = ?",
    ).bind(userId).first();
    const afterAccount = await authDb.prepare(
      "SELECT id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt FROM account WHERE id = ?",
    ).bind("synthetic-returning-account").first();
    expect(afterUser).toEqual(beforeUser);
    expect(afterAccount).toEqual(beforeAccount);
    expect(await readSavedResearch(userId)).toEqual(beforeResearch);
    expect(afterAccount).toMatchObject({
      issuer: "https://accounts.google.com",
      accountId,
      providerId: "google",
      userId,
      accessToken: null,
      refreshToken: null,
      idToken: null,
    });
  });

  it.each([
    { mismatch: "subject", storedIssuer: "https://accounts.google.com", storedSubject: "123456789012345678902", incomingSubject: "123456789012345678903" },
    { mismatch: "issuer", storedIssuer: "https://other-issuer.example.test", storedSubject: "123456789012345678904", incomingSubject: "123456789012345678904" },
  ])("denies a different $mismatch for an existing email without auto-linking or changing saved research", async ({ mismatch, storedIssuer, storedSubject, incomingSubject }) => {
    const userId = `synthetic-mismatch-${mismatch}-user`;
    const accountRowId = `synthetic-mismatch-${mismatch}-account`;
    const accountId = storedSubject;
    const email = `synthetic-mismatch-${mismatch}-user@example.test`;
    const timestamp = Date.now();
    await authDb.batch([
      authDb.prepare(
        "INSERT INTO user (id, name, email, emailVerified, image, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
      ).bind(userId, "Mismatch Synthetic User", email, 1, null, timestamp, timestamp),
      authDb.prepare(
        "INSERT INTO account (id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      ).bind(accountRowId, storedIssuer, accountId, "google", userId, null, null, null, null, null, "openid email profile", null, timestamp, timestamp),
    ]);
    await seedSavedResearch(userId, timestamp);
    const beforeResearch = await readSavedResearch(userId);
    const beforeUsers = await authDb.prepare(
      "SELECT id, name, email, emailVerified, image, createdAt, updatedAt FROM user WHERE email = ? ORDER BY id",
    ).bind(email).all();
    const beforeAccounts = await authDb.prepare(
      "SELECT id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt FROM account WHERE userId = ? ORDER BY id",
    ).bind(userId).all();

    const result = await completeSyntheticGoogleCallback({
      sub: incomingSubject,
      email,
      name: "Different Provider User",
    }, "198.51.100.202");
    expect(result.callback.status).toBeGreaterThanOrEqual(300);
    expect(result.callback.status).toBeLessThan(400);
    const location = new URL(result.callback.headers.get("location") ?? "", "https://base2026.dev");
    expect(location.origin).toBe("https://base2026.dev");
    expect(location.pathname).toBe("/my-research/");
    expect(location.searchParams.get("error")).toBe("account_not_linked");
    expect(location.searchParams.has("error_description")).toBe(false);
    expect(result.sessionCookie).toBeUndefined();

    const afterUsers = await authDb.prepare(
      "SELECT id, name, email, emailVerified, image, createdAt, updatedAt FROM user WHERE email = ? ORDER BY id",
    ).bind(email).all();
    const afterAccounts = await authDb.prepare(
      "SELECT id, issuer, accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt FROM account WHERE userId = ? ORDER BY id",
    ).bind(userId).all();
    expect(afterUsers.results).toEqual(beforeUsers.results);
    expect(afterAccounts.results).toEqual(beforeAccounts.results);
    expect(afterAccounts.results).toHaveLength(1);
    expect(await readSavedResearch(userId)).toEqual(beforeResearch);
    expect(afterAccounts.results[0]).toMatchObject({
      issuer: storedIssuer,
      accountId,
      providerId: "google",
      userId,
      accessToken: null,
      refreshToken: null,
      idToken: null,
    });
  });

  it("applies the native D1 schema with isolated member tables", async () => {
    const tables = await authDb.prepare(
      "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('user', 'session', 'account', 'verification', 'member_rate_limits') ORDER BY name",
    ).all<{ name: string }>();
    expect(tables.results.map((row) => row.name)).toEqual([
      "account",
      "member_rate_limits",
      "session",
      "user",
      "verification",
    ]);
  });
});
