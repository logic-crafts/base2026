# Base2026 priority internal-link candidate — 2026-06-29

## Trigger

After full-sitemap Bing IndexNow submission, the next priority was to improve crawl and conversion paths rather than repeatedly resubmitting unchanged URLs.

## Audit result

A live audit of the main seed hubs and top money/resource pages found that priority Bing/Copilot/local-service pages are technically indexable and have CTAs, but each top money page had only one obvious inbound link from the checked seed hubs.

Audit file:

- `output/indexnow/base2026-priority-link-cta-audit-20260629.json`

Checked seed hubs:

- `/knowledge/`
- `/knowledge/ai-visibility-pages/`
- `/knowledge/ai-visibility-resources.html`
- `/knowledge/topics/`
- `/knowledge/creators/`
- `/knowledge/api.html`
- `/knowledge/analytics.html`

Priority pages checked:

- `/knowledge/bing-seo-for-roofing-companies/`
- `/knowledge/bing-seo-for-hvac-companies/`
- `/knowledge/bing-seo-for-law-firms/`
- `/knowledge/bing-seo-for-dentists-and-clinics/`
- `/knowledge/bing-seo-for-local-contractors/`
- `/knowledge/bing-webmaster-tools-ai-visibility-audit/`
- `/knowledge/ai-visibility-audit-for-local-service-businesses/`
- `/knowledge/ai-visibility-audit-for-bing-traffic/`
- `/knowledge/service-area-pages-and-ai-visibility-for-local-businesses/`
- `/knowledge/copilot-seo-for-service-businesses/`

## Local candidate created

Patched generator:

- `scripts/generate-ai-visibility-pages.py`

Added:

- `PRIORITY_BING_SLUGS`
- `priority_bing_cluster_section(...)`
- a visible `Priority crawl path` section on the AI Visibility Lab index
- the same cross-link section on generated AI visibility/money pages

The section links the 10 priority pages together as the first Bing/Copilot inspection and crawl path set.

## Local QA

Generated preview:

```bash
python3 scripts/generate-ai-visibility-pages.py \
  --input data/ai_visibility_pages_master.json \
  --out output/ai_visibility_priority_link_preview_20260629 \
  --indexable
```

Result:

- Generated pages: 65
- `ai-visibility-pages/index.html`: priority section present, 10 priority links, `index,follow`, one H1
- sampled money pages: priority section present, `index,follow`, one H1
- all 10 priority pages exist in preview
- 16 California city/niche drafts remained `noindex,nofollow`
- `git diff --check` passed

## Publishing status

Not deployed yet. This is a prepared local candidate only because public site edits/deploys should be explicit. Next safe step is to package/deploy through the normal Base2026 release gate only after approval.
