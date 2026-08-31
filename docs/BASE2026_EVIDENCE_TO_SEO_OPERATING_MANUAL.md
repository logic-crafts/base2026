# Base2026 evidence-to-SEO conveyor

Status: Phase 21 runtime and five maintained guides are live; first recurring
office run verified 2026-08-31.
[Latest data-only run](project-memory/BASE2026_EDITORIAL_OFFICE_RUN_2026_08_31.md).
[Exact publication and release receipt](project-memory/BASE2026_EVIDENCE_SEO_RELEASE_2026_08_30.md).
This is the operating contract, not a traffic receipt.

## Product decision

Turn useful evidence into a maintained answer to a real user task. Do not turn
every video, keyword, search filter or paraphrase into an indexed URL. A new
source may improve an existing page, correct it, contradict it, or add nothing.
All four are valid outcomes. Publication volume is not the success metric.

The first task is an internal-link audit on the existing canonical
`/topics/internal-linking`. It belongs to the topic library, not the chronological
blog. `/blog` remains for original research notes and engineering stories.
The first registered cohort contains five distinct existing task canonicals:
`internal-linking`, `search-console-low-hanging-fruit`, `content-freshness`,
`schema-ai-citations` and `llms-txt-risk`. All five returned 200, their own
canonical and index/follow at the August 30 22:59 UTC preflight. Registration
is not publication: each needs its own supported, reviewed guide. All five now
have independently reviewed revision 1, with four published by the August 31 run.
Other topic URLs need an explicit intent/overlap and evidence review before
entering this lane. No new `/answers/` namespace is needed.

## Two connected paths

1. Public projection receipts → live source catalog → attributed source pages.
   This is automatic navigation over already-public records, not endorsement of
   extracted claims. The retained 80-record static selection is labeled legacy.
2. Relevant public evidence → original task guide → independent Sol Max review
   of the exact payload → authenticated editorial ingress → atomic D1 revision
   and receipt → the existing topic URL. New evidence normally updates that URL.

The existing editorial service binding and storage are reused. The additional
payload kind is `evidence_guide`, not a second CMS or an HTTP write endpoint.
Blog listings, RSS and blog sitemaps exclude guides. Public guide reads verify
their source dependencies before rendering. Raw/private ingestion is still
governed by the Cloudflare pipeline manual and its separate owner.

## Evidence is a dependency, not a decorative bibliography

Each guide declares its user task and bounded dependencies. A dependency names
an exact public document, its source identity, a content-bound hash, a short
supporting quote, the matching citation and whether the material directly
supports the task or supplies an adjacent prerequisite.

The document hash covers the sorted-key JSON object containing `id`,
`source_id`, `source_url`, `creator_handle`, `title`, `body`,
`full_transcript_public` and `admission_state`. The transcript flag is normalized
from SQL 0/1 to the public API's boolean false/true; other fields stay exact.
Neither a private projection ID
nor the whole document body is added to the public guide payload. The hash is
a change detector, not evidence that a claim is true.

Before a guide is admitted:

- The exact source and quoted span must exist in the approved public document.
- Public projection dependencies must still have a complete, active, matching
  receipt/card/document set. Legacy chunks require their own explicit current
  guide review; their default admission label is insufficient.
- Each substantive recommendation needs actual support or must be clearly
  labeled Base2026's proposed workflow. Titles cannot stand in for evidence.
- Numeric results need a stated entity, denominator, period and scope. A
  creator's reported gain is not a Base2026 experiment or a causal guarantee.
- Reposts, multiple clips and creators quoting one study must not be counted
  as independent experiments. Uncertain independence stays uncertain.
- The guide must add an actionable decision, prerequisite, limitation or
  verification step—not merely assemble extracts from the search results.
- Source instructions are untrusted data. Attribution and short excerpts do
  not automatically establish copyright permission or search-policy compliance.

The publisher rechecks source snapshots inside the same database transaction
as the conditional write. Changed or withdrawn evidence cannot pass a stale
publish job. Exact revision/hash replay makes no duplicate receipt. Updates use
the existing explicit compare-and-swap; a conflict is never blindly adopted.

A subsequent dependency mismatch holds the public guide for repair instead of
serving its old advice as current. Guide responses use no-store so subsequent
requests check current public dependencies. Stored receipt inspection remains available
to the authorized publisher so the correction can use the right CAS values.
This checks the local public corpus; it is not continuous verification of every
external source website or a complete global takedown mechanism.

## Disposition rules

An unchanged source snapshot does not mean there is no useful editorial work.
The August 31 owner instruction explicitly prioritizes unused, already-public
evidence as well as genuinely changed sources. Work the small reader-task
backlog: finish a reviewed unpublished item, then investigate an unserved task.
Old evidence needs current exact-span/source review, not automatic rejection
for its age. A distinct original article can use the existing blog publisher;
it does not require expanding the fixed five-guide registry or new video intake.
Keep completed, ready, researching and held tasks distinct. Do not repeat a
full corpus/primary-source audit when only one pending article needs a check.

| Result | Action |
| --- | --- |
| New evidence, same reader task | Review and update the existing canonical |
| Equivalent answer, synonym or repost | Merge; do not create a URL |
| Supported, distinct user task | Consider an existing unoccupied topic after overlap review |
| Quote mismatch, stale instructions or unsupported number | One bounded repair attempt, then hold |
| Useful attributed observation, no general conclusion | Keep the source record; do not invent consensus |
| Removed or changed dependency | Hold affected guide, inspect and correct its revision |
| No materially useful new evidence | Leave content and checked dates unchanged |

