# Phases

## Phase 18 — Engineering journal and free editorial distribution

Purpose: explain the Cloudflare evidence architecture in one canonical public
article and measure useful discovery rather than buying ranking links. Status:
live/measurement active. The Base2026 article, one canonical Medium adaptation,
and adapted X/LinkedIn announcements are already live. Current action: measure
referrals and search discovery; do not create another copy in the current
non-publication closeout.

## Phase 17 — Public dataset and contextual discovery

Purpose: expose a reviewed, machine-readable public dataset surface with a
landing page, catalog, quickstart and reproducible query example. Status:
live/distribution active. Enigmavista, Dreamwood and Aster contextual reference
pages are live; Golem remains code-only without a production receipt. Hugging
Face and Zenodo are held until a dataset-specific rights/license model,
per-record provenance and takedown/version policy exist.

## Phase 16 — Production source synchronization and live statistics

Purpose: align current public Worker source, founder/product surfaces and
read-only D1 totals with the canonical public repository. Status: live. Current
public Worker is `3e06c10b-9fa4-40aa-ad14-913a11b85f30`; public D1 reports
2,175 documents, 1,574 videos, 50 projections, 83 cards and zero public full
transcripts.

## Phase 15 — Evidence Brief V2 and homepage product polish

Purpose: make the product immediately understandable and useful from the home
page without changing the public/private data boundary. Status: historical
release receipt, verified on 2026-08-28 and superseded by Phase 16/current
status. Public Worker at that checkpoint
`35a2ee9e-1d95-45c4-b971-26f19183d732` rolls back to
`dcbeb2e9-27af-4d45-b510-fdaaea055f4a`. Evidence Brief V2, V1 compatibility,
desktop/mobile layout, keyboard, reduced-motion and no-JS gates passed. Retain
this entry as release history; use `CURRENT_STATUS.md` for live identifiers.

## Phase 14 — SEO/GEO positioning and search measurement

Purpose: make the public evidence graph technically crawlable, connect Google
and Bing, and measure real query/page evidence. Status: live/measurement active.
GSC currently reports 22 impressions, zero clicks and average position 55.4;
Bing performance is still preparing. Sixty source-backed enrichment entries are
configured; public route and indexation state vary and are audited individually.

## Phase 13 — Capture fairness and transport resilience

Purpose: keep fresh sources ahead of bounded retries and preserve source-level
holds without stalling the cloud pipeline. Status: live observation. Private
Worker `14adacb6-7f0f-4aa7-9131-fc41469eec15` has no stale/dead jobs and the
automatic lane has zero eligible backlog. Container app v8 is active/running
without errors while its detail counter remains `healthy=0`; do not restart for
telemetry alone.

## Phase 12 — Automatic Cloudflare-only publication

Purpose: discover and acquire new TikTok sources in Cloudflare, keep raw
material private, and automatically project only policy-eligible excerpt cards
through an exact private-to-public RPC contract. Status: live and verified on
2026-08-23. Broad release, local adapter, automated ChatGPT Web, AI Gateway, and
paid fallback remain off. Canonical reference:
`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`.

## Phase 9 — Independent domain and Cloudflare hosting

Purpose: serve Base2026 independently at `base2026.dev` through Workers Static
Assets and public D1 FTS5, with `www` redirected to the apex and legacy
VPS/Meilisearch retained only as rollback infrastructure. Status: live.

## Phase 0 — Repo hygiene and publication boundary

Purpose: make the repo safe to inspect and commit. Allowed: `.gitignore`, audits, memory docs. Forbidden: pushing, publishing private folders. Done: public/private boundary is explicit and verified.

## Phase 1 — Public TikTok dataset model

Purpose: define the public export shape. Allowed: reviewed metadata, public URLs, public-safe transcript payloads. Forbidden: committing raw dumps, logs, credentials, unreviewed private sources. Done: export is reproducible and documented.

## Phase 2 — Transcript polish pipeline

Purpose: convert raw captions into faithful English transcript text. Allowed: cleanup punctuation, paragraphs, speaker-faithful formatting. Forbidden: inventing claims, translating to Russian, adding meaning not present in source. Done: pipeline has QA rules and rerun instructions.

## Phase 3 — Meilisearch index and search API

Purpose: provide fast search/facets over public data. Allowed: public index updates, search-only key usage. Forbidden: exposing master key or private indexes. Done: search works locally and on VPS.

## Phase 4 — Public web UI

Purpose: make the database usable by humans. Allowed: search, filters, transcripts, source links, responsive UI. Forbidden: UI changes without desktop/mobile QA. Done: user can find, filter, read, and open source posts.

## Phase 5 — Deploy and VPS runbook

Purpose: make deploy repeatable and reversible. Allowed: package release, upload, symlink switch, nginx reload. Forbidden: overwriting WordPress root or leaking keys. Done: deploy and rollback commands are documented.

## Phase 6 — Hermes automation

Purpose: refresh creators and ingest new videos. Allowed: dry-run checks, dedupe, local update, reviewed deploy. Forbidden: uncontrolled always-on scraping or silent public publishing. Done: scheduled refresh has logs, stop command, and QA gate.

## Phase 7 — Open-source packaging

Purpose: prepare GitHub publication. Allowed: license, contributing docs, sample data, public scripts. Forbidden: committing private data or generated local artifacts. Done: first public-safe commit and repository metadata are ready.

## Phase 8 — Security and compliance audit

Purpose: catch leaks and operational risks before public push. Allowed: staged diff review, secret scan, docs review. Forbidden: pushing before audit. Done: reviewer signs off with no private data in staged files.
