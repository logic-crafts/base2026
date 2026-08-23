# Current Handoff

## 2026-08-23 — Cloudflare-only pipeline live; canonical manual is authoritative

**Current gate: LIVE AND FAIL-CLOSED.** The scheduled TikTok runtime is
Cloudflare-only; the Mac adapter is disabled. The automatic lane admits only
explicitly eligible TikTok excerpt cards, keeps broad release off, and verifies
the exact public D1 projection. The verified snapshot has 2,136 public
documents, 1,557 videos, 33 applied projections, 44 projected cards, and zero
public full transcripts.

Start from
`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`. It supersedes
older pipeline architecture descriptions. The public GitHub source can be
behind the protected live Worker, so reconcile source, migrations, bindings,
versions, and D1 receipts before deploy. Next observation: the 2026-08-24
10:00 UTC daily discovery cycle.

## 2026-07-15 — Stitch V1 AI Recommends Solutions production release closed

**Current gate: COMPLETE.** Alex explicitly authorized production deploy in source message `224273`. PR #12 passed CodeQL and merged as `9a4670143acd615d0e832a855577b61367b89c4b`. Exact release `base2026-search-solutions-stitch-v1-preview-r3-20260715-094010`, ZIP SHA-256 `711b79b492bd4a70e38379878a39f5230f635dfa4458c08f079463122af2f6c7`, is active at `/var/www/base2026-knowledge/current`. Atomic deploy and exact live contract passed: `1706/1706` byte/status checks, `135/135` future/private 404, sitemap contract clean, Source Detail responsive browser gate `8/8`, and Solutions-specific live browser/interaction gate `24/24` at 1440/1280/390/320. Exact live hashes match the package for all six Solutions HTML routes plus CSS/JS (`8/8`). Manual live visual inspection passed. Rollback target is `base2026-search-solutions-security-20260714-193405`; rollback was not needed. Meilisearch, IndexNow, WordPress, corpus data and sitemap membership were deliberately unchanged. Canonical release record: `docs/project-memory/BASE2026_SOLUTIONS_STITCH_V1_PRODUCTION_RELEASE_2026_07_15.md`.

## 2026-07-14 — Search V1 corrective hardening and Sol/high review PASS; Git closure in progress

**Current gate: OPTION A RECORDED; CORRECTIVE LOCAL GATES PASS; FINAL SOL/HIGH REVIEW PASS; SCOPED GIT/CI CLOSURE AUTHORIZED.** Alex explicitly chose option A (`Продолжай по а`). Search V1 canonical and newly generated links use `/knowledge/?q=...`; the outbound `#search?...` prohibition applies to changed/new generation paths. The 4,183 byte-identical files inherited from the immutable Source Detail V2 baseline are grandfathered and may retain their 10,340 pre-existing outbound hash links until a separately verified family regeneration. Runtime compatibility still accepts an inbound legacy hash bookmark and immediately migrates it to the canonical query URL. Exact candidate remains `base2026-search-v1-derived-20260714-024003.zip` at SHA-256 `3261f235864a57c2c3f17f0ccd9588f24f888b21d5bf5c400ec089fe19311235`, derived reproducibly from baseline SHA-256 `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`, with `1,493 normal + 199 archive/noindex + 135 future/private/404 = 1,827`. The pre-hardening PASS is superseded. Final isolated `gpt-5.6-sol`/high read-only review session `019f5f81-056e-70e1-82b0-9d1cb7785566` returned `VERDICT PASS`, no blockers, and `SAFE_TO_COMMIT YES` for the exact nine-file scope. Canonical review record: `docs/project-memory/BASE2026_SEARCH_V1_INDEPENDENT_REVIEW.md`. Next: rerun final local gates on the documented diff, commit/push PR #10, require green CI/CodeQL, merge, and bind merged SHA to the frozen artifact. Production deployment remains separately authorization-gated. Any scope, manifest, or candidate-SHA drift reopens review. Do not re-export, reindex Meilisearch, submit IndexNow, mutate WordPress, or rewrite inherited baseline pages.

## 2026-07-13 — Source Detail V2 production release closed

**Current gate: COMPLETE.** Exact release `base2026-source-detail-v2-admission1827-deploycontract-20260713-142944` is live at ZIP SHA-256 `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`. Transactional deploy and exact live contract/browser QA passed; rollback was armed and not required. Production coverage is 1,493 normal/indexable, 199 archive/noindex, 135 future/private 404 and 1,933 sitemap URLs; browser QA passed 8/8 at 320/390/1280/1440. Meilisearch was intentionally unchanged. IndexNow accepted all 1,493 changed indexable Source Detail URLs with HTTP 200 and excluded archive/private routes. Canonical closure: `docs/project-memory/BASE2026_SOURCE_DETAIL_V2_PRODUCTION_RELEASE_2026_07_13.md`.

## Superseded pre-deploy packet — retained for audit history

- Exact release: `base2026-source-detail-v2-sitemapcontract-20260713-133158`.
- Exact ZIP: `output/releases/base2026-source-detail-v2-sitemapcontract-20260713-133158.zip`; SHA-256 `9b69b32042e62322395e546b10ad06543cdb039485457a81bc3bdd6596acc8bb`; fresh `unzip -t` exit `0` with no compressed-data errors.
- Immutable input: `.planning/release-candidate-a/candidate-manifest.json`; SHA-256 `92d5571f4d427a88be3646e303fc71ae62d76ef1c1c41120fb818e4b70587303`.
- Integrated local gate receipt: `.planning/source-detail-v2-sitemapcontract-20260713-133158-final/gate-receipt.json`; contract `PASS`, browser `PASS`, release/ZIP binding exact.
- Contract coverage: `1,493` normal public, `199` archive/noindex, `122` future/private 404; `1,706` exact byte/status checks; missing normal/archive sitemap URLs `0`; future/private sitemap leaks `0`.
- Browser/visual evidence: normal + archive across 320/390/1280/1440; `8/8` automated checks green, no console/page/network failures; manual exact-artifact review `PASS` at 390/1440.
- Fresh package validation: `ok=true`, staged `1,692/1,692`, future/private not emitted `122`, no HTML mismatches; report `.planning/source-detail-v2-sitemapcontract-20260713-133158-review-package-validation.json`, SHA-256 `7b9a29b58c1dc694781b899542ee604fac2602244d1cfec099924693e317c977`.
- Fresh regression/boundary checks: `51 passed in 0.82s`; publication boundary has no forbidden/needs-review/secret findings; `git diff --check` exit `0`.
- Frozen independent-review packet: `.planning/source-detail-v2-sitemapcontract-20260713-133158-independent-review-packet.md`; SHA-256 `411c0cfa42e6fa008359137cf68750dc865d1f6b4ed564fd225e89816633004a`.
- The background notification for `base2026-source-detail-v2-sitemapfix-20260713-171440` is historical evidence for a different artifact and must not be used as the verdict or SHA binding for this release.
- No deploy, upload, SSH/network mutation, symlink switch, nginx reload, Meilisearch reindex, IndexNow, git push or production action occurred.

