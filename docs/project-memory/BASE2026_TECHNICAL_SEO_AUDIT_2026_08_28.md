# Base2026 Technical SEO/GEO Audit — 2026-08-28

## Executive result

The canonical HTTPS apex is live and crawlable, and the public evidence corpus
is indexable. A fresh robots-aware crawl found no P0 outage, 5xx response, or
public full-transcript exposure in the audited sample. The release is not
SEO-clean: the sitemap and nearly every sampled URL use redirecting `.html`
URLs, the apex HTTP URL serves a 200 instead of redirecting to HTTPS, and every
sampled HTML page lacks both `og:image` and `twitter:image` even though the
public preview asset exists. The live public roadmap also describes the old VPS
phase/status sequence while the checked-in roadmap describes the Cloudflare
pipeline and current indexability work.

Scores are heuristic (10 = healthy; not a ranking forecast):

| Area | Score | Evidence |
| --- | ---: | --- |
| Crawlability/indexation | 7/10 | `robots.txt`, sitemap index, and 500/500 sampled HTML responses were healthy; HTTP apex does not redirect to HTTPS. |
| Canonical/redirect hygiene | 3/10 | 494/500 sampled pages were requested from sitemap URLs that 307-redirect to extensionless URLs while retaining `.html` canonicals. |
| On-page HTML | 9/10 | 500/500 had a title, description, exactly one H1, `index,follow`, and `lang=en`. |
| Structured data | 9/10 | 500/500 had parseable JSON-LD; zero parser errors. |
| Social/entity metadata | 4/10 | 500/500 were missing `og:image` and `twitter:image`; the 200 PNG asset is unused by these heads. |
| GEO/agent access | 7/10 | `llms.txt`, JSONL exports, API index, and a read-only D1 search API work; API metadata and route naming drift. |
| Public-data boundary | 9/10 | Manifest is excerpt-only; sampled API results expose `full_transcript_public:false`; no public private-pipeline material was observed. |

## Scope and method

- Audit window: 2026-08-28 09:15–09:36 UTC; primary crawl snapshot
  `2026-08-28T09:15:34.120Z`.
- Fetched `https://base2026.dev/robots.txt`, honored its `Allow: /`, followed
  its declared `https://base2026.dev/sitemap.xml`, fetched all five child
  sitemaps, and found 1,617 unique declared URLs with no duplicate sitemap
  entries.
- Fresh crawler limit: 500 HTML pages, 10 concurrent requests, 40 ms request
  spacing, 15 s per-request timeout. It made GET requests only and did not
  write to production, GSC, Bing, Cloudflare, or git.
- The existing `scripts/live-seo-crawl-gate.mjs` was also run to `/tmp` only as
  a cross-check. Its hard-coded `/knowledge/sitemap.xml`, `/knowledge/` seed,
  and pre-migration link contract generated false positives on this
  root-mounted release; its `6548` bad-link count and seven errors are not used
  below as live defects. The fresh crawl is the source of audit counts.

## P0 findings

None in this read-only sample. The live robots endpoint and sitemap index
returned 200; the fresh sample returned 500/500 HTML 200 responses, zero 5xx,
zero fetch errors, zero `noindex`, and zero missing title/description/H1 or
schema parse errors. This is not a guarantee for URLs outside the 500-page
limit.

## P1 findings

### P1-1 — Canonicals and sitemap URLs point at redirecting `.html` routes

Evidence:

- The live sitemap declares 1,617 unique URLs. In the 500-page sample, 494
  sitemap URLs returned `307` to an extensionless URL and then `200`.
- Those 494 pages retained a `.html` canonical, so `canonical_not_self=494`.
  Example: `https://base2026.dev/sources/tiktok-video-7388244947352210734.html`
  returns `307 Location: /sources/tiktok-video-7388244947352210734`; the final
  page canonical is still
  `https://base2026.dev/sources/tiktok-video-7388244947352210734.html`.
- The same contract exists on public info pages:
  `https://base2026.dev/roadmap.html` → `307 /roadmap`, and the final page
  still declares the `.html` canonical.
- The Worker source's dynamic source renderer already builds extensionless
  canonicals (`cloudflare/base2026-worker/src/index.ts:867`), while
  `scripts/generate-base2026-sitemap.py:17-81` derives URLs from filenames and
  filters against canonicals. This is a release-builder/generator contract
  mismatch, not a page-content issue.

Suggested source ownership: choose one public URL form, then align
`scripts/generate-base2026-sitemap.py`,
`scripts/build-base2026-cloudflare-release.py`, generated page templates, the
Worker dynamic renderer, and internal links. Regenerate the sitemap only after
the canonical/redirect decision is made.

### P1-2 — HTTP apex is indexable 200 instead of redirecting to HTTPS

