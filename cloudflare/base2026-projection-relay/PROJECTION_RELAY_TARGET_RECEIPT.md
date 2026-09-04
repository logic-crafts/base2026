# Target-account projection relay receipt

Date: 2026-09-04
Status: local candidate only; no deploy, migration apply, stage, commit, or
private-producer wiring performed.

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
The HMAC secret is intentionally absent from source/config and must be set as
an out-of-band `RELAY_HMAC_SECRET` secret before an owner-approved canary.
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

## Root rollout decision

Review the package and migration, apply the target D1 migration, set the
dedicated secret, and deploy the `internal` workers.dev environment once with
the relay disabled. After the disabled readback, enable only that environment
and run a signed presence canary followed by one already-authorized
apply/verify canary. A signed canary cannot run while `RELAY_ENABLED=false`;
producer wiring remains held until the exact target receipts are accepted.
