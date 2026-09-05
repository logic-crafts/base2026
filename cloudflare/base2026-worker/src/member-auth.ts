import { betterAuth, type Auth } from "better-auth";

export const MEMBER_AUTH_ORIGIN = "https://base2026.dev" as const;
export const MEMBER_AUTH_BASE_PATH = "/api/auth" as const;
export const MEMBER_AUTH_LOCAL_ORIGIN = "http://localhost:8787" as const;
export const MEMBER_AUTH_LOCAL_ORIGINS = [
  MEMBER_AUTH_LOCAL_ORIGIN,
  "http://127.0.0.1:8787",
] as const;

const AUTH_ROUTE_RE = /^\/api\/auth\/(?:sign-in\/social|callback\/google|sign-out)\/?$/u;
const AUTH_PATH_RE = /^\/api\/auth(?:\/|$)/u;
const ALLOWED_MEMBER_CALLBACKS = new Set(["/workspace/", "/my-research/"]);
const MAX_AUTH_BODY_BYTES = 8 * 1024;

export interface MemberAuthEnv {
  AUTH_DB?: D1Database;
  /** Public read-only source database used by evidence validation. */
  DB?: D1Database;
  BETTER_AUTH_SECRET?: string;
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  MEMBER_AUTH_ENABLED?: string;
  MEMBER_AUTH_LOCAL_DEV?: string;
}

export interface MemberAuthSession {
  user: {
    id: string;
    name: string;
    email: string;
    emailVerified?: boolean;
    image?: string | null;
  };
  session: {
    id: string;
    userId: string;
    expiresAt: Date;
    createdAt?: Date;
    token?: string;
    fresh?: boolean;
  };
}

export interface MemberRateLimitResult {
  allowed: boolean;
  retryAfter: number | null;
}

const RATE_LIMIT_RETENTION_SECONDS = 60 * 60;
const VERIFICATION_CLEANUP_INTERVAL_SECONDS = 17;

