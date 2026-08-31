# Base2026 maintained evidence guides — live release

Verified 2026-08-30. This is a deployed runtime and first-guide receipt, not a
traffic result. Phase 20 remains the historical first-blog release.

## Exact production

- Public Worker: `a63f4c74-b6b2-4935-a392-61003d28567a`, 100%.
- Artifact: `base2026-seo-evidence-20260830-v1`; 4,245 served files,
  89,875,862 bytes; tree SHA-256
  `fa3626039508a4ab4a483044c8336b93a8f63eebb3798bcc46c3e8b15620aa39`.
- Five changed assets versus the retained v3 artifact: API HTML, API index,
  robots, guide CSS and guide JS. Homepage, founder, Workspace, shared styling
  and source-corpus files were not changed. Selected live bytes also match.
- No new public migration. Guides reuse the existing editorial tables.
- Separately owned private ingress: version 56,
  `4af232c8-27b5-4be1-a4e2-bf9593abed32`, deployed at 23:29:21 UTC;
  rollback `9b72420c-e963-4d52-b67b-f49c4bec6534`. Its displayed application
  version remains 0.6.4 intentionally: config, bindings, gates, Container,
  credentials, migrations and Instagram code were not changed by this adapter.
- Source branch: `codex/base2026-seo-evidence-engine-20260830`, HEAD
  `5b709108d69229d92fa2a73b049392e161781969`. Phase 20 dirty changes were
  preserved. Exact source is deployed but **uncommitted/unpushed**; HEAD alone
  is not the release. The private 51-file implementation manifest hash is
  `4ad2812f83705d219fee6d6d70dfacc3d2617439d766683ff2d1f95e0ba188bb`.

Important rollback constraint: a pre-guide public Worker cannot safely read a
new `evidence_guide` in the shared editorial table. Version `a63f4c74...` is the
first guide-compatible restore point. Use a verified compatible release or a
separately reviewed recovery; do not erase guide data/receipts to run old code.

## First useful guide, outside the blog

