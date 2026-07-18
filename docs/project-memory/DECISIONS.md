# Decisions

## 2026-07-17 — Source-to-Solution discovery requires an exact reviewed evidence edge

Decision: Base2026 may expose a Source-to-Solution path only when an explicitly allowlisted Solution contains an exact reviewed `source_id` + `claim_id` evidence tuple that resolves to an admitted normal-public Source route. Topic similarity, keyword overlap, creator authority, or author opinion alone must not create the edge. The UI must label the material as a reviewed creator signal and keep it separate from Base2026 synthesis and authoritative verification.

Decision: Base product activation uses only the master event IDs `product_search_submitted`, `source_opened`, `evidence_actioned`, and `solution_opened`. `research_bridge_clicked` is an optional assist, not a service conversion. Events require affirmative stored analytics consent, accept only declared properties, and must not contain raw query/filter text, PII, full URLs/referrers, private source IDs, or private data. A rendered Apply Research page does not equal a request submission.

Reason: Base2026 must remain a useful independent research product rather than a disguised agency landing page. Exact evidence edges make the research-to-decision path auditable; the separate optional bridge permits business-specific diagnosis without overstating creator claims or contaminating product activation with service funnel metrics.

## 2026-07-17 — Public manifests are allowlisted and sitemap admission excludes noindex archives

Decision: Base2026 public dataset manifests use `base2026.public-dataset-manifest/v1` and may contain only declared public fields. Machine-local source-ledger and database paths are forbidden. The AI visibility page manifest uses `base2026.public-page-manifest/v1` and stores normalized paths relative to the release `web/` root. Recursive public-manifest validation reports only a JSON pointer and stable reason code, never a rejected value.

Decision: sitemap membership is the exact union of approved indexable Source Detail routes and a versioned static-route allowlist. Every admitted page must return a valid local file, be indexable, and have exactly one self-canonical. `provenance_archive_noindex` and `future_private_backlog` routes are excluded. For the immutable R6 Phase 0 preview this is 1,493 normal Source Detail + 241 frozen non-source = 1,734 URLs; 199 archive/noindex and 135 future/private routes are excluded.

Reason: noindex archive URLs cannot satisfy the sitemap indexability contract, and permissive filesystem crawling cannot prove route admission. Exact versioned inputs make omissions, additions, canonical drift and local-path leakage fail closed. The frozen 241-route R6 cohort is a migration control plane, not owner approval for future public SEO changes.

## 2026-07-14 — Search V1 uses canonical query URLs with a grandfathered immutable legacy baseline

Decision: Base2026 Search V1 canonical and newly generated discovery links use `/knowledge/?q=...` plus explicit query parameters. The outbound `#search?...` prohibition applies to Search V1 changed paths and to all new or regenerated generation paths. The immutable Source Detail V2 baseline is grandfathered: its 4,183 unchanged files may retain their 10,340 inherited outbound hash-search links until those page families are deliberately regenerated under a separately verified release. Runtime code must continue accepting an inbound `#search?...` bookmark and immediately migrate it to the canonical query URL with `history.replaceState`.

Reason: the exact Search V1 derivative changes only the search shell/assets and compatibility aliases while preserving 4,183 baseline files byte-for-byte. Rewriting every inherited link now would silently turn a bounded search-shell release into a thousands-of-pages corpus migration, invalidate the exact candidate SHA, and require full semantic, responsive, sitemap, and release revalidation. Grandfathering the immutable baseline preserves provenance and release safety without emitting any new legacy links.

Execution authorization: Alex chose option A (`Продолжай по а`). After corrective Search-runtime hardening, the exact verified candidate is `base2026-search-v1-derived-20260714-024003.zip` at SHA-256 `3261f235864a57c2c3f17f0ccd9588f24f888b21d5bf5c400ec089fe19311235`. Final isolated `gpt-5.6-sol`/high review returned `VERDICT PASS`, no blockers, and `SAFE_TO_COMMIT YES` for the exact nine-file scope. Proceed through scoped Git commit/push, green CI/CodeQL, merge, and merged-SHA/artifact binding. Production deployment remains separately authorization-gated. Do not re-export the corpus, reindex Meilisearch, submit IndexNow, mutate WordPress, or rewrite inherited baseline pages in this release.

## 2026-07-04 — Add WordPress/CMS as a private-first Base2026 vertical under web development

Decision: Base2026 should treat WordPress/CMS implementation insights as a separate source/category vertical under the broader web-development expansion, rather than burying them inside generic SEO. Initial anchors are `@iamdandavies` as a WordPress-focused creator and `@webhivedigital` as an SEO/WordPress hybrid source. The vertical remains private-first until reviewed source text, exact-evidence insight cards, and the existing indexation/release gates approve any public promotion.

Reason: A 2026-07-04 audit found that Base2026 already has a staged WebDevLog category, 61 exact WordPress public source-record matches, 13 WordPress/CMS topic rows, and multiple existing WordPress topics/cards. The current signal is real but scattered across SEO/CMS/web-dev topics, so a canonical vertical prevents routing loss while preserving the thin-content/publication safeguards.

Execution note: the first cards-only batch was completed on 2026-07-04 with 12 exact-evidence WordPress/CMS `insight_card_candidate` rows promoted to `reviewed` in local SQLite, 0 promoted to `approved`, and no public pages/deploy/indexation/outreach. Batch #2 was completed the same day with 12 more exact-evidence rows (10 from `@webhivedigital`, 2 from `@iamdandavies`) promoted only to `reviewed`, bringing the two-batch private reviewed WordPress/CMS card set to 24 rows with 0 public/approved promotion from these batches.

