# Base2026 Source Diversity Check candidate

Date: 2026-09-04 19:14 UTC
State: reviewed local candidate; not deployed
Branch: `codex/base2026-source-diversity-check-20260904`
Base: `origin/main` at `09a24a6f28184e50aea73f025c88a61c750bbb20` (PR44)

## Outcome

The candidate adds one public utility route:

`https://base2026.dev/tools/source-diversity-check/`

The release builder renders the route with the current startup shell, copies
its scoped CSS and JavaScript into the public static bundle, and adds one hub
sitemap entry. Evidence Search has one contextual handoff link that carries a
bounded set of validated record IDs. The existing AI Visibility Resources page
has one honest hub link. No live route or sitemap was changed.

The tool accepts up to 12 canonical Base2026 record IDs
(`tiktok-video-<digits>` or the numeric video alias) or canonical public source
IDs (`tiktok:<creator>:<video_id>`). Each accepted ID is resolved through the
existing anonymous, read-only `/api/mcp` `get_source` call with protocol
version `2026-07-28`, at most three concurrent requests and a 12-second
per-request timeout. It does not crawl, rank, query backlinks or Search
Console, call an LLM, assign a score, or write to Base2026.

The output contract is `base2026.source-diversity-check.v1`:

- exact accepted record identities are grouped separately from creators,
  normalized original-source URLs and public source IDs;
- `distinct_records`, `distinct_sources` and `distinct_creators` are separate
  counts, with `resolved_records` and unresolved metadata counts shown beside
  them;
- creator groups use an attributed normalized handle or name;
- source groups remove query/fragment noise, trailing slashes and the `www.`
  host alias while retaining the original HTTPS URL on each card;
- failed lookups and missing creator/source metadata remain visible in the
  record list and both Markdown and JSON exports;
- the public boundary requires `public_read_only`, no raw captions/ASR/media,
  no private data and no writes. Only bounded metadata is copied from the
  response; passages and applied cards are ignored.

The page states visibly that diversity is not consensus or truth. Decisions
are local browser notes only. Analytics emits only the bounded event names
`source_check_run`, `source_check_completed`,
`source_check_decision_recorded` and `source_check_card_copied`, without record
IDs or source text in event properties.

## Changed files

- `scripts/build-base2026-cloudflare-release.py` — additive route/template/
  asset wiring and hub sitemap entry.
- `templates/base2026-source-diversity-check.html` — canonical indexable tool
  shell, visible boundary, form, results/export containers and valid
  WebApplication/BreadcrumbList schema.
- `templates/base2026-source-diversity-check.css` — scoped responsive styling
  using the existing `b26-independent-v1` token system.
- `templates/base2026-source-diversity-check.js` — bounded MCP lookup,
  deterministic grouping, unresolved-state handling, decisions, analytics and
  Markdown/JSON export.
- `templates/base2026-evidence-search.html` and
  `templates/base2026-evidence-search.js` — one contextual handoff from
  selected admitted results.
- `templates/base2026-evidence-search.css` — handoff card styling.
- `templates/base2026-ai-visibility-resources.html` — one hub link.
- `tests/test_base2026_source_diversity_check.py`,
  `tests/test_base2026_evidence_search_tool.py` and
  `tests/test_build_base2026_cloudflare_release.py` — focused route, handoff,
  builder and boundary assertions.

## Verification

- Focused Python/build/public-artifact tests: `41 passed`.
- Worker tests: `634 passed` across 13 Vitest files.
- Worker TypeScript: `npm run typecheck` passed.
- JavaScript syntax: `node --check templates/base2026-source-diversity-check.js` passed.
- Python syntax: `python3 -m py_compile scripts/build-base2026-cloudflare-release.py` passed.
- `git diff --check` passed.
- Wrangler dry-run was attempted but could not start because the checkout has
  no generated release assets at the configured
  `output/cloudflare-migration/base2026-enrichment-retirement-20260831-v2`
  directory. This is an expected local-candidate limitation; no deployment
  occurred. The builder test still rendered and verified the route and assets.
- Publication-boundary audit: 6 changed files, zero forbidden paths, zero
  needs-review paths and zero secret findings.

## Boundaries and next action

No Worker, MCP, D1, member-auth, Google binding, secret, relay, pipeline,
Cloudflare deployment, IndexNow submission, automation, browser, or generated
public export file was changed. No push or merge was performed.

Next action for the root command center: review this exact commit and the
public-boundary receipt. If accepted, build a fresh reviewed Cloudflare
candidate from the current public export and authorize deployment separately;
then perform live route, API, canonical, sitemap, mobile and analytics
readback. Do not claim the route is live, indexed or traffic-producing from
this local candidate.
