# Decisions

## 2026-09-06 — Store truthful reviewer identity without rewriting history

New editorial approvals follow Astra ownership. Accept exact gpt-6-astra and
legacy sol-max identities through the existing publisher; routine executors
cannot approve their own output. Store and return the actual approved reviewer.
The receipt migration widens only the CHECK and retains every legacy row in a
backup table. A rollback after any Astra receipt must fail rather than discard
or relabel data. Preserve all source, timestamp, hash and authority checks.

## 2026-09-05 — Bring the research workflow into an editor people already use

Ship one small, free WordPress companion to the existing public evidence API,
not a second corpus, paid authoring service or automatic publishing system.
Explicit short-topic search and explicit editable-note insertion preserve
source attribution and user control. Titles are never treated as quotations;
the optional project backlink is opt-in. Publish only a deterministic exact
four-file plugin ZIP, not arbitrary release archives.

Use an honest illustrative factory with separate live public totals. Preserve
the established light-blue/white visual system and existing search. Keep the
two authorized Chrome identities separate and isolate CLI account credentials;
recovery of an existing OAuth client does not require replacing it.

## 2026-09-05 — Make applied research the product; measure repeat value

Retain the Cloudflare supply/search architecture and current design. Test a
narrow practitioner job with a usable source-attributed SEO experiment, starting
with content-refresh diagnosis. Do not equate corpus size, article output,
directory submission or an aggregate event with demand or customer value.
Prefer delivered work artifacts, maintained useful topics, repeat agent workflows
and reproducible original research over arbitrary page quotas.

AgencyOS remains the management authority. Reuse the existing supervisor and
transactional reconciler; add only a read-only decision evaluator and bounded
optional measurement tags. Status readiness is not authorization. Preserve
unknown effects, channel-specific gates and the private/public boundary. A local
heartbeat is not laptop-independent execution. Document full cloud autonomy and
market validation as unfinished until directly demonstrated.

The complete contract is `../BASE2026_SELF_GROWTH_OPERATING_MODEL.md`.

## 2026-09-04 — Release the complete three-tool loop with first-party measurement

Release Evidence Search -> Source Diversity Check -> Source-backed Brief as one
measurable acquisition path. Keep Brief deterministic and limited to selected
public records, bounded excerpts, attribution and explicit unknowns. Activation
may use only the allowlisted first-party Analytics Engine contract; deployment
canaries must remain distinguishable from non-owner product use.

The migrated Cloudflare account's four D1 UUIDs are now the checked deployment
authority. `MEMBER_AUTH_ENABLED=false` remains intentional until the Google
member contour is separately re-enabled; never restore an old-account UUID or
silently flip the auth flag. Failed pre-version deployments are not releases.

## 2026-09-04 — Align claims to live intent; never relabel a different tool

Use “search inside expert videos” for the existing Evidence Search because the
route really searches Base2026's processed expert-video corpus. Preserve the
bounded-corpus, attribution and non-verdict language. Do not rename Source
Diversity Check as a source reliability checker: that SERP expects URL/DOI,
publisher credibility or bias analysis. Do not create a TikTok transcript
generator landing page until the product can actually accept a public URL and
return a private, policy-controlled result.

Reason: a precise high-intent promise can improve discovery without deceptive
doorway pages, false facts or a mismatch between query and product.

## 2026-09-04 — Compete with a narrow free-tool loop, not page volume

Use the sequence Evidence Search -> Source Diversity Check -> Source-Backed
Brief as the primary acquisition product test. Pair it with a reproducible
GitHub Evidence Pack and one platform-native original-data demonstration.
Measure non-owner referrals and successful tool actions over 72 hours. Do not
expand the existing 4,000-plus HTML corpus with keyword-swapped doorway pages,
fake `verified`/`best`/consensus language or promotional link spam. `Free` is a
valid acquisition hook only where the utility is genuinely usable for free.

Reason: the technical foundation already produces impressions; the missing
step is an inspectable reason to click, use and cite Base2026.

## 2026-09-04 — Use a bounded first-party Analytics Engine sink for public tool activation

The three public acquisition tools may emit only the allowlisted activation
events defined in `src/analytics.ts`, for the three exact tool routes. Store
event name, route, server UTC-hour bucket and coarse enum properties in
Analytics Engine; never store raw query/record/source IDs, notes, IP,
user-agent, referrer, cookies, fingerprint, auth/member or private-pipeline
data. Reuse the existing `MCP_RATE_LIMIT` binding under a separate key prefix,
cap events per browser page and keep the write fail-open for product UX.

Choose Analytics Engine over D1 because it is a native non-blocking custom-event
sink without a schema migration or scheduler; do not use Cloudflare Web
Analytics because it does not accept custom events. Do not claim unique
visitors. Production activation is recorded in
`HANDOFF_2026-09-04_SOURCE_BRIEF_ACTIVATION_RELEASE.md`; the earlier candidate
receipt remains implementation history, not current deployment state.

## 2026-09-02 — Merge Claim Receipt source but hold production at zero eligibility

Merge the independently reviewed public-repository implementation so the
schema, tests, exporter and fail-closed route are versioned, but do not apply
migration0005 or deploy the route while live public D1 has zero exact eligible
`internal-linking` cards. No relabeling, synonym inference, padding or filler
is allowed to manufacture the ten-row canary. Production requires both the
protected private typed wrapper and exactly ten genuine public projections.

Reason: source integration is reversible and reviewable; a live empty or
fabricated claim surface would create false product and SEO signals.