## 2026-06-26 — Hold templated city/niche AI visibility pages out of the index until evidence-approved

Decision: Broad Base2026 AI visibility hub pages may remain indexable, but generated city/niche audit pages must render `noindex,nofollow` and stay out of the sitemap unless a page is explicitly evidence-approved with unique local source material.

Reason: QA showed the current 16 California city/niche pages are mostly templated swaps after normalizing city and niche terms. Indexing them would create doorway/thin-content risk and conflict with the public research/proof layer.

## 2026-06-23 — Keep Base2026 discovery state out of crawlable query URLs (superseded for new/changed paths by 2026-07-14 Search V1 decision)

Decision: canonical Base2026 search/discovery URLs should be `/knowledge/` plus client-side `#search?...` state, not `/knowledge/index.html?...` or other crawlable query variants. Generated static entity pages should link back to the search workspace through hash state, while sitemap generation remains limited to self-canonical, indexable HTML files.

Reason: GSC/Ahrefs already surfaced duplicate/canonical noise around `/knowledge/index.html` and query-state search routes. Hash state preserves user navigation without asking crawlers to spend budget on filter/query combinations that canonicalize back to the search root.

## 2026-06-23 — Use Logic Crafts organization as GitHub home

Decision: treat `logic-crafts` as the current company GitHub organization for Base2026 and related Alex/company startup assets. Base2026 canonical GitHub URL is `https://github.com/logic-crafts/base2026`; local `origin` should point to `https://github.com/logic-crafts/base2026.git`.

Reason: Alex registered a company/org GitHub account because startup/application flows often request a company identity, and the project/repositories were moved there while keeping access effectively the same.

## 2026-06-15 — Use a compact current handoff to prevent context rot

Decision: keep `docs/project-memory/CURRENT_HANDOFF.md` as the first resume file for the active task. It should summarize the current goal, dirty source files, done work, verification, open loops, and exact next action. Full project-memory rereads should be targeted, not automatic.

Reason: the Base2026 thread is long and `git status` contains thousands of generated-page changes. Repeated full-context rehydration wastes attention and increases the chance of stale or contradictory action.

## 2026-06-15 — Add visible Evidence Q&A before any FAQ schema

Decision: source/topic pages may get visible Evidence Q&A sections generated from public-safe data, but do not add FAQPage schema in this pass.

Reason: Q&A can make source and topic pages more useful for readers, Google, and LLM retrieval. FAQ schema is no longer a general SEO shortcut and should only be added later if it matches visible content, passes validation, and has a clear user value.

## 2026-06-15 — Keep sitemap URLs self-canonical

Decision: the Base2026 sitemap should include only indexable HTML pages whose canonical URL matches the page URL.

Reason: Google Search Console already surfaced canonical/indexing confusion. Submitting alternate-canonical URLs wastes crawl budget and muddies diagnostics.

## 2026-06-15 — Generated entity routes must fail closed

Decision: missing generated source/topic/creator/compare URLs should return 404 instead of falling back to a generic Base2026 page.

Reason: ghost URLs with 200 responses create soft-404/indexing problems and make GSC diagnostics noisy.

## 2026-06-15 — Use static mailto forms on Base2026 until a backend form endpoint exists

Decision: `/knowledge/support.html` and `/knowledge/roadmap.html` may render a styled contact form, but for now it submits through `mailto:offflinerpsy@gmail.com` instead of copying the WordPress `admin-post.php` form.

Reason: Base2026 is a generated static site under `/knowledge/`. The WordPress form uses server-side handling and nonce/state that cannot be safely hardcoded into static generated HTML. A mailto form gives a visible support path now without pretending a backend submit flow exists. A future WordPress/plugin endpoint can replace it as a separate task.

## 2026-06-14 — Add public analytics as a compact search signal layer, not another navigation mode

Decision: Base2026 should expose deterministic public analytics generated from public JSONL during normal release packaging. Analytics may appear as a compact strip, topic/creator counts, and a dedicated `/knowledge/analytics.html` page. It should not create another modal, third column, or extra per-result button layer. Typography for the Base2026 product surface should use Geist / Geist Mono for a denser search-product feel.

Reason: the project is a searchable creator-video source database, so counts and signal rankings make the database more useful for users and future API/MCP consumers. But the UI was already suffering from repeated buttons and competing page states. Analytics should clarify ranking and signal strength while preserving the accepted `filters | workspace` model and familiar search-result flow.

## 2026-06-14 — Treat WordPress visual work as design-system work

Decision: WordPress public-site changes must be handled as design-system work, not isolated selector tweaks. Before reporting a WordPress UI task as done, inspect the live structure, normalize shared component rules, deploy/clear cache, verify live desktop/mobile, verify SEO title/description, and update project memory.

Reason: the homepage had inconsistent section grids, type scales, list treatments, and CTA sizing. The site is small and public-facing, so inconsistent page sections make the business look improvised.

## 2026-06-06 — Use file-based project memory

Decision: use `docs/project-memory/` as the operational source of truth for Base2026 planning, status, handoffs, public/private boundaries, deploy notes, and Hermes automation notes.

Reason: long Codex chats are disposable and can compact. Repo files remain inspectable by Codex, Hermes, maintainers, and future contributors.

## 2026-06-06 — Keep public TikTok product separate from private research base

Decision: publish only the public TikTok knowledge product and safe project code/docs. Keep private SEO/GEO/AEO research folders local unless explicitly reviewed and exported.

Reason: the project is moving toward open source and public deployment.

