# Base2026 Consolidation Handoff — 2026-08-29

## Current baseline

- Live `origin/main` is `616d6de4c64c13fa91bbc589f0a59fddbcd69a63`.
- Isolated candidate: `/Users/alexyarosh/Projects/base2026-migration/DW/.worktrees/base2026-consolidate-20260829`, branch `codex/base2026-consolidate-20260829`.
- The exact reviewed public candidate is
  `output/cloudflare-migration/base2026-consolidation-20260829-v2`.

## Live founder receipt

The 2026-08-28 receipt in `FOUNDER_PROFILE_HERO_RELEASE_2026_08_28.md` remains the source receipt. A 2026-08-29 public readback returned HTTP 200 and exactly matched:

- `/founder`: `d03b01a8a464adcdd7b09de4989f9655f9292283a45bb58e7a553f18b35a6539`
- `/static/base2026-founder.css`: `43ec793f4e6eab25ea1f67a543b9b4bc14a20f2391d8c60435dbc89142f31e1c`
- `/static/assets/alex-yarosh-founder-step-wall.webp`: `3922ebadf65f2b7ba928efa8ddec9b537276aa4353d297825675831a8a7e89a8`
- Candidate artifact tree: `a7cba1e05e7aa51aa54fe9fa6747d447c69e9cb88fc4da863b2115fe8fc55010`
  (4,235 served files; 4,237 including ignored release metadata)

Unchanged live sentinels remain homepage `cf384e7c890b76b7bc8b446a03d96e959af52fb41e914dee812569500f6750b3`, homepage CSS `bec459945e06bc7e295d3e4d5d17b55a3264ac871717dc90ee85551e5df24f6f`, and Evidence Brief JS `ef57559fe992fa467a6d82425dc9e0495789bfe47b777f343313ee64938f6a7d`.

## Integrated source boundary

The founder sub-delta was applied first: founder template, founder-only CSS, approved public WebP, the builder's two founder asset writes, founder-specific test expectations, the dated founder receipt, and Wrangler's exact v4 artifact directory (`founder-profile-hero-20260828-v4`). That sub-delta did not alter homepage, shared header/footer, Worker API, Evidence Brief, analytics, D1, or private pipeline source. The combined worktree now also contains root-owned live-stats/API/analytics edits outside this founder slice; those are not represented as founder changes here.

The dirty root checkout's Wrangler path pointed at v3, while the live receipt
and matching local artifact are v4. The consolidated builder now writes the
reviewed founder assets plus the tracked Analytics, API and API-index sources;
Wrangler points only to the exact v2 candidate above.

## Candidate gates

- Python release/UI/SEO contract tests: 29 passed.
- Public Worker: 44 tests passed; TypeScript check passed.
- D1 import dry-run: 2,095 rows read, 224 skipped, 33 deterministic batches.
- Wrangler asset dry-run: 4,249 uploadable files read.
- Artifact publication gate: passed with four reviewed public JSONL files.
- Git publication audit: 30 public-safe files, zero forbidden paths, zero
  review holds and zero secret findings.
- Browser QA: homepage, founder, Analytics and API passed without horizontal
  overflow or console errors; built Analytics/API copy was verified from v2.
- Pre-deploy public D1 invariant: 2,175 documents, 1,574 distinct videos,
  50 applied projections, 83 projected cards and zero public full transcripts.
- Current public rollback before this release:
  `1ad991e4-bc8f-4c34-a8d1-c77723377137`.
