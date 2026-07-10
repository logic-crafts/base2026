# Base2026 Video Source Intelligence

Base2026 is a local-first, public-facing source intelligence system for short-form expert videos.

The current public demo focuses on TikTok creators talking about SEO, GEO, AEO, AI search visibility, schema, keyword research, Google, Bing, and related topics.

Live demo: <https://aggressorbulkit.online/knowledge/>

## Project Identity and Ownership

Base2026 is an independent experimental startup product created by Alex Yarosh. Ownership and rights belong to Logic Crafts LLC, Kyrgyzstan. Base2026 is not a marketing agency, does not represent marketing agency services, and should not be evaluated as a marketing-services business. It is a productized public source-intelligence and knowledge-base system for short-form expert video.

Public API and AI access: <https://aggressorbulkit.online/knowledge/api.html>

## Public API & AI Access

Base2026 is built to be useful to humans and agents. The public site exposes a
read-only, public-safe API surface so AI tools, scripts, researchers, and search
systems can inspect the library without scraping the visual UI.

Start here:

- API overview: <https://aggressorbulkit.online/knowledge/api.html>
- Machine-readable API index: <https://aggressorbulkit.online/knowledge/api-index.json>
- Agent context file: <https://aggressorbulkit.online/knowledge/llms.txt>
- Data dictionary: <https://aggressorbulkit.online/knowledge/data-dictionary.json>
- Public documents JSONL: <https://aggressorbulkit.online/knowledge/static/documents.jsonl>
- Public passages JSONL: <https://aggressorbulkit.online/knowledge/static/passages.jsonl>
- Public insight cards JSONL: <https://aggressorbulkit.online/knowledge/static/insight_cards.jsonl>

The API surface is intentionally public-only. It does not expose raw captions,
raw ASR, media files, private QA notes, local databases, credentials, logs, or
unreviewed pipeline artifacts.

## What It Does

- converts public creator videos into searchable English source text and evidence passages;
- keeps raw captions, raw ASR output, media, private QA notes, and unreviewed transcripts local/private;
- can expose reviewed polished public source text/transcript as a source-record reading surface where policy allows;
- exports public-safe source records, passages, insight cards, topics, and creator metadata;
- indexes searchable passages with Meilisearch;
- serves a static read-only web UI under `/knowledge/`;
- generates creator, source, topic, and comparison pages from public JSONL.
- exposes agent-readable public entry points (`/knowledge/llms.txt`, `/knowledge/data-dictionary.json`, `/knowledge/api-index.json`) so AI tools can inspect the public library without scraping the visual UI.

The public site is designed for source discovery, attribution, comparison, citation, and searchable source reading. It is not a video re-hosting platform and not a raw transcript dump.

## Current Status

Latest deployed release: `base2026-source-intelligence-contract-ay54-20260619`.

Current public export:

- 1,476 source records;
- 2,016 searchable passages;
- 1,631 insight cards;
- 1,060 public insight cards;
- 1,522 topics;
- 1,008 public topics;
- 10 creator profiles.

Recent readiness checks:

- public export policy: current live release uses reviewed public source text where policy allows and continues to forbid raw/unreviewed transcript dumps;
- newest-source readiness: latest public sources must have reviewed topics or Source Intelligence before release;
- publication boundary audit: passing with `forbidden=0` and `secret_findings=0` in the current launch-readiness pass;
- GitHub metadata validation: passing for the public repository metadata, homepage, license, and topics;
- live SEO crawl gate: passed on 500 crawled pages with 0 P0 bad links and 0 crawled error pages;
- mobile visual QA: passed 78 public UI checks with 0 failures.

## Current Public Shape

Public pages:

- `/knowledge/`
- `/knowledge/creators/{handle}.html`
- `/knowledge/sources/{item_id}.html`
- `/knowledge/topics/{topic_id}.html`
- `/knowledge/compare/{topic_id}.html`
- `/knowledge/roadmap.html`
- `/knowledge/story.html`
- `/knowledge/methodology.html`
- `/knowledge/privacy.html`
- `/knowledge/source-policy.html`
- `/knowledge/support.html`
- `/knowledge/site-structure.html`
- `/knowledge/opt-out.html`

Public data files generated locally:

- `source_records.jsonl`
- `passages.jsonl`
- `insight_cards.jsonl`
- `topics.jsonl`
- `creators.jsonl`
- `manifest.json`

Compatibility files:

- `documents.jsonl`
- `chunks.jsonl`

Agent-readable public files:

- `/knowledge/llms.txt`
- `/knowledge/api.html`
- `/knowledge/api-index.json`
- `/knowledge/data-dictionary.json`

The public search UI also uses a server-side Meilisearch proxy at `/knowledge-search/multi-search`. The proxy is read-only and injects the public search key server-side; integrations should prefer static JSONL for bulk/offline analysis.

Generated public data and release archives are deploy artifacts, not GitHub source.

## Public Boundary

Do not commit or publish:

- private research folders;
- local SQLite databases;
- raw captions;
- ASR audio/video;
- cookies, tokens, API keys, SSH keys;
- generated release zips;
- generated `public-data/`;
- local Meilisearch data;
- logs.

Raw captions, raw ASR, media, private QA notes, and unreviewed transcripts are private/local. Reviewed polished public source text may be shown where policy allows. Public source pages and source detail must show attribution, original links, source context, methodology, and correction/opt-out paths.

## What This Repository Is For

This repository is intended to show the public-safe system layer:

- data contracts for public source records, passages, insight cards, topics, and creator metadata;
- static page generation for search, creator, source, topic, comparison, roadmap, methodology, policy, support, and correction/removal pages;
- local worker scripts for export, validation, indexing, packaging, and deployment;
- project memory and runbooks for repeatable operation;
- open-source issue templates and contribution paths.

Private research data, raw platform material, local databases, and deploy archives are intentionally excluded.

## Architecture

```text
creator registry
  -> local intake / captions / ASR
  -> transcript cleanup and QA
  -> passage chunking
  -> topic and insight extraction
  -> public JSONL export
  -> static page generation
  -> Meilisearch passage index
  -> read-only public UI under /knowledge/
```

No live LLM call is required during public search.

## Local Commands

Export public TikTok data:

```bash
python3 scripts/export-public-tiktok.py
python3 scripts/check-public-export-policy.py public-data/tiktok
```

Do not use implicit public-card promotion for GitHub or public release preparation. Public insight cards should come from reviewed source-backed rows, not from one-off export flags.

Index passages into Meilisearch:

```bash
python3 scripts/meili-index-public.py --index base2026_public_tiktok
```

Package a public release:

```bash
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/package-public-release.ps1 -ReleaseName <release-name>
```

Current public packages can include reviewed public source text where policy allows. Do not use `-IncludeFullTranscripts` or `--auto-promote-insights` for public deploys; raw captions, raw ASR, media, private QA, and unreviewed transcripts stay private.

Deploy to the VPS:

```bash
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/deploy-public-vps.ps1 -ReleaseName <release-name>
```

Audit before staging for GitHub:

```bash
python3 scripts/audit-publication-boundary.py
python3 scripts/validate-github-metadata.py
pwsh -NoProfile -ExecutionPolicy Bypass -File ./scripts/preflight-github-launch.ps1 -SkipExportPolicy -SkipLiveCheck
```

## Project Docs

- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Governance](GOVERNANCE.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- Funding links are declared in `.github/FUNDING.yml` when public sponsorship accounts are ready.

## Project Control

Agents and maintainers should start from repo files, not chat memory.

Read first:

- `AGENTS.md`
- `docs/project-memory/ACTIVE_PHASE.md`
- `docs/project-memory/NEXT_ACTION.md`
- `docs/project-memory/STATUS_BOARD.csv`
- `docs/project-memory/PUBLICATION_BOUNDARY.md`
- `docs/GIT_PUBLICATION_AUDIT.md`

## About the Maintainer

Base2026 is created and maintained by [Alex Yarosh](https://aggressorbulkit.online/about/), an independent AI Search Visibility consultant working across SEO, GEO, AEO, local search, entity/trust signals, and public source intelligence.

Alex is building Base2026 as an independent pilot project for studying how public expert knowledge can become searchable, attributable, and useful to both humans and AI systems.

- Website: <https://aggressorbulkit.online/>
- Live Base2026 demo: <https://aggressorbulkit.online/knowledge/>
- Contact: <offflinerpsy@gmail.com>

## Contribution Areas

Useful contributions include:

- extractor adapters for additional public short-form platforms;
- caption and ASR quality benchmarks;
- safer public export validators;
- Meilisearch ranking and faceting improvements;
- static page, schema, sitemap, and accessibility improvements;
- creator correction/removal workflow improvements;
- documentation that makes local operation easier.

Please do not submit raw third-party captions, unreviewed transcripts, media files, cookies, credentials, or private research exports.

## License

Repository code and documentation are licensed under Apache-2.0. Third-party creator videos, platform captions, and original source content are not relicensed by this repository.