## 2026-06-06 — Use status board as operational planning board

Decision: use `STATUS_BOARD.csv` and `PHASES.md` as the planning board for Base2026 work.

Reason: CSV is easy for agents to update and easy for humans to inspect.

## 2026-06-06 — Separate ASR backlog from source-review backlog

Decision: use `needs_source_review` when captions fail and fallback media has no audio stream. Do not keep those videos in `needs_asr`.

Reason: ASR cannot succeed without an audio track. Retrying Whisper wastes time and creates false queued jobs.

## 2026-06-06 — Gate public UI through visual-system review

Decision: before broader public/GitHub exposure, run a dedicated visual-system pass for controls, spacing, filters, result cards, transcript expansion, desktop/mobile screenshots, and strict reviewer checks.

Reason: the UI works technically, but the current visual quality is not good enough to show as the public face of the product.

## 2026-06-07 — Treat Hermes as local prototype only

Decision: Hermes is a local/private helper for testing the knowledge-base idea, not a production or GitHub dependency.

Reason: the public project needs a Hermes-free transcription intake path for TikTok and Instagram. Before production hardening or GitHub publication, research and choose a reproducible pipeline that can run on VPS or use reliable free/self-hosted components.

## 2026-06-07 — Default daily ingestion to zero paid LLM usage

Decision: the daily TikTok/Instagram ingestion loop should use local tools by default: `yt-dlp`/fallback extractors, `ffmpeg`, local ASR, deterministic cleanup, token-diff guards, JSONL upload, and optional local LLM cleanup only after validation.

Reason: paid LLMs and Codex subscriptions should not be consumed by routine daily ingestion. Codex remains the command center for architecture/debugging/review, not the scheduled worker.

## 2026-06-07 — Use Gemma 4 12B as primary local cleanup LLM target

Decision: `faster-whisper` or `whisper.cpp` handles transcription. Gemma 4 12B is the primary local LLM target for transcript cleanup, topic extraction, quality flags, and admin/operator tasks. The exact model remains configurable by local endpoint.

Reason: transcription should be ASR, not LLM guessing. Cleanup can use a local open model, but only behind token-diff guards and with paid LLM disabled by default.

## 2026-06-07 — Keep public prose direct and stop AI slop

Decision: apply a stop-slop style review to README, docs, UI copy, and public GitHub positioning. Do not apply it as a rewrite policy for creator transcripts.

Reason: public docs should sound like engineering notes, not generated marketing. Transcripts must preserve how the creator spoke.

## 2026-06-07 — Public product is an attributed intelligence layer

Decision: Base2026 public launch should not be framed or implemented as a mass dump of full third-party TikTok/Instagram transcripts. The public layer should prioritize attributed excerpts, source records, topic pages, insight cards, comparison views, methodology, and opt-out/correction flow. This 2026-06-07 safety mode is superseded by the 2026-06-14 product passport where it conflicts: raw/unreviewed transcripts stay private, but reviewed polished public source text/transcript may be exposed as the source-record reading surface when policy allows.

Reason: this reduces platform, SEO, creator-trust, and product-quality risk while increasing the actual value of the project.

## 2026-06-07 — Public exports are excerpt-only by default

Decision: public export scripts must not include raw/unreviewed full third-party transcripts by default. The old `-IncludeFullTranscripts` flag remains unsafe for public deploys because it is a blunt raw-export path. The target public implementation is a reviewed public source-text field with policy/QA support, not a shortcut through raw transcript export.

Reason: default public artifacts should match the source-record/insight architecture and avoid accidental transcript dumping while still allowing the database product to expose reviewed source text intentionally.

## 2026-06-08 — Index only aggregate topic and comparison pages

Decision: generate topic and comparison pages for public UX, but only allow `index,follow` when a topic has at least two public source-backed insight cards. Singleton topic/compare pages must be `noindex,follow` and excluded from topic index pages.

Reason: this keeps navigation useful without turning Base2026 into thin programmatic SEO pages or scaled content abuse.

## 2026-06-08 — Generate public info pages from Markdown source

Decision: keep public roadmap, project story, privacy, source/content policy, support, and site-structure copy in `docs/public-pages/`, then generate static HTML with `scripts/generate-info-pages.py`.

Reason: the public site needs visible trust/roadmap pages, while future agents need editable Markdown source instead of hand-maintaining generated HTML.

## 2026-06-09 — Use existing Rank Math; add static SEO directly to Base2026

Decision: do not install Yoast or another SEO plugin on top of the already active Rank Math plugin. Keep WordPress SEO under Rank Math and add Base2026 static metadata, canonical URLs, schema, and sitemap generation directly in the Base2026 build pipeline.

Reason: two SEO plugins create conflicts. Base2026 is static under `/knowledge/`, so it needs build-time SEO output and a dedicated sitemap instead of relying only on WordPress plugin discovery.

## 2026-06-10 — Keep backfill candidates private until explicit promotion

Decision: local model claim backfill may import verified candidates into SQLite as `claim_type = insight_card_candidate` and `review_status = pending`, but those candidates must not be auto-promoted into public insight cards by the normal export auto-promotion flag.

Reason: the backfill layer is new and must prove evidence fidelity before it changes public source/topic pages. Public promotion remains a separate reviewed step.

## 2026-06-10 — Use a project-local Python worker environment

Decision: use `.venv` plus `requirements-local-worker.txt` for local worker dependencies such as `faster-whisper`, `ctranslate2`, and `requests`.

Reason: MacBook system Python is not a stable production worker environment, and ASR dependencies should not be installed ad hoc into global Python.

