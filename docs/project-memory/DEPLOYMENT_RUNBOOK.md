# Deployment Runbook

## Current Cloudflare authority

For the live Base2026 domain, public Worker, private TikTok pipeline,
service-binding projection, D1 migrations, verification, and rollback, follow
`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md` first. The
VPS/nginx instructions below are retained for legacy rollback and historical
releases; they are not the active Base2026 search/publication path.

Never deploy the public Worker from a stale public clone. First reconcile the
live projection RPC module and migration state, then use the contract-compatible
public-before-private deployment order in the canonical manual.

Current Workers Static Assets release:

- Domain: `https://base2026.dev/`
- Public Worker: `f8781f4d-30fd-4d70-ab96-a4e8d718226a`
- Compatible immediate rollback: `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e`.
  It preserves member auth and Evidence Search but does not expose public MCP.
- Artifact tree SHA-256:
  `eb7538f97e322a88f87ec08578fd9477c3da4d13320dea1086bb4959362838ba`
- Canonical source repository: `https://github.com/offflinerpsy/base2026`
- Reviewed public source commit: `16884d148fa01da970e334396c17bcf4acc9429f`,
  merged through PR34 as `98bfb65efd5940e01ecff13e4095ad9442a53986`.
- Live release receipt:
  `HANDOFF_2026-09-01_PUBLIC_API_MCP_PRODUCTION_RELEASE.md`.

Before every public deploy, dry-run and live version readback must retain
`AUTH_DB`, all three member-auth secret names and `MEMBER_AUTH_ENABLED=true`.
Public MCP additionally requires `MCP_RATE_LIMIT`; absence or failure must
leave `/api/mcp` closed. Do not deploy a config that reconstructs only the
older four-binding public surface.

Always pass the exact reviewed candidate to Wrangler with `--assets`; the
ignored output path in the checked-in config is not an implicit release
selection. The current config is pinned to `base2026-enrichment-retirement-20260831-v2`;
verify that pin and the actual tree hash before every deploy. Rebuilt candidates
must exclude previous builder receipts and keep
the Workspace Project Story link on `/about`. `/sources/*` must remain
Worker-first so static and projected source routes share canonical redirects
and security headers. The editorial extension applied additive public migration
0004 only; it did not import or rewrite source-corpus tables. The guide extension
reuses those tables without a migration; `/topics/*` and guide sitemap are now
Worker-first. Source-catalog and guide responses must not be bypassed by assets.

For data-only original articles, follow `docs/BASE2026_EDITORIAL_PUBLISHING.md`:
prepare and semantically review an exact packet, use the existing authenticated
private client, inspect after uncertainty, and verify HTML/API/RSS/sitemap.
Never redeploy the site merely to add article text, and never write article
tables directly. A new illustration still requires an exact reviewed asset
release. Public/private Worker code deployments remain separately reviewed and
owned, in public-before-private contract order.

Maintained guides additionally follow
`docs/BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md`: exact source dependencies,
no-store public reads, no blog duplicate and repair through reviewed CAS.
First article and first guide acceptance-replays are complete; routine content
publishing must not repeat them. Both archive articles are also published;
never reuse their completed writes as release tests.

### Private release and rollback fence — 2026-08-31

Release57 deployed09:57:24 after additive migration0016 at09:55:59.
Diagnostic-only release58 deployed10:15:41.832;388 Worker/18 courier tests,
types/dry-run, health, no pending migration and45-binding parity passed.
Keep private deployment identifiers and exact operations in protected receipts.

Release57 is the diagnostic rollback. Do not restore56 unless a fresh owner
check proves zero active capture leases and no reserved/settling/uncertain
operations. Preserve0016 and its ledger; never force-clear ownership or drop
records to make rollback possible. Uncertain operations remain held, without
automatic refund/replay. Recovery covers evidenced pending media only, not
resurrection of withdrawn tuples. The10:16:53 record of19 browser/9 capture
operations settled with no owners is dated, not permanent rollback permission.
Cleanup pagination/starvation requires separate scope; no broader deletion.

Legacy VPS rollback path:

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

The current live release snapshot has 1,493 normal public cards, 199 provenance archive/noindex records, 122 private future-backlog sources, 1,692 public source records, 2,276 public passages, 2,396 insight cards, 1,873 public insight cards, 1,628 topics, and 18 creators. Normal incomplete cards = 0. Machine receipt: `.planning/tiktok-pipeline-v2/production-completeness-release-receipt-2026-07-10.json`. The current admission ledger is newer: 1,827 total with 135 future/private; its 13 additions have no public effect and must remain absent from every public artifact.

