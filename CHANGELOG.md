# Changelog

All notable public-facing changes to Base2026 are summarized here.

Base2026 is early, so this changelog focuses on useful release milestones rather than every internal pipeline run.

## 2026-08-30 — Technical SEO and release-contract fixes

Live public Worker: `eeeabd1b-7454-4ec5-9ac3-6b35d3bb3fa3`.

### Fixed

- Removed the `noindex` Workspace from the hub sitemap while preserving its
  internal discovery links.
- Unified baseline security headers across Worker API, dynamic HTML/XML,
  redirects and Static Assets responses.
- Added a canonical 308 for trailing-slash dynamic source variants and routed
  `/sources/*` Worker-first so the contract is consistent after deployment.
- Removed conflicting static JSONL cache directives and corrected the
  machine-readable Workspace URL.
- Made the current tracked roadmap page part of the deterministic release
  overlay so the old VPS/local-first fallback cannot return in a clean build.
- Preserved the Workspace Project Story link to `/about` during rebuilds and
  excluded generated builder metadata from replayed source records.

### Verified

- 41 Python tests, 47 public Worker tests, typecheck, deterministic import,
  artifact policy and explicit-assets dry-run passed before deployment.
- Homepage, founder, Workspace and the four public JSONL files retain their
  production bytes. Public D1 remains at 2,175 documents, 1,574 videos, 50
  projections, 83 cards and zero full transcripts; no database rows changed.
- No private Worker, DNS, external post or indexing submission changed.
- Exact deployment and live checks:
  [`technical release receipt`](docs/project-memory/BASE2026_TECHNICAL_RELEASE_2026_08_30.md).

## 2026-08-28 — Product positioning, indexation and design authority

### Changed

- Defined Base2026 as an open video research engine and source-first evidence
  library, with explicit honest differentiation and competitor boundaries.
- Synchronized the public roadmap with the live Cloudflare Workers, D1, R2,
  Queues, Workflows, Workers AI, automatic projection and indexation surfaces.
- Connected the release plan to Google Search Console and Bing Webmaster Tools
  monitoring and source-backed topic evidence maps.
- Reconciled the homepage to a dated live D1 snapshot: 2,150 search documents,
  1,563 distinct videos and 39 applied automatic projections.
- Established `b26-independent-v1` as the only production visual authority and
  documented legacy Alex V4/WordPress/Stitch assets as quarantined history.
- Normalized dynamic projected-source pages to the current cool-blue Base2026
  core stylesheet and added a fail-closed design-authority check.

### Research and verification

- Ran a cost-controlled US/en DataForSEO positioning packet for $0.077 and
  rejected downloader, troubleshooting and surveillance-oriented intent.
- Preserved creator attribution, correction/removal and public/private data
  boundaries while updating product language.

## 2026-08-23 — Canonical Cloudflare pipeline operating manual

### Changed

- Added one authoritative manual for the cloud-only TikTok discovery,
  acquisition, Workers AI, private import, automatic excerpt-card projection,
  public D1 FTS5, monitoring, and rollback path.
- Added mandatory manual links to the agent contract and public README.
- Documented the source-synchronization boundary between the public repository
  and the protected production control-plane checkout.
- Strengthened Git/publication rules so architecture can be documented without
  admitting private Worker source, artifacts, endpoints, identifiers, or logs.

### Verified

- Live health and read-only D1 checks confirmed 2,136 public documents, 1,557
  distinct videos, 33 applied projections, 44 projected cards, and zero public
  full transcripts at the dated snapshot.
- Private migrations were current and the automatic-publication policy had no
  hard hold.

## 2026-06-19 — Source Intelligence contract release

Live release: `base2026-source-intelligence-contract-ay54-20260619`

### Changed

- Fixed the source-detail contract so "Questions this source answers" is rendered only from reviewed Source Intelligence cards, not copied from raw source text fallbacks.
- Added reviewed Source Intelligence for the newest public source that exposed the bug.
- Kept the public source-reading surface focused on reviewed public source text, summaries, topics, and insight cards.
- Reindexed the public Meilisearch index with 2,016 public passages.

### Verified

- Current live export: 1,476 source records, 2,016 passages, 1,631 insight cards, 1,060 public insight cards, 1,522 topics, 1,008 public topics, and 10 creators.
- Public export policy passed with `include_full_transcripts=false`.
- Newest-source readiness passed with `--latest 3`.
- Publication boundary audit passed with no forbidden or secret findings.
- Live SEO crawl gate passed 500 crawled pages with 0 P0 bad links and 0 crawled error pages.
- Full mobile visual QA passed 78 checks with 0 failures.

## 2026-06-18 — Social metadata and H1 hardening

Live release: `base2026-social-metadata-h1-ay39-20260618`

### Changed

- Added shared Open Graph and X/Twitter metadata across generated source, topic, compare, creator, index, and info pages.
- Fixed the runtime source-detail mobile H1 contract so hydrated source-detail pages expose exactly one visible H1.
- Kept source pages honest when no reviewed Source Intelligence exists.

### Verified

- Static SEO/social metadata audit passed for indexable generated and info pages.
- GitHub metadata validation passed.

## 2026-06-17 — Ahrefs P0 link-contract baseline

Live release: `base2026-ahrefs-p0-link-contracts-ay37-20260617`

### Changed

- Fixed P0 link-contract defects found during launch monitoring.
- Made `/knowledge/analytics.html` source and creator links resolve to generated static Base2026 pages.
- Pointed Base2026 footer/contact links to the main AI visibility audit funnel.
- Redirected WordPress `/author/` to `/about/` and filtered author links to `/about/`.

### Verified

- Live link and crawl checks passed for the fixed paths.

## 2026-06-15 to 2026-06-16 — Public API and source-page polish

### Changed

- Added the public API/AI access page at `/knowledge/api.html`.
- Added and updated `llms.txt`, `api-index.json`, and `data-dictionary.json`.
- Improved source pages and runtime source detail so public source text and Source Intelligence are readable without duplicate evidence blocks.
- Added shared favicon/touch-icon assets.
- Improved footer social icons and API navigation.

### Verified

- Public API files returned 200 on the live site.
- Source pages and runtime source-detail checks passed on desktop and mobile.
- Meilisearch was reindexed where data changed.

## 2026-06-14 — Public source-text contract

### Changed

- Moved the public product toward a source-intelligence database instead of a transcript-dump interface.
- Added reviewed `public_source_text`, `source_summary_short`, and `source_summary_long` fields to public source records where policy allows.
- Kept legacy raw transcript fields empty in public exports.
- Added public source-reading pages and runtime detail states that explain attribution, policy, and correction/removal paths.

### Verified

- Public export remained excerpt/review gated.
- Live desktop and mobile QA passed without horizontal overflow.

## 2026-06-10 — Public repository launch foundation

### Changed

- Created the public GitHub repository as `offflinerpsy/base2026`.
- Added Apache-2.0 license, README, contribution docs, security policy, issue templates, and public/private boundary documentation.
- Published the first public-safe source tree.
- Added validation scripts for publication boundary and GitHub metadata.

### Verified

- Publication staging dry-run reported no forbidden files or secret findings.
- GitHub repository metadata was set with the public demo homepage and relevant topics.
- Public site and sitemap were live under `https://aggressorbulkit.online/knowledge/`.

## Older work

Before the public launch foundation, Base2026 was developed as a local research and source-intelligence prototype. Older private research artifacts, raw captions, raw ASR, local databases, media files, and generated release archives are intentionally excluded from the public changelog and repository.
