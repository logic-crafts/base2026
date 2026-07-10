# Base2026 ночная смена — 2026-06-26

## Статус
- done: inspected repo/state, project-memory, generated web/static output, sitemap, AI visibility batch data, TikTok/public export artifacts.
- done: session_search по `Base2026 TikTok transcript расшифровка транскрипт short-form creator видео` вернул 0 совпадений, поэтому новые chat-only материалы не подхвачены.
- done: проверены локальные TikTok/public-safe источники: `public-data/tiktok/`, `12_knowledge-base/sources/tiktok/insight-candidates/`, `docs/research/TIKTOK_PRESS_RELEASE_AI_VISIBILITY_CASE_2026_06_26.md`.
- done: исправлен генератор AI visibility страниц: page-specific H1, брендовый hero больше не единственный H1, city/niche pages noindex до уникальной локальной evidence-базы, очищен duplicated Google Fonts URL.
- done: очищен `data/ai_visibility_pages_batch01.json` от private absolute `source_file` путей и нормализован display `HVAC`.
- done: перегенерированы AI visibility pages в `web/static` и sitemap.
- done: добавлены `web/static/topics/index.html` и `web/static/creators/index.html`, чтобы навигационные ссылки `/knowledge/topics/` и `/knowledge/creators/` не вели в пустоту.
- blocked: public deploy не выполнялся. Ночная задача разрешала deploy только при очевидно безопасном existing production pipeline; в текущем проходе безопаснее оставить deploy-ready local batch после QA.

## Команды и проверки
```bash
git status --short
python3 scripts/generate-ai-visibility-pages.py --input data/ai_visibility_pages_batch01.json --out web/static --indexable
python3 scripts/generate-base2026-sitemap.py --web-root web/static --base-url https://aggressorbulkit.online/knowledge --out web/static/sitemap.xml
```

Проверки после генерации:
- `city_noindex=1` для `web/static/california/los-angeles-roofers-ai-visibility-audit/index.html`.
- `hub_index=1` для `web/static/hvac-marketing-ai-visibility/index.html`.
- `collection_h1=True` для `web/static/ai-visibility-pages/index.html`.
- `city_h1=True` для `web/static/california/los-angeles-roofers-ai-visibility-audit/index.html`.
- `topics_index_exists=True`, `creators_index_exists=True`.
- `source_file_in_json=False`.
- `los_angeles_roofers_in_sitemap=False`, потому что city/niche page теперь noindex и sitemap-generator исключил её.
- `hvac_hub_in_sitemap=True`.
- sitemap: `sitemap_urls=473 sitemap_files=2`.
- `git diff --check` passed.
- `PYTHONPYCACHEPREFIX=/private/tmp/base2026-pycache python3 -m py_compile scripts/generate-ai-visibility-pages.py scripts/generate-base2026-sitemap.py scripts/audit-publication-boundary.py` passed.
- `python3 scripts/audit-publication-boundary.py` => `changed_files=62`, `needs_review=0`, `forbidden=0`, `secret_findings=0`, `ok_to_stage_public_safe_candidates=true`.
- `python3 scripts/validate-public-release-contract.py --export-dir ./public-data/tiktok --baseline-export-dir ./public-data/tiktok --enforce-count-floor` => `ok=true`, `violation_count=0`.

## QA вывод
Индексируемыми оставлены broad hub/collection pages. 16 California city/niche pages пока выведены из индекса и sitemap, потому что QA показал высокий doorway/near-duplicate риск: после нормализации city/niche они схлопываются в 4 body-шаблона без локальных доказательств. Их можно возвращать в индекс только после добавления city-specific evidence.

## TikTok/source status
- Public export exists: `public-data/tiktok/manifest.json`, `documents.jsonl`, `chunks.jsonl`, `creators.jsonl`.
- Manifest signal from local inspection: 1512 documents, 2063 chunks, 10 creators, 1066 public insight cards, `include_full_transcripts=false`, `public_policy=excerpt_only`.
- Recent refresh logs show 18 new candidate video IDs in preview/import-check mode, but `apply=false`, so they are not reviewed public sources yet.
- `docs/research/TIKTOK_PRESS_RELEASE_AI_VISIBILITY_CASE_2026_06_26.md` remains internal only until Yahoo Finance / GlobeNewswire / follow-on article URLs are independently verified and rewritten for public use.

## Next concrete slice
1. Build one evidence-backed public page from reviewed insight cards, not from raw transcripts: `Measuring AI visibility when query/click data disappears`.
2. Add 3-5 cited source cards from `reviewed-candidates.jsonl` and public source pages.
3. Keep city/niche pages noindex until each page has local SERP/source evidence.
4. If Alex approves, deploy the current safe batch after a production pipeline preflight.


