# Deployment Runbook

Current public path:

- Root URL: `https://aggressorbulkit.online/`
- Base2026 URL: `https://aggressorbulkit.online/knowledge/`
- WordPress root: `/var/www/alex-yarosh`
- server current symlink: `/var/www/base2026-knowledge/current`
- server releases: `/var/www/base2026-knowledge/releases/`
- latest deployed release: `base2026-card-completeness-r1-20260710-173448`
- SSL certificate: Let's Encrypt `aggressorbulkit.online`, domains `aggressorbulkit.online` and `www.aggressorbulkit.online`, auto-renewed by `certbot.timer`

Latest WordPress root visual pass: `alex-yarosh` child theme `style.css?ver=1.5.63`, applied directly on 2026-06-19 for the compact `/about/` founder hero. Cache Enabler generated cache for `aggressorbulkit.online` should be cleared after direct theme updates.

## Domain and SSL

The nginx site `alex-yarosh` serves WordPress at the root and aliases Base2026 under `/knowledge/`.

The `/knowledge/static/` location should be declared before the broader `/knowledge/` alias and should set long-lived immutable cache headers plus gzip for CSS, JS, JSON, and SVG assets. The broader `/knowledge/` location serves HTML and fallback routing.

Canonical domain:

```text
https://aggressorbulkit.online
```

WordPress options must stay aligned:

```bash
cd /var/www/alex-yarosh
wp option get home --allow-root
wp option get siteurl --allow-root
```

Expected value for both:

```text
https://aggressorbulkit.online
```

SSL check:

```bash
certbot certificates
systemctl list-timers | grep certbot
nginx -t
```

## Local package

Current live release: `base2026-card-completeness-r1-20260710-173448`.

Latest data/reindex checkpoint: the same completeness release, with Meilisearch task `487` succeeded.

Current live export has 1,493 normal public cards, 199 provenance archive/noindex records, 122 private future-backlog sources, 1,692 public source records, 2,276 public passages, 2,396 insight cards, 1,873 public insight cards, 1,628 topics, and 18 creators. Normal incomplete cards = 0. Machine receipt: `.planning/tiktok-pipeline-v2/production-completeness-release-receipt-2026-07-10.json`.

Latest IndexNow closure for this release: 1,734/1,734 current sitemap URLs passed the live 200/indexable/self-canonical gate and were accepted with HTTP 200; 62/62 previous-public/current-private URLs returned 404 and their deletion notification was accepted with HTTP 200; all 199 archive URLs were live `noindex` and excluded. Receipt: `.planning/tiktok-pipeline-v2/indexnow-card-completeness-2026-07-10/indexnow-release-closure-receipt.json`.

The `base2026-api-nav-footer-r3-20260616` deploy changed generated HTML/navigation and the hotfix packaging contract only. It intentionally skipped Meilisearch reindex because public data and index fields did not change. The deploy fixed global `/knowledge/api.html` navigation in the search root, generated pages, mobile Base2026 nav, and footer.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-public-release.ps1 -ReleaseName <release-name>
```

Current public packages use reviewed public source text where policy allows. Latest deployed release: `base2026-identity-disclaimer-20260626` (identity/legal disclaimer hotfix: Base2026 is an independent experimental startup product created by Alex Yarosh and owned by Logic Crafts LLC, Kyrgyzstan; it is not a marketing agency or marketing-services offering). Public package/deploy scripts must not expose `-IncludeFullTranscripts` as a public shortcut and must not call `--auto-promote-insights`. Raw captions, raw ASR, media, private QA, and unreviewed transcripts stay private. Private/gated review exports should use `scripts/export-public-tiktok.py --out <ignored-private-dir>` directly and must not be deployed as the public `/knowledge/` release.

Latest data-preserving static hotfix: `base2026-bing-money-pages-r1-20260628`. It added the live source-backed `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/` page, preserves the live measurement, AI-ready documentation, and review sentiment pages, keeps AI visibility collection/social metadata complete, keeps the 1200×630 social preview card, keeps city/niche drafts `noindex,nofollow`, skipped Meilisearch reindex, and passed live crawl with `warning_groups=0`.

For explicitly approved data-preserving hotfixes where the current ignored `public-data/tiktok` membership/counts must be preserved while static UI/page rendering is repaired, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-public-hotfix-from-export.ps1 -ReleaseName <release-name> -MeiliUrl /knowledge-search
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-public-vps.ps1 -ReleaseName <release-name> -SkipPackage -SkipReindex
```