## 2026-06-10 — Keep Qwen primary for claim extraction; test Gemma 4 as reviewer

Decision: do not promote `gemma4:12b` to primary private claim extractor yet. Keep `qwen3:8b` as the primary extractor for the next controlled backfill batch, and test `gemma4:12b` as a semantic reviewer/precision gate before broader import.

Reason: on the same current 3-source backfill queue sample, `gemma4:12b` produced 1 verified candidate at 49.870 seconds/source, while `qwen3:8b` produced 5 verified candidates at 33.972 seconds/source. Gemma 4's single candidate was clean, but yield and latency are not good enough to make it the main extractor without a prompt/reviewer redesign.

## 2026-06-10 — Use ChatGPT Pro as a manual review lane, not a production worker

Decision: ChatGPT Pro/GPT-5.4 may be used through generated review packets for small-batch semantic and copy review of private insight-card candidates. It must not be treated as scheduled browser automation, a limit-bypass architecture, or a replacement for deterministic evidence verification.

Reason: Base2026 needs high-quality, faithful insight-card copy more than raw candidate volume. Local models can generate candidates cheaply, but exact evidence matching does not prove semantic entailment. A manual GPT review lane gives better text quality while keeping the durable pipeline scriptable, auditable, private-by-default, and safe to continue without publishing private material.

## 2026-06-10 — Prefer GPT/Codex for small-batch insight-card text quality

Decision: for the current low-volume backfill and launch-quality card work, ChatGPT Pro/GPT-5.4 or Codex may act as the primary source-backed claim extraction and semantic/copy quality lane. `qwen3:8b` remains useful as optional local draft/prefilter/offline mode, but it is not required before GPT review and must not be trusted as a final writer.

Reason: the project does not currently have mass throughput pressure. The important failure mode is not cost; it is bad public-facing claims that sound plausible but do not follow from the source. GPT-first packets let the system skip weak local drafts when quality matters, while local scripts still enforce repeatable queueing, strict JSON handoff, evidence verification, private/pending import, and public promotion gates.

## 2026-06-10 — Require promotion reports before public insight-card promotion

Decision: pending `insight_card_candidate` rows must pass a read-only promotion review report before any future command can promote them into public insight cards.

Reason: evidence verification and private import prove that claims are source-backed enough to store locally, but public promotion also needs source-level selection, duplicate control, text-quality checks, and explicit reviewer accountability. The report is a gate; it does not publish or mutate SQLite.

## 2026-06-10 — Gate public UI changes with mixed mobile visual QA

Decision: use `scripts/mobile-visual-qa.mjs` as the repeatable visual QA gate for the mixed WordPress root site and Base2026 `/knowledge/` app before public UI deploys.

Reason: the public site spans WordPress theme CSS and static Base2026 pages. Mobile bugs can appear in either layer, so the gate must check both surfaces across phone, tablet, and desktop viewports for horizontal overflow, clipped controls/headings, console errors, search readiness, forms, and the Base2026 source dialog.

## 2026-06-11 — Use one canonical source identity system

Decision: Base2026 source pages, creator pages, search cards, and source modals must render creator/source identity through one shared pattern: avatar, `@handle`, date when relevant, platform icon, compact meta chips, and compact share actions. Do not introduce separate page-specific layouts for the same source metadata.

Reason: inconsistent repeated labels made the product look improvised and hard to scale. A canonical identity system keeps static generation, modal rendering, SEO/schema naming, and future multi-index UI work aligned without rebuilding every page surface separately.

## 2026-06-11 — Keep Base2026 filters native to the static app

Decision: Base2026 mobile search filters should be implemented as a native static-app drawer in the `/knowledge/` UI, not through a WordPress or Contact Form plugin.

Reason: the filter state belongs to the Meilisearch/InstantSearch app under `/knowledge/`, not to WordPress form handling. A native drawer avoids plugin coupling, keeps the public app fast, works with the existing static export, and is easier to test in repeatable live QA.

## 2026-06-11 — Keep mobile navigation visually unified across WordPress and Base2026

Decision: WordPress and Base2026 mobile headers should use one shared visual contract: avatar header, compact light floating drawer, a non-navigating `Base2026` parent item that expands submenu links, and a high-contrast CTA hover/focus state.

Reason: the public site spans WordPress and a static Base2026 app. If the two mobile menus behave differently, users experience the product as stitched together rather than intentional. Keeping one navigation contract reduces launch QA risk and makes future page additions easier to verify.

## 2026-06-11 — Use h264-first media fallback and local worker ASR on macOS

Decision: TikTok ASR fallback on Mac must use POSIX-safe yt-dlp output templates, prefer known h264/downloadable media formats before generic `best`, and invoke the project `base2026-worker.py transcribe` faster-whisper path instead of relying on a global `whisper` CLI.

Reason: macOS PowerShell path separators created bad backslash-named media paths, TikTok H265/bytevc1 downloads failed ffmpeg audio extraction in the local environment, and the old global `whisper` command was not installed. The local worker path is reproducible, checked by `doctor`, and keeps ASR inside the project runtime.

## 2026-06-11 — Derive Base2026 static cache-bust from release name

Decision: release packages should use the release name as the static CSS/JS cache-bust value instead of a manually edited hardcoded marker.

Reason: manual cache-bust constants go stale and can make a successful deploy appear broken in the browser. Release-derived cache busting makes every package self-identifying and reduces launch QA ambiguity.

## 2026-06-12 — Version delayed static payloads with the release cache-bust

