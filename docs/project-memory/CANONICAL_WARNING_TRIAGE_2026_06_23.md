# Canonical warning triage — 2026-06-23

URL: `https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic`

## Finding

The ay56b full live crawl reported one non-blocking canonical mismatch:

- final URL: `https://aggressorbulkit.online/ai-visibility-audit/?plan=diagnostic`
- status: `200`
- canonical: `https://aggressorbulkit.online/ai-visibility-audit/`
- robots: `max-image-preview:large`
- H1 count: `1`

A direct live fetch confirmed the same behavior for both the query URL and the clean URL. The query URL remains `200`, and WordPress/Rank Math emits the clean canonical.

## Conclusion

This is not actionable inside the Base2026 repo. The URL belongs to the WordPress/personal-site conversion layer (`/ai-visibility-audit/`), while Base2026 static output lives under `/knowledge/`.

Treat the warning as acceptable unless GSC/Ahrefs shows material duplicate-indexing or crawl-budget issues for the query variants. The current behavior can be a valid conversion-context pattern: package/query parameters preserve user context while canonicalizing ranking signals to the clean audit page.

## If it becomes actionable

Handle it in the WordPress/personal-site layer, not in Base2026:

1. Keep the canonical URL as `/ai-visibility-audit/`.
2. Either leave query variants indexable-but-canonicalized, or add a WordPress-layer noindex/redirect rule for known `?plan=` URLs if duplicates become noisy.
3. Preserve package/context tracking for the lead form if that is still needed.
4. Re-run WordPress footer/social-preview QA after any theme/plugin edit.

## Verification evidence

- Full crawl artifact: `output/seo-crawl-gate/ay56b-full-20260623/summary.json`
- Full crawl result: 1,700 crawled pages, 1,577 sitemap URLs, all crawled pages `200`, bad link-contract count `0`, crawled error pages `0`.
- Direct live fetch: both `/ai-visibility-audit/?plan=diagnostic` and `/ai-visibility-audit/` return `200` with canonical `https://aggressorbulkit.online/ai-visibility-audit/`.