async function digestRateLimitKey(key: string, secret: string): Promise<string> {
  const hmacKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const digest = await crypto.subtle.sign("HMAC", hmacKey, new TextEncoder().encode(key));
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

/**
 * D1-backed atomic rate-limit storage. The key is hashed before persistence,
 * so request metadata (including any provider/IP material Better Auth may put
 * in its transient key) never lands in AUTH_DB.
 */
export function createMemberRateLimitStorage(db: D1Database, secret: string): {
  consume(key: string, rule: { window: number; max: number }): Promise<MemberRateLimitResult>;
} {
  return {
    async consume(rawKey, rule) {
      const now = Math.floor(Date.now() / 1000);
      const window = Math.max(1, Math.min(Math.floor(rule.window), 24 * 60 * 60));
      const max = Math.max(1, Math.min(Math.floor(rule.max), 10_000));
      const key = await digestRateLimitKey(rawKey, secret);

      // Keep stale abuse keys from accumulating indefinitely. Cleanup is
      // opportunistic and bounded so a burst cannot turn every request into a
      // full-table delete.
      if (now % 17 === 0) {
        await db.prepare(
          "DELETE FROM member_rate_limits WHERE key IN (SELECT key FROM member_rate_limits WHERE updatedAt < ? ORDER BY updatedAt ASC LIMIT 50)",
        ).bind(now - RATE_LIMIT_RETENTION_SECONDS).run();
      }
      const row = await db.prepare(
        `INSERT INTO member_rate_limits (key, windowStarted, count, updatedAt)
         VALUES (?, ?, 1, ?)
         ON CONFLICT(key) DO UPDATE SET
           windowStarted = CASE
             WHEN ? >= member_rate_limits.windowStarted + ? THEN ?
             ELSE member_rate_limits.windowStarted
           END,
           count = CASE
             WHEN ? >= member_rate_limits.windowStarted + ? THEN 1
             WHEN member_rate_limits.count < ? THEN member_rate_limits.count + 1
             ELSE ?
           END,
           updatedAt = ?
         RETURNING windowStarted, count`,
      ).bind(
        key,
        now,
        now,
        now,
        window,
        now,
        now,
        window,
        max,
        max + 1,
        now,
      ).first<{ windowStarted: number; count: number }>();
      const count = Number(row?.count ?? max + 1);
      const windowStarted = Number(row?.windowStarted ?? now);
      return {
        allowed: count <= max,
        retryAfter: count <= max ? null : Math.max(1, window - (now - windowStarted)),
      };
    },
  };
}

export async function consumeMemberRateLimit(
  db: D1Database,
  secret: string,
  key: string,
  rule: { window: number; max: number },
): Promise<MemberRateLimitResult> {
  return createMemberRateLimitStorage(db, secret).consume(key, rule);
}

export function isMemberAuthPath(pathname: string): boolean {
  return AUTH_PATH_RE.test(pathname);
}

export function memberAuthIsConfigured(env: MemberAuthEnv): boolean {
  return env.MEMBER_AUTH_ENABLED === "true" && Boolean(
    env.AUTH_DB && env.BETTER_AUTH_SECRET && env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET,
  );
}

function allowsLocalOrigin(env: MemberAuthEnv): boolean {
  return env.MEMBER_AUTH_LOCAL_DEV === "true";
}

export function memberTrustedOrigins(env: MemberAuthEnv): string[] {
  return allowsLocalOrigin(env)
    ? [MEMBER_AUTH_ORIGIN, ...MEMBER_AUTH_LOCAL_ORIGINS]
    : [MEMBER_AUTH_ORIGIN];
}

export function isTrustedMemberOrigin(origin: string | null, env: MemberAuthEnv): boolean {
  if (!origin) return false;
  if (origin === MEMBER_AUTH_ORIGIN) return true;
  return allowsLocalOrigin(env) && (MEMBER_AUTH_LOCAL_ORIGINS as readonly string[]).includes(origin);
}

function stripAccountTokens<T extends Record<string, unknown>>(account: T): T {
  return {
    ...account,
    accessToken: null,
    refreshToken: null,
    idToken: null,
    accessTokenExpiresAt: null,
    refreshTokenExpiresAt: null,
  } as T;
}

export function createMemberAuth(env: MemberAuthEnv): Auth<any> {
  if (!memberAuthIsConfigured(env)) throw new Error("MEMBER_AUTH_NOT_CONFIGURED");
  const clientId = env.GOOGLE_CLIENT_ID;
  const clientSecret = env.GOOGLE_CLIENT_SECRET;
  const secret = env.BETTER_AUTH_SECRET;
  if (!clientId || !clientSecret || !secret || !env.AUTH_DB) throw new Error("MEMBER_AUTH_NOT_CONFIGURED");
  return betterAuth({
    database: env.AUTH_DB,
    baseURL: MEMBER_AUTH_ORIGIN,
    basePath: MEMBER_AUTH_BASE_PATH,
    secret,
    trustedOrigins: memberTrustedOrigins(env),
    // OAuth callback errors can include provider response payloads. Do not
    // pass them to Worker invocation logs at all.
    logger: { disabled: true },
    // Keep Better Auth's failure redirect on the private page. The member
    // client allowlists the displayed message and removes OAuth query fields;
    // the default /api/auth/error page would expose an unhelpful public error
    // surface and can be blocked by browser extensions.
    onAPIError: { errorURL: `${MEMBER_AUTH_ORIGIN}/my-research/` },
    rateLimit: {
      enabled: true,
      window: 60,
      max: 20,
      customStorage: createMemberRateLimitStorage(env.AUTH_DB, secret),
    },
    socialProviders: {
      google: {
        clientId,
        clientSecret,
        accessType: "online",
        includeGrantedScopes: false,
        disableDefaultScope: true,
        disableIdTokenSignIn: true,
        scope: ["openid", "email", "profile"],
      },
    },
    emailAndPassword: { enabled: false },
    account: {
      accountLinking: {
        enabled: false,
        disableImplicitLinking: true,
        allowDifferentEmails: false,
        allowUnlinkingAll: false,
      },
      updateAccountOnSignIn: false,
      // Hooks below strip all provider token fields. Keep encryption enabled
      // as a defense-in-depth guard if a future Better Auth write path adds a
      // token field that the hook does not yet know about.
      encryptOAuthTokens: true,
      storeAccountCookie: false,
      storeStateStrategy: "database",
    },
    user: {
      changeEmail: { enabled: false },
      deleteUser: { enabled: false },
    },
    session: {
      cookieCache: { enabled: false },
      freshAge: 10 * 60,
    },
    advanced: {
      useSecureCookies: true,
      disableCSRFCheck: false,
      disableOriginCheck: false,
      // Keep Better Auth's request rate limiter active, but only use the
      // deployment's trusted edge headers and strip the address in hooks
      // before any session row is written.
      ipAddress: {
        disableIpTracking: false,
        ipAddressHeaders: ["cf-connecting-ip"],
      },
    },
    databaseHooks: {
      session: {
        create: { before: async (session: Record<string, unknown>) => ({ data: { ...session, ipAddress: null, userAgent: null } }) },
        update: { before: async (session: Record<string, unknown>) => ({ data: { ...session, ipAddress: null, userAgent: null } }) },
      },
      account: {
        create: { before: async (account: Record<string, unknown>) => ({ data: stripAccountTokens(account) }) },
        update: { before: async (account: Record<string, unknown>) => ({ data: stripAccountTokens(account) }) },
      },
    },
  });
}

export interface BoundedBodyRequest {
  headers: { get(name: string): string | null };
  body?: {
    getReader(): {
      read(): Promise<{ done: boolean; value?: Uint8Array }>;
      cancel(reason?: unknown): Promise<void>;
    };
  } | null;
  text(): Promise<string>;
}

async function readBodyWithinLimit(request: BoundedBodyRequest, maxBytes: number): Promise<string | null> {
  let reader: ReturnType<NonNullable<BoundedBodyRequest["body"]>["getReader"]> | undefined;
  try {
    reader = request.body?.getReader();
  } catch {
    return null;
  }
  if (!reader) return "";
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      const value = chunk.value;
      if (!value) continue;
      size += value.byteLength;
      if (size > maxBytes) {
        await reader.cancel("member request body exceeds limit");
        return null;
      }
      chunks.push(value);
    }
  } catch {
    await reader.cancel("member request body could not be read").catch(() => undefined);
    return null;
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(bytes);
}

