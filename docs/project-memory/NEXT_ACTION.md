# Next Action

## Source-backed Brief candidate — September 4, 2026

The isolated branch `codex/base2026-source-backed-brief-20260904` adds the
public `/tools/source-backed-brief/` utility on top of current `origin/main`
at `946b771fd`. It accepts a question, audience, format and up to eight
already-selected canonical public record/source IDs, then performs bounded
anonymous `get_source` lookups and renders the same deterministic
record/creator/original-source/excerpt/unknowns snapshot as Markdown or JSON.
It does not infer truth, consensus or independence, call an LLM, read private
or raw media/transcript fields, write D1, or deploy. Evidence Search and the
resource hub carry one contextual link each; Source Diversity behavior and
member/auth bindings remain unchanged.

Next action: root command center reviews the exact implementation commit,
focused tests and public-boundary receipt. If approved, build a fresh reviewed
Cloudflare candidate and authorize deployment separately, then verify the live
route, API readback, canonical, sitemap, mobile behavior and the four bounded
analytics events. Do not treat this local candidate as live traffic or
indexing evidence. Details:
[HANDOFF_2026-09-04_SOURCE_BACKED_BRIEF.md](HANDOFF_2026-09-04_SOURCE_BACKED_BRIEF.md).

## Evidence Search intent aligned; acquisition measurement active — September 4, 2026

Public Worker `327a21a5-ca54-457c-8099-aa2447a7fe1a` now serves the existing
Evidence Search with the truthful user job “search inside expert videos” in
its title, description, H1 and WebApplication data. The successful deployment
uploaded one changed asset; health and the adjacent tool/API routes pass. The
immediate rollback is `da308428-5609-43ab-8b31-88deb124dc7b`.

Next action: compare CTR and activation against the existing baseline, publish
the reviewed Evidence Pulse worked example and complete Source-Backed Brief.
Treat the larger `tiktok transcript generator` demand as a separate gated
product build, never as a keyword-only landing page. Details:
[HANDOFF_2026-09-04_EVIDENCE_SEARCH_INTENT_RELEASE.md](HANDOFF_2026-09-04_EVIDENCE_SEARCH_INTENT_RELEASE.md).

## Source Diversity Check and Evidence Pack are live — September 4, 2026

`/tools/source-diversity-check/` is live on public Worker
`327a21a5-ca54-457c-8099-aa2447a7fe1a`. It performs bounded public
`get_source` lookups, separates record/original-source/creator counts, keeps
unresolved states visible, and exports deterministic Markdown/JSON without a
truth, quality, consensus or independence score. PR46 merged the tool source;
PR47 merged a dependency-free public Evidence Pack into the canonical GitHub
repository. The one new canonical URL received one accepted IndexNow request;
that is discovery notification, not indexing or traffic proof.

Next action: run the 72-hour acquisition experiment from the verified
`257 impressions / 0 clicks / position 14.9` baseline. Publish one
platform-native worked example from Evidence Pulse #001, measure non-owner
tool runs and referral sessions, and build the deterministic Source-Backed
Brief as the next product step. Do not create keyword-swapped pages or count
impressions, directory submissions or IndexNow acceptance as users. Details:
[HANDOFF_2026-09-04_SOURCE_DIVERSITY_PRODUCTION_RELEASE.md](HANDOFF_2026-09-04_SOURCE_DIVERSITY_PRODUCTION_RELEASE.md).

## Crawl-derived SEO/GEO repair live — September 3, 2026

Worker `99849d8e-802d-4e8e-a840-8d352f176da6` is live at 100%. It preserves
API/MCP, Evidence Search, Google member auth/My Research and the public/private
boundary while fixing verified source-title/H1, sitemap ownership, canonical
link, unique source descriptions, favicon and structured-data defects. The first invalid canary was rolled
back and must never be restored. Exact audit, artifact, test, rollback and live
readbacks are in
[HANDOFF_2026-09-03_DATAFORSEO_SEO_GEO_PRODUCTION_RELEASE.md](HANDOFF_2026-09-03_DATAFORSEO_SEO_GEO_PRODUCTION_RELEASE.md).

Next action: measure Google/Bing discovery, referral traffic and real API/MCP
use from this fixed baseline. Do not treat crawler spelling/image-title flags
or crawler-defined orphans as defects without a reproducible page/link example.
Do not widen programmatic indexation. Claim Receipt migration and deployment
remain separately held on their existing eligibility gate.

## Claim Receipt Ledger source integrated and held — September 2, 2026

PR36 is merged to public main at
`25bca067514fb5efd9bbc84c36c6b3cd73f43d3f`. The reviewed source adds the
additive public D1 migration `0005_claim_receipt_ledger.sql`,
the service-binding-only admission/read/rollback lane, the strict read route,
deterministic public-D1 readback exporter, sidecar publication gates, schema,
API and correction documentation, and focused tests. No public migration,
Worker deploy, sidecar publication, sitemap submission or external mutation
was performed.

