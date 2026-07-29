# Base2026 daily shell normalization — production closure

**Status: deployed and live-verified.**

- New production release: `base2026-daily-batch-20260729-shell-normalized`.
- Previous release retained as rollback: `base2026-daily-batch-20260728-03-release`.
- The post-generation normalizer replaced the shared header/footer shell on all **4,209** emitted HTML pages. It passed with zero failures and preserved the body-content fingerprints for every page.
- The production symlink was atomically switched only after the staging report passed; nginx configuration validation and reload passed.
- Protected artifacts are byte-identical to the previous daily release: sitemap, public dataset manifest, documents JSONL, and passages JSONL. Meilisearch, IndexNow, source data, and sitemap membership were not changed.
- Browser QA after a reload: `/knowledge/` has the canonical V4 body classes, header/footer, four footer navigation groups, no desktop or mobile horizontal overflow, and uses release-versioned shell CSS assets.

## Separate root-site interaction hotfix

- The WordPress `alex-yarosh` child-theme mega-menu hover bridge was copied to production after a server-side backup and exact SHA-256 read-back.
- WordPress object cache and Cache Enabler page cache were cleared.
- Live desktop interaction QA moved the pointer from Services through the former gap into the panel. The mega menu stayed visible and interactive; no horizontal overflow was detected.

No production rollback was needed.
