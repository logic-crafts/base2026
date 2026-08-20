# Contributing

Base2026 welcomes focused contributions to its public-safe code, product UI, search, data contracts, source-quality checks, accessibility, documentation and creator correction/removal workflows.

## Before you start

Read:

- `AGENTS.md`
- `docs/project-memory/PUBLICATION_BOUNDARY.md`
- `docs/GIT_PUBLICATION_AUDIT.md`
- `SECURITY.md`
- `ROADMAP.md`

For a substantial change, open an issue describing the user problem, affected data/rights boundary and how success will be verified.

## Public boundary

Do not add private research, raw captions, raw ASR, media, generated exports, local databases, logs, cookies, tokens, keys, credentials or deployment archives.

`public-data/`, `output/`, local D1 state, Wrangler state and `node_modules/` are generated or local artifacts—not repository source.

Do not submit confidential material through GitHub issues or the live Support/Partner forms.

## Development checks

Run the smallest relevant checks. For startup release or Worker changes, use:

```bash
python3 -m pytest tests/test_build_base2026_cloudflare_release.py -q
python3 scripts/audit-publication-boundary.py

cd cloudflare/base2026-worker
npm ci
npm run typecheck
npm test
npm run import:dry-run
npm run wrangler:dry-run
```

For UI changes, verify representative desktop and mobile viewports, keyboard behavior, horizontal overflow and the browser console.

## Pull request expectations

- explain the user-facing outcome;
- list exact verification commands and results;
- call out public/private data or creator-rights risk;
- keep changes focused and reviewable;
- update docs when architecture, behavior or boundaries change;
- never include generated release trees or unrelated local changes.
