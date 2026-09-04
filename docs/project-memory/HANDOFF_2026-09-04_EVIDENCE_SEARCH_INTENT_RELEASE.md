# Evidence Search intent-alignment release

Date: 2026-09-04
Status: live and verified

## Outcome

The existing free Evidence Search now describes its actual user job in the
title, description, structured data, H1 and lede: search inside Base2026's
bounded corpus of processed expert videos for attributable evidence. It does
not claim arbitrary video upload, universal web coverage, full transcripts,
source reliability scoring or a verdict that advice works.

The wording is backed by a bounded US-English DataForSEO check. `search inside
video` has approximate volume 90 and a relevant in-video-search SERP. Generic
`free research tool` and `tiktok research tool` were rejected because their
live SERPs have different intent. A larger TikTok transcript-generator demand
is a separate product opportunity only if Base2026 builds the real private,
rate-limited paste-URL utility; no doorway page was created.

## Source and release identity

- Source branch: `codex/base2026-evidence-search-intent-20260904`.
- Source files: `templates/base2026-evidence-search.html` and its focused test.
- Release artifact tree SHA-256:
  `149abf84420443c0194823e13b73c59687a10c36149eff263482f4c30ca029c7`.
- Public Worker: `327a21a5-ca54-457c-8099-aa2447a7fe1a` at 100%.
- Immediate compatible rollback:
  `da308428-5609-43ab-8b31-88deb124dc7b`.

The artifact builder reported exactly one changed served file relative to the
reviewed Source Diversity release. Wrangler uploaded exactly
`/tools/evidence-search/index.html` in the successful target-account deploy.

## Verification

- Focused Python tests: 34 passed.
- TypeScript typecheck: passed.
- Target-account Wrangler dry-run: passed with all four D1 bindings, rate
  limit, static assets and `MEMBER_AUTH_ENABLED=false`.
- Publication gate: passed; four public data files; artifact hash matched.
- Live Evidence Search: HTTP 200, exact title/H1/description and self-canonical.
- Live home, Source Diversity Check and MCP: HTTP 200.
- Live health: OK.
- Live stats: 2,259 documents, 1,638 distinct sources, 114 public evidence
  routes, 167 cards and zero public full transcripts.
- Member session remains intentionally fail-closed with HTTP 503 while member
  auth is disabled on the migrated account.

One initial Wrangler command inherited the legacy local account and failed on
binding validation before a Worker version or deployment was created. The
target account was then read back explicitly, pinned in the release config and
the dry-run was repeated before the successful one-asset deployment.

IndexNow was not repeated because the canonical URL did not change. This is a
CTR/intent experiment, not proof of indexing, clicks, traffic or activation.

## Next action

Compare the title/CTR and activation window against the existing Search Console
baseline, publish one original-data Evidence Pulse demonstration, and complete
the Source-Backed Brief. Do not clone the wording into keyword-swapped pages.
