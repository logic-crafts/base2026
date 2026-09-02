# Base2026 Claim Receipt Ledger

The claim-receipt ledger is a bounded, read-only public canary for
source-backed internal-linking evidence. It is an undeployed candidate until
the owner approves the private admission wrapper, the public D1 migration and
the normal release gates.

## Public contract

The only public route is:

```text
GET|HEAD /api/claim-receipts/v1?canary=base2026.internal-linking.canary.v1&topic=internal-linking
```

The query string is exact. Unknown parameters, duplicate parameters, a
different canary/topic, pagination, and mutation methods are rejected. A
mutation receives `405` with `Allow: GET, HEAD`. A canary with fewer than ten
active receipts receives `503` with
`CLAIM_RECEIPT_CANARY_NOT_READY`; no partial ledger is returned.

When ready, the response has schema
`base2026.claim-receipt-ledger.v1`, exactly ten receipts, one distinct public
source per receipt, and no more than two receipts per creator. Each receipt
contains the source/projection/card/search identities, creator attribution,
the exact original URL, a stable Base2026 source URL, the published date,
claim/action/topic, a bounded evidence excerpt and time range, the public
projection receipt hash, and the admission policy version.

The receipt digest is SHA-256 over canonical sorted-key JSONL. Mutable ledger
state and timestamps are excluded from receipt and ledger digests. The static
export therefore has the same digest as a validated public-D1 readback.
Evidence timecodes are bounded to one day and millisecond precision; values
outside that shared JavaScript/Python canonical range fail closed.

## Static export

The reviewed exporter is
`scripts/export-public-claim-receipts.py`. It accepts a validated public-D1
readback and writes only:

- `/static/claim_receipts.jsonl` — ten canonical immutable receipt rows;
- `/static/claim_receipts_manifest.json` — schema, canary, count, ledger hash,
  JSONL hash and the validated-readback provenance marker.

The exporter refuses private fields, non-public values, stale/malformed
identities, duplicate sources, over-limit creators, non-canonical URLs,
partial canaries, digest mismatches and sidecar overwrites. It does not read a
local pipeline database or copy generation timestamps into JSONL.

## Admission and rollback boundary

Admission, readback and rollback methods exist only on the Worker service
binding entrypoint. There is no public write route. Admission rereads each
candidate from `public_projection_receipts`, `public_projection_cards` and
`search_documents`, verifies the exact public tuple and privacy predicates,
then inserts all ten rows in one D1 batch. A replay of the same digest is
idempotent; a conflicting tuple or any validation failure writes nothing.

The ledger is append-only by state transition: `active`, `superseded`,
`removed`, or `rolled_back`. Rows are never hard-deleted. Creator correction
and removal remain the existing email-only path at
[offflinerpsy@gmail.com](mailto:offflinerpsy@gmail.com); there is no public
correction API. The private owner workflow must suppress the source and roll
back its exact public projection before accepting a replacement receipt.

## Remaining private-owner integration gate

This public repository intentionally does not contain the typed private
pipeline-control wrapper. The owner must add that wrapper in the protected
private control plane and limit it to public DTOs and service-binding calls.
It must select the deterministic ten-row public-D1 manifest, record only
allowlisted audit metadata in the private audit system, and preserve the
fail-closed result when the public data does not qualify. No private import
hash, source vault text, transcript, media, contact, inbox or pipeline path
may enter this repository or either public sidecar.

## Safe integration order

1. Owner reviews the private wrapper and confirms the exact ten-row public-D1
   candidate readback.
2. Apply `0005_claim_receipt_ledger.sql` to the intended public D1 only after
   the migration receipt is approved.
3. Deploy the public Worker canary candidate with service binding wiring and
   keep the route held unless the live public-D1 predicates produce exactly
   ten rows.
4. Read back the route/service result, run the exporter and publication
   boundary checks, and compare the API and sidecar ledger digests.
5. Only after those receipts are reviewed may the canary be considered for a
   separately authorized release. This task performs none of those live
   actions.