Decision: static JSONL payloads loaded by Base2026 JavaScript after page load, starting with `documents.jsonl`, must use the same release cache-bust/version as the JS/CSS assets when immutable cache headers are active.

Reason: Meilisearch results can update with a new deploy while a browser still holds an older immutable JSONL payload. Versioning delayed payload fetches keeps source-modal record lookup aligned with the deployed search index and prevents false `Source record unavailable` states.

## 2026-06-12 — Normalize Base2026 asset versions after all static generators run

Decision: `scripts/package-public-release.ps1` must run a final recursive HTML pass over the release `web/` folder after every generator has finished and rewrite all public CSS/JS asset query strings to the current release cache-bust, including `../static/...` paths used by source/topic pages.

Reason: generator-local hardcoded style versions can overwrite earlier package-time replacements. With immutable `/knowledge/static/` cache headers, stale query strings make mobile fixes appear missing on live source/topic pages even when the deployed CSS file is correct.

## 2026-06-11 — Replay approved insight-card candidates from private archive

Decision: approved/reviewed/public `insight_card_candidate` rows are persisted in an ignored private JSONL archive under `12_knowledge-base/sources/tiktok/insight-candidates/reviewed-candidates.jsonl` and replayed by `build-kb-sqlite.py` during clean SQLite rebuilds. These replayed candidates do not create markdown claim cards under `12_knowledge-base/canonical/claims`; `kb-audit.py` now treats the difference between SQLite claims and markdown claim-card files as valid only when it equals the `insight_card_candidate` count.

Reason: reviewed candidate promotion must be durable without committing private review artifacts or generated claim-card files. Clean rebuilds should preserve approved public cards, while private `needs_human` candidates remain local and unpublished until separately reviewed.

## 2026-06-11 — Replay private candidate queues locally but exclude them from public export

Decision: ignored `insight-card` review archives may replay private queue statuses such as `needs_human` during clean local SQLite rebuilds, but `export-public-tiktok.py` must exclude every non-public `insight_card_candidate` row from public JSONL artifacts.

Reason: the operator needs durable private review state after clean rebuilds, but public deployment must not expose unapproved candidate claims even with `public=false` flags.

## 2026-06-11 — Keep the local TikTok refresh queue at all current public creators

Decision: the MacBook local refresh default is `config/tiktok-intake-queue.local.json`, ignored by Git, with all four current public TikTok creator sources. The committed `config/creators.example.json` also lists the same four public sources as a safe example.

Reason: a partial default creator config caused a full refresh command to check only two creator accounts. The local queue must match the public source set so scheduled and manual runs do not silently miss active creators.

## 2026-06-11 — Count existing approved cards before candidate promotion

Decision: insight-card promotion review must count already approved/reviewed/public candidate cards for the same source before recommending more candidates from that source. The reviewer must also flag speculative claims, generic actions, and overbroad actions as `needs_human`.

Reason: evidence-exact text can still be bad public product copy, and source pages should not be overfilled by repeatedly promoting mechanically verified candidates from the same video.

## 2026-06-12 — Use GPT/Codex as the current card text review lane

Decision: for the current launch-quality insight-card backlog, use GPT/Codex source-only review packets as the primary semantic/card-writing lane. The preferred working model is ChatGPT/GPT 5.5 Medium through Codex when available. Do not use local LLMs as the primary extractor or final writer for public card text.

Reason: the backlog is low-volume enough that quality and source faithfulness matter more than cheap local throughput. Scripts still own queueing, exact evidence verification, private import, reviewer promotion, rebuild/export, and deployment gates.

## 2026-06-12 — Enforce the public release contract in code and CI

Decision: public Base2026 package/deploy paths must obey `contracts/base2026.public-release-contract.json`: no full transcript release flag, no implicit public insight auto-promotion, no tracked generated export artifacts, fixture-backed positive/negative CI checks, and staged release exports before packaging.

Reason: the public boundary cannot depend on chat memory or manual operator discipline. The live ay76 export is excerpt-only, but it still contains legacy `auto_evidence_match` public cards. Future public data-changing deploys must either explicitly review/migrate those cards or block before replacing the live release.

## 2026-06-12 — Split legacy public-card migration into text and visual lanes

Decision: legacy `auto_evidence_match` public cards must be migrated through `scripts/base2026-review-legacy-insights.py`. Text-only cards can be approved deterministically or repaired through GPT/Codex source-only JSON packets. Cards whose meaning depends on what the TikTok shows must be marked `needs_visual_context` until a thumbnail/frame evidence layer confirms the visible context.

Reason: rough TikTok transcripts often omit or distort the visual point of the video. Rewriting those cards from text alone can create confident but false public claims. A separate visual-context lane keeps the public insight layer useful without inventing screenshots, UI states, charts, or visual demonstrations that the supplied public passages do not prove.

## 2026-06-13 — Replay reviewed legacy public cards during clean rebuilds

Decision: reviewed legacy public insight cards are persisted in an ignored local archive at `12_knowledge-base/sources/tiktok/insight-candidates/reviewed-legacy-insights.jsonl` and replayed by `scripts/build-kb-sqlite.py` during clean SQLite rebuilds. The replay deletes any prior claim evidence for that claim before inserting reviewed evidence so one claim cannot duplicate in public export.

Reason: the ay80 pipeline showed that a clean SQLite rebuild can erase DB-only reviewed legacy approvals and collapse public cards unless those approvals have a replayable source of truth. Keeping the replay hook in code and the reviewed archive local/ignored preserves launch-quality public cards without committing private review artifacts or generated exports.

## 2026-06-13 — Keep the public GitHub repo Actions-free