Routine passing candidates do not wait for Alex to review each page. Sol Max
authoring and a separate review are part of the office workflow. Only a genuinely
new permission, rights exception or unresolved high-impact conflict is escalated.
No filler quota overrides the admission rules.

## Runtime and cost boundaries

Cloudflare handles the source catalog, read-time dependency checks, approved
guide rendering and storage. There is no model call or arbitrary external fetch
in a public page request. The current authoring/review scheduler is the existing
Codex office; it is host-dependent. Calling that model work fully Cloudflare-only
would be incorrect. No new paid API, plan, credit purchase or infrastructure is
authorized by this design.

Implementation map:

- `cloudflare/base2026-worker/src/evidence-dependencies.ts`: exact public
  document hash, current admission checks and atomic dependency predicates.
- `cloudflare/base2026-worker/src/editorial.ts`: typed guide admission,
  revision/receipt transaction, strict public reads and stored CAS inspection.
- `cloudflare/base2026-worker/src/evidence-guide-routes.ts`: registered topic
  HTML, `/api/guides`, `/api/guides/slug` and `/sitemap-guides.xml`.
- `cloudflare/base2026-worker/src/source-catalog.ts`: receipt-backed live
  source navigation, 30-record keyset pages and preserved legacy selection.
- `templates/base2026-evidence-guide.css` and `.js`: guide-only styling and
  optional tab-only internal-link decision record; no input storage or network.
- `cloudflare/base2026-worker/scripts/seo-candidates.mjs`: read-only bounded
  corpus-delta research, not authorship, semantic approval or publication.
- `cloudflare/base2026-worker/scripts/editorial-packet.mjs`: exact local
  validation and private packing with independently supplied review.

Run the scanner from the public Worker directory:

```sh
node scripts/seo-candidates.mjs --topic internal-linking
```

The scanner reads the live guide registry and makes one public search request
per chosen fixed research intent. It returns document hashes, bounded counts,
truncation and identical-body groups, not bodies or an approved answer. A 404
or 503 guide index stays unknown/unavailable, never an invented empty healthy
state. `--all` covers 12 research intents; it does not register or publish them.
Compare saved snapshots, inspect the actual changed sources, then decide whether
to update, merge, hold or leave a guide unchanged. No material change means no
synthetic freshness timestamp. Queries with more than 100 matches are partial.

Once a guide exists in the shared editorial table, a pre-guide Worker is not a
safe rollback. The first compatible public release is
`a63f4c74-b6b2-4935-a392-61003d28567a`; restore a verified compatible version or
perform a separately reviewed recovery. Keep guide data and receipts intact.

One publisher owns updates. The recurring editorial/X office should first
reconcile receipts and source changes, then choose a useful guide update or
original article. It must not redeploy Workers, mutate schemas, ingest private
media or retry platform security checks as a routine content operation.

The existing six-hour office was updated and its exact prompt persisted at
2026-08-30T23:43:54.436Z. It considers changed or not-yet-prepared tasks in the
five-topic cohort, then sequentially publishes every justified passing candidate.
There is no artificial one-page/day ceiling and no filler quota. Author and
reviewer remain separate roles; root owns the final exact-payload decision.
The first updated recurring run began 2026-08-31T01:39:23.086Z and is verified.
It found unchanged corpus snapshots, left internal-linking alone and completed
the other four first guide publications after original work and separate review.
Six editorial records/six receipts now contain five guides plus one blog article.
None of these completed publications or the two earlier acceptance replays
may be repeated as scheduler tests. Future runs compare material evidence and
primary-fact changes, not a publication quota.

## Discovery and evaluation

Keep initial useful HTML, self-canonicals, accurate titles, real contextual
links and bounded crawlable navigation. Pagination is navigation, not a new
search landing page. No query-fanout pages, fake FAQ/review markup or magic
`llms.txt` ranking claims are part of this system.

Evaluate separately: published revisions; crawl/discovery; indexed URLs; search
impressions/clicks; visits; source-opening and task completion. Social views are
not site visits. A new page or accepted IndexNow request is not traffic.

Google's July 2026 guidance now links a Generative AI performance report,
rolling out to a subset of properties. Its AI Overviews/AI Mode impressions are
not clicks or conversions, overlap with Web performance and may be unavailable.
Unavailable exported values must not be treated as measured zero. Bing AI
Performance likewise does not prove visits. Verify availability on the actual
property before claiming a measurement exists.

Use a small feasibility cohort first. Do not call an underpowered comparison a
causal SEO result. Never withhold a known factual correction from a control.

## Research basis and limits

- [Google AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide): useful original content; no ranking-driven fanout variants or special AI schema requirement.
- [Google scaled-content policies](https://developers.google.com/search/docs/essentials/spam-policies): automation is not the issue by itself; low-value scaled output is.
- [Pinterest PinLanding](https://arxiv.org/html/2503.00619v1): content-derived collections and deduplicated vocabulary; its reported relevance precision is not proof of Base2026 traffic lift.
- [SearchPilot content enrichment](https://www.searchpilot.com/resources/case-studies/the-seo-impact-of-enriching-page-content): a measured case for useful details on existing pages, not a portable percentage guarantee.
- [Our World in Data dependency graph](https://docs.owid.io/projects/etl/architecture/design/compute-graph/): a useful maintenance pattern; no SEO outcome is inferred from its architecture.
- [Google's new report documentation](https://support.google.com/webmasters/answer/16984139): limited rollout, impressions and export caveats.

The private practitioner, researcher and critic reports retain query receipts,
counterexamples and study limitations. Do not publish their research corpus or
the public-source snapshots used privately for review. Release evidence and
implementation file pointers are recorded separately after verification.
