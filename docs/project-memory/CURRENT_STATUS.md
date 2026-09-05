# Base2026 Current Status

## Current — September 5 Studio continuation

This checkpoint supersedes the September 4 status below. Resume through
[the Studio operating guide](../BASE2026_STUDIO_OPERATING_GUIDE.md),
[PROJECT_STATE.md](PROJECT_STATE.md), [NEXT_ACTION.md](NEXT_ACTION.md) and
[the current handoff](HANDOFF_2026-09-05_PRODUCT_STUDIO.md).

Tools Studio and the installable WordPress Evidence Sidebar beta are live
on public Worker `ab2589fa-36a4-4bdb-985f-e66a383c8d6d`. Public routes,
exact download identity and signed-out private guards passed release readback.
[PR54](https://github.com/offflinerpsy/base2026/pull/54) merged at
2026-09-05 18:37:53 UTC as
`d5116a3f06ecfa0bd4888b4417d4e6227b728f8f`; source publication is complete.

Auth is enabled and Google consent is complete. The actual application error
is `account_not_linked`; the earlier Chrome block hid that result. Existing
member data and saved research remain intact. There is no newly established
owner-login action and no successful current Google round-trip receipt.
The four-file error-UX/native-regression source merged through
[PR55](https://github.com/offflinerpsy/base2026/pull/55) at 19:02:37 UTC as
`1fdd877022277f1f4387f543168f3944e174b9c0`; it is not deployed and does
not repair identity binding. Identity continues its separate private source
diagnostic; browser allocation is tracked by Chief in the existing private
operations registry, not inferred from an earlier handoff.

Separate Product Engineering and Design & Media departments join the existing
Identity, Editorial & Distribution, Directories and Chief Engineering owners.
HQ owns decisions, integration, merges and public releases. AgencyOS remains
the existing operational registry with one supervisor and designated writers.
An old worktree or local candidate is not the deployed product.

Chief has built one clean combined candidate from main `8dd92483`, exact
PR57 `b3c1326a` and PR58 `b5dd2fb9`, with reviewed media, a sixth Page Source
Check card/sitemap and the completed temporary Playground demo link. It is
not merged or deployed. The retained-data RC2 contains 4,293 files; exact
identity, tests and review limits are in the
[integration handoff](HANDOFF_2026-09-05_STUDIO_INTEGRATION.md).
Page Source Check inspects supplied HTML; the full
arbitrary-URL live audit remains unfinished. Design's factory is an
illustration, visibly separate from timestamped public inventory data.
Growth departments continue their existing tasks and send history. One free
mcpservers.org submission showed success at 19:01:23 UTC and awaits review;
there is no accepted listing/backlink receipt. The cloud research returned
the full existing report as plain text after its earlier artifact-reference
limitation. Direct readback verified retrieval without repeating the research;
the report's external claims still require action-time source checks.
Media Office now owns the pilot and two next episode cards, using the existing
video renderer. Prepared cards and one submitted take are not final videos.
The existing X assistant is under bounded local repair with public effects
OFF; original publishing remains Growth-owned. A separate ClaudeRules
submission is pending review. Medium publication is held at sign-in with no
draft or publish effect; other authorized Growth work continues.
Release, submission and QA do not establish visitors or repeat use.

## Historical checkpoint — September 4, 21:27 UTC

Verified 2026-09-04 through 21:27 UTC. Public Worker
`3ecddaf3-f594-4b4a-91d4-fd409bd62e4a` is live at 100%; compatible immediate
rollback is `327a21a5-ca54-457c-8099-aa2447a7fe1a`. The current public counters
are 2,268 documents / 1,644 distinct sources / 120 evidence routes / 176
projected cards / zero full transcripts.

Evidence Search, Source Diversity Check and Source-backed Brief are live. Their
bounded first-party activation sink is live in Analytics Engine dataset
`base2026_activation_v1`; initial counts are QA smoke, not visitors. Member auth
remains deliberately fail-closed during the migrated-account contour. Current
artifact, bindings, IndexNow and live QA are in
[the combined release receipt](HANDOFF_2026-09-04_SOURCE_BRIEF_ACTIVATION_RELEASE.md).
Older dated receipts and counters below are history, not the current release.

### Product at the September 4 checkpoint

- Three-tool workflow: Evidence Search -> Source Diversity Check ->
  Source-backed Brief. All three routes are HTTP 200, self-contained and use
  only bounded public MCP reads.
- `POST /api/mcp` lists six read-only tools; `GET /api/mcp` correctly returns
  405. `/api/auth/session` correctly returns 503 `MEMBER_AUTH_DISABLED`.
- Source-backed Brief live QA resolved two public records, kept one unresolved
  record explicit, rendered three bounded excerpts and preserved a query-free
  URL with Markdown/JSON export controls.
- Analytics rejects route/event mismatch with 400 and wrong origins with 403;
  SQL readback proved the dataset and brief event classes.
- IndexNow accepted only the new Brief canonical once. Notification acceptance
  is not indexing, traffic or conversion.

## Historical product baseline through 2026-09-03

- Public Worker `99849d8e-802d-4e8e-a840-8d352f176da6` is live at 100% with
  the crawl-derived SEO/GEO repair. Recursive sitemap readback is 1,874/1,874
  unique with zero duplicate membership. Source catalog, source pagination,
  representative static/dynamic source pages, API/MCP, Evidence Search and
  My Research all pass live. The exact audit and release receipt is
  [HANDOFF_2026-09-03_DATAFORSEO_SEO_GEO_PRODUCTION_RELEASE.md](HANDOFF_2026-09-03_DATAFORSEO_SEO_GEO_PRODUCTION_RELEASE.md).
  Final source correction is merged through
  [PR39](https://github.com/offflinerpsy/base2026/pull/39), merge
  `fa9d30bfdb0489bc031164101aebfeae5fecb55c`.
- Rejected canary `f298cd98-6125-4bfe-ab72-afd98467b8ad` was rolled back after
  `/sources/` 503 and `/my-research/` 404. Never restore it. Immediate healthy
  rollback is final pre-description Worker `14174d46-c237-4ad9-897c-7952060f3e70`;
  member-safe SEO Worker `60429ef4-b1b8-47dc-9af4-b4b882ac2390` is a second-level rollback.

- Claim Receipt Ledger source is merged through
  [PR36](https://github.com/offflinerpsy/base2026/pull/36), merge
  `25bca067514fb5efd9bbc84c36c6b3cd73f43d3f`, but it is not live. Exact
  public-D1 eligibility is 0 cards /0 sources /0 creators and the live route
  returns404. Migration0005, Worker deploy, sidecars, sitemap and IndexNow were
  deliberately withheld; no claim pages or traffic are asserted.

- Previous API/MCP Worker `f8781f4d-30fd-4d70-ab96-a4e8d718226a` remains the
  immediate healthy rollback. Its read-only MCP, API/integration guidance,
  rate limit, Evidence Search, member auth/My Research and binding contract are
  preserved by the current `99849d8e-802d-4e8e-a840-8d352f176da6` release.
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