## Continuation tick — 2026-06-26 04:07 Minsk
- done: built the next source-backed public page candidate: `/knowledge/measuring-ai-visibility-without-query-click-data/`.
- done: page evidence stack uses official Google docs first, then reviewed Base2026 TikTok insight cards. No raw transcript text was published.
- done: generator now supports safe Markdown links in generated body copy, with external links marked `target="_blank" rel="noopener noreferrer"`.
- done: regenerated `web/static` AI visibility pages and sitemap. Local static sitemap now includes the new measurement page in `web/static/sitemaps/base2026-001.xml`.
- done: patched `scripts/package-public-hotfix-from-export.ps1` so data-preserving hotfix packages include the AI visibility page batch, not only source/topic generated pages.
- done: created deploy-ready local package, not deployed: `output/releases/base2026-nightshift-ai-visibility-measurement-20260626.zip`.
- verified: release package contains `/web/measuring-ai-visibility-without-query-click-data/index.html`, `index,follow`, canonical URL, source links, and sitemap entry.
- verified: California city/niche drafts remain `noindex,nofollow` and absent from release sitemaps.
- blocked: no public deploy executed because the current cron task allowed deploy only if fully safe and obvious; package is ready for approval-gated deploy.

Additional checks:
```bash
python3 scripts/generate-ai-visibility-pages.py --input data/ai_visibility_pages_batch01.json --out web/static --indexable
python3 scripts/generate-base2026-sitemap.py --web-root web/static --base-url https://aggressorbulkit.online/knowledge --out web/static/sitemap.xml
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/package-public-hotfix-from-export.ps1 -ReleaseName base2026-nightshift-ai-visibility-measurement-20260626 -MeiliUrl /knowledge-search
git diff --check
PYTHONPYCACHEPREFIX=/private/tmp/base2026-pycache python3 -m py_compile scripts/generate-ai-visibility-pages.py scripts/generate-base2026-sitemap.py scripts/audit-publication-boundary.py
python3 scripts/audit-publication-boundary.py
python3 scripts/validate-public-release-contract.py --export-dir ./public-data/tiktok --baseline-export-dir ./public-data/tiktok --enforce-count-floor
```

Package output:
- `release=base2026-nightshift-ai-visibility-measurement-20260626`
- `path=output/releases/base2026-nightshift-ai-visibility-measurement-20260626`
- `zip=output/releases/base2026-nightshift-ai-visibility-measurement-20260626.zip`

## Continuation tick — 2026-06-26 05:07 Minsk
- done: live network and SSH became available from this cron context: `curl -I https://aggressorbulkit.online/knowledge/` returned `200`; `ssh geo 'echo ssh_ok'` returned `ssh_ok`.
- done: deployed the first measurement package with the existing data-preserving hotfix path, then immediately fixed non-blocking social metadata warnings found by the live crawl.
- done: created a proper 1200×630 social preview card at `web/static/assets/base2026-ai-visibility-card.png` instead of using the square avatar as the large-card image.
- done: patched `scripts/generate-ai-visibility-pages.py` to emit complete OG/X metadata for AI visibility pages and the collection page, and to reuse a deduplicated Google Fonts URL.
- done: regenerated AI visibility pages and sitemap, packaged, and deployed `base2026-nightshift-ai-visibility-measurement-socialfix-20260626` with `-SkipPackage -SkipReindex`.
- verified: server current symlink points to `/var/www/base2026-knowledge/releases/base2026-nightshift-ai-visibility-measurement-socialfix-20260626`.
- verified: `/knowledge/measuring-ai-visibility-without-query-click-data/` returns `200`, has one H1, `index,follow`, canonical URL, complete OG/X image metadata, and uses `/knowledge/static/assets/base2026-ai-visibility-card.png`.
- verified: `/knowledge/ai-visibility-pages/` returns `200`, has one H1, `index,follow`, canonical URL, and complete OG/X image metadata.
- verified: sample city/niche draft `/knowledge/california/los-angeles-roofers-ai-visibility-audit/` returns `200` but stays `noindex,nofollow`.
- verified: social preview image returns `200 image/png`, server file is `1200 x 630`.
- verified: live sitemap index has 5 child sitemaps / 1,620 URLs; child `base2026-001.xml` includes the measurement page; city/niche noindex draft is absent.
- verified: `node scripts/live-seo-crawl-gate.mjs` passed after deploy: 500 crawled pages, 1,620 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.
- verified: `git diff --check`, Python compile gate, publication-boundary audit (`changed_files=63`, `needs_review=0`, `forbidden=0`, `secret_findings=0`), and public release contract (`ok=true`, `violation_count=0`) passed.
- not_attempted: no GSC request-indexing clicks, no IndexNow push, no Ahrefs recrawl, no registrations, no paid actions, no outreach.
- package sitemap: `sitemap_urls=1620 sitemap_files=5`

