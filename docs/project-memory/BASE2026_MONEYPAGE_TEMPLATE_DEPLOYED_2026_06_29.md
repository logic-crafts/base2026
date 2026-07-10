# Base2026 Money/CTPH Template Deployed — 2026-06-29

## Scope

Implemented and deployed the Alex/Base2026-style commercial money-page template for the generated Base2026 AI visibility / CTPH / money pages.

Release:

- `base2026-money-template-alex-style-20260629`
- Public path: `https://aggressorbulkit.online/knowledge/`
- Deploy type: data-preserving static/template hotfix from current live public export
- Meilisearch reindex: skipped intentionally; public data membership and index data were preserved

## Implementation

Changed the generated money-page template in:

- `scripts/generate-ai-visibility-pages.py`
- `web/static/styles.css`

Template elements added:

- warm Alex/Base2026 hero section
- conversion-first CTA path to `/ai-visibility-audit/` and `/pricing/`
- right-side diagnostic panel
- diagnostic checkpoint cards
- Base2026 method cards
- offer/commercial CTA section
- priority internal-link cluster
- upgraded contact/audit form wrapper
- mobile overflow safeguards

## QA results

Local/package checks:

- `python3 -m py_compile scripts/generate-ai-visibility-pages.py` passed
- `git diff --check` passed
- package built from live public export with content-readiness checks passed
- public release contract passed with `violation_count=0`
- 5 pilot pages checked in release package: HTTP structure, `index,follow`, self-canonical, one H1, new hero/diagnostic blocks, CTA path and priority links present
- 16 city drafts remained `noindex,nofollow`

Deploy/live checks:

- deploy completed successfully
- nginx config test passed before/after symlink switch
- current release symlink points to `/var/www/base2026-knowledge/releases/base2026-money-template-alex-style-20260629`
- 5 pilot URLs live-tested as `200`, `index,follow`, self-canonical, one H1, new hero/diagnostic blocks, CTA path and priority links present
- live stylesheet is cache-busted as `/knowledge/static/styles.css?v=base2026-money-template-alex-style-20260629`
- sitemap index live with 5 sitemap files and `lastmod=2026-06-29`
- browser visual QA confirmed the new template is visible above the fold; only expected cookie popup overlay was observed

Pilot URLs verified:

- `https://aggressorbulkit.online/knowledge/bing-seo-for-roofing-companies/`
- `https://aggressorbulkit.online/knowledge/bing-seo-for-hvac-companies/`
- `https://aggressorbulkit.online/knowledge/bing-seo-for-law-firms/`
- `https://aggressorbulkit.online/knowledge/ai-visibility-audit-for-local-service-businesses/`
- `https://aggressorbulkit.online/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/`

## IndexNow

Submitted changed indexable money/template URLs through live-gated IndexNow flow:

- candidate URLs: 48
- eligible URLs: 48
- skipped URLs: 0
- IndexNow response: `200`

Artifacts:

- `output/indexnow/base2026-money-template-20260629-urls.txt`
- `output/indexnow/base2026-money-template-20260629-payload.json`
- `output/indexnow/base2026-money-template-20260629-checks.csv`

## Remaining follow-ups

- Check Bing/GSC dashboards after crawl cycle instead of blindly resubmitting all URLs again.
- Close the local data-changing blocker before any next data release: fresh source-only TikTok record still needs review/topic/insight assignment or exclusion.
- Continue LinkedIn/UGC amplification only against the now-polished commercial pages.