export async function readBoundedJson(
  request: BoundedBodyRequest,
  maxBytes = MAX_AUTH_BODY_BYTES,
): Promise<Record<string, unknown> | null> {
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (!Number.isFinite(contentLength) || contentLength < 0 || contentLength > maxBytes) return null;
  const raw = await readBodyWithinLimit(request, maxBytes);
  if (raw === null) return null;
  if (!raw.trim()) return {};
  try {
    const parsed: unknown = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as Record<string, unknown> : null;
  } catch {
    return null;
  }
}

/** Remove only a bounded batch of expired OAuth-state rows. */
export async function cleanupExpiredMemberVerification(
  db: D1Database,
  timestamp = Date.now(),
  force = false,
): Promise<void> {
  const now = Math.floor(timestamp / 1_000);
  if (!force && now % VERIFICATION_CLEANUP_INTERVAL_SECONDS !== 0) return;
  await db.prepare(
    "DELETE FROM verification WHERE id IN (SELECT id FROM verification WHERE expiresAt < ? ORDER BY expiresAt ASC LIMIT 50)",
  ).bind(timestamp).run();
}

export function validateAuthBody(pathname: string, body: Record<string, unknown>): string | null {
  const path = pathname.replace(/\/$/u, "");
  const keys = Object.keys(body);
  if (path === "/api/auth/sign-out") {
    return keys.length === 0 ? null : "INVALID_SIGN_OUT_BODY";
  }
  if (path !== "/api/auth/sign-in/social") return "INVALID_AUTH_ROUTE";
  if (keys.some((key) => key !== "provider" && key !== "callbackURL")) return "INVALID_SIGN_IN_BODY";
  if (body.provider !== "google") return "PROVIDER_NOT_ALLOWED";
  if (body.callbackURL !== undefined && !callbackPathAllowed(body.callbackURL)) return "CALLBACK_NOT_ALLOWED";
  if (body.callbackURL === undefined) return "CALLBACK_REQUIRED";
  return null;
}

export function callbackPathAllowed(value: unknown): value is string {
  if (typeof value !== "string" || value.length > 512 || value.includes("\\") || /[\u0000-\u001f\u007f\s]/u.test(value)) {
    return false;
  }
  if (!value.startsWith("/") || value.startsWith("//")) return false;
  try {
    const parsed = new URL(value, MEMBER_AUTH_ORIGIN);
    return parsed.origin === MEMBER_AUTH_ORIGIN && ALLOWED_MEMBER_CALLBACKS.has(parsed.pathname);
  } catch {
    return false;
  }
}

