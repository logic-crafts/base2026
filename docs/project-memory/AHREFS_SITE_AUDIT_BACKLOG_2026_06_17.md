# Ahrefs Site Audit Backlog - 2026-06-17

## Scope

Ahrefs project: `9961307`

Audited property: `https://aggressorbulkit.online/`

Crawl date shown by Ahrefs export: 2026-06-14

Export pulled locally on: 2026-06-17

Raw export location, not for Git: `output/ahrefs/site-audit-9961307-20260617/raw/`

Parsed analysis location, not for Git: `output/ahrefs/site-audit-9961307-20260617/analysis/`

Tracked task CSV: `docs/project-memory/AHREFS_SITE_AUDIT_TASKS_2026_06_17.csv`

The Ahrefs bulk ZIP button was unavailable, so the enabled CSV exports were downloaded one by one from the Bulk Export screen. The crawl also showed that monthly crawl credits were exhausted during the crawl, so some lower-priority crawl-budget findings should be rechecked after the structural fixes below.

## Export Inventory

19 CSV exports were captured, totaling about 206 MB:

- `alt-texts`: 1,232 rows
- `anchor-texts`: 132,938 rows
- `crawled-links`: 156,296 rows
- `duplicate-content`: 2,677 rows
- `external-links`: 14,998 rows
- `image-references`: 1,232 rows
- `internal-html-200`: 5,778 rows
- `internal-urls`: 5,856 rows
- `links-canonical`: 5,777 rows
- `links-follow`: 132,938 rows
- `links-target-2xx`: 156,254 rows
- `links-target-4xx`: 42 rows
- `links-target-inde`: 151,822 rows
- `links-target-noin`: 4,474 rows
- `links-target-redi`: 5,766 rows
- `links`: 172,468 rows
- `orphan-pages`: 533 rows
- `redirect-chains`: 1 row
- `uncrawled-links`: 16,172 rows

## Ahrefs Issue Snapshot

The Issues screen showed 31 actual issue groups:

- Internal pages: 39 `404 page`, 39 `4XX page`
- Indexability: 1,789 `Noindex page`, 1,789 `Noindex follow page`
- Links, indexable: 532 orphan pages, 5 pages linking to broken pages, 1,304 pages linking to redirects, 52 pages with only one dofollow internal incoming link
- Links, not indexable: 1 orphan page, 4,461 pages linking to redirects, 3,572 pages with only one dofollow internal incoming link
- Redirects: 4 3XX redirects, 2 HTTP to HTTPS redirects, 1 redirect chain
- Content, indexable: 138 long meta descriptions, 38 short meta descriptions, 7 long titles, 1 missing or empty H1, 1 missing meta description, 1 short title
- Content, not indexable: 739 short meta descriptions, 303 long titles
- Social tags: 1,304 incomplete Open Graph pages, 1,314 missing X/Twitter cards, 10 missing Open Graph pages
- Performance/images/CSS: 1 slow page, 1 oversized image, 4 oversized CSS files
- Sitemaps/other: 1 non-canonical sitemap URL, 1,314 IndexNow candidates, 1,219 structured-data rich result validation errors

## Root-Cause Clusters

### P0: Broken URLs and redirect noise

The real launch blockers are not random. They come from repeatable templates:

- `/knowledge/analytics.html` links to Base2026 assets as if it lived at the root, for example `/topics/...` and `/index.html?source=...`, producing real 404 targets.
- WordPress pages still expose `/author/`, which currently returns 404.
- Public Base2026 pages link to `/contact/` 5,765 times even though the active contact surface is on the About/contact flow. This is a crawl-wide redirect generator.

### P1: Crawlable architecture gaps

Ahrefs sees 533 orphan pages, including 530 source pages. That means source pages exist and may be indexable, but crawlers do not reliably discover them through a clean crawlable archive or pagination path.

The duplicate-content export also shows large duplication around `/knowledge/` query-state URLs. Runtime query URLs are useful for the app, but search engines should not treat every query state as another indexable content page when a static source/topic/creator page exists.

### P1: Rich-result and sharing metadata gaps

