# Base2026 public API/MCP production release

Verified: 2026-09-02 00:44 UTC

## Release identity

- GitHub PR: [#34](https://github.com/offflinerpsy/base2026/pull/34), merged.
- Reviewed source commit: `16884d148fa01da970e334396c17bcf4acc9429f`.
- `origin/main` merge commit: `98bfb65efd5940e01ecff13e4095ad9442a53986`.
- Worker: `f8781f4d-30fd-4d70-ab96-a4e8d718226a`, selected at 100%.
- Immediate rollback: `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e`.
- Reviewed static artifact: 4,253 served files, 92,018,350 bytes, tree SHA-256
  `eb7538f97e322a88f87ec08578fd9477c3da4d13320dea1086bb4959362838ba`.

## What is live

- `POST https://base2026.dev/api/mcp` is a stateless, no-key, read-only MCP
  surface over the public D1 database.
- `https://base2026.dev/api`, `/mcp` and `/integrations` are HTTP 200,
  self-canonical and indexable.
- Six bounded tools are discoverable: `search_sources`, `get_source`,
  `get_creator`, `get_topic`, `get_topic_signal` and `get_public_manifest`.
- The release builder now explicitly includes the MCP page, integrations page,
  data dictionary, both llms files and API index. A regression test prevents
  repository-only developer pages from disappearing from a future artifact.

## Preserved boundaries

Version readback contains `DB`, `INBOX_DB`, `OUTREACH_DB`, `AUTH_DB`, `ASSETS`,
the three member-auth secret names, `MEMBER_AUTH_ENABLED=true`, and
`MCP_RATE_LIMIT` namespace `20260901` at 60 requests per 60 seconds. No secret
value is recorded here. MCP reads only `DB`, has no write method and returns no
raw captions, raw ASR, full private transcript, media, inbox, outreach, member
or private-pipeline data. Missing abuse protection fails closed.

Signed-out `/api/auth/session` remains HTTP 403 with private/no-store,
noindex/nofollow, no-referrer and DENY headers. `/my-research/` remains HTTP
200, canonical and noindex/nofollow. The strict member CSP intentionally blocks
Cloudflare's optional analytics beacon instead of permitting third-party script
execution on the private page.

## Verification

- Worker typecheck passed; 625 Worker tests passed.
- 171 Python tests and the design-authority check passed.
- Generated Wrangler types are current.
- Full PR publication audit: 100 public-safe files, zero forbidden paths, zero
  review holds and zero secret findings.
- Wrangler dry-run and deployed version readback show all required bindings.
- Live MCP gates passed: modern `server/discover`, `tools/list`, one bounded
  `search_sources`, legacy `initialize`, invalid-protocol rejection and empty
  202 notification handling.
- Live public search returned one bounded result from 27 estimated matches with
  no private marker.
- Desktop and mobile browser checks passed for home, API, MCP and integrations:
  one H1, correct canonical, no horizontal overflow and zero public-page console
  errors.
- Direct public D1 read: 2,198 documents, 1,589 distinct sources, 65 applied
  projection routes, 106 projected cards and zero public full transcripts.

## Discovery receipt

The existing IndexNow key file read back exactly with HTTP 200. Exactly two new
URLs, `/mcp` and `/integrations`, were submitted once; IndexNow returned HTTP
200. Submission is not proof of indexing, ranking, traffic or citation.

## Next action

Measure discovery and real tool use. The next product implementation candidate
is the bounded Claim Receipt Ledger canary; keep it separate from this completed
release and do not widen automatic indexation until its source-integrity gates
pass.
