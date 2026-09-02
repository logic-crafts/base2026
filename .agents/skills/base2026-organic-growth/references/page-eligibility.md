# Base2026 page eligibility

This reference contains the Base2026-specific decisions that generic SEO guidance does not know.

## Use an evidence verdict, not a vanity score

Record the page type, public evidence counts, intent, unique utility, technical checks, hard vetoes, and proof links. For a topic/evidence map, the project's strong-evidence threshold is:

```json
{
  "page_type": "topic_map",
  "evidence_score": 3,
  "source_count": 6,
  "creator_count": 3,
  "public_insight_count": 4,
  "hard_vetoes": [],
  "status": "indexable"
}
```

`evidence_score` is only the count of satisfied threshold checks: `source_count >= 5`, `creator_count >= 2`, and `public_insight_count >= 3`. It is not sufficient by itself. A hard veto or failed technical gate wins. Re-read current counts from the live/public source of truth; never copy a dated snapshot into a page.

## Page-type decisions

- **Topic/evidence map:** require the strong-evidence threshold, a clear definition and search intent, coverage/date context, representative canonical source links, reviewed public insights, a short method/correction path, and useful synthesis. Fewer than two public insights means `noindex,follow` and exclusion from topic indexes; do not manufacture a map from a title or corpus count.
- **Public source/detail page:** require a reviewed public source URL/ID and public intelligence or topic context. Source text alone is a noindex quarantine, not an indexable landing page or topic-index entry. Use the generator/release path that preserves provenance.
- **Editorial/guide:** one bounded intent, original or first-party utility, visible supporting sources, and no raw transcript masquerading as analysis. Do not promise coverage, rankings, or guarantees the evidence cannot support.
- **Free tool/API/dataset:** the public route and promised core action must work with real public data, have a clear input/output and reproducible result, and remain useful without an unnecessary lead gate. A stub, roadmap, private/auth-only route, or broken endpoint is noindex/hold. Dataset JSON-LD requires an actual versioned public dataset; it is not a rich-result promise.
- **City/niche/local page:** hold or use `noindex,follow` until there is unique local evidence, source links, and actionable local utility. Do not create a templated page farm.

## Indexable gate

All of these must be true before an indexable status is recorded:

- public provenance and source links support the visible claims;
- the page answers a real, bounded intent with unique utility;
- final live response is `200`, self-canonical, crawlable, and not `noindex`;
- title, description, H1, body, and schema agree with the actual page;
- the page is reachable from a relevant hub or related page and is not orphaned;
- only indexable self-canonical HTML is included in the generated sitemap;
- no privacy, rights, unsupported modifier, contradictory-counter, thin-page, or generated-fallback veto remains.

If any check is unknown, record `hold` rather than infer success. Keep `draft`, `generated`, `deployed`, and `live` distinct from `indexable`.

## Modifier truth table

- `free`: the promised core action is available without payment, a hidden key, or a “free” trial that does not deliver the claim.
- `best`/`top`: use only for a bounded, dated comparison with named criteria and a defined set; prefer descriptive wording when no comparison exists.
- `confirmed`/`verified`: name the fact checked, receipt, account/surface, and date. Do not convert a submission or HTTP 200 into verification.
- `examples`, `template`, `checker`, `search`, `API`, `MCP`, `plugin`: the visible route, artifact, or integration must exist and work. A planned capability is not live.
- `latest`: attach a date or snapshot scope; do not imply real-time freshness.

## Free-tool and technical checks

Before promoting a tool page, verify the live route, real public input, deterministic or explainable output, mobile layout, keyboard/accessibility basics, no private-data leakage, and a measurable success event/readback. Keep the tool focused on one adjacent job and do not duplicate the main workspace merely to create a keyword page.

Use the project generators and tests as authority. Current Base2026 routes are generally extensionless, but resolve the final live URL rather than assuming a path. Internal links should connect the home/workspace, topic/source hubs, related evidence, method, correction, and API/data-contract surfaces with descriptive anchors; never create orphan pages or keyword-stuffed anchor variants.

Use `scripts/generate-base2026-sitemap.py` and inspect its child sitemaps. Include only live, indexable, self-canonical HTML. Do not resubmit unchanged URLs. Schema must describe visible content: use applicable WebPage, Article, Dataset, or Breadcrumb markup; do not add generic FAQPage, Product, Review, or unsupported ranking markup as a shortcut.
