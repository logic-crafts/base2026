# Active Phase

Phase 25 — claim-receipt source merged; production held on zero eligibility.
Current checkpoint: 2026-09-02 01:48 UTC. PR34 remains live, public Worker
`f8781f4d-30fd-4d70-ab96-a4e8d718226a` is selected at 100%, and the reviewed
API/MCP artifact has live readback.

## Claim Receipt Ledger — source integrated, not released (2026-09-02)

PR36 merged at `25bca067514fb5efd9bbc84c36c6b3cd73f43d3f` after an independent
NO-GO found five blockers, root fixed all five, and re-review returned GO for
source integration only. The live eligibility read is zero and the live route
is 404, so no remote migration, deploy, sidecar publication, sitemap or
IndexNow action occurred. Exact receipts are in
[the source-integration handoff](HANDOFF_2026-09-02_CLAIM_RECEIPT_SOURCE_INTEGRATION.md).

## Public API/MCP distribution — released (2026-09-01)

The isolated growth integration is now merged through PR34. The public no-key
MCP route reads only public D1, is fail-closed behind `MCP_RATE_LIMIT`, and has
live discovery/tool/readback proof. Member auth, Evidence Search, the current
visual shell and public/private boundary remain intact. Exact release and
rollback receipts are in
[the production handoff](HANDOFF_2026-09-01_PUBLIC_API_MCP_PRODUCTION_RELEASE.md).

## Completed scope

- Source316a39f64 merged through PR31; correction4960c99bd was pushed before
  its exact two-asset public release. Design and other static assets are preserved.
- Two independently reviewed archive-backed articles are published; blog5 and
  five unchanged maintained guides are distinct counts. Do not replay them.
- Two exact unsupported historical cards were withdrawn with private history
  preserved. The later natural projection is separate from those withdrawals.
- Private releases57/58 and additive migration0016 are deployed. Release58
  changes only diagnostic revision filtering over release57's reliability work.

## Remaining work

- Measure discovery and real API/MCP use; accepted IndexNow submission is not
  indexing or traffic.
- Integrate the protected private typed wrapper and wait for exactly ten
  genuine eligible cards before any Claim Receipt migration/deploy/export.
- Observe the bounded cohort and fail-closed holds/retries. At 10:16, 27 admitted
  yielded 6 media, 5 transcripts and one verified projection, not 27 completions.
- Continue two distinct unfinished archive candidates with separate author and
  critic; no filler quota or repeated unchanged-guide publication.
- Keep cleanup pagination/starvation and external deployment/access blockers
  separate; no expanded deletion, old-record resurrection or blind retries.

The editorial office remains every six hours. Private fallback is incident-first
at 04:45/10:45/16:45/22:45 UTC; native five-minute doctor is unchanged.
External silent-outage detection may take six hours plus host availability.
Authoring/review/refill need the Codex host; both legacy local jobs remain paused.

No new scheduler, CMS, paid API, redesign or private-source publication.
Root remains the sole editorial publisher; private operations retains its own
release authority and protected receipts.

[Current state](CURRENT_STATUS.md) ·
[Closure and exact receipts](BASE2026_OFFICE_CLOSURE_2026_08_31.md) ·
[Editorial contract](../BASE2026_EDITORIAL_PUBLISHING.md) ·
[Guide contract](../BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md)
