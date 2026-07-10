# Base2026 local evidence gate for city/niche pages — 2026-06-26

Purpose: prevent Base2026 city/niche pSEO pages from becoming thin doorway pages while still allowing aggressive expansion when evidence exists.

## Definition

A city/niche page has **unique local evidence** when it contains specific proof, observations, or data that would stop being true/useful if the city or niche were swapped for another one.

Bad page: same template with only `{city}` + `{niche}` replaced.

Good page: proof-based local intelligence page with source-backed local or niche-specific observations.

## Minimum indexation gate

A city/niche page may be switched from `noindex` to `index` only when it has:

1. unique city/niche intro and title, not just variable substitution;
2. at least 2 local/niche evidence points;
3. at least 1 linked source/evidence page;
4. at least 1 actionable block: what this business type should fix;
5. self-canonical URL;
6. no query/filter crawl state;
7. internal link from a hub/topic page;
8. no near-duplicate conflict with another city/niche page;
9. clear CTA path to Alex/Base2026 MoneyPage where relevant.

## Evidence types that count

- Local SERP / local pack / GBP observation.
- Review/sentiment pattern for that city/niche.
- TikTok/source/video signal tied to the business problem.
- Query pattern specific to the city/niche.
- Competitor gap analysis: missing FAQ, schema, service page, proof, reviews, before/after, or AI-answer readiness.
- Local regulation/event/seasonality/market condition if relevant.
- First-party mini-audit output generated for that exact page.

## Evidence types that do not count

- Generic SEO advice repeated across cities.
- AI-written intro with city/niche names swapped.
- Same FAQ copied across every city.
- Unsourced claims like “many businesses in Austin struggle with AI visibility”.
- Directory/list pages with no analysis.

## Operating rule

Default state for city/niche pages: `noindex`.

Promotion state: `index` only after the local evidence gate passes and the URL is added to the controlled indexation ledger.

## Batch scaling

- Batch 0: source/proof/topic pages.
- Batch 1: 25–50 highest-evidence city/niche pages.
- Batch 2: 50–100 more only after indexation/engagement signals are healthy.
- Do not jump to hundreds/thousands of leaf pages without GSC/Bing evidence.
