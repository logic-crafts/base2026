# Better Auth + Cloudflare Workers/D1 stack research

Status: candidate evidence only, checked 2026-08-31. This note does not
authorize a Google-console change, a D1 migration, a deployment, or a
production release.

## Finding

The smallest supported candidate is Better Auth's built-in D1 path inside the
existing Worker, with a dedicated `AUTH_DB` binding and a dedicated migration
directory. Pass the D1 binding directly as `database: env.AUTH_DB`; no Drizzle,
Prisma, hosted auth service, extra Worker, or extra domain is required by this
stack. Keep the public search D1 separate.

The npm registry currently reports `better-auth@1.7.2` as the latest stable
release (published 2026-08-26). Pin the directly installed Better Auth
packages together at `1.7.2`; the matching core and Kysely adapter are
`@better-auth/core@1.7.2` and `@better-auth/kysely-adapter@1.7.2`. The
version-pinned optional CLI package is `auth@1.7.2` (`npx auth@1.7.2 ...`);
do not silently substitute the older `@better-auth/cli` line.

The repository's Worker already uses Wrangler `4.124.0` and
`compatibility_flags: ["nodejs_compat"]`. That flag is required by Better
Auth's Workers guidance and should remain enabled.

## Minimal binding and handler shape

This is a verified API shape, not application code or a request to put
credentials in source:

~~~ts
function createAuth(env: Env) {
  return betterAuth({
    baseURL: "https://base2026.dev",
    basePath: "/api/auth",
    secret: env.BETTER_AUTH_SECRET,
    database: env.AUTH_DB, // D1Database; native adapter
    trustedOrigins: ["https://base2026.dev"], // exact origins only
    socialProviders: {
      google: {
        clientId: env.GOOGLE_CLIENT_ID,
        clientSecret: env.GOOGLE_CLIENT_SECRET,
        disableDefaultScope: true,
        scope: ["openid", "email", "profile"],
        accessType: "online",
        includeGrantedScopes: false,
      },
    },
    account: {
      storeStateStrategy: "database",
      skipStateCookieCheck: false,
      storeAccountCookie: false,
      encryptOAuthTokens: true,
      updateAccountOnSignIn: false,
      accountLinking: {
        disableImplicitLinking: true,
        allowDifferentEmails: false,
      },
    },
    session: {
      cookieCache: { enabled: false },
    },
    rateLimit: {
      enabled: true,
      storage: "database",
      // Add bounded customRules only after endpoint tests establish limits.
    },
    advanced: {
      useSecureCookies: true,
      disableCSRFCheck: false,
      disableOriginCheck: false,
      ipAddress: {
        disableIpTracking: false,
        ipv6Subnet: 64,
      },
    },
  });
}

// Build auth in the request path/factory so the request-scoped D1 binding is
// available; then route only /api/auth/* to auth.handler(request).
~~~

The exact handler type is `Auth.handler(request: Request): Promise<Response>`.
The D1 value is accepted directly by `betterAuth` as `D1Database`; an
additional adapter wrapper is not part of the native path. A factory created
from the incoming request is the safer Workers shape: a D1 binding is not
available as a module-scope runtime value. This also merits an abort/concurrent
request test because Better Auth 1.6.x had a reported lazy-initialization
hang; 1.7.2 includes an async-context fix, but the package still has a lazy
async-hooks path under the Workers export.

`baseURL` should be explicit, not inferred from the request. The production
Google callback is:

    https://base2026.dev/api/auth/callback/google

Add a separate exact localhost origin/callback only in a development
configuration. Never use a wildcard trusted origin for this candidate.

## Google identity, state, and token handling

In `@better-auth/core@1.7.2`, `GoogleOptions` includes:

    clientId: string | string[]
    clientSecret: string
    disableDefaultScope?: boolean
    scope?: string[]
    accessType?: "offline" | "online"
    includeGrantedScopes?: boolean

Google's built-in default scope is `["email", "profile", "openid"]`. Setting
`disableDefaultScope: true` plus the explicit three-item scope list makes the
allowed request auditable. Set `accessType: "online"` and
`includeGrantedScopes: false`; do not add Gmail/Drive scopes,
`offline_access`, `prompt: "consent"`, or an offline access parameter. The
provider may still return an access/id token as part of sign-in.

