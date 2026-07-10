# Base2026 TikTok public deploy — 2026-07-03

Release: `base2026-tiktok-public-20260703-1711`
Live path: `https://aggressorbulkit.online/knowledge/`
Remote current: `/var/www/base2026-knowledge/releases/base2026-tiktok-public-20260703-1711`

## Root causes fixed/handled

- Public deploy was blocked by the newest-source readiness gate: fresh TikTok sources were visible as source-only records without reviewed Source Intelligence.
- A mixed retry batch had three ASR-derived items that were not safe for public promotion; they were kept private as `needs_source_review`.
- The release boundary also failed while unrelated needs-review files were in the working tree; those paths were temporarily stashed for the deploy gate and restored after deploy.
- Packaging initially failed on Python 3.9 because `scripts/generate-ai-visibility-pages.py` used `Path.write_text(..., newline="\n")`; changed it to `path.open(..., newline="\n")`.

## Fresh TikTok split

Published / public-ready with reviewed insight cards:

- `7657320829214035214` — Google Business Profile search phrases → services/local pages.
- `7658272059235044622` — know/go/do/buy micro-moment intent mapping.
- `7658364826338512141` — fast lead response / AI responder for hot leads.

Held private as `needs_source_review`:

- `7658374079799446797`
- `7658424210007657736`
- `7658443172820815135`

## Verification evidence

Release gate before deploy:

- `check-public-content-readiness`: `blocked=[]`, `sources_checked=3`.
- `audit-publication-boundary`: `changed_files=153`, `public_safe_candidates=153`, `needs_review=0`, `forbidden=0`, `secret_findings=0`, `ok_to_stage_public_safe_candidates=true`.
- Public export policy: `ok=true`, `include_full_transcripts=false`, `source_records=1614`, `passages=2188`, `insight_cards=1648`, `public_insight_cards=1077`, `public_topics=1024`.
- Release contract: `ok=true`, `violation_count=0`.

Deploy:

- nginx config test passed before and after switch.
- Remote current symlink: `/var/www/base2026-knowledge/releases/base2026-tiktok-public-20260703-1711`.
- Meilisearch reindex: `indexed=2188`, `index=base2026_public_tiktok`, `task=483`.
- Live SEO crawl gate: `status=pass`, `crawled_pages=500`, `sitemap_urls=1775`, `bad_link_contract_count=0`, `crawled_error_pages=0`.
- Base2026-only mobile visual QA: `results=42`, `failures=0`.

Live smoke:

- `/knowledge/static/manifest.json`: `documents=1614`, `chunks=2188`, `public_insight_cards=1077`, `created_at=2026-07-03T17:10:36`.
- Live static data contains the three published fresh video IDs in `documents.jsonl`, `passages.jsonl`, and `insight_cards.jsonl`.
- Live static data does not contain the three held `needs_source_review` video IDs.
- Search endpoint `POST /knowledge-search/multi-search` returns `tiktok:gobigsystems:7657320829214035214` for the Google Business Profile query.

## Residual note

The full-site mobile visual QA command returned non-zero only because WordPress home lacks the historical "roadmap CTA" anchor on four mobile viewports. Base2026 knowledge routes passed; this is separate from the TikTok public deploy.
