# Next Action

Last verified: 2026-08-29

## In progress

- Private pipeline task: diagnose and repair the 12 creator cursors returning
  `browser_discovery_empty`; deploy private-only after full tests and a bounded
  live canary.
- Public integration task: finish founder source synchronization, `/api/stats`,
  live homepage/analytics counters and current API documentation in
  `codex/base2026-consolidate-20260829`.

## Release gate

1. Verify the founder sub-delta reproduces the existing live founder hashes.
2. Run Python release/UI tests, public Worker tests/typecheck/dry-run, exact
   artifact build, publication-boundary audit and independent review.
3. Commit and push only the reviewed public-safe diff.
4. Deploy the exact candidate; verify `/`, `/founder`, `/api/health`,
   `/api/stats`, Evidence Brief V1/V2, both sitemaps and
   `full_transcripts_published=0`.
5. Record Worker version, rollback, artifact hash and live D1 counts.

## After release

- Recheck GSC/Bing once processing data appears.
- Audit historical dirty worktrees before any removal; never bulk-delete them.
- Keep the current founder page unless Alex separately selects a premium
  redesign direction.