## 2026-09-01 — Release the bounded public MCP without weakening member auth

Ship the reviewed MCP only after the release builder includes every developer
surface, generated Worker types match the manifest, `AUTH_DB` and
`MEMBER_AUTH_ENABLED=true` survive dry-run/version readback, and a unique
account-scoped rate-limit namespace is present. MCP remains stateless,
public-D1-only and read-only. Production release receipts, not source presence,
control any claim that the endpoint is live.

## 2026-09-01 — Keep public API/MCP additive and read-only

Integrate the public API/MCP contract around the newer member-auth and
Evidence Search routes. The public Worker route may read only allowlisted
public D1 evidence/projection data and exposes bounded lookups; it must not
share member bindings, sessions, writes, moderation, credentials, raw ASR,
media, inbox or private pipeline state. The source/docs candidate is not a
deployment receipt, and any live release still needs the existing worker,
static, browser and publication-boundary gates.

## 2026-09-01 — Add reliability contracts without widening production authority

Keep the redacted production manifest, channel-job state contract, private
incident snapshot and privacy-safe measurement-event contract as additive,
read-only release-closure gates. They must report unresolved commit/binding,
incident, or external-effect conditions as holds; they do not authorize a
deployment, external retry, private-pipeline replay, analytics write, or
public data release.

## 2026-09-01 — Preserve external-effect fences and privacy-safe measurement

Unsupported channel states remain held until their contract is repaired, and a
possibly effective external action remains fenced until the same target is read
back. The five-event member measurement trace may use only opaque references and
bucketed properties; raw queries, private artifacts, credentials and provider
responses remain excluded. Emission stays a future reviewed canary.

## 2026-08-31 — Preserve reliability ownership and uncertain-operation holds

Complete attributed-segment selection, rejection of contradictory retain/
negative-classification decisions and prompt fit
remain distinct from quote/hash verification; neither proves creator truth.
Additive migration0016 ownership and operation accounting must survive rollback.
Release58's diagnostic rollback is57. Older56 requires zero active capture
leases and zero reserved/settling/uncertain operations. Never force-clear,
refund or replay uncertain work; pending-media recovery is not resurrection.
Cleanup pagination/starvation stays a separate scoped issue, not wider deletion.

## 2026-08-31 — Retire an unsupported orphan instead of fabricating a page

The content-strategy enrichment key did not create a generated route and its
proof references did not support the intended answer. Remove only that orphan
from active configuration, preserve its preimage privately and leave59other
entries unchanged. No alias to an adjacent noindex page, automatic new route or
weakened gate. Roadmap copy must distinguish configuration, publication,
indexation and dated performance in both initialHTML and JS.

## 2026-08-31 — Use archive work and correct exact unsupported claims

- Unchanged source hashes mean no forced guide revision, not no editorial work.
  The same six-hour office must finish distinct useful archive-backed tasks;
  fresh intake, another CMS or a new scheduler is unnecessary.
- An exact quote/hash is structural evidence, not proof that an inferred claim
  follows. Independent semantic review controls publication. Two known failed
  pairs were narrowly withdrawn with receipts/private history preserved.
  Do not rearm old publication tuples or reprocess unrelated sources.
- Private fallback is incident-first four times daily, native recovery remains
  five-minute. Accept and disclose external total-outage detection latency of
  up to six hours plus host availability; this is not continuous external watch.
- Preserve deployed source and reviewed public assets through exact audited Git
  changes. Source, generated artifact and live data are separate recovery inputs.
  No stale-design restore or private/generated bulk staging.


## 2026-08-30 — Maintain task guides, not one SEO page per video

- Reuse existing topic canonicals for supported user tasks; keep original
  blog stories separate. New evidence may update, merge, contradict or add
  nothing. No-change does not produce a synthetic freshness date.
- Reuse the existing editorial store and signed publisher with the
  `evidence_guide` kind. Five existing topics form the first registered cohort;
  registration does not approve their content. Routine reviewers do not ask
  Alex to check every passing page.
- A guide binds short quotes to exact public document hashes and admission
  checks. Publish/read-time dependency checks detect drift; independent semantic
  review still establishes support, attribution, uncertainty and original value.
  Neither hashes nor the absence of full transcripts proves rights or truth.
- Source catalog navigation follows existing public receipts, not unreviewed
  intake. The legacy selection stays visible and labeled.
- Keep one sequential data-only publisher. A guide correction uses a separately
  reviewed higher revision and explicit CAS. Stored inspection is for repair
  identity, not a public source-health certificate.
- Pre-guide Worker versions are not compatible with guide rows in the shared
  table. Use verified compatible restore points, never delete receipts/data to
  make an older design/runtime work.
- Continue the existing six-hour office rather than introducing another
  scheduler. All execution/review seats remain Sol Max under the owner override.
  Cloudflare serves published pages; authoring/review/refill is host-dependent.

Reason: the focus group and live corpus checks found useful task evidence but
also duplicate works, unsupported claim/span pairs and a real catalog gap.
Maintained canonical answers and source-dependent repair are a stronger
product than bulk paraphrase pages. Release proof:
[Phase 21](BASE2026_EVIDENCE_SEO_RELEASE_2026_08_30.md).

## 2026-08-30 — Separate X scheduling from LinkedIn Computer Use

- The owner selected Computer Use in the existing Chrome session for LinkedIn,
  explicitly excluding Buffer. Do not retry LinkedIn OAuth or disguise browser
  automation. Stop at new security checks and preserve the existing session.
