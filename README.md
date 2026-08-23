# Base2026

Base2026 is an open-source public-source intelligence layer for short-form expert video. It turns public videos into attributed, searchable evidence that people and AI systems can inspect, compare and cite.

Built and maintained by solo founder Alex Yarosh.

- Product: <https://base2026.dev/>
- Search workspace: <https://base2026.dev/workspace/>
- Methodology: <https://base2026.dev/methodology>
- Public roadmap: <https://base2026.dev/roadmap>
- Support: <https://base2026.dev/support>
- Partnerships: <https://base2026.dev/partner>

## Why Base2026 exists

Useful expert knowledge is increasingly published in short-form video, but it is difficult to search, verify and cite. Platform feeds are optimized for viewing, not research. Search engines and AI agents often lose the original speaker, timestamp and context.

Base2026 creates a public evidence layer that keeps those connections visible.

## What the product does

- discovers public expert sources in SEO, GEO, AEO, AI search and adjacent fields;
- converts reviewed public source material into searchable passages;
- preserves creator attribution, original-source links and evidence context;
- generates source, creator, topic and comparison pages;
- exposes public-safe machine-readable files for scripts and AI agents;
- provides a Cloudflare Worker search API backed by D1 FTS5;
- documents methodology, corrections, opt-out and publication boundaries.

The current release is a working public prototype. The 2026-08-23 verified snapshot contained 2,136 indexed public documents across 1,557 distinct videos. These numbers describe a dated dataset snapshot, not users, revenue or commercial traction.

## Who it is for

- researchers checking what public experts actually said;
- marketers and founders comparing source-backed tactics;
- journalists and educators looking for attributable evidence;
- developers building search, analysis or agent workflows;
- creators who need clear attribution, correction and opt-out paths.

## How it works

```text
Cloudflare discovery
  -> private D1/R2 intake and dedupe
  -> private Container audio capture
  -> Workers AI transcription and evidence guard
  -> deterministic private packets and import
  -> policy-bound excerpt-card projection
  -> public Worker + D1 FTS5 search
```

No live LLM call is required to search the public library. Raw captions, raw ASR, media, private QA notes and unreviewed material stay outside the public release.

## Open-source architecture

- `scripts/build-base2026-cloudflare-release.py` builds the startup-only static release and fails closed on personal-site or WordPress-form leakage.
- `templates/base2026-*` contains the public startup shell, homepage and Support/Partner/About/Privacy pages.
- `cloudflare/base2026-worker/` contains the D1 search API, private proposal endpoints, migrations and tests.
- `cloudflare/base2026-www-redirect/` redirects the `www` hostname to the canonical apex domain.
- `scripts/audit-publication-boundary.py` checks the repository publication boundary.
- [`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`](docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md) is the mandatory architecture, data-flow, security, operations and rollback reference for the cloud-only TikTok pipeline.

Generated website trees, public export artifacts, local databases and deployment archives are not committed.

The live private control plane and the latest public projection delta are
maintained in a protected operational checkout and may be ahead of public
`main`. The canonical manual records this source-synchronization boundary so a
fresh clone is never mistaken for a complete production deployment source.

## Trust and privacy

Base2026 is not a video re-hosting platform and not a raw transcript dump. Public pages are designed around attribution, provenance, correction and removal.

Support and Partner forms:

- accept structured proposals only—no file uploads or credentials;
- validate exact origin, field limits, consent, timing and a bot honeypot;
- store proposals in a private D1 database separate from public search;
- do not store IP addresses or user-agent strings;
- remove untouched new proposals after 90 days.

See the live [privacy notice](https://base2026.dev/privacy) and [source policy](https://base2026.dev/source-policy).

## Local verification

Python release tests:

```bash
python3 -m pytest tests/test_build_base2026_cloudflare_release.py -q
```

Worker tests:

```bash
cd cloudflare/base2026-worker
npm ci
npm run typecheck
npm test
npm run import:dry-run
npm run wrangler:dry-run
```

Build a new, non-overwriting candidate from an existing public web artifact:

```bash
python3 scripts/build-base2026-cloudflare-release.py \
  --source-web output/cloudflare-migration/source-web \
  --out output/cloudflare-migration/candidate-web-<release-id>
```

Run the publication audit before staging:

```bash
python3 scripts/audit-publication-boundary.py
```

## Roadmap

Current priorities are search quality, provenance and creator-rights workflows, API documentation, accessibility, more public-safe tests and carefully reviewed source expansion. See [ROADMAP.md](ROADMAP.md) or the [live roadmap](https://base2026.dev/roadmap).

## Contributing and security

Contributions that improve public-safe code, source quality, accessibility, documentation and correction workflows are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [GOVERNANCE.md](GOVERNANCE.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

Base2026 is licensed under [Apache-2.0](LICENSE).