[Internal linking: choose and verify one useful link](https://base2026.dev/topics/internal-linking)
replaces the older static page at the same canonical; it does not create a
second keyword-variant URL or a duplicate blog post.

- Revision 1; normalized payload SHA-256
  `3e3bb3282cc7777f185bdbcefd26f33617dacf822949462a901e72cc838a7e1a`.
- Independent root Sol Max review completed at `2026-08-30T23:23:01.000Z`.
- Signed publication recorded at `2026-08-30T23:34:41.154Z`; follow-up signed
  inspection returned the exact tuple. No overwrite or direct SQL write.
- Three short, exact, directly supporting public document excerpts, three
  attributed creator works and Google's link guidance. Four cited URLs are
  not four independent experiments or verified ranking results.
- Original inspect/decide/verify workflow and optional internal-link decision
  record. The form stays in the browser tab; it does not fetch entered URLs,
  send data, persist entries or record input analytics. Copy/CSV are explicit
  user actions; CSV neutralizes spreadsheet-formula input.
- One deliberate acceptance replay returned `already_published`, unchanged
  revision/hash/recorded time. **Do not repeat either this replay or the
  completed Phase 20 worksheet replay.**
- Public D1 after replay: **two editorial records and two receipts**—one blog
  article and one guide. Blog/API/RSS still contain three articles including
  the two unchanged legacy journals. Guide count is separate from source counts.

Guide HTML, `/api/guides`, detail API and `/sitemap-guides.xml` return 200.
The sitemap contains one guide. Public reads recheck evidence dependencies and
use no-store; drift returns 503/noindex for repair. Blog aliases return 404 and
blog feed/sitemap exclude guides. Trailing-slash and .html aliases redirect 308
to the existing canonical; query variants are noindex; public POST returns 405.

## Existing-source discovery repaired

At 22:13 UTC the source catalog contained 80 legacy source IDs and none of the
50 IDs in the dynamic sitemap. At 23:25 UTC, live keyset navigation exposes
all 50 cloud-added records across 30/20-record pages; the union exactly matches
the dynamic sitemap, missing 0 / extra 0. Both pages preserve the labeled 80-entry
legacy selection. The continuation is noindex/follow, not a new search page.

This is repaired navigation to already-public records, not 50 new videos
ingested today. Public `/api/stats` remains 2175 documents / 1574 sources /
50 evidence routes / 83 cards / 0 full-transcript flags. Receipt-backed metadata
is not automatic endorsement of historical extracted claims.

## Verification

- Root reran 597 Worker tests and 56 Python release/UI tests, typecheck, exact
  candidate dry-run, whitespace and artifact-policy checks.
- Actual Miniflare/D1 tests cover 12 legacy and 12 projected dependencies through
  publish/read/replay/CAS and withdrawal races. D1's depth 100 SQL-expression
  limit was reproduced and fixed by grouping predicates without removing them.
- Exact-artifact privacy gate passes with four approved public data files.
  Repository scan: forbidden 0 / secrets 0; four pre-existing Python test files
  remain flagged for manual review; no waiver was applied. Nothing was staged.
- Closeout rechecked all 51 files in the frozen implementation manifest:
  zero hash or size mismatches. `git diff --check` also passed.
- Native Chrome 1440/390: no horizontal overflow, matching canonical, readable
  hierarchy, working citations/TOC and decision enhancement. Preview banner is
  absent from production. Keyboard focus/reduced motion and script-disabled
  readable content were separately verified on the exact rendered candidate.
- Native CSV button created a 369-byte synthetic QA record with formula input
  escaped; no form-input fetch/XHR/beacon. Chrome relay's download-path command
  is unsupported, but the ordinary button operation worked.

## Research and recurring scope

Three separate Sol Max focus roles covered SEO practice, current research and
critical failure modes. Root checked the primary evidence and selected maintained
task guides plus source navigation, not a video-to-keyword-page factory.
Exa's official advanced-search/fetch MCP worked without a paid key.

The deployed registry permits five existing canonicals: internal-linking,
search-console-low-hanging-fruit, content-freshness, schema-ai-citations and
llms-txt-risk. Registration is not publication; only internal-linking is live
as a maintained guide at this release.

A post-release scan at 23:36:07 UTC made 13 read-only requests across 12 research
intents, saw the live guide revision and five registered topics. Internal-link
matches: 73 documents / 59 sources / 9 handles. Search Console matched 149 but returned
100, so that lane is explicitly partial. Service-page and technical-SEO scans
are also partial. Identical-body groups are duplicate content, not proof of
source independence. Other useful registered lanes returned 30 content-refresh,
19 schema and 15 llms.txt documents. None are automatically approved articles.

The existing six-hour editorial/X office is the scheduler; no second CMS,
paid API or additional scheduler is needed. Its author/reviewer/refill still
requires the owner's Codex host. Cloudflare serves and checks published guides
independently. Observe the first future updated run separately; this acceptance
run is not evidence of uninterrupted future output.

## Discovery and outstanding measurement

IndexNow accepted exactly the changed guide and source catalog at
`2026-08-30T23:37:51.580Z` with HTTP 200, using the existing live-verified key.
No unchanged article batch was resubmitted. Acceptance is not indexing.
The guide sitemap was submitted exactly once through the existing Base2026 GSC
property. The current live table shows Success, 1 discovered page and 0 videos.
Existing blog/dynamic/static sitemaps show Success with 1/50/1636 discovered URLs
at 23:31 UTC.

No ranking, traffic, AI-citation or conversion increase is claimed. Preserve
Medium/X receipts and reconcile existing queued posts before another send.
LinkedIn remains outside unattended publishing; no login or security workaround.

## Source handoff

Changed implementation surfaces are the public Worker's editorial/dependency,
guide-rendering/routing and source-catalog modules; their tests; the candidate
scanner and editorial-packet CLI; the exact artifact configuration; guide CSS/JS;
the release builder/tests; and public API documentation. Project documentation
includes the new evidence-to-SEO manual, this receipt, editorial/deployment
instructions, README/roadmap and the required project-memory state files.
The private ingress adapter remains separately owned and documented.

Suggested commit message, **not executed**:
`feat: add evidence-backed SEO guides and source discovery`.
Preserve the existing Phase 20 changes and resolve the four audit review flags
before a separately authorized, exact-file Git publication pass.

Canonical instructions:
[evidence-to-SEO manual](../BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md),
[shared editorial publisher](../BASE2026_EDITORIAL_PUBLISHING.md),
[Cloudflare intake boundary](../BASE2026_CLOUDFLARE_PIPELINE_CANONICAL_OPERATING_MANUAL.md).
