# Base2026 DataForSEO SEO/GEO production release

Verified through 2026-09-03 00:26 UTC.

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

## Release identity and safety

- Git source commits: `16c9ee84b` and `56f78605e` on `codex/base2026-dataforseo-audit-fixes-20260902`.
- Production-only selected patch base: last released API/MCP source `b91fc124f`, commits `bef53ad94` and `d51d5156b`. This prevents the held Claim Receipt Ledger source from being accidentally deployed before migration and eligibility approval.
- Final asset: 4,272 served files, tree SHA-256 `de422d545b43c2fe73f2038c9c2b8ff9517bf906db3d7c122536ca28f9178c2d`.
- Final asset invariants: 1,724 unique source titles/H1s, title maximum 65, 19 pagination pages, 1,763 unique static sitemap URLs, zero duplicate sitemap membership, zero internal relative `.html` links and zero `VideoObject` pages.
- Member-safe build flag was explicit. `my-research/index.html`, member CSS and member JavaScript are present; member CSS/JavaScript hashes match the retained reviewed member release.
- Publication gate passed with four approved public data files and no private marker failure.
- Source branch passed 180 Python tests, 634 Worker tests and TypeScript; the focused source-catalog suite passed 80/80. Production patch branch passed 178 Python tests, 627 Worker tests, TypeScript and final Wrangler dry-run with all public/member bindings.
- Independent reviewer verdict: PASS, no release blocker.

## Canary rollback and final live result

The first canary `f298cd98-6125-4bfe-ab72-afd98467b8ad` exposed two live-gate failures: `/sources/` returned 503 because the runtime shell validator did not accept builder-canonicalized source links, and `/my-research/` returned 404 because the member workspace flag was omitted. It was immediately rolled back to `f8781f4d-30fd-4d70-ab96-a4e8d718226a`; both routes returned 200 after rollback.

The repaired member-safe release is Worker `60429ef4-b1b8-47dc-9af4-b4b882ac2390` at 100%. Live readback confirms:

- homepage, blog, founder, API, MCP, integrations, Evidence Search, source catalog, source pagination and representative static/dynamic source records return 200 with expected canonicals;
- `/my-research/` returns 200 with `noindex,nofollow` and private/no-store policy;
- signed-out `/api/auth/session` remains 403 with private/no-store policy;
- held `/api/claim-receipts/v1` remains 404;
- the recursive sitemap graph has 1,874 occurrences, 1,874 unique URLs and zero duplicate memberships.

Post-release DataForSEO full-crawl task `09030026-1882-0216-0000-a8712b158b1e` is the measurement follow-up. Its final totals must be appended when the remote crawl reaches `finished`; task creation is not a completed verification.

Immediate rollback is `f8781f4d-30fd-4d70-ab96-a4e8d718226a`. Do not use the rejected `f298cd98-6125-4bfe-ab72-afd98467b8ad`.
