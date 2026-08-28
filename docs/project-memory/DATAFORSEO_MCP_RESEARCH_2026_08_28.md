# DataForSEO MCP research — 2026-08-28

Status: methodology researched and first positioning packet executed.

- Documentation snapshot fetched: 2026-08-28 (UTC).
- Paid calls made: `10` decision-scoped tasks.
- Observed paid cost: `$0.077` total.
- Credentials, account identity, balance, cookies, and raw private responses were not accessed or recorded.

This memo is a publication-safe operating reference for Base2026 SEO/GEO research. It is based on the connected DataForSEO MCP documentation, not on a live account balance or a paid result. Current prices must be checked immediately before any future request; the documentation pages generally describe relative pricing and link to the live pricing pages rather than exposing a stable base price.

## Operating rule

Treat DataForSEO as dated, decision-scoped evidence. Start with existing GSC/GA4/local evidence and cached receipts; define one decision and a stop condition; use the smallest batch that can resolve it; retain a sanitized receipt and an interpretation memo; then label the hypothesis `KEEP`, `KILL`, `TEST`, `HOLD`, or `UNKNOWN`. A positive volume, CPC, ranking, impression, indexation, or tool score is not proof of demand, intent, commercial fit, success, or future traffic.

Do not publish a page, alter routes, change Cloudflare, or infer a local service area from a query as a consequence of this research. The output of a paid call, if later approved, is evidence for a reviewed decision—not publication authorization.

## Endpoint families and useful roles

The links below are the official documentation pages consulted. Paths are shown as documentation/API families, not as executed requests.

