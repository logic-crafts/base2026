# Base2026 Source Detail V2 — Production Release Closure

Date: 2026-07-13

## Result

`DEPLOYMENT_GO` was executed after explicit owner authorization. The exact SHA-pinned static release is live and passed the integrated production gate. Rollback remained armed and was not required.

## Exact release

- Release: `base2026-source-detail-v2-admission1827-deploycontract-20260713-142944`
- ZIP: `output/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944.zip`
- ZIP SHA-256: `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`
- Previous target: `base2026-ai-solutions-shell-20260712-163556`
- Current target: `/var/www/base2026-knowledge/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944`
- Deploy completed: `2026-07-13T19:37:51Z`
- Deploy mode: exact package, `-SkipPackage -SkipReindex`, transactional symlink switch, automatic rollback on a red live gate
- WordPress root mutation: `false`

## Production verification

- Contract gate: `PASS`
- Exact HTTP 200 + byte-hash checks: `1,706`
- Rendered Source Detail routes: `1,692`
- Normal public/indexable routes: `1,493`
- Provenance archive routes: `199`, HTTP 200 with `noindex,follow`
- Future/private routes: `135`, HTTP 404 and sitemap-excluded
- Sitemap URLs: `1,933`, unique across 5 child sitemaps
- Expected/actual route digest: `932d9996c0c0560c2256a315b195f17787680937a8aefbd79eec5a81080cf6c5`
- Browser gate: `8/8 PASS` at 320, 390, 1280 and 1440; zero console, page or network failures
- Remote ZIP SHA read-back: exact match
- VPS current symlink read-back: exact release
- nginx config/runtime: valid and active

Local ignored receipts:

- `output/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944-live-evidence/deployment-receipt.json`
- `output/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944-live-evidence/gate-receipt.json`
- `output/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944-live-evidence/contract/report.json`
- `output/releases/base2026-source-detail-v2-admission1827-deploycontract-20260713-142944-live-evidence/browser/report.json`

## Search/indexation decision

Meilisearch reindex was intentionally skipped because this was a data-preserving static/template release: public search documents and index fields did not change.

IndexNow was submitted only for the `1,493` changed, live-gated, indexable Source Detail URLs. The `199` archive/noindex routes and `135` future/private/404 routes were excluded. The public key location matched the local key and the provider returned HTTP `200`.

Ignored receipt: `output/indexnow/source-detail-v2-20260713/receipt.json`.

## Rollback boundary

The previous release target remains recorded in the deployment receipt. The deploy wrapper would restore it automatically on any non-zero live gate. Because the exact live contract and browser gates passed, no rollback was executed.
