# Publication Boundary

Base2026 has two layers:

1. public open-source product
2. private local research and operations assets

## Public-safe

- `AGENTS.md`
- `.agents/skills/`
- `.env.example`
- `.gitignore`
- `requirements-local-worker.txt`
- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `GOVERNANCE.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `.github/FUNDING.yml` when it contains only public sponsorship links or commented placeholders
- `docs/`
- `docs/public-pages/` public Markdown used to generate site info pages
- `scripts/`
- `contracts/`
- public-safe test fixtures under `tests/fixtures/public-export-*`
- `web/static/` source shell files, shared assets, public info pages, API metadata, and runtime JS/CSS
- `10_agent-instructions/`
- reviewed public-safe documentation under `12_knowledge-base/`
- `config/creator-profiles.json`
- public-safe examples under `config/`, such as `config/creators.example.json`
- public-safe generator source data under `data/`, such as `data/ai_visibility_pages_batch01.json`, after private absolute paths and unreviewed source material are removed
- the redacted canonical Cloudflare pipeline manual at
  `docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md`

## Do not commit

- private research folders listed in `docs/GIT_PUBLICATION_AUDIT.md`
- `.env`
- secrets, cookies, API keys, tokens, SSH keys
- raw captions unless explicitly reviewed
- ASR audio/video
- logs
- screenshots unless intentionally documented
- release zips
- imported roadmap/support source ZIPs such as `docs/*_roadmap_pack.zip`
- generated public export folders
- generated `web/static/sources/`, `web/static/topics/`, `web/static/compare/`, `web/static/creators/`, `web/static/sitemaps/`, and generated sitemap/analytics JSON artifacts
- TikTok intake queues and release target configs under `config/`
- Meilisearch local data
- private client workspaces
- `cloudflare/base2026-pipeline-control/` until a separate file-by-file source
  publication review admits it
- private Worker hostnames, account/database identifiers, Container image
  identifiers, signed requests, raw D1/R2 rows, and operational tail output

## Deployable but not committed

- `public-data/tiktok`
- release folder under `output/releases`
- `web/static/documents.jsonl` inside release package
- generated source/topic/compare/creator HTML pages under `web/static/`
- generated public sitemap files and public analytics JSON/JSONL under `web/static/`

Reason: these are generated artifacts. They can be uploaded to VPS, but should not become GitHub source unless intentionally sampled.

## Public demo content rule

The public demo must not publish raw scraped caption dumps or unreviewed third-party transcripts.

Preferred public layer:

- attributed source records;
- reviewed polished public source text/transcript where policy allows;
- short highlighted snippets for search-result previews;
- topic and insight cards;
- creator/source links;
- methodology and opt-out/correction path.

Raw captions, raw ASR, media, logs, private QA notes, and unreviewed transcripts remain private/local. A selected public source record may expose readable reviewed source text as the database surface when it is contextualized by Base2026-authored summaries, topics, insight cards, attribution, original source links, and correction/removal controls.

## Pre-stage rule

Before any `git add`, run:

```powershell
git status --short --branch
```

Then compare staged candidates against:

- `docs/GIT_PUBLICATION_AUDIT.md`
- this file

## Canonical Cloudflare pipeline documentation boundary

The public manual may name Worker roles, Cloudflare product classes, binding
names, state tables, schedules, gates, and non-secret versioned contracts so
future agents can understand the complete architecture. It must not contain
secret values, a private control endpoint, account/database IDs, raw artifacts,
signed headers, provider responses, private packet contents, or operational
logs.

The manual documents the production system; it does not make the private
control-plane source public-safe. A fresh public clone can therefore be behind
the live Worker, and an agent must reconcile source and migrations before any
deployment.

## Automatic Cloudflare-only publication boundary — 2026-08-23

The dedicated machine lane is live under `base2026.machine-publication.v1` (owner ref `owner-20260823-base2026-auto-publication-v1`, SHA-256 `b37c900a03eb63252c7736c2197f2be1eae3f117eae76914f3cbef306d89e573`, batch10, attempts4). `AUTOMATIC_PUBLICATION_ENABLED=true`, `IMPORT_ENABLED=true` and `PUBLIC_PROJECTION_ENABLED=true`; broad `PUBLIC_RELEASE_ENABLED=false` remains a separate intentional stop. `LOCAL_ADAPTER_ENABLED=false`; Cloudflare discovery runs at `0 10 UTC`, and reconcile/capture/automatic publication run every five minutes.

Automatic admission requires explicit `publication_eligible`, exact source/release/import/manifest tuple and RPC presence/verification. Synthetic fixture `7999999999999999933` is excluded, `full_transcript_public=0` remains enforced, leases are fenced, hard-hold stops the batch globally, and exhausted leases become terminal holds. Valid eligible packets need no user manual review; malformed, privacy-risk and mismatch states fail closed. The first live run applied two packets and recognized one already-public packet with zero retries/holds; public search found both new rows and the site hash was unchanged. Raw media, transcripts, provider responses, private packets, credentials and local paths remain outside public D1/assets.