| Family | Exact useful endpoints | Best use and cost posture |
| --- | --- | --- |
| Free SERP metadata | [Google Organic locations](https://docs.dataforseo.com/v3/serp/google/locations.md), [languages](https://docs.dataforseo.com/v3/serp/google/languages.md) | Resolve stable location/language codes before paid work. Free; use codes and record the returned name. |
| Google Organic SERP | [overview](https://docs.dataforseo.com/v3/serp/google/organic/overview.md), `POST /v3/serp/google/organic/live/regular`, `POST /v3/serp/google/organic/live/advanced`, [Regular Live](https://docs.dataforseo.com/v3/serp/google/organic/live/regular.md), [Advanced Live](https://docs.dataforseo.com/v3/serp/google/organic/live/advanced.md), [Standard task post](https://docs.dataforseo.com/v3/serp/google/organic/task_post.md) | `regular` is the smallest exact organic/paid validation. Use `advanced` only when complete SERP features, AI Overview, PAA, or feature positions matter. Standard task posting is normally cheaper when latency permits; Live is immediate and generally highest cost. |
| Local SERP | Google [Maps](https://docs.dataforseo.com/v3/serp/google/maps/overview.md) and [Local Finder](https://docs.dataforseo.com/v3/serp/google/local_finder/overview.md) families | Use only for a local decision. Keep map/local-pack evidence separate from organic rankings; provider service-area evidence remains the source for a location claim. |
| SERP lifecycle and free status | [SERP overview](https://docs.dataforseo.com/v3/serp/overview.md), [tasks ready](https://docs.dataforseo.com/v3/serp/google/organic/tasks_ready.md), [task get](https://docs.dataforseo.com/v3/serp/google/organic/task_get/regular.md) | Standard flow is task post → callback, or free `tasks_ready` → `task_get`. Only posting a Standard task is charged; the documented GET is free within its retention window. |
| Labs intent | [Search Intent Live](https://docs.dataforseo.com/v3/dataforseo_labs/google/search_intent/live.md) | Compact intent classification (`informational`, `navigational`, `commercial`, `transactional`) for up to 1,000 keywords per task. Requires location and language; no device field. A good first lane when the decision is intent, not traffic. |
| Labs keyword metrics | [Keyword Overview Live](https://docs.dataforseo.com/v3/dataforseo_labs/google/keyword_overview/live.md), [Bulk Keyword Difficulty Live](https://docs.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_difficulty/live.md) | Overview combines search volume, CPC, trends, difficulty, SERP metadata, and intent (up to 700 keywords); difficulty accepts up to 1,000. Omit stored SERP inclusion and clickstream in a budget packet; clickstream doubles the documented request price. Use difficulty after intent/shortlisting. |
| Labs discovery | [Keyword Suggestions](https://docs.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live.md), [Keyword Ideas](https://docs.dataforseo.com/v3/dataforseo_labs/google/keyword_ideas/live.md), [Keywords for Site](https://docs.dataforseo.com/v3/dataforseo_labs/google/keywords_for_site/live.md), [Related Keywords](https://docs.dataforseo.com/v3/dataforseo_labs/google/related_keywords/live.md) | One seed for Suggestions; up to 200 seeds for Ideas; a domain/page for Keywords for Site; related-term expansion when a specific decision needs it. Do not request `include_clickstream_data` or stored SERPs in the first packet. Discovery is a candidate list, not proof of commercial fit. |
| Labs competitor candidates | [SERP Competitors](https://docs.dataforseo.com/v3/dataforseo_labs/google/serp_competitors/live.md), [Domain Intersection](https://docs.dataforseo.com/v3/dataforseo_labs/google/domain_intersection/live.md), [Ranked Keywords](https://docs.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live.md) | SERP Competitors can batch up to 200 keywords and returns candidate domains/visibility. Intersection and Ranked Keywords are late-stage named-domain checks. An empty result is `UNKNOWN`, not “there are no competitors.” |
| Google Ads keyword data | [Google Ads overview](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview.md), [Search Volume Live](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live.md), [Keywords for Keywords Live](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live.md), [Keywords for Site Live](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live.md) | Search Volume accepts up to 1,000 keywords per request at the same per-request charge, regardless of whether the list contains one or 1,000. Keywords for Keywords accepts up to 20 inputs and can return up to 20,000 suggestions. Standard is normally more affordable when real-time data is unnecessary. Google Ads Live is rate-limited to 12 requests/minute. |
| Google Ads freshness and geography | [status](https://docs.dataforseo.com/v3/keywords_data/google_ads/status.md), [locations](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations.md), [languages](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages.md) | Free preflight. Check the reported update month/date before comparing periods; do not treat missing data as zero. Google Ads supports finer location targeting than Labs. |
| AI keyword demand | [AI Keyword Data overview](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/overview.md), [AI Search Volume Live](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live.md), [locations/languages](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages.md) | Up to 1,000 keywords, location/language required, no device field. Use after ordinary search intent when the decision concerns AI-search question demand; it is not a replacement for an exact Google SERP. |
| GEO visibility | [LLM Mentions overview](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/overview.md), [Target Metrics Lite](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/target_metrics_lite/live.md), [Search Mentions](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/search_mentions/live.md), [Top Mentioned Domains Lite](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_mentioned_domains_lite/live.md) | Target Metrics Lite is the compact benchmark for up to 10 target entities, with one included target required. Use Search Mentions only when source-level citations are the decision; use Top Mentioned Domains for a citation landscape, not as a backlink or commercial-competitor list. ChatGPT data is constrained to US English; Google and ChatGPT are separate platforms. |
| Free Labs/AI freshness | [Labs status](https://docs.dataforseo.com/v3/dataforseo_labs/status.md), [Labs locations/languages](https://docs.dataforseo.com/v3/dataforseo_labs/locations_and_languages.md), [AI locations/languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages.md) | Check data update dates and supported country/language combinations before interpretation. Russia and Belarus are documented as unsupported in relevant location lists. |
| Free recovery/metadata | [API status](https://docs.dataforseo.com/v3/appendix/status.md), [ID list](https://docs.dataforseo.com/v3/appendix/id_list.md), [API errors](https://docs.dataforseo.com/v3/appendix/api_errors.md), [Sandbox](https://docs.dataforseo.com/v3/appendix/sandbox.md) | Status and ID/error metadata are free and useful for reconciliation. Sandbox validates schema/rate behavior, not market evidence. Do not use account or balance endpoints for this methodology packet. |

The [DataForSEO API overview](https://docs.dataforseo.com/v3/ai_optimization/overview.md) confirms the Standard/Live distinction across families. LLM Responses and LLM Scraper are intentionally excluded from the first packet: generated responses add variance and are only justified by a separately approved prompt-level decision.

## Recommended Base2026 sequence

1. **Local evidence and decision.** Read existing GSC/GA4, approved local/service-area source material, prior sanitized receipts, and the exact Base2026 route or page under consideration. Deduplicate terms. Write the decision and a falsifiable stop condition first.

2. **Free preflight.** Resolve location and language codes; check Labs and Google Ads freshness; check API status. Fix one locale per task. Do not mix “worldwide,” a country, and a city in the same conclusion.

3. **Choose one data lane.** For a first paid packet, choose exactly one of intent, metrics, exact SERP, or GEO visibility. Batch terms/entities inside that one task where supported. Avoid clickstream, stored SERP inclusion, rectangles, AI Overview loading, PAA click depth, operators, and high priority unless the decision specifically requires one.

4. **Inspect and interpret.** Save the full sanitized task response, cost, status, locale, and observed result types. Treat null/missing values as `UNKNOWN`. Join any useful finding to an existing exact route before proposing new content.

5. **Escalate only for an unresolved decision.** Validate one ambiguous high-value query with Google Organic `live/regular`. Use `advanced` only for complete feature/AI Overview/PAA classification. Use Labs SERP Competitors after exact SERP candidates have been classified; use Domain Intersection or Ranked Keywords only for a named domain decision.

6. **GEO follow-up.** Once an entity/page benchmark is justified, use Target Metrics Lite; escalate to Search Mentions for source-level citation inventory. Keep AI Overview references and LLM sources separate from normal organic rank evidence.

7. **Close the loop.** Record the decision, limitations, and next action. No page generation, route mutation, publication, deploy, or Cloudflare action follows automatically.

## Cost and batching guardrails

The documentation snapshot does not expose stable base prices for all families. Therefore “cheapest” means the following operational ordering, not a promised dollar estimate:

- Free locations/languages/status/tasks-ready/metadata first.
- One batch instead of repeated single-keyword calls when the endpoint charges per request. Google Ads Search Volume accepts up to 1,000 terms at the same per-request charge; Labs Search Intent accepts up to 1,000; Labs Overview up to 700; AI Keyword Search Volume up to 1,000; LLM Mentions Lite up to 10 entities.
- For exact SERP, one Google Organic Live Regular task per call, `depth=10`, no operators or optional feature loaders. Standard task posting is the cheaper asynchronous choice when latency is acceptable; a Standard POST can hold up to 100 tasks, but the first packet uses only one.
- Labs Live supports one task per request, up to 2,000 calls/minute and 30 concurrent tasks. SERP Standard supports up to 100 tasks per POST and documented aggregate POST/GET rate limits. Google Ads Live is documented at 12 requests/minute.
- Do not add clickstream in a budget packet: the relevant Labs/Google Ads pages document that it doubles the request price. Do not add SERP rectangles or PAA clicks unless their feature is the decision.
- Documented SERP add-ons in the fetched pages include Standard asynchronous AI Overview `$0.0006`, Advanced asynchronous AI Overview `$0.002`, PAA click depth `$0.00015` per click, and rectangles `$0.002`; verify the current price page before use.
- Use the actual returned task cost for reconciliation. Do not infer a current price from a prior run, a memory note, a balance, or a similarly named endpoint.

## Locations, languages, and devices

- Call the free location/language directory first and prefer `location_code`/`language_code` over ambiguous names. Record the requested and returned code/name, country, and data freshness.
- Labs Google uses country-level locations and requires location plus language on the principal live endpoints. Google Ads can use more granular geographical targets. SERP can use a city/location/coordinate, but only one location selector may be used per task.
- SERP tasks default to desktop and support desktop/mobile plus the corresponding OS. Use mobile only when a device-specific decision can change the conclusion; record device and OS. The Google News, Events, Images, Search By Image, and Jobs families are documented as desktop-only.
- AI Keyword Data and LLM Mentions do not have a device dimension. LLM Mentions must record platform; ChatGPT is documented as US English only, while Google and ChatGPT outputs must not be merged as if they were the same SERP.
- A locale-specific keyword result does not prove that a provider serves that geography. For local claims, use direct provider service-area evidence and state the exact CMS/publication boundary.

## Receipt contract

Every future paid task must produce a sanitized receipt with at least:

```text
receipt_id / human tag
endpoint family and exact path / method
task id (if returned)
normalized keywords, domain, URL, or target entities
location code and name / country; language code and name
device and OS (SERP only; otherwise device: not_applicable)
depth, priority, and every optional include_* or feature flag
requested_at and observed_at in UTC
task status code/message; top-level and task-level cost as applicable
result counts, item types/features, rank fields, and check_url (SERP)
freshness/status source and whether the result was null or omitted
interpretation, limitations, decision, and next action
```

Reconcile the sum of task-level costs without double-counting a top-level aggregate. Preserve the full response for the receipt; the documentation says an `.ai`-cropped GET omits cost/time and other empty or positional fields. If the MCP wrapper exposes an AI-cropped response mode, obtain the full/no-AI response for the cost receipt before using a condensed view for reading. No credentials or account metadata belong in the receipt.

## SERP and competitor classification

For an exact query, retain query, UTC timestamp, country/location, language, device/OS, depth, check URL, item types, and the complete feature inventory. Record both `rank_group` (position inside an item type) and `rank_absolute` when present; do not compare an organic group position to an AI Overview reference or a local-pack position as if they were one ranking.

Use Google Organic `regular` for the inexpensive organic/paid check. It does not provide a complete feature inventory. Use `advanced` when the question is specifically about AI Overview, PAA, local pack, knowledge graph, video, shopping, or another feature; retain AI Overview text/links/references separately. A featured snippet, local pack, map result, paid result, People Also Ask block, video, and organic result are different evidence types.

For competitors:

1. Run the exact decision query (or use an already valid exact receipt) and collect the visible top domains/pages.
2. Classify each page from its title, URL, description, and visible offer as `consultant`, `agency`, `editorial publisher`, `SaaS/tool`, `marketplace`, `directory`, or `unrelated`.
3. Call a domain a commercial competitor only after buyer job and offer overlap are verified. Domain similarity alone is not evidence.
4. Use Labs SERP Competitors as candidate discovery, not proof. Use Domain Intersection only after a named domain pair and a stated overlap decision. Empty/partial data remains `UNKNOWN`.
5. Treat Top Mentioned Domains and LLM source domains as a GEO citation landscape. They are not automatically commercial competitors, backlink prospects, or publication targets. Backlink research requires a separate approved packet.

## First positioning packet — executed 2026-08-28

The owner explicitly replaced the artificial fixed-cost ceiling with a quality
rule: use DataForSEO where it can change a real product or visibility decision,
batch efficiently, record the exact cost, and stop when the decision is clear.
This does not authorize an open-ended keyword dump. Every future packet still
needs a named question, bounded endpoints/calls, locale, stop condition and
actual-cost receipt.

Executed locale: United States (`2840`), English (`en`); exact SERPs used
desktop/Windows and depth 10. Clickstream, stored SERP data, rectangles, PAA
clicks and other paid add-ons remained disabled.

| Task | Calls | Cost | Receipt |
|---|---:|---:|---|
| Keyword Overview, 40 category hypotheses | 1 | `$0.015` | `08281023-1882-0607-0000-f8cd3073ed94` |
| Google Organic Live Regular, 7 exact intent checks | 7 | `$0.014` | task IDs listed in `DATAFORSEO_POSITIONING_RECEIPT_2026_08_28.md` |
| SERP Competitors, 7 shortlisted terms | 1 | `$0.024` | `08281026-1882-0383-0000-6be9183c0c06` |
| Keyword Ideas, five seeds and 100 returned rows | 1 | `$0.024` | `08281026-1882-0400-0000-0e46a05be954` |
| **Total** | **10** | **`$0.077`** | all task statuses `20000` |

The packet resolved the category decision. `video intelligence platform` is a
poor primary label because its live SERP is dominated by multimodal APIs,
surveillance and enterprise video analytics. `AI search visibility tools` has
real commercial demand but describes monitoring products rather than the
current Base2026 offer. The closest discoverable wedge is a combination of
`AI video search`, `TikTok search`, `content intelligence`, and source-backed
SEO/GEO research—not any one of those broad categories alone.

Useful returned demand signals and false-intent details are recorded in
`DATAFORSEO_POSITIONING_RECEIPT_2026_08_28.md`. The next paid packet should run
only after GSC/Bing expose actual queries or a named content decision remains
unresolved; it should not repeat this category packet.

## Continuing boundary

DataForSEO evidence does not directly authorize publication, redirects,
canonicals, Cloudflare mutation, outreach or ranking claims. Account lookup,
credentials and balance remain outside the research record. Product and copy
changes require repository evidence, live checks and the normal release gate.
