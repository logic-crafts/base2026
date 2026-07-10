# Base2026 Demand Traffic Batch 1 — 2026-06-27

## Intent
Move from defensive proof-linking to demand-led traffic pages. This batch upgrades 10 already-indexable Base2026 topic pages into traffic-capture pages with explicit query intent, answer-first sections, FAQ/FAQPage schema, source proof cards and commercial CTAs into Alex Yarosh AI Visibility / Source Footprint offers.

## Deployed release
- Release: `base2026-demand-traffic-batch1-20260627`
- Live base: `https://aggressorbulkit.online/knowledge/`
- Release gate: `release_gate_ok=true`

## Updated generator/config
- `scripts/generate-public-pages.py`
  - Loads `data/base2026_topic_traffic_pages.json`.
  - Applies SEO title/meta overrides per topic.
  - Renders answer capsule, source proof cards, FAQ section, FAQPage JSON-LD and topic-specific CTA.
  - Resolves proof source IDs by `source_id`, `item_id`, or slugged `item_id`.
- `data/base2026_topic_traffic_pages.json`
  - Human-authored public demand config for this first batch.
- `web/static/styles.css`
  - Added topic traffic-page styles only; preserved current visual system.
- `scripts/audit-publication-boundary.py`
  - Added `data/base2026_topic_traffic_pages.json` to public-safe exact allowlist.

## Upgraded live URLs
1. https://aggressorbulkit.online/knowledge/topics/ai-citation-tracking.html
2. https://aggressorbulkit.online/knowledge/topics/ai-citations.html
3. https://aggressorbulkit.online/knowledge/topics/ai-search-reporting.html
4. https://aggressorbulkit.online/knowledge/topics/chatgpt-query-research.html
5. https://aggressorbulkit.online/knowledge/topics/local-seo-google-business-profile.html
6. https://aggressorbulkit.online/knowledge/topics/google-business-profile.html
7. https://aggressorbulkit.online/knowledge/topics/google-search-console-ai-visibility-reporting.html
8. https://aggressorbulkit.online/knowledge/topics/brand-proof-pages.html
9. https://aggressorbulkit.online/knowledge/topics/answer-first-content.html
10. https://aggressorbulkit.online/knowledge/topics/schema-ai-citations.html

## Live QA
Release gate output:
- Public content readiness: ok
- Publication boundary: ok
- GitHub metadata: ok
- Public export policy: ok
- Public release contract: ok
- Deployed/reindexed on VPS: ok
- Live SEO crawl gate: `status=pass`, `crawled_pages=500`, `sitemap_urls=1662`, `bad_link_contract_count=0`, `crawled_error_pages=0`
- Mobile visual QA: `results=78`, `failures=0`

Targeted live QA evidence:
- File: `output/evidence/base2026-demand-traffic-batch1-live-targeted-qa.json`
- For all 10 URLs:
  - HTTP `200`
  - robots `index,follow`
  - self-canonical correct
  - meta description present
  - answer capsule present
  - 3 FAQ items
  - FAQPage JSON-LD present
  - source proof cards present
  - commercial CTA present

## IndexNow
- URL set: `output/indexnow/demand-traffic-batch1-urls-20260627.txt`
- Payload: `output/indexnow/demand-traffic-batch1-payload-20260627.json`
- Eligible: `10/10`
- Skipped: `0`
- Submit status: `indexnow_status=200`

## GSC manual inspection set
- File: `output/indexnow/demand-traffic-batch1-gsc-inspection-set-20260627.txt`
- In GSC:
  1. Ensure `https://aggressorbulkit.online/knowledge/sitemap.xml` is submitted as a sitemap.
  2. Inspect the 10 upgraded URLs.
  3. Request indexing where available.
  4. Recheck in 48–72 hours: discovered/indexed/impressions/queries.

## Outbound parallel batch
- Draft file: `/Users/alexyarosh/Projects/ai-agency-obsidian-command-center/data/base2026_ai_visibility_mini_audit_batch_20260627.csv`
- Source: existing `tiktok_local_business_leads.csv`.
- Count: 10 prospects.
- Status: `draft_not_sent`; no outreach sent.

## Next production step
Do not wait for Google to reward this passively. Next step should run in parallel:
1. GSC: submit/inspect this exact set.
2. Create 3–5 one-page mini-audit drafts from the outbound batch.
3. Prepare Batch 2 with 10 more demand pages, but only where public evidence supports source proof + clear lead intent.