The first independent review found five release blockers and all five were
fixed before integration: secondary exporter privacy scanning, shared
JavaScript/Python timecode canonicalization, a broken documentation link,
concurrent rollback idempotency, and missing-table fail-closed behavior. The
reviewer returned GO for commit/push/merge only as an undeployed held
candidate. Full verification now passes 632 Worker tests, 173 Python tests,
TypeScript typecheck and local migration application.

Next action is not deployment. The route remains fail-closed until an exact
ten-row public-D1 candidate is available. The current live public-D1 check
found zero applied cards whose
normalized topic is `internal-linking` or `internal-linking-*`; no synonym
inference, relabeling or padding is allowed. The remaining gate is the
private-owner typed wrapper and its review/audit integration in the protected
pipeline-control repository, followed by separately authorized migration,
deployment and public-D1/export readbacks.

## Public API/MCP release — September 1, 2026

PR34 is merged and its API/MCP capabilities remain live through current Worker
`99849d8e-802d-4e8e-a840-8d352f176da6`; prior Worker
`f8781f4d-30fd-4d70-ab96-a4e8d718226a` is the healthy rollback. API, MCP,
integrations, member-auth preservation, rate limiting, D1 counts and browser
behavior passed live readback. IndexNow accepted exactly `/mcp` and
`/integrations`; this is not indexing or traffic.

Next action: measure discovery and real tool use, then build the bounded Claim
Receipt Ledger canary from reviewed public evidence. Keep it in a separate
implementation/review contour and do not publish or auto-index claims that fail
source integrity, attribution, limitation or public-boundary gates.

The integrated reliability manifest is an observed, redacted receipt with
`release_ready=false`; its unresolved commit/binding and private-incident
recommendations remain holds. Channel reconciliation and member measurement
contracts are staging/read-only artifacts, not external-action permission.

The reviewed evidence-map canary generator, public-safe config, checker and
visual template are integrated but no generated pages or sitemap overlay have
been materialized in this candidate. Re-fetch current public D1 topic exports
into an ephemeral location before any approved generation; keep the canary
outside the live release until root completes the final review.

The public API/MCP candidate section is complete. Its source, artifact, live
version, tests, binding readback and rollback are recorded in
[the production handoff](HANDOFF_2026-09-01_PUBLIC_API_MCP_PRODUCTION_RELEASE.md).

## Evidence Search production release — September 1, 20:10 UTC

Worker `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e` is live at 100% with
`/tools/evidence-search/` returning HTTP 200. Real public D1 search, self
canonical, indexability, hub sitemap, no-JS fallback, mobile render, provenance
links, claim boundaries and zero-console-error browser QA passed. Member-auth,
private headers and both `/guides` aliases remain intact. IndexNow accepted the
single new URL with HTTP 200; indexing and traffic remain unproved.

Release details are in
[HANDOFF_2026-09-01_BASE2026_EVIDENCE_SEARCH_PRODUCTION_RELEASE.md](HANDOFF_2026-09-01_BASE2026_EVIDENCE_SEARCH_PRODUCTION_RELEASE.md).
Safe rollback is `5a326a64-c755-4036-93af-1a1809e0aeb6`; never restore the
regressed `da381253-2427-4b8d-9834-56ba86f46b9b`. Do not redeploy from the
dirty candidate without freezing an exact reviewed tree.

Next product action: measure discovery and use the live tool as the destination
for the already reviewed supporting editorial package. Next source action:
review the exact 45-file public candidate before any Git staging/commit/push.

## Member auth plus guide alias checkpoint — September 1

Worker `5a326a64-c755-4036-93af-1a1809e0aeb6` is live at 100%. It retains the
exact reviewed member asset tree `1039f92aeae0195dee2dfb4c63bc905e41cee2fe41e60fe177b34785713fe361`,
all member bindings and secrets, and adds only `/guides` and `/guides/` 308
redirects to `/topics/`. Member/public route readbacks pass. The safe rollback
is member version `5b72e529-a3af-467e-b6f1-bada347129d1`; never restore the
regressed guide release `da381253-2427-4b8d-9834-56ba86f46b9b`.

The post-deploy full observability readback has invocation logging and log/trace
persistence off, traces disabled, Worker Logpush off and no tail consumer.
`redact_query_string` is false, so do not claim query redaction; account, zone
and instant Logpush inventory remains unverified under the current OAuth grant.
Private receipt: `auth/20260831/member-guide-alias-hotfix-20260901T1601Z.json`.

Identity A completed real Google login, private save/revisit/export and logout.
Testing allowlist was not changed: the unsaved second row was closed with the
count still at one. Google recognizes identity B and now waits at the owner's
physical password screen. After the owner completes it, finish identity-B
save/revisit/export/logout and cross-user deny without changing scopes, client,
audience or publishing status. No secrets, OAuth codes or visitor data belong
in Git or logs. The v4 shared-header candidate remains local and undeployed.

## Evidence Search integration checkpoint — superseded by live release

