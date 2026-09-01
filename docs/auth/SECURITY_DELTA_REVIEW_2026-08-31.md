# Google sign-in and My Research: security delta review

Date: 2026-08-31
Scope: frozen Base2026 candidate, local source/config/artifact review only

## Decision

**Code/security gate: PASS.** The five findings in the historical
[security review](SECURITY_REVIEW_2026-08-31.md) are closed in the frozen
delta. No critical or high-severity blocker was found in the reviewed source,
native-D1 tests, private routing, UI, privacy notice, or member-enabled static
configuration.

**Release gate: PENDING.** This is not a production or Google-E2E receipt. No
real Google callback, remote D1 migration, secret injection, deployment,
production trace/log-retention review, or coordinator release ACK was performed.
The Google test configuration is limited to the approved basic identity
scopes. The checked-in public configuration remains member-disabled.

## Finding closure

| Finding | Independent result | Evidence and residual |
| --- | --- | --- |
| F01 Google authorization URL/parameters | **CLOSED** | The browser guard accepts only HTTPS `accounts.google.com`, `/o/oauth2/v2/auth`, an allowlisted parameter set, exact `code`/`online`/`S256`, exact `openid email profile`, the canonical callback, one non-empty state and PKCE challenge, and no userinfo/hash. Unknown, duplicate, incremental, offline, wrong-path, wrong-redirect and malformed values are rejected (`templates/base2026-members.js:115-163`; UI test URL matrix). Backend provider settings independently pin the same scope and online flow (`cloudflare/base2026-worker/src/member-auth.ts:193-219`; native auth test). |
| F02 expired OAuth-state cleanup | **CLOSED with documented residual** | Account deletion forces an expired-only cleanup before its single D1 batch, limits deletion to 50 rows, preserves valid/in-flight rows, and treats cleanup failure as non-authoritative (`cloudflare/base2026-worker/src/member-auth.ts:317-328`; `cloudflare/base2026-worker/src/member-research.ts:508-532`; native deletion test). Verification rows have no owner column, so inactive expired rows can remain until later authentication activity. The privacy notice and runbook disclose that bounded residual and introduce no background cron (`templates/base2026-members-privacy.html:5`; `docs/auth/MEMBER_AUTH_RUNBOOK.md:142-149`). |
| F03 missing/invalid trusted client IP | **CLOSED** | In production, a missing, malformed, or multi-value `CF-Connecting-IP` causes the unauthenticated session summary to fail closed with safe `503 MEMBER_UNAVAILABLE`; it is intentionally not a `403`. Valid IPv4 `/24` and IPv6 `/64` partitions work. Only the explicit local-dev flag permits a missing edge header (`cloudflare/base2026-worker/src/member-research.ts:148-186,535-547`; member test). Better Auth keeps `disableIpTracking: false` and accepts only `cf-connecting-ip`; hooks remove session IP/UA fields before persistence. |
| F04 recent-sign-in freshness | **CLOSED** | Freshness uses a strict age `< 600s` test (not `<=`), while Better Auth's explicit fresh flag remains authoritative for a newly authenticated session (`cloudflare/base2026-worker/src/member-research.ts:257-263`). Stale and exact-ten-minute account deletion attempts are rejected with `403 REAUTH_REQUIRED` in native-D1 tests. |
| F05 cookie transport and revocation | **CLOSED** | Cookie extraction uses `getSetCookie()` with a `getAll("Set-Cookie")` fallback, appends every value, and throws a safe error when sign-out fails or produces no cookie; there is no silent cookie-skip path (`cloudflare/base2026-worker/src/member-auth.ts:398-446`). Synthetic callback, logout, revoke and deletion tests observe multiple cookies and an expired session cookie. The root private response preserves the private no-store/security policy and strips public CORS (`cloudflare/base2026-worker/src/index.ts:366-386`). |

## Boundary and implementation checks

- Better Auth is pinned to `better-auth@1.7.2` in the Worker manifest and
  lockfile. The reviewed configuration uses request-local native D1 via
  `database: env.AUTH_DB`, exact `baseURL`/`basePath` and trusted origins,
  disabled library logging, online Google with only `openid email profile`,
  database OAuth state, secure cookies, disabled cookie cache, authoritative
  session reads (`disableCookieCache` and `disableRefresh`), and an enabled
  D1-backed atomic limiter. Provider token fields are nulled by database hooks;
  encryption remains enabled as defense in depth. No provider bearer token is
  returned by member responses or export.