Decision: do not ship `.github/workflows` or GitHub Actions Dependabot config in the public Base2026 repository. Local scripts (`validate-github-metadata.py`, publication boundary audit, public release contract, export policy checks, and visual QA) are the required validation lane before push/deploy.

Reason: the current GitHub account/repo setup should not depend on GitHub Actions. Keeping the repository Actions-free prevents GitHub from creating failing/unavailable checks while preserving the public/private boundary through local deterministic gates.

## 2026-06-13 — Replace source modal primary UX with a source-detail workspace

Decision: the main `/knowledge/` search experience should keep search and filters visible while opening source detail in the main results workspace, not in a modal. Static source pages remain for canonical URLs, SEO, sharing, and direct indexing, but they should use the same source-detail structure as the live search workspace. Search results should expose one primary action, `View source`; original source, creator, correction/removal, and share actions belong inside source detail.

Reason: the modal/source-page split makes users guess where the complete record lives and breaks the search flow. Base2026 is growing toward API/MCP consumption, so UI, static SEO pages, and future public API responses need one shared source-detail model instead of separate modal and page logic.

## 2026-06-13 — Make `/knowledge/` the primary navigation workspace

Decision: `/knowledge/` is the primary interactive Base2026 workspace. Generated source, creator, topic, and compare pages remain for SEO, canonical URLs, sitemap inclusion, sharing, and direct entry, but internal exploration from the search workspace should stay in the search workspace through route state such as `?source=`, `?creator=`, `?topic=`, and `?compare=`. Static generated pages should provide an `Open in Search Workspace` action back into `/knowledge/`.

Reason: the public product should feel like one searchable knowledge workspace, not a set of disconnected generated pages. This preserves programmatic SEO value while keeping user navigation, filters, and search context coherent.

## 2026-06-13 — Keep the `/knowledge/` workspace two-column on desktop

Decision: desktop `/knowledge/` must not show filters, results, and source detail as three simultaneous columns. The accepted workspace contract is `filters | workspace`: the left column keeps filtering/search context, and the right column shows one active state at a time. Default state shows wide results; `?source=` state replaces results with a wide source detail view.

Reason: the three-column attempt made the product feel like several narrow admin panes and squeezed the main evidence reading surface. Base2026 should behave like a search workspace: filters stay available, but results/detail/creator/topic states occupy one readable main workspace instead of competing for horizontal space.

## 2026-06-14 — Do not render platform caption metadata snippets in public source UI

Decision: runtime source detail and generated source pages must not render the platform title/caption metadata snippet block. Public source UI should use the reviewed public excerpt/passages plus stable provenance fields such as platform, policy, language, and original source link.

Reason: truncated platform metadata looks like a broken transcript and confuses users. The public evidence surface should show readable public evidence text, not cropped platform metadata that Base2026 did not author or verify as transcript content.

## 2026-06-14 — Exclude no-public-text source records from public export

Decision: `export-public-tiktok.py` must skip source records that have neither public transcript text nor public chunks. Held rows such as `needs_source_review` may remain in local inventory, but they must not become empty public source JSONL rows, static source pages, or sitemap entries.

Reason: an empty source record is not useful to readers or search engines and can leak unreviewed/truncated platform metadata. Public source pages need usable public evidence before publication.

## 2026-06-14 — Keep source provenance as compact metadata, not bottom cards

Decision: public source detail UI must not render a separate bottom `Source Provenance` card stack or empty `Public Insight Cards` sections. Source-level platform, public policy, language, and linked insight count belong in compact top metadata chips. Source detail should render only meaningful content blocks: source excerpt, matched passage when selected, related passages when present/loading, and insight cards only when linked.

Reason: the bottom provenance cards duplicate information already visible in the source header and make mobile navigation feel like several disconnected pages. Empty sections add noise and make users hunt through repeated labels instead of reading the evidence.

## 2026-06-14 — Treat reviewed public source text as the database surface

Decision: the long-term public product contract is not `excerpt-only` source detail. Base2026 should expose reviewed polished public source text/transcript as the readable source-record surface when policy and QA allow, while keeping raw captions, raw ASR, media, logs, private QA notes, and unreviewed transcripts private. Public source pages and `/knowledge/?source=` should pair that source text with Base2026-authored summaries, topics, insight cards, attribution, original links, methodology, and correction/removal paths.

Reason: Base2026 was conceived as a searchable text database for creator videos. The previous excerpt-only contract reduced scraping risk but became product architecture by accident, causing selected source records to feel cropped, repetitive, and less useful than the underlying database. The corrected boundary is no raw/unreviewed transcript dumps, not no readable transcript/source text.

## 2026-06-14 — Make public source detail intelligence-led without duplicating source text

Decision: public source pages and runtime `/knowledge/?source=` detail should pair reviewed public source text with Base2026-authored source intelligence. Reviewed `Source Intelligence` cards, summaries, topics, and comparisons should explain the source; the readable public source text/transcript should provide the database context when policy allows. The same source text must not be repeated as the hero lead, heading, source excerpt, matched passage, and related/additional passage. Search-match and additional-evidence blocks should render only when they add distinct context. Raw/unreviewed transcripts remain private/local.

Reason: repeating a TikTok transcript across several public sections makes Base2026 look like a raw transcription dump and destroys the product value. Hiding the reviewed source text entirely also weakens the database. The public product should feel like an annotated source-backed knowledge base: readable source text plus a claim/insight layer for verification, SEO, sharing, API/MCP consumption, and creator correction/removal workflows.

## 2026-06-14 — Use a search-engine result model for Base2026 UX