- Buffer Free is X/Twitter-only; the private client's submit path rejects
  LinkedIn, including dry-run. The first X thread and four scheduled posts have
  real receipts, not merely prepared copy.
- Computer Use's action-time confirmation applies before the final LinkedIn
  public Post. Standing publication permission does not remove that skill gate.
- Scheduled Buffer posts publish in its cloud; local queue refilling requires
  Codex and Keychain access. Do not call that unlimited cloud-only autonomy.

Reason: protect the existing LinkedIn account after repeated verification and
follow the owner's chosen publishing route without conflating drafts and posts.

## 2026-08-29 — Hold third-party dataset mirrors until rights are explicit

- Apache-2.0 covers repository code and documentation; it does not
  automatically license third-party creator video, captions or bounded source
  text for redistribution as a hosted dataset.
- Do not upload the current JSONL corpus to Hugging Face, Zenodo or another
  mirror until a dataset-level rights model, per-record reuse basis/provenance,
  complete versioned payload, checksums, and correction/takedown policy pass a
  new public-release review.
- A deliberately metadata/pointer-only export may be evaluated later, but it
  is not an automatic exception to the rights and provenance gate.

Reason: the audited static-v3 documents, passages and insight cards have useful
source attribution but no explicit license/rights/provenance keys. A public,
readable excerpt is not by itself evidence of third-party redistribution
rights.

## 2026-08-29 — Keep operating memory compact and public totals live

- `CURRENT_STATUS.md` is the one-screen current operating snapshot. Keep
  `PROJECT_STATE.md`, `ACTIVE_PHASE.md`, `NEXT_ACTION.md` and
  `CURRENT_HANDOFF.md` compact; Git history and dated receipts preserve old
  states. Do not append competing chronological "current" sections.
- Public corpus totals come from a read-only, cacheable `/api/stats` endpoint
  backed by public D1. Homepage and analytics keep a verified no-JS fallback
  but refresh from this endpoint when available.
- The July analytics corpus remains available only as an explicitly dated
  historical release analysis; it must not be presented as current D1 totals.
- Public stats expose aggregate public counts only. Private pipeline state,
  media, transcripts, artifacts, credentials and publication controls remain
  outside the endpoint.

## 2026-08-28 — Evidence Brief V2, restrained motion and personal GitHub

- Preserve the approved blue-white `b26-independent-v1` visual authority.
- Use bounded progressive enhancement only: one coalesced scroll listener, one
  observer, finite motion, readable no-JS output and complete reduced-motion
  fallback. No parallax, hover scaling or infinite decorative loops.
- Keep `/api/evidence-brief/v2` additive and preserve unversioned V1.
- Explain homepage counters literally: documents, distinct sources, public
  evidence routes, and zero published full third-party transcripts.
- Canonical public repository is `https://github.com/offflinerpsy/base2026`;
  the former LogicCrafts repository is legacy history, not current authority.
- Never publish the separate private capture Worker, raw media, transcripts,
  secrets, operational logs or generated release artifacts.

## 2026-08-28 — Base2026 category, design authority and research spending

- Position Base2026 as an **open video research engine** and **source-first
  evidence library for short-form expert video**.
- Keep “Search what experts actually said” as the H1. Treat Cloudflare as
  technical proof and operating advantage, not the primary user benefit.
- Do not claim generic video intelligence, AI-visibility monitoring, complete
  TikTok coverage, perfect transcription, guaranteed rankings or live MCP.
- Preserve `b26-independent-v1` as the only public production visual authority.
  Historical design assets are quarantined and may be retired only after
  dependency proof and separate review.
- DataForSEO has no arbitrary per-project dollar ceiling. Every paid request
  must still have a concrete decision, current price check, bounded payload and
  durable receipt. The first positioning packet cost `$0.077`.
- Strong evidence maps outrank bulk thin-page generation as the first organic
  growth wedge.

## 2026-08-26 — Capture retries must be fair, bounded, and private

Decision: Cloudflare's five-minute capture scheduler must not use oldest-row selection alone. Fresh zero-attempt TikTok candidates rank before due retries; failed captures back off for 15, 30, then 60 minutes; attempt four transitions the individual source and private registry to held review. Retry state is durable in private D1 and its source transition/audit receipt is atomic. Rows with exhausted attempt counts are ineligible even if damaged legacy state leaves their status as `awaiting_capture`.

Reason: three historical Player API failures were repeatedly selected, starving the new Cloudflare discovery backlog and wasting container/browser allowance. The repair is migration-forward only (`0013`, `0014`), affects exactly those three historical incident rows, and changes neither public content nor `PUBLIC_RELEASE_ENABLED=false`.

## 2026-08-23 — Operate private discovery/acquisition cloud-only in v0.5.2

Decision: the private v0.5.2 Worker is the authoritative discovery/acquisition edge. It uses bounded Browser/Player/Container execution with `*/5 * * * *` capture/reconcile and `0 10 * * *` discovery; the local adapter and Base2026 LaunchAgents remain off. The direct manual Container endpoint, paid fallback, AI Gateway and broad `PUBLIC_RELEASE_ENABLED` gate remain disabled. ChatGPT is manual owner-only and never a scheduler.

The `19:56Z` run admitted 21 of 135 discovered rows from 19 creators and scheduled capture completed 3/3 attempts. A `20:01Z` cron then captured 2 of 3 attempts and left one private retry; registry/media/AI counters therefore moved to 12 captured / 9 admitted, media 201 and five transcription jobs at the restored 7,500-Neuron cap. Monthly accounting remains below the 80% hard hold, and no raw browser output, media, transcript, cookie, prompt or provider response may leave private storage. Public projection remains exact-tuple and owner-authorized only; public D1 did not change. Read live receipts before each decision.