Next exact action: obtain and verify an independent read-only Sol/high `DEPLOYMENT_GO`/`DEPLOYMENT_NO_GO` for the exact sitemap-contract ZIP and review packet. Even a GO is not deploy authorization; VPS readiness and explicit production authorization remain separate gates.

## 2026-07-13 — Source Detail V2 b26-3/b26-4 green; fresh independent deployment review required

## 2026-07-13 — Source Detail V2 immutable package built and validated; deployment permit pending

**Current gate: PACKAGE GO. DEPLOYMENT PENDING separate Sol/high permit. Production remains unchanged.**

- Immutable source candidate remains `.planning/release-candidate-a`; candidate-manifest SHA-256 is unchanged at `92d5571f4d427a88be3646e303fc71ae62d76ef1c1c41120fb818e4b70587303`.
- The first package attempt failed closed because PowerShell `Set-Content` appended a second terminal newline to every rewritten HTML file. Membership and all candidate asset hashes were already correct; the package validator rejected `1,692` HTML mismatches.
- Root cause was repaired in `scripts/package-public-hotfix-from-export.ps1` by replacing pipeline `Set-Content` with UTF-8-no-BOM `System.IO.File.WriteAllText`, preserving the candidate byte shape except for approved cache-bust query values. PowerShell parsing, `git diff --check`, and an exact representative normalized-HTML microtest passed.
- Successful release: `base2026-source-detail-v2-20260713-150938`.
- Release directory: `output/releases/base2026-source-detail-v2-20260713-150938`.
- ZIP: `output/releases/base2026-source-detail-v2-20260713-150938.zip`; SHA-256 `8bd0ecec9a396b1f89f50ca61522df1db708c4f79919eb945f715a84ad86904b`; `unzip -t` passed.
- Package receipt: `.planning/source-detail-v2-package-build-receipt.json`; SHA-256 `f93674f530fb521f96b8687e870c3d74a1355158b92006fc4e9541ded1145218`.
- Package validation: `.planning/source-detail-v2-release-package-validation.json`; SHA-256 `096e501d9a970d0aef22882fa25adb3a559a11f7e3bc83aa767bd0fe196bf3e1`; `ok: true`, `errors: []`, `html_mismatches: []`, staged `1,692/1,692`, future-private not emitted `122`, all six candidate assets exact.
- ZIP inventory contains `4,186` entries and all required package manifests, validation receipt, release text, sitemap, and `1,692` Source Detail HTML files.
- No deploy, symlink switch, nginx reload, Meilisearch reindex, IndexNow submission, push, or production mutation has occurred at this checkpoint.

Next exact action: issue a separate Sol/high deployment GO/NO-GO over this exact ZIP/hash, deploy atomically with `-SkipPackage -SkipReindex` only on complete GO, then run exact live normal/archive/future contract probes plus desktop/mobile visual QA and sitemap checks before any changed-URL indexation decision.

## 2026-07-13 — Admission and sitemap blockers closed

**Release: NO-GO until ownership/worktree scope and independent release permit are closed.**

- 13 post-freeze emitted source records were classified `future_private_backlog` because they have transcripts but zero reviewed/public claims.
- isolated public export PASS: `normal_public_card=1493`, `provenance_archive_noindex=199`, `future_private_backlog=135`, `source_records=1692`, `passages=2052`.
- all 13 new IDs are absent from all 8 public export artifacts; unit tests: `4 passed`; public corpus did not expand.
- decision record: `docs/project-memory/BASE2026_SOURCE_ADMISSION_CLOSURE_2026_07_13.md`.
- the reported sitemap omission was a false positive: `Framework` is title wording; canonical route is `solutions/content-refresh-prioritization.html`.
- isolated sitemap regeneration PASS: `1734` URLs / `5` files; canonical route appears exactly once locally and once live; noncanonical `...-framework.html` appears zero times.
- sitemap record: `docs/project-memory/BASE2026_SITEMAP_CLOSURE_2026_07_13.md`.
- no package, deploy, indexation request, or production mutation was performed.

## 2026-07-13 — Source Detail V2 shared-footer closure: isolated visual GO

The isolated Source Detail V2 footer parity gate is closed against current-live WordPress authority. No package, deploy, reindex, indexation or production mutation occurred.

- Final candidates: `.planning/source-detail-v2-full-candidate-20260713-footer-final-o` and `...-final-p`.
- Each candidate contains 1,712 files and represents 1,692 emitted normal/archive routes; 122 `future_private_backlog` routes remain absent/404.
- Both independent validators returned `valid: true`, `errors: []`.
- Byte determinism is `true`, differences `[]`; both candidate manifests have SHA-256 `92d5571f4d427a88be3646e303fc71ae62d76ef1c1c41120fb818e4b70587303`.
- Final strict matrix at 1440/1280/390/320: `passed: true`, `failures: []`; report `.planning/source-detail-v2-footer-visual-final2/report.json`, SHA-256 `b6977cf26ce7159348300a18fcb330742dd37e38845432a6c6019589bcf7d49c`.
- Manual comparison of all final normal/archive contact sheets against current-live is PASS at all four widths. CTA, social controls, disabled LinkedIn, nav rows, Cookie Preferences and copyright/bottom area match visually.
- Manual review caught and fixed one real mobile-only regression missed by the previous runner: a candidate-only separator above copyright. The runner now fail-closes on `bottomStyleEqual`; only O/P plus `visual-final2` are final evidence.
- Canonical review receipt: `.planning/source-detail-v2-footer-visual-final2/MANUAL_REVIEW.md`.

Gate split:
- **Source Detail V2 shared-footer visual gate: GO.**
- **Admission gate: GO.** The 13 post-freeze records were terminally classified private; isolated export and absence verification passed.
- **Sitemap gate: GO.** The reported `...-framework.html` omission was a noncanonical route-label false positive; the exact canonical route is present once locally and live.
- **Overall package/deploy gate: NO-GO until separate release blockers close.** Remaining blockers are clean ownership/publication-scope recapture and an independent release permit.

