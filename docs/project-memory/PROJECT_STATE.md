# Project State

Last verified: 2026-08-29

Canonical current snapshot: [`CURRENT_STATUS.md`](CURRENT_STATUS.md).

Base2026 is live at `https://base2026.dev/` as a free, open-source video
research engine. Workers Static Assets and public D1 FTS5 serve the product;
a separate private Cloudflare Worker, D1, R2, Queues, Workflows, Workers AI,
Browser Rendering and restricted Container run cloud-only intake.

The public product and exact Git source are synchronized through PR #26. Live
statistics, Evidence Brief V1/V2, founder page, API documentation, Analytics,
both sitemaps and the first engineering journal article pass production
readback. The public privacy invariant remains zero full transcripts.

The journal article is also live on Medium with a canonical back to Base2026,
and adapted launch posts are live on X and LinkedIn. These are free editorial
distribution receipts, not paid ranking links.

Private creator discovery remains recovered at 135 discovered / 17 fresh / 118
duplicates / one source-review failure. Private D1 has 339 sources, and R2's
318 media-object aggregate exactly matches D1. No stale leases, failed/dead
jobs, Queue failures, or automatic-publication backlog exist. The Cloudflare
Container is active/running with no errors or failed instance while its detail
counter remains `healthy=0`; do not loop restarts for this telemetry mismatch.

Google now reports 22 early impressions across 13 pages with zero clicks and
average position 55.4. Page indexing/Links and Bing performance are still
processing; Bing's live journal test is eligible while its index view remains
discovered-not-crawled. Historical dirty checkouts remain protected. Older
narratives stay in Git history and dated receipts; do not append them back into
this file.

A reviewed but undeployed source candidate fixes the remaining sitemap,
security-header, cache, API-index and roadmap-release defects. Its artifact tree
is `6b4dddd702917831e574153f36261d62c2f1b090ffcbbe78c20eba24a74c5e09`.
Do not describe these fixes as live until a separate deployment task produces a
new Worker/version and production readback.
