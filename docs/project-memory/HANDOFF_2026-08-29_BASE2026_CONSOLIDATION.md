# Base2026 Consolidation Handoff — 2026-08-29

## Current baseline

- Production code is merged through PR #19 (`dbc273782…`) and review-fix PR
  #20 (`f06a27aa…`).
- Exact release source remains reproducible from
  `output/cloudflare-migration/base2026-consolidation-20260829-v3`.

## Live founder receipt

The 2026-08-28 receipt in `FOUNDER_PROFILE_HERO_RELEASE_2026_08_28.md` remains the source receipt. A 2026-08-29 public readback returned HTTP 200 and exactly matched:

- `/founder`: `d03b01a8a464adcdd7b09de4989f9655f9292283a45bb58e7a553f18b35a6539`
- `/static/base2026-founder.css`: `43ec793f4e6eab25ea1f67a543b9b4bc14a20f2391d8c60435dbc89142f31e1c`
- `/static/assets/alex-yarosh-founder-step-wall.webp`: `3922ebadf65f2b7ba928efa8ddec9b537276aa4353d297825675831a8a7e89a8`
- Candidate artifact tree: `4abe1a4f67ff8e67c81578429f8bb1776a3ea6f9f62a33e1ce81d198ee80d83e`
  (4,235 served files; 4,237 including ignored release metadata)

## Integrated source boundary

The founder sub-delta was applied first: founder template, founder-only CSS, approved public WebP, the builder's two founder asset writes, founder-specific test expectations, the dated founder receipt, and Wrangler's exact v4 artifact directory (`founder-profile-hero-20260828-v4`). That sub-delta did not alter homepage, shared header/footer, Worker API, Evidence Brief, analytics, D1, or private pipeline source. The combined worktree now also contains root-owned live-stats/API/analytics edits outside this founder slice; those are not represented as founder changes here.

The consolidated builder writes the reviewed founder assets plus the tracked
Analytics, API and API-index sources. Wrangler points only to the immutable v3
candidate above. Generated deployment trees remain ignored and uncommitted.

## Candidate gates

- Python release/UI/SEO contract tests: 29 passed.
- Public Worker: 44 tests passed; TypeScript check passed.
- D1 import dry-run: 2,095 rows read, 224 skipped, 33 deterministic batches.
- Wrangler asset dry-run: 4,249 uploadable files read.
- Artifact publication gate: passed with four reviewed public JSONL files.
- Git publication audits: 31-file consolidation plus 7-file correction, both
  with zero forbidden paths, review holds or secret findings.
- Browser QA: homepage, founder, Analytics and API passed without horizontal
  overflow or console errors; final Analytics passed desktop and mobile live.
- Independent review caught misleading zero-filled historical Analytics in v2.
  V3 restores the verified 2026-07-29 summary totals and removes empty ranking,
  creator, year and latest-record sections; regression tests cover this gate.
- Post-deploy public D1 invariant: 2,175 documents, 1,574 distinct videos,
  50 applied projections, 83 projected cards and zero public full transcripts.
- Public Worker: `79e3677f-3828-4355-8c59-8801458f0fb2` at 100%; deployment
  `d315d098-a0ed-4f79-b3da-cda0fd6cb98b`.
- Safe pre-consolidation rollback:
  `1ad991e4-bc8f-4c34-a8d1-c77723377137`.
