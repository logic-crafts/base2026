# Live SEO Crawl Gate - 2026-06-17

Status: **FAIL**

Analyzed at: 2026-06-23T23:01:13.325Z

Base URL: https://aggressorbulkit.online

## Scope

- Live crawl starting from `/`, `/knowledge/`, and `/knowledge/sitemap.xml`.
- Max pages: 1700.
- Robots respected for same-site crawl decisions.
- No GSC, IndexNow, Ahrefs recrawl, deploy, commit, push, or TikTok intake was run.

## Summary

- Crawled pages: 1700
- Sitemap URLs: 1577
- Sitemap files: 4
- Internal links seen: 85813
- Unique internal links seen: 1932
- Redirected crawled pages: 0
- Status counts: {200:1669,404:31}

## P0 Gate

- Bad link-contract links (`/contact/`, `/author/`, root `/topics|sources|creators|compare`): 0
- Crawled 4xx/5xx/fetch-error pages: 31
- Crawled 5xx pages: 0

### Critical Findings

- **CRAWLED_4XX_5XX_OR_FETCH_ERROR** (31): At least one crawled internal URL returned 4xx/5xx or failed to fetch.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html
  - https://aggressorbulkit.online/knowledge/topics/seo-budget-prioritization.html
  - https://aggressorbulkit.online/knowledge/topics/google-business-profile-spam-reporting.html

## SEO Basics

- noindex_pages: 84
- canonical_missing: 31
- canonical_mismatch_indexable: 1
- title_missing: 0
- meta_description_missing: 31
- h1_missing: 0
- h1_multiple: 0
- og_incomplete: 31
- twitter_incomplete: 31
- schema_missing: 31
- schema_invalid: 0

## Non-Blocking Warnings

- **CANONICAL_MISSING** (31): HTML pages missing canonical URL.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html
- **CANONICAL_MISMATCH_INDEXABLE** (1): Indexable HTML pages whose canonical URL differs from the final URL.
  - https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic
- **META_DESCRIPTION_MISSING** (31): HTML pages missing meta description.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html
- **OG_INCOMPLETE** (31): Indexable HTML pages with incomplete Open Graph tags.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html
- **TWITTER_INCOMPLETE** (31): Indexable HTML pages with incomplete X/Twitter card tags.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html
- **SCHEMA_MISSING** (31): Indexable HTML pages with no JSON-LD schema.
  - https://aggressorbulkit.online/knowledge/topics/local-pack-ranking-factors.html
  - https://aggressorbulkit.online/knowledge/topics/local-seo-myths.html
  - https://aggressorbulkit.online/knowledge/topics/risk-avoid-fake-reviews.html

## Files

- Machine summary: `output/seo-crawl-gate/latest/summary.json`
- Crawled page details: `output/seo-crawl-gate/latest/pages.json`
- Link details: `output/seo-crawl-gate/latest/links.json`
- Issue details: `output/seo-crawl-gate/latest/issues.json`
- Cache summary: `.seo-cache/live-crawl-summary.json`

## Limitations

- This is a bounded live crawl, not an Ahrefs replacement for historical external crawl metrics.
- The crawl is capped at 1700 pages; sitemap contains 1577 URLs.
- The gate validates current live HTML/link contracts and metadata basics; it does not submit URLs to GSC, IndexNow, or Ahrefs.

## Next Safe SEO Action

Fix the listed P0 failures before any GSC/IndexNow submission or public SEO push.