- `member-research.ts` scopes all reads/writes/exports to the authenticated
  owner. Collection/item quotas are enforced in owner-scoped atomic
  `INSERT ... SELECT` statements; duplicate evidence saves are idempotent and
  do not overwrite an existing note. Public `DB` is used only for an
  eligibility read of an already-public source. Account deletion batches
  owned items, collections, account, sessions and user; it does not write to
  public D1 or remove another member's live OAuth state.
- The root Worker dispatches `/api/auth/*`, `/api/my-research/*` and
  `/my-research/` before public routes. Private responses are no-store,
  no-index, same-origin/CSP constrained, non-CORS, and callback exceptions do
  not log URLs or provider payloads. The proposed member-enabled overlay keeps
  `observability.logs.invocation_logs=false`; the Worker library logger is also
  disabled. Separate trace/Logpush destinations remain a release-time review
  item.
- Static candidate scan found no local-path, secret-marker, private-token or
  loopback leakage. No review-only `tests/member-security-review.test.ts` was
  needed or added.

## Proposed overlay and public artifact receipt

The review-only member-enabled Wrangler overlay (private path intentionally not
recorded here) independently verified all of the following: the three existing
public D1 bindings, route list and `run_worker_first` list are unchanged; the
only added D1 entry is the `AUTH_DB` placeholder pointing at
`migrations-members`; members are explicitly enabled; local-dev mode is absent;
`nodejs_compat` is present; invocation logs are off; and `main`/assets resolve
to the reviewed Worker source and candidate tree.

- Overlay SHA-256: `e1dcb230fce2a88e4d3c5c8eb850d4e9f74dd1a9ddbbd845b8fb918869b19390`.
- Candidate served files: 4,248; bytes: 89,959,711.
- Candidate artifact tree SHA-256:
  `1039f92aeae0195dee2dfb4c63bc905e41cee2fe41e60fe177b34785713fe361`.
- Candidate receipt SHA-256:
  `29285f3bb28bba17830042d799b2e97bf5f51d76db85ef1d7f28f15876415467`.
- Output inventory: 4,250 files including two metadata files; 5 changed public
  files (3 added, 2 changed); manifest/readback and zero-leak checks passed.
- Pinned Wrangler dry-run bundle receipt: extracted worker module,
  2,099,671 bytes, SHA-256
  `e59f97bf7a9d9aaf4f445f3c2a77068bcfeb18a51f81abd2e410a8755b9ff42b`;
  reported 2,050.46 KiB / 374.07 KiB gzip. No secrets were supplied.

## Independently rerun gates

All commands completed successfully against the frozen worktree:

- `npm run typecheck` — TypeScript passed.
- `npm test` — 11 Worker test files, 612 tests passed (Vitest 4.1.11).
- `npm run test:members` — 2 native-D1 member test files, 13 tests passed.
- `python3 -m pytest -q tests/test_build_base2026_cloudflare_release.py tests/test_base2026_members_ui.py` — 28 tests passed.

The member suite covers synthetic Google URL construction, state/PKCE,
multiple-cookie callback handling, token/session-field stripping, IPv4/IPv6
rate partitions, production no-IP fail-closed behavior, full CRUD and
idempotency, owner isolation, logout/revocation, export exclusion, strict
freshness, forced cleanup with live-state preservation, and deletion cascade.
The UI suite covers the same strict authorization URL matrix plus storage,
accessibility, stale-load and fresh-reauth behavior. These are local synthetic
checks, not evidence of a live Google or remote-D1 operation.

## Checked hashes

SHA-256 values below identify the exact files reviewed:

