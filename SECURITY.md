# Security Policy

Base2026 is a public prototype. The deployed product serves a public read-only evidence library and accepts structured Support/Partner proposals. Source ingestion and review remain maintainer-controlled workflows.

## Reporting

Report security issues privately through the repository's security reporting channel. Do not include credentials, private datasets or sensitive personal information in public issues or in the website forms.

## Supported public surface

- static product and evidence pages on `base2026.dev`;
- read-only search endpoints backed by D1 FTS5;
- public-safe JSONL and metadata files;
- validated Support and Partner proposal endpoints.

There are no public source-ingestion, transcript-refresh, database-admin, media-upload or hosted-transcription endpoints.

## Required controls

- no secrets in source code or generated artifacts;
- public search data and private proposals use separate D1 databases;
- proposal endpoints validate exact origin, content type, field limits, consent, elapsed time and a honeypot;
- proposal storage excludes IP addresses and user-agent strings;
- untouched new proposals expire after 90 days;
- public releases exclude raw captions, raw ASR, media, private QA, local databases, logs and unreviewed material;
- the release builder fails closed on personal-site shell, WordPress-form and retired-route markers;
- a publication-boundary audit is required before staging for GitHub.

## Verification

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
