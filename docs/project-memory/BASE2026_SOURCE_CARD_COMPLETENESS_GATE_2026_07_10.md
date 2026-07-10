# Base2026 Source Card Completeness Gate — 2026-07-10

## Decision

**The local data/card cleanup gate is closed and redesign may now begin against the frozen admission contract.** Production remains unchanged and still reflects the pre-gate live counts below.

## Exact observed counts

| Surface | Source cards | With public Source Intelligence | Without Source Intelligence and Questions | Incomplete |
|---|---:|---:|---:|---:|
| Live production | 1,614 | 680 | **934** | **57.87%** |
| Local frozen corpus | 1,811 | 1,446 | **365** | **20.15%** |

`Questions this source answers` is rendered from public Source Intelligence only. Therefore the sources missing Source Intelligence and the sources missing the Questions block are the exact same set under the current renderer. A live empty-state page was directly verified at `https://aggressorbulkit.online/knowledge/sources/tiktok-video-7658420235816406285.html`.

## Why production is much worse

- 731 of the 934 incomplete live sources are already enriched in the local export but have not been released.
- 203 live sources remain source-only in the local corpus.
- 197 local source records are not on production; 156 of those are source-only and 41 are complete.
- Six live sources have legacy public cards that are absent locally. Four removals are intentional reclassification (`future_cluster_backlog` or `reviewed_no_card`); two require replacement from approved evidence-exact decisions rather than restoring weak legacy cards.

## The 365 local source-only records are fully classified

| Terminal state | Count | Correct product treatment |
|---|---:|---|
| `approved_pending_promotion` | 47 | Promote into KB/export; then normal solution card |
| `future_cluster_backlog` | 119 | Keep private/backlog; exclude from public main-card surface |
| `reviewed_no_card_source_only` | 199 | Provenance/archive surface, explicit source-only state, noindex; not a normal solution card |
| Unclassified | **0** | — |

The 47 approved rows currently live in `reviewed-candidates.jsonl`; `apply-base2026-editorial-decisions.py` intentionally does not promote, rebuild, export, deploy, or publish them.

## Pre-redesign closure gate

- [x] Promote the 47 approved candidates into the local KB/export with exact evidence preserved.
- [x] Encode the 119 future-backlog sources as non-public card inventory.
- [x] Encode the 199 reviewed-no-card sources as provenance/archive records, excluded from normal public search cards and noindexed.
- [x] Rebuild and verify locally:
  - 1,493 complete normal public source cards;
  - 119 private future-backlog sources;
  - 199 archive/source-only records;
  - **0 normal public cards missing Source Intelligence or Questions**.

## Local closure result

Verified at `2026-07-10T16:26:28Z`:

- `source-admission.jsonl`: 1,811 unique source IDs = 1,493 `normal_public_card` + 199 `provenance_archive_noindex` + 119 `future_private_backlog`.
- KB rebuild replayed 910 reviewed candidate claims, including the 47 newly approved editorial rows.
- Canonical local export: 1,493 search documents, 1,692 source records, 2,052 search chunks, 2,276 page passages, 2,396 insight cards, and 1,873 public insight cards.
- Promotion: 47/47 approved source IDs have public Source Intelligence; missing = 0.
- Normal contract: 1,493/1,493 generated pages are `index,follow` and contain both `Source Intelligence` and `Questions this source answers`.
- Archive contract: 199/199 generated pages are `noindex,follow`, carry explicit `Provenance archive` / `Archive status` labeling, and have no Search Workspace CTA.
- Future contract: 119/119 are absent from all public JSONL artifacts, generated pages, creator/topic listings, and sitemaps while remaining in the private ledger/backlog.
- Existing gates: 45/45 unit tests pass; public-export policy passes; content readiness reports 0 blocked records; scoped `git diff --check` passes.

The cleanup gate is closed locally. Redesign is now permitted against these three frozen states. No live deploy, Meilisearch reindex, external indexation, outreach, or commit was performed.

## Receipts

- `.planning/tiktok-pipeline-v2/source-card-completeness-audit-2026-07-10.json`
- `.planning/tiktok-pipeline-v2/source-card-state-ledger-2026-07-10.jsonl`
- `.planning/tiktok-pipeline-v2/local-completeness-gate-receipt-2026-07-10.json`
- `12_knowledge-base/sources/tiktok/source-admission.jsonl`
