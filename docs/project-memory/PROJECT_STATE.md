# Project State

Public release verified: 2026-08-30; private and search-console snapshots: 2026-08-29.

Canonical current snapshot: [`CURRENT_STATUS.md`](CURRENT_STATUS.md).

Base2026 is live at `https://base2026.dev/` as a free, open-source video
research engine. Workers Static Assets and public D1 FTS5 serve the product;
a separate private Cloudflare Worker, D1, R2, Queues, Workflows, Workers AI,
Browser Rendering and restricted Container run cloud-only intake.

The public product includes the technical closeout through deployed source
`0ced3a5c03554d1316397c5cbeceeb697a4d5c05`. Live
statistics, Evidence Brief V1/V2, founder page, API documentation, Analytics,
both sitemaps and the first engineering journal article pass production
readback. The public privacy invariant remains zero full transcripts.

The journal article is also live on Medium with a canonical back to Base2026,
and adapted launch posts are live on X and LinkedIn. These are free editorial
distribution receipts, not paid ranking links.

The 2026-08-29 private discovery snapshot recorded 135 discovered / 17 fresh / 118
duplicates / one source-review failure. Private D1 has 339 sources, and R2's
318 media-object aggregate exactly matches D1. No stale leases, failed/dead
jobs, Queue failures, or automatic-publication backlog exist. The Cloudflare
Container is active/running with no errors or failed instance while its detail
counter remains `healthy=0`; do not loop restarts for this telemetry mismatch.

The 2026-08-29 Google snapshot reports 22 early impressions across 13 pages with zero clicks and
average position 55.4. Page indexing/Links and Bing performance are still
processing; Bing's live journal test is eligible while its index view remains
discovered-not-crawled. Historical dirty checkouts remain protected. Older
narratives stay in Git history and dated receipts; do not append them back into
this file.

The sitemap, security-header, cache, API-index and roadmap-release fixes are
live on public Worker `eeeabd1b-7454-4ec5-9ac3-6b35d3bb3fa3`. Artifact tree:
`02dc9883597dfab6215cb10b2082c19c804fda21bbbc3e71fe882a2d273a3065`.
The release also fixes replay of the Workspace Project Story link and generated
build metadata. Public data and the approved visual design are unchanged.
See [`BASE2026_TECHNICAL_RELEASE_2026_08_30.md`](BASE2026_TECHNICAL_RELEASE_2026_08_30.md).
