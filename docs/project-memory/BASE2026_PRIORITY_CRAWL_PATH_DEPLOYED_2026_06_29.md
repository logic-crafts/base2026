# Base2026 priority crawl path deployed — 2026-06-29

## Release

- Release name: `base2026-priority-crawl-path-20260629`
- Public path: `https://aggressorbulkit.online/knowledge/`
- Server current symlink after deploy: `/var/www/base2026-knowledge/releases/base2026-priority-crawl-path-20260629`
- Deploy mode: data-preserving static hotfix, `-SkipPackage -SkipReindex` after a locally built zip from live production public-data.

## Why live public-data was used

The normal local hotfix packaging path initially failed the public content readiness gate because local `public-data/tiktok` contained one newest source-only TikTok record without public topic/insight assignment:

- source: `tiktok:gobigsystems:7656643400426458382`
- reason: `public_text_without_topics_or_public_insights`

To avoid accidentally shipping new unreviewed data, the hotfix package was rebuilt from the current live server export:

- documents/source records: `1543`
- passages: `2097`
- insight cards: `1642`

This kept the release strictly static/data-preserving.

## Change shipped

Added a visible `Priority crawl path` section to the generated AI visibility/money-page template through `scripts/generate-ai-visibility-pages.py`.

The block strengthens internal links around 10 priority Bing/Copilot/local-service pages plus the AI Visibility Lab hub.

Priority set:

- `/knowledge/ai-visibility-pages/`
- `/knowledge/bing-seo-for-roofing-companies/`
- `/knowledge/bing-seo-for-hvac-companies/`
- `/knowledge/bing-seo-for-law-firms/`
- `/knowledge/bing-seo-for-dentists-and-clinics/`
- `/knowledge/bing-seo-for-local-contractors/`
- `/knowledge/bing-webmaster-tools-ai-visibility-audit/`
- `/knowledge/ai-visibility-audit-for-local-service-businesses/`
- `/knowledge/ai-visibility-audit-for-bing-traffic/`
- `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/`
- `/knowledge/copilot-seo-for-service-businesses/`

## Package output

- Generated AI visibility pages: `65`
- Generated sitemap URLs: `1703`
- Sitemap files: `5`
- Release zip: `output/releases/base2026-priority-crawl-path-20260629.zip`

## QA evidence

Local release QA:

- All 10 priority money pages plus AI Visibility Lab existed in the release package.
- All checked priority pages had `index,follow`.
- All checked priority pages had self-canonical URLs.
- All checked priority pages had one H1.
- All checked priority pages had the `Priority crawl path` block.
- AI Visibility Lab had 20 priority-link occurrences.
- Priority pages had 10–11 priority-link occurrences.
- CTA paths remained present.

Deploy output:

- `nginx -t` passed.
- nginx remained `active`.
- current symlink resolved to `/var/www/base2026-knowledge/releases/base2026-priority-crawl-path-20260629`.

Live QA:

- Checked 11 live URLs.
- Bad live checks: `0`.
- All checked pages returned HTTP 200.
- All checked pages were `index,follow`.
- All checked pages had self-canonical URLs.
- All checked pages had one H1.
- All checked pages had the priority crawl-path block.
- Static CSS returned HTTP 200 with gzip and long-lived immutable cache headers.
- Live sitemap index showed 5 sitemap chunks dated 2026-06-29.
- Browser smoke check of `/knowledge/bing-seo-for-roofing-companies/` showed hero, H1, CTAs and content visible.

## IndexNow after deploy

Submitted only the changed priority set after live eligibility checks.

- Input URLs: `11`
- Eligible URLs: `11`
- Skipped URLs: `0`
- IndexNow HTTP status: `202`
- Payload: `output/indexnow/base2026-priority-crawl-path-payload-20260629.json`
- Checks: `output/indexnow/base2026-priority-crawl-path-checks-20260629.csv`

## Important follow-up

The local public-data readiness blocker should be resolved before the next data-changing release. The blocked `@gobigsystems` record needs reviewed public topic/insight assignment or exclusion before using local `public-data/tiktok` as a release source again.

Next high-leverage step: after Bing/GSC crawl-cycle delay, check discovered/indexed/excluded states for the 11 priority URLs, then pick 3–5 strongest pages for CTA/analytics/conversion testing.