Evidence:

- `http://base2026.dev/` returned `200 OK` with the public homepage.
- `https://base2026.dev/` returned `200 OK`.
- `http://www.base2026.dev/` and `https://www.base2026.dev/` returned `301`
  to `https://base2026.dev/`.

The protocol policy is therefore inconsistent: the apex has an HTTP duplicate
while `www` is normalized. Suggested ownership: Cloudflare custom-domain /
edge redirect policy owner; verify with a fresh `curl -I` after any change.

### P1-3 — OG/Twitter image metadata is absent across the audited HTML sample

Evidence:

- `og_incomplete=500/500` and `twitter_incomplete=500/500`; the missing field in
  both sets is the image URL. Titles, descriptions, URL, `og:site_name`, and
  `twitter:card` are present on the sampled pages.
- Exact live examples: `/`, `/workspace/`,
  `/sources/tiktok-video-7388244947352210734`, and `/roadmap` all lack
  `og:image` and `twitter:image`.
- `https://base2026.dev/static/assets/base2026-ai-visibility-card.png` is live
  (`200 image/png`, 88,586 bytes), but no sampled page head references it.
- `templates/base2026-startup-homepage.html:8-21` contains the startup head and
  omits both image tags. The checked-in release/generator stack has image-tag
  logic for other generated pages, so the standalone startup/dynamic source
  surfaces need one shared social metadata contract.
- This contradicts the older completion claims in
  `docs/project-memory/PROJECT_STATE.md:141` and
  `docs/project-memory/CURRENT_HANDOFF.md:444`, which mention complete OG/X
  metadata and a 1200×630 card.

Suggested source ownership: shared head/template authority, especially
`templates/base2026-startup-homepage.html`, generated info/source page
templates, and `scripts/build-base2026-cloudflare-release.py`. Use the live
asset only after confirming its intended public brand/attribution use.

### P1-4 — Live sitemap coverage does not match the public route/API contract

Evidence:

- The five live child sitemaps contain only: `/source-policy.html`, `/sources/`
  plus 1,525 source records, `/story.html`, `/support.html`, and `/topics/`
  plus 87 topic pages (1,617 URLs total).
- These live 200 public entry points are absent from the sitemap inventory:
  `/creators/`, `/compare/`, `/analytics`, `/methodology`, `/roadmap`, `/api`,
  `/about`, `/privacy`, `/partner`, and `/apply-research`.
- `https://base2026.dev/api-index.json` says its sitemap covers “generated
  source, topic, comparison, creator, and info pages,” which is not what the
  live sitemap declares.

Suggested source ownership: sitemap generation/release packaging
(`scripts/generate-base2026-sitemap.py` and
`scripts/build-base2026-cloudflare-release.py`) plus the API-index metadata.
Either intentionally scope the sitemap to source/topic discovery and update
the contract, or include the canonical public hubs and info pages.

### P1-5 — Declared dynamic sitemap route is absent from production

Evidence:

- `cloudflare/base2026-worker/src/index.ts:1510-1514` handles
  `/sitemap-dynamic.xml`; `cloudflare/base2026-worker/wrangler.jsonc:16-19`
  lists it under `run_worker_first`.
- `scripts/build-base2026-cloudflare-release.py:734-739` emits a robots
  payload declaring both the static and dynamic sitemap URLs.
- Live `https://base2026.dev/sitemap-dynamic.xml` returned `404`.
- The static `/sitemap.xml` works, so this is a release/runtime contract gap,
  not a total sitemap outage. If dynamic discovery is intentionally retired,
  remove or revise the stale declaration in the owning source; if intended,
  deploy and re-test the route.

Suggested source ownership: `cloudflare/base2026-worker/src/index.ts`,
`cloudflare/base2026-worker/wrangler.jsonc`, and the release/deployment owner.
No deployment was attempted in this audit.

## P2 findings and watch items

- Sitemap child `<lastmod>` values are `2026-07-29`, while the audit was
  2026-08-28. The manifest has the same `created_at` date. Refresh timestamps
  as part of a deliberate release; do not fabricate dates.
- `/static/documents.jsonl`, `/static/passages.jsonl`,
  `/static/insight_cards.jsonl`, and `/static/topic_signal_briefs.jsonl` return
  200 but omit a `Content-Type` in the observed response headers; they also
  receive `Cache-Control: no-cache, no-cache`. This is workable for browser
  fetches but weakens machine-client/content-negotiation and cache behavior.
  Ownership: release headers/static asset packaging.
- `api-index.json` is versioned `2026-06-18`; its `human_search_workspace`
  entry points to `/` even though the dedicated search workspace is
  `/workspace/`, and its `.html` route templates redirect. `llms.txt` correctly
  points to `/workspace/`; align machine-readable documentation.
