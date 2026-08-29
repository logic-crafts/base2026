# Base2026

Base2026 is an open-source video research engine and source-first evidence library for short-form expert video. It turns reviewed public videos into attributed, searchable evidence that people and AI systems can inspect, compare and trace to the original source.

Built and maintained by solo founder Alex Yarosh.

- Product: <https://base2026.dev/>
- Repository: <https://github.com/offflinerpsy/base2026>
- Search workspace: <https://base2026.dev/workspace/>
- Public dataset: <https://base2026.dev/dataset>
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

The current release is a working public prototype. The verified 2026-08-29
snapshot contained 2,175 search documents across 1,574 distinct videos, with
50 public evidence projections applied and zero public full transcripts. These
are dated database dimensions, not users, revenue, universal coverage or
commercial traction. Current totals are available from the read-only
[`/api/stats`](https://base2026.dev/api/stats) endpoint.

## Public dataset quickstart

Base2026 exposes public source documents, evidence passages, reviewed insight
cards and topic signal briefs as JSONL. Search the live D1 FTS5 layer without a
key:

```bash
curl -sS -X POST https://base2026.dev/api/search/multi-search \
  -H 'content-type: application/json' \
  --data '{"queries":[{"indexUid":"base2026_public_tiktok","q":"AI search visibility","limit":5}]}'
```

See the [dataset landing page](https://base2026.dev/dataset),
[full quickstart](docs/PUBLIC_DATASET_QUICKSTART.md), and the
[standard-library Python example](examples/query_public_evidence.py).
The Apache-2.0 license applies to repository code; creator/source rights remain
governed by the public source policy.

## Build reproducibility boundary

This repository contains the public Worker, templates, deterministic release
builder, tests and publication checks. A production static release additionally
requires an already-reviewed public `--source-web` artifact. That generated
corpus is intentionally excluded from Git because it is a deployable data
artifact, not source code. A clean clone can reproduce the software tests and
Worker dry-run, but must not claim byte-for-byte reproduction of a live release
without the exact reviewed source artifact and its recorded tree hash.

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

The public product and bounded cloud pipeline use Cloudflare Workers, Workers
Static Assets, D1, R2, Queues, Workflows and Workers AI. Durable identities,
validation and receipts prevent retries from silently publishing a different
record. Only sanitized excerpt cards cross from the private evidence lane into
public D1.

## What makes it different

- a free public research corpus rather than a private saved-video library;
- reviewed, bounded evidence instead of a public raw-transcript dump;
- creator attribution, original-source links and correction/removal paths;
- human pages plus public API, JSONL and machine discovery files;
- open-source code and a documented public/private publication boundary;
- edge search that does not spend an LLM call for every visitor query.

Base2026 does not claim complete TikTok coverage, perfect transcription,
real-time monitoring, guaranteed rankings or an AI-visibility dashboard.

## Open-source architecture

- `scripts/build-base2026-cloudflare-release.py` builds the startup-only static release and fails closed on personal-site or WordPress-form leakage.
- `templates/base2026-*` contains the public startup shell, homepage and Support/Partner/About/Privacy pages.
- `cloudflare/base2026-worker/` contains the D1 search API, private proposal endpoints, migrations and tests.
- `cloudflare/base2026-www-redirect/` redirects the `www` hostname to the canonical apex domain.
- `scripts/audit-publication-boundary.py` checks the repository publication boundary.
- [`docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`](docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md) is the mandatory architecture, data-flow, security, operations and rollback reference for the cloud-only TikTok pipeline.

Generated website trees, public export artifacts, local databases and deployment archives are not committed.

The live private control plane is maintained in a protected operational
checkout and is not public source. Compare public `main` with current live
Worker versions and migration receipts before every deployment. The canonical
manual records this boundary so a fresh clone is never mistaken for the
private production control plane.

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
python3 -m pytest tests/test_base2026_design_authority.py -q
python3 scripts/check-base2026-design-authority.py
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

Current priorities are monitored indexation, strong source-backed topic evidence maps, versioned public data examples, provenance and creator-rights workflows. See [ROADMAP.md](ROADMAP.md) or the [live roadmap](https://base2026.dev/roadmap).

## Contributing and security

Contributions that improve public-safe code, source quality, accessibility, documentation and correction workflows are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [GOVERNANCE.md](GOVERNANCE.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

Base2026 is licensed under [Apache-2.0](LICENSE).