Reason: v0.5.2 provides a bounded cloud acquisition path without relying on the Mac while preserving private D1/R2 state, retry/hold semantics, budget accounting and the existing public/private release boundary. Local plists and the prior Worker remain rollback material, not active production schedulers.

## 2026-08-23 — Make dispatch and daily-cap recovery durable; enforce one private local boundary

Decision: a reconciler may recover only stale dispatch claims, never a fresh `dispatching` claim. A `queued + pending` outbox mismatch is explicitly repaired and republished. Workers AI soft/hard-cap deferrals record the current UTC budget date, do not consume an execution attempt, and remain held until a later UTC date. Legacy cap-loop rows with exact cap receipts are repaired to the same state. Broad public release remains disabled.

Decision: every directory and regular file under the exact validated `PRIVATE_BASE2026_WORK_INBOX` root is private by construction (`0700`/`0600`), with symlinks and non-regular artifacts rejected. This applies equally to media, raw transcripts, metadata, Luna packets, work orders, indexes, status files, logs and receipts; high-throughput concurrency is not permission to weaken the filesystem boundary.

Reason: the live audit found one Queue/reconcile race-stranded capture job, 31 same-day AI cap-loop jobs, and 767 local private entries with overly broad modes. Worker v0.4.2 recovered the jobs without spend or data loss, the whole private root was normalized, and regression/live checks now show zero outbox inconsistencies, wrong modes, symlinks or owners.

## 2026-08-22 — Scale private intake by batching; keep semantic and public gates exact

Decision: remove arbitrary one-source and 100-source daily ceilings. A daily Luna Max run admits the full fresh unseen set through repeated exact allowlist waves of at most 100 IDs, stages audio with four download workers, and transfers independent Cloudflare batches of at most 10 sources / 50 MiB. Workers AI may durably queue overflow but must stop at the existing 7,500/9,000 daily Neuron limits without paid fallback. Luna processes all currently ready sources in batches of at most 10.

High throughput applies to discovery, download, private storage, transcription and review; it does not authorize broad publication. Each evidence excerpt must be an exact continuous transcript span. Failed evidence remains held, and public projection still requires the exact reviewed source, newest release, private materialization and manifest tuple while `PUBLIC_RELEASE_ENABLED=false`.

Reason: the live batch pass admitted all 210 unseen candidates, uploaded 178 after retry, held 32 acquisition failures privately, reviewed 31 completed sources, published 22 evidence-valid sources and held nine weak ones. The public corpus rose to 2,129 documents / 1,548 unique TikTok videos without exposing raw transcripts or private artifacts.

## 2026-08-22 — Enable exact public projection; keep broad release off

Decision: allow one owner-authorized, evidence-admitted private import at a time to cross from `base2026-pipeline-control` to public Worker `base2026` through the named `PublicProjectionEntrypoint` service binding. The public DTO contains only source attribution plus one to three admitted claim/evidence cards. It must not contain private source text, raw transcripts/captions, prompts, questions, local paths, contacts, credentials, or unrelated packet fields.

Every projection is keyed by exact source, release, import, manifest, content hash, and actual private importer receipt. Dispatch uses a bounded recoverable lease; public D1 writes are atomic and idempotent; exact rollback removes only its projected cards/search rows. A corrected manifest may be applied only after the prior projection for that source is rolled back. `PUBLIC_PROJECTION_ENABLED=true`; the unrelated broad `PUBLIC_RELEASE_ENABLED` gate remains false.

Historical pilot posture used one daily Luna Max automation with a hard one-source cap and failure-only notifications. That throughput cap is superseded by the batch decision above; the exact public projection, evidence verification and live-search receipt requirements remain in force. The older 30-minute Sol automation remains paused to control token use.

Reason: the real end-to-end proof published source `7673404909294800145` with one exact evidence card, increased public video count from 1,525 to 1,526, preserved the site asset hash, and passed replay/privacy/rollback tests. This closes the missing public handoff without weakening the existing public/private boundary.

## 2026-08-22 — Operate v0.3.1 privately; keep Container, AI Gateway, and public release off

Decision: operate the implemented Cloudflare pipeline with intake, reconciler, local adapter, Workers AI, manual ChatGPT courier, deterministic private import, and retention enabled. Keep `CONTAINER_CAPTURE_ENABLED=false`, `AI_GATEWAY_ENABLED=false`, and `PUBLIC_RELEASE_ENABLED=false`. The local LaunchAgent runs every 15 minutes without a model or Codex heartbeat; it may upload only authenticated private artifacts and may never cross the release owner gate.

Workers AI remains bounded by D1 preflight accounting at 7,500 soft / 9,000 hard daily Neurons, one AI message at a time, no paid fallback, and a UTC reset wait state. The exact semantic allowlist uses `@cf/meta/llama-3.1-8b-instruct-fp8-fast`; aliases and the former 70B model fail closed. The locally verified Container image is retained only as a POC because remote deployment can introduce metered usage. AI Gateway is deferred because the current Workers AI binding plus D1 hard gate supplies the required zero-incremental-spend stop without adding another active dependency.

