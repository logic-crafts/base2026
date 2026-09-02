# Public Claim Receipt Ledger Schema

Version: `base2026.claim-receipt-ledger.v1`

This is a public immutable evidence contract. It contains attribution and a
bounded reviewed excerpt only. It never contains raw captions, ASR, full
transcripts, media, contact details, private import hashes, private paths or
pipeline-control state.

## Read response

`GET|HEAD /api/claim-receipts/v1?canary=base2026.internal-linking.canary.v1&topic=internal-linking`

The JSON response has exactly these keys:

```json
{
  "schema_version": "base2026.claim-receipt-ledger.v1",
  "canary_id": "base2026.internal-linking.canary.v1",
  "topic": "internal-linking",
  "policy_version": "base2026.claim-receipt-admission.v1",
  "count": 10,
  "ledger_sha256": "<64 lowercase hex characters>",
  "generated_at": "<ISO-8601 response timestamp>",
  "receipts": []
}
```

`receipts` contains exactly ten rows in `selection_rank` order. A row has the
following keys:

```text
schema_version, receipt_id, canary_id, selection_rank,
source_id, projection_id, card_id, search_id, card_ordinal,
creator_handle, creator_display_name, creator_url, original_url, video_id,
base2026_url, published_at, published_date,
claim_text, suggested_action, topic_label, evidence_excerpt,
evidence_start_seconds, evidence_end_seconds,
public_projection_receipt_sha256, policy_version
```

The `receipt_id` is the SHA-256 of the canonical immutable row with
`receipt_id` omitted. `ledger_sha256` is the SHA-256 of those canonical rows,
one JSON object per line with a final newline. Ledger state and D1 timestamps
are intentionally absent from the public digest. Evidence timecodes are
bounded to 0–86,400 seconds and millisecond precision so JavaScript and Python
produce the same canonical JSON numeric representation; more precise values
are rejected rather than rounded silently.

## Static sidecar manifest

The deterministic exporter writes
`claim_receipts_manifest.json` with exactly these keys:

```json
{
  "schema": "base2026.claim-receipt-static-manifest.v1",
  "canary_id": "base2026.internal-linking.canary.v1",
  "topic": "internal-linking",
  "policy_version": "base2026.claim-receipt-admission.v1",
  "count": 10,
  "ledger_sha256": "<same API digest>",
  "jsonl": "claim_receipts.jsonl",
  "jsonl_sha256": "<64 lowercase hex characters>",
  "generated_from": "validated-public-d1-readback"
}
```

The JSONL sidecar has no nondeterministic timestamp. It is generated only from
validated public-D1 readback, never from a local private table or stale static
file.
