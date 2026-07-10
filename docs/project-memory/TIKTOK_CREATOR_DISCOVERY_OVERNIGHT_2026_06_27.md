# TikTok Creator Discovery — Overnight 2026-06-27

## Scope

Autonomous overnight pass for Base2026: find additional TikTok creators/accounts covering marketing, growth, SEO, AI search, paid ads, funnels, and local-business marketing. Only profiles with verifiable >=50k followers were allowed into the approved local intake queue.

## Existing config checked

- `config/tiktok-intake-queue.local.json`
- `scripts/hermes-tiktok-refresh.ps1`
- `scripts/import-social-discovery-to-tiktok-csv.py`
- `docs/project-memory/DATA_SOURCES.md`

Existing creators were preserved.

## Approved and added to local intake queue

All follower counts below were verified from TikTok profile JSON during the run and copied into queue notes.

| Handle | Profile | Follower evidence | Fit | Base2026 reason | Risk / notes |
| --- | --- | --- | --- | --- | --- |
| `@neilpatel` | https://www.tiktok.com/@neilpatel | 294.5K followers | Digital marketing, SEO, AI search | Broad SEO/GEO marketing education source with high public visibility. | Generalist/high-volume creator; only reviewed, evidence-backed rows should publish. |
| `@willfrancis24` | https://www.tiktok.com/@willfrancis24 | 219K followers | AI + digital marketing | Useful for AI-marketing/operator workflow topics. | Some content may be creator/social-media tactical rather than SEO; gate by topic. |
| `@samdespo` | https://www.tiktok.com/@samdespo | 716K followers | AI, marketing, paid ads agency | Strong AI/marketing and paid-growth overlap. | Some content may be offer/agency-promo heavy; keep weak rows private. |
| `@keenyakelly` | https://www.tiktok.com/@keenyakelly | 514.2K followers | TikTok monetization/growth | Useful for creator-growth and short-form funnel patterns. | Not SEO-specific; publish only strategy/evidence rows with clear Base2026 relevance. |
| `@jera.bean` | https://www.tiktok.com/@jera.bean | 1.5M followers | TikTok/content growth strategy | High-signal short-form content strategy source. | Recent imported rows were mostly gated/out-of-scope; keep strict topical filter. |
| `@keeansocial` | https://www.tiktok.com/@keeansocial | 119.9K followers | Short-form content marketing strategy | Useful for content distribution/creative testing patterns. | Imported rows were older/out-of-scope; do not force-publish. |
| `@pulpdigitalagency` | https://www.tiktok.com/@pulpdigitalagency | 66.5K followers | Paid ads, creative, ecommerce growth | Small enough to be tactical; overlaps paid ads/funnels. | Needs careful evidence review. |
| `@tiktokforbusiness` | https://www.tiktok.com/@tiktokforbusiness | 1.5M followers | Official business/ads/growth education | Official TikTok business education source; good for platform ad/product guidance. | Official/platform source rather than independent creator; label accordingly. |
| `@tiktok_small_business` | https://www.tiktok.com/@tiktok_small_business | 801.2K followers | Official small-business marketing education | Small-business marketing and local-business-adjacent examples. | Official/platform source; publish only reviewed generalizable lessons. |

## Not approved / pending

No `unable_to_verify` profile was added to `config/tiktok-intake-queue.local.json`. Search results that did not expose a reliable follower count or did not produce enough relevant/fresh evidence were left out rather than guessed.

## Intake / processing result

- Approved sources added to local queue: 9.
- Local video rows for the new approved sources: 45.
- Publishable/pass batch: 17 transcribed rows, 17 clean files, 17 polished files, 0 missing polished, 0 `needs_review`.
- Private holds: 24 rows remain `needs_source_review` / `source_review_required_after_polish_qa`.
- Out-of-scope/old: 5 rows marked `out_of_scope_old`.
- Public export after rebuild: 1,542 source records, 2,096 passages, 1,641 insight cards, 1,070 public insight cards, 1,531 topics, 1,017 public topics.

## Release / gates

Release name: `base2026-overnight-marketing-creators-20260626`.

Gates passed:

- Current-batch polish status: 17 clean/polished/pass rows; 0 missing; 0 `needs_review`.
- Public content readiness: 0 blockers after adding strict reviewed evidence card `claim-overnight-f8ba1bfbc18eab4488ca` for `@gobigsystems` local Google Ads negative-keyword guidance.
- Publication boundary: `needs_review=0`, `forbidden=0`, `secret_findings=0`.
- Public release contract: `ok=true`, `violation_count=0`.
- Deploy/reindex: VPS current release `/var/www/base2026-knowledge/releases/base2026-overnight-marketing-creators-20260626`; Meilisearch task `447`, 2,096 passages indexed.
- Live SEO crawl gate: pass, 500 crawled pages, 1,661 sitemap URLs, 0 bad link-contracts, 0 crawled error pages, `warning_groups=0`.
- Mobile visual QA: 78 results, 0 failures.

## Next action

Review the 24 private source-review holds one by one before clearing any additional rows. Keep future candidates out of approved config unless follower count is verifiable and topical fit is clear.