Execution receipt: Worker version `905ae9e4-fe0f-47fb-b3c1-06dd6bfe7319`; migrations `0001`-`0007`; exact synthetic release `072a76060006a4212889af4ccc368c616fa30183`; private materialization `a6c7ea121154b043253337b72ff11e1e005f8627`; exact 8B live receipt `01b7214ee6ba289a38acd7a0300d8d0e9cde015f` at 22 Neurons; one held-private card; all public flags `0`; idempotent duplicate review/import; contradictory review rejected; public Worker/data/homepage unchanged.

Reason: this is the smallest supported system that achieves unattended durable work inside current included allowances while keeping private evidence, ChatGPT Terms compliance, public publication authority, and spend control independently fail-closed.

## 2026-08-22 — Use a separate Cloudflare-first private control plane; do not automate ChatGPT web extraction

Decision: the target Base2026 evidence/TikTok pipeline uses a separate private Cloudflare Worker, D1, Queues, Workflows, short-lived private R2, Workers AI, and AI Gateway spend controls. It must not be added to the public Base2026 Static Assets/search Worker or share the public Evidence/Outreach databases. Existing deterministic admission, importer, publication, release, and live-verification gates remain authoritative.

Workers AI is the Cloudflare-native unattended semantic lane and must stop below the daily free allocation through an AI Gateway spend rule plus a D1 preflight ledger. ChatGPT Pro may be tested only through supported Scheduled Tasks and Google Drive/Sheets actions; it is optional and cannot be a critical dependency. Cloudflare Browser Run, Playwright, CDP, or another program must not sign in to ChatGPT or extract its responses. TikTok acquisition stays on the existing local adapter until a credential-free, bounded Cloudflare Container POC proves reliable reachability and included-budget operation.

Reason: the current local pipeline already has useful stage and evidence contracts, but its full automations are paused and its controller/courier paths have locking, transactional, validation, selector, and test gaps that should not be copied. Cloudflare's paid-plan allowances can host the durable controller at current volume, while OpenAI's individual Terms of Use prohibit automatic/programmatic extraction of ChatGPT output. Keeping private control, semantic execution, and public projection separate preserves the established publication boundary and gives every new component a shadow, budget, quality, rollback, and owner-authorization gate.

## 2026-08-21 — Keep Outreach intelligence in a separately admitted search collection

Decision: expose only explicitly reviewed Outreach findings through a future separate D1 database/binding and the fixed logical index `base2026_public_outreach`. Preserve the current reviewed evidence corpus in `base2026-public-search` / `base2026_public_tiktok`. A browser request may select only the two server-owned collection identifiers. The All view returns two labelled result groups and never merges their ranks or scores.

Publication requires a separate admission row that pins the normalized source by SHA-256 and records `approved_public`, reviewer, timezone-aware review time and policy version. Workbook score, verdict or workflow status cannot substitute for admission. Contacts, emails, comments, owner notes, client/ACQ3/Gmail/Search Ops/GSC data, queues, backups and operational records are prohibited. Research workers remain frozen. This decision authorizes local fixtures, tests and isolated candidates only; it does not authorize a real-row import, Cloudflare resource/binding, deployment, Sheet write, commit or push.

Reason: the live workbook contains 34 tabs spanning multiple security domains and has no explicit public-release field. A separate data and rollback boundary prevents a heterogeneous private operations system from weakening the existing reviewed public evidence contract.

Execution closure: after explicit owner release authority, semantic review admitted 78 of 400 mechanically eligible candidates and excluded 322 weak, redundant, promotional, private or operational rows. The collection is live in isolated D1 `base2026-outreach-search`; Evidence and Inbox remain separate. Future workbook changes do not inherit publication permission and must repeat the semantic admission and controlled-release gates.

## 2026-08-20 — Establish `b26-independent-v1`; do not revive an Alex-coupled visual candidate

Decision: Base2026 visual recovery must use one independent Base2026-only contract at the generator/release boundary. No historical complete candidate may be restored verbatim because the inspected Stitch, Personal V4, shell-consistency and startup variants all retain either retired Alex Personal shell/footer authority or the warm/orange legacy visual treatment. The only recoverable historical input is the dense research-product component discipline, not its visual brand or markup.

The contract and migration matrix are canonical in `BASE2026_DESIGN_RECOVERY_AUDIT_2026_08_20.md`. It protects D1 search, form intake, public data, external attribution, canonical/robots/redirect and deployment boundaries. This decision authorizes a local isolated candidate only; it does not authorize deployment, indexation, Cloudflare/D1/DNS/GitHub change, data import or Git publication.

## 2026-08-19 — Separate Base2026 from Alex Personal with Workers Static Assets and D1

Decision: target `https://base2026.dev/` as the independent Base2026 product origin on Cloudflare Workers Static Assets, with public search implemented by a Worker and D1 FTS5. Keep Alex Personal WordPress at `https://aggressorbulkit.online/` on the existing VPS. After the new origin passes preview and cutover gates, preserve old Base2026 paths with path-preserving permanent redirects from `/knowledge/*` to the new domain. Keep a Worker-to-VPS Meilisearch proxy only as a bounded fallback, not the preferred final state.

Reason: the Base2026 public release is predominantly a generated static artifact and fits current Cloudflare Free asset limits, while D1 supports FTS5 and the present public search corpus is small enough for a measured prototype. This creates a real failure and hosting boundary between the startup and the agency WordPress site without moving WordPress or publishing the private build pipeline.

## 2026-07-20 — Scheduled Base2026 checks must start from a minimal environment

Decision: the `com.base2026.hermes-tiktok-check` LaunchAgent must execute through `/usr/bin/env -i` with only the explicit runtime variables required by the check-only worker. It must not inherit arbitrary GUI-session secrets.

