# Base2026 editorial runtime — live release and first article

Verified 2026-08-30. This is a production receipt, not a proposed architecture.
The older technical/source-diversity receipts remain release history.

## Exact production

- Public Worker: `2b1a1c19-a9ab-4c43-b4b6-973678d9ee07` at 100%.
- Immediate public rollback: `d242f1aa-60f5-4ff5-97af-883318173027`.
- Artifact: `base2026-growth-office-20260830-v3`; tree SHA-256
  `1d0220c8392aa36e712b7a2f0ffb2a718fa5b807d993157e6f3cbff58629ec92`.
- Public migration `0004_editorial_articles.sql` applied: additive article and
  receipt tables only. Existing search data and counters remain separate.
- Separately owned private ingress: v0.6.4,
  `9b72420c-e963-4d52-b67b-f49c4bec6534`; rollback
  `ba61607a-0748-4cd4-877d-9dd863f097e1`. No new private migration, secret,
  broad-release gate or Container change in that ingress release.
- Source branch: `codex/base2026-growth-office-20260830`, unchanged HEAD
  `5b709108d69229d92fa2a73b049392e161781969`. Exact working-tree changes are
  deployed but not committed/pushed. HEAD alone does not reproduce this release.

## What now works

The canonical [blog](https://base2026.dev/blog) joins the two retained journal
articles with reviewed original articles from public D1. New article text is
published through the authenticated private admin receiver and the existing
Worker service binding. No public HTTP write endpoint is exposed.

Each article automatically updates server-rendered HTML, `/api/blog`, RSS and
an independent blog sitemap. The shared header/footer link to the blog; article
pages link to sources, related research and evidence search. A text-only article
does not require a static rebuild. A new image requires a reviewed asset release.

Operating contract: [`BASE2026_EDITORIAL_PUBLISHING.md`](../BASE2026_EDITORIAL_PUBLISHING.md).
The TikTok acquisition/projection lane is still a separate system governed by
the canonical Cloudflare pipeline manual.

## First real article and exact replay

- [AI visibility is not traffic: a four-part measurement worksheet](https://base2026.dev/blog/ai-visibility-measurement-worksheet/).
- Revision 1; nine cited public sources; five sections; original practical
  worksheet with visible AI assistance and illustration disclosure.
- Exact normalized payload SHA-256:
  `ba59b023b672d0c82010ce75d9f716b605e1dcfd199e98a22f3e4655d71072c1`.
- Reviewed at `2026-08-30T21:04:00.948Z`; actual publication receipt recorded
  at `2026-08-30T21:08:58.525Z`. Editorial publication/update metadata is
  `2026-08-30T21:03:11.746Z`.
- First signed dispatch returned `published`; signed inspection returned the
  exact current tuple. One deliberately authorized identical replay returned
  `already_published`, with the same recorded time/hash/revision.
- Public D1 remained **one editorial article and one publication receipt**.
  No overwrite, duplicate, synthetic production fixture or direct SQL write.
- Blog/API/RSS now list **three articles total**: two legacy journal entries
  and one new D1 article. The blog sitemap child lists exactly the new article;
  legacy journal URLs remain in the static hub sitemap and do not move.
- Source corpus remains 2,175 documents, 1,574 sources, 50 evidence routes,
  83 cards and zero public full transcripts.

## Verification

- 308 public Worker tests, including actual D1 atomic/replay/race tests and 55
  CLI subprocess checks; typecheck and exact-candidate Wrangler dry-run pass.
- 58 selected Python release/UI tests pass. Independent Sol Max source review
  found no remaining blocker after four reproduced route/render defects were
  fixed: absent search bridge, conflicting card IDs, sitemap payload validation,
  and duplicate template-region delimiters.
- Private ingress owner reports 248 Worker and 18 courier tests plus type and
  dry-run checks. Missing admin-secret fallback and uncertain post-write receipt
  handling were independently found, reproduced and fixed before deployment.
- Artifact gate passes with exactly four approved public JSONL files. Repo
  audit: forbidden paths zero, credentials zero. Four new Python tests flagged
  for manual review were individually classified public-safe; no scanner waiver.
- Three protected shared/home/founder stylesheets and four public dataset files
  are byte-identical to the previous reviewed release. Existing HTML changes
  are limited to two header Blog links and one footer Blog link.
- Live homepage/founder response bytes match the candidate; Workspace and
  health/API remain 200. Public POST `/api/blog` returns 405.
- At 21:11 UTC article, public DTO, hub, RSS, sitemap index and child all return
  200. Canonical, exact payload hash, one H1, disclosure, nine citations and four
  related destinations pass; all related destinations return 200 directly.
- Native Chrome at 1440/390 px: no horizontal overflow, image loaded, all TOC
  and citation targets resolve. Keyboard focus, reduced motion and native mobile
  navigation passed. Content requires no executable JavaScript.
- Reviewed AI image SHA-256:
  `77db0ab313b1df0b484db6dfa71ed50ff0a5ebc32383f1a25eb956c89ba9389f`;
  1536 by 1024 pixels. Live image bytes match; it is not a measured dashboard.

## Search discovery and distribution

IndexNow accepted exactly the blog hub and new article with HTTP 200 at
`2026-08-30T21:13:11.097Z`, using the existing verified key. This is submission,
not indexing or a ranking result. No old URL batch was resubmitted.

Google Search Console confirmed the new `sitemap-blog.xml` submission. Its
initial table state was `Unknown / Couldn't fetch`, zero discovered URLs.
A separate Google live test at 21:20:06 UTC then proved **Crawl allowed: Yes;
Page fetch: Successful; Indexing allowed: Yes**. The sitemap and child also
parse as valid XML and return 200 to the documented Base2026 client. The
follow-up native report at about 21:50 UTC then showed **Sitemap index / Success /
Last read August 30 / 1 discovered page / 0 videos**. The initial fetch-pending
state resolved without another submission. Discovery is not indexing success.
Default Python-urllib requests triggered Cloudflare 1010, while the documented
truthfully identified client worked. No WAF setting or browser identity was
changed to obtain the Google live-test result.

The new four-part X adaptation was sent through Buffer Free at 21:18:43 UTC:
[native thread](https://x.com/AleksejAros/status/2094172998009835607).
Native readback verified all four parts, the loaded illustration with disclosure
and the final link card; its redirect resolves directly to the live article.
Four previously scheduled X posts were preserved.
LinkedIn remains Computer Use-only with its existing action-time gate; no new
LinkedIn post, login or Buffer connection was made.

The existing six-hour heartbeat was updated and its persisted configuration
verified as **Base2026 — Editorial and X growth office**, ACTIVE, in the same
task. All helpers use Sol Max. It covers source-based article preparation,
separate exact-hash review, one protected data-only publisher, live readback,
X queue reconciliation and attributable measurement. Routine runs cannot edit
Worker code, schema, design, DNS, Git or intake policy. Its first future run
under these updated instructions is not yet observed.

## Sources and remaining boundaries

The Sol Max source office verified 36 creator candidates, including 16
creator-site-corroborated Instagram identities and eight exact Instagram URLs
from four creator sites. **Zero new creators were admitted, and zero Instagram
captures were proved.** TikTok-only runtime identifiers must not be relabeled
as a working Instagram/YouTube adapter. Access, rights and cross-platform
duplicates remain separate preflight questions.

Three further editorial briefs were prepared from six public evidence-brief
requests with verified contextual internal links. They are research inputs,
not approved or published articles. All current AI execution seats are Sol Max;
the existing Cloudflare transcription model was not silently replaced.

Serving and durable article publication are Cloudflare-native. Sol Max research,
review and queue refill currently need the owner's Codex host and protected
credentials. No unlimited cloud-only ChatGPT Pro bridge, paid upgrade, new paid
model API, bought backlink or traffic outcome is claimed.