Next execution sequence: recapture scoped publication/Git ownership evidence, build an immutable scoped candidate, obtain independent go/no-go review, then package/deploy atomically only if every gate is green.

## 2026-07-12 — User-authorized full template rollout, fail-closed

The user explicitly authorized an overnight **local → production** Base2026 template rollout. This supersedes the earlier *planning-only* scope **only if every gate below passes**; it does not authorize shortcuts, manual edits to generated output, or a deploy with failing contract/visual/footer checks.

Decision routing:
- Sol/X High owns architecture, analytical conclusions, material visual/SEO/release decisions, and explicit go/no-go verdicts.
- Terra High executes the approved deterministic implementation and verification steps.

Required closure before package/deploy:
1. deterministic, manifest-driven generation — never a DOM/regex reskin of `web/static`;
2. per-route contracts preserve title/meta, canonical, robots, JSON-LD, H1, attribution, original links, public-state membership and future 404 absence;
3. isolated candidate and reproducibility validation pass for every family;
4. Playwright/browser checks across 1440, 1280, 390 and 320, including overflow, console/network errors, keyboard/focus, header and canonical responsive footer;
5. exact footer evidence confirms the compact Home v4 grid/CTA behavior rather than an uncontrolled wide replacement;
6. scoped public-safe Git package, deploy preflight, atomic deploy, and live verification pass.

Current gate state: Source Detail V2 full-family isolated build renders 1,692 200 routes and excludes 122 future-private routes. Initial independent validation failed closed on candidate asset-layout and typed semantic-normalization defects; these are being repaired and will be rerun before any integration. Production remains unchanged.

## 2026-07-12 — Sol/X High architecture verdict + Source Detail V2 isolated evidence

### Sol/X High decision (read-only independent review)

**Verdict: do not execute a broad site-wide migration or deploy yet.** The visual/template family route inventory and output mapping are not established for the other families; Source Detail is the only bounded family candidate. A broad rollout would violate the user-required evidence gate.

### Current isolated Source Detail V2 state

- Contract/provenance validator: `valid: true`, `errors: []`; expected states reconcile to `1,493 normal`, `199 archive`, `122 future/404`.
- Determinism: two clean candidates contain the same `1,712` files and identical SHA-256 hashes after removal of volatile timestamp from `candidate-manifest.json`.
- **Visual acceptance: BLOCKED.** Live-vs-candidate footer matrix at `1440`, `1280`, `390`, and `320` has no horizontal overflow, but candidate footer is materially taller than live (`+113/+98/+103/+60px` respectively); inner HTML signatures differ and candidate adds an unwanted 1px top border at 1280.
- Source: `.planning/source-detail-v2-live-candidate-footer-matrix.json`; candidates: `.planning/source-detail-v2-full-candidate-20260712-final` and `...-final-rerun`.

- 2026-07-13: fresh direct Playwright live authority corrected a stale cached geometry assumption: the current Home v4 footer is `1160px` wide with a `450px` lead at `1440/1280`; the main/header containment contract remains `1120px`. Portable footer must follow live footer geometry, not the old 1120/410 provisional matrix. Mobile live geometry is `20px` gutters and `22px/1.16` footer h2 at `390/320`.

### Required next bounded repair

Reconcile `scripts/alex_v4_static_shell.py` portable footer HTML/CSS with **current live WordPress DOM/CSS**, then rebuild two clean candidates, repeat independent validator, and repeat the four-viewport browser matrix. Do not integrate/deploy until parity passes and a Sol/X High visual acceptance review is captured.

### 2026-07-13 — bounded portable-footer repair in progress

Live Home was refetched directly from WordPress (`HTTP 200`, body classes include `ay-stitch-home-v3 ay-stitch-home-v4`, canonical `.ay-site-footer` exists). The stale portable shell differs from the live compact footer in three contract-relevant ways: 1160px instead of 1120px desktop container, 450px instead of approximately 410px lead grid, and stale CTA/section markup. The repair is confined to `scripts/alex_v4_static_shell.py`; it does not modify `web/static`, routes, production, package, deploy, sitemap, or index state. Next: clean dual builds, independent semantic/footer validation, then four viewport Playwright geometry + screenshots.

## 2026-07-12 Source Detail v2 local pilot — historical visual reference, superseded by full-family verification

Scope: Base2026 Source Detail redesign only. This is the replacement for the fully rejected first five-page V4 pilot; it is not Alex Personal Home work. The following local-pilot evidence is **historical and insufficient for a corpus migration or production change**; the current full-family candidate must re-pass all required gates in the top handoff section.

Current verified state:

- the rejected pilot remains architecture evidence only and must not be reused as the presentation layer;
- Source Detail v2 is rebuilt with new semantic body markup, not a CSS skin over the legacy composition;
- normal and provenance/archive records are two states of the same template;
- the body follows the accepted direction: arrival-aware breadcrumb/back link, one horizontal creator row, restrained source thesis, functional actions, editorial Source Text, compact Source Intelligence, hairline Questions disclosures, and a quiet archive provenance row;
- the static shell mirrors the canonical Alex Personal Home v4 header/footer contract; production has not been changed;
- automated QA passed at 1440, 1280, 390, and 320 widths for both states: HTTP 200, one H1, zero horizontal overflow, creator/avatar/H1 same row, expected actions and canonical footer copy present, zero orange/ochre surfaces, and no browser errors.

Artifacts:

- generator: `scripts/generate-base2026-source-detail-v2.py`;
- shared shell: `scripts/alex_v4_static_shell.py`;
- page CSS/JS: `scripts/base2026_source_detail_v2.css`, `scripts/base2026_source_detail_v2.js`;
- local output: `.planning/base2026-source-detail-v2/site/`;
- QA report/screenshots: `.planning/base2026-source-detail-v2/qa/`.

There is no unresolved clarification needed from Alex at this checkpoint. Exact next action: show the normal and archive local pilot for visual review. Only after explicit visual acceptance, expand to pathological fixtures and integrate the accepted template into the common generator. Do not mass-migrate or deploy before that acceptance.

## 2026-07-10 production source-card completeness release deployed and verified

Release `base2026-card-completeness-r1-20260710-173448` is active at `/var/www/base2026-knowledge/current`. It replaced `base2026-tiktok-public-20260703-1711` after explicit user approval.