Reason: the P0 audit found an unrelated sensitive environment variable inside the loaded job. The worker does not need it, and inherited credentials increase exposure without adding pipeline capability.

## 2026-07-04 — Add WordPress/CMS as a private-first Base2026 vertical under web development

Decision: Base2026 should treat WordPress/CMS implementation insights as a separate source/category vertical under the broader web-development expansion, rather than burying them inside generic SEO. Initial anchors are `@iamdandavies` as a WordPress-focused creator and `@webhivedigital` as an SEO/WordPress hybrid source. The vertical remains private-first until reviewed source text, exact-evidence insight cards, and the existing indexation/release gates approve any public promotion.

Reason: A 2026-07-04 audit found that Base2026 already has a staged WebDevLog category, 61 exact WordPress public source-record matches, 13 WordPress/CMS topic rows, and multiple existing WordPress topics/cards. The current signal is real but scattered across SEO/CMS/web-dev topics, so a canonical vertical prevents routing loss while preserving the thin-content/publication safeguards.

Execution note: the first cards-only batch was completed on 2026-07-04 with 12 exact-evidence WordPress/CMS `insight_card_candidate` rows promoted to `reviewed` in local SQLite, 0 promoted to `approved`, and no public pages/deploy/indexation/outreach. Batch #2 was completed the same day with 12 more exact-evidence rows (10 from `@webhivedigital`, 2 from `@iamdandavies`) promoted only to `reviewed`, bringing the two-batch private reviewed WordPress/CMS card set to 24 rows with 0 public/approved promotion from these batches.

## 2026-06-26 — Hold templated city/niche AI visibility pages out of the index until evidence-approved

Decision: Broad Base2026 AI visibility hub pages may remain indexable, but generated city/niche audit pages must render `noindex,nofollow` and stay out of the sitemap unless a page is explicitly evidence-approved with unique local source material.

Reason: QA showed the current 16 California city/niche pages are mostly templated swaps after normalizing city and niche terms. Indexing them would create doorway/thin-content risk and conflict with the public research/proof layer.

## 2026-06-23 — Keep Base2026 discovery state out of crawlable query URLs

Decision: canonical Base2026 search/discovery URLs should be `/knowledge/` plus client-side `#search?...` state, not `/knowledge/index.html?...` or other crawlable query variants. Generated static entity pages should link back to the search workspace through hash state, while sitemap generation remains limited to self-canonical, indexable HTML files.

Reason: GSC/Ahrefs already surfaced duplicate/canonical noise around `/knowledge/index.html` and query-state search routes. Hash state preserves user navigation without asking crawlers to spend budget on filter/query combinations that canonicalize back to the search root.

## 2026-06-23 — Historical Logic Crafts GitHub home (superseded 2026-08-28)

Historical decision: use `logic-crafts` as the company GitHub organization for Base2026 and related startup assets. This was superseded on 2026-08-28; the canonical repository and local `origin` are now `https://github.com/offflinerpsy/base2026`.

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
# 2026-07-20 — Stable creator routes and recoverable stale-lock quarantine

Decision: when a TikTok handle route stops resolving, discovery may use a verified stable TikTok channel-ID URL in the ignored private creator configuration while preserving the internal creator ID and documenting any handle transition. A stale worker lock may be moved to an ignored backup only after its PID is absent and no process holds the file.

Reason: public handles can change independently of Base2026 identity, and a dead handle must not keep the whole check-only controller yellow. Stable channel routing restores deterministic discovery without silently rewriting public attribution. Recoverable quarantine removes an ownerless controller block while preserving forensic evidence.
# 2026-07-20 — WordPress V4 footer is the only global footer authority

Decision: the canonical global footer is the original five-column WordPress V4 footer used by Personal Home, Services, Pricing and About. Base2026 must consume that footer template and a footer-only parity stylesheet. The compact Personal/Research registry footer must not be used as the global footer or promoted back into WordPress.

Reason: the compact footer removed the commercial service architecture, CTA ladder, Base2026 project links and established WordPress visual hierarchy. Sharing the canonical WordPress markup while isolating its CSS from Base component styles preserves one recognizable site system without allowing either product shell to overwrite the other.
## 2026-08-19 — Keep WordPress and Base2026 operationally separated

Decision: Base2026 production is `base2026.dev` on Cloudflare Workers Static Assets plus D1 FTS5; Alex Personal remains `aggressorbulkit.online` on the VPS. Preserve the VPS Base2026 release and Meilisearch as rollback-only infrastructure during a stability window rather than deleting them at cutover.

Reason: the verified Cloudflare release removes the startup runtime from the WordPress/VPS serving path while retaining a recoverable fallback.

## 2026-08-20 — Base2026 owns an independent startup shell

Decision: on `base2026.dev`, the Base2026 startup header, footer and product navigation supersede the former shared WordPress V4 shell. The Alex Personal shell remains authoritative only on `aggressorbulkit.online`. Base2026 may name Alex Yarosh as the factual founder, but it must not link into or sell personal services from the startup product surface.

Reason: startup-program reviewers need a coherent product property with clear open-source, roadmap, methodology, support and partnership paths. Sharing the personal commercial shell made Base2026 look like an agency funnel and blurred the operational domain separation already established on Cloudflare.

## 2026-08-20 — Startup proposals use a separate private inbox

