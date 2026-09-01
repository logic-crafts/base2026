# Base2026 receipts and workflow states

## Truth hierarchy

For current claims, use this order: live HTTP/Cloudflare/D1/GSC/Bing/audit receipts; AgencyOS tasks/events/artifacts and its readable board; current worktree/Git/handoff; dated project docs; chat history. A board or task status tracks workflow and accountability; a native platform URL, live readback, or search-console result proves the external effect.

## Never collapse states

Keep these transitions distinct:

```text
code:     changed -> committed -> deployed -> live
page:     drafted -> approved -> generated -> live -> in sitemap -> indexed
external: prepared -> submitted/queued -> published/sent -> public URL -> readback verified
```

Google/Bing indexing is an external outcome and may remain asynchronous. `HTTP 200`, sitemap acceptance, IndexNow `200/202`, a draft, a scheduled item, moderation, or an attempted directory submission is not proof of indexing, traffic, publication, or backlink.

## Outreach as a separate signal

Use the current public read-only `/api/search/multi-search` surface only to form hypotheses, then cross-check the signal against Base2026 public evidence and official platform facts. Verify the route live before relying on it. Evidence and Outreach are separate collections and must be reported separately; do not merge their ranks or imply that an Outreach finding is a source record. A representative multi-search is:

```json
{
  "queries": [
    {"indexUid": "base2026_public_tiktok", "q": "internal linking", "limit": 10},
    {"indexUid": "base2026_public_outreach", "q": "organic distribution", "limit": 10}
  ]
}
```

Re-read current corpus counts and endpoint behavior before reporting them. Private workbooks, contacts, owner notes, raw exports, and credentials never enter the public skill, repo, or output. For a new public Outreach row, require semantic selection, source hash/admission, deterministic import, and live public readback; a score, verdict, or workflow status is not permission to publish.

## Distribution and directory receipts

For every external action, retain the minimum safe receipt: service/account surface, item ID or exact public URL, action and timestamp, workflow status, source artifact, destination URL, readback result, and dedupe/idempotency key. Never put tokens or private response payloads in a report.

Use explicit states such as `candidate`, `preflight`, `attempted`, `submission_unknown`, `moderation_pending`, `approved_scheduled`, `published`, `backlink_verified`, `rejected`, and `blocked_human_check`. Only a live URL plus a successful readback closes publication. `backlink_verified` requires checking the target URL, anchor/context, canonical/robots where relevant, and the actual relationship attribute; do not infer dofollow. Do not blind-retry `submission_unknown`.

Keep native publishing states separate: draft/imported, scheduled, sent/published, and verified. For example, an X scheduled item is not sent; a native Medium/LinkedIn/DEV draft is not a live article. An owned-site article does not close a social task. For an owned-site Base2026 reference, use one normal contextual branded link, verify the target live, and avoid reciprocal or keyword-stuffed claims.

## GSC, Bing, and IndexNow

Use the exact current Base2026 property and domain (`sc-domain:base2026.dev` at the time of this project context); never substitute a personal property or historical `/knowledge` surface. Recheck the current GSC/Bing preflight and live sitemaps before acting.

- Google: submit/monitor the sitemap and inspect a selective set of priority URLs; log property/account, sitemap, URL, page version/date, and result.
- Bing: read back the exact imported Base2026 site and sitemap status; use IndexNow only for changed canonical URLs and record the response plus the later URL check.
- Measurement: record clicks, impressions, position, discovered/indexed/excluded/errors, and the query/date window separately from publication receipts. No result should be called “indexed” or “traffic” without the corresponding readback.

Do not repeatedly submit unchanged URLs or use submission volume as a growth KPI.

Treat DataForSEO as a bounded research input, not public evidence: verify the current price, run only a concrete decision-scoped request, and retain the task/cost/result receipt. Do not turn an old packet, keyword volume, or competitor result into a claim about the live Base2026 corpus.

## AgencyOS handoff

When the private operations surface is mounted, read the current Base2026 marketing board/handoff and the matching AgencyOS project, task, event, and artifact records. Resolve by current project/task title rather than hardcoded IDs. The office viewer is a read-only view, not a scheduler, authorization layer, or proof that a worker is alive. If updating state, use the existing task’s idempotency/source reference and verify the resulting event/artifact; do not create a second tracker, database, or scheduler.

Statuses such as `in_progress`, `assets_ready`, `native_draft_saved`, `scheduled`, `moderation_pending`, `owner_fact_required`, `review_pending`, and `unknown` require follow-up and are not publication proof. Keep private AgencyOS databases, raw receipts, contacts, and account data out of the repository and public artifacts.

Report each lane with `workflow_state`, `external_state`, `proof`, `next_check`, and `owner/blocker` so a future agent can resume without turning an inferred state into a fact.
