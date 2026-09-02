# Base2026 Evidence Map Canary — 2026-09-01

Status: PR-ready in isolated worktree; not pushed, merged, deployed or
submitted for indexation.

## Scope and boundary

This is a bounded static indexable-corpus canary for the existing public
Base2026 search/evidence surface. It adds one hub and three evidence maps. The
builder consumes public D1 search API exports only; it does not read the
private knowledge base, private Cloudflare pipeline, raw media, raw captions,
credentials or local database files.

The generated pages contain a direct answer, a scope note, three practical
actions, six short attributed public excerpts and links back to the public
workspace/methodology/hub. Source excerpts are capped at 300 characters and a
single card is selected per source ID. The original TikTok post remains the
canonical source. No full transcript is emitted.

## Live preflight

Observed on 2026-09-01 from the isolated worktree:

- `GET https://base2026.dev/api/health`: HTTP 200, `service=base2026`,
  `search=d1-fts5`, `index=base2026_public_tiktok`.
- `POST https://base2026.dev/api/search/multi-search` with an empty public
  query and facets estimated 2,198 documents. The live topic facets used for
  this canary were 232, 116 and 66 estimated matches.
- `robots.txt`: HTTP 200, allows `/` and advertises the static, dynamic, blog
  and guide sitemaps.
- `sitemap.xml`: HTTP 200, five `base2026-*.xml` children plus the existing
  hub shard. `sitemap-dynamic.xml`: HTTP 200 with 50 current projected-source
  URLs, including URLs last modified on 2026-09-01.
- Representative current routes `/workspace/`, `/topics/`, `/creators/`,
  `/methodology`, `/api` and one projected source route returned HTTP 200 and
  valid canonical/robots/H1/JSON-LD metadata. `/workspace/` is intentionally
  `noindex,follow`; the other representative content routes are indexable.
- Current Git/worktree preflight: the canonical checkout remains dirty at
  `/Users/alexyarosh/Projects/base2026-migration/DW/base2026`; this task used
  only `/Users/alexyarosh/.codex/worktrees/a2d7/base2026`.

The live values above are a dated readback, not a promise that the public D1
or sitemap will remain unchanged. Recheck them before integration.

## Candidate selection and exact canary receipt

The three public search exports were fetched with the public D1 index and the
exact topic IDs below. The first two were bounded to 100 rows; the third
returned all 66 rows. The exports were ephemeral and are not committed.

