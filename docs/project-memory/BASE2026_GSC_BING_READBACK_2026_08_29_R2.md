# Base2026 GSC/Bing readback R2 — 2026-08-29

Scope: read-only measurement in the authenticated Base2026 work identity. No
URL inspection request, sitemap resubmission, IndexNow notification, property
change, deployment, D1 write, or external publication was made.

Evidence tier: Tier 2 first-party dashboard evidence. Counts can change as the
engines finish processing; the next dashboard readback supersedes this dated
receipt.

## Google Search Console

- Property: `sc-domain:base2026.dev`; visible account: `hello@base2026.dev`.
- Performance, last three months: 0 clicks, 22 impressions, 0% CTR, average
  position 55.4.
- Visible early queries include `self promotional listicles` (2 impressions,
  average position 40.5), `chatgpt citation tracker` (2 impressions),
  `ai citation tracking definition` (2 impressions), and
  `how to get cited in ai search` (1 impression).
- Thirteen pages have impressions. The leading route is the historical
  `.html` form of `/topics/ai-citation-tracking` with 8 impressions; Roadmap
  has 3; the topic and comparison routes for self-promotional listicles and
  the content-refresh solution route have 2 each. Eight additional source,
  topic, Story and Workspace routes have 1 impression each.
- Page indexing and Links still say `Processing data, please check again in a
  day or so`; neither report exposes a usable indexed-page or backlink dataset.
- Static sitemap: submitted 2026-08-28, last read 2026-08-29, `Success`, 1,634
  discovered pages.
- Dynamic sitemap: submitted 2026-08-28, last read 2026-08-29, `Success`, 49
  discovered pages.

### Canonical transition readback

- `https://base2026.dev/topics/ai-citation-tracking.html` is currently reported
  as indexed by Google.
- The extensionless route is reported as a non-indexed alternate whose stored
  crawl selected the `.html` URL as canonical. That stored crawl predates the
  2026-08-28 live correction, where `.html` redirects to the extensionless URL
  and the extensionless page self-canonicalizes.
- The new engineering journal URL is currently unknown to Google.
- This is a normal recrawl/consolidation transition, not evidence that the live
  canonical contract regressed. No manual indexing request was sent.

## Bing Webmaster Tools

- Selected site: `base2026.dev/`.
- Search Performance still says that data is being prepared and asks to check
  back in 48 hours.
- AI Performance, last three months: 0 citations and average cited pages 0; no
  grounding-query dataset is available.
- Known sitemaps: 2; errors: 0; warnings: 0; 872 URLs discovered in total.
- Sitemap index: `Success`, last submitted/crawled 2026-08-28, six child
  sitemaps.
- Dynamic sitemap: `Success`, 39 URLs discovered.
- Backlinks, Site Explorer indexed URLs, and Recommendations expose no data yet.
- Journal URL inspection: Bing Index says `Discovered but not crawled`; a live
  test on 2026-08-29 says the URL can be indexed, finds no SEO/GEO issue, and
  recognizes two markup types. No manual indexing request was sent.

## Operating conclusion

Google has moved from zero reporting to early query/page impressions, while
Bing is still preparing measurement data. Preserve the current canonicals and
sitemaps, let engines recrawl, and measure query/page growth before creating a
second version of the same article or resubmitting unchanged URLs.