OAuth state and PKCE are framework-managed. Better Auth writes the redirect
URI, state, and code-challenge; its OAuth `additionalParams` cannot override
reserved `state`, `client_id`, `redirect_uri`, `response_type`,
`code_challenge`, `code_challenge_method`, or `scope` keys. With a database
available, `account.storeStateStrategy: "database"` is the default and
explicitly records state in the verification table while a signed state
cookie is checked on callback. Keep `skipStateCookieCheck: false`; do not
turn it off to work around a test.

Better Auth stores provider account columns (`accessToken`, `refreshToken`,
`idToken`, expiry, and scope) by default. There is no verified
`storeTokens: false` option in 1.7.2. Therefore:

- `encryptOAuthTokens: true` is required defense in depth; the package
  encrypts token values with AES-256-GCM before persistence.
- `storeAccountCookie: false` prevents a second copy of account/token data in
  an encrypted browser cookie.
- `updateAccountOnSignIn: false` avoids rewriting token fields on repeat
  sign-ins when this product does not use provider APIs. It does not prevent
  token fields from being stored for the first account creation.
- `accessType: "online"` reduces the chance of a refresh token but is not a
  zero-token persistence guarantee. Do not expose account-token retrieval,
  refresh, or provider API routes.

The current package declarations expose
`user.validateUserInfo(data, context)`, where `data` contains
`user` and `source`; for an OAuth-only allowlist, the callback can fail closed
unless `source.oauth?.providerId === "google"`. The callback may return
`{ error, errorDescription? }`. This is an optional defense-in-depth gate,
not a substitute for exact provider configuration.

The current website documents an `account.identityStrategy` option, but the
installed 1.7.2 package declaration inspected here does not expose that
field. Do not add it without a version-pinned typecheck; this is a
documentation/package drift caveat.

## D1 schema and migration contract

Better Auth's supported migration helper is:

    import { getMigrations } from "better-auth/db/migration";
    const migrations = await getMigrations(auth.options, {
      throwOnUnsafe: true,
    });
    await migrations.runMigrations();       // one-off controlled operation
    const sql = await migrations.compileMigrations();

The helper returns `toBeCreated`, `toBeAdded`, `toBeAddedIndexes`,
`unsafeChanges`, `runMigrations`, and `compileMigrations`. The default
`throwOnUnsafe` is true. Inspect `unsafeChanges` and generated SQL before any
non-empty database migration. Never call `runMigrations()` on every request.
The CLI `migrate` path is for the built-in Kysely adapter; it does not solve
the request-scoped D1 binding problem. Use one controlled migration workflow
and record its receipt.

The generated baseline normally includes Better Auth's `user`, `session`,
`account`, and `verification` tables; database-backed rate limiting adds the
rate-limit table. Treat the generated 1.7.2 SQL as authoritative and inspect
indexes/columns rather than hand-writing a shortened schema. In particular,
the account identity requires the current `issuer` and `accountId` fields and
their compound uniqueness.

The Wrangler D1 binding shape is `binding`, `database_name`,
`database_id`, and optional `migrations_dir`. Use a dedicated
`migrations_dir` such as `migrations-auth` for `AUTH_DB`; keep actual IDs and
database names in private deployment configuration, not in this note. Check
the intended database with:

    npx wrangler d1 migrations list <AUTH_DB_DATABASE_NAME>
    npx wrangler d1 migrations apply <AUTH_DB_DATABASE_NAME> --local

Use `--remote` only after the owner-approved release gate. D1's Worker API
supports `prepare().bind().run()/first()/raw()` and `batch()`. D1 does not
provide interactive transactions; Better Auth's built-in D1 dialect uses
batching where atomicity is needed. Do not mix the auth migrations into the
existing public-search migrations.

## Sessions, deletion, and export

The core session defaults are seven days (`expiresIn: 604800`) with a
one-day refresh age (`updateAge: 86400`). Cookie cache is off by default and
should stay off for immediate database revocation. The relevant core routes
are:

    GET/POST /api/auth/get-session
    GET     /api/auth/list-sessions
    POST    /api/auth/revoke-session       { token }
    POST    /api/auth/revoke-sessions
    POST    /api/auth/revoke-other-sessions
    POST    /api/auth/sign-out
    POST    /api/auth/delete-user