## Final resume verification after context compaction — 2026-06-26
- done: reread current repo state, project-memory source-of-truth files, overnight artifacts, and `CURRENT_HANDOFF.md` after context compaction.
- done: `session_search` for fresh Base2026/TikTok/transcript context returned 0 matches; no new chat-only TikTok transcript material was available to ingest.
- fixed: normalized `docs/project-memory/STATUS_BOARD.csv` line endings after `git diff --check` flagged CRLF/trailing-whitespace noise.
- verified: `git diff --check` passed.
- verified: `PYTHONPYCACHEPREFIX=/private/tmp/base2026-pycache python3 -m py_compile scripts/generate-ai-visibility-pages.py scripts/generate-base2026-sitemap.py scripts/audit-publication-boundary.py` passed.
- verified: `python3 scripts/audit-publication-boundary.py` => `changed_files=67`, `needs_review=0`, `forbidden=0`, `secret_findings=0`.
- verified: `python3 scripts/validate-public-release-contract.py --export-dir ./public-data/tiktok --baseline-export-dir ./public-data/tiktok --enforce-count-floor` => `ok=true`, `violation_count=0`.
- verified: live smoke for measurement page, AI visibility collection, city/niche noindex sample, and social preview image returned expected status/robots/metadata.
- verified: `node scripts/live-seo-crawl-gate.mjs` => `status=pass`, 500 crawled pages, 1,620 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.

## Continuation tick — 2026-06-26 AI-ready documentation page
- done: added source-backed page `/knowledge/ai-ready-business-documentation-for-service-pages/` from official Google Search documentation plus reviewed Base2026 insight cards `tiktok:tjrobertson52:7644738887486639373` and `tiktok:tjrobertson52:7649531548655521038`.
- done: regenerated AI visibility pages and sitemap; local sitemap now has 475 URLs and includes the new page.
- done: packaged and deployed data-preserving hotfix `base2026-ai-ready-documentation-page-20260626`; Meilisearch reindex skipped because public passage/index data did not change.
- verified: live page returns `200`, has one H1, `index,follow`, canonical URL, official Google links, reviewed Base2026 source IDs, and sitemap inclusion.
- verified: city/niche sample remains `noindex,nofollow` and absent from sitemap.
- verified: `node scripts/live-seo-crawl-gate.mjs` passed with 500 crawled pages, 1,621 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.
- verified: `git diff --check`, publication-boundary audit, and public release contract passed.
- not_attempted: no GSC request-indexing clicks, no IndexNow push, no Ahrefs recrawl, no registrations, no paid actions, no outreach.

## Continuation tick — 2026-06-26 review sentiment page
- done: added source-backed public page `/knowledge/review-sentiment-and-ai-visibility-for-local-businesses/` on review sentiment, Google Business Profile review handling, service-page proof, and AI visibility.
- evidence: official Google Business Profile review docs, Google Search business-details docs, Google AI Search guidance, and reviewed Base2026 insight cards `tiktok:darrenshawseo:7654610774547074311`, `tiktok:gobigsystems:7652081880103275789`, `tiktok:darrenshawseo:7652007874536819976`, `tiktok:webhivedigital:7654592219722157334`.
- done: regenerated AI visibility pages and sitemap; local `web/static` has 24 generated AI visibility artifacts including the collection page.
- done: ran canonical release gate and deployed `base2026-review-sentiment-ai-visibility-20260626` through `scripts/base2026-release-gate.ps1 -Deploy -SkipLiveQa`; deploy step reindexed Meilisearch task `439` and switched the server current symlink to `/var/www/base2026-knowledge/releases/base2026-review-sentiment-ai-visibility-20260626`.
- verified: live new page returns `200`, has H1, `index,follow`, canonical URL, official Google source links, and sitemap inclusion.
- verified: live sample city/niche draft remains `noindex,nofollow`.
- verified: live SEO crawl gate passed: 500 crawled pages, 1,622 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.
- verified: release gate passed `git diff --check`, content readiness, publication-boundary audit, GitHub metadata, public export policy, and public release contract.
- not_attempted: no GSC request-indexing clicks, no IndexNow push, no Ahrefs recrawl, no external registrations, no paid actions, no outreach.
## Continuation tick — 2026-06-26 service-area AI visibility page
- done: added source-backed public page `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/` on safe service-area pSEO, Google Business Profile service-area limits, proof requirements, and noindex gates for weak city pages.
- evidence: official Google Business Profile service-area guidance, Google SEO Starter Guide, Google AI Search guidance, and reviewed Base2026 insight cards `tiktok:darrenshawseo:7652384458804432136`, `tiktok:gobigsystems:7652520714678832398`, `tiktok:build_in_public:7511085007818001686`, `tiktok:tjrobertson52:7553015536142126391`.
- done: regenerated AI visibility pages and sitemap; local `web/static` generator returned `pages=25`, `sitemap_urls=477`, `sitemap_files=2`.
- done: packaged and deployed data-preserving hotfix `base2026-service-area-ai-visibility-20260626`; Meilisearch reindex skipped because public passage/search data did not change.
- verified: live new page returns `200`, has one H1, `index,follow`, canonical URL, official source links, reviewed Base2026 source IDs, and child sitemap inclusion in `base2026-001.xml`.
- verified: live sample city/niche draft remains `noindex,nofollow` and absent from child sitemaps.
- verified: live SEO crawl gate passed: 500 crawled pages, 1,623 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.
- verified: `git diff --check`, Python compile gate, publication-boundary audit, and public release contract passed.
- not_attempted: no GSC request-indexing clicks, no IndexNow push, no Ahrefs recrawl, no external registrations, no paid actions, no outreach.