The high counts for Open Graph, X/Twitter cards, and structured data validation errors mean generated Base2026 pages need one shared metadata contract, not page-by-page patches.

### P2: Content metadata tuning

Title/meta length warnings are real but secondary. They should be fixed through templates after URL architecture and metadata contracts are stable.

### P2: Assets and crawl budget

One large image and four CSS warnings should be optimized, but these are not more important than broken URLs, redirects, orphan pages, and schema/social metadata.

## Work Queue

| ID | Priority | Area | Problem | Evidence | Task | Done When |
| --- | --- | --- | --- | --- | --- | --- |
| AHREFS-P0-01 | P0 | Base2026 analytics links | `/knowledge/analytics.html` emits root-relative Base2026 links that 404. | 42 links to 39 unique 4xx targets; most non-author samples come from `/knowledge/analytics.html`. | Fix analytics link generation to use `/knowledge/topics/...`, `/knowledge/sources/...`, `/knowledge/creators/...`, or app query URLs under `/knowledge/`. | Ahrefs 4xx samples from analytics are gone; local link checker finds no root `/topics/` or root `/index.html?source=` links. |
| AHREFS-P0-02 | P0 | WordPress author URL | WordPress pages link to `/author/`, which returns 404. | Top 4xx target `/author/` has 4 source pages. | Disable bad author archive links or redirect `/author/` to `/about/`. | `/author/` no longer appears as a 404 in crawl output. |
| AHREFS-P0-03 | P0 | Contact URL contract | Public pages link to `/contact/` but that URL redirects. | 5,765 links to redirect target `/contact/`. | Choose one canonical contact URL, then update WordPress and Base2026 footers/navigation/forms to link directly to it. | Ahrefs links-to-redirect count for `/contact/` is zero or intentionally minimal. |
| AHREFS-P1-04 | P1 | Source-page discoverability | 530 generated source pages are orphaned. | `orphan-pages`: 533 total, 530 `knowledge/sources`. | Add a crawlable paginated source archive and/or creator/topic source lists with static anchors to every public source page. | Every public source page has at least one crawlable internal incoming link. |
| AHREFS-P1-05 | P1 | Query-state duplicates | `/knowledge/` query-state URLs create a huge duplicate cluster. | Largest duplicate content group has 2,664 URLs; indexable duplicate sample includes `/knowledge/`. | Keep interactive query URLs for users, but canonical/noindex or replace crawlable internal links with static source/topic/creator URLs where possible. | Indexable duplicate cluster is eliminated or reduced to intentional canonical pages. |
| AHREFS-P1-06 | P1 | Base2026 social metadata | Generated pages miss or incompletely declare social share tags. | 1,304 incomplete Open Graph pages, 1,314 missing X/Twitter cards, 10 OG missing. | Add one shared OG/Twitter card template for source, topic, creator, compare, API, and info pages. | Indexable pages have complete `og:title`, `og:description`, `og:url`, `og:type`, `og:image`, `twitter:card`, and related fields. |
| AHREFS-P1-07 | P1 | Structured data | Google rich result validation errors are widespread. | 1,219 structured-data validation errors. | Validate and fix generated JSON-LD templates; remove invalid rich-result markup when data is insufficient. | Rich-result validation errors are zero or explicitly documented as non-rich schema. |
| AHREFS-P1-08 | P1 | Sitemap canonical hygiene | One non-canonical page is included in sitemap. | Ahrefs sitemap issue count: 1. | Identify the exact URL and update sitemap generation to include only canonical, indexable URLs. | Sitemap contains only canonical indexable URLs. |
| AHREFS-P2-09 | P2 | Title/meta template tuning | Several indexable pages have title/meta length issues. | 310 titles over 70 chars; 138 long meta descriptions; 38 short meta descriptions; 1 missing meta; 1 missing H1. | Tune generated and WordPress title/meta/H1 templates after URL contracts settle. | Indexable page title/meta warnings are cleared or reduced to justified edge cases. |
| AHREFS-P2-10 | P2 | Links to noindex pages | Crawlers find thousands of links to noindex targets. | 4,474 links to noindex, mostly `knowledge/topics` and `knowledge/compare`. | Decide which topic/compare surfaces should be indexable, canonical, or non-crawlable from public navigation. | No high-value public page is both heavily linked and noindex without a reason. |
| AHREFS-P2-11 | P2 | Crawl budget | 1,174 internal URLs were not crawled because Ahrefs monthly page crawl limit was reached. | `uncrawled-links`: 1,174 internal URLs due monthly page crawl limit. | Reduce duplicate/query crawl paths, then rerun Ahrefs with enough crawl credits. | A follow-up crawl completes without internal limit exhaustion. |
| AHREFS-P2-12 | P2 | Image performance | One image is too large. | `alex-yarosh-cutout-v115.png` is about 1.8 MB. | Generate responsive WebP/AVIF or compressed PNG variants and update theme references. | Ahrefs image-size warning clears; visual QA still passes. |
| AHREFS-P2-13 | P2 | CSS size | Four CSS files are flagged as too large. | Ahrefs CSS file size warnings: 4. | Audit loaded CSS, minify/split where it actually helps, and avoid breaking WordPress/Base2026 shared styles. | CSS warnings are cleared or accepted with compression evidence. |
| AHREFS-P3-14 | P3 | IndexNow/GSC submission | Ahrefs lists 1,314 pages to submit to IndexNow, but submitting before fixes would amplify bad URLs. | Ahrefs `Pages to submit to IndexNow`: 1,314. | Submit only after P0 and core P1 fixes are deployed and live smoke passes. | IndexNow/GSC submission list contains stable canonical URLs only. |

