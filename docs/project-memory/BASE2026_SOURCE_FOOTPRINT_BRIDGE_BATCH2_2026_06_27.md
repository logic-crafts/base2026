# Base2026 Source Footprint Bridge Batch 2 — 2026-06-27

## Intent
Controlled proof-linking batch from already-indexable Base2026 topic pages into Alex Yarosh AI Visibility / Source Footprint MoneyPages.

Goal: strengthen the commercial bridge from evidence-led Base2026 topic pages to the Source Footprint / AI Visibility Audit path without mass-linking, redesigning templates, or touching noindex pages.

## Implementation
Updated `scripts/generate-public-pages.py` with a small whitelist-based `TOPIC_MONEY_BRIDGE_COPY` and `topic_money_bridge_section(topic_id)`.

The topic template now inserts the bridge after the topic evidence/Q&A section and before Top Creators, only for whitelisted topic IDs.

## Changed live Base2026 URLs
- `https://aggressorbulkit.online/knowledge/topics/ai-citation-tracking.html`
- `https://aggressorbulkit.online/knowledge/topics/ai-citations.html`
- `https://aggressorbulkit.online/knowledge/topics/ai-search-reporting.html`
- `https://aggressorbulkit.online/knowledge/topics/brand-proof-pages.html`
- `https://aggressorbulkit.online/knowledge/topics/youtube-ai-citations.html`

## Target Alex MoneyPages / service pages
- `/ai-visibility-source-footprint/`
- `/ai-visibility-audit/`
- `/ai-visibility-diagnostic-audit/`
- `/pricing/`
- `/services/`

## Release / deploy
Release name: `base2026-source-footprint-bridge-batch2-20260627`

Release gate output:
- `release_gate_ok=true`
- `deployed=base2026-source-footprint-bridge-batch2-20260627`
- live SEO crawl gate: `status=pass`
- crawled pages: `500`
- sitemap URLs: `1662`
- bad link contract count: `0`
- crawled error pages: `0`
- mobile visual QA: `results=78`, `failures=0`

## Targeted live QA
For all 5 changed URLs:
- HTTP status: `200`
- robots: `index,follow`
- canonical: self-canonical
- bridge section found: yes
- expected links found: yes

Targeted CDP mobile check at 390px:
- `docScrollWidth=390`
- `bodyScrollWidth=390`
- `overflow=false`
- offenders: `[]`
- bridgeVisible: `true`

Evidence files:
- `output/evidence/source-footprint-bridge-batch2-mobile-check.py`
- `output/evidence/source-footprint-bridge-batch2-mobile-check.json`

## IndexNow
Submitted only the 5 changed indexable URLs.

Script output:
- input URLs: `5`
- eligible URLs: `5`
- skipped URLs: `0`
- submitted: `true`
- `indexnow_status=200`

Files:
- `output/indexnow/source-footprint-bridge-batch2-urls-20260627.txt`
- `output/indexnow/source-footprint-bridge-batch2-payload-20260627.json`
- `output/indexnow/source-footprint-bridge-batch2-checks-20260627.csv`

## Next recommended step
Do not mass-link next. Next batch should be either:
1. promote 3–5 currently-relevant noindex topic pages to indexable only if public insight count/evidence threshold is met; or
2. add one Alex-side hub section that explains the Base2026 evidence trail and links back to the 5 strongest topic pages, preserving the existing visual template.
