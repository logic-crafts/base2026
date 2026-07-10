# SEO Structure Audit — Alex Yarosh WordPress + Base2026

Date: 2026-06-23
Scope: live `https://aggressorbulkit.online/` WordPress pages + Base2026 public knowledge library under `/knowledge/`.

## Source basis

- Google Search Central SEO Starter Guide:
  - organize sites logically so users and search engines understand page relationships;
  - use descriptive URLs and group related pages in directories;
  - reduce duplicate content and link internally to canonical URLs;
  - headings help users navigate; Google does not require a magic heading count, but clean organization helps readability/accessibility.
- Google canonical guidance:
  - redirects, `rel=canonical`, and sitemap inclusion stack as canonical signals;
  - internal links should point to canonical URLs, not duplicate variants;
  - sitemaps should list preferred canonical URLs only.
- Google sitemap guidance:
  - sitemaps matter most for larger/complex sites and should contain URLs that the site considers important.
- SEO community sanity check from Reddit/r/SEO snippets:
  - use headings as nested structure, not styling;
  - one clear H1 per page is still the practical convention;
  - H2 sections can directly follow H1; H3s should expand an H2 section.
- Base2026 positioning:
  - source library should remain crawlable as a clean evidence architecture, not a crawl-trap of workspace/query variants.

## Live crawl findings

### WordPress main pages

Sampled:

- `/`
- `/services/`
- `/pricing/`
- `/about/`
- `/ai-visibility-audit/`
- `/category/uncategorized/`

Findings:

- Main commercial pages return `200`.
- Canonicals are present on the important commercial pages:
  - `/` canonical `/`
  - `/services/` canonical `/services/`
  - `/pricing/` canonical `/pricing/`
  - `/about/` canonical `/about/`
  - `/ai-visibility-audit/` canonical `/ai-visibility-audit/`
- Each important commercial page has exactly one main-content H1.
- No main-content heading-level skips were detected on sampled commercial pages.
- Category archive is still live on production as of this crawl:
  - `/category/uncategorized/` returns `200`
  - robots meta currently: `max-image-preview:large`
  - no canonical detected
  - H1 count: `0`
  - this should be fixed by deploying the already-prepared WordPress theme patch that emits `noindex,follow` and removes category/tag taxonomies from WP sitemap.
- Footer/cookie/accessibility headings appear in the full document as H2s. This is not a primary SEO blocker because they are outside the main content, but they inflate heading counts in simple crawlers. Optional cleanup: demote repeated footer/cookie headings visually/semantically if we want cleaner crawler output.
- Header/footer/nav links repeat across desktop/mobile/footer, so simple crawlers report many duplicate nav links. This is normal, but duplicated Base2026 `index.html` links should be avoided after deploy.

### WordPress sitemap/robots

Live `robots.txt` currently includes:

- `Sitemap: https://aggressorbulkit.online/wp-sitemap.xml`
- `Sitemap: https://aggressorbulkit.online/knowledge/sitemap.xml`

Live `wp-sitemap.xml` currently still references:

- `wp-sitemap-taxonomies-category-1.xml`

That confirms the WordPress noindex/sitemap patch is not deployed yet, even though the code change exists locally.

## Base2026 live findings

Sampled:

- `/knowledge/`
- `/knowledge/analytics.html`
- `/knowledge/topics/`
- `/knowledge/creators/`
- `/knowledge/sources/tiktok-video-7652384458804432136.html`

Findings:

- Sampled Base2026 pages return `200`.
- Canonicals are present and absolute.
- Robots meta is `index,follow` on sampled public knowledge pages.
- Each sampled page has one H1.
- `/knowledge/topics/` and `/knowledge/creators/` live currently have an H1 followed directly by H3 card headings. This is not fatal for Google, but it is weaker for accessibility/content outline and contradicts the clean nested structure we want.
- Live Base2026 nav still contains links to `/knowledge/index.html` from generated pages. Previous local patch has already removed query variants and local generated output now avoids plain `index.html` hrefs too; this needs deploy.
- `/knowledge/sitemap.xml` does not contain `index.html?` query URLs in sampled sitemap index output.

## Fixes already prepared locally in code

### WordPress repo

Path: `/Users/alexyarosh/Projects/base2026-migration/geo/wp-theme/alex-yarosh/functions.php`

