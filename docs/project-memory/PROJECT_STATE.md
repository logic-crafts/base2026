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

Private creator discovery recovered from 7 active / 12 failed cursors to 18
active / 1 source-review failure. One private media canary completed, but the
Cloudflare Container reports contradictory telemetry (`running`,
`active=1`, `healthy=0`) after one bounded recycle. Do not loop restarts; treat
stable Container readiness as the remaining infrastructure observation.

Google and Bing accept both sitemaps but are still processing measurement
data. Historical dirty checkouts remain protected. Older narratives stay in
Git history and dated receipts; do not append them back into this file.
