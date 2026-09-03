# Base2026 DataForSEO SEO/GEO production release

Verified through 2026-09-03 01:08 UTC.

## Audit evidence

- DataForSEO full-crawl task `09022244-1882-0216-0000-9accf64c340c` finished by empty queue after 3,782 URLs/resources. OnPage score was 95.30; broken internal links, broken resources, redirect loops, 5xx responses, recursive canonicals and canonicals to broken/redirect targets were all zero.
- The only 404 was the explicitly supplied but nonexistent `/journal/` priority probe. It was not an internal-link or sitemap failure.
- The reproducible baseline quality debt was 635 duplicate titles, 843 titles over the crawler threshold, 1,922 redirects/links to redirects, 85 favicon warnings and five duplicate guide URLs across sitemap feeds.
- An independent exhaustive public crawl fetched all 1,746 baseline sitemap URLs: every URL returned 200, remained indexable and self-canonical. It confirmed the title/H1/sitemap findings and found zero broken sampled internal targets and zero orphan candidates.
- A ten-template rendered DataForSEO probe finished 10/10 with score 96.6. The homepage lab LCP was 1,372 ms and API LCP 488 ms; no rendered broken/orphan page was found.
- An independent ChatGPT Pro reasoning audit agreed that provenance is the product strength and that controlled indexation, not broad automatic indexation, is the correct release policy.

## Released fixes

- Static source pages now have deterministic, unique browser titles of at most 65 characters and unique claim-led H1s that preserve a short source ID.
- Dynamic public source pages retain a short source ID in both browser title and H1 and include favicon/touch-icon links.
- The static source catalog now has 19 normal pagination pages so all 1,525 indexable static source records are reachable without creating query-state crawl expansion.
- Internal links are emitted directly to extensionless canonical routes instead of `.html` aliases; the source-catalog runtime accepts both pre-build and canonicalized shell forms.
- Static sitemap ownership is deduplicated: guide and hub URLs have one owner, and neighboring sitemap records are protected by regression tests.
- Misleading `VideoObject` markup was removed from pages that link to a TikTok webpage rather than a directly accessible media object. `CreativeWork` attribution remains.
- Editorial structured data always has a valid fallback image, and a small set of overlong core titles was shortened.
- Every generated source description now includes its stable source ID; the
  1,724 released static source descriptions are unique and at most 159
  characters. Dynamic D1 source descriptions use the same ID-based invariant.
- Blog and editorial calls to action link directly to `/workspace/`, removing
  the only crawl-discovered internal hop through `/workspace`.
- AI Recommends `Article` schema now declares the existing public social image.

## Release identity and safety

- Git source commits: `16c9ee84b`, `56f78605e` and final correction
  `d541d0aa8`; PR39 merged them to main as `fa9d30bfdb0489bc031164101aebfeae5fecb55c`.
- Production-only selected patch base: last released API/MCP source `b91fc124f`,
  commits `bef53ad94`, `d51d5156b` and final runtime patch `e152e73ae`.
  This prevents the held Claim Receipt Ledger source from being accidentally
  deployed before migration and eligibility approval.
- Final asset: 4,272 served files, tree SHA-256 `0b547f531bcbcd4543d89ebcc55050d78697bcf7b670ef884ec50d25278669d4`.
- Final asset invariants: 1,724 unique source titles/H1s, title maximum 65, 19 pagination pages, 1,763 unique static sitemap URLs, zero duplicate sitemap membership, zero internal relative `.html` links and zero `VideoObject` pages.
- Member-safe build flag was explicit. `my-research/index.html`, member CSS and member JavaScript are present; member CSS/JavaScript hashes match the retained reviewed member release.
- Publication gate passed with four approved public data files and no private marker failure.
- Source branch passed 181 Python tests. Production patch branch passed 627
  Worker tests, TypeScript and final Wrangler dry-run with all public/member bindings.
- Independent reviewer verdict: PASS, no release blocker.

## Canary rollback and final live result

The first canary `f298cd98-6125-4bfe-ab72-afd98467b8ad` exposed two live-gate failures: `/sources/` returned 503 because the runtime shell validator did not accept builder-canonicalized source links, and `/my-research/` returned 404 because the member workspace flag was omitted. It was immediately rolled back to `f8781f4d-30fd-4d70-ab96-a4e8d718226a`; both routes returned 200 after rollback.

The repaired member-safe canary was Worker `60429ef4-b1b8-47dc-9af4-b4b882ac2390`. Later bounded releases shortened the last 68-character solution title to 61 characters, added the validated Article image, removed the single `/workspace` redirecting link and made all source descriptions deterministic. Final Worker `99849d8e-802d-4e8e-a840-8d352f176da6` is at 100%. Live readback confirms:

- homepage, blog, founder, API, MCP, integrations, Evidence Search, source catalog, source pagination and representative static/dynamic source records return 200 with expected canonicals;
- `/my-research/` returns 200 with `noindex,nofollow` and private/no-store policy;
- signed-out `/api/auth/session` remains 403 with private/no-store policy;
- held `/api/claim-receipts/v1` remains 404;
- the recursive sitemap graph has 1,874 occurrences, 1,874 unique URLs and zero duplicate memberships.

The second full task `09030026-1882-0216-0000-a8712b158b1e` crossed several
live versions while crawling. It was stopped at 2,260 pages instead of being
misrepresented as a clean after-snapshot. It exposed the last internal
`/workspace` 307 and source-description duplication before their fixes.

Fresh bounded DataForSEO evidence after the final corrections:

- task `09030033-1882-0216-0000-17a075b38002`: solution title length 61,
  HTTP 200, self-canonical, favicon present, no broken link and no long-title flag;
- task `09030059-1882-0216-0000-af4277b30e3b`: Article structured data has
  fatal 0, errors 0 and warnings 0;
- task `09030102-1882-0216-0000-6cce65a9fdae`: ten-page blog probe has
  redirects 0, links to redirects 0, broken links 0 and 4xx/5xx 0.

Immediate rollback is `14174d46-c237-4ad9-897c-7952060f3e70`; second-level
rollback is `60429ef4-b1b8-47dc-9af4-b4b882ac2390`. Do not use the rejected
`f298cd98-6125-4bfe-ab72-afd98467b8ad`.
