# Target-account projection relay receipt

Date: 2026-09-04
Status: target relay deployed and authenticated presence canary passed;
private-producer wiring and projection reconciliation remain held pending one
exact already-authorized apply/verify canary.

## Exact delta

Added the dedicated package at
`cloudflare/base2026-projection-relay/`:

- `src/index.ts` — default Worker fetch plus public exports.
- `src/relay.ts` — fixed-path receiver, envelope/payload/result validation,
  HMAC gate, nonce replay fence, fixed RPC dispatch, and hash-only audit.
- `src/crypto.ts` — Web Crypto SHA-256/HMAC and `BASE2026-HMAC-V1`
  canonical construction.
- `src/public-contract.ts` — adapter to the checked-in public projection
  validators/types.
- `src/editorial-contract.ts` — adapter to the checked-in public editorial
  packet validator/types.
- `migrations/0001_relay.sql` — only `relay_nonces` and
  `relay_audit_receipts` tables/indexes.
- `tests/relay.test.ts` — nine receiver contract tests.
- `wrangler.jsonc`, `worker-configuration.d.ts`, `package.json`, lockfile,
  `tsconfig.json`, `vitest.config.ts`, and `README.md`.

No existing public Worker or private producer source was modified.

The reviewed package was committed on the isolated branch as `3fb7905c3`.

## Binding decision

The receiver binds `PUBLIC_PROJECTION_TARGET` to service `base2026` at
entrypoint `PublicProjectionEntrypoint`. The checked-in target source exports
that class at `cloudflare/base2026-worker/src/index.ts:1998` and exposes
`publishEditorialArticle`, `inspectEditorialArticle`, `applyProjection`,
`inspectPublicSource`, `verifyProjection`, and `rollbackProjection` in the
same entrypoint. Editorial therefore works through the same binding without
modifying the public Worker or adding `PUBLIC_EDITORIAL_TARGET`.

`RELAY_DB` is configured to target-account D1
`base2026-projection-relay`, ID `2df3df60-812d-40f6-9877-2756cc423749`.
Wrangler D1/service binding arrays are repeated under `env.internal` because
named environments do not inherit those arrays. The default environment has
`RELAY_ENABLED=false`, `workers_dev=false`, and no production route; the
internal environment has `workers_dev=true` but remains disabled by default.
The HMAC secret is absent from source/config and was set out-of-band as
`RELAY_HMAC_SECRET`. Its local recovery copy is stored only in macOS Keychain;
the value was not printed, logged or written to Git.
The internal workers.dev environment is the sole bounded test route; it is not
a production endpoint, and both environments remain disabled by default.

## Verification receipt

Commands run from the package directory:

| Check | Result |
| --- | --- |
| `npm run wrangler:types` | passed; bindings generated for D1 and `base2026#PublicProjectionEntrypoint` |
| `npm run typecheck` | passed (`tsc --noEmit`) |
| `npm test` | passed: 1 file, 9 tests |
| `npx wrangler deploy --dry-run --env internal` | passed; D1, service, and disabled flag present |
| `npx wrangler deploy --dry-run --env=""` | passed; D1, service, and disabled flag present |

The tests cover canonical HMAC, disabled mode, POST/path/query/header
allowlists, exact envelope fields, body size, body hash and byte length,
timestamp skew, invalid payloads, nonce replay, duplicate idempotency with a
fresh nonce, TTL reclamation, target RPC mapping, missing target no-write,
target failure audit, and no request-data logging.

## Privacy/reviewer pass

- No `console` logging exists in the receiver; response errors contain only a
  safe code. Wrangler invocation logs are disabled in config.
- The relay never constructs caller-controlled SQL or a destination URL.
- Request bodies are public-contract DTOs only; public projection and editorial
  validators reject private/raw/contact material before target dispatch.
- D1 stores only hashed nonce/request/result values and bounded operation,
  idempotency, outcome, and timestamps; no body, headers, URL, or payload.
- Target result shape is validated before a response is returned; malformed or
  unconfirmed target results fail closed.
- The package does not update repository project-memory files because this
  isolated candidate is not yet integrated into the root branch.

## Target deployment and live canary

- Migration `0001_relay.sql` applied to target D1 and read back both tables
  with zero rows before the canary.
- Disabled internal deployment: version
  `3b460045-8820-4f87-bc47-aed0b6735de6`; exact signed path returned
  `relay_disabled` with HTTP 404.
- Enabled authenticated internal deployment: version
  `96a5f58c-5800-4882-80e7-b4104ea7dfd2` at
  `https://base2026-projection-relay-internal.white-dust-fdaa.workers.dev`.
- A signed `projection_presence` request for a nonexistent fixture returned a
  valid `absent` receipt from the target public RPC. Repeating the same nonce
  returned HTTP 409 `relay_nonce_replay`.
- Target relay D1 readback after the canary: one nonce; one `presence` audit
  receipt; one `replay_rejected` audit receipt. No public projection/editorial
  row was written by this fixture canary.

Before the enabled deployment, 9/9 tests, TypeScript and an internal Wrangler
dry-run passed again with `RELAY_ENABLED=true` and the exact D1/service
bindings.

## Root next action

Select one of the exact 17 already-verified private projection tuples, confirm
target presence, then perform exactly one apply/verify canary through the
reviewed client. A timeout is unconfirmed and is not retried blindly. Producer
wiring and the remaining 16 tuples stay held until the exact target receipt,
row count and relay hash-only audit all match.
