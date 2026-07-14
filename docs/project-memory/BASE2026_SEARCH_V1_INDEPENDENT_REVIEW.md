# Base2026 Search V1 — Independent Corrective Review

**Date:** 2026-07-14

**Mode:** independent read-only review; no edit, commit, push, merge, deploy, reindex, or IndexNow authority

**Contract decision:** Option A (`docs/project-memory/DECISIONS.md`)

**Current candidate:** `output/releases/base2026-search-v1-derived-20260714-024003.zip`

**Candidate SHA-256:** `3261f235864a57c2c3f17f0ccd9588f24f888b21d5bf5c400ec089fe19311235`

**Immutable baseline SHA-256:** `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`

## Current verdict

**VERDICT PASS — SAFE_TO_COMMIT YES**

An independent read-only Codex review completed on `gpt-5.6-sol` with `reasoning_effort=high`, read-only sandbox, restricted network, and no repository mutation. Machine receipt: session `019f5f81-056e-70e1-82b0-9d1cb7785566`. The reviewer found no blocking findings and bound the verdict to candidate `024003`, exact candidate SHA `3261f235864a57c2c3f17f0ccd9588f24f888b21d5bf5c400ec089fe19311235`, immutable baseline SHA `a25f1a037572b6878ebc33951e6eec5ff4a89c86ad9c8ea80d3b59b41af6dd65`, and the exact nine-file corrective working-tree scope.

The review authorizes only the reviewed scoped commit and push for PR CI. Production deployment remains separately authorization-gated. The reviewer could not rerun focused pytest inside the read-only sandbox because no writable temporary directory was available; it independently rechecked JavaScript syntax and treated the retained local `3/3` focused and `55 + 8 subtests` full-suite evidence as supporting release evidence.

## Option A scope under review

- New and changed Search V1 generation/outbound paths must use canonical `/knowledge/?...` query URLs.
- The `4,183` byte-identical immutable Source Detail V2 baseline files are grandfathered and may retain the `10,340` inherited `#search?...` links until a separately authorized family regeneration.
- Inbound legacy `#search?...` bookmarks must runtime-migrate to canonical query state.
- Any inherited file that is not byte-identical, or any changed path that newly emits an outbound legacy hash link, is blocking.
- The changed Search runtime must not execute attacker-controlled HTML. Its direct `.innerHTML =` assignments were removed; script/style/iframe/object/embed elements and inline handlers must be stripped, URL attributes sanitized, and browser probes must prove scripts and handlers do not execute.

## Corrective local evidence available to reviewer

- Exact candidate ZIP SHA-256: `3261f235864a57c2c3f17f0ccd9588f24f888b21d5bf5c400ec089fe19311235`.
- Deterministic repeat derivation: PASS, byte-identical ZIP.
- Direct base-tree/candidate comparison: `9` changed paths and `4,183` unchanged files.
- Legacy hash literals: `10,340`, confined to inherited immutable content; `0` changed outbound legacy paths.
- Focused Search V1 tests: `3 passed` locally after hardening; the earlier broader focused selection reported `9 passed`.
- Full Python suite: `55 passed`.
- JavaScript syntax, candidate package validation, publication boundary, public-data release contract, Source Detail V2 contract gate, Search browser/XSS gate, and Source Detail browser gate: PASS.
- Exact candidate visual review at desktop `1440` and mobile `390`: PASS with no obvious overflow, overlap, or responsive regression.

## Reviewer history and disposition

1. The original pre-hardening review PASS applied only to candidate `002149`; it is superseded.
2. The first post-hardening Codex review returned FAIL because active docs still bound the release to `002149`. That blocker has been corrected across the active release docs.
3. That review also found six direct assignments in byte-identical baseline `web/static/roadmap.js`. Dataflow inspection found all external text escaped, width numeric, no open CodeQL alert, no diff from `origin/main`, and no new executable flow. This is inherited maintainability debt, not a blocker for the scoped Search-runtime corrective diff. The final reviewer must judge the changed Search runtime, while still reporting any actual package-wide attacker-controlled flow if found.
4. A delegated Terra review timed out without a summary or verdict and is not evidence of approval.
5. A later retained Terra review independently returned `VERDICT PASS` and `SAFE_TO_COMMIT YES`; it is useful supporting technical evidence but does not replace the required Base2026 Sol/high final release judgment.
6. The final isolated Sol/high review returned `VERDICT PASS`, no blockers, and `SAFE_TO_COMMIT YES` for candidate `024003` and the exact nine-file diff. This closes the independent corrective-review gate.

## Release sequence after final PASS

This retained `VERDICT PASS` authorizes only scoped commit, push to PR #10, CI/CodeQL verification, merge, and merged-SHA/artifact binding. Production deployment remains separately authorization-gated. If later authorized, deployment must use the exact frozen ZIP with `-SkipPackage -SkipReindex` and no IndexNow.
