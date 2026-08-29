# Base2026 Current Status

Verified: 2026-08-29

This is the one-screen operating snapshot. Live Cloudflare receipts override
dated counters. Git history and dated receipts preserve older states; do not
append historical narratives here.

## Product

Base2026 is a free, open-source video research engine. It turns eligible public
expert videos into attributable evidence cards and searchable public pages.
The scheduled production path is Cloudflare-native and does not require the
MacBook or ChatGPT Web.

## Public production

- Domain: `https://base2026.dev/`
- Worker: `3e06c10b-9fa4-40aa-ad14-913a11b85f30` (100%).
- Exact artifact tree:
  `e04bc4be2b46a29de89fd7f59bf4e845ef686d3d9036b28f5439c6a8908a011c`.
- Immediate rollback: `fadc6c25-1d9f-4805-aed2-614e1463a018`.
- Public D1: 2,175 documents; 1,574 distinct videos; 50 applied projections;
  83 projected cards; zero public full transcripts.
- Homepage and Analytics refresh these totals from read-only `/api/stats`.
  Analytics also preserves verified 2026-07-29 summary totals without empty
  historical ranking sections.
- Core routes, Evidence Brief V1/V2, founder hashes and API docs pass live
  readback. The current static sitemap contains 1,636 unique URLs and the
  dynamic sitemap 50; GSC's last processed copies report 1,634 and 49.
- The first public engineering journal article is live at
  `/journal/source-backed-video-search-cloudflare/`. Its free distribution is
  live on Medium, X and LinkedIn; the Medium copy canonicals to Base2026.

## Private production pipeline

- Private Worker: v0.6.2, `14adacb6-7f0f-4aa7-9131-fc41469eec15`
  (100%). Resolve its immediate rollback from the live deployment list before
  any mutation; this readback made no rollback selection.
- Cron: reconciliation/capture/publication every five minutes; discovery daily
  at 10:00 UTC.
- Private R2/D1 intake, Workers AI, automatic eligible-card publication and
  receipt-based retention are active.
- Latest discovery: 135 discovered, 17 fresh/admitted, 118 duplicates and one
  failed source across 19 creators. The failed `@webhivedigital` cursor remains
  a source-review issue, not a capture retry loop.
- Private D1 has 339 sources; R2 has 1,280 objects including 318 media objects,
  exactly matching D1's stored-media aggregate. There are no stale leases,
  failed/dead jobs or Queue delivery failures.
- Automatic publication has 19 applied and 1 already-public receipt, no
  pending/retry/held receipt, and zero currently eligible candidates.
- Container image 0.5.5 / app v8 has one active/running instance, no failed
  instance and no errors. Cloudflare's detail counter still says `healthy=0`;
  this is contradictory telemetry, not a restart trigger or proof of failure.
- Hourly heartbeat `base2026-private-pipeline-hourly-watchdog` is active in the
  dedicated pipeline task. It is read-only first and explicitly forbids another
  restart for this incident without a real Container-required failure.
- Broad `PUBLIC_RELEASE_ENABLED=false` remains correct. The narrow, policy-bound
  automatic projection lane remains enabled.

## Git authority

- Canonical public repository: `https://github.com/offflinerpsy/base2026`
- PR #19 merged the consolidated source; PR #20 merged the independent-review
  Analytics correction; PR #23 shipped the reviewed public dataset; PR #26
  shipped the engineering journal. Current production source merge:
  `74662da45f70316279b963e231eaecc6cd4ed79c`.
- The original SEO/GEO checkout and historical worktrees are dirty snapshots.
  Never bulk-stage, reset, merge, prune or delete them.

## Search-engine measurement

- Google Search Console and Bing both accept the static and dynamic sitemaps.
- Google now exposes early three-month performance: 0 clicks, 22 impressions,
  0% CTR and average position 55.4. Thirteen pages have impressions; the
  historical `.html` AI-citation topic leads with 8 while Google recrawls the
  corrected extensionless canonical topology.
- Google Page indexing and Links still process; the new journal is not indexed.
- Bing still prepares Search Performance. Its journal live test reports that
  the URL can be indexed with no SEO/GEO issue, while the index view says
  discovered but not crawled. Sitemap totals remain 872 discovered URLs.
- Do not resubmit unchanged URLs or claim discovery/impression counts as
  indexation.

## Reviewed local closeout — not deployed

- The current source branch fixes the Workspace sitemap mismatch, conflicting
  JSONL cache directives, API-index Workspace URL, stale roadmap overlay,
  baseline Worker security headers and trailing-slash dynamic-source canonical;
  `/sources/*` is explicitly routed Worker-first for that contract.
- Candidate artifact tree:
  `6b4dddd702917831e574153f36261d62c2f1b090ffcbbe78c20eba24a74c5e09`;
  artifact policy, tests, deterministic import and explicit-assets Wrangler
  dry-run pass.
- These fixes are source/GitHub candidates only. The live Worker and public
  artifact above remain unchanged because this task excluded deployment and
  further external publication.

## Open loops

1. Observe Container readiness without restart loops; prove fallback only on a
   real candidate that requires it.
2. Keep `@webhivedigital` in source review; do not force a candidate or mistake
   its zero-attempt holds for a transport failure.
3. Let Google recrawl the corrected canonicals and Bing finish processing;
   measure query/page growth without resubmitting unchanged URLs.
4. Measure referral and discovery signals from the existing distribution
   before creating or publishing another copy of the same article.

## Protected boundaries

Never publish private pipeline source, raw media/transcripts, credentials,
provider responses, private owner-profile/CV files, logs, local databases or
generated deployment trees. Never change the public and private Workers in one
unreviewed batch.
