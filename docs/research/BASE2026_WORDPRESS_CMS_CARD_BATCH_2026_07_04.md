# Base2026 WordPress/CMS source-backed card batch — 2026-07-04

Status: private/local card batch. No public pages, public export, deployment, IndexNow, GSC/Bing request-indexing, outreach, or source publication was performed by this batch.

Generated at: `2026-07-04T12:30:13Z`

## Scope

- Parent vertical: `web_development`.
- Child vertical/category: `wordpress_cms`.
- Output shape: source-backed `insight_card_candidate` rows only.
- Explicit non-goal: no separate WordPress landing/topic/source pages in this pass.

## Batch summary

- Candidate cards: `12`
- Creators: `{'@iamdandavies': 10, '@joshuamaraney': 2}`
- Evidence precheck: `{'exact': 12}`
- Candidate JSONL: `.planning/claim-candidates-20260704-wordpress-cms-cards.jsonl`
- Review queue JSONL: `.planning/backfill-insight-cards-20260704-wordpress-cms.jsonl`

## Cards

| # | Creator | Source | Topic | Claim | Evidence match |
| ---: | --- | --- | --- | --- | --- |
| 1 | `@iamdandavies` | [`tiktok:iamdandavies:7655405261770870038`](https://www.tiktok.com/@iamdandavies/video/7655405261770870038) | WordPress update safety | Outdated WordPress core, plugins, and themes create security exposure; update after checking dashboard notices and taking a backup. | `exact` |
| 2 | `@iamdandavies` | [`tiktok:iamdandavies:7653138444624858390`](https://www.tiktok.com/@iamdandavies/video/7653138444624858390) | WordPress form email deliverability | WordPress contact forms should avoid default PHP mail when deliverability matters; configure SMTP instead. | `exact` |
| 3 | `@iamdandavies` | [`tiktok:iamdandavies:7652389271193570582`](https://www.tiktok.com/@iamdandavies/video/7652389271193570582) | WordPress transient cleanup | Deleting WordPress plugins can leave transient rows in wp_options; database cleanup can become a speed and maintenance card when backed up first. | `exact` |
| 4 | `@iamdandavies` | [`tiktok:iamdandavies:7650798286932053270`](https://www.tiktok.com/@iamdandavies/video/7650798286932053270) | WordPress update cadence nuance | Frequent WordPress and plugin updates are not automatically proof of insecurity; they can include features, compliance, bug fixes, compatibility work, and vulnerability patches. | `exact` |
| 5 | `@iamdandavies` | [`tiktok:iamdandavies:7649853023690312982`](https://www.tiktok.com/@iamdandavies/video/7649853023690312982) | Broken WordPress site triage | WordPress outage triage should first separate a site that is down from a site that is slow, because the fixes are different. | `exact` |
| 6 | `@iamdandavies` | [`tiktok:iamdandavies:7649439207634554134`](https://www.tiktok.com/@iamdandavies/video/7649439207634554134) | WordPress backup restore testing | WordPress backup claims are not enough; maintenance should verify off-site/off-server backups can actually restore the site. | `exact` |
| 7 | `@iamdandavies` | [`tiktok:iamdandavies:7651252900642999574`](https://www.tiktok.com/@iamdandavies/video/7651252900642999574) | AI-assisted WordPress CMS workflow | AI can speed up WordPress builds, but the creator still keeps WordPress as the client-facing CMS for content, SEO meta, and page updates. | `exact` |
| 8 | `@iamdandavies` | [`tiktok:iamdandavies:7650749738836331798`](https://www.tiktok.com/@iamdandavies/video/7650749738836331798) | WordPress backend versus custom Laravel backend | The creator returned from Laravel to WordPress because WordPress already provides a customizable admin backend for client content management. | `exact` |
| 9 | `@iamdandavies` | [`tiktok:iamdandavies:7650125230567935254`](https://www.tiktok.com/@iamdandavies/video/7650125230567935254) | WordPress CMS versus design quality | WordPress is the CMS engine, not the front-end design quality; professional-looking sites depend on design and build skill, not the platform label. | `exact` |
| 10 | `@iamdandavies` | [`tiktok:iamdandavies:7649339890156588310`](https://www.tiktok.com/@iamdandavies/video/7649339890156588310) | WordPress admin performance debugging | Temporary debugging plugins can be justified when they identify which plugin is slowing WordPress admin, as long as they are used for diagnosis. | `exact` |
| 11 | `@joshuamaraney` | [`tiktok:joshuamaraney:7628528677860461831`](https://www.tiktok.com/@joshuamaraney/video/7628528677860461831) | WordPress noindex setting QA | A WordPress site can disappear from Google if the Reading setting still discourages search engines from indexing it. | `exact` |
| 12 | `@joshuamaraney` | [`tiktok:joshuamaraney:7607861624908647700`](https://www.tiktok.com/@joshuamaraney/video/7607861624908647700) | WordPress plugin vulnerability risk | Outdated WordPress plugins can create vulnerabilities that let attackers into the system. | `exact` |

## Gate decision

- Source text review: passed for this card batch using public passages only.
- Deterministic evidence gate: passed: `12/12` exact evidence matches, `0` rejected, `0` needs review.
- Import gate: passed: `12` private `insight_card_candidate` rows imported into the local SQLite KB with `12` evidence rows.
- Review gate: passed: `12/12` candidates classified as `promotion_candidate`; report: `docs/research/BASE2026_WORDPRESS_CMS_CARD_REVIEW_REPORT_2026_07_04.md`.
- Cards-only internal release gate: passed by promoting the batch from `pending` to `reviewed`, not `approved`/public.
- Public release/indexation gate: held. No standalone WordPress pages, deploy, IndexNow, GSC/Bing request-indexing, outreach, or public source/transcript publication was performed.
- Publication-boundary check: `changed_files=163`, `forbidden=0`, `secret_findings=0`, `needs_review=5`; the 5 review items are pre-existing dirty-tree paths (`data/ai_visibility_pages_bing_batch04.json`, Alex site generator scripts, and temp GSC scripts), so this WordPress batch was not staged/committed.

## Execution artifacts

- Raw candidate batch: `.planning/claim-candidates-20260704-wordpress-cms-cards.jsonl`
- Verified candidate batch: `.planning/claim-candidates-20260704-wordpress-cms-cards.verified.jsonl`
- Evidence report: `.planning/evidence-verify-20260704.report.json`
- Review report JSON: `.planning/wordpress-cms-insight-cards-review-20260704.json`
- Review report Markdown: `docs/research/BASE2026_WORDPRESS_CMS_CARD_REVIEW_REPORT_2026_07_04.md`
- SQLite backups created before writes:
  - `12_knowledge-base/indexes/kb.sqlite.bak-claim-import-20260704-053258`
  - `12_knowledge-base/indexes/kb.sqlite.bak-promote-insights-20260704-053334`