Verified live state:

- **1,493 normal public cards; 0 normal cards without public Source Intelligence/Questions**;
- **199 provenance archive pages**, visibly labeled and `noindex`, excluded from normal documents, sitemap, and Meilisearch;
- **122 future private sources**, with no public page, normal document, sitemap URL, or Meilisearch membership;
- 2,052 Meilisearch chunks across 1,493 unique normal sources; task `487` succeeded;
- 1,734 unique sitemap URLs across 5 child sitemaps; representative normal included, archive/future excluded;
- live JSONL hashes match the release package; tests passed 45/45.

The user-reported `tiktok-video-7656864410052627714` URL now returns HTTP 404 and is absent from documents, sitemap, and Meilisearch. Its canonical state remains `future_private_backlog`.

Three fresh post-freeze QA-pass sources arrived during preflight without reviewed Source Intelligence. They were classified fail-closed as private future backlog, raising that state from 119 to 122 before packaging.

Production receipt: `.planning/tiktok-pipeline-v2/production-completeness-release-receipt-2026-07-10.json`.

Release report: `docs/project-memory/BASE2026_SOURCE_CARD_COMPLETENESS_PRODUCTION_RELEASE_2026_07_10.md`.

IndexNow closure was completed after live-gating the full current sitemap and the previous-to-current source diff:

- 1,734/1,734 current sitemap URLs were HTTP 200, indexable, and self-canonical;
- 199/199 provenance archive URLs were HTTP 200 + `noindex` and remained excluded from the submission;
- 62/62 URLs that were public in the previous release and are now private returned HTTP 404;
- the public key file was verified;
- the current/updated URL submission and the deleted-URL submission both returned HTTP 200.

IndexNow receipt: `.planning/tiktok-pipeline-v2/indexnow-card-completeness-2026-07-10/indexnow-release-closure-receipt.json`.

Git publication closure is complete. Four scoped release commits were pushed through PR #8; CodeQL Python, JavaScript/TypeScript, and aggregate checks passed; PR #8 merged into `main` as `0ca9f2a7f985be2d58e62c76432fa29fff82b4bd`; the remote feature branch was deleted; local and remote `main` were synchronized. Before push, the complete dirty worktree was classified; temporary GSC helpers were removed; private/generated ignored artifacts remained outside Git; publication boundary was 218/218 public-safe with 0 forbidden, 0 needs-review, and 0 secret findings. Full tests passed 45/45 and `git diff --check` was clean.

Post-merge live verification passed again for the normal/archive/future samples, 1,493 unique normal documents, 1,734 sitemap URLs, the AI Recommends Solutions hub, and the 2,052-chunk Meilisearch index. Receipt: `.planning/tiktok-pipeline-v2/final-post-merge-live-verification.json`.

## Superseded pre-release correction — production previously had 934 source-only normal cards

Before this release, a user-visible live check found 934/1,614 production cards without public Source Intelligence. That baseline is preserved in `.planning/tiktok-pipeline-v2/live-production-card-gap-recheck-2026-07-10.json`; it is no longer the current live state.

## 2026-07-10 Base2026 local source-card completeness gate closed

Scope: promote the 47 approved evidence-exact cards, enforce the 119/199 admission split, rebuild the canonical local export/generated site, and close the pre-redesign data gate without touching production.

Verified at `2026-07-10T16:26:28Z` from the canonical private admission ledger, rebuilt SQLite, canonical local JSONL/export, generated HTML, sitemap, unit tests, public-export policy, content-readiness gate, and the machine-readable closure receipt.

### Closed local state

- 1,811 unique admitted source IDs = **1,493 normal public cards + 199 provenance/archive noindex records + 119 private future-backlog records**.
- All 47 approved editorial source IDs were replayed into the KB and now have public Source Intelligence; missing = **0**.
- All 1,493 normal generated source pages are `index,follow` and contain both `Source Intelligence` and `Questions this source answers`.
- All 199 archive pages are `noindex,follow`, explicitly labeled `Provenance archive` / `Archive status`, have no Search Workspace CTA, and are absent from creator/topic listings and sitemaps.
- All 119 future-backlog sources remain in the private ledger/backlog and are absent from public JSONL, HTML, listings, and sitemaps.
- Canonical local export: 1,493 documents, 1,692 source records, 2,052 search chunks, 2,276 page passages, 2,396 insight cards, 1,873 public insight cards.
- Verification: 45/45 unit tests; public-export policy `ok=true`; content-readiness blocked=0; exact invariant receipt `all_checks_pass=true`; scoped `git diff --check` exit 0.

### Important implementation correction

The first rebuild exposed a real replay-schema mismatch: editorial apply rows stored claim copy as legacy `text`, while the KB loader read only `claim_text`. The producer now writes canonical `claim_text`, and the loader accepts both canonical and legacy rows. Regression tests cover this path.

### Decision and exact next action

**The pre-redesign local data/card gate is closed.** The next phase may start the frontend redesign against the frozen three-state admission contract; it must not reintroduce private future records or archive records into normal search/card/listing/sitemap surfaces. Production remains unchanged at the earlier live baseline. No deploy, Meilisearch reindex, external indexation, outreach, or commit was performed or authorized.

Receipts:

- `docs/project-memory/BASE2026_SOURCE_CARD_COMPLETENESS_GATE_2026_07_10.md`
- `.planning/tiktok-pipeline-v2/local-completeness-gate-receipt-2026-07-10.json`
- `12_knowledge-base/sources/tiktok/source-admission.jsonl`

## 2026-07-10 Base2026 TikTok intake / polish / insight pipeline checkpoint

Scope: Base2026 AI Recommends Solutions, monitored TikTok creators, new-video intake, transcript polish/QA, insight-card repair, and local-vs-live release state.

Verified at approximately `2026-07-10 07:15 EDT` / `14:15 +03` from live cron state, repo artifacts, Agency OS SQLite/handoffs, a fresh dry-run repair-queue build, and the public live manifest.

### Operational state

