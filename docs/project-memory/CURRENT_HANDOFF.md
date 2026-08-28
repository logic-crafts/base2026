# Base2026 Current Handoff

Last updated: 2026-08-28

## Source of truth

Start with `AGENTS.md`, the required `docs/project-memory/` files and
`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`. Do not use
old chat counters or historical VPS/design notes as current production truth.

## Live public release

- Domain: `https://base2026.dev/`
- Public Worker version: `35a2ee9e-1d95-45c4-b971-26f19183d732`
- Immediate rollback: `dcbeb2e9-27af-4d45-b510-fdaaea055f4a`
- Immutable candidate receipt tree SHA-256:
  `af3641c48f0ff59a7686c623835c07fab39b7b0e5908f6a9d12290cb8e212a52`
- Live D1 snapshot: 2,170 search documents, 1,572 distinct sources,
  48 public evidence routes and zero public full third-party transcripts.

The homepage, Evidence Brief V2, preserved V1 API, roadmap, workspace, API
health and public sitemaps returned successfully after deployment. Desktop,
mobile, keyboard, reduced-motion and no-JS QA preserved the current cool-blue
shell with zero horizontal overflow or browser/request errors.

Canonical public repository: `https://github.com/offflinerpsy/base2026`.
The private capture Worker and raw pipeline artifacts remain excluded.

## Product definition

Base2026 is an **open video research engine** and **source-first evidence
library for short-form expert video**. The homepage H1 remains “Search what
experts actually said.” Cloudflare is technical proof and operating advantage,
not the primary hero benefit.

Do not claim complete TikTok coverage, perfect transcription, generic video
intelligence, AI-visibility monitoring, guaranteed rankings/citations or live
MCP. The public product retrieves reviewed, bounded, attributed evidence.

## Architecture

The public product runs on Cloudflare Workers Static Assets and public D1
FTS5. A separate private Cloudflare lane uses Workers, private D1, R2, Browser
Rendering/restricted Container acquisition, Workers AI, Queues and Workflows.
Only exact, sanitized one-to-three-card projections cross the service-binding
boundary into public D1. Raw media, raw ASR, full transcripts, private packets,
credentials and logs remain private.

The private control-plane source is not admitted to the public Git repository.
Do not change the private Worker while working on the public product release.

## Design authority

`b26-independent-v1` is the only production design authority:

- `templates/base2026-core.css`
- `templates/base2026-startup-*`
- `scripts/build-base2026-cloudflare-release.py`
- `scripts/check-base2026-design-authority.py`

Alex V4, WordPress, Stitch, Search V1, Source Detail V2 and template-migration
assets are quarantined history/compatibility. Do not delete them blindly and
do not invoke them from the Cloudflare builder. Retire them only after proving
all callers and rollback dependencies.

## GitHub release

- Current repository: `https://github.com/offflinerpsy/base2026`
- Historical LogicCrafts merge: `d0dd1dbe2700bb3a4e619ee0ced7cc6b71d0c8da`
- Historical LogicCrafts pull request: `https://github.com/logic-crafts/base2026/pull/16`
- Historical public release commit: `95c2083d14dbd945b3e094baf6a812ac830e12bd`
- Description and topics now identify video search, research tools, evidence,
  Cloudflare Workers/D1 and Workers AI; stale `meilisearch` topic was removed.

CodeQL previously did not start in the LogicCrafts organization because GitHub
reported a billing lock. That historical account-level failure is not a
Base2026 code-test failure.

The original working checkout remains intentionally dirty and untouched at
`/Users/alexyarosh/Projects/base2026-migration/DW/base2026`. Release work was
performed in a clean worktree to avoid losing user changes.

## Verification receipts

- 16 Python release/design/info-page tests passed.
- 37 Worker tests passed; TypeScript typecheck passed.
- Public import dry-run read 2,095 rows and emitted 2,095 deterministic rows.
- Wrangler dry-run passed against the portable `candidate-web` path.
- Publication audit: 62 public-safe files, zero needs-review, forbidden or
  secret findings.
- DataForSEO US/en market packet cost `$0.077`; exact task IDs are in
  `DATAFORSEO_POSITIONING_RECEIPT_2026_08_28.md`.

## Next action

Monitor the first meaningful GSC/Bing processing readback. Then build 10–15
strong source-backed topic evidence maps from existing records, add a versioned
public dataset sample/API quickstart/corpus changelog, and improve creator claim
and correction tracking. Do not mass-publish thin pages or repeatedly resubmit
unchanged URLs.
