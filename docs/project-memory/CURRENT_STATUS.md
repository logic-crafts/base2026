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
- Worker: `1ad991e4-bc8f-4c34-a8d1-c77723377137`
- Public D1: 2,175 documents; 1,574 distinct videos; 50 applied projections;
  83 projected cards; zero public full transcripts.
- Core routes, Evidence Brief V1/V2, static sitemap (1,634 URLs) and dynamic
  sitemap (50 URLs) pass live readback.
- `/founder` campaign hero is live. Its source is being synchronized into the
  clean public Git candidate described below.
- Candidate improvement: `/api/stats` plus live homepage/analytics counters;
  not deployed until all gates and review pass.

## Private production pipeline

- Private Worker: v0.6.2, deployment
  `48968a83-9a9f-4824-82a9-d8181b9ffee3` at the last readback.
- Cron: reconciliation/capture/publication every five minutes; discovery daily
  at 10:00 UTC.
- Private R2/D1 intake, Workers AI, automatic eligible-card publication and
  receipt-based retention are active.
- Current degradation: 12 of 19 creator cursors report
  `browser_discovery_empty`; repair is isolated to the private pipeline task.
- Broad `PUBLIC_RELEASE_ENABLED=false` remains correct. The narrow, policy-bound
  automatic projection lane remains enabled.

## Git authority

- Canonical public repository: `https://github.com/offflinerpsy/base2026`
- Canonical baseline: `origin/main` at
  `616d6de4c64c13fa91bbc589f0a59fddbcd69a63`.
- Clean integration candidate:
  `/Users/alexyarosh/Projects/base2026-migration/DW/.worktrees/base2026-consolidate-20260829`
  on `codex/base2026-consolidate-20260829`.
- The original SEO/GEO checkout and historical worktrees are dirty snapshots.
  Never bulk-stage, reset, merge, prune or delete them.

## Search-engine measurement

- Google Search Console and Bing both accept the static and dynamic sitemaps.
- Google: processing; 1,634 static and 49 dynamic URLs discovered.
- Bing: processing; 833 static and 39 dynamic URLs discovered.
- Neither engine exposes performance or indexed-page data yet. Do not resubmit
  unchanged URLs or claim discovery counts as indexation.

## Open loops

1. Finish and verify the private creator-discovery repair.
2. Reproduce live `/founder`, live stats and truthful API/analytics docs from
   the clean public candidate; run full tests and publication audit.
3. Commit/push through a reviewed public branch, deploy the exact candidate,
   and verify live hashes/API/privacy invariants.
4. Observe GSC/Bing after their processing window. Premium founder redesign is
   a separate optional selection; the current founder page remains live.

## Protected boundaries

Never publish private pipeline source, raw media/transcripts, credentials,
provider responses, private owner-profile/CV files, logs, local databases or
generated deployment trees. Never change the public and private Workers in one
unreviewed batch.