- Discovery/intake is healthy: `Base2026 TikTok Creator Auto-Refresh` runs every 2 hours and the watchdog reports `healthy=true`; no live parent/inner lock PID was present.
- The latest run (`20260710-054208`) scanned 19 creators / 245 candidate records, added 3 new video rows, transcribed 2, sent 1 to source review, then created 2 Markdown polish batches containing 11 pending videos.
- The autonomous chain stops after batch creation. The refresh cron is script-only and there is no scheduled agent consumer that writes `transcripts/polished/*.txt` plus `polished-qa/*.json`; its own log ends with `After Hermes writes polished outputs, run this script with -AfterPolish`.
- Today’s production summary shows 11 newly added rows, 10 transcript outputs, but 0 polished/QA outputs, 0 SQLite/public additions, 0 insight-cycle additions, and 0 static pages.
- Across the recent window there are 26 rows: 5 QA-pass, 10 source-review blockers, and 11 missing polish.

### Duplicate batch symptom

From July 9–10 there are 11 auto batch sets containing only 20 unique video IDs but 51 set memberships; 9 IDs repeat and the worst repeat appears in 6 sets. These are not 51 independent new videos: the cron keeps rebuilding batches around unresolved rows.

Current canonical polish queue is the latest set only:

- `12_knowledge-base/sources/tiktok/transcript-polish-batches/auto-creators-20260710-054208/batch-001.md`
- `12_knowledge-base/sources/tiktok/transcript-polish-batches/auto-creators-20260710-054208/batch-002.md`
- combined unique pending videos: **11**.

### Fresh repair/readiness counts

Fresh read-only `base2026-tiktok-repair-queue.py` result (`2026-07-10T11:15:57Z`):

| Queue / metric | Current |
|---|---:|
| sources | 1,651 |
| insight cards | 2,403 |
| sources without any insight | 175 |
| sources without public insight | 224 |
| `queued_needs_insight` | 155 |
| `queued_local_not_live` | 37 |
| `source_review_total` | 213 |
| source review: caption/manual-or-GPT lane | 112 |
| source review: retry ASR then QA | 78 |
| source review: cold hold/no local source | 23 |

Current public export policy and release-contract validators pass, but content readiness is **not clean**: 175 public-text source records are blocked because they lack reviewed topics/public insights.

### Local versus live

- Local manifest: `created_at=2026-07-09T13:34:49`, 1,651 documents, 1,832 public insight cards.
- Live manifest: `created_at=2026-07-03T17:10:36`, 1,614 documents, 1,077 public insight cards.
- Local is ahead by 37 source documents and 755 public-insight-card rows; none of this checkpoint authorizes deployment.

### Agency OS reconciliation

Agency OS doctor is healthy, but the latest B26 TikTok handoff there is from July 7 and current July 8–10 auto-polish batches are not represented as task cards. For this pipeline state, the repo is newer than the Agency OS/Plane mirror.

### Next exact safe sequence

1. Process only the latest 11-video batch set; ignore older duplicate auto batch directories.
2. Apply QA/source gates and run `hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet auto-creators-20260710-054208`.
3. Regenerate the repair queue and verify policy, release contract, and content readiness.
4. Continue bounded insight batches from the fresh `needs_insight=155` queue; separately route 112 caption-review, 78 ASR-retry, and 23 cold-hold rows.
5. Add a real scheduled agent polish consumer or equivalent queue worker before calling the 2-hour pipeline autonomous.
6. Do not deploy/publish/index/commit until the release gate is clean and Alex separately approves the data-changing release.

## 2026-07-08 Base2026 AI Recommends Solutions / TikTok insight-card repair checkpoint

Scope for this checkpoint: **Base2026 only** — AI Recommends Solutions / TikTok insight-layer / insight-card repair batches. Do **not** route this handoff into Alex personal-site, CMS, or WordPress lanes; those are separate historical contexts below and are not the active task in this chat.

Canonical sources checked for this checkpoint:

- repo queue summary: `.planning/insight-repair/repair-summary-latest.json` (`created_at=2026-07-07T23:57:14Z`, `dry_run=false`);
- repo queues: `.planning/insight-repair/needs-insight-latest.jsonl`, `source-review-latest.jsonl`, `local-not-live-latest.jsonl`;
- repo batch artifacts: `.planning/insight-repair/claim-candidates-gpt55-*20260707*`, strict-check reports, and promotion allowlists;
- Agency OS handoffs: `2026-07-07-tiktok-insight-repair-batches-1-4.md` and `2026-07-07-tiktok-insight-repair-batch-5.md`;
- verification commands run locally from the repo: `check-public-export-policy.py`, `validate-public-release-contract.py`, `check-public-content-readiness.py`.

Current status: **local repair applied; live deploy / production publish / outreach / indexation not executed from this checkpoint**.

Current repo-state metrics:

| Metric | Current |
|---|---:|
| `source_records` / sources | 1,639 |
| `passages` | 2,215 |
| `insight_cards` | 2,403 |
| `public_insight_cards` | 1,832 |
| `sources_with_any_insight` | 1,476 |
| `sources_with_public_insight` | 1,427 |
| `sources_without_any_insight` | 163 |
| `sources_without_public_insight` | 212 |
| queued `needs_insight` | 143 |
| queued `local_not_live` | 25 |
| `source_review_total` | 190 |

Batch status:

- Agency OS handoff confirms batches 1–4 added 56 local public insight cards and batch 5 added 12 more; no live deploy.
- Local artifact scan confirms batch 1 local-not-live promotion IDs exist for 20 cards (`first8` + `local-not-live-remaining12`).
- Batches 2–22 have strict-check artifacts with `ok=true`, `rejected=0`, total strict accepted rows/cards: **711**.
- Batch 23 has candidate/report artifacts but no strict-check artifact; treat it as **not accepted / not promoted** until strict check + review gate pass.

Remaining open debt:

- `needs-insight-latest.jsonl`: **143** rows still queued; top handles include `@build_in_public` (37), `@joshuamaraney` (20), `@darrenshawseo` (15), `@webhivedigital` (14), `@harrysandersseo` (10), `@tjrobertson52` (10), `@gobigsystems` (8), `@heytonyagency` (6).
- `source-review-latest.jsonl`: **190** rows; action split is `manual_or_gpt55_source_review_caption=103`, `retry_asr_then_qa_review=67`, `cold_hold_no_local_caption_or_audio=20`; QA split is `needs_review=139`, `missing_qa=51`.
- `local-not-live-latest.jsonl`: **25** rows still queued; top handles include `@gobigsystems` (9), `@build_in_public` (4), `@harrysandersseo` (4), `@heytonyagency` (3), `@neilpatel` (2).
- `check-public-content-readiness.py` still reports blocked source-only public-text records (`public_text_without_topics_or_public_insights`), so this is **not a release-ready state** even though export policy and release-contract validation are OK.

