# Base2026 Source-backed Brief candidate

Date: 2026-09-04
State: reviewed local candidate; not deployed
Branch: `codex/base2026-source-backed-brief-20260904`
Base: `origin/main` at `946b771fd`

## Outcome

The candidate adds one public utility route:

`https://base2026.dev/tools/source-backed-brief/`

The release builder renders the route with the current startup shell, copies
its scoped CSS and JavaScript into the public static bundle, adds one hub
sitemap entry, and exposes the route in the public root/library LLMS entry
points. Evidence Search and the AI Visibility Resources hub each have one
contextual handoff link. Source Diversity and member/auth surfaces were not
changed.

The tool accepts a question, audience, `brief`/`memo`/`outline` deliverable and
up to eight unique canonical public record IDs
(`tiktok-video-<digits>` or a numeric video alias) or public source IDs
(`tiktok:<creator>:<video_id>`). Each accepted ID is resolved through the
existing anonymous, read-only `/api/mcp` `get_source` call using protocol
version `2026-07-28`, at most three concurrent requests and a 12-second
per-request timeout.

The output contract is `base2026.source-backed-brief.v1`:

- the request framing and exact accepted IDs remain visible in the snapshot;
- each record keeps its canonical record ID, returned public source ID, safe
  creator attribution, original-source URL and returned Base2026 source page
  URL when available;
- only the `excerpt` field from up to three public passages is copied per
  resolved record, bounded to 360 characters; passage IDs and chunk indexes
  remain attached when returned;
- unresolved records stay in input order with a visible status, lookup reason
  and unknown rather than a fabricated title, link or excerpt;
- missing attribution, source links, Base2026 links and excerpts are explicit
  unknowns; rejected input and duplicate IDs are counted;
- Markdown and JSON exports are generated locally from the same rendered
  snapshot, with Markdown escaping for user/record text and safe HTTPS links.

The public boundary is fail-closed: the response must prove
`public_read_only`, `raw_captions=false`, `raw_asr=false`,
`media_files=false`, `private_data=false` and `writes=false`. Full public
transcripts, private/needs-review/raw/media policy signals and non-HTTPS links
are rejected or omitted. The tool does not crawl, rank, compare source
independence, infer truth/consensus/agreement, call an LLM, use D1 directly,
write data, access auth/member state, or publish raw captions/transcripts or
media.

The only emitted analytics names are
`brief_required_fields_completed`, `brief_preview_created`, `brief_exported`
and `brief_completed`. Event properties are bounded buckets/status/format and
viewport values; question text, record IDs, source URLs and excerpts are not
sent to analytics.

## Changed-file manifest

- `scripts/audit-publication-boundary.py` — allow the new public-safe focused
  test in the existing publication audit.
- `scripts/build-base2026-cloudflare-release.py` — add route/template/asset
  constants and generated route/static/sitemap/LLMS wiring; recognize the
  public `tools` route family during path transformation.
- `templates/base2026-source-backed-brief.html` — canonical indexable route
  shell, no-JS method/boundary content, input form, result/export containers
  and WebApplication/BreadcrumbList schema.
- `templates/base2026-source-backed-brief.css` — scoped responsive styling
  using the existing `b26-independent-v1` tokens, mobile wrapping and reduced
  motion behavior.
- `templates/base2026-source-backed-brief.js` — bounded `get_source` lookup,
  public-boundary checks, deterministic normalization, unresolved handling,
  DOM-safe rendering, analytics and Markdown/JSON export.
- `templates/base2026-evidence-search.html` — replace the planned placeholder
  with one link to the implemented brief route.
- `templates/base2026-ai-visibility-resources.html` — add one honest resource
  hub link to the implemented brief route.
- `tests/test_base2026_source_backed_brief.py` — focused route/runtime/CSS,
  builder, escaping, eight-ID cap, unresolved-state, boundary and link tests.
- `tests/test_base2026_evidence_search_tool.py` — update the planned-link
  expectation to the implemented handoff.
- `tests/test_build_base2026_cloudflare_release.py` — update the additive
  fixture artifact-count expectation for the three brief route assets.
- `docs/project-memory/NEXT_ACTION.md` — record the held candidate and root
  review next action.
- `docs/project-memory/PROMPT_LOG.md` — record the implementation prompt and
  boundary.
- `docs/project-memory/HANDOFF_2026-09-04_SOURCE_BACKED_BRIEF.md` — this
  unique implementation receipt.

No generated `web/static` release artifact, private source vault, raw
transcript/media, local database, credential, auth/member binding, pipeline,
DNS, Worker, D1, Cloudflare deployment, IndexNow submission or external
automation was changed.

## Verification

- Focused Python tests: `15 passed` across the new brief, Evidence Search and
  Source Diversity suites.
- JavaScript syntax: `node --check templates/base2026-source-backed-brief.js`
  passed.
- Python syntax: `python3 -m py_compile` passed for the builder and focused
  tests.
- Builder fixture test rendered and byte-verified the route HTML, CSS and JS,
  hub sitemap and both LLMS entry points.
- Design authority check: `python3 scripts/check-base2026-design-authority.py`
  passed.
- Publication-boundary audit: `13` changed files, zero forbidden paths, zero
  needs-review paths and zero secret findings; `ok_to_stage_public_safe_candidates=true`.
- No Wrangler run or deployment was performed. Live HTTP, API/MCP,
  canonical/sitemap, analytics, mobile browser, indexation and traffic remain
  unverified for this local candidate.

## Root next action

Review this exact file manifest, the focused evidence/runtime tests and the
publication-boundary receipt. If approved, build a fresh reviewed Cloudflare
candidate from current public inputs and authorize deployment separately. Do
not claim this branch is live, indexed or traffic-producing. Merge/deploy is
outside this candidate handoff.