export function isTrustedMemberRequestOrigin(request: Request, env: MemberAuthEnv): boolean {
  return isTrustedMemberOrigin(new URL(request.url).origin, env);
}

export function authRouteAllowed(request: Request, env: MemberAuthEnv): boolean {
  const url = new URL(request.url);
  if (!AUTH_ROUTE_RE.test(url.pathname)) return false;
  if (!isTrustedMemberRequestOrigin(request, env)) return false;
  const path = url.pathname.replace(/\/$/u, "");
  if (path === "/api/auth/callback/google") return request.method === "GET";
  if (path !== "/api/auth/sign-in/social" && path !== "/api/auth/sign-out") return false;
  if (request.method !== "POST") return false;
  const origin = request.headers.get("origin");
  return isTrustedMemberOrigin(origin, env);
}

export function memberNoStoreHeaders(contentType = "application/json; charset=utf-8"): Headers {
  const headers = new Headers({
    "Content-Type": contentType,
    "Cache-Control": "private, no-store",
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
  });
  return headers;
}

export function memberJson(data: unknown, init: ResponseInit = {}): Response {
  const headers = memberNoStoreHeaders();
  new Headers(init.headers).forEach((value, key) => headers.set(key, value));
  return new Response(JSON.stringify(data), { ...init, headers });
}

export function memberError(status: number, code: string, message: string): Response {
  return memberJson({ error: { code, message } }, { status });
}

export function memberAuthDisabledResponse(): Response {
  return memberError(503, "MEMBER_AUTH_DISABLED", "Member authentication is unavailable.");
}

type HeadersWithSetCookie = Headers & { getSetCookie?: () => string[] };

function responseSetCookies(headers: Headers): string[] {
  const withSetCookie = headers as HeadersWithSetCookie;
  if (typeof withSetCookie.getSetCookie === "function") {
    const values = withSetCookie.getSetCookie();
    if (values.length > 0) return values;
  }
  const getAll = withSetCookie as Headers & { getAll?: (name: string) => string[] };
  return typeof getAll.getAll === "function" ? getAll.getAll("Set-Cookie") : [];
}

/**
 * Ask Better Auth to expire the current session cookie and carry every cookie
 * field it generated onto an already-built member response. The auth handler
 * owns cookie names/signing/attributes; this helper only transports headers.
 */
export async function appendMemberSignOutCookies(
  response: Response,
  auth: Auth<any>,
  request: Request,
): Promise<Response> {
  const headers = new Headers({
    Accept: "application/json",
    "Content-Type": "application/json",
    Origin: MEMBER_AUTH_ORIGIN,
  });
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("Cookie", cookie);
  const signOutRequest = new Request(
    `${MEMBER_AUTH_ORIGIN}${MEMBER_AUTH_BASE_PATH}/sign-out`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ disableRedirect: true }),
    },
  );
  const signOutResponse = await auth.handler(signOutRequest);
  if (!signOutResponse.ok) throw new Error("MEMBER_SESSION_COOKIE_CLEAR_UNAVAILABLE");
  const cookies = responseSetCookies(signOutResponse.headers);
  if (cookies.length === 0) throw new Error("MEMBER_SESSION_COOKIE_CLEAR_UNAVAILABLE");
  const merged = new Headers(response.headers);
  for (const value of cookies) merged.append("Set-Cookie", value);
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: merged,
  });
}

export async function getAuthoritativeSession(
  auth: Auth<any>,
  request: { headers: Headers },
): Promise<MemberAuthSession | null> {
  const result = await auth.api.getSession({
    headers: request.headers,
    query: { disableCookieCache: true, disableRefresh: true },
  });
  if (!result) return null;
  const user = result.user as MemberAuthSession["user"];
  const session = result.session as MemberAuthSession["session"];
  return { user, session };
}

export function sessionCookieName(request: Request): string {
  // Deliberately unused by API code; retained as a narrow helper for tests to
  // assert that no bearer/session token is ever copied into a response body.
  return new URL(request.url).protocol === "https:" ? "better-auth.session_token" : "better-auth.session_token";
}

export { ALLOWED_MEMBER_CALLBACKS, AUTH_ROUTE_RE, MAX_AUTH_BODY_BYTES };
