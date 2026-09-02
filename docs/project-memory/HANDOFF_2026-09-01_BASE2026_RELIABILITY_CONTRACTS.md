# Base2026 Reliability Contracts Handoff — 2026-09-01

Handoff ID: `base2026-reliability-contracts-20260901T223336Z`

Status: PR-ready local implementation in the isolated branch
`codex/base2026-reliability-contracts-20260901`. No push, merge, deploy, D1
write, OAuth change, social retry, or external publication was performed.

## Scope and live receipt

This pass is limited to the reliability work needed to make the SEO/product
lane measurable and releaseable. SEO and directory work remains active; this
handoff does not pause either lane, rebuild the office, or add a scheduler.

The read-only production readback recorded in
`docs/reliability/BASE2026_PRODUCTION_MANIFEST_2026-09-01.json` binds the
public Worker version 34 and its 100% traffic deployment, the public redirect
Worker, the logical private Worker release `0.6.6`/deployment ordinal `60`,
custom domains, worker-first patterns, runtime bindings, tracked migrations,
and safe live route/stat checks. Public live stats at readback were 2,198
documents, 1,589 distinct sources, 65 evidence routes, 106 projected cards,
and zero public full transcripts.

The manifest deliberately records two closure failures instead of smoothing
them over: the deployed artifact came from a dirty source candidate, so exact
commit binding and reproducibility remain unresolved; and `AUTH_DB` was
observed in the release/runtime contract but is absent from the tracked
public Worker config in this checkout. Private Worker identifiers and
control-plane source remain withheld.

## Implemented

- `contracts/base2026.production-manifest.schema.json` defines a redacted
  manifest for commit/tree/artifact provenance, Worker versions, routes,
  bindings, migrations, live checks, and unresolved release blockers.
- `contracts/base2026.channel-publication-job.schema.json` defines the v2
  channel state/payload contract. `native_draft_saved` is an explicit legacy
  alias to `held_contract`; any possible external effect must be fenced before
  retry.
- `contracts/base2026.private-pipeline-incident-snapshot.schema.json` defines
  the aggregate input for a bounded incident-closure check without raw private
  artifacts or source content.
- `contracts/base2026.measurement-event.schema.json` defines the privacy-safe
  five-event path: `search_submitted`, `result_opened`, `save_completed`,
  `revisit_completed`, and `export_completed`. Raw query text is not a field.
- `scripts/validate-base2026-reliability.py` is a read-only standard-library
  validator. It validates the manifest, reconciles channel jobs without
  writing receipts, checks bounded incident closure, and validates an ordered
  measurement trace.
- `tests/test_base2026_reliability_contracts.py` covers known channel drift,
  no-replay behavior, incident closure gates, privacy-safe events, and contract
  JSON versions.

## Current channel reconciliation

The current external job set was inspected through the new read-only command;
job contents were not rewritten:

| Channel | Observed state | Canonical disposition | Next action |
| --- | --- | --- | --- |
| DEV | `native_draft_saved` | `held_contract` | `repair_job_contract` |
| X | `publishing` | `fenced_no_retry` | `inspect_same_external_target_before_retry` |
| LinkedIn | `published_verified` | `terminal_verified` | `none` |
| Medium | `published_verified` | `terminal_verified` | `none` |

The readback is 4 jobs / 2 invalid, with zero external actions and zero
replays. X remains mutually exclusive with any automatic retry until the same
external target is read back. Existing terminal publication receipts remain
immutable.

## Incident-closure check

The new check closes an incident only when a production-identity bounded cohort
has terminal receipts for every item, orphan jobs are zero, public projection
count is zero, accounting is complete, no external effect was replayed, and
the two subsequent doctor runs are healthy without the incident. The current
live aggregate still cannot close: its health readback identifies `shadow`
environment and the recent doctor runs remain degraded by the AI-runtime
incident. No private cohort was executed by this pass.

## Measurement status

The five-event contract and validator are implemented as staging artifacts only.
No live event emission, analytics schema, database write, or tracking
deployment was made. A future canary must use one opaque trace/query reference,
bucketed properties, and actor continuity across save → revisit → export.

## Live-unapplied recommendations

1. Produce a clean source commit from the exact deployed candidate and prove
   commit/tree/artifact equality before any deployment.
2. Add and verify `AUTH_DB` plus member migration declarations in the tracked
   release config, then perform a fresh full migration readback.
3. Refresh private environment identity and migration state from the protected
   control plane before mutation.
4. Feed a bounded synthetic cohort into the private owner-controlled process,
   then require terminal accounting, zero orphans, and two subsequent doctor
   runs that are not degraded by the incident.
5. Stage the measurement emitter and run a separate privacy/canary review.
   Do not retry X or repair DEV by replaying an unknown external effect.

## Review receipt

The implementation pass includes a reviewer check for scope, public/private
leakage, documentation pointers, concrete next action, and no external
mutation.

Verification completed:

- `python3 -m pytest -q`: 92 passed.
- `python3 -m unittest tests.test_base2026_reliability_contracts -v`: 8 passed.
- Worker `npm test`: 3 files / 37 tests passed.
- Worker `npm run typecheck`: passed.
- `python3 scripts/audit-publication-boundary.py --json`: 12 public-safe
  candidates, 0 needs-review, 0 forbidden, 0 secret findings.
- The manifest validator passed structurally with `release_ready: false` by
  design. The channel validator read 4 jobs and returned its expected non-zero
  hold status for 2 invalid jobs; it performed no external action or replay.
