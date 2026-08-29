# Base2026 private-pipeline readback R2 — 2026-08-29

Scope: read-only Cloudflare audit. No deployment, restart, hold clearance,
source admission, D1/R2 mutation, external publication, or raw-log export was
performed.

## Runtime

- Private Worker: v0.6.2, deployment
  `14adacb6-7f0f-4aa7-9131-fc41469eec15`.
- Public Worker: `3e06c10b-9fa4-40aa-ad14-913a11b85f30`; public health passed.
- Private migrations: 14 applied, none pending.
- Intake, discovery, capture, AI, private import, narrow public projection, and
  policy-bound automatic publication are enabled.
- The local adapter and broad `PUBLIC_RELEASE_ENABLED` switch remain disabled.
- The automatic-publication hard hold is false.
- Private capture build 0.5.5, Container application version 8:
  one active/running instance, zero failed instances and no reported errors.
  The detail counter still says `healthy=0`; this contradictory telemetry is
  an observation, not evidence of a failed runtime and not a restart trigger.

## Durable state

- Private D1: 339 sources — 1 awaiting capture, 12 awaiting transcription, 3
  awaiting semantic work, 52 imported privately, and 271 in source review.
- No stale lease, failed/dead job, or Queue delivery failure was found.
- Latest discovery: 19 creators; 135 discovered; 17 fresh/admitted; 118
  duplicates; 1 failed source; 0 held by the discovery run.
- Private R2: 1,280 objects including 318 media objects. The media aggregate
  exactly matches the 318 stored-media artifacts recorded in D1.
- Workers AI: 3,943 actual/reserved Neurons across 69 invocations; hard block
  false. Monthly cloud reservations are zero and the monthly hard hold is
  false.
- Automatic publication: 19 applied and 1 already-public receipt; no pending,
  retry, or held receipt. The exact eligible-candidate query returns zero.
- Public D1: 2,175 documents; 1,574 distinct videos; 50 applied projection
  receipts; 83 excerpt cards; `full_transcript_public=0`.

## Source-specific review

`@webhivedigital` is not cycling through capture failures. Twenty eligible
registry entries remain known; eighteen source rows are held for source review
with zero capture attempts/error, while two are imported privately and have
historical applied projection receipts. There is no creator-scoped automatic
publication backlog.

Fresh isolated sources produced bounded `capture_ytdlp_unavailable` and
`capture_ytdlp_failed` holds on 2026-08-29. They are source-specific, private,
and not evidence of a systemic transport regression. Preserve normal retry and
hold policy and investigate only if the same transport signature recurs across
otherwise valid current sources.

## Conclusion

The scheduled pipeline is operational and idle at the publication boundary:
new media exists in private R2/D1, deterministic stages have a bounded backlog,
automatic public projection has no eligible queue, and the zero-full-transcript
privacy invariant holds. No repair or restart is justified by this readback.
