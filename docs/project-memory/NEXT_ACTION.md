# Next Action

Checkpoint: 2026-09-06 — Source Laboratory presentation candidate.
Continue from [the design handoff](HANDOFF_2026-09-06_SOURCE_LAB.md).
The active product phase remains Phase 29.

1. HQ accepted the desktop/mobile design and requested a final copy delta.
   That delta is complete in v4; HQ now integrates the accepted candidate.
   The candidate covers the homepage, tools and forms, public workspace,
   catalog/source pages, editorial/docs families and the signed-out member
   shell. It is a local source candidate, not a merged or deployed release.
2. Use the latest accepted public artifact as the build input and pass both
   `--members-workspace` and `--retain-member-script`. The repository's default
   asset path and optional member runtime are older than the accepted auth
   recovery release; they are not a deployment baseline.
3. Apply only the projected-source presentation patch to HQ's current private
   Worker source. Its applicability is checked; auth implementation, bindings,
   private data and member logic remain owned by their existing engineering
   lane. Complete HQ's normal combined runtime checks before any release.
4. Preserve the exact released WordPress 0.1.0 and 0.1.1 downloads, current
   member runtime, source/API contracts, metadata, forms and hidden states.
   The supplied-HTML check does not establish live HTTP, crawling or indexing.
5. No merge, push, deployment or intake automation is authorized by this
   candidate. HQ owns the release decision; Chief remains the sole existing
   AgencyOS/board writer. Keep ongoing Growth, Directories and Media work in
   their existing tasks without duplicate queues, offices or timers.

Earlier Studio delivery checkpoints remain in
[the September 5 handoff](HANDOFF_2026-09-05_PRODUCT_STUDIO.md) and
[the RC2 integration handoff](HANDOFF_2026-09-05_STUDIO_INTEGRATION.md).
Those dated source snapshots do not override the newer accepted deployment.
