# Base2026

Base2026 is a free, open-source video research engine and source-first evidence library. It turns selected public practitioner videos into attributed, searchable passages with original links and context, so a researcher can move from a question to the source. Selection improves retrieval and context; it does not certify that a recommendation or claim is true.

Built and maintained by solo founder Alex Yarosh.

- Product: <https://base2026.dev/>
- Repository: <https://github.com/offflinerpsy/base2026>
- Search workspace: <https://base2026.dev/workspace/>
- Search inside expert videos: <https://base2026.dev/tools/evidence-search/>
- Source diversity check: <https://base2026.dev/tools/source-diversity-check/>
- Source-backed brief builder: <https://base2026.dev/tools/source-backed-brief/>
- Public dataset: <https://base2026.dev/dataset>
- Live source catalog: <https://base2026.dev/sources/>
- Maintained guides API: <https://base2026.dev/api/guides>
- Blog: <https://base2026.dev/blog>
- Blog RSS: <https://base2026.dev/blog/feed.xml>
- Methodology: <https://base2026.dev/methodology>
- Investor overview: <https://base2026.dev/investors>
- Public roadmap: <https://base2026.dev/roadmap>
- Factory scenario: <https://base2026.dev/factory/>
- Support: <https://base2026.dev/support>
- Partnerships: <https://base2026.dev/partner>

## Why Base2026 exists

Useful expert knowledge is increasingly published in short-form video, but it is difficult to search, verify and cite. Platform feeds are optimized for viewing, not research. Search engines and AI agents often lose the original speaker, timestamp and context.

Base2026 creates a public evidence layer that keeps those connections visible. The founder and team select creators for practical relevance, usefulness and provenance. Base2026 does not accept paid creator placement or creator applications; the original source remains the reference point, with correction and removal paths available.

## What the product does

- discovers public expert sources in SEO, GEO, AEO, AI search and adjacent fields;
- converts selected public practitioner videos into attributed, searchable passages with original links and evidence context;
- preserves creator attribution, original-source links and evidence context;
- generates source, creator, topic and comparison pages;
- exposes public-safe machine-readable files for scripts and AI agents;
- provides a Cloudflare Worker search API backed by D1 FTS5;
- publishes original source-linked research articles through a separate reviewed editorial path;
- maintains task-focused topic guides with exact evidence dependencies and useful decision tools;
- documents methodology, corrections, opt-out and publication boundaries.

## Developer access

### Free WordPress Evidence Sidebar beta

Research one SEO/GEO question from Gutenberg, inspect an original source and
optionally insert an editable attributed research note. There is no Base2026
account, API key or paid AI setup. Only the short topic is sent after Search;
the plugin does not automatically upload a draft or publish a post.

