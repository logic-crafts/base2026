# Data Sources

## 2026-09-04 Evidence Search intent and live release evidence

A bounded US-English DataForSEO packet checked candidate free-tool language.
`search inside video` returned approximate volume 90 and a mixed but relevant
in-video-search SERP. `free research tool` and `tiktok research tool` were
rejected for current routes because their live intent is keyword research and
TikTok's research/product ecosystem. `tiktok transcript generator` returned
approximate volume 2,900, but its exact SERP expects a working paste-URL
transcriber; it is not evidence that an article or renamed tool would rank.

Worker `327a21a5-ca54-457c-8099-aa2447a7fe1a` now serves the aligned Evidence
Search copy. The route is HTTP 200 and self-canonical; health, home, Source
Diversity and MCP remain 200. Counts are unchanged at 2,259 documents, 1,638
sources, 114 evidence routes, 167 cards and zero public full transcripts.

Last updated: 2026-09-04

## 2026-09-04 Source Diversity Check production evidence

Worker `da308428-5609-43ab-8b31-88deb124dc7b` serves the reviewed free Source
Diversity Check at `https://base2026.dev/tools/source-diversity-check/`. The
route is HTTP 200, self-canonical, indexable and present exactly once in the hub
sitemap. A live browser run with two existing IDs and one nonexistent ID
resolved two public records and retained the third as explicit unresolved
metadata on desktop and 390 px mobile. The same run had no console/page errors
or horizontal overflow. The public MCP `get_source` readback remained inside
the documented public read-only boundary.

The release artifact tree is
`0f225c3cfb86b4b89dc0325c70e81d289f79457fa2123f9407d7a7ae819e21c8`.
Live public counts remained 2,259 documents, 1,638 distinct sources, 114 public
evidence routes, 167 projected cards and zero public full transcripts. One
IndexNow request for the exact new canonical returned HTTP 200; this proves
notification only. PR47 merged the separate public Evidence Pack at
`0341b8911a3df42b51285816e3d3e07e615ed96e`.

Last updated: 2026-09-04

## 2026-09-01 Evidence Search production release

Worker `0337f7d6-ebe4-4bcc-8b4a-e23317a99a8e` serves the reviewed Evidence
Search release at `https://base2026.dev/tools/evidence-search/`. The route is
HTTP 200, self-canonical, indexable and present in the hub sitemap. A live D1
query for `internal linking` returned 24 hits with an estimated total of 27;
the browser rendered 10 deduplicated attributed results. The no-JS fallback,
390 px mobile view, privacy headers, member routes and Google-auth boundaries
were rechecked after deployment. One exact IndexNow URL was accepted with HTTP
200; this is submission evidence, not proof of indexing or traffic.

The exact deployment, artifact hashes, rollback version and live QA matrix are
recorded in
`HANDOFF_2026-09-01_BASE2026_EVIDENCE_SEARCH_PRODUCTION_RELEASE.md`.

Last updated: 2026-09-01

## 2026-09-01 live member and guide-alias evidence

Worker `5a326a64-c755-4036-93af-1a1809e0aeb6` is the verified rollback for the
current release. Its live hashes for
workspace, My Research, privacy, member JS and member CSS match the reviewed v2
asset bundle; `/guides` and `/guides/` now return bodyless 308 responses to
`/topics/`, including query preservation. The private release receipt is
`auth/20260831/member-guide-alias-hotfix-20260901T1601Z.json`.

Fresh script-settings readback has invocation logging and log/trace persistence
off, traces disabled, Worker Logpush off and no tail consumer. Query redaction
is false, and account/zone/instant Logpush inventory is still unknown because
the current OAuth grant lacks Logpush read; do not infer an empty inventory.

Google's current basic-scope exception allows External/Testing access when the
app requests only `openid email profile`; the unsaved second test-user row was
closed without changing the one-user allowlist. Identity B is recognized by
Google but waits at the owner's password screen. This is not a completed
identity-B or cross-user-isolation receipt.

Last updated: 2026-09-01

## 2026-08-31 isolated member-auth evidence

Live Google Console confirms the intended owner completed physical sign-in.
The selected existing project denies OAuth configuration reads; an exact
Base2026 project search returned no resources. A dedicated free project was
subsequently created once within the coordinator-confirmed scope and selected,
with a completed Google creation notification. No old project was deleted;
no billing or IAM change was made. After the owner's action-time confirmation,
Google confirmed OAuth app and one web-client creation. Canonical origin and
callback were read back; homepage/privacy/domain and basic identity scopes
were saved. Audience is External/Testing with one owner test user and no
sensitive or restricted scopes. Credentials are stored privately with mode600.
These receipts prove Google configuration, not product Google-login success.

The local member asset candidate has five changed/added served paths and
independent per-file hash readback. Native workerd/D1 tests use synthetic
Google responses; browser fixture checks are UI evidence only. Neither proves
live Google OAuth or production private D1 operation. Follow the
[auth handoff](HANDOFF_2026-08-31_GOOGLE_AUTH.md) for the exact candidate and
passed final security delta review and remaining integration/release gates. Private account and browser
details remain outside public Git.

## 2026-08-31 latest public and natural-pipeline checkpoint

Public /api/stats at10:15 UTC:2175 documents/1573 distinct sources/49 evidence
routes/83 projected cards/zero full transcripts. Blog5 and the five unchanged
revision1 guides are separate counts. The09:16 withdrawal totals below remain
dated history; the later natural projection is a separate event.

The second archive article, comparison-page-evidence-check, revision1, was
recorded10:06:01.197 UTC; normalized payload SHA
`c074c9e44ec6bb69e03269e59a6d656064e60e59814e0c9450573e3431bda4bb`.
Independent critic/root API/hash and1440/390 QA passed without overflow/errors;
29 same-origin links passed. Its single URL received IndexNow HTTP200 at
10:06:43.593 UTC. The first article's31-link/09:20:30.522 acceptance below is
unchanged. Acceptance is not indexing or traffic. Comparison is complete;
two distinct archive candidates remain, not approved publications.

Private57/58 and migration0016 are deployed. The10:16 cohort is27 admitted/
6 media/5 transcripts/one packet/import/verified projection. Semantic outcomes
are1 packet/2 review classifications/2 contract holds. Eighteen unique
source-state corrections were recorded (16 historical/2 fresh); terminal false-wait backlog is
zero in that receipt. One external capture failure remains on bounded retry;
not all27 are processed. One fresh R2 byte/hash readback passed.