The matching client operations are `signOut`, `listSessions`,
`revokeSession`, `revokeSessions`, and `revokeOtherSessions`. For sensitive
operations, use an authoritative database session check (or the package's
`sensitiveSessionMiddleware` where it applies), not a cached cookie-only
decision. Test that sign-out/revoke-all invalidates an old cookie immediately.

`user.deleteUser` has the exact option shape:

    enabled?: boolean
    sendDeleteAccountVerification?: (data: {
      user: User; url: string; token: string
    }, request?: Request) => Promise<void>
    beforeDelete?: (user: User, request?: Request) => Promise<void>
    afterDelete?: (user: User, request?: Request) => Promise<void>
    deleteTokenExpiresIn?: number

If `sendDeleteAccountVerification` is omitted, enabled deletion is immediate;
choose the verification/reauthentication behavior explicitly before exposing
the destructive endpoint. Core deletion clears the user's sessions; still
test a previously issued session and any custom My Research rows. An export
endpoint is application-owned, not a core Better Auth endpoint: query only
rows owned by the authoritative session user, allowlist fields, and exclude
the entire account token column set and internal verification/state data.

## CSRF, origin, cookies, IPs, and rate limits

Keep `advanced.disableCSRFCheck: false` and
`advanced.disableOriginCheck: false`. Keep `trustedOrigins` exact and
`advanced.useSecureCookies: true`; test emitted cookies for `HttpOnly`,
`Secure`, and the intended `SameSite` behavior. Do not enable
`crossSubDomainCookies` unless a separate subdomain requirement is approved.

The exact IP options are under `advanced.ipAddress`:

    ipAddressHeaders?: string[]
    disableIpTracking?: boolean
    ipv6Subnet?: number
    trustedProxies?: string[]

Keep `disableIpTracking: false`; the package documents disabling IP tracking
as a security risk. Do not trust `cf-connecting-ip` or a forwarded header
unless the origin is reachable only through the trusted proxy path and
clients cannot spoof that header. The default IPv6 rate-limit subnet is 64.

`rateLimit.storage` accepts `"memory"`, `"database"`, or
`"secondary-storage"`; `"database"` causes the rate-limit table to be added
to generated schema. Start with bounded custom rules for OAuth start/callback,
sign-in, and sensitive My Research mutations only after measuring the
candidate's UX. Verify repeated requests return `429`, keys include the
trusted client-IP behavior, and IPv6 addresses cannot evade the limit.

## Invocation-log privacy

The existing Worker observability config enables automatic observability.
Cloudflare documents this supported Wrangler shape:

~~~jsonc
"observability": {
  "enabled": true,
  "head_sampling_rate": 1,
  "logs": {
    "invocation_logs": false
  }
}
~~~

Set `observability.logs.invocation_logs: false` before exposing the OAuth
callback. Invocation records can contain the method and full request URL;
the callback query can contain the authorization `code` and state. This
setting disables automatic invocation events while leaving the application
responsible for any deliberate structured `console` logs. Never log the
request URL/query, authorization code, state, PKCE verifier, cookies,
authorization headers, account rows, or token values.

Cloudflare's API resource model also exposes a
`redact_query_string` script-observability setting, but the inspected pinned
Wrangler schema (`4.124.0`, and the current registry schema checked during
research) does not accept it in `wrangler.jsonc`. Treat it as a separately
managed API/account setting only after verifying the deployment surface; do
not add an unsupported local key. Query Builder filters are post-ingestion
selection, not redaction. Review traces and Logpush destinations for URL
retention as a separate release check.

## Advisory and compatibility review

The reviewed core advisories are patched by 1.7.2:

