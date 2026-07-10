# Base2026 Source Card Completeness Production Release — 2026-07-10

## Status

**Deployed and live-verified.**

- Release: `base2026-card-completeness-r1-20260710-173448`
- Previous rollback target: `base2026-tiktok-public-20260703-1711`
- Production symlink: `/var/www/base2026-knowledge/releases/base2026-card-completeness-r1-20260710-173448`
- User approval: explicit in Telegram topic 22.

## Live contract

| Admission state | Count | Public behavior |
|---|---:|---|
| Normal public card | 1,493 | Searchable/indexable; every card has public Source Intelligence and Questions |
| Provenance archive | 199 | Direct source page retained, visibly labeled, `noindex`, excluded from search/sitemap |
| Future private backlog | 122 | No public page, search document, Meili record, or sitemap URL |
| Total classified | 1,814 | Closed admission ledger |

Three sources arrived after the local freeze. All three were QA-pass but lacked reviewed Source Intelligence, so they were added to the private future backlog before packaging.

## Production verification

- Live JSONL hashes match the deployed package.
- `documents.jsonl`: **1,493** normal cards.
- Normal cards without public Source Intelligence: **0**.
- Public insight cards: **1,873**.
- Meilisearch task `487`: **succeeded**; 2,052 indexed chunks across 1,493 normal source IDs.
- Sitemap: 5 child files, 1,734 unique URLs, no duplicate URLs.
- Unit tests: **45/45 passed**.
- ZIP: 4,178 files, no private transcript/SQLite/admission artifacts.

## User-reported URL

`https://aggressorbulkit.online/knowledge/sources/tiktok-video-7656864410052627714.html`

Live result after release:

- HTTP **404**;
- absent from `documents.jsonl`;
- absent from sitemap;
- absent from Meilisearch;
- old source-only page is gone.

Its canonical admission state is `future_private_backlog`; it remains private until later evidence-backed clustering.

## Samples

- Normal complete: `https://aggressorbulkit.online/knowledge/sources/tiktok-video-7508482964414663958.html` — `200`, `index,follow`, SI + Questions, sitemap + Meili present.
- Archive: `https://aggressorbulkit.online/knowledge/sources/tiktok-video-7509256911708261634.html` — `200`, provenance label, `noindex`, excluded from sitemap + Meili.

## IndexNow closure

- Current sitemap live gate: **1,734/1,734 eligible** (`200`, indexable, self-canonical).
- Archive gate: **199/199** live `noindex`; none were submitted as indexable URLs.
- Previous-public/current-private diff: **62/62** live HTTP 404 and absent from the current sitemap.
- Public IndexNow key-file verification: passed.
- Current/updated URL submission: **1,734 URLs, HTTP 200**.
- Deleted URL notification: **62 URLs, HTTP 200**.

Receipt: `.planning/tiktok-pipeline-v2/indexnow-card-completeness-2026-07-10/indexnow-release-closure-receipt.json`.

IndexNow acceptance is a crawl notification, not a guarantee that Bing will index every eligible page.

## Git publication closure

- Dirty worktree classified instead of using blanket `git add -A`.
- Temporary GSC helpers removed; ignored private/release artifacts stayed outside Git.
- Publication boundary: **218/218 public-safe**, 0 forbidden, 0 needs-review, 0 secret findings.
- Tests: **45/45 passed**; Python compile, GitHub metadata, AI Recommends contract/HTML validation, and `git diff --check` passed.
- Scoped commits were prepared on `codex/base2026-launch-next` for pipeline/contracts/tests, public surfaces, research/project records, and final release documentation.
- Remote publication proceeds through existing PR #8 rather than an unreviewable blanket commit.

No Google bulk indexing automation was performed. Google remains on sitemap discovery plus selective GSC inspection for priority pages; no outreach was performed.

Machine receipt: `.planning/tiktok-pipeline-v2/production-completeness-release-receipt-2026-07-10.json`.