Decision: Support and Partner forms write to a dedicated private D1 binding, `base2026-inbox`, never to the public search database. The Worker validates exact origin, structured fields, consent, elapsed time and a honeypot; it stores neither IP address nor user agent and removes untouched new proposals after 90 days. File uploads and secrets are forbidden.

Reason: application and collaboration intake is operational/private data, not public evidence. A separate database and narrow retention boundary reduce accidental publication and limit collected personal data.

## 2026-08-20 — Legacy commercial pSEO pages do not ship on the startup domain

Decision: generated pages containing WordPress `admin-post.php` commercial forms and the matching personal-shell assets are excluded by the final Cloudflare release builder. The release fails closed if personal origins, shell markers, WordPress forms or retired service-route links remain.

Reason: these pages are part of the founder's personal services funnel and conflict with the standalone startup positioning. Keeping the exclusion in the final release boundary protects current production while the older source generators are refactored separately.

## 2026-08-20 — Google Workspace is the sole Base2026 mail authority

Decision: `base2026.dev` uses the existing paid Google Workspace Business Starter tenant for both inbound and outbound mail. `hello@base2026.dev` is the primary Gmail identity and `offflinerpsy@gmail.com` remains a retained sender/recipient identity in the same mailbox. Cloudflare Email Routing is disabled. Root mail DNS must not mix providers: MX points only to Google; SPF authorizes Google; DKIM uses Google's generated 2048-bit `google` selector; DMARC starts at monitoring-only `p=none` until real reports justify enforcement.

Reason: the owner needs one Gmail mailbox with a selectable branded From address, not forwarding-only infrastructure. A single provider removes ambiguous MX routing, while SPF, DKIM and monitoring DMARC establish the deliverability baseline without prematurely rejecting mail.

## 2026-08-23 — Enable fenced automatic Cloudflare-only publication

Decision: valid `publication_eligible` packets may publish automatically through policy `base2026.machine-publication.v1` (owner ref `owner-20260823-base2026-auto-publication-v1`, SHA-256 `b37c900a03eb63252c7736c2197f2be1eae3f117eae76914f3cbef306d89e573`, batch10, attempts4). `AUTOMATIC_PUBLICATION_ENABLED`, `IMPORT_ENABLED` and `PUBLIC_PROJECTION_ENABLED` are true; broad `PUBLIC_RELEASE_ENABLED=false` remains intentional, and `LOCAL_ADAPTER_ENABLED=false`. Malformed, privacy-risk and mismatch states fail closed automatically; valid eligible packets do not require user manual review.

Receipt: public Worker `790e21d6-f341-4265-ae0c-7dc536a32495` (rollback `86faccf2-e986-4437-a39a-4b3d66a1883f`), private Worker v0.6.1 `70fd6e68-ea54-462d-ba27-e3b1a66fa997` (pre-automatic rollback `f9e4a494-9780-4bd2-bb33-5b7f5a068f81`), and private migrations `0011`/`0012` applied with none pending. The first run attempted3/applied2/already_public1/retry0/held0/`hard_hold=false`; new public IDs were `7271043105799834912` and `7402026836600851717`, while `7662399921894591761` was already legacy public and fixture `7999999999999999933` was absent. Post-release counts were public 2,136 documents / 1,557 videos / 33 projection receipts / 44 cards / zero full transcripts; private imports35 / applied projections33 / ready0 / automatic receipts 2 applied + 1 already-public / problems0; registry4123 / eligible209 / invalid eligible0.

Reason: exact eligibility, synthetic-fixture exclusion, RPC verification, full-transcript exclusion, fenced leases, global hard-hold stop and exhausted-lease terminal hold preserve the public/private boundary while removing a manual step only for already verified packets. Observe the first full post-release daily discovery cycle at `2026-08-24 10:00 UTC`; it is not yet observed.

## 2026-08-26 — Use curl-cffi only as a bounded TikTok transport compatibility layer

Decision: the private Container image pins yt-dlp with its curl-cffi transport
and fixed Chrome TLS impersonation. The only allowed input remains a
D1-authoritative canonical TikTok video URL reached after Player API and
Browser Player-API fallback. Cookies, authenticated accounts, browser profiles,
proxies, arbitrary URLs, and public Container endpoints remain prohibited.

Reason: a live local-equivalent diagnostic showed TikTok rejecting the
Container's unimpersonated webpage negotiation, while the same bounded request
with curl-cffi resolved a valid audio format. The live private reconciliation
then stored one new media artifact. This fixes compatibility without turning
the pipeline into account automation or widening the data boundary.

## 2026-08-28 — Standardize public SEO on extensionless canonical URLs

Decision: `base2026.dev` uses extensionless public canonicals. Sitemaps,
internal links, canonical tags and Cloudflare Static Assets redirects must
resolve to the same non-redirecting URL. A release fails when a sitemap URL
redirects or its final canonical differs.

Reason: the former `.html` sitemap URLs redirected to extensionless pages that
canonicalized back to `.html`, splitting crawl and canonical signals across
more than 1,600 URLs.

## 2026-08-28 — Make eligible D1 projections continuously indexable

Decision: every applied, public-safe automatic projection receives a stable
attributable HTML page and an entry in `sitemap-dynamic.xml`. Pages remain
excerpt-only and must not expose raw transcripts, media, logs, credentials or
private D1/R2 artifacts.

Reason: automatic publication previously updated D1 search without creating a
crawlable public URL, so new evidence could not participate in organic search
or citation discovery.

## 2026-08-28 — Keep DataForSEO measurement explicitly cost-gated