Decision: `/knowledge/` should behave like a familiar search engine over creator-video source records. Results are a simple vertical list of matching videos/authors/topics with short previews. Selecting a result opens the full source record: short explanation, fuller explanation, normalized transcript/source text, and related topics/insights. Creator exploration should behave like applying a creator filter in the same search workspace. Avoid button proliferation and competing page/modal variants.

Reason: users already understand Google-style search: query, scan result previews, open the full result, return/filter/refine. Base2026 should not invent an admin-like navigation model with many buttons and duplicated source surfaces when the core product is a searchable knowledge database.

## 2026-06-14 — Generate public topic signal briefs only for strong topics

Decision: Base2026 topic signal briefs are deterministic public-release artifacts generated from public JSONL only. They render only for topics with at least 5 source records, 2 creators, and 3 public insight cards. Weak or thin topics remain ordinary topic/search pages and must not receive inflated signal UI.

Reason: the signal layer should make Base2026 more useful as a source-backed market intelligence library without creating thin SEO pages, unsupported claims, or another transcript dump. Keeping the generator deterministic and public-data-only preserves the publication boundary and makes future API/MCP exposure safer.

## 2026-06-14 — Add deterministic public analytics and Geist search-product typography

Decision: Base2026 now ships a deterministic `analytics_summary.json` generated from public release JSONL only. `/knowledge/` uses it for the compact analytics strip, topic/source-count chips, and creator/source-count chips. `/knowledge/analytics.html` is the public analytics page for source records, passages, topics, creators, and signal rankings. Base2026 product UI uses Vercel Geist/Geist Mono for the search workspace while keeping the warm Alex Yarosh visual system and WordPress ecosystem header/footer.

Reason: the database should expose useful aggregate intelligence without adding another private runtime dependency or publishing raw captions. Build-time public analytics updates automatically whenever a new public TikTok release is packaged. Geist reduces the heavy, oversized feel of the previous UI and makes the product read more like a compact search/research tool.

## 2026-06-15 — Do not publish newest source-only records silently

Decision: the public export/package lane now includes a readiness check for the newest source record. If the latest public source has readable public source text but no topic assignment and no public reviewed insight, `scripts/check-public-content-readiness.py --latest 1 --fail` blocks release packaging. `export-public-tiktok.py` also honors reviewed `claim_evidence.quote_or_span` when building public insight cards instead of re-deriving evidence only from the claim text.

Reason: a source-only record with just normalized transcript text does not express the Base2026 product value. The database needs both readable source text and an intelligence layer: reviewed topics, source-backed claims, and suggested actions. Ignoring reviewed evidence caused approved candidate rows to create topics without visible public insight cards, which made new TikToks look empty even after review.

## 2026-06-15 — Keep analytics and legacy generated routes inside `/knowledge/`

Decision: generated Base2026 analytics links must stay inside the `/knowledge/` app. From `/knowledge/analytics.html`, topic links use `./topics/...` and workspace links use `./index.html?...`. Legacy/root paths for generated entities (`/topics/...`, `/sources/...`, `/creators/...`, and `/compare/...`) should 301 redirect into `/knowledge/...` rather than falling through to WordPress.

Reason: Base2026 generated pages are SEO/share support for the knowledge product, not WordPress root pages. Root-escaping links made populated topic pages appear empty/404 and split navigation between WordPress and Base2026. Redirects preserve existing or accidental public links while keeping canonical pages under `/knowledge/`.

## 2026-06-15 — Group near-duplicate Source Intelligence in source detail

Decision: runtime source detail and generated static source pages should group closely related reviewed insight rows from the same source into one Source Intelligence card. Topic navigation belongs in compact topic chips; repeated large `Search this topic` buttons should not appear under every insight card.

Reason: multiple reviewed rows can be valid data while still looking like duplicated product value when they describe the same event or argument from adjacent topic angles. Grouping preserves the evidence and topic coverage without making the user read the same source claim several times or guess which identical-looking button matters.

## 2026-06-15 — Keep source page hero actions and evidence blocks minimal

Decision: generated source pages and runtime source detail should show the platform icon only in compact metadata, not beside the creator identity. Source hero primary actions should stay limited to `Open in Search Workspace`, `Open original`, and `Creator`; correction/removal remains a trust/support/footer path, not a hero CTA. Supporting passage blocks should render only for genuinely distinct public passages, not same-source chunks already contained in the visible Source Text.

Reason: duplicated platform badges, second-row trust buttons, and tail passage fragments make source records feel unstructured and non-production. Source detail should read as one clear record: identity, metadata, primary actions, Source Text, Source Intelligence, and only meaningful supporting context.

## 2026-06-15 — Publish AI/API access as a read-only public contract

Decision: Base2026 exposes a public `API & AI Access` page, `api-index.json`, `llms.txt`, and static JSONL entry points for reviewed public data. The live search proxy at `/knowledge-search/multi-search` is documented as read-only and ranking-oriented; bulk/agent analysis should prefer the static public JSONL files. Raw captions, raw ASR, media, private QA, local databases, and unreviewed transcript material remain excluded.

Reason: Base2026 is meant to be useful to humans and AI tools as a source-backed knowledge base. Publishing a clear read-only access contract makes integrations possible without encouraging scraping of the visual UI or leaking private pipeline material.

## 2026-06-17 — Show Source Intelligence state even when no public cards exist

Decision: runtime source-detail pages and generated static source pages must always render the `Source Intelligence` section for a selected source. If a source has no reviewed/public Source Intelligence cards, show an explicit empty state instead of hiding the section. Do not promote pending/private cards just to remove the empty state.