The reviewed Evidence Search slice is integrated into this dirty member-auth
candidate as an additive, anonymous and read-only `/tools/evidence-search/`
route around the existing public D1 FTS5 endpoint. The source candidate's
4,248-file tree hash was `40d292499478b88228249f472e071d4393caf208285de6a9303dc030d135c622`;
its implementation, builder and test hashes are recorded in the [integration
handoff](HANDOFF_2026-09-01_BASE2026_EVIDENCE_SEARCH_MEMBER_AUTH_INTEGRATION.md).
The member-auth source, bindings, templates and current live asset
bundle remain otherwise untouched.

The route requests only bounded public metadata from
`base2026_public_tiktok`, caps public title summaries at 360 characters,
keeps missing attribution/original links visibly unresolved, uses fragment
query state, and retains a truthful no-JS fallback. This integration-only state
is retained as history; the production handoff above now controls live claims.
Git source remains uncommitted and must not be treated as synchronized merely
because Cloudflare is live.

## Retained public-office checkpoint

Checkpoint: 2026-08-31 10:17 UTC.
[Current state](CURRENT_STATUS.md) ·
[Closure and receipts](BASE2026_OFFICE_CLOSURE_2026_08_31.md).

PR31 is merged; correction/closure are tracked by PR32. Verify its GitHub
merge receipt before further release; do not preclaim it or rewrite history.

1. Observe deployed private release58 and the ongoing cohort at10:45 UTC; do not repeat
   its completed migration/release as a test. At 10:16, 27 admitted yielded
   6 media, 5 transcripts and one packet/import/verified projection. Keep
   external capture retry bounded and semantic holds fail-closed.
2. Preserve the rollback fence: release57 is the diagnostic rollback.
   Release56 requires zero active capture leases and no reserved, settling
   or uncertain operation. Keep migration0016/ledger; no automatic refund,
   replay, tuple rearming or resurrection. Cleanup pagination/starvation
   needs its separate bounded investigation, not broader deletion.
3. Both archive articles are published revision1, recorded at 09:15:33.466
   and 10:06:01.197 UTC. Do not replay them, the worksheet or completed guide
   acceptances. Corrections need independent exact-payload review and explicit CAS.
4. Comparison is complete; two archive candidates remain: research/expert
   interviews and context-preserving repurposing. They are research tasks,
   not approved publications. The six-hour office should finish useful pending
   work even when guide snapshots are unchanged, with separate author/critic
   and one publisher. Preserve truncation and source/rights caveats.
5. Reconcile existing X IDs before refill. The 08:20 snapshot is four sent/
   five scheduled/one queued thread; no new posts in this closure. Next slot:
   August31 12:30 UTC. The first 24-hour launch window begins19:24 UTC.
   LinkedIn remains Computer Use/action-time Post confirmation, never Buffer/stealth.
6. Keep private fallback at 04:45/10:45/16:45/22:45 UTC and native doctor every
   five minutes. Healthy unchanged checks stop cheaply. External total-outage
   detection is up to six hours plus host availability. Direct GPT Work
   incident delivery is unverified; do not report an unobserved dispatch.
7. Golem remains blocked by Actions startup and unavailable authorized SSH;
   merged code is not a live backlink. Preserve existing contextual references.
   Instagram and dataset mirrors still require access/rights clearance.
8. The orphan enrichment key is retired; 59 others are preserved, not
   recertified. Matching roadmap HTML/JS is live. Do not invent a replacement page.

Public Worker `7522595a-13bf-4437-8955-fd14816b2569` serves tree
`ed0a9371e0471d13006b62b250d458c7f3b3fdbcc8530fc938dd32c758fe46e2`.
Compatible public rollback: `a63f4c74-b6b2-4935-a392-61003d28567a`.
Never restore a pre-guide Worker over guide-kind data. Routine editorial work
does not deploy code or change design, DNS, credentials, budgets or private intake.

## 2026-09-03 — Current SEO/GEO technical state

Public Worker `64c7065b-a4b4-4f31-a2ac-b8a0ccfebff4` is at 100% and serves
artifact `5bbe22a3a6c8276043206bf3e2898b2268a6fd990da997c40d1b57c3c12c516f`.
The clean DataForSEO full crawl finished `4,061` URL states by empty queue with
score `96.22`; broken internal links/resources, 5xx, redirect loops and broken
canonicals were zero. Its one 404 and two redirects were deliberately supplied
wrong probes, not site links. A post-release 20-page DataForSEO probe confirms
the source catalog now has zero duplicate descriptions and zero hard errors.

The final live sitemap has `1,876` unique URLs; all `1,876` return 200, are
indexable and self-canonical. Do not re-add noindex topic/search states merely
to increase page count. The next SEO action is measurement and selective
admission: reconcile GSC crawl/index/click evidence and AI citations, then admit
only complete, materially distinct citation units. PR41 contains the description
fix; PR42 makes future releases fail closed on pagination/sitemap drift.
