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
- Core routes, Evidence Brief V1/V2, founder hashes, API docs, static sitemap
  (1,634 URLs) and dynamic sitemap (50 URLs) pass live readback.
- The first public engineering journal article is live at
  `/journal/source-backed-video-search-cloudflare/`. Its free distribution is
  live on Medium, X and LinkedIn; the Medium copy canonicals to Base2026.

## Private production pipeline

- Private Worker: v0.6.2, `4d9f291e-0f7e-4795-adb4-e18c5f028d58`
  (100%); rollback `48968a83-9a9f-4824-82a9-d8181b9ffee3`.
- Cron: reconciliation/capture/publication every five minutes; discovery daily
  at 10:00 UTC.
- Private R2/D1 intake, Workers AI, automatic eligible-card publication and
  receipt-based retention are active.
- Latest discovery: 135 discovered, 17 fresh/admitted, 118 duplicates and one
  `browser_discovery_empty`; 18 cursors active, only `@webhivedigital` failed.
- One bounded private canary stored media and completed transcription and
  semantic jobs. It used official Player API Browser acquisition, so it did
  not prove Container fallback.
- Container app v8 is `running`, but Cloudflare telemetry regressed from
  `healthy=1` immediately after one recycle to `active=1, healthy=0, errors=[]`.
  No second restart was attempted; stable readiness remains the real blocker.
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
- Google: processing; 1,634 static and 49 dynamic URLs discovered.
- Bing: processing; 833 static and 39 dynamic URLs discovered.
- Neither engine exposes performance or indexed-page data yet. Do not resubmit
  unchanged URLs or claim discovery counts as indexation.

## Open loops

1. Observe Container readiness without restart loops; prove fallback only on a
   real candidate that requires it.
2. Review `@webhivedigital` as a source problem; do not force a candidate.
3. Observe GSC/Bing after their processing window. Premium founder redesign is
   separate optional scope; the current founder page remains live.
4. Measure referral and discovery signals from Medium, X and LinkedIn before
   duplicating the same article on more editorial platforms.

## Protected boundaries

Never publish private pipeline source, raw media/transcripts, credentials,
provider responses, private owner-profile/CV files, logs, local databases or
generated deployment trees. Never change the public and private Workers in one
unreviewed batch.