This hotfix path copies the existing export, repairs public excerpt fields from already-public passages, validates the current safe public policy and text-boundary safety, verifies JSONL counts are preserved, rebuilds generated pages/static assets, and skips Meilisearch reindex unless passages or index settings changed.

## One-command deploy

Use this for normal VPS deploys:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-public-vps.ps1 -ReleaseName <release-name>
```

The script packages the release, uploads the zip, unpacks to a new release folder, switches the `current` symlink, reloads nginx after `nginx -t`, reindexes Meilisearch, and verifies the deployed path.

For data-changing TikTok/source refreshes, prefer the canonical release gate instead of calling deploy directly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\base2026-release-gate.ps1 `
  -ReleaseName <release-name> `
  -BatchSet <batch-set> `
  -RunAfterPolish `
  -LatestReadiness 3 `
  -Deploy
```

This runner prevents the common out-of-order failure: public text is exported before a reviewed topic/insight layer exists for the newest source. It also keeps the current-batch polish gate, publication boundary, metadata, export policy, package, deploy/reindex, live crawl, and mobile visual QA in one audited sequence.

## Server deploy shape

1. Upload release zip to `/tmp/<release-name>.zip`.
2. Unzip to `/var/www/base2026-knowledge/releases/<release-name>`.
3. Keep the browser pointed at `/knowledge-search`.
4. Ensure nginx proxies `/knowledge-search/multi-search` to Meilisearch and injects the public search-key Authorization header server-side.
5. Ensure nginx serves `/knowledge/static/` with immutable cache headers and gzip for CSS/JS/JSON/SVG assets.
6. Verify `web/static/documents.jsonl` exists.
7. Verify `web/methodology.html`, `web/opt-out.html`, `web/roadmap.html`, `web/privacy.html`, `web/source-policy.html`, and `web/support.html` exist.
8. Switch `/var/www/base2026-knowledge/current` symlink with `ln -sfnT` so the symlink target is replaced, not nested.
9. Run `nginx -t`.
10. Reload nginx.
11. Verify `/knowledge/`, `/knowledge/roadmap.html`, `/knowledge/privacy.html`, `/knowledge/source-policy.html`, `/knowledge/support.html`, `/knowledge/methodology.html`, `/knowledge/opt-out.html`, `/knowledge/static/documents.jsonl`, and `/knowledge-search/multi-search`.
12. Verify live compression/cache headers:

```bash
curl -I -H 'Accept-Encoding: gzip, br' https://aggressorbulkit.online/knowledge/static/styles.css
curl -I -H 'Accept-Encoding: gzip, br' https://aggressorbulkit.online/knowledge/static/meili.js
```

Both static asset checks should show `Content-Encoding: gzip`, `Vary: Accept-Encoding`, and a long-lived `Cache-Control`.

13. Reindex Meilisearch from the deployed release data when `passages.jsonl`, index settings, or topic fields changed.

Current server reindex command shape:

```bash
cd /var/www/base2026-knowledge/current
python3 scripts/meili-index-public.py \
  --data public-data/tiktok/chunks.jsonl \
  --url http://127.0.0.1:7700 \
  --index base2026_public_tiktok \
  --master-key "$(cat /var/www/base2026-knowledge/shared/.meili_master_key)"
```

## Rollback

Switch `current` symlink back to previous release, run `nginx -t`, reload nginx, verify `/knowledge/`.

## Forbidden

- do not overwrite WordPress root
- do not print or commit Meilisearch keys
- do not deploy private local source folders
