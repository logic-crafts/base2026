# Publication Boundary

Base2026 has two layers:

1. public open-source product
2. private local research and operations assets

## Public-safe

- `AGENTS.md`
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