## Recommended Execution Order

1. Fix P0 broken URL and redirect generators.
2. Regenerate/deploy only after local link checks prove no new root-relative Base2026 URL regressions.
3. Fix source archive/discoverability and query-state canonical policy.
4. Add shared metadata and schema contracts.
5. Tune title/meta and asset performance.
6. Run a fresh Ahrefs crawl before requesting large-scale indexing or IndexNow submission.

## 2026-06-17 P0 Deploy Pass

Status: deployed, live smoke passed, pending Ahrefs/GSC recrawl.

- `AHREFS-P0-01`: `/knowledge/analytics.html` no longer emits root-level `/topics/...` or `/index.html?source=...` links. Analytics source links now point to generated static source pages, and creator links point to generated creator profile pages.
- `AHREFS-P0-02`: WordPress author archive traffic is forced to `/about/` with a 301 redirect, and generated WordPress author links are filtered to `/about/`.
- `AHREFS-P0-03`: generated Base2026 and static entrypoint footers no longer link to redirecting `/contact/`; they link directly to `/ai-visibility-audit/`.

Verification:

- `python3 -m py_compile scripts/generate-public-pages.py scripts/generate-info-pages.py`
- `python3 scripts/generate-info-pages.py --source docs/public-pages --out web/static`
- `python3 scripts/generate-public-pages.py --data public-data/tiktok --out web/static`
- `rg` checks found no root-level analytics source/topic query links and no Base2026 `/contact/` footer links.
- public release contract, public export policy, publication-boundary audit, and `git diff --check`.
- deployed Base2026 as `base2026-ahrefs-p0-link-contracts-ay37-20260617` with `scripts/deploy-public-vps.ps1 -SkipPackage -SkipReindex`.
- deployed the WordPress author redirect in `functions.php`; server PHP lint passed and backup was saved at `/root/alex-yarosh-file-backups/20260617-ahrefs-p0-author-redirect/`.
- live smoke confirmed 200 responses for the checked root/Base2026 pages, `/author/` 301s to `/about/`, sitemap exposes 1,482 URLs, and checked live pages do not emit the known P0 bad links.

Limitations:

- Ahrefs status must remain `deployed-pending-recrawl` until a fresh crawl confirms the 404/redirect counts are gone.
- Meilisearch reindex was intentionally skipped because public data/index fields did not change.

## 2026-06-17 AHREFS-P1-06 Local Review

Status: local-reviewed, not deployed.