- `root-llms.txt` is live 200, while the alternate-looking
  `/llms-root.txt` is 404. Keep one documented name or add an intentional
  redirect/alias. `llms.txt` itself is live 200 and useful.
- `/workspace/` includes `<base href="/">` and several `./*.html` links. With
  that base tag, browser resolution reaches the root routes (which return 200
  or their documented 307), but the literal `/workspace/*.html` forms return
  404. Prefer explicit root-relative links to make non-browser crawlers and
  future refactors less base-tag dependent. This is not counted as a broken
  rendered link.
- `/knowledge/` is 404 on the new canonical host. The old repo
  `ROADMAP.md:5` still calls `https://aggressorbulkit.online/knowledge/` the live
  demo, while the current public product is at `base2026.dev`; treat old
  documents as migration history or update their ownership deliberately.

## Live route/API and data checks

| Check | Result |
| --- | --- |
| `GET /robots.txt` | 200; `User-agent: *`, `Allow: /`, static sitemap declared; no disallow rules. |
| `GET /sitemap.xml` + five children | 200; 1,617 unique URLs, no duplicate entries. |
| `GET /llms.txt`, `/root-llms.txt` | 200; public entry points and boundary text present. |
| `GET /api/health` | 200 JSON: `ok=true`, `search=d1-fts5`, index `base2026_public_tiktok`. |
| Read-only `POST /api/search/multi-search` | 200; query `schema` returned one hit and `estimatedTotalHits=40`; hit carried `full_transcript_public=false`. |
| Read-only `POST /knowledge-search/multi-search` | 200; same legacy alias behavior. |
| `GET /sitemap-dynamic.xml` | 404; see P1-5. |
| Source/detail/index routes | Root, workspace, topics, creators, sources, compare, roadmap, methodology, API, analytics, about, privacy, support, partner, apply-research, opt-out, story, and solutions routes returned 200 at their extensionless form. |
| Search aliases | `/search`, `/search/`, `/search.html`, and `/meili.html` return 301 to `/workspace/`. |
| Schema | Sampled pages contained `WebPage`; source details also contained `CreativeWork` and `VideoObject`; no JSON-LD parser errors. |
| Internal links | 20,787 anchors seen, 1,432 unique internal targets in the 500-page sample, zero legacy `aggressorbulkit.online` links. Workspace base-tag links were normalized before judging brokenness. |

## Public data sanity check

The live manifest (`2026-07-29`) reports 1,525 documents, 2,319 passages,
2,463 insight cards (1,939 public), 1,724 source records, 18 creators, and
1,670 topics. These counts match the visible homepage counters and the
machine-readable release shape. The manifest states `excerpt_only` and
`include_full_transcripts=false`; the read-only API sample also returned
`full_transcript_public=false`. One private, `needs_review` insight row with an
empty evidence excerpt exists in the non-public card set; it was not observed
in the public API hit or public page sample and is a data-quality hold, not a
confirmed public leak.

## Roadmap reconciliation

Live `https://base2026.dev/roadmap` is 200; `.html` is a 307 alias. The live
rendered/fallback roadmap says “Public VPS deployment” and marks Phase 1, Phase
3, and Phase 5 `Live`, Phase 2 and Phase 4 `In progress`, and Phase 6 `Research`.
Its Now/Next/Later sequence places Content Ingestion next and API/MCP later.

The checked-in public roadmap at `docs/public-pages/01_ROADMAP.md` instead says
the product runs on Cloudflare, Phase 2 is “Live, monitored,” Phase 3 is
“In progress,” Phase 5 is “In progress,” and Now is canonical/sitemap/indexable
alignment. This is a public truth mismatch, not merely a title difference. The
live page is generated from the older `web/static/roadmap.html` / `roadmap.js`
surface; suggested ownership is the roadmap source plus
`scripts/generate-info-pages.py` and the Cloudflare release builder. Do not
claim the roadmap is reconciled until the live body and checked-in source agree.

## Prioritized next action (no fixes performed)

1. Owner decision: extensionless versus `.html` canonical URL contract; then
   update generator, release, Worker dynamic renderer, internal links, and
   sitemap together.
2. Normalize apex HTTP to HTTPS and verify both protocol/host variants.
3. Add one approved social-image contract to all public HTML heads and verify
   the live PNG, OG, and Twitter tags.
4. Resolve static versus dynamic sitemap ownership and make sitemap coverage
   match the documented public route contract.
5. Reconcile live Roadmap copy/status with `docs/public-pages/01_ROADMAP.md`,
   then repeat a 500-page crawl using a base-aware link resolver.

No production, account, git, or implementation changes were made by this
audit; only this report was written.