| map slug | public topic facet | estimated matches | rows received | rows rejected by public-safety/quality checks | selected records | unique sources | creators | score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ai-visibility-answer-readiness` | `ai-visibility-and-answer-readiness` | 232 | 100 | 1 | 6 | 6 | 6 | 100/100 |
| `seo-research-tooling-workflow` | `seo-research-and-tooling-workflow` | 116 | 100 | 2 | 6 | 6 | 6 | 100/100 |
| `local-seo-google-business-profile-operations` | `google-business-profile-local-seo-operations` | 66 | 66 | 0 | 6 | 6 | 6 | 100/100 |

Aggregate export receipt: 266 deduplicated input rows; the three estimates
sum to 414 but are overlapping topic-query estimates and must not be treated
as 414 unique records. The generator selected 18 records for output, all with
`full_transcript_public=false` in the live response. `eligible_count=3` and
`rejected_count=0` at the page-candidate level.

Per-page score weights are unique evidence 25, source diversity 20,
substantive answer/utility 25, canonical uniqueness 15 and internal-link
support 15. Hard requirements are at least four unique excerpts, four source
IDs, three creator handles, a 45-word answer, 260 visible words, a 0.75
unique-evidence ratio, three internal links and a unique extensionless
canonical route. The live canary exceeded each requirement: six excerpts,
six source IDs, six creators, 1.0 uniqueness ratio, 5 internal links and
615–651 measured visible words in the deterministic content model.

## Implementation

The exact implementation files are:

- `data/base2026_evidence_map_canary.json` — three public topic/intent
  definitions and neutral answer/action copy.
- `scripts/generate-evidence-map-canary.py` — public-export loader, fail-closed
  row safety checks, diversity selector, eligibility score, hub/map renderer,
  sitemap shard writer and optional idempotent sitemap-index linker.
- `scripts/check-evidence-map-canary.py` — local page, metadata, JSON-LD,
  internal-link, stylesheet and sitemap membership gate.
- `templates/base2026-evidence-map.css` — current Base2026 visual tokens and
  responsive evidence-map layout.
- `tests/test_generate_evidence_map_canary.py` — eligibility, privacy,
  rendering, sitemap and checker coverage.
- `scripts/audit-publication-boundary.py` — admits the new public-safe config,
  generator, checker and test paths to the existing publication audit.

The generated artifact is intentionally not a Git source artifact. A
successful run writes only managed files under the selected release-root
overlay:

- `evidence-maps.html`
- `evidence-maps/<map-slug>.html` for each eligible map
- `static/evidence-map-canary.css`
- `sitemaps/evidence-maps-canary.xml`
- `evidence-map-canary-ledger.json`

## Verification receipt

- Generator run against the live exports: 3 eligible / 0 rejected.
- Canary checker: `pages_checked=4`, `sitemap_urls=4`, one indexable canonical,
  one H1 and one valid JSON-LD block per page; no `full_transcript_public`,
  local-path or unmanaged internal-canary-link marker remained.
- Relevant Python test set: 27 passed.
- `python3 -m py_compile scripts/generate-evidence-map-canary.py
  scripts/check-evidence-map-canary.py scripts/audit-publication-boundary.py`:
  passed.
- `git diff --check`: passed.
- `python3 scripts/audit-publication-boundary.py --json`: passed with 6 changed
  public-safe candidates, 0 forbidden paths, 0 needs-review paths and 0
  secret findings before this receipt was added.
- Isolated canary-only `build-base2026-cloudflare-release.py` smoke test:
  passed with 13 output files and zero redirecting `.html` canonical/sitemap,
  private-token, local-path or personal-origin markers. The mixed legacy
  `web/static` copy is not a release input for this task; the coordinator must
  run the final builder against the canonical generated `source-web` artifact.

## Safe integration instructions

Do not deploy from this receipt. The command center should re-fetch current
public rows and review the ledger before integration.

1. Query the live public API with the three topic IDs in
   `data/base2026_evidence_map_canary.json`, saving each JSON response to an
   ephemeral file. Do not add credentials or private exports. The API request
   shape is:

   ```bash
   curl -fsS -H 'content-type: application/json' \
     -d '{"queries":[{"indexUid":"base2026_public_tiktok","q":"","limit":100,"facetFilters":["topics:ai-visibility-and-answer-readiness"],"attributesToRetrieve":["id","source_id","creator_handle","creator_url","body","title","source_url","published_date","topic_labels","topics","video_id","full_transcript_public","admission_state"]}]}' \
     https://base2026.dev/api/search/multi-search
   ```

   Repeat with the other two topic IDs; use `limit=100` for the 116-match
   cluster and `limit=100` (or the returned 66 rows) for the 66-match cluster.

2. After the canonical release pipeline has materialized its public
   `source-web` directory and its root `sitemap.xml`, run:

   ```bash
   python3 scripts/generate-evidence-map-canary.py \
     --search-export /tmp/base2026-ai-visibility.json \
     --search-export /tmp/base2026-seo-workflow.json \
     --search-export /tmp/base2026-gbp-operations.json \
     --config data/base2026_evidence_map_canary.json \
     --output-dir output/cloudflare-migration/source-web \
     --base-url https://base2026.dev \
     --as-of 2026-09-01 \
     --sitemap-index output/cloudflare-migration/source-web/sitemap.xml
   python3 scripts/check-evidence-map-canary.py \
     --output-dir output/cloudflare-migration/source-web \
     --base-url https://base2026.dev
   ```

   Use a fresh `--as-of` date for a later run. The sitemap-index option is
   idempotent and fails closed if the target is missing or not an index.

3. Run the existing public publication audit and non-overwriting Cloudflare
   release builder against the canonical candidate. Verify the final artifact
   again; the canary checker must remain green and the final sitemap index must
   contain `https://base2026.dev/sitemaps/evidence-maps-canary.xml`.

4. Stop for command-center/coordinator ACK. Only an explicitly approved
   release may proceed through the canonical deployment runbook. Do not send
   GSC, Bing or IndexNow submissions from this branch and do not infer
   indexation from sitemap membership.

Rollback before any deployment is simply to omit the managed canary overlay
   from the next candidate and regenerate the release artifact. No Worker,
D1 row, production sitemap or live page was changed by this task.

## Commit and ownership

- Implementation branch: `codex/base2026-evidence-map-canary-20260901`.
- Base commit: `c9ff51b4d`.
- Implementation commit: `efab336d55b4b22c018b383fd1e436fa5e276420`
  (`feat: add gated evidence map canary`).
- This receipt-file pin is a follow-up documentation commit; the final
  response identifies both hashes and the branch remains unpushed.
- No AgencyOS write was performed. This document is the handoff receipt for
  command-center review; an AgencyOS update is appropriate only if the owner
  chooses to record this receipt in its operational system.