- Added one shared OG/X metadata contract to `scripts/generate-public-pages.py` for generated source, topic, compare, creator, index, and analytics pages.
- Added the same OG/X contract to `scripts/generate-info-pages.py` for methodology, roadmap, story, privacy, source policy, support, site structure, opt-out, and API pages.
- Added complete OG/X metadata to `web/static/index.html` and `web/static/meili.html`.
- Regenerated `web/static` public pages and info pages, then regenerated the Base2026 sitemap.

Verification:

- `python3 -m py_compile scripts/generate-public-pages.py scripts/generate-info-pages.py scripts/generate-base2026-sitemap.py`
- temporary public/info generation passed.
- representative real `web/static` source, topic, compare, creator, analytics, roadmap, API, and search entrypoint checks passed.
- full local HTML scan passed for 1,483 indexable pages with complete `og:title`, `og:description`, `og:url`, `og:type`, `og:image`, `twitter:card`, `twitter:title`, `twitter:description`, and `twitter:image`; 1,929 noindex pages were skipped.
- `python3 scripts/generate-base2026-sitemap.py --web-root web/static --out web/static/sitemap.xml --base-url https://aggressorbulkit.online/knowledge/` produced 1,482 sitemap URLs.
- public export policy, GitHub metadata validation, publication-boundary audit, and targeted `git diff --check` passed.

## Indexing Rule

Do not submit the affected URL set to GSC or IndexNow until P0 and core P1 items are fixed. Submitting pages while the crawl still contains broken internal links, redirect chains, duplicate query URLs, incomplete social metadata, and schema errors would waste crawl budget and make Search Console noise harder to interpret.


## 2026-06-23 Ahrefs/GSC Live Check After ay55

Status: live baseline improved, still needs Ahrefs recrawl / GSC follow-up.

Ahrefs dashboard, project `9961307` / `Aggressorbulkit`:

- Health Score: `Crawl failed` in Ahrefs dashboard; this is an Ahrefs crawl-state issue to rerun/repair, not reproduced by live HTTP checks.
- Domain Rating: `0`.
- Referring domains: `76` with `+41` trend.
- Organic traffic: `0`; organic keywords: `0`.
- Ahrefs dashboard project target: `*.aggressorbulkit.online/*`.

Google Search Console, domain property `aggressorbulkit.online`:

- Performance, last 3 months: `0` clicks, `110` impressions, `0%` CTR, average position `27.8`; last update shown as `12.5 hours ago`.
- Page indexing overview: `29` indexed pages, `814` not indexed pages, `6` reasons; last update shown as `2026-06-11`.

Live technical smoke from terminal/browser:

- `robots.txt` is 200 and lists both WordPress sitemap and `/knowledge/sitemap.xml`.
- `/knowledge/sitemap.xml` is 200 and exposes 4 sitemap files, `1,577` URLs.
- No `index.html?` query URLs were found in the live Base2026 sitemap.
- 70 sampled sitemap URLs returned 200 with no canonical mismatches and no `noindex` findings.
- Representative live pages (`/knowledge/`, `/knowledge/roadmap.html`, `/knowledge/support.html`, one source page) return 200, self-canonical, `index,follow`, and expected H1/title.
- Live OG/X metadata spot-check passed for `/knowledge/`, `/knowledge/roadmap.html`, and a source page.
- `AhrefsBot/7.0` and `Googlebot/2.1` user-agent requests to `/knowledge/` return 200; HTTP to HTTPS redirect for `/knowledge/` returns 301 then 200.

Current interpretation:

- P0 broken URL/redirect work remains deployed-pending-recrawl in Ahrefs; live smoke does not reproduce the old P0 blockers.
- P1 social metadata appears live on representative pages, but should remain pending a full recrawl/export check before closing.
- Sitemap canonical hygiene appears clean in live sample; keep `AHREFS-P1-08` pending recrawl unless the exact old non-canonical sitemap URL is identified.
- Main next action is to restart/fix Ahrefs Site Audit crawl for project `9961307` and export fresh issue CSVs; GSC indexation has only 29 indexed pages vs 1,577 sitemap URLs, so source/archive discoverability and crawl-budget/query-duplicate cleanup remain the highest-impact SEO tasks.
