# Combined Studio integration candidate — September 5

Status: RC2 verified, final visual GO; ready for the scoped PR and HQ review.
This is not a merge, deployment, identity repair or adoption receipt.

## Exact source and artifact

- Base main: `8dd924833540ce2e544beec240faf6e5cfd58f45`, including merged PR55/56.
- Imported without rewriting their branches: PR57
  `b3c1326a6838c7504e319b91985e7c908a1c2aba` and PR58
  `b5dd2fb9ba38f02ed4fc3794039018adc44f1994`.
- Branch: `codex/base2026-studio-integration-20260905`.
- Retained V3 input: 4,286 served files / 94,086,308 bytes / tree
  `f8fc68906f0224940d74de6c786025f6e2a4916395794cf4c22bf19f984140db`.
- RC2: 4,293 served files / 94,611,209 bytes / tree
  `80e76f05f84c2e9d0bcd5d7978cc779f44fb0d7478cd6ce225dfae40931ce445`.

The build uses the real retained artifact with explicit members-workspace
support, not the small test fixture. Seven files are added and none removed.
All four public JSONL files, the public data manifest and released plugin ZIP
remain byte-identical. RC2 differs from RC1 only in Tools Studio CSS.

## Changes and boundaries

The builder admits exactly four reviewed repository media exports, with
pinned manifest, source hash, size and output mapping. The review manifest
is not served. A dedicated four-file writer records provenance without
weakening the generic binary preservation gate. Missing, tampered, redirected
or partial retained media and plugin version/name mismatch fail closed.

Page Source Check inspects supplied HTML/file content with an optional HTTPS
URL for context. It does not fetch that URL, prove crawl/indexing/ranking
status or claim observed network facts. The sixth card and exact hub sitemap
entry expose this bounded tool. Illustrations remain distinct from public
inventory data.

The WordPress landing reuses the exact previously verified temporary
Playground link. Its explicit-click CTA discloses the disposable session,
official CORS proxy and public-material limitation; there is no automatic
research, insertion or publication. The plugin remains 0.1.0, 19,096 bytes:
`f588eddae0df5b91da4d70576b6cdec01d3a637b003ea076b9357cace6cb7e2a`.
A narrow PHP Version-header/download-filename check prevents a silent version
mismatch. PR59's 0.1.1 and private identity diagnostic remain separate.

## Verification

- Worker public suite: 645/645; native members: 16/16; dedicated Page Source
  Check: 35/35; typecheck PASS.
- Member UI: 9/9; builder/negative cases: 39/39; final Tools/WordPress Python:
  18/18; Tools JavaScript: 8/8; design-authority check PASS.
- Retained public import dry-run: 2,095 rows / 33 batches, no import executed.
- RC1 and RC2 artifact publication policies and exact-assets Wrangler dry-runs
  PASS, with all existing binding roles preserved and no deployment.
- RC1 native loopback smoke: three tool routes and exact ZIP passed; Page
  Source Check original/corrected input returned the expected observations.
  Private session/collections/export failed closed with no-store/noindex.
  Build metadata returned 404.
- Independent RC1 review: 26 interaction/layout assertions, 18 separate
  1440x1000 and 390x844 captures, four served media hashes, focus, reduced
  motion and no-JS PASS. Zero script exceptions or horizontal overflow.
  One desktop orphan final card led to the narrowly approved RC2 CSS change.
  Final RC2 delta review: VISUAL GO at 1440 and 390px, with 720/721px
  breakpoint geometry verified and no overflow/page exceptions. HTML remained
  byte-identical to RC1. Chief inspected both final screenshots and rehashed
  all 4,293 RC2 files against the build receipt.

Loopback uses empty local D1 and no owner credentials: unavailable stats and
private 503 responses are expected, not evidence of live data or successful
sign-in. No remote D1/config/auth/private-pipeline change, merge or deploy was
performed. Playground was not reopened by integration or visual QA.

Source publication audit requires individual review of the exact four media
exports plus their manifest; these are the explicitly approved PR57 assets,
not a broad permission to publish arbitrary binary or generated material.
Screenshots, generated artifacts and private operations receipts stay out of
Git. HQ owns the final exact-candidate review, merge and deployment decision.
