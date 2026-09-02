# Next Action

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

PR34 is merged and Worker `f8781f4d-30fd-4d70-ab96-a4e8d718226a` is live at
100%. API, MCP, integrations, member-auth preservation, rate limiting, D1
counts and desktop/mobile browser behavior passed live readback. IndexNow
accepted exactly `/mcp` and `/integrations`; this is not indexing or traffic.

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
