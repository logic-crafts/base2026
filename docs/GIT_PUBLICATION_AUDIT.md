# Git Publication Audit

Date: 2026-06-06

## Commit Safe

- `.env.example`
- `.gitignore`
- `requirements-local-worker.txt`
- `README.md`
- `SECURITY.md`
- `docs/`
- `docs/BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md` after the
  exact staged diff passes redaction and secret review
- `scripts/`
- `scripts/tiktok-source-review-audit.py`
- the four reviewed UTF-8 source files under `plugins/wordpress/base2026-evidence-sidebar/`
  (`base2026-evidence-sidebar.php`, `assets/editor.js`, `readme.txt`, `LICENSE`)
- `web/static/` source shell files, shared assets, public info pages, API metadata, and runtime JS/CSS
- `10_agent-instructions/`
- `.agents/skills/`
- `config/creator-profiles.json`
- `config/creators.example.json`
- public-safe readmes under `12_knowledge-base/`

## Do Not Commit

- `.planning/`
- `.playwright-mcp/`
- `output/`
- `meili_data/`
- `public-data/`
- `manifest.json`
- `00_sources/`
- `01_core-methodology/`
- `02_factor-maps/`
- `03_sops/`
- `04_checklists/`
- `05_templates/`
- `06_prompt-bank/`
- `07_client-workspaces/`
- `08_experiments/`
- `09_sales-packaging/`
- `11_dreamwood_offer/`
- `99_original_research/`
- `12_knowledge-base/indexes/`
- `12_knowledge-base/sources/`
- generated canonical claims/methods/risks/topic maps
- generated `web/static/sources/`, `web/static/topics/`, `web/static/compare/`, `web/static/creators/`, `web/static/sitemaps/`, sitemap XML, and public analytics JSON/JSONL artifacts
- any `.env`, raw captions, ASR audio, screenshots, logs, release zips
- imported roadmap/support source ZIPs such as `docs/*_roadmap_pack.zip`
- `config/tiktok-intake-queue*.json`
- `config/release-target*.json`
- `cloudflare/base2026-pipeline-control/` until a separate source-publication
  audit explicitly admits each file
- live operational receipts that expose private Worker hosts, account/database
  identifiers, Container image identifiers, signed requests, or raw D1/R2 rows

The installable WordPress beta ZIP is a generated download, not a Git source
file. Its release builder uses only the four reviewed plugin files above;
it never packages the repository, operational state, tests or a release tree.
The single exact download path is regenerated, not inherited from old assets.

Non-secret Worker roles, binding names, table/state contracts, schedules,
fail-closed gates, and redacted deployment snapshots may be documented in the
canonical operating manual. This does not admit the private implementation or
its generated artifacts to Git.

## First Commit Shape

Recommended first commit:

```text
Initial Base2026 public TikTok knowledge app
```

Include only safe app code, docs, workflow scripts, and public-safe instructions.

Keep generated public export out of git. It is rebuilt by:

```powershell
python .\scripts\export-public-tiktok.py
```