| Advisory | Affected range / issue | Candidate disposition |
| --- | --- | --- |
| [GHSA-g38m-r43w-p2q7](https://github.com/advisories/GHSA-g38m-r43w-p2q7) | `<1.6.11`; OAuth implicit-linking pre-account hijack | Pin 1.7.2; keep `disableImplicitLinking: true` and no local password flow in this slice. |
| [GHSA-2vg6-77g8-24mp](https://github.com/advisories/GHSA-2vg6-77g8-24mp) | `>=0.3.4,<1.6.11`; stale sessions after deletion under specific secondary-storage/admin/anonymous conditions | Pin 1.7.2; no secondary storage; test self-delete and stale-cookie rejection. |
| [GHSA-p6v2-xcpg-h6xw](https://github.com/advisories/GHSA-p6v2-xcpg-h6xw) | `<1.4.17` and affected beta range; IPv6 rate-limit bypass | Pin 1.7.2; keep IPv6 subnet 64 and verify rate-limit behavior. |

Plugin-only advisories were not treated as blockers because this candidate
does not add SCIM, SSO, OAuth-provider, MCP, device-auth, organization, or
OIDC-provider plugins. Re-run the dependency/advisory audit whenever the
version or plugin set changes. Better Auth 1.7 release guidance also says to
upgrade directly installed Better Auth and `@better-auth/*` packages
together.

## Minimum prototype checks before any release decision

1. Typecheck the Worker with the generated `AUTH_DB` binding and run the
   existing test suite; confirm the 1.7.2 declarations accept the exact
   option shape.
2. Generate/inspect the 1.7.2 migration plan on an empty local auth D1,
   including the rate-limit table; apply once, rerun for zero changes, and
   confirm the public D1 remains untouched.
3. Assert the Google authorization URL has exactly `openid email profile`,
   `access_type=online`, and no Gmail/Drive or incremental-grant parameter.
   Tampered, replayed, missing, and cross-origin state/PKCE callbacks must
   fail.
4. Complete login, `get-session`, sign-out, revoke-current, revoke-all, and
   old-cookie checks with cookie cache disabled. Verify no token appears in
   response bodies, cookies, deliberate logs, or unencrypted D1 values.
5. Exercise account deletion with the chosen verification/reauthentication
   gate; confirm sessions and owned My Research data are removed, while an
   unauthenticated or different user cannot export it.
6. Exercise rate limits on OAuth and sensitive routes, including concurrent
   requests and representative IPv6 addresses; confirm `429` and no
   sensitive URL/query logging.
7. Abort and overlap several Worker requests during auth creation/callback;
   confirm no hanging initialization or cross-request D1/session state.
8. Run `wrangler types` and `wrangler deploy --dry-run`; inspect that the
   dedicated binding/migration directory and
   `observability.logs.invocation_logs: false` are represented without
   private IDs or secrets in the public artifact.

## Primary sources

- [Better Auth installation](https://better-auth.com/docs/installation)
- [Better Auth options reference](https://better-auth.com/docs/reference/options)
- [Better Auth database concepts and programmatic migrations](https://better-auth.com/docs/concepts/database)
- [Better Auth 1.5 native Cloudflare D1 announcement](https://better-auth.com/blog/1-5)
- [Better Auth 1.7 release notes](https://better-auth.com/blog/1-7)
- [Better Auth changelog](https://better-auth.com/changelog)
- [better-auth 1.7.2 npm package](https://www.npmjs.com/package/better-auth/v/1.7.2)
- [@better-auth/core 1.7.2 npm package](https://www.npmjs.com/package/@better-auth/core/v/1.7.2)
- [Cloudflare D1 Worker API](https://developers.cloudflare.com/d1/worker-api/)
- [Cloudflare D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/)
- [Wrangler D1 commands](https://developers.cloudflare.com/workers/wrangler/commands/d1/)
- [Cloudflare Workers Logs and invocation logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Cloudflare Workers Logs Query Builder](https://developers.cloudflare.com/workers/observability/query-builder/)
- [Cloudflare API script observability settings](https://developers.cloudflare.com/api/resources/workers/subresources/scripts/subresources/settings/methods/edit/)
- [Better Auth advisory index](https://github.com/better-auth/better-auth/security/advisories)
- [Better Auth Workers lazy-initialization issue](https://github.com/better-auth/better-auth/issues/10315)
- [Better Auth D1 request-context discussion](https://github.com/better-auth/better-auth/discussions/7487)