Next exact operator sequence for this chat:

1. Continue from `.planning/insight-repair/needs-insight-latest.jsonl`, not from old chat memory.
2. Finish or discard batch 23 only after strict checker + review report pass; do not treat generated candidates as promoted.
3. Work the remaining queues in this order: `local_not_live` 25 → `needs_insight` 143 → `source_review` 190.
4. After each accepted batch, rerun `scripts/base2026-check-insight-batch.py`, `scripts/check-public-export-policy.py public-data/tiktok`, `scripts/validate-public-release-contract.py --export-dir public-data/tiktok`, and `scripts/check-public-content-readiness.py`.
5. Do not deploy, publish, index, outreach, or commit until the release/readiness gate is clean and Alex separately approves a public/data-changing release.

## 2026-07-03 Base2026 TikTok pipeline restored

The July TikTok/video production gap is fixed and deployed. Root cause: post-polish batches contained legitimate QA `needs_review` outputs; the pipeline either stopped on those rows before `AfterPolish`, or left them marked `transcribed` so public export/readiness saw fresh source-only records. Added `scripts/tiktok-apply-qa-gates.py`, wired it into `scripts/hermes-tiktok-refresh.ps1 -AfterPolish -BatchSet ...`, and patched `scripts/base2026-release-gate.ps1 -RunAfterPolish` so mixed batches can proceed only after non-pass rows are gated private.

Live release: `base2026-tiktok-fresh-qa-gated-20260703`. Counts in the deployed export: 1,609 source records, 2,183 passages, 1,645 insight cards, 1,074 public insight cards, 1,535 topics. Meilisearch reindex: `indexed=2183`, task `479`. Live smoke passed for `/knowledge/`, fresh pages `tiktok-video-7657320786566450445`, `tiktok-video-7657320834268204301`, `tiktok-video-7657749901186583816`; held `needs_review` row `tiktok-video-7658094847831723278` returns 404.

Next safe action: keep 29 recent `needs_source_review` rows private until source/audio review. For the next data-changing TikTok release, use `base2026-release-gate.ps1 -RunAfterPolish -LatestReadiness 3`; the QA gate must run before SQLite rebuild/export. Before any Git commit, stage only public-safe source/docs changes from the large existing dirty tree.

## 2026-06-26 Base2026 night-shift status

The overnight shift created, deployed, and verified two indexable source-backed AI visibility pages: `/knowledge/measuring-ai-visibility-without-query-click-data/` and `/knowledge/ai-ready-business-documentation-for-service-pages/`. Evidence stack: official Google Search Central docs plus reviewed Base2026 TikTok insight cards. Live release: `base2026-ai-ready-documentation-page-20260626`. No raw transcripts were published, no outreach/registration/paid actions were executed, and Meilisearch reindex was skipped because public passage data did not change.

Verification: both live pages return `200`, each has one H1, `index,follow`, canonical URL, complete OG/X metadata, and the 1200×630 `/knowledge/static/assets/base2026-ai-visibility-card.png` preview image. Sample city/niche draft remains `noindex,nofollow`. Live sitemap index has 5 child sitemaps / 1,621 URLs; child `base2026-001.xml` includes both new pages and excludes the noindex city draft. `node scripts/live-seo-crawl-gate.mjs` passed with 500 crawled pages, 0 bad link-contracts, 0 crawled error pages, and `warning_groups=0`.

Next action: use the live documentation page and measurement page as the first share targets for DEV.to/LinkedIn/Product Hunt prep. If doing GSC work, inspect/submit only the live documentation page, measurement page, AI visibility collection, and other strong indexable hubs after manual review. Keep California city/niche pages noindex until each has unique local evidence.

# Current Handoff

Last updated: 2026-06-24

Purpose: this is the compact resume file for Base2026. Read this after `AGENTS.md`, then read only the referenced files needed for the next edit. Do not rehydrate the full project memory unless this file conflicts with repo state.

## Anti-Loop Resume Protocol

Required resume order:

1. Read `AGENTS.md`.
2. Read this file.
3. Read `docs/project-memory/LAUNCH_COMMAND_CENTER.md`.
4. Read `docs/project-memory/PIPELINE_ERROR_LEDGER.md` only for intake/deploy/release work.
5. Run `git status --short --branch --untracked-files=no` or a similarly bounded status check.
6. Read only the task-specific source/runbook files named in the handoff or command center.

Do not reread the full project-memory bundle unless one of these is true:

- this file conflicts with current repo state;
- the task explicitly touches deployment, publication boundary, data sources, or visual system contracts;
- the next action is unclear after reading this file and the command center;
- the user asks for a full audit/restart.

Generated `web/static/**`, `public-data/**`, `output/**`, `.planning/**`, local DBs, media, logs, and private review archives are not context material by default.

## Active Goal

Keep Base2026 launch work stable and reproducible: public UI fixes, SEO/GSC work, TikTok/source refresh, deploy, Meilisearch reindex, and GitHub preparation must run through bounded checklists and repo memory instead of ad hoc chat memory.

## Current Branch And Release State

- Branch: `codex/base2026-launch-next`; pushed to GitHub and fast-forwarded into GitHub `main` on 2026-06-19.
- Current live release: `base2026-ai-ready-documentation-page-20260626`.
- Previous pending traffic package `base2026-traffic-architecture-ay59-20260624` was superseded for Base2026 static deploy purposes by the night-shift AI visibility hotfix; Alex/WordPress-side traffic architecture work may still need separate `geo` repo deploy/import if not already handled.
- Current live export: 1,512 source records, 2,063 passages, 1,637 insight cards, 1,066 public insight cards, 1,528 topics, 1,014 public topics, 10 creators.
- Current policy: `include_full_transcripts=false`.
- Current Meilisearch index: `base2026_public_tiktok`, 2,063 public passages.
- Latest live QA: ay58 deploy passed newest-source readiness, live SEO crawl gate (500 crawled pages, 0 bad link-contracts, 0 crawled error pages), and mobile visual QA rerun (78 checks, 0 failures). Direct live smoke confirmed all seven newly Alex-approved source pages return 200.

## What Was Just Done