At10:17, root verified the [natural public source](https://base2026.dev/sources/tiktok-video-7679869746929601806):
two cards by read-only SELECT, zero writes; HTTP200/self-canonical/index-follow,
dynamic sitemap/catalog page2, two normal search queries and1440/390 QA.
This proves one natural end-to-end path, not creator truth, reuse rights or
traffic. Private identifiers/raw evidence remain protected. Direct GPT Work
incident delivery is unverified; no dispatch is claimed.

## 2026-08-31 first archive article and semantic correction (09:15–09:20 receipt)

One existing-corpus article published at09:15:33.466UTC recorded time:
`evidence-first-content-backlog`, revision1, normalized payload SHA
`4decbafa3759a4c75f09c00cc57e9eb2e40bc67c2d2f449eea0820cc4860afef`.
Five cited sources, eight sections, separate exact-source author/critic review.
Signed inspect and live API match; blog4/guides5. Existing five guide hashes
and revisions are unchanged. The article uses existing reviewed public records;
no new media or transcript acquisition is claimed.

Exactly two historical claim/excerpt pairs failed independent semantic review
and were withdrawn through receipt-fenced rollback, preserving private evidence
and history. Neither affected current guide dependencies. Live stats09:20UTC:
2173documents/1572sources/48evidenceroutes/81projectedcards/zero full transcripts.
The decrease is deliberate quality correction, not pipeline loss.

IndexNow accepted only the new article URL once at09:20:30.522UTC (HTTP200).
Thirty-one same-origin article links passed; canonical, index/follow, blog/feed/
actual child-sitemap inclusion and existing hosted key were verified. No old
batch repeated. Acceptance does not prove indexing or traffic.
[Closure proof](BASE2026_OFFICE_CLOSURE_2026_08_31.md).

## 2026-08-31 second recurring check (historical receipt)

At 07:50 UTC all 12 bounded corpus snapshots still matched baseline/prior run.
Five guide payloads and the worksheet matched their exact approved packets and
signed receipts. Six selected primary pages plus the GSC filtering page were
read semantically; no material correction identified. This is bounded review,
not continuous external monitoring or renewed source-rights clearance.
No editorial/public-corpus change. X03 is sent; one GSC standalone is scheduled
for September 1 07:30 UTC. At 08:00 UTC: four sent/five scheduled/one queued
thread/no unresolved write. GSC remains 45 impressions/0 clicks through Aug28;
older sitemap discovery counts are not indexing. [Check receipt](BASE2026_EDITORIAL_OFFICE_CHECK_2026_08_31_0739.md).

## 2026-08-31 first recurring editorial run (publication receipt)

The 01:43:23 UTC scanner repeated 12 fixed intents in 13 read-only calls.
All source snapshot hashes matched the prior baseline. Internal-linking stayed
no_change; four existing unprepared topic tasks received original reviewed
guides, not four newly discovered sources. The GSC corpus query remains partial
at 149 matches / 100 returned. Seven unregistered directions stay research-only.

Two authors, an independent critic and root read selected full public bodies
and current primary documents. All six direct dependencies across the four
guides were individually checked; quotes, identities and eight-field hashes
match. Review corrected a schema-measurement distinction and an unsupported
GSC attribution before publication. No invented experiment, generalized creator
outcome, independent-study count or reuse-license claim was admitted.

Remote D1 SELECTs confirm six editorial records/six receipts/five guides/zero
orphan receipts, with zero rows written by those checks. Four single writes
were recorded 02:07:18.124–02:17:13.029 UTC; exact signed receipts and full
public API payloads match the approved candidates. Existing guide/worksheet
dates and receipts are unchanged. Blog/API/RSS remain three articles, separate
from the five-entry guide API/sitemap. Corpus remains 2175/1574/50/83/zero
full-transcript flags; no intake claim follows from editorial publications.

IndexNow accepted only four changed guide URLs at 02:21:36.532 UTC, HTTP 200.
GSC's read-only snapshot retains Success for all four sitemaps and discovered
counts 1/1/50/1636; its guide count predates the four new entries. Available Web
data still covers August 27–28: 45 impressions/0 clicks/position 52.8. No traffic
lift or AI-citation outcome is proved; a report absent from inspected navigation
is not a measured zero or proof of the property's inclusion setting.

X-02 was confirmed sent with a native URL. Official history now has three sent
and five scheduled publications, including one queued thread; two additions
are scheduled for August 31 19:30/22:30 UTC, not published. The X-06 field
distinction is now explicit: dueAt 21:18:43.810 versus actual sentAt 21:18:46.272
on August 30. The 24/72-hour measurement windows were not yet due.

The first updated six-hour office run is observed. Same public Worker and all
51 pinned implementation files remain unchanged. No code/schema/design/Git/
private intake or LinkedIn mutation. [Exact run and limits](BASE2026_EDITORIAL_OFFICE_RUN_2026_08_31.md).

## 2026-08-30 Phase 21 evidence-to-SEO (historical release receipt)

The independent SEO practitioner, researcher and critic used live Base2026
queries and current primary sources. Exa advanced search/fetch worked via its
official MCP without a paid key. Private reports retain the detailed query
evidence; they are not a public research dump or a rights license.

At 23:36:07 UTC the shipped scanner made 13 read-only requests for 12 research
intents. It observed five registered topics and the live internal-linking
revision. Selected cohort counts: internal linking 73 documents / 59 sources /
9 handles; Search Console 149 matches but only 100 returned (partial);
content refresh 30; schema markup 19; llms.txt 15. Queries overlap; do not add
these into a distinct-corpus or independent-source total. Identical-body groups
were found in reporting/Search Console results, not proved independent works.

The first guide uses three individually rechecked public document pins and
Google's primary link guidance. Four URLs are not four controlled experiments.
Root reviewed the exact final payload; signed publication recorded
`2026-08-30T23:34:41.154Z`, SHA
`3e3bb3282cc7777f185bdbcefd26f33617dacf822949462a901e72cc838a7e1a`.
One acceptance replay made no duplicate. Editorial D1 now has two records/two
receipts: one guide plus the prior blog article; blog/RSS still list three.

Source navigation now reaches all 50 current dynamic-sitemap IDs over 30/20
record pages, preserving 80 labeled legacy entries. This closes the earlier
catalog graph gap without new intake. Public corpus remains 2,175 documents,
1,574 sources, 50 routes, 83 cards and zero full-transcript flags.

Public Worker `a63f4c74-b6b2-4935-a392-61003d28567a`; tree
`fa3626039508a4ab4a483044c8336b93a8f63eebb3798bcc46c3e8b15620aa39`.
No new public migration or source-corpus rewrite. Private owner deployed only
the compatible editorial adapter as `4af232c8-27b5-4be1-a4e2-bf9593abed32`,
preserving config/Container/intake/Instagram state. Displayed label stays 0.6.4.

IndexNow accepted the changed guide and catalog at 23:37:51 UTC. GSC guide
sitemap is Success / 1 discovered page / 0 videos after exactly one submission.
Discovery is not indexing or traffic. The existing six-hour office update was
persisted at 23:43:54.436 UTC; its first future run is unobserved. Source and
deployment are uncommitted/unpushed on the isolated SEO-engine branch.

[Live release and limitations](BASE2026_EVIDENCE_SEO_RELEASE_2026_08_30.md);
[canonical guide operating manual](../BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md).

## 2026-08-30 Phase 20 editorial runtime and source office (historical receipt)

Public Worker `2b1a1c19-a9ab-4c43-b4b6-973678d9ee07` serves artifact tree
`1d0220c8392aa36e712b7a2f0ffb2a718fa5b807d993157e6f3cbff58629ec92`;
rollback is `d242f1aa-60f5-4ff5-97af-883318173027`. Branch
`codex/base2026-growth-office-20260830` remains at HEAD
`5b709108d69229d92fa2a73b049392e161781969`: the release delta is deployed,
uncommitted and unpushed. HEAD alone does not reproduce this release.

[The blog](https://base2026.dev/blog) now contains two retained journal entries
and [the first new article](https://base2026.dev/blog/ai-visibility-measurement-worksheet/).
Revision 1 published at `2026-08-30T21:08:58.525Z`, with payload SHA-256
`ba59b023b672d0c82010ce75d9f716b605e1dcfd199e98a22f3e4655d71072c1`.
One exact replay returned `already_published`; the store stayed at one article
and one publication receipt. That replay proof is complete; do not repeat it.
Nine cited public URLs are not nine independent studies. Source-corpus totals
remain 2,175 documents, 1,574 videos, 50 evidence routes, 83 cards and zero
public full transcripts; editorial storage is separate.

Source discovery produced 36 creator candidates, including 16 corroborated
Instagram identities and eight exact Instagram URLs from four creators.
Admissions and proved Instagram captures are both zero; access, rights and
cross-platform dedupe remain held. Three next-cycle briefs from six public
evidence-brief queries are research inputs, not written/reviewed/published
articles. The strongest next action-card brief used 36 internal-link matches,
five selected records and three handles, without claiming independence.

The new four-part X thread was sent with image/article link at
`2026-08-30T21:18:43.810Z`; all four native posts were verified. Earlier
Medium/X releases and four previously scheduled X posts remain distinct.
IndexNow accepted the two new URLs with HTTP 200. After one GSC submission,
the initial Couldn't fetch state is historical: the 21:50 UTC native readback
shows the blog sitemap Success, type Sitemap index, last read August 30, one
discovered page and zero videos. Static and dynamic sitemaps also show Success
with 1,636 and 50 discovered pages. The earlier Google live test succeeded at
21:20:06 UTC. No resubmission or configuration change was made; processing and
discovery do not prove article indexation or traffic.

The existing six-hour heartbeat is updated and persisted ACTIVE as
“Base2026 — Editorial and X growth office”, with the owner's explicit Sol Max
override for all helpers. Its first future updated run is not observed.
Authoring/review/refill require the owner's Codex host and protected
credentials; Cloudflare serving and queued Buffer posts run in the cloud.

The separate v0.6.4 owner reports passing health/doctor and R2 checks and daily
production-packet remainder 9 to 7 to 6 to 0. These bounded checks do not prove
whole-pipeline health. Older private and search snapshots below retain their
original dates. Exact production/QA proof:
[release receipt](BASE2026_EDITORIAL_RUNTIME_RELEASE_2026_08_30.md);
[editorial contract](../BASE2026_EDITORIAL_PUBLISHING.md).

## 2026-08-30 post-release search measurement

Authenticated Google Web performance (three-month range) reports 45 impressions,
zero clicks, 33 page rows and average position 52.8; its available chart covers
August 27–28. Google sitemaps report Success with 1,636 static and 50 dynamic
discovered pages. Page indexing and Bing Search Performance still process.
Other Bing reports, Google Links and individual URL inspection were not rerun.
Public `/api/stats` independently still reports 2,175 documents, 1,574 sources,
50 evidence routes, 83 cards and zero full transcripts. Exact bounded receipt:
`BASE2026_GSC_BING_READBACK_2026_08_30.md`. Older source snapshots below remain
historical; none of these measurements authorize publication or data import.

## 2026-08-28 positioning and live release evidence

- Live public D1 remote query: 2,150 `search_documents`, 1,563 distinct
  `video_id`, 39 applied public projections, zero public full transcripts.
- DataForSEO US/en packet: Keyword Overview, seven exact desktop SERPs, SERP
  competitors and Keyword Ideas; total cost `$0.077`; exact task IDs are in
  `DATAFORSEO_POSITIONING_RECEIPT_2026_08_28.md`.
- Official/public competitor surfaces reviewed for indexed video search,
  personal saved-video search, video-AI infrastructure, enterprise video
  intelligence, AI visibility suites and native TikTok discovery.
- Live Base2026 routes verified after Worker deployment: homepage, roadmap,
  workspace, health API, static sitemap, dynamic sitemap and a projected source
  page. Cloudflare version is `3f5a6687-4eb8-4ba5-9610-7fe2533282ba`.

## Private Cloudflare capture fairness receipt — 2026-08-26

Live private authority is `base2026-pipeline-control` version `555f0294-5530-4007-85af-d6e4a9639c4d`, backed by private D1 migrations `0013_capture_retry_fairness.sql` and `0014_capture_retry_incident_receipts.sql`; remote migration list is empty. The direct live D1 predicate matched exactly three historical `awaiting_capture`, media-less rows with a Player API retry receipt before migration. They are now private `needs_source_review` rows with immutable hold receipts; their registry rows are held. No source identifier, media, caption, transcript or provider response is represented in this public-operating note.

The source-selection contract is live: only `capture_attempt_count < 4` rows are eligible, due times use SQLite time normalization, fresh zero-attempt sources precede retries, and retry state plus its audit event commit atomically. Initial post-deploy count was 52 `awaiting_capture`, three terminal private reviews, and 210 stored media artifacts. Public Worker/data and broad release gate were not changed.

## Automatic Cloudflare-only publication — live release receipt (2026-08-23)

Public Worker `base2026` version `790e21d6-f341-4265-ae0c-7dc536a32495` is live (rollback `86faccf2-e986-4437-a39a-4b3d66a1883f`). Private Worker v0.6.1 `70fd6e68-ea54-462d-ba27-e3b1a66fa997` is live (pre-automatic rollback `f9e4a494-9780-4bd2-bb33-5b7f5a068f81`); private migrations `0011` and `0012` are applied, none pending. Policy `base2026.machine-publication.v1` / owner `owner-20260823-base2026-auto-publication-v1` / SHA `b37c900a03eb63252c7736c2197f2be1eae3f117eae76914f3cbef306d89e573` uses batch10 and attempts4. `AUTOMATIC_PUBLICATION_ENABLED=true`, `IMPORT_ENABLED=true`, `PUBLIC_PROJECTION_ENABLED=true`, broad `PUBLIC_RELEASE_ENABLED=false`; local adapter false. Schedules are discovery `0 10 UTC` and reconcile/capture/automatic publication `*/5`.

First run: attempted3, applied2, already_public1, retry0, held0, `hard_hold=false`. New public IDs: `7271043105799834912`, `7402026836600851717`; `7662399921894591761` was already legacy public with no duplicate; fixture `7999999999999999933` was absent. Post-counts: public documents2136, distinct videos1557, projection receipts33, cards44, `full_transcript_public=0`; private imports35, applied projections33, ready0, automatic receipts 2 applied + 1 already_public, problems0; registry total4123, `publication_eligible=209`, invalid eligible0. Site hash remains `696c473bc5bf1a93ecb01e140100edc9019f8efc5c8ff3f5a9b29ddc6acdf98d`; API search found both IDs; replay attempted0.

Capacity snapshot: discovery partial 135 discovered / 21 fresh / 114 duplicates / 21 admitted / 0 held / 1 failed; AI jobs 308 completed / 18 pending / 43 held; 8,699 actual/reserved Neurons / 246 invocations / `hard_blocked=0`; monthly `hard_hold=0`, browser hours approximately `0.01793`, container invocations25. Pending jobs resume automatically at the next daily Neuron budget and are not completed. Final `*/5` receipt: reconcile dispatched/recovered/dead-lettered/resumed all0; capture status/attempted/succeeded/failed `completed:0:0:0`; automatic attempted/applied/already_public/retried/held `0:0:0:0:0`; signed `hard_hold=false`. Public34/34, private183/183, courier18/18, types/typecheck/dry-run pass. Observe the first full post-release discovery cycle at `2026-08-24 10:00 UTC`; it has not happened yet.

## Cloud-only private discovery/acquisition — v0.5.2 live checkpoint at 19:56Z (2026-08-23)

Private Worker `base2026-pipeline-control` v0.5.2 (`f9e4a494-9780-4bd2-bb33-5b7f5a068f81`) has migrations `0001`-`0010` applied. Cloud discovery uses the private Browser/Player/Container path; the local adapter and both Base2026 LaunchAgents are unloaded, the direct manual Container endpoint is disabled, and ChatGPT remains a manual owner-only lane. Scheduled capture/reconcile runs every five minutes and discovery runs at `10:00Z`.

Discovery run `83ae6e9cfc18babf715fe66c3a597f597bd16d68` covered 19 creators: 135 discovered, 21 fresh/admitted, 114 duplicates, 1 failed and 0 held. The private registry contains 4,123 rows: 4,102 known, 10 captured and 11 admitted. Final scheduled capture completed 3/3 attempts with zero failures; monthly usage is `.0524033333` GiB-h memory, `.78605` vCPU-minutes, `.2096133333` GiB-h disk and `.0165713889` browser-hours across 12 Container invocations, with reservations at zero and `hard_hold=0`.

At `19:56Z` private D1 contained 213 sources: 12 `awaiting_capture`, 42 `awaiting_transcription`, 10 `awaiting_semantic`, 114 `needs_source_review`, 3 `ready_for_import_held` and 32 `imported_private`. It contained 805 artifacts: 199 media, 159 raw transcripts, 152 metadata, 34 source-intelligence, 34 editorial, 39 production and 188 manifests. At `20:01Z` the next cron captured 2 of 3 attempts, left 1 retry, moved registry status to 12 captured / 9 admitted, moved media to 201, and left five transcription jobs pending at the restored 7,500-Neuron cap. Public D1 remained 2,134 documents / 1,555 videos / 31 applied projections / 42 cards / `full_transcript_public=0`. These counters drift by design; latest D1/status receipts are authoritative.

At `20:21Z`, the discovered wave was fully acquired: all 21 newly admitted registry rows are `captured`, none remain `admitted`, stored media is 210, and 14 new transcription jobs are pending behind the included AI stop. AI usage stayed at 8,699 Neurons / 246 invocations. Capture accounting is 25 invocations with zero reservations and `hard_hold=0`; the remaining `awaiting_capture` D1 row is the older synthetic shadow control.

Four semantic jobs created under the superseded native-schema provider contract are now exact pending rows for `2026-08-24 00:00:00`, each with a pending outbox and `AI_PROVIDER_CONTRACT_REPAIRED_REQUEUE` audit receipt. This repair consumed no AI budget. Evidence-range and transcription-invalid rows remain private review holds.

The primary private `ready_for_import_held` E2E is source `45351675f81412d58f8226fdfa5fee43610798e4` / TikTok ID `7662399921894591761`: media artifact `8fb0b5aaa25c57c7a83d294674f842e70de066af` is 350,070 bytes (hash prefix `76a974…`), and production artifact `e3d7ffe1c3f1a7228d35c7e7e50b4baa9bfa3e30` has hash prefix `042a42…`. Duplicate replay returned `duplicate=true`, `dispatched=false`, `ai_dispatched=false`, with the same artifact and unchanged AI usage; full hashes remain in private receipts.

The exact private cleanup receipts are `PRIVATE_BASE2026_WORK_INBOX/base2026-media-prune-20260823-01/deletion-plan.json` and `deletion-receipt.json`; 143 processed/cloud-backed media files totaling 619,674,115 bytes were removed, while the current dry run is eligible `0` and 139 uncertain files remain retained. No raw media, transcript, provider response or public artifact is represented here.

## TikTok cloud acquisition live receipt — 2026-08-26

Private Cloudflare D1/R2 is the authoritative acquisition source. Worker
`dbad0d33-070a-47fd-9e5e-ea36f18c59d4` runs the healthy Container application
version 6 on `base2026-pipeline-capture:0.5.4`. A signed private capture
two signed reconciliations attempted six queued sources, captured two, and
increased the stored `media` artifact count from 210 to 212. Current retry rows remain
private, durable, and backoff-limited; they are not public data or publication
permission. No public Base2026 data, public Worker, or broad release setting
changed.

## TikTok live and discovery inventory — bounded daily Cloudflare run (2026-08-23)

The fresh private discovery receipt contains 245 TikTok source rows and no discovery failures. Comparing only those receipt IDs against the canonical queue yielded one exact unseen ID; the explicit allowlist dry-run and apply admitted it, and the post-wave remainder is zero. It staged as one audio-only media/manifest pair and uploaded successfully in a one-source, 5,574-byte transfer chunk.

Cloudflare D1 now contains 191 sources, 188 media artifacts, 188 manifests, 151 raw transcripts, 31 source-intelligence artifacts, 31 editorial artifacts, 36 production packets and 32 private imports. The new source is `awaiting_transcription` with `ai_soft_cap`; no Luna/private-import/public-projection work was eligible in this run. Workers AI is 7,494 reserved/actual Neurons on 2026-08-23, hard block `0`. Public D1 remains 2,134 documents / 1,555 unique videos / zero public full transcripts with 31 applied projections.

The private aggregate receipt is `PRIVATE_BASE2026_WORK_INBOX/cloud-discovery-20260823-01/aggregate-receipt.json`. The private inbox boundary still verifies current-user ownership, no symlinks/non-regular entries, directories `0700` and regular files `0600`.

## TikTok live and discovery inventory — repaired checkpoint (2026-08-23)

Local canonical `videos.csv` contains 4,101 unique IDs. The newest 245-row check-only discovery snapshot found eight unseen IDs; all eight were explicitly admitted, so the fresh unseen remainder is zero. Seven produced exact private audio/manifest pairs and uploaded to Cloudflare; `7676979014401051917` remains private `media_retry_pending` after both pre/post-upgrade extractor attempts returned no formats.

Private Cloudflare D1 now contains 190 sources, 187 media artifacts, 187 manifests and 32 private imports. Workers AI ledger is 7,494/7,500 Neurons, hard block `0`; overflow remains private until the next UTC reset. Two current Luna Max batches reviewed 20 ready sources, admitted eight and held twelve.

Public Evidence D1 contains 2,134 documents representing 1,555 unique TikTok videos. There are 31 applied exact projections and 42 projection-owned public rows; `full_transcript_public=0`. Three legacy passages belonging to one contact-bearing video were removed with an exact private rollback receipt before the eight new evidence-valid sources were projected.

`PRIVATE_BASE2026_WORK_INBOX` is an ignored local-only source boundary. Current verification reports only current-user-owned non-symlink directories/files at modes `0700`/`0600`; the daily automation must recheck that invariant on every run.

## TikTok live and discovery inventory — batch operational (2026-08-22)

Public Evidence D1 `base2026-public-search` contains 2,129 public search documents representing 1,548 unique TikTok videos. Twenty-two newly reviewed sources were added through exact projection; each public row remains excerpt-only with `full_transcript_public=0`.

Private local canonical `12_knowledge-base/sources/tiktok/videos.csv` contains 4,093 unique video IDs. The 245-row discovery snapshot started with 35 known and 210 unseen IDs; all 210 are now privately admitted, so the snapshot unseen remainder is zero. Admission is not publication permission.

Of those 210, 178 now have exact private media/manifest pairs in Cloudflare after initial staging and one retry. Thirty-two remain in the private retry/manual-source lane; no-audio/codec sources are not forced through transcription. Total private Cloudflare storage is 180 media plus 180 manifests including two earlier controls.

## Private Cloudflare pipeline sources — operational (2026-08-22)

Private evidence runtime now uses isolated D1 `base2026-pipeline-private` (`91dfd575-029e-43e5-91d6-6cd9aca130ca`) and non-public R2 `base2026-pipeline-artifacts`. These are private processing sources only; neither is a public Base2026 dataset or public-search binding. Queue and Workflow messages contain IDs/hashes, while raw media and stage packets remain in private R2 under retention classes.

Live synthetic verification source `7999999999999999933` is `imported_private` and materialized one `held_private` card under import `a6c7ea121154b043253337b72ff11e1e005f8627`. Release/public/materialized-card flags all read back `0`; production R2 SHA-256 is `0476db9f0a94ba4ff0745c12c3c017a81f2b98a7559dd1ae2c4114250c254bca`. This synthetic record is a control-plane receipt, not a public source candidate.

The local `PRIVATE_BASE2026_WORK_INBOX` remains an ignored rollback/review boundary. At the 2026-08-22 checkpoint, LaunchAgent `com.base2026.cloudflare-pipeline-adapter` read its deterministic controller work order every 15 minutes; it is now unloaded, `LOCAL_ADAPTER_ENABLED=false`, and the retained plist is rollback-only. Manual ChatGPT courier packets also remain inside this private filesystem boundary.

## Outreach source status — curated public v1 live (2026-08-21)

The connected workbook `Outreach Growth Intelligence — X, TikTok, Backlinks` (`1CTeyNPXZWo2ZSSKFis2t3ber0P0b9OXgiRNKaBjVuSQ`) currently has 34 tabs. Canonical primary ledgers include 1,032 findings, 1,004 authors and 245 backlink/directory opportunities. The file also contains private operational Search Ops, GSC, ACQ3/Gmail, queue, client, backup and handoff surfaces. Those surfaces are excluded from Base2026. The derived topic view currently contains a broken reference, and dashboard counts may lag primary ledgers.

Public status: 78 findings are explicitly admitted and live in separate public D1 `base2026-outreach-search` (`ffbef187-67ef-491f-8fae-62f625636ed5`) under logical index `base2026_public_outreach`. They were semantically selected from 400 mechanically eligible candidates; 322 low-fit, weak, redundant, promotional, private or operational candidates remained excluded. The workbook has no public-release field, so future rows stay private until a new semantic selection, source-hash-pinned admission, export/import receipt and controlled release pass. The workbook remains read-only and the research schedule remains frozen.

## Runtime source status — standalone startup release (2026-08-20)

The reviewed public source artifact is live at `https://base2026.dev/` through Cloudflare Workers Static Assets. Evidence search uses reviewed D1 `base2026-public-search` (`ac034130-4169-43c2-9a17-4b72d05457b0`), while curated Outreach findings use isolated D1 `base2026-outreach-search` (`ffbef187-67ef-491f-8fae-62f625636ed5`). The verified startup snapshot records 1,724 sources, 2,319 passages, 18 creators and 1,670 topics; the Evidence D1 has 2,095 chunks and Outreach readback is 78 findings / 78 FTS rows / 83 topics / 86 lanes. The former VPS Meilisearch runtime is rollback-only and is not the current public search path.

The public/private boundary is unchanged: raw captions/ASR/media, private vaults, local databases, review queues, logs and credentials are not Cloudflare/public sources. Support and Partner proposals enter only the separate private `base2026-inbox` D1 (`542a77ef-da00-4522-8b7a-3d78fc646c72`) with the documented retention boundary; no intake data is merged into public search.

Private queue completion receipt: the final two `daily-batch-20260729-01` sources, `7667677267211865376` and `7667726450258201869`, imported with four approved cards and shipped through acknowledged data-only release `base2026-daily-batch-20260729-03-release`. The release is live-verified. Aggregate controller state is `already_imported=33`, `hold_private=60`, no pending release admission, and `idle`; the queued/needs-source-review selector returned zero eligible or unclaimed records.

Private queue receipt: the 2026-07-28 controller-authorised final two-source work order imported source IDs `7666938115918957857` and `7667255862116879648` from `daily-batch-20260728-01`. Data-only release `base2026-daily-batch-20260728-03-release` is deployed, live-verified, and acknowledged. Aggregate controller state is `already_imported=23`, `hold_private=60`, no pending release admission, and `idle`.

Private discovery receipt: the 2026-07-29 daily check-only refresh found 135 recent candidates and bounded import to exactly 10 new queue rows. All 10 explicit sources staged and produced durable private raw-transcript packets. The first controller-authorised group of four completed the private ChatGPT lane, imported ten approved cards, and shipped through acknowledged data-only release `base2026-daily-batch-20260729-01-release`. The next group of four also completed the private lane, imported eleven approved cards, and shipped through acknowledged data-only release `base2026-daily-batch-20260729-02-release`. The final two records completed all private stages, imported four approved cards, and shipped through acknowledged data-only release `base2026-daily-batch-20260729-03-release`. Aggregate controller state is `already_imported=33`, `hold_private=60`, and `idle`, with no pending release admission and `public_content=false`.

| Source | Status | Public? | Notes |
| --- | --- | --- | --- |
| Cloudflare private evidence control plane | live/private v0.5.2 | no | D1/R2/Queues/Workflow/Browser/Player/Container state for authenticated bounded processing only. Migrations `0001`-`0010`; cloud-only discovery/acquisition, local adapter off, direct manual Container endpoint off, `PUBLIC_RELEASE_ENABLED=false`; exact private-import receipts and public flags remain owner-gated. |
| TikTok: `@webhivedigital` | indexed; SEO/WordPress hybrid | yes, reviewed export only | Public creator source. Reclassified by `BASE2026_WORDPRESS_VERTICAL_AUDIT_2026_07_04.md` as `seo_wordpress_hybrid`: keep SEO/search material in SEO/GEO lanes, and route plugin/CMS/WordPress implementation material into the private-first WordPress/CMS vertical. The 2026-06-12 source `tiktok-video-7650509272832380183` has a reviewed public AI Search Traffic insight. The 2026-06-17 source `tiktok-video-7652365345709231382` was blocked by newest-source readiness until a strict exact-evidence public insight was reviewed/promoted for `WordPress SEO / plugin capabilities`. 2026-07-04 Batch #2 added 10 private reviewed WordPress/CMS/ecommerce-CMS cards from this source family under `docs/research/BASE2026_WORDPRESS_CMS_CARD_BATCH2_2026_07_04.md`; these are `reviewed` only, not approved/public. |
| TikTok: `@tjrobertson52` | indexed; eight new packets live; one historical production hold | yes, reviewed export only | Public creator source. The 2026-06-12 source `tiktok-video-7650601606215372046` now has reviewed public AI Knowledge Base and Open Knowledge Format insights. On 2026-07-27, one production record returned `NOT_ADMITTED` and remains a terminal private hold; its source identity is intentionally omitted from public-safe documentation. Releases `base2026-daily-batch-20260729-01-release` and `base2026-daily-batch-20260729-02-release` added seven controller-authorised source records with 20 approved cards total. Release `base2026-daily-batch-20260729-03-release` added `tiktok-video-7667726450258201869` with three approved cards. All passed exact live-route/dataset verification. |
| TikTok: `@build_in_public` | indexed; latest controller packet live | yes, reviewed export only | Public creator source. ay71 refresh added 1 new caption-backed source and 2 exact-evidence public insight cards. The 2026-06-13 source `tiktok-video-7650935514643614998` now has reviewed public topics/insights for Brand Mentions and Channel Strategy. ay41 added the 2026-06-18 source `tiktok-video-7652732487843581206`; newest-source readiness blocked it until a strict exact-evidence insight was reviewed/promoted for `Search Console / high-intent queries`. 2026-06-27 source-review cleared user-approved `tiktok-video-7655821023589272864` after metadata/VTT/video-audio ASR verification; release `base2026-social-source-footprint-20260627` publishes it with a reviewed `AI Overview source footprint` Source Intelligence card framed as off-site/social citation-surface trust-risk evidence, not as a spam tactic. The 2026-07-28 data-only releases acknowledged seven admitted batch packets. Release `base2026-daily-batch-20260729-01-release` added one controller-authorised source record with one approved card; release `base2026-daily-batch-20260729-03-release` added `tiktok-video-7667677267211865376` with one approved card. Both passed exact live-route/dataset verification. |
| TikTok: `@joshuamaraney` | indexed | yes, reviewed export only | ay63 refresh added 1 new caption-transcribed source and closed its polish/export path. The 2026-06-14 source `tiktok-video-7651218412475059464` was operator-approved and now has reviewed public topics/insights for AI Model Governance and AI Security Risk in `base2026-content-pipeline-fix-20260615`. ay41 added the 2026-06-18 source `tiktok-video-7652742095228210450` after current-batch polish and release-gate checks. |
| TikTok: `@darrenshawseo` | indexed; one new packet admitted locally, release blocked | yes, reviewed export only | Public creator source added in `base2026-darrenshawseo-intake-ay90-r2-20260616`. Public export includes a stable local creator avatar at `/knowledge/static/assets/creators/darrenshawseo.jpeg` copied from the public TikTok profile image. ay41 added the 2026-06-18 source `tiktok-video-7652758207361731847` after current-batch polish and release-gate checks. ay54 added a strict reviewed Source Intelligence card for `tiktok-video-7652384458804432136` under `Local SEO service-area rankings` after the live source page showed an empty Source Intelligence layer and invalid Q&A fallback. On 2026-07-27, production packet `7663512971737484551` was admitted and imported locally; it is not live because the public export gate stopped before a candidate was created. Existing admitted source `7662399921894591761` is one of the two stale row-state blockers requiring controller-authorized reconciliation. Held rows remain gated when source/audio verification is required. |
| TikTok: `@heytonyagency` | indexed/gated mixed | yes, reviewed export only | Added in `base2026-ai-recommends-creators-ay42-20260618` from the AI Recommends Solutions creator pass. Discovery imported recent TikTok candidates into private local `videos.csv`; only QA-pass polished/reviewed public rows are exported. QA-needs-review/source-review rows remain private/gated. |
| TikTok: `@iamdandavies` | indexed/gated mixed; WordPress anchor | yes, reviewed export only | Added in `base2026-ai-recommends-creators-ay42-20260618` from the AI Recommends Solutions creator pass. Reclassified by `BASE2026_WORDPRESS_VERTICAL_AUDIT_2026_07_04.md` as the first `wordpress_anchor` for the private-first WordPress/CMS implementation insights vertical. The newest-source readiness gate blocked `tiktok-video-7652708771701067030` until a strict exact-evidence reviewed insight for `WordPress static homepage setup` was added. 2026-07-04 Batch #1 added 10 private reviewed cards from this creator, and Batch #2 added 2 supplemental private reviewed cards for form-plugin/SMTP tradeoffs and client-manageable CMS capability. The 2026-07-27 autonomous transcription pass added another low-confidence record to a terminal private hold; it is not eligible for Source Intelligence or public export. Remaining QA-needs-review/source-review rows stay private/gated. |
| TikTok: `@harrysandersseo` | indexed/gated mixed | yes, reviewed export only | Added in `base2026-ai-recommends-creators-ay42-20260618` from the AI Recommends Solutions creator pass. Public output is limited to QA-pass polished/reviewed rows; uncertain transcript/source rows remain private. |
| TikTok: `@ray_fu` | indexed/gated mixed | yes, reviewed export only | Added in `base2026-ai-recommends-creators-ay42-20260618` from the AI Recommends Solutions creator pass. Public output is limited to QA-pass polished/reviewed rows; uncertain transcript/source rows remain private. |
| TikTok: `@gobigsystems` | indexed/gated mixed | yes, reviewed export only | Added in `base2026-ai-recommends-creators-ay42-20260618` from the AI Recommends Solutions creator pass. ay44 fixed two fresh source-only readiness blockers by adding exact-evidence reviewed Source Intelligence cards for `AI Recommendation Readiness` and `Google Business Profile Search Terms`. ay45 added one ASR-recovered QA-pass public source through the canonical release gate. ay46 added one strict exact-evidence `Google Business Profile Categories` readiness card. 2026-06-27 overnight release added one strict exact-evidence reviewed card for local Google Ads negative-keyword guidance. Public output is limited to QA-pass polished/reviewed rows; uncertain transcript/source rows remain private. |
| TikTok: overnight marketing/growth expansion (`@neilpatel`, `@willfrancis24`, `@samdespo`, `@keenyakelly`, `@jera.bean`, `@keeansocial`, `@pulpdigitalagency`, `@tiktokforbusiness`, `@tiktok_small_business`) | indexed/gated mixed | yes, reviewed export only | Added to local intake queue on 2026-06-27 after TikTok profile JSON follower verification, each >=50k followers. Discovery/import produced 45 local video rows. Release `base2026-overnight-marketing-creators-20260626` shipped only QA-pass polished/reviewed rows: 17 publishable/pass batch rows, 24 source-review holds kept private, 5 older/off-topic rows marked `out_of_scope_old`. The 2026-07-27 autonomous transcription pass moved one additional `@tiktokforbusiness` record to a terminal private low-confidence hold. Its one minimal schema-valid companion later returned zero Source Intelligence cards and `OUT_OF_SCOPE`, so it also remains a terminal private hold. Neither changed public output. |
| Private Base2026 SEO/GEO/AEO files | local only | no | Do not publish raw project folders. |
| `public-data/tiktok` | generated local export | no git | The 2026-08-29 reviewed public artifact contains 1,525 static documents, 2,095 passages, 1,939 reviewed public insight cards, 1,670 topics, 1,204 public topics, and 18 public creators from the dated 2026-07-29 snapshot. The 524 `needs_review`/non-public card rows remain outside the Cloudflare artifact. Live source records include reviewed `public_source_text`, `source_summary_short`, and `source_summary_long` while keeping legacy `transcript` empty and `include_full_transcripts=false`. Raw captions, raw ASR, media, logs, private QA, and unreviewed transcripts remain local/private. Runtime copies of `documents.jsonl`, `passages.jsonl`, `insight_cards.jsonl`, and derived public analytics files live under `/knowledge/static/` for source-detail/search analytics hydration. Caption/platform metadata snippets are not rendered as public UI blocks. Source UI should not duplicate the same transcript-like text across excerpt/matched/related sections; insight evidence is collapsed by default; same-source passage fragments already contained in `Source Text` must not render as separate supporting evidence. Closely related Source Intelligence rows are grouped into one card with topic chips. Source Q&A renders only from reviewed Source Intelligence cards, not from source text fallbacks. `/knowledge/api.html`, `/knowledge/api-index.json`, and `/knowledge/llms.txt` document public read-only AI/API access over reviewed public data only. Clean rebuild replays ignored reviewed legacy/candidate archives and keeps `claim_evidence` duplicate claim IDs at 0. |
| Meilisearch index `base2026_public_tiktok` | deployed runtime | public search only | Search key only; master key private. Last reindexed during `base2026-daily-batch-20260729-03-release` with 2,095 public search documents (task `551`). |
| TikTok transcript queue `config/tiktok-intake-queue.local.json` | idle | no git | Mac pipeline refresh is operational after runner fixes. The 2026-07-29 bounded daily intake added exactly 10 recent queue rows, staged all 10 explicit sources, and produced 10 durable private raw-transcript packets. All three controller-authorised groups completed the full private ChatGPT lane, imported 25 approved cards total, and shipped through acknowledged releases `base2026-daily-batch-20260729-01-release`, `base2026-daily-batch-20260729-02-release`, and `base2026-daily-batch-20260729-03-release`. Current totals are `already_imported=33` and `hold_private=60`, with no pending release admission and `public_content=false`; the persisted controller work order is idle. The queued/needs-source-review selector returned zero eligible, inflight, selected, or unclaimed records. The remaining discovery preview was not bulk-imported. `scripts/hermes-tiktok-refresh.ps1 -AfterPolish` skips inventory/caption intake and only rebuilds from existing reviewed polish outputs. `scripts/hermes-tiktok-refresh.ps1 -CheckOnly` is read-only and verified by hash before/after. Held rows must remain gated until source/audio verification. |
| Platform-neutral social discovery spool `.planning/social-discovered.jsonl` | private proof layer | no git | Phase 1/2 from `docs/research/FREE_SOCIAL_VIDEO_INTAKE_RECOMMENDATIONS_2026_06_18.md` is implemented locally. `scripts/social-discover.py` reads current creator config shapes, discovers TikTok creator posts with `yt-dlp --flat-playlist`, writes normalized private JSONL, and does not modify `videos.csv`. The ay42 AI Recommends Solutions run wrote 200 private records across 10 configured TikTok creators, then the dry-run-first importer added 100 deduped candidates on explicit apply with an ignored backup. Phase 3 bridge is `scripts/import-social-discovery-to-tiktok-csv.py`: dry-run by default, TikTok-only, dedupe by `video_id`, safe missing-metadata fill, old-row cutoff, and ignored backup before `--apply`. Instagram currently records `missing_adapter_gallery_dl` because optional adapters are not installed and must not be imported into TikTok `videos.csv`. |
| TikTok source-review backlog | needs review | no git | Overnight marketing/growth expansion added 24 private source-review holds from new verified creators; they must be reviewed one by one before public clearance. User-approved review candidate `tiktok-build-in-public` / `7655821023589272864` should be evaluated as cautionary evidence for AI Overview/social-UGC citation and off-site AI visibility footprint, not as a spam tactic. Broader historical source/audio verification debt remains gated. Rows stay private until audio/source verification; source records without usable public transcript/chunks are excluded from public source JSONL/static pages. Explicit QA-pass rows may be cleared with `scripts/tiktok-clear-reviewed-source-rows.py`, which verifies QA/pass and transcript file presence before changing private `videos.csv`. |
| Private insight-card backfill queue | active local queue | no git | ay52 generated 21 local candidates for the 5 new source records, evidence-verified all 21, promoted 6 public candidates, and retained 15 private `needs_human` candidates. ay57/ay58/ay59 resolved/replayed the first reviewed-candidate archive. ay67-ay71 promoted 54 exact-evidence public cards after GPT/Codex review gates. ay79-ay81 closed the legacy public-card contract: public legacy cards are now explicit reviewed/approved rows, `auto_evidence_match` public output is 0, and ignored local replay archives preserve reviewed legacy/candidate state across clean SQLite rebuilds. 2026-06-15 content-pipeline fix added 7 approved reviewed candidate rows for fresh source-only records and fixed public export to honor reviewed evidence spans. Visual-dependent cards remain gated until a thumbnail/frame evidence lane exists. |

| AI visibility page batch `data/ai_visibility_pages_batch01.json` | deployed static public pages | public-safe after generation QA | 2026-06-26 overnight batch removed private absolute `source_file` paths, normalized HVAC display text, and now contains 23 source-backed/content pages plus the collection output. Broad hub/proof pages are indexable/live, including measurement, AI-ready documentation, review sentiment, and service-area AI visibility pages; 16 California city/niche audit pages are generated as `noindex,nofollow` until unique local evidence is added. Latest live static release: `base2026-service-area-ai-visibility-20260626`. |

Rule: update this file whenever a source is added, removed, reclassified, or moved from local-only to public-safe export.

Runtime update 2026-08-19: the reviewed public Base2026 artifact is now served from Cloudflare at `base2026.dev`. Public search moved from the VPS Meilisearch proxy to D1 FTS5 (`base2026-public-search`, 2,095 documents). Private source vaults, raw media/captions, local databases, logs, and review queues remain local/VPS-only and were not copied to Cloudflare.

Runtime update 2026-08-28: Google Search Console Domain property
`sc-domain:base2026.dev` is verified under `hello@base2026.dev`; Bing Webmaster
Tools imported only `https://base2026.dev/`. Both receive
`https://base2026.dev/sitemap.xml` and
`https://base2026.dev/sitemap-dynamic.xml`; Google reports Success and Bing is
Processing with zero immediate errors/warnings. These are measurement sources,
not public content sources, and no account token is stored in the repository.
DataForSEO remains a cost-controlled external measurement source. One bounded
positioning packet was executed on 2026-08-28 for `$0.077`; its exact receipt is
`DATAFORSEO_POSITIONING_RECEIPT_2026_08_28.md`. Do not repeat paid tasks without
a concrete decision need and current price verification.

Runtime update 2026-08-29: Google last read the static and dynamic sitemaps on
2026-08-29 and reports Success with 1,634 and 49 discovered pages. Bing reports
Success with 833 and 39 discovered URLs, zero sitemap errors and zero warnings.
Both performance/indexing datasets are still processing; discovered sitemap
counts are not indexed-page or traffic evidence. Exact safe receipt:
`BASE2026_GSC_BING_READBACK_2026_08_29.md`.

Runtime update 2026-08-29 (public): Worker
`79e3677f-3828-4355-8c59-8801458f0fb2` serves 2,175 public documents across
1,574 videos, 50 applied evidence routes and 83 projection cards. Read-only
`/api/stats` reports the same totals and zero public full transcripts. The
verified 2026-07-29 static Analytics summary remains a dated historical source,
not a current D1 counter.

Runtime update 2026-08-29 (reviewed dataset release): Worker
`fadc6c25-1d9f-4805-aed2-614e1463a018` serves the public `/dataset` landing,
quickstart and versioned sample/catalog files. The deployed static artifact has
1,939 insight-card rows and zero `public:false`, `needs_review:true` or
non-public-policy rows. Live D1 remains a separate current source with 2,175
documents, 1,574 videos, 50 evidence routes, 83 projection cards and zero full
transcripts. The GitHub release `public-data-v2026.08.29` publishes only the
public catalog JSON; generated data bodies remain runtime artifacts rather than
Git-tracked source.

Runtime update 2026-08-29 (contextual discovery): Enigmavista, Dreamwood and
Aster each expose one useful, crawlable page with one branded contextual link
to Base2026 public evidence. Enigmavista uses `/projects/base2026/` and links to
the live `/topics/ai-visibility-and-answer-readiness` evidence page; Dreamwood
and Aster use `/source-transparency/`, link to `/dataset` and are discoverable from
`/answers/` and `/city-guides/` respectively. All three pages are live and in
their XML sitemaps. Golem Roofing is code-merged only and remains excluded from
the live-source count until its production deployment receives a real receipt.

Runtime update 2026-08-29 (private): Worker
`4d9f291e-0f7e-4795-adb4-e18c5f028d58` restored discovery to 18 active
creator cursors and one `@webhivedigital` source-review failure. One bounded
canary stored media and completed downstream AI jobs, but used official Player
API Browser acquisition rather than Container fallback. Container app v8 is
running while health telemetry remains unstable (`active=1`, `healthy=0`, no
reported errors); this is an infrastructure observation, not authority to
repeat restarts or widen acquisition.

Runtime update 2026-08-29 (editorial distribution): the canonical engineering
article is live at
`https://base2026.dev/journal/source-backed-video-search-cloudflare/` on public
Worker `3e06c10b-9fa4-40aa-ad14-913a11b85f30`. The Medium copy is live and
canonicals to Base2026. Adapted X and LinkedIn posts are live and link to the
canonical article. Exact URLs, hashes and scope are recorded in
`BASE2026_EDITORIAL_SYNDICATION_RECEIPT_2026_08_29.md`. These external pages are
distribution/measurement sources, not Base2026 evidence-corpus inputs.

Runtime update 2026-08-29 R2 (private): Worker v0.6.2 deployment
`14adacb6-7f0f-4aa7-9131-fc41469eec15` has 14 migrations applied and none
pending. Private D1 records 339 sources and 318 stored-media artifacts; direct
R2 aggregation returns the same 318 media objects among 1,280 objects. There
are no stale leases, failed/dead jobs or Queue delivery failures. Automatic
publication is caught up at 19 applied plus 1 already-public receipt and zero
eligible candidates. The Container is active/running with no errors or failed
instance; `healthy=0` remains a contradictory detail counter, not a restart
trigger. Exact safe aggregate receipt:
`BASE2026_PIPELINE_READBACK_2026_08_29_R2.md`.

Runtime update 2026-08-29 R2 (search measurement): Google Search Console now
reports 0 clicks, 22 impressions, 0% CTR and average position 55.4 across 13
pages for the last three months. The indexed `.html` AI-citation topic and the
current extensionless canonical are in a stored-crawl transition following the
2026-08-28 redirect/canonical correction; Page indexing and Links still
process. Bing Search/AI Performance remains unpopulated, while a live journal
test says it can be indexed with no SEO/GEO issue and the index view says
discovered but not crawled. No indexing request or sitemap resubmission was
made. Exact receipt: `BASE2026_GSC_BING_READBACK_2026_08_29_R2.md`.

Runtime update 2026-08-30 (public technical release): Worker
`eeeabd1b-7454-4ec5-9ac3-6b35d3bb3fa3` serves artifact tree
`02dc9883597dfab6215cb10b2082c19c804fda21bbbc3e71fe882a2d273a3065`.
Post-deployment public D1 readback is 2,175 documents, 1,574 distinct videos,
50 applied projections, 83 cards and zero public full transcripts. The query
changed no rows. All four public JSONL distributions are byte-identical to
the pre-deployment live files; no source admission, import, private data
publication or external submission occurred. Sitemap, API-index, security,
cache and roadmap fixes are now live, not merely prepared. Exact receipt:
`BASE2026_TECHNICAL_RELEASE_2026_08_30.md`. Private pipeline and GSC/Bing
snapshots above remain dated 2026-08-29.

Runtime update 2026-08-30 (source-diversity growth): public Worker
`d242f1aa-60f5-4ff5-97af-883318173027` serves the additive article release,
tree `473d735f87d8c8aad2b2bbec77a1c7db9e613b88c257e03c197b76f8577c86cf`.
The dated public V2 query `AI citation tracking` returned 12 matched records,
three selected sources and two distinct creators. This is one query/corpus
observation; `status: full` is not factual validation or complete coverage.
Public D1 counters and all four JSONL payloads remain unchanged; private state
was not reread or changed by this growth release.

The new canonical article, canonicalized Medium copy and four-part X thread
are live. Four additional X posts are scheduled, not published. Official
Buffer readback and native X/Medium UI confirm the exact states recorded in
`BASE2026_GROWTH_RELEASE_2026_08_30.md`. LinkedIn is now Computer Use-only; no
new LinkedIn publication is claimed. External distribution is measurement,
not evidence-corpus intake. Credentials, private audience data, API operation
logs and browser/security receipts remain outside public Git.
