# Base2026 Current Status

Verified 2026-09-02 through 00:44 UTC. Public counters below are the current
live read. [API/MCP production receipt](HANDOFF_2026-09-01_PUBLIC_API_MCP_PRODUCTION_RELEASE.md)
and [closure receipt](BASE2026_OFFICE_CLOSURE_2026_08_31.md)
separates completed releases from remaining observation and external blockers.
Older dated receipts are history, not current counters.

## Live product

- Claim Receipt Ledger source is merged through
  [PR36](https://github.com/offflinerpsy/base2026/pull/36), merge
  `25bca067514fb5efd9bbc84c36c6b3cd73f43d3f`, but it is not live. Exact
  public-D1 eligibility is 0 cards /0 sources /0 creators and the live route
  returns404. Migration0005, Worker deploy, sidecars, sitemap and IndexNow were
  deliberately withheld; no claim pages or traffic are asserted.

- Public Worker `f8781f4d-30fd-4d70-ab96-a4e8d718226a` is at 100%. It adds
  live read-only MCP, API/integration guidance and `MCP_RATE_LIMIT` while
  preserving Evidence Search, member auth/My Research, four D1 bindings, three
  remote member secret names and both `/guides` aliases. Immediate rollback is
  `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e`.
- `/api`, `/mcp` and `/integrations` are live200, canonical and indexable.
  Modern discovery, six-tool listing, bounded search, legacy initialization,
  invalid-header rejection and no-id notification behavior passed live.
- Evidence Search is live200, self-canonical, indexable and in the hub sitemap.
  A real D1 search rendered ten deduplicated records from 24 returned hits;
  no-JS fallback, mobile390 and console0 QA passed. IndexNow accepted exactly
  this new URL with HTTP200; indexing/traffic are not proved.
- Public `/api/stats` and direct D1 at 00:44: **2,198 documents, 1,589 distinct
  sources, 65 evidence routes, 106 projected cards, zero full transcripts**.
  The earlier 09:16 total of 2173/1572/48/81/0 followed two exact unsupported
  card withdrawals. Their private history remains; neither was a guide dependency.
- Blog/API/RSS contain **five articles**; all five maintained guides retain
  their approved revision-1 hashes. Two distinct archive-backed articles are
  now live: [content backlog](https://base2026.dev/blog/evidence-first-content-backlog/)
  and [comparison-page evidence check](https://base2026.dev/blog/comparison-page-evidence-check/).
  Exact hashes and recorded publication times are in the closure receipt.
- Both new articles passed independent review, exact live API/hash checks,
  HTML/feed/sitemap checks and Chrome 1440/390 QA with no overflow or errors.
  All 31/29 same-origin links passed. IndexNow accepted each new URL once;
  acceptance is not indexing, citations or traffic.
- The newly projected source was verified at 10:17: two public cards,
  source HTML/canonical/indexability, dynamic sitemap, catalog page 2, two
  normal search queries and desktop/mobile QA. This proves one natural
  end-to-end path, not creator truth or complete daily processing.

## Source, release and recovery

- Source `316a39f64190d9e2133aba600ea22a5008c604ef` merged through
  [PR31](https://github.com/offflinerpsy/base2026/pull/31) at 09:27:49 UTC;
  remote main was `d05f1b0efd30eeadb4c086331b8fbe3fd1131ef5`.
  Correction `4960c99bd84a9384e3f3083e18b0389a4f21967c` was pushed before
  the 09:39 two-asset deployment. [PR32](https://github.com/offflinerpsy/base2026/pull/32)
  tracks the correction and final documentation. Read its GitHub merge receipt
  before further releases; this dated snapshot does not preclaim integration.
- The initial source gate passed 597 Worker/56 Python tests, typecheck,
  exact-artifact dry-run and artifact policy. Its six filename-classification
  exceptions were individually reviewed. The later 59-file source manifest
  supersedes the original 51 pins. Local checks are not CI: zero GitHub checks
  and no GitHub Actions workflows are claimed.
- Git source, the reviewed static artifact and live D1/private state are
  separate restore inputs. Generated/private material is not committed.
  Public compatible rollback is `a63f4c74-b6b2-4935-a392-61003d28567a`;
  never restore a pre-guide Worker over guide-kind data.

## Private reliability: deployed, with bounded outcomes

- Release 57 deployed at 09:57:24 after additive migration 0016 at 09:55:59.
  Its gate passed 387 Worker/18 courier tests, types and dry-run, with all
  45 bindings preserved. It adds complete attributed-segment selection,
  a veto for contradictory retain/negative-classification decisions and
  prompt-fit checks, terminal false-wait repair,
  source capture leases and atomic operation accounting. Hashes are not truth.
- Release 58 deployed at 10:15:41.832, 100%: only the two-file diagnostic
  revision filter changed. Independent review, 388 Worker/18 courier tests,
  types/dry-run, health, no pending migration and 45-binding parity passed.
  One fresh R2 artifact byte/hash readback passed at 10:16.
- Owner's 10:16 cohort: 27 admitted, 6 media, 5 transcripts, one packet,
  one import and one verified projection. The five semantic attempts are
  classified as 1 packet / 2 review classifications / 2 contract holds.
  The final owner receipt reports 18 unique source-state corrections
  (16 historical/2 fresh), with zero terminal false-wait backlog.
  Not all 27 are processed;
  the next tick is ongoing, one external capture failure has bounded retry,
  and semantic holds remain fail-closed.
- Diagnostic rollback is release 57. Older release 56 requires zero active
  capture leases and zero reserved/settling/uncertain operations; preserve
  migration 0016 and its ledger. Uncertain operations are held, not refunded
  or replayed. Recovery is limited to evidenced pending-media work, not
  resurrection of withdrawn records. Cleanup pagination/starvation remains
  separate; no expanded deletion authority.

## Automation and external limits

- Editorial office: every six hours, all helpers Sol Max, separate author/
  critic and one publisher. Comparison is completed; two distinct archive
  candidates remain, not approved publications. Unchanged guides are not redated.
- Private fallback: 04:45/10:45/16:45/22:45 UTC, incident-first; its dated
  release-57 prompt was refreshed. Native five-minute doctor is unchanged.
  External silent-outage detection can take six hours plus host availability.
  Authoring/review/refill still need the Codex host; both legacy local jobs stay paused.
- Golem remains 404: Actions startup and unavailable authorized SSH block
  deployment. It is not a live backlink. Instagram capture is unproved;
  dataset mirrors remain held for rights/provenance. Direct GPT Work incident
  delivery is unverified; no dispatch is claimed.
- The orphan enrichment entry is retired without a replacement page; 59
  other entries are preserved, not newly certified. X's 08:20 snapshot remains
  four sent/five scheduled, with no new posts in this closure. LinkedIn keeps
  its Computer Use/action-time gate. GSC's 45 impressions/0 clicks are dated
  Aug27–28; no growth result is invented.
