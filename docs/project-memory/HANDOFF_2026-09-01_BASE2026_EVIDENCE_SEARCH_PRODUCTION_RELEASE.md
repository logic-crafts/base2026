# Base2026 Evidence Search production release

Date: 2026-09-01 20:10 UTC
State: deployed and live-verified
Worker: `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e` at 100%
Rollback: `5a326a64-c755-4036-93af-1a1809e0aeb6`

## Outcome

`https://base2026.dev/tools/evidence-search/` is live with HTTP 200,
self-canonical, `index,follow`, hub-sitemap exposure and an honest no-JavaScript
fallback. A real public D1 search for `internal linking` returned 24 hits with
an estimated corpus total of 27 and rendered ten deduplicated source records.
Creator attribution, the stable Base2026 record, available original links and
the claim boundary remain visible.

The release preserved `AUTH_DB`, the three remote member-auth secret names,
`MEMBER_AUTH_ENABLED=true`, the signed-out 403/401 guards and the private
My Research response headers. `/guides` and `/guides/` still return bodyless
308 responses to `/topics/`.

## Gates

- 157 Python, 614 public Worker and 13 member Worker tests passed.
- TypeScript, design-authority, diff and Wrangler dry-run gates passed.
- Publication audit: 43 public-safe files, two explicitly reviewed synthetic
  test sources, zero forbidden paths and zero secret findings.
- Browser QA: live search worked; mobile width 390; console errors/warnings 0.
- IndexNow accepted exactly the new tool URL with HTTP 200. This is a
  notification receipt, not proof of indexing or traffic.

Private operational receipt:
`/Users/alexyarosh/Projects/base2026-growth-operations-20260830/office/continuous-20260831/free-tools-strategy/evidence-search-production-release-20260901T201055Z.json`

No Git commit, push, merge, staging, D1 mutation, OAuth change or duplicate
social publication was performed. The source candidate remains a dirty,
uncommitted worktree and requires a separately reviewed public Git integration.