Decision: documentation discovery and free first-party measurements are the
default. A paid DataForSEO request may run only after current-price verification,
explicit approval, one mutually exclusive decision packet and a hard `$0.10`
ceiling.

Reason: the project is no-budget by design; measurement must answer a concrete
decision and must not become an open-ended crawl or keyword-spend loop.

## 2026-08-29 — Publish only reviewed public insight cards

Decision: the Cloudflare release artifact may contain only insight-card rows
that are explicitly public, reviewed and governed by the public policy. Rows
marked `needs_review`, non-public or governed by another policy remain outside
the artifact even when older local exports include them. The builder and
artifact gate fail closed on a contradictory row.

Reason: the public dataset landing exposed that an older static file mixed 524
review holds with 1,939 public cards. Filtering only in the UI is insufficient;
the publication boundary must be enforced before files enter the artifact.

## 2026-08-29 — Earn contextual references instead of building a link network

Decision: an owned-domain Base2026 reference must live on a standalone,
truthful page that is useful without the link, use one natural branded anchor,
be internally discoverable and appear in a valid sitemap. Footer/sitewide
links, hidden orphan pages, reciprocal link patterns and keyword anchors are
forbidden. Paid publisher tests are for relevant referral reach only, require
explicit budget approval and use `rel="sponsored"` or `nofollow`; buying links
for ranking is forbidden.

Reason: contextual editorial references can document real implementation while
preserving user value and search-engine policy. A cross-domain owner network or
paid dofollow package would add risk without proving qualified traffic.

## 2026-08-29 — Syndicate reviewed journal releases without a preview handoff

Decision: after a Base2026 journal article is reviewed and live on its canonical
URL, the operator may complete the Medium publish action and publish adapted
announcement posts to Alex Yarosh's X and LinkedIn accounts without a separate
preview or final-click handoff. Preserve the Base2026 canonical on syndicated
copies and use the canonical URL in social posts. This standing scope does not
authorize paid promotion, DMs, comments, replies, account changes or unrelated
content.

Reason: the owner explicitly requested autonomous publication of the current
article and the same bounded distribution pattern for future reviewed releases.
Removing the repeated final-click handoff closes the editorial pipeline while
keeping unrelated representational actions outside scope.

## 2026-08-30 — Separate original editorial publishing from video projection

Decision: reviewed original articles use the additive public editorial D1
tables, `/blog/<slug>/`, a signed private ingress and existing service binding.
They do not write into the video corpus or expose a public admin endpoint.
Structural validation and a separate semantic/privacy review must cover one
exact normalized payload hash. Atomic conditional revisions and receipts make
the same publication idempotent; uncertain writes require inspection before
retry, and corrections require explicit compare-and-swap authorization.

Reason: a useful original article can publish without a full-site rebuild or
manual SQL while preserving attribution, reproducibility and the raw-transcript
boundary. Serving/publication runtime is Cloudflare-native; local Codex review
and credential access are not a cloud-only authoring service.

## 2026-08-30 — All growth-office execution seats use Sol Max

Decision: the owner's latest explicit model override replaces the earlier
Luna/Terra staffing for this office. Every assistant/executor uses
`gpt-5.6-sol` with `max` reasoning; root owns architecture, integration,
semantic review and release. Private pipeline maintenance stays with its
separate owner and worktree. This does not replace the deployed Cloudflare
transcription model or change global routing configuration.

Reason: the owner explicitly requested the same maximum-capability route for
all office seats. Scoped ownership and one publisher prevent concurrent agents
from overwriting each other's files or duplicating an external write.

## 2026-08-30 — Run a reviewed editorial/X loop, not a bulk posting quota

Decision: extend the existing six-hour growth heartbeat to source research,
original article preparation, separate exact-hash review, signed data-only
publication and X distribution/measurement. Reconcile completed/in-flight
receipts first; ordinary runs must not mutate Worker code, schema, design,
DNS, Git, secrets or intake policy. Publish a useful article when warranted,
not filler to reach a quota. Preserve free-plan capacity and count already
published/scheduled X content before refill.

Reason: one connected repeatable path is safer than several competing
schedulers. A configured future run, submitted URL, queued post, social view
and attributable website action are distinct states with different receipts.

## 2026-08-30 — LinkedIn uses Computer Use and its action-time gate

Decision: the owner's newer Computer Use-only route supersedes the LinkedIn
part of the August 29 no-final-click-handoff decision. Do not use Buffer,
DOM/CDP, another login route or anti-bot concealment. Prepare drafts safely;
the final Computer Use Post requires its action-time confirmation. A menu-only
readback without a usable composer is not permission to click blind.

Reason: preserve the verified account and follow the selected interaction
channel after repeated security checks. X's reviewed official Buffer route
and Medium's normal-browser publication route are unchanged.
## 2026-09-03 — SEO releases preserve held features and explicit member assets

Decision: when `main` contains a reviewed but production-held feature, a
different authorized repair may be deployed as a selected patch over the exact
last-live source base. The Git source still integrates normally, but the
production build must not activate the held feature, migration or route. Any
member-enabled Base2026 release must pass `--members-workspace`, prove all three
member UI assets are present and live-check `/my-research/` plus its private
headers. Builder canonicalization and runtime shell validators require a shared
compatibility test.

Reason: the first SEO canary correctly failed the live gate after an omitted
member build flag and a source-shell assumption collided with extensionless
link normalization. Immediate rollback prevented the defect from remaining
live; explicit release invariants prevent recurrence without activating the
separately held Claim Receipt contour.
