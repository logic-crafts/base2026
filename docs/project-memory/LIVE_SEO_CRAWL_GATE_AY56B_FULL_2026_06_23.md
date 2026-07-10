# Live SEO Crawl Gate - 2026-06-17

Status: **PASS**

Analyzed at: 2026-06-23T23:34:33.584Z

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
- Internal links seen: 87586
- Unique internal links seen: 1471
- Redirected crawled pages: 0
- Status counts: {200:1700}

## P0 Gate

- Bad link-contract links (`/contact/`, `/author/`, root `/topics|sources|creators|compare`): 0
- Crawled 4xx/5xx/fetch-error pages: 0
- Crawled 5xx pages: 0

No P0 crawl/link failures found in this bounded live crawl.

## SEO Basics

- noindex_pages: 115
- canonical_missing: 0
- canonical_mismatch_indexable: 1
- title_missing: 0
- meta_description_missing: 0
- h1_missing: 0
- h1_multiple: 0
- og_incomplete: 0
- twitter_incomplete: 0
- schema_missing: 0
- schema_invalid: 0

## Non-Blocking Warnings

- **CANONICAL_MISMATCH_INDEXABLE** (1): Indexable HTML pages whose canonical URL differs from the final URL.
  - https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic

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

Use this gate as the local replacement for the blocked Ahrefs recrawl, then continue P1 crawl architecture work: source archive/internal links, query-state canonical/noindex policy, shared OG/X metadata, schema validation, and sitemap canonical hygiene.

