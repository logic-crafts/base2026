# Handoff: Base2026 public API, MCP and agent integrations

Date: 2026-09-01
Branch: `codex/base2026-growth-integration-20260901`
Base: `codex/base2026-google-auth-20260831` at `561a917eb0706173cc71cf97721d45430111061c`
Status: local integrated candidate; no push, merge or Cloudflare deployment occurred

## Outcome

This candidate adds a small public developer-distribution surface over the
existing public-safe Base2026 evidence projection:

- `POST /api/mcp` in the existing public Worker;
- six bounded, read-only MCP tools;
- current `2026-07-28` discovery with an intentional `-32601` rejection for
  modern `initialize`, while retaining compatible legacy 2025 `initialize`;
- free API, MCP, Codex and Claude Code documentation;
- indexable `/api`, `/mcp` and `/integrations` pages using the current
  Base2026 startup shell;
- public-only `api-index.json`, `data-dictionary.json`, `llms.txt` and
  `llms-root.txt` contracts;
- a repository-local instruction-only skill and explicit non-marketplace
  integration manifest.

The route is implemented and locally tested, but it is not live until a
separate deployment receipt, live smoke test and rollback record exist. The
current public baseline was read without mutation: `GET /api/health` returned
200, the existing `POST /api/search/multi-search` returned 200 for `AI search`,
and the undeployed `GET /api/mcp` returned the expected pre-release 404.
The local candidate fails closed unless the configured Cloudflare
`MCP_RATE_LIMIT` binding is present (60 requests/minute per edge identity);
binding configuration and live readback remain release blockers.

## Public routes and machine files

| Surface | Contract |
| --- | --- |
| Existing API health | `GET https://base2026.dev/api/health` |
| Existing live search | `POST https://base2026.dev/api/search/multi-search` |
| Candidate MCP server | `POST https://base2026.dev/api/mcp` |
| Human API page | `GET https://base2026.dev/api` |
| Human MCP page | `GET https://base2026.dev/mcp` |
| Human integrations page | `GET https://base2026.dev/integrations` |
| Agent context | `GET https://base2026.dev/llms.txt` |
| Public API index | `GET https://base2026.dev/api-index.json` |
| Public data dictionary | `GET https://base2026.dev/data-dictionary.json` |
| Dated static manifest | `GET https://base2026.dev/static/manifest.json` after a populated release build |

The MCP tool names are exactly:

1. `search_sources` - distinct public source summaries with bounded excerpts;
2. `get_source` - one source with at most eight passages and three applied cards;
3. `get_creator` - public creator metadata, topic counts and at most ten source samples;
4. `get_topic` - public topic counts, creator samples and at most ten source samples;
5. `get_topic_signal` - deterministic public-D1 evidence gate, not a trend score;
6. `get_public_manifest` - live public-D1 dimensions and endpoint/policy links.

MCP request bodies are capped at 64 KiB. `search_sources` is capped at 20
results and offset 1,000; all other samples are bounded in the implementation.
Modern requests use JSON-RPC 2.0 with `MCP-Protocol-Version`, `Mcp-Method`,
matching `params._meta` protocol metadata, and `Mcp-Name` for `tools/call`.
Modern `initialize` is deliberately rejected as unsupported (`-32601`), while
legacy 2025 `initialize` remains available; `ping` returns
`{"resultType":"complete"}`. Any request without an `id`, including
`tools/call`, is accepted with HTTP 202 and an empty body without dispatching to
D1. Explicit `notifications/initialized` and `notifications/cancelled`
handling remains intact. The handler is stateless JSON-only HTTP: no session
IDs, SSE, DELETE or writes.
Requests are protected by `MCP_RATE_LIMIT` and return `429` with a retry hint
when the per-identity minute budget is exhausted; an unavailable binding
returns `503` and does not execute D1.

## Security and privacy boundary

The MCP handler reads only the public Worker `DB` binding and the public tables
`search_documents`, `search_topics`, `public_projection_receipts` and
`public_projection_cards`. It does not reference the Worker’s separate
`INBOX_DB` or `OUTREACH_DB` bindings and does not widen the existing public
search contract.

The response projection contains only public source metadata, short bounded
evidence excerpts, public topic/creator fields, attribution and applied public
cards. It excludes raw captions, raw ASR, full private transcripts, media,
private review packets, inbox/lead data, credentials, logs, control-plane
state, moderation and publication actions. Every tool result includes a
`public_boundary` object. Original source URLs remain required attribution;
Base2026 source-page URLs are returned only for an applied card with a numeric
video ID.

## Exact local verification commands

Run from the repository root in the isolated worktree:

```bash
git switch codex/base2026-growth-integration-20260901

cd cloudflare/base2026-worker
npm ci
npm run typecheck
npm test
MCP_DRYRUN_ASSETS="$(mktemp -d /tmp/base2026-mcp-dryrun.XXXXXX)"
npx wrangler deploy --dry-run --assets "$MCP_DRYRUN_ASSETS"
cd ../..

python3 -m py_compile scripts/generate-info-pages.py scripts/build-base2026-cloudflare-release.py
python3 -m pytest -q
python3 scripts/check-base2026-design-authority.py
git add <reviewed-candidate-paths>
python3 scripts/audit-publication-boundary.py --json
git diff --check
```

The publication audit must run after the candidate paths are staged (or against
an equivalent real diff), so its receipt must show the integrated changed-file
set rather than `changed_files=0`. Never create a private or raw substitute to
make an importer or release gate appear green.

