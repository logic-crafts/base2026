# Project State

Last verified: 2026-08-29

Canonical current snapshot: [`CURRENT_STATUS.md`](CURRENT_STATUS.md).

Base2026 is live at `https://base2026.dev/` as an open-source video research
engine. Public Workers Static Assets and D1 FTS5 serve the product; a separate
private Cloudflare Worker, D1, R2, Queues, Workflows, Workers AI, Browser
Rendering and restricted Container run the cloud-only intake pipeline.

The public product is healthy. The private pipeline is producing media and
public projections, but creator discovery is degraded for 12 of 19 cursors and
is under bounded repair. Google and Bing accept both sitemaps but are still
processing initial measurement data.

Public Git authority is `offflinerpsy/base2026` `origin/main` at
`616d6de4c64c13fa91bbc589f0a59fddbcd69a63`. Current integration work happens
only in the clean branch/worktree recorded in `CURRENT_STATUS.md`; historical
dirty checkouts must not be staged or cleaned wholesale.

Older production narratives remain available in Git history and dated receipts.
Do not append them back into this file.