- 2026-06-24 Base2026 to Alex traffic architecture source pass: added `docs/public-pages/09_APPLY_RESEARCH.md`, generated `web/static/apply-research.html`, added Apply links to Base2026 nav/footer/search-root/info/public page templates, and patched packaging so the page ships. Alex conversion-layer work was implemented in the sibling `geo` repo generator/theme: four money pages, service/audit proof bands, theme footer/submenu, and reciprocal Base2026 proof links. Created `docs/project-memory/GSC_READY_TRAFFIC_ACTION_SET_2026_06_24.md`. Packaged `base2026-traffic-architecture-ay59-20260624` successfully with public counts preserved and sitemap now at 1,614 URLs. Deploy was blocked only by the current sandbox: live domain DNS failed locally and SSH to `geo` returned `Operation not permitted`.
- 2026-06-24 ay58 remaining Alex-approved source review release: Alex approved list items 15, 14, 13, 12, 11, 10, and 9 from the remaining fresh private queue. Created `.planning/source-review-approval-alex-20260624-remaining-nums-15-14-13-12-11-10-9.json`, moved 7 QA JSON files to `pass`, cleared 7 `videos.csv` rows back to `transcribed` / `source_review_pass` with backup `.planning/backups/videos-before-source-review-clear-20260624-091514.csv`, and added two exact-evidence Source Intelligence cards for newest-source blockers: `@ray_fu` / `tiktok-video-7654808550417468703` under `Multi-perspective AI research prompts` and `@gobigsystems` / `tiktok-video-7654341038856817933` under `Competitor Google Ads offer research`. Deployed `base2026-source-review-alex-approved-remaining-ay58-20260624`, reindexed Meilisearch task `423`, live SEO crawl passed, an initial mobile QA had one transient `ERR_CONNECTION_RESET`, and the rerun passed 78/0. Eight fresh QA-needs-review rows plus the ASR-too-little row remain private.
- 2026-06-24 ay57 Alex-approved source review release: Alex approved list items 3, 4, 6, 7, 8, 9, 10, and 13 from the fresh private queue. Created an explicit review manifest, moved 8 QA JSON files to `pass`, cleared 8 `videos.csv` rows back to `transcribed` / `source_review_pass`, rebuilt/exported, added one exact-evidence `@darrenshawseo` Source Intelligence card for `AI review sentiment persistence` when readiness blocked the newest source, deployed `base2026-source-review-alex-approved-ay57-20260624`, reindexed Meilisearch task `419`, and passed live SEO crawl plus full mobile visual QA. 15 fresh QA-needs-review rows plus the ASR-too-little row remained private before ay58.
- 2026-06-24 ay56 fresh TikTok production pipeline: applied 45 discovered recent TikTok candidates from the existing 10 configured creators with private backup, processed only that bounded queue with `-SkipInventory`, generated 44 usable transcripts, polished them through GPT-5.5, shipped only the 21 QA-pass rows, held 23 QA-needs-review rows plus 1 ASR-too-little row private, added 3 exact-evidence Source Intelligence cards to clear newest-source readiness, deployed `base2026-fresh-tiktok-pipeline-ay56-20260624`, reindexed Meilisearch task `415`, and passed live SEO crawl plus full mobile visual QA.

- 2026-06-23 ay55 creator-avatar hotfix: live `/knowledge/` smoke found 404s for `harrysandersseo.jpeg`, `gobigsystems.jpeg`, and `iamdandavies.jpeg`; fetched stable TikTok avatar assets, regenerated the public export so avatar URLs propagate through chunks/search data, patched the hotfix packager optional static-file fallback, deployed `base2026-creator-avatar-assets-ay55-20260623`, reindexed Meilisearch task `407`, and verified desktop/tablet Base2026 visual QA 14/14 with 0 failures.

- 2026-06-23 indexation foundation: WordPress theme now removes category/tag taxonomies from WP sitemaps and emits `noindex,follow` on category/tag/date archives to keep `/category/uncategorized/` out of index strategy.
- 2026-06-23 Base2026 crawl cleanup: generated search links now target `/knowledge/` and `#search?...` hash state instead of crawlable `/knowledge/index.html?...` query routes; static `meili.html` and runtime `meili.js` understand the hash route; regenerated temp pages had 0 `index.html?` links and 0 `./index.html`/`../index.html` search links.
- 2026-06-23 SEO structure audit: live WordPress/Base2026 H1-H3/canonical/sitemap crawl saved to `docs/project-memory/SEO_STRUCTURE_AUDIT_2026-06-23.md`; generator now inserts H2 list headings before Base2026 index card H3 grids so topics/creators/sources index pages have clean H1→H2→H3 structure.
- 2026-06-23 footer alignment guard: WordPress theme and Base2026 CSS now keep footer CTA buttons in one row on mobile instead of stacking into multiple rows; local Playwright CSS-injection check at 390px showed one row.
- Processed the AI Recommends Solutions creator pass for `@heytonyagency`, `@iamdandavies`, `@harrysandersseo`, `@ray_fu`, and `@gobigsystems`.
- Ran `scripts/social-discover.py` into ignored private JSONL: 200 discovered source records across 10 configured TikTok creators, 0 failures.
- Ran importer dry-run/apply into private local `videos.csv`: 100 new candidate rows added and safe missing metadata updated with an ignored backup.
- Ran Hermes refresh with `hermes-polish-20260618-ai-recommends`: 100 selected captions, 77 transcribed/polished, 23 `needs_asr`, 0 failed.
- Ran GPT polish and QA: 30 passed, 47 `needs_review`, 0 failed.
- Gated 47 QA-needs-review rows as `needs_source_review`; they were not allowed into public release.
- Added one strict exact-evidence reviewed public insight for `@iamdandavies` / `tiktok-video-7652708771701067030` after newest-source readiness correctly blocked a source-only row.
- Fixed `scripts/hermes-tiktok-refresh.ps1 -AfterPolish` so it skips inventory/caption intake and cannot expand `videos.csv` during release packaging.
- Ran `base2026-ai-recommends-readiness-fix-ay44-20260619` through package, deploy, Meilisearch reindex, live SEO crawl, and mobile QA.
- Before ay44, ay43 briefly packaged/deployed but an extended `--latest 3` readiness check caught two fresh `@gobigsystems` source-only pages. ay44 fixed the root cause by adding two strict exact-evidence reviewed Source Intelligence cards, then reran the full release gate with `-LatestReadiness 3`.
- Retried the audio-backed source-review queue and deployed `base2026-asr-gobig-pipeline-ay45-20260619`: one QA-pass `@gobigsystems` ASR-recovered source shipped publicly, 13 weak/no-speech ASR rows stayed private, Meilisearch reindexed 1,980 public passages, live SEO crawl passed, and the mobile visual QA rerun passed 78/0.
- Deployed `base2026-gobig-readiness-card-ay46-20260619` after newest-source readiness found one ay45 source-only `@gobigsystems` row; ay46 adds one strict exact-evidence Source Intelligence card for `Google Business Profile Categories` and keeps the remaining source-review backlog gated.
- Mechanically cleaned twenty-one local-caption source-review rows across ay47-ay53, approved them through `scripts/tiktok-qa-review-apply.py`, cleared only those explicit QA-pass rows back to `transcribed` with `scripts/tiktok-clear-reviewed-source-rows.py`, and deployed `base2026-source-review-local-caption-ay53-20260619` through the canonical release gate. The current private gated queue is 36 rows: 21 local-caption review rows, 13 audio-backed too-little/no-speech rows, and 2 rows with no usable local caption/audio. Adjacent rows with unresolved entity/product/model wording or visual/source dependence remain private because they need source verification before publication.
- Fixed and deployed `base2026-source-intelligence-contract-ay54-20260619` after the live `@darrenshawseo` source `tiktok-video-7652384458804432136` showed no Source Intelligence and rendered invalid "Questions this source answers" from Source Text. The generator now renders source Q&A only from reviewed Source Intelligence cards, and that source has a reviewed `Local SEO service-area rankings` card.

