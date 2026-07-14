# Base2026 Search V1 — Independent Final Review

**Date:** 2026-07-14

**Mode:** independent read-only Codex review

**Contract decision:** Option A (`docs/project-memory/DECISIONS.md`)

**Candidate:** `output/releases/base2026-search-v1-derived-20260714-002149.zip`

**Candidate SHA-256:** `a12f4c5fa2f2b9ab6ca0c1b40a1180e3fab3b93c4b2e78c9f250ec118bfc8b67`

**Immutable baseline SHA-256:** `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`
**Deployment binding manifest SHA-256:** `70f8943c3529b51960b302bedf918f369602cfc31d05b97eb1f2787d32bfc2d6`

## Verdict

**VERDICT PASS**

- Blocking findings: **none**.
- Non-blocking observation: an earlier desktop browser run had transient no-results evidence; both final browser reruns passed and the final evidence hashes are intact.
- Release disposition: safe to proceed with a scoped commit/PR and exact-SHA deployment using `-SkipPackage -SkipReindex`, with no IndexNow.

## Option A scope reviewed

The reviewer was explicitly instructed to treat the following as the approved release contract rather than as a defect waiver inferred after the fact:

- New and changed Search V1 generation/outbound paths must use canonical `/knowledge/?...` query URLs.
- The `4,183` byte-identical immutable Source Detail V2 baseline files are grandfathered and may retain the `10,340` inherited `#search?...` links until a separately authorized family regeneration.
- Inbound legacy `#search?...` bookmarks must runtime-migrate to canonical query state.
- A failure remains mandatory if any inherited file is not byte-identical or if any changed path newly emits an outbound legacy hash link.

## Evidence checked by the independent reviewer

- Direct candidate ZIP SHA-256 and deployment-manifest SHA-256.
- Direct base-tree/candidate byte comparison: `9` changed paths, `4,183` unchanged files.
- `10,340` legacy hash literals confined to inherited immutable content.
- No changed-path legacy outbound emitter.
- Alias redirects and inbound legacy migration.
- Source Detail contract/corpus/sitemap preservation.
- Search browser evidence and publication-boundary audit.

## Local release gates immediately before review

- Focused Search V1 tests: `9 passed`.
- Full Python suite: `55 passed`.
- Deterministic derivation: byte-identical candidate ZIP.
- Candidate package validation: PASS.
- Source Detail V2 contract gate: PASS, `0` failures.
- Search browser gate: PASS, mobile + desktop + aliases + legacy migration.
- Publication boundary: PASS, `15 changed / 15 public-safe`, no forbidden, review-required, or secret findings.
- Deployment `PlanOnly`: PASS with exact ZIP SHA, exact manifest binding, `skip_package=true`, `skip_reindex=true`, rollback armed.

## Reviewer isolation

The review command used a read-only sandbox and had no permission to edit files, commit, push, deploy, or access release credentials. A prior CLI argument conflict exited before analysis and is not a verdict; the corrected invocation exited `0` and produced the PASS above.
