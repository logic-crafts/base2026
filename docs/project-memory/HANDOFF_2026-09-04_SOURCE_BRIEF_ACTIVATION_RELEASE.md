# Base2026 Source-backed Brief and activation release

Date: 2026-09-04 21:23 UTC

Status: deployed and live-verified

Public Worker: `3ecddaf3-f594-4b4a-91d4-fd409bd62e4a`

Immediate rollback: `327a21a5-ca54-457c-8099-aa2447a7fe1a`

## Outcome

The public acquisition loop is now fully usable:

1. Evidence Search finds bounded public records.
2. Source Diversity Check compares record, original-source and creator paths.
3. Source-backed Brief assembles up to eight selected public records into a
   deterministic brief, memo or outline with attribution, bounded excerpts,
   explicit unknowns and Markdown/JSON exports.

The three tools now emit only allowlisted, coarse activation events to a
first-party Cloudflare Analytics Engine dataset. This release does not publish
raw captions, raw ASR, full transcripts, media, member data or private pipeline
state, and it does not infer truth, consensus, independence or quality.

## Source and artifact

- Source-backed Brief source: PR50, merge `c7b00f28`.
- Integrated activation source: PR51, merge `36e4c26ca`.
- Candidate artifact:
  `output/cloudflare-migration/base2026-brief-activation-20260904-v2`
- Served files: `4281`; Wrangler asset scan: `4303`.
- Bytes: `93676065`.
- Artifact tree SHA-256:
  `bffcbbd3502daa38a6ca14282a456a0a9663e8447a66c133faec7ee0e7383405`.
- Source tree SHA-256:
  `124e11760d6af60a4010377d5941ee0ed7b8ca57d9a499fffa60f946944d55fb`.
- Publication-boundary audit passed with exactly four admitted public data
  files and no forbidden/private data.

## Account-migration repair

The first deployment attempt stopped before creating a Worker version with
Cloudflare error `10089`: Analytics Engine was not enabled in the migrated
`hello@base2026.dev` account. The dashboard activation created the price-$0
`Beta Analytics Engine API` subscription at 21:20 UTC. After entitlement
propagation, the next attempt correctly advanced to D1 validation and exposed
stale database UUIDs inherited from the former account.

The checked Wrangler configuration now uses the current account resources:

| Binding | Database | Current UUID |
|---|---|---|
| `DB` | `base2026-public-search` | `3ec00e3b-0d92-4ab6-9ae9-3acfc27c6e80` |
| `INBOX_DB` | `base2026-inbox` | `fabcf17d-b9ed-4932-9b6b-ef678705d622` |
| `OUTREACH_DB` | `base2026-outreach-search` | `054440bd-b91e-41f7-aa70-45a148462cac` |
| `AUTH_DB` | `base2026-member-auth` | `8b5c2f98-164f-43f1-bb12-d9eda96d289a` |

No failed attempt changed the selected public Worker. The successful deployment
then selected `3ecddaf3-f594-4b4a-91d4-fd409bd62e4a` at 100%.

## Verification before deployment

- Worker TypeScript typecheck: passed.
- Worker tests: 13 files / 641 tests passed.
- Full Python suite: 211 tests passed.
- Focused integration suite: 53 tests passed.
- JavaScript syntax and `git diff --check`: passed.
- Target-account Wrangler dry-run: all four D1 bindings, `ANALYTICS`,
  `MCP_RATE_LIMIT`, `ASSETS` and `MEMBER_AUTH_ENABLED=false` present.
- Local browser: 1440 and 390 px, no console/request errors or horizontal
  overflow; safe mocked MCP; URL remained query-free; no-JS content readable.

## Live readback

At 21:23:57 UTC:

- `/api/health`: HTTP 200, D1 FTS5 healthy.
- `/api/stats`: 2268 documents, 1644 distinct sources, 120 public evidence
  routes, 176 projected cards, zero published full transcripts.
- `/tools/evidence-search/`: HTTP 200.
- `/tools/source-diversity-check/`: HTTP 200.
- `/tools/source-backed-brief/`: HTTP 200, self-canonical, `index,follow`, and
  present once in `/sitemaps/base2026-hubs.xml`.
- `GET /api/mcp`: expected HTTP 405; `POST tools/list`: HTTP 200 with six
  bounded read-only tools.
- `/api/auth/session`: expected HTTP 503 `MEMBER_AUTH_DISABLED`; member auth
  remains deliberately fail-closed during the account-migration contour.
- `/my-research/`: HTTP 200 private/noindex surface; no public member data was
  exposed.

Live Source-backed Brief used two existing public record IDs plus one
nonexistent ID. It rendered 2 resolved records, 1 explicit unresolved record
and 3 bounded excerpts, retained the same query-free URL, exposed Markdown/JSON
exports and produced no console error.

## Activation measurement

- Event/route mismatch: HTTP 400.
- Wrong origin: HTTP 403.
- One bounded valid canary: HTTP 204.
- `SHOW TABLES` returned `base2026_activation_v1`.
- First aggregate readback returned:
  - `brief_required_fields_completed`: 1
  - `brief_preview_created`: 2
  - `brief_completed`: 1

These counts are deployment/QA smoke events. They are not unique visitors,
traffic, conversions or owner-excluded product adoption. The sink stores event
name, exact tool route, server UTC-hour bucket and allowlisted coarse enums;
it does not store typed questions, search queries, record/source IDs, IP,
user-agent, referrer, cookies, fingerprint, auth/member or private data.

## Discovery notification

After the canonical, robots, sitemap and key-file gates passed, IndexNow
received exactly one URL:
`https://base2026.dev/tools/source-backed-brief/`. It returned HTTP 200 at
21:27:13 UTC. This proves notification acceptance only, not indexing or traffic.
Evidence Search and Source Diversity were not resubmitted.

## Rollback

If a production regression is reproduced, restore public Worker
`327a21a5-ca54-457c-8099-aa2447a7fe1a`. Do not delete the Analytics Engine
dataset or migrated D1 databases as part of code rollback. Recheck all four D1
bindings, the public/private boundary, member fail-closed behavior and the MCP
rate-limit binding after any rollback.

## Next measurement gate

Measure non-owner referrals and successful tool actions over the existing
72-hour acquisition window. Keep QA smoke separate from real activation. Do
not widen the programmatic corpus, generate keyword-swapped doorway pages or
manufacture `verified`, `best`, consensus or independence claims.
