# GSC-Ready Traffic Action Set - 2026-06-24

Status: deploy-ready after the Base2026 to Alex traffic architecture source pass.

## Basis

- Latest local GSC snapshot available in project memory: last 3 months `0` clicks, `110` impressions, average position `27.8`; Pages overview `29` indexed, `814` not indexed.
- No fresh exported GSC query/page CSV was available locally in this pass.
- Existing priority file used as a seed: `docs/project-memory/BASE2026_PRIORITY_INDEXATION_URLS_2026_06_23.csv`.
- This set intentionally excludes Reddit, YouTube-plan, and Google Business Profile-for-Base2026 actions. Base2026 remains a public research/proof layer, not a local business.
- Do not automate GSC request-indexing clicks. Submit manually only after deployment and live HTTP checks pass.

## Priority URL Set

### Alex Conversion Layer

1. `https://aggressorbulkit.online/ai-visibility-audit/`
2. `https://aggressorbulkit.online/ai-visibility-diagnostic-audit/`
3. `https://aggressorbulkit.online/technical-seo-geo-foundation/`
4. `https://aggressorbulkit.online/answer-ready-service-pages/`
5. `https://aggressorbulkit.online/entity-trust-source-intelligence/`
6. `https://aggressorbulkit.online/services/`
7. `https://aggressorbulkit.online/pricing/`

### Base2026 Proof Layer

1. `https://aggressorbulkit.online/knowledge/`
2. `https://aggressorbulkit.online/knowledge/apply-research.html`
3. `https://aggressorbulkit.online/knowledge/api.html`
4. `https://aggressorbulkit.online/knowledge/methodology.html`
5. `https://aggressorbulkit.online/knowledge/analytics.html`
6. `https://aggressorbulkit.online/knowledge/topics/`
7. `https://aggressorbulkit.online/knowledge/creators/`

### Base2026 Compatible Topic Proof Pages

Use these only after the hubs above are confirmed live and indexable:

1. `https://aggressorbulkit.online/knowledge/topics/ai-citations.html`
2. `https://aggressorbulkit.online/knowledge/topics/ai-citation-tracking.html`
3. `https://aggressorbulkit.online/knowledge/topics/answer-first-content.html`
4. `https://aggressorbulkit.online/knowledge/topics/brand-proof-pages.html`
5. `https://aggressorbulkit.online/knowledge/topics/content-freshness.html`
6. `https://aggressorbulkit.online/knowledge/topics/ai-knowledge-base.html`
7. `https://aggressorbulkit.online/knowledge/topics/schema-ai-citations.html`
8. `https://aggressorbulkit.online/knowledge/topics/search-console-low-hanging-fruit.html`
9. `https://aggressorbulkit.online/knowledge/topics/internal-linking.html`
10. `https://aggressorbulkit.online/knowledge/topics/risk-avoid-scaled-content-abuse.html`

## Manual GSC Sequence

1. After deploy, fetch each conversion-layer URL and `https://aggressorbulkit.online/knowledge/apply-research.html` with HTTP `200`, self-canonical or expected canonical, and no `noindex`.
2. In GSC, inspect the seven Alex conversion URLs first because they are the money/service layer.
3. Inspect the Base2026 proof hubs next, especially `/knowledge/apply-research.html`, `/knowledge/`, `/knowledge/api.html`, and `/knowledge/methodology.html`.
4. Only then inspect selected compatible topic pages that reinforce AI visibility, answer-ready pages, source intelligence, internal linking, and content freshness.
5. Record outcomes in `PROMPT_LOG.md` or a dated GSC follow-up doc. Do not click request indexing repeatedly after quota/error states.

## Post-Deploy Validation

Required before manual GSC submission:

- Base2026 release package contains `web/apply-research.html`.
- `web/sitemap.xml` includes the new Base2026 page.
- Alex generated import contains the four new money pages with `status=publish`.
- Alex footer/nav/content links to Base2026 proof pages.
- Base2026 search/info/topic pages link toward `/ai-visibility-audit/` and `/knowledge/apply-research.html`.