## Verification So Far

- Traffic architecture package verification passed: Base Python syntax check with `PYTHONPYCACHEPREFIX=/private/tmp/base2026-pycache`, `git diff --check`, `python3 scripts/audit-publication-boundary.py`, public release contract, and `pwsh ./scripts/package-public-hotfix-from-export.ps1 -ReleaseName base2026-traffic-architecture-ay59-20260624 -SourceExportRoot ./public-data/tiktok -MeiliUrl /knowledge-search`.
- New `apply-research.html` release output has canonical `https://aggressorbulkit.online/knowledge/apply-research.html`, `robots index,follow`, one H1, and links to Alex audit/services/pricing plus Base search.
- Targeted grep over new Base bridge/search-root assets returned no matches for Telegram, Reddit, YouTube, or Google Business Profile.
- `git diff --check` passed.
- `python3 scripts/audit-publication-boundary.py` passed with forbidden 0, needs_review 0, secret_findings 0.
- `python3 scripts/validate-github-metadata.py` passed.
- `python3 scripts/check-public-export-policy.py public-data/tiktok` passed.
- `python3 scripts/validate-public-release-contract.py --export-dir public-data/tiktok --baseline-export-dir public-data/tiktok --enforce-count-floor` passed.
- `pwsh ./scripts/base2026-release-gate.ps1 -Help` exits without running intake/deploy.
- `pwsh ./scripts/hermes-tiktok-refresh.ps1 -Help` exits without running inventory/intake.
- Phase 1/2 verification passed: `scripts/base2026-worker.py doctor` reports required/optional capabilities, TikTok discovery smoke wrote 15 private JSONL rows across 5 creators via `tiktok_yt_dlp_flat_playlist`, Instagram missing-adapter state is explicit, `.planning/` outputs are ignored, and `12_knowledge-base/sources/tiktok/videos.csv` hash stayed unchanged.
- Phase 3 verification passed: importer dry-run found 15 TikTok candidates; apply added 1 new queued recent source (`7652732487843581206`) and safely filled missing metadata for 14 existing rows; a post-apply dry run showed 0 new rows and 0 updates; backup is under ignored `.planning/backups/`.
- `scripts/hermes-tiktok-refresh.ps1 -CheckOnly` is now truly read-only. It runs social discovery plus importer dry-run, then prints current queue state. A hash check around `-CheckOnly -PlaylistEnd 3` proved `videos.csv` did not change.
- ay45 release gate passed package and deploy lanes: `-LatestReadiness 3`, publication boundary, GitHub metadata, public export policy, public release contract, VPS deploy, Meilisearch reindex, live SEO crawl, and mobile visual QA rerun.
- ay54 Source Intelligence contract release is live: symlink points to `base2026-source-intelligence-contract-ay54-20260619`; public export policy, release contract, newest-source readiness, live SEO crawl gate, direct live URL smoke, and mobile visual QA pass.
- ay44 live smoke verified `/knowledge/`, live manifest counts, and the two `@gobigsystems` source pages `tiktok-video-7652081880103275789` and `tiktok-video-7652520714678832398` with `Source Intelligence`.
- Final repo gates after the memory update passed: `git diff --check`, publication-boundary audit, GitHub metadata validation, public export policy, public release contract, and newest-source readiness.

## Open Loops

- The Base2026 static night-shift package is already live as `base2026-ai-ready-documentation-page-20260626`; do not redeploy the superseded ay59 or measurement-only Base2026 static packages over it.
- Alex/WordPress-side traffic architecture work from the sibling `geo` repo may still need separate deploy/import if it was not already handled there.
- GSC individual URL submissions remain manual-only. Inspect/submit only the live documentation page, live measurement page, AI visibility collection, and strong existing hubs after manual review. Do not submit noindex city/niche drafts.
- Git commit/staging is not done for the current large working tree. Before any commit, apply the publication boundary: do not stage generated release archives, `public-data`, `.planning`, `output`, local DBs, logs, raw captions, ASR, media, tokens, or private review archives.
- Historical source/audio verification debt remains gated; do not bulk-pass held rows.
- Future data-changing TikTok/source releases must use `scripts/base2026-release-gate.ps1 -LatestReadiness 3`.

## Exact Next Safe Action

1. Use `/knowledge/ai-ready-business-documentation-for-service-pages/` and `/knowledge/measuring-ai-visibility-without-query-click-data/` as the first public share targets for DEV.to/LinkedIn/Product Hunt prep.
2. If doing GSC work, inspect the live documentation page, measurement page, and AI visibility collection first; keep city/niche drafts out of GSC until each has unique local evidence and passes duplicate/doorway QA.
3. If Alex wants the conversion-layer bridge fully live, verify/deploy the sibling `geo` repo WordPress changes separately and run live URL/crawl/schema checks there.
4. If committing this Base2026 work, stage only public-safe source/docs/generator changes after `git diff --check`, publication-boundary audit, and manual generated-artifact review.
5. If the user gives new creators, add them to the ignored local creator/intake config, run social discovery, dry-run the importer, apply only clean TikTok candidates, then process them through `scripts/base2026-release-gate.ps1 -LatestReadiness 3`.