Prepared:

- remove `category` and `post_tag` from WP sitemap taxonomies;
- add `noindex,follow` for category/tag/date archives.

Needs deploy to affect production.

### Base2026 repo

Path: `/Users/alexyarosh/Projects/base2026-migration/DW/base2026/scripts/generate-public-pages.py`

Prepared before this audit:

- search/workspace links no longer emit `index.html?...` query URLs;
- generated nav now points to canonical directory root where applicable;
- sitemap generation emits canonical URLs only.

Prepared during this audit:

- index pages now insert a real H2 section heading before H3 card grids:
  - `Topic Evidence Pages` → `Available topic evidence pages` → H3 topic cards;
  - `Creator Source Profiles` → `Available creator source profiles` → H3 creator cards;
  - `Source Records` → `Available source records` → H3 source cards.
- Base2026 footer CSS now keeps CTA buttons on one row at mobile widths instead of stacking into separate rows, matching the WordPress footer fix.

Verification output:

- generated `/tmp/base2026-structure-check` with:
  - `sources: 1476`
  - `topics: 1008`
  - `creators: 10`
  - `compare_pages: 1008`
  - `indexable_topics: 38`
- local heading audit on generated pages showed:
  - `topics/index.html`: one H1, no heading skips, no `index.html?`, no plain `../index.html` hrefs;
  - `creators/index.html`: one H1, no heading skips, no `index.html?`, no plain `../index.html` hrefs;
  - `sources/index.html`: one H1, no heading skips, no `index.html?`, no plain `../index.html` hrefs;
  - sampled topic/source detail pages: one H1, no heading skips.
- `python3 -m py_compile scripts/generate-public-pages.py` passed.
- `git diff --check -- scripts/generate-public-pages.py` passed.

## Recommended next actions

### P0 — deploy the prepared foundation

1. Deploy WordPress theme patch.
2. Regenerate and deploy Base2026 static pages/sitemaps.
3. After deploy, re-crawl:
   - `/category/uncategorized/` must show `noindex,follow` or be removed/redirected if we choose a stronger route;
   - `wp-sitemap.xml` must no longer include category/tag sitemap indexes;
   - Base2026 generated nav should not link to `/knowledge/index.html` or `index.html?...`.

### P1 — clean commercial page semantic surface

1. Keep one H1 per commercial page.
2. Keep H2s as real page sections and H3s as children of those sections.
3. Consider demoting repeated footer labels/cookie modal labels from H2 to non-heading elements or isolate them better so automated heading reports are cleaner.
4. Add/verify BreadcrumbList schema on commercial pages if not already supplied by WordPress/Kadence.
5. Add Organization/WebSite schema consistency for the main site and Base2026.

### P1 — make Base2026 more citable, not just crawlable

1. Keep source pages indexable only when they have sufficient public evidence and canonical source text.
2. Keep thin/low-evidence topic pages `noindex,follow`; index only strong topic pages.
3. Add clearer answer-first H2 sections on source/topic pages where useful:
   - `Questions this source answers`
   - `What operators should inspect first`
   - `Related topic evidence`
4. Preserve source attribution, correction/removal controls, and public evidence boundaries for trust.
5. Consider a public `/knowledge/llms.txt` or root `/llms.txt` pointer later, but do not treat it as a Google ranking requirement.

### P2 — crawl-budget and internal-linking hardening

1. Crawl all internal links after deploy and assert:
   - no `index.html?` internal links;
   - no source links with workspace/search query params;
   - no 404s from header/footer/related sections;
   - every indexable source/topic page has at least one internal inbound path.
2. Add a small CI check that parses generated HTML and fails on:
   - zero H1 or multiple H1 in `<main>`;
   - heading jumps in `<main>`;
   - internal links containing `index.html?`;
   - sitemap URLs with query strings.
3. Track live GSC after deploy: Coverage, Crawled - currently not indexed, Duplicate without user-selected canonical, and sitemap submitted/indexed counts.

## Bottom line

The core direction is right: reduce duplicate crawl surfaces, keep WordPress utility archives out of index strategy, and make Base2026 a clean evidence architecture. The remaining important work is deploy + full crawl verification, plus a small semantic cleanup layer so headings/nav/footer do not look noisy to crawlers and accessibility tooling.