| File | SHA-256 |
| --- | --- |
| `cloudflare/base2026-worker/src/member-auth.ts` | `058ea8b06261a2bef5814c23dcda7bc5e6a9ba2d8066942b060b512e494c4ed2` |
| `cloudflare/base2026-worker/src/member-research.ts` | `72338baaa90d9a7f535df9790bea6339660a6fabaf5a7628ff65290d97ee080c` |
| `cloudflare/base2026-worker/src/member-prototype.ts` | `69ba223d2baaa640ea5d197049dba9bb74bb4e9875115716a9e7edd237ca85ea` |
| `cloudflare/base2026-worker/src/index.ts` | `1bddda0b887afc1f2bf6a07ab245ef6267685363975a06fd3a8111feb30e8608` |
| `cloudflare/base2026-worker/migrations-members/0001_better_auth.sql` | `e1fb742277591305d6968ab3f5df9bb1a5624bdfced8dee9f65a1a182e19ce80` |
| `cloudflare/base2026-worker/migrations-members/0002_member_research.sql` | `fd62b1be3a6420efc8624c0995df9d074f8ced3638f74fc54585c096b862f07a` |
| `cloudflare/base2026-worker/tests/member-auth-prototype.test.ts` | `37b5360ae0dd068886f408aa88c8895761d3e042e1b874783332a3b4254f2107` |
| `cloudflare/base2026-worker/tests/member-research.test.ts` | `71c9f6b49841581cd444e723949d69b76732da820768423e26f6b29ce394b856` |
| `templates/base2026-members.js` | `ff80f7722bfa98547feeb3feb7d6e7cb1cd32468fbfab84887f709d974e8eaf7` |
| `tests/test_base2026_members_ui.py` | `a79077dcb7e980044563235e5ff1604c32a9978ad79612240b66b468938be16b` |
| `templates/base2026-members-privacy.html` | `aa402085005c97c719590ebdd06ef4a0598297876042a0e4e55d23631b3d30f4` |
| `docs/auth/MEMBER_AUTH_RUNBOOK.md` | `823fd64ecff73399203b46929e354150db88a231ec02172276631a92fc9f63cf` |
| `cloudflare/base2026-worker/package.json` | `7e056d8121a6b22ea4a9747ecc3980c507e961e0699ef45d04ad9b2560f437e6` |
| `cloudflare/base2026-worker/package-lock.json` | `6cd36f72a8ba102cacdff56d06c7a43d8fbb0b16524b7ffec3159ca9e61a11b7` |
| `cloudflare/base2026-worker/wrangler.jsonc` | `210d9327aa76e4b46dbdd68509885e037ef404df252ece9dad34dcbda96212e5` |
| `cloudflare/base2026-worker/member-worker-configuration.d.ts` | `6406e15e5d593794cb19a9a34c826a1fe61467af3587a2bfd452c23820d64b66` |
| `cloudflare/base2026-worker/vitest.config.ts` | `6a5e6eb73f3e62b17b14b3274e15acc6ef4433190f5d82ec41c219fa109e3f37` |
| `cloudflare/base2026-worker/vitest.members.config.ts` | `a99e3db5a20dc3efa9271443a623da742cb9bbaab34329530a41f8b4709e639f` |
| `cloudflare/base2026-worker/wrangler.members-local.jsonc` | `bf46de3ffe703f621dc0248586c03c3612e5c85bc821b54d54817dfb9417657a` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/workspace/index.html` | `a7e376c4e67cd3920b8729784a4099e33f4cddc3325f85897caec9ed35ae1c78` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/my-research/index.html` | `41fe03ec980b8562d6759855af668377e028ce14c4ca9e19f63de34d5cdb46c7` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/privacy.html` | `191f1324808178c02f57e0640f79b02543078daca7138e58832d9feba77e140f` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/static/base2026-members.css` | `692d06549f4c1de78ad2e907557e27699a79bb2c8ed29ea866b341408d0c5652` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/static/base2026-members.js` | `ff80f7722bfa98547feeb3feb7d6e7cb1cd32468fbfab84887f709d974e8eaf7` |
| `output/cloudflare-migration/base2026-members-candidate-20260831-v2/.assetsignore` | `22245a9cf2585614475bab68f4f16fbc4638afd78b2f2246f0617cd0f695fac6` |

## Primary references

- [Better Auth installation](https://www.better-auth.com/docs/installation),
  [D1 adapter](https://www.better-auth.com/docs/adapters/d1),
  [social sign-in](https://www.better-auth.com/docs/authentication/social-sign-in),
  and [session management](https://www.better-auth.com/docs/concepts/session-management).
- [`better-auth@1.7.2` package registry entry](https://www.npmjs.com/package/better-auth/v/1.7.2)
  and [Better Auth security advisories](https://github.com/better-auth/better-auth/security/advisories).
- [Cloudflare D1 Worker API](https://developers.cloudflare.com/d1/worker-api/d1-database/),
  [D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/),
  and [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/).