Reason: hiding the section makes a valid source record look broken and leaves users unsure whether the pipeline failed. An explicit empty state preserves the public/private boundary, explains that unreviewed candidates are withheld, and keeps the UI contract stable while visual/evidence-dependent cards wait for review.

## 2026-06-18 — Route data-changing releases through one canonical gate

Decision: TikTok/source data-changing releases must use `scripts/base2026-release-gate.ps1` as the command center. The gate owns polish status, optional `AfterPolish`, newest-source readiness, publication boundary, metadata validation, export policy, release contract, packaging, optional deploy/reindex, live SEO crawl, and mobile visual QA. Direct deploy is reserved for explicit reviewed hotfixes or releases that have already passed the gate.

Reason: repeated regressions came from treating intake, public export, deploy, reindex, and QA as separate chat-driven steps. A single reproducible release gate gives future agents one route through the same checks and makes the previous failure modes visible in `PIPELINE_ERROR_LEDGER.md`.

## 2026-06-18 — Keep platform-neutral social discovery private and non-mutating first

Decision: Phase 1/2 of the free social intake plan adds capability reporting and `scripts/social-discover.py`, but discovery output remains private JSONL under ignored `.planning/`. The script must not write `videos.csv`, public export, Meilisearch, or deploy. TikTok discovery stays `yt-dlp --flat-playlist` first; `gallery-dl` and `instaloader` are optional adapters surfaced by doctor and failure records.

Reason: Base2026 needs a repeatable adapter/spool layer before expanding beyond TikTok. Mutating the proven TikTok CSV or public release path before the adapter contract is verified would recreate the same ad hoc pipeline failures the release gate is meant to prevent.

## 2026-06-18 — Bridge social discovery into TikTok queue only through a dry-run importer

Decision: `scripts/import-social-discovery-to-tiktok-csv.py` is the only supported bridge from ignored `.planning/social-discovered.jsonl` into private local `12_knowledge-base/sources/tiktok/videos.csv`. The importer is dry-run by default, imports only TikTok source rows, dedupes by `video_id`, fills only missing safe metadata on existing rows, preserves old-source cutoff semantics, and creates an ignored backup before `--apply`. It must not trigger public export, Meilisearch, deploy, or Git staging.

Reason: the user needs a pipeline that can accept new creators without chat improvisation, but the proven TikTok CSV remains a private compatibility layer. A dry-run-first bridge lets new discovery feed the current refresh/release gate while preventing non-TikTok leakage, duplicate rows, and accidental public publication.

## 2026-06-18 — Check-only TikTok refresh must be read-only

Decision: `scripts/hermes-tiktok-refresh.ps1 -CheckOnly` and `-DryRun` must never run legacy mutating inventory before exiting. They now run social discovery into ignored `.planning/`, run the discovery importer without `--apply`, print current queue state, and preserve the exact `videos.csv` hash.

Reason: a command named check-only must be safe to run repeatedly while diagnosing the queue. If it mutates `videos.csv`, agents cannot tell whether new rows came from an intentional import or from a supposedly read-only check.

## 2026-06-18 — Treat social discovery as production-proven only through the release gate

Decision: the social-discovery bridge is accepted as the path for adding new TikTok creators only when the full route is used: ignored local creator/intake config, private discovery JSONL, importer dry-run, explicit apply with ignored backup, current-batch polish gate, newest-source readiness, public export policy, release contract, deploy/reindex, live SEO crawl, and mobile visual QA. The ay41 and ay42 releases are the proof cases for this route.

Reason: discovery and queue import are not enough. The user needs a traffic/content pipeline, but Base2026 can only scale safely if new creator videos become live public records through the same review and publication gates that protect source quality, public/private boundaries, and search index consistency.

## 2026-06-18 — AfterPolish must not run discovery or inventory

Decision: `scripts/hermes-tiktok-refresh.ps1 -AfterPolish` is a rebuild/export lane only. It must skip inventory, caption intake, social discovery, and importer work, then rebuild from existing reviewed polish outputs. New discovery belongs before the polish batch; release packaging must not silently expand `videos.csv`.

Reason: the ay42 release attempt proved that running inventory inside `AfterPolish` can expand the private queue with default limits after the operator has already selected a batch. That makes release results non-deterministic and can introduce unreviewed rows. Keeping `AfterPolish` rebuild-only makes the pipeline predictable.

## 2026-06-19 — Fresh creator releases must use `LatestReadiness 3`

Decision: data-changing releases that add fresh creator/video rows must run `scripts/base2026-release-gate.ps1` with `-LatestReadiness 3` until the readiness gate becomes batch-aware. A single newest-source check is not enough for multi-creator batches.

Reason: the ay43 pass showed that one latest source can pass while two adjacent fresh `@gobigsystems` source pages still lack reviewed public Source Intelligence. ay44 fixed those pages with exact-evidence reviewed cards and proved that `-LatestReadiness 3` catches this class of launch defect before final sign-off.

## 2026-06-19 — ASR-too-little rows stay private

Decision: ASR fallback rows that produce no usable speech or very short text must remain `needs_source_review` and must not be bulk-promoted into public export. `scripts/tiktok-process-transcripts.ps1` must report the ASR failure class and dedupe notes so retry results are auditable instead of noisy.

Reason: some downloaded TikTok audio is music-only, visually dependent, or otherwise unusable for faithful transcription. Publishing a confident public source record from 0-4 words would invent meaning. The safe path is to ship only QA-pass ASR rows and keep weak ASR rows private until a better source/audio verification lane exists.
