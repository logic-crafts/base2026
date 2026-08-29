# Base2026 Public Consolidation Release — 2026-08-29

## Release authority

- Repository: `https://github.com/offflinerpsy/base2026`
- Consolidation commit: `440dc5c61896d69184f6f95d95496b0edc04c93a`
- PR #19 merge: `dbc273782388c7e42ac8684d9ad22358bd0019be`
- Analytics correction commit: `268c8cb1d6e648cf7e3eada496d73e8c27f5b152`
- PR #20 merge: `f06a27aa2261704aa566837405a5ed623ef1ad83`
- Public Worker: `79e3677f-3828-4355-8c59-8801458f0fb2` at 100%
- Deployment: `d315d098-a0ed-4f79-b3da-cda0fd6cb98b`
- Exact artifact tree:
  `4abe1a4f67ff8e67c81578429f8bb1776a3ea6f9f62a33e1ce81d198ee80d83e`
- Safe pre-consolidation rollback:
  `1ad991e4-bc8f-4c34-a8d1-c77723377137`

Immediate predecessor `de84ef34-6cf9-4f6c-b392-34c064626d2a` contains the new
APIs but also the independently detected zero-filled historical Analytics
defect. Prefer the safe rollback above if rollback is required.

## What is live

- Tracked founder HTML, founder-only CSS and approved public hero image now
  reproduce the live founder release exactly.
- Read-only `/api/stats` reports aggregate public D1 totals only.
- Homepage and Analytics refresh current totals from `/api/stats`, with verified
  fallback values.
- Analytics preserves the verified 2026-07-29 summary totals and does not render
  empty historical rankings.
- API and API-index pages document the current D1 FTS5, Evidence Brief V1/V2,
  sitemap and public-static-data contracts.
- Dynamic source pages use the current blue/white visual authority and shared
  core stylesheet.

## Verification

- Python release/UI/SEO tests: 29 passed before each artifact build.
- Public Worker: 44 tests passed; TypeScript check passed.
- Import dry-run: 2,095 rows read, 224 skipped, 33 deterministic batches.
- Wrangler dry-run: 4,249 uploadable files read.
- Artifact policy: four reviewed public JSONL files; all leak gates zero.
- Publication audits: 31-file release and 7-file correction both passed with
  zero forbidden paths, review holds or secret findings.
- Independent reviewer: initial NO-GO on zero-filled historical Analytics;
  corrected v3 received GO with no remaining blocker.
- Live desktop/mobile browser QA: homepage, founder and Analytics have zero
  horizontal overflow and zero console errors; founder images load.
- Live Evidence Brief: V1 ready with six selected evidence records; V2 returned
  five attributable findings for the bounded test query.
- Static and dynamic sitemaps are valid XML; a dynamic source route loads the
  shared core CSS and `#315eea` accent without the retired orange accent.

## Live D1 invariant

Read-only post-deploy queries returned:

- 2,175 public documents;
- 1,574 distinct videos;
- 50 applied projection receipts;
- 83 projected cards;
- zero public full transcripts;
- zero rows written and `changed_db=false` for every verification query.

Founder hashes remain exact:

- HTML: `d03b01a8a464adcdd7b09de4989f9655f9292283a45bb58e7a553f18b35a6539`
- CSS: `43ec793f4e6eab25ea1f67a543b9b4bc14a20f2391d8c60435dbc89142f31e1c`
- WebP: `3922ebadf65f2b7ba928efa8ddec9b537276aa4353d297825675831a8a7e89a8`

## Separate private-pipeline readback

Private Worker v0.6.2 `4d9f291e-0f7e-4795-adb4-e18c5f028d58` restored
creator discovery from 7 active / 12 failed cursors to 18 active / 1 failed.
The last discovery found 135 candidates, admitted 17 fresh rows, classified 118
duplicates and retained only `@webhivedigital` for source review. One bounded
canary stored private media and completed downstream AI jobs.

One Container recycle completed without changing its image or configuration.
App v8 is running, but Cloudflare telemetry later reported `active=1`,
`healthy=0`, `errors=[]` after briefly reporting healthy. The canary used the
official Player API Browser path, so stable Container readiness and an organic
Container-fallback proof remain unresolved. Do not loop restarts or weaken
capture/privacy gates.

## Boundary

No private pipeline source, media, transcript, provider response, log,
credential, local database, generated release tree, browser receipt, private CV
or owner-profile file was committed or published. Broad
`PUBLIC_RELEASE_ENABLED=false` remains intentional; only the policy-bound
automatic projection lane is enabled.