For a populated public source artifact, build a new non-overwriting candidate
and then point the local Wrangler config at that candidate path (or copy the
candidate contents into the configured ignored `output/cloudflare-migration/candidate-web`):

```bash
python3 scripts/generate-info-pages.py --source docs/public-pages --out web/static
python3 scripts/build-base2026-cloudflare-release.py \
  --source-web output/cloudflare-migration/source-web \
  --out output/cloudflare-migration/candidate-web-20260901-api-mcp

cd cloudflare/base2026-worker
npm run wrangler:dry-run
cd ../..
```

The standalone builder gate must report zero stale-origin, local-path,
private-token, personal-shell, WordPress-form, personal-route and
personal-commercial markers, and must include `/mcp` and `/integrations` in
`sitemaps/base2026-hubs.xml`.

Local worker smoke request for the modern discovery contract:

```bash
curl -sS https://base2026.dev/api/mcp \
  -H 'content-type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  --data '{"jsonrpc":"2.0","id":"discover","method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
```

Use that smoke request only after deployment. Before deployment it is expected
to return the current public 404 and must not be described as a live feature.

## Files changed

Worker and tests:

- `cloudflare/base2026-worker/src/index.ts`
- `cloudflare/base2026-worker/src/mcp.ts`
- `cloudflare/base2026-worker/tests/mcp.test.ts`
- `cloudflare/base2026-worker/wrangler.jsonc`

Public docs and integration guidance:

- `README.md`
- `docs/public-pages/01_ROADMAP.md`
- `docs/public-pages/08_API_ACCESS.md`
- `docs/public-pages/10_MCP_FOR_AI_AGENTS.md`
- `docs/public-pages/11_PLUGINS_AND_INTEGRATIONS.md`
- `docs/integrations/base2026-public-mcp/SKILL.md`
- `docs/integrations/base2026-public-mcp/integration-manifest.json`

Build, packaging and design authority:

- `scripts/build-base2026-cloudflare-release.py`
- `scripts/generate-info-pages.py`
- `scripts/package-public-release.ps1`
- `scripts/package-public-hotfix-from-export.ps1`
- `templates/base2026-core.css`
- `templates/base2026-startup-header.html`
- `templates/base2026-startup-footer.html`

Generated public pages and machine contracts:

- `web/static/api-index.json`
- `web/static/api.html`
- `web/static/apply-research.html`
- `web/static/data-dictionary.json`
- `web/static/integrations.html`
- `web/static/llms-root.txt`
- `web/static/llms.txt`
- `web/static/mcp.html`
- `web/static/methodology.html`
- `web/static/opt-out.html`
- `web/static/privacy.html`
- `web/static/roadmap.html`
- `web/static/site-structure.html`
- `web/static/source-policy.html`
- `web/static/story.html`
- `web/static/support.html`

Tests and project memory:

- `tests/test_build_base2026_cloudflare_release.py`
- `tests/test_root_llms_contract.py`
- `docs/project-memory/ACTIVE_PHASE.md`
- `docs/project-memory/DECISIONS.md`
- `docs/project-memory/NEXT_ACTION.md`
- `docs/project-memory/PROMPT_LOG.md`

`DATA_SOURCES.md` and `STATUS_BOARD.csv` were intentionally not changed:
the public source status and phase state did not change in this candidate.

## Verification receipts from this pass

- Worker Vitest: 12 files / 625 tests passed; targeted MCP suite 11/11.
- Worker TypeScript: `npm run typecheck` passed.
- Python full suite: 171 passed; relevant integration subset: 39 passed.
- Python compile checks for the generator and release builder: passed.
- Design-authority check: passed.
- Info-page generator: `info_pages=12`; API, MCP and integrations pages
  regenerated from the source Markdown.
- Wrangler dry-run: completed with an empty temporary assets directory; the
  binding inventory included `MCP_RATE_LIMIT` at 60 requests/60 seconds; no
  deployment performed.
- Publication audit: the full base-to-candidate snapshot (auth base plus the
  staged reviewer fixes) reported `changed_files=61`, all 61 public-safe,
  `forbidden=[]`, `needs_review=[]`, and `secret_findings=[]`.
- No public source export was present in this isolated worktree, so no import
  or populated standalone artifact was manufactured for this pass.
- Live read-only baseline: `/api/health` 200; existing search API 200;
  candidate `/api/mcp` 404 because this branch was not deployed.

## Integration order

1. Review this handoff, the diff and the publication-boundary output.
2. Rebuild from the newest public-safe export and repeat worker, static,
   builder, API and browser gates; do not use private/raw source substitutes.
3. Obtain an explicit release/deploy decision; this candidate alone does not
   authorize Cloudflare mutation.
4. Deploy the public Worker and static asset candidate while leaving D1 schema
   and private pipeline bindings unchanged.
5. Read back `/api/health`, `/api/search/multi-search`, `/api/mcp`, `/mcp` and
   `/integrations`; run modern MCP discovery, `tools/list`, one bounded
   `search_sources` call and one invalid-header rejection.
6. Record the deployed Worker version, static receipt, live smoke responses and
   rollback target before any sitemap/indexation submission.
7. Only after that receipt, update the project memory with live status; keep
   Outreach, Inbox, raw media/ASR and all public write/control routes outside
   this integration.

Suggested commit message: `feat: add public Base2026 MCP and developer access`