Historical pre-Source-Detail-V2 IndexNow closure for the 2026-07-10 completeness release: 1,734/1,734 then-current sitemap URLs passed the live 200/indexable/self-canonical gate and were accepted with HTTP 200; 62/62 previous-public/current-private URLs returned 404 and their deletion notification was accepted with HTTP 200; all 199 archive URLs were then live `noindex` and excluded. Receipt: `.planning/tiktok-pipeline-v2/indexnow-card-completeness-2026-07-10/indexnow-release-closure-receipt.json`. This historical sitemap state is superseded for Source Detail V2 by the explicit contract below: the same 199 public archive source-detail URLs are sitemap-included, while the current 135 future/private URLs are sitemap-excluded. IndexNow/reindex remains a separate explicit post-live decision.

The `base2026-api-nav-footer-r3-20260616` deploy changed generated HTML/navigation and the hotfix packaging contract only. It intentionally skipped Meilisearch reindex because public data and index fields did not change. The deploy fixed global `/knowledge/api.html` navigation in the search root, generated pages, mobile Base2026 nav, and footer.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-public-release.ps1 -ReleaseName <release-name>
```

Current public packages use reviewed public source text where policy allows. Latest deployed release: `base2026-identity-disclaimer-20260626` (identity/legal disclaimer hotfix: Base2026 is an independent experimental startup product created by Alex Yarosh and owned by Logic Crafts LLC, Kyrgyzstan; it is not a marketing agency or marketing-services offering). Public package/deploy scripts must not expose `-IncludeFullTranscripts` as a public shortcut and must not call `--auto-promote-insights`. Raw captions, raw ASR, media, private QA, and unreviewed transcripts stay private. Private/gated review exports should use `scripts/export-public-tiktok.py --out <ignored-private-dir>` directly and must not be deployed as the public `/knowledge/` release.

Latest data-preserving static hotfix: `base2026-bing-money-pages-r1-20260628`. It added the live source-backed `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/` page, preserves the live measurement, AI-ready documentation, and review sentiment pages, keeps AI visibility collection/social metadata complete, keeps the 1200×630 social preview card, keeps city/niche drafts `noindex,nofollow`, skipped Meilisearch reindex, and passed live crawl with `warning_groups=0`.

For explicitly approved data-preserving static releases, package first and deploy only the reviewed immutable ZIP. The deploy step requires the exact ZIP SHA-256 and candidate manifest; it never chooses them implicitly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-public-hotfix-from-export.ps1 `
  -ReleaseName <release-name> `
  -MeiliUrl /knowledge-search `
  -SourceDetailCandidate .planning/<approved-immutable-candidate> `
  -SourceAdmissionClosureReceipt .planning/<hash-bound-admission-closure-receipt.json>

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-public-vps.ps1 `
  -ReleaseName <release-name> `
  -ZipPath output/releases/<release-name>.zip `
  -ExpectedZipSha256 <approved-64-hex-sha256> `
  -CandidateManifest .planning/<approved-immutable-candidate>/candidate-manifest.json `
  -SkipPackage `
  -SkipReindex `
  -PlanOnly
```

Remove `-PlanOnly` only after an independent textual `DEPLOYMENT_GO` for those exact identifiers, verified VPS prerequisites, and Alex's explicit publication authorization. `-SkipReindex` is mandatory for this data-preserving static path; Meilisearch and IndexNow are separate release decisions.

This path copies the existing export, repairs public excerpt fields from already-public passages, validates the current safe public policy and text-boundary safety, verifies JSONL counts are preserved, overlays the approved immutable candidate, regenerates sitemaps with every `normal_public_card` and every public `provenance_archive_noindex` route present, keeps every `future_private_backlog` route absent, and skips Meilisearch reindex.

Source Detail V2 packages use schema `base2026.public-hotfix-from-export/v3`. The root manifest binds release name, candidate-manifest SHA, route-manifest SHA, current admission-ledger SHA, closure-receipt SHA, counts, and sitemap policy. The deploy wrapper validates that manifest and the exact ZIP locally even under `-PlanOnly`, then repeats required-file checks after VPS extraction. Required runtime files are the static `web/` and public-data files named in that manifest, including `web/sources/index.html`. There is no release-local Python app: public search remains the existing nginx proxy to Meilisearch. An in-package nginx config is neither required nor mutated because the wrapper validates the already-installed system config with `sudo nginx -t`.

## Deprecated unpinned deploy mode

Do not invoke `deploy-public-vps.ps1` with only a release name. The static deploy wrapper is fail-closed: `ExpectedZipSha256`, `CandidateManifest`, and `-SkipReindex` are mandatory, and release-boundary approval is attached to the exact ZIP/candidate identifiers.

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