The [plugin source and installation instructions](plugins/wordpress/base2026-evidence-sidebar/readme.txt)
are available for review. The [installable beta and guide](https://base2026.dev/tools/wordpress-evidence-sidebar/)
are live. WordPress 6.5+, PHP 7.4+, GPL-2.0-or-later.
The website download, directory acceptance and real user adoption are separate
release outcomes; see the [Product Studio handoff](docs/project-memory/HANDOFF_2026-09-05_PRODUCT_STUDIO.md).

### Free SEO Experiment Planner skill

Use Base2026 in an existing agent workflow: investigate a content page's decline
and produce one source-attributed experiment with a measurement worksheet.
The pack is free; your agent/provider costs are separate. It does not promise
rankings, invent keyword volumes or upload private GSC exports to Base2026.

```bash
npx skills add offflinerpsy/base2026 --skill base2026-seo-experiment-planner --agent codex
```

[Install for Codex or Claude Code](docs/BASE2026_FREE_SKILLS.md) ·
[See a complete worked example](docs/examples/content-refresh-experiment.md) ·
[Inspect the skill](.agents/skills/base2026-seo-experiment-planner/SKILL.md)

### Public API and MCP

The public developer surface is read-only and keyless. The compatible search
API provides bounded retrieval, and the stateless MCP endpoint provides
AI-agent lookups over the same public evidence boundary:

```bash
curl -sS -X POST https://base2026.dev/api/search/multi-search \
  -H 'content-type: application/json' \
  --data '{"queries":[{"indexUid":"base2026_public_tiktok","q":"AI search","limit":5}]}'

codex mcp add base2026 --url https://base2026.dev/api/mcp
claude mcp add --transport http base2026 https://base2026.dev/api/mcp
```

The MCP contract is limited to `search_sources`, `get_source`, `get_creator`,
`get_topic`, `get_topic_signal` and `get_public_manifest`. It reads only
allowlisted public D1 data and does not expose raw captions, raw ASR, media,
private records, credentials, writes, moderation or publication controls. See
the [API guide](docs/public-pages/08_API_ACCESS.md),
[MCP guide](docs/public-pages/10_MCP_FOR_AI_AGENTS.md) and
[integration guide](docs/public-pages/11_PLUGINS_AND_INTEGRATIONS.md).

The public product is a live working prototype. The [product experience
release](docs/project-memory/HANDOFF_2026-09-06_PRODUCT_EXPERIENCE.md) records
the current reviewed site and public factory scenario. Live corpus dimensions
are available from the read-only
[`/api/stats`](https://base2026.dev/api/stats) endpoint and must not be treated
as users, revenue, universal coverage or commercial traction. Public full
transcripts remain disabled by design; the public product exposes bounded
excerpts with attribution instead.

Maintained task guides cover internal linking, content refresh, Search Console
opportunity selection, structured-data checks and llms.txt consumer evaluation.
They are original, source-linked decision workflows at existing topic URLs,
separate from the blog. An initial recurring editorial run published reviewed
guides without a Worker redeploy; see the
[data-only publication receipt](docs/project-memory/BASE2026_EDITORIAL_OFFICE_RUN_2026_08_31.md).
Original research articles are available, including an
[evidence-first content backlog](https://base2026.dev/blog/evidence-first-content-backlog/)
and a [comparison-page evidence check](https://base2026.dev/blog/comparison-page-evidence-check/),
both built from existing reviewed sources. The same editorial office can produce
useful new work without waiting for new videos; unchanged guides are not redated.
Publication and accepted discovery requests do not establish traffic growth.
See the [source synchronization and quality receipt](docs/project-memory/BASE2026_OFFICE_CLOSURE_2026_08_31.md).

## Product and operating boundary

Base2026's free product includes Evidence Search, Source Diversity Check,
Source-backed Brief, the WordPress Evidence Sidebar, public API access and the
read-only MCP interface described above. A proposed commercial pilot would test
whether small SEO practices return to Base2026 for recurring client research
decisions; it is unproven, and there is no shipped paid plan or claim of
traction, ROI or funding.

The public [`/factory/`](https://base2026.dev/factory/) route is a separate
English playable authored Scenario. A private local AgencyOS snapshot UI is an
operational view for the project; its database and implementation are not
published here and are not a separate startup release. The factory scenario and
that private operational view do not change the public product boundary.

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

## Original research blog

The [blog](https://base2026.dev/blog) connects original practical articles with
the evidence library. Approved structured articles are validated, reviewed
against an exact content hash, then published through an authenticated private
receiver and Worker service binding into separate public D1 editorial tables.
HTML, the [read-only article API](https://base2026.dev/api/blog), RSS and the
blog sitemap update without rebuilding the site for each text publication.
Retries are idempotent; corrections require an explicit revision comparison.
Existing journal URLs remain unchanged.

Sources, contextual research links and AI-assistance disclosures are visible.
Assisted research and review remain bounded by the public/private publication
contract; the cloud serves
published articles independently. No unlimited, cloud-only ChatGPT Pro
authoring service is claimed.

See the [editorial operating contract](docs/BASE2026_EDITORIAL_PUBLISHING.md)
and the [first live publication/replay receipt](docs/project-memory/BASE2026_EDITORIAL_RUNTIME_RELEASE_2026_08_30.md).

## Maintained evidence guides

A video is an input, not automatically another SEO page. Relevant public
evidence can improve a maintained guide at an existing topic URL. Each guide
answers a concrete task, attributes the evidence, separates observed practices
from Base2026 synthesis, and offers a decision or verification step. The blog
remains separate for original research stories.

Guide publication binds short supporting quotes to exact public document hashes.
The Worker rechecks source eligibility and dependencies before serving a guide;
changed or withdrawn evidence holds the page for repair. An exact-hash semantic
review is still required: matching bytes do not establish truth or reuse rights.
No model call is made on a public request. A new text revision uses the same
authenticated data-only publisher, without rebuilding the website.

The [live catalog](https://base2026.dev/sources/) provides bounded crawlable
navigation to cloud-added source records and preserves the labeled legacy
selection. [Guide metadata](https://base2026.dev/api/guides) and the separate
[guide sitemap](https://base2026.dev/sitemap-guides.xml) describe actual
published guides, not the number of videos or promised traffic.

See the [evidence-to-SEO operating manual](docs/BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md)
for source-delta research, merge/update rules, read-time holds and host limits.

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
npm --prefix cloudflare/base2026-worker ci
npm --prefix cloudflare/base2026-worker run typecheck
npm --prefix cloudflare/base2026-worker test
```

The import and Static Assets dry-runs require reviewed generated data that a
clean clone intentionally does not contain. Pass the public JSONL input and
candidate asset directory explicitly when they live outside the checkout:

```bash
node cloudflare/base2026-worker/scripts/import-public-chunks.mjs \
  --dry-run --input /absolute/path/to/reviewed/passages.jsonl
cd cloudflare/base2026-worker
npx wrangler deploy --dry-run --assets /absolute/path/to/reviewed/candidate-web
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

**Now:** improve free evidence search, practical tools, navigation, source
explanations, attribution and correction paths.

**Next:** measure repeat research and test a proposed recurring workflow with
small SEO practices while keeping the public search and tools free.

**Exploring:** consider commercial integrations only after repeated use and
responsible delivery provide evidence. See [ROADMAP.md](ROADMAP.md) or the
[public roadmap](https://base2026.dev/roadmap).

## Contributing and security

Contributions that improve public-safe code, source quality, accessibility, documentation and correction workflows are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [GOVERNANCE.md](GOVERNANCE.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

Base2026 is licensed under [Apache-2.0](LICENSE).
