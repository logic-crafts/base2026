# Base2026 target-account projection relay

This directory is a local, owner-reviewable target-account Worker candidate.
It is not deployed, staged, committed, or wired into the private producer.
The receiver is deliberately small: it authenticates one fixed POST contract,
reserves a hashed nonce in its own D1, calls a fixed service-binding RPC, and
returns only a bounded receipt or safe error code.

## Bindings and defaults

The default Wrangler environment is production-shaped but intentionally inert:

- `RELAY_ENABLED` is `false`.
- `workers_dev` is `false`; no production route is selected yet.
- `RELAY_DB` is the target-account D1 `base2026-projection-relay` (`2df3df60-812d-40f6-9877-2756cc423749`).
- `PUBLIC_PROJECTION_TARGET` is service `base2026`, entrypoint `PublicProjectionEntrypoint`.
- `RELAY_HMAC_SECRET` is a secret binding set out-of-band. No secret value is
  stored in this package, Wrangler config, tests, receipts, or logs.

The `internal` environment repeats the D1 and service bindings explicitly,
because Wrangler does not inherit those binding arrays into named
environments. It sets `workers_dev` to `true` only for the owner-authorized
internal test route; that workers.dev URL is not a production endpoint and
the relay remains disabled there by default.

The current target public Worker exports `PublicProjectionEntrypoint` with all
four projection RPCs and both editorial RPCs. Therefore one service binding is
the compatible contract and no `PUBLIC_EDITORIAL_TARGET` binding is added.
Editorial publication remains subject to the target Worker’s canonical
editorial validator and D1 CAS/evidence checks.

## Fixed contract

| Operation | Receiver path | Target RPC |
| --- | --- | --- |
| `projection_apply` | `/internal/base2026/projection/apply` | `applyProjection` |
| `projection_rollback` | `/internal/base2026/projection/rollback` | `rollbackProjection` |
| `projection_presence` | `/internal/base2026/projection/presence` | `inspectPublicSource` |
| `projection_verify` | `/internal/base2026/projection/verify` | `verifyProjection` |
| `editorial_publish` | `/internal/base2026/editorial/publish` | `publishEditorialArticle` |
| `editorial_inspect` | `/internal/base2026/editorial/inspect` | `inspectEditorialArticle` |

Every route requires `POST`, exact `application/json`, no query string, the
four-key `base2026.cross-account-projection.v1` envelope, and the operation
assigned to that path. The body is capped at 65,536 bytes before JSON parsing.
The five required authentication headers carry the
`BASE2026-HMAC-V1` canonical tuple:

```text
BASE2026-HMAC-V1
POST
<fixed pathname>
<unix timestamp seconds>
<nonce>
<body sha256>
<body byte length>
```

Timestamp skew is at most five minutes. Nonces are hashed before D1 storage,
reserved atomically with `INSERT OR IGNORE`, and expire after ten minutes.
Only fixed SQL statements for `relay_nonces` and append-only
`relay_audit_receipts` exist. Caller-provided SQL, destination URLs, headers,
cookies, tokens, private source text, raw transcripts, and arbitrary RPC
methods are not accepted or logged.

Projection payloads and receipts reuse the public Worker’s canonical public
validators. Editorial packets reuse the target public editorial packet
validator; only the packet plus the bounded compare-and-swap overwrite tuple
cross the relay, and publication results are reduced to receipt/diagnostic
metadata or safe issue fields.

## Local verification

From this directory:

```sh
npm ci
npm run wrangler:types
npm run typecheck
npm test
npx wrangler deploy --dry-run --env=""
npx wrangler deploy --dry-run --env internal
```

The dry-runs are non-mutating. Before any real deployment, the owner must
apply the D1 migration and set the secret through the approved Cloudflare
secret workflow; neither action is performed by this candidate.

## Deploy order

1. Review the target-account D1 migration and apply it to the configured D1.
2. Set `RELAY_HMAC_SECRET` out-of-band and keep `RELAY_ENABLED=false`.
3. Choose and review the production route. Keep the default `workers_dev=false`;
   use only the `internal` environment’s workers.dev test route for a bounded
   internal canary.
4. Deploy the disabled relay and verify the service binding resolves to
   `base2026#PublicProjectionEntrypoint` and the target D1 is the configured
   D1.
5. Verify the disabled route returns the bounded `relay_disabled` response.
   Then change only the `internal` environment to `RELAY_ENABLED=true`, repeat
   the dry-run, deploy that authenticated environment, and run a signed
   presence canary.
6. Run one already-authorized apply/verify canary, comparing the exact
   identity/hash/card/row receipt tuple. A timeout is unconfirmed and must not
   be blindly retried.
7. Only after those receipts pass, wire the private producer. Keep its prior
   service binding and last known Worker version as rollback points until
   post-change readback is complete.

## Rollback

Stop producer wiring first and disable the relay. Restore the prior private
service binding, then inspect target presence/receipts before deciding whether
any exact tuple needs a single controlled retry. Do not retry an unconfirmed
target write solely because transport timed out. Stop on signature failure,
nonce replay, receipt/hash mismatch, target legacy/mixed state, unexpected
fields, privacy rejection, or any public release-gate change. This relay has
no unauthenticated public write route; its workers.dev ingress accepts only the
fixed HMAC contract. The target public RPC remains the authority for public D1
state and rollback semantics.
