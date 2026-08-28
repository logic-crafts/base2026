# Base2026 SEO/GEO growth map

**Research date:** 2026-08-28 (America/New_York)
**Scope:** fresh public-web and live-site research only; no paid DataForSEO calls, account creation, publication, sitemap submission, outreach, code change, deploy, commit, or push.
**Status:** strategy hypothesis map, not a claim of product-market fit or a launch receipt.

## Executive decision

Base2026 is best described as an **open public-source intelligence and evidence-retrieval layer for short-form expert video**, with a specific use case in SEO, GEO, AEO, AI-search research, and source-backed content work.

It is not a generic SEO suite, social-listening dashboard, video host, transcript dump, private research vault, or marketing-services funnel. The useful product unit is a source-linked, reviewed passage/insight card that a person or an agent can retrieve, inspect, cite, and trace back to the original public source.

The public competitor set researched here contains adjacent substitutes, but no active product with the same observed combination of:

- short-form expert-video source corpus;
- public, searchable source/topic/creator pages;
- reviewed evidence and attribution rather than only engagement metrics or generated answers;
- public machine-readable access (`llms.txt`, JSONL, read-only API, data dictionary); and
- open-source, rights-aware publication boundaries.

This is a positioning hypothesis, not proof that Base2026 has no competitor. Competitor claims below are limited to the job and evidence surface that each product publicly describes.

## What is live and what it proves

The following public surfaces were checked live on 2026-08-28:

| Surface | Observation | Strategic meaning |
|---|---|---|
| [Base2026 home](https://base2026.dev/) | Positions the product as public source intelligence; the page displays 1,724 source documents, 2,319 public passages, 18 creators, and 1,670 topic clusters. | The strongest category and trust message is already on the canonical entry point. |
| [Search workspace](https://base2026.dev/workspace/) | Public SEO/GEO/AEO source library with source, creator, topic, and source-backed pattern language. Its visible stat card says 1,219 sources, 1,715 passages, and 4 creators. | A material freshness/trust mismatch exists between the workspace card and the home/manifest. Treat this as a measurement and citation risk, not as evidence that search itself is broken. |
| [Public methodology](https://base2026.dev/methodology.html) | Source-first records, public reviewed text, source links, evidence cards, and explicit exclusion of raw captions/ASR/media/logs/private notes. | Provenance and rights are product features, not compliance footnotes. |
| [Public API guide](https://base2026.dev/api.html) | Read-only public records/passages/cards, static JSONL, `llms.txt`, API index, data dictionary, and route templates for source/topic/creator/compare pages. | Base2026 can distribute as a small open data product as well as a browser workspace. |
| [Public source policy](https://base2026.dev/source-policy.html) | Allows public-source attribution and review while excluding private, paywalled, leaked, minors' and other disallowed material; rejects scaled-content farms and inauthentic mentions. | Growth must compound trust and usefulness; volume or manufactured authority would damage the moat. |
| [Public manifest](https://base2026.dev/static/manifest.json) | Current export metadata reports 1,724 source records, 2,319 passages, 2,463 insight cards, 1,939 public insight cards, 1,670 topics, and 18 creators. | Use one manifest as the public count source. Do not hardcode older numbers into new pages. |
| [Public `llms.txt`](https://base2026.dev/llms.txt), [data dictionary](https://base2026.dev/data-dictionary.json), and [API index](https://base2026.dev/api-index.json) | Agent-readable orientation, schema/boundary definitions, and read-only route/data entry points are public. | This is a practical extraction and citation advantage for developers and agents, but not a Google ranking hack. |
| [Open-source repository](https://github.com/logic-crafts/base2026) | Describes an Apache-2.0, source-first public intelligence project with reviewed passages, attribution, public route/data surfaces, and private raw-data boundaries. | Builders can inspect and reproduce the architecture; the repo is also a no-budget distribution channel. |

The root and manifest numbers are current public snapshots. The workspace card is stale relative to them; the figures must not be blended into one “total.” The repository README also contains a dated 2026-08-23 snapshot (2,136 indexed documents / 1,557 distinct videos), which should remain explicitly dated if referenced.

## Category and positioning

### Category statement

> Base2026 is an open, public-source intelligence layer that turns short-form expert videos into attributed, searchable evidence for SEO, GEO, AEO, AI-search, and research workflows.

### One-line alternatives by audience

- **SEO/GEO specialist:** Find source-backed expert patterns and exact passages before writing or auditing.
- **Researcher/analyst:** Compare what multiple creators said about a topic, with dates and original links.
- **Founder/content strategist:** Turn dispersed expert conversations into a defensible brief without pretending the corpus is universal.
- **Developer/AI agent:** Retrieve public, structured records and citations through JSONL/read-only endpoints.
- **Creator/source owner:** See attribution, context, correction, and opt-out boundaries.

### Positioning guardrails

Keep “source intelligence,” “evidence,” “attribution,” “reviewed,” and “public boundary” visible. Explain that GEO/AEO work is normal helpful-search and evidence work, not a promise to force an AI system to cite anyone. Google’s own [AI features guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) says generative search uses core SEO, retrieval-augmented generation, and query fan-out; it also says there is no special AI markup or `llms.txt` requirement for Google. `llms.txt` and machine-readable files remain useful for non-Google agents and developers because they make the public contract easier to parse.

## User and buyer jobs

These are evidence-backed product hypotheses from the live role descriptions and public data contract, not validated willingness-to-pay findings. No pricing or revenue conclusion should be drawn from them.

| Role / likely buyer | Job to be done | Trigger | Desired proof/output | Product surface |
|---|---|---|---|---|
| SEO, GEO, or AEO specialist; likely first adopter | “Before I write a recommendation, show me what credible practitioners actually said and where.” | New brief, audit, or client question | Short source-backed pattern, reviewed passage, creator/date, canonical source | Workspace; topic/source pages; evidence map |
| Content strategist, founder, or in-house marketer | “Find recurring tactics and disagreements so the brief is differentiated.” | Planning a page, campaign, or editorial angle | Topic cluster, multiple creator perspectives, bounded synthesis | Topic and compare pages; source cards |
| Research/insight analyst | “Search a noisy video feed as a small evidence library.” | Need to investigate a question across many clips | Reproducible query, source list, dates, provenance, correction path | Workspace; JSONL; API; methodology |
| Developer or AI-agent builder | “Ground an answer or workflow in public records that an application can parse.” | Building a research assistant, citation workflow, or internal tool | Stable public schema, canonical URL, attribution, read-only retrieval | `llms.txt`; API index; data dictionary; JSONL/API |
| Creator or source owner; rights stakeholder | “Know how my public source is represented and correct or remove an error.” | Attribution question, correction, or opt-out | Source link, context, correction/opt-out channel | Source policy; methodology; opt-out |
| Agency or consultant | “Reduce research time while keeping the client recommendation defensible.” | Repeated client research | Exportable evidence packet with clear scope | Public API/data; topic pages; GitHub examples |

### Buyer sequence hypothesis

The first economic buyer hypothesis is a solo consultant or small SEO/content team that needs faster, defensible research and can tolerate a narrow public corpus. A developer/agent team is a second potential buyer or distribution partner. A broad enterprise social-intelligence buyer is not the initial target: its performance, sentiment, and competitive-monitoring requirements are already served by mature tools and do not match Base2026's evidence unit.

## Competitive map

“Competitor” means a product that can substitute for a specific user job, not any site that mentions SEO, AI, video, or research. “Closest” means overlap in a layer; it does not mean equivalent product scope.

| Class | Public example | What it solves | Distance from Base2026 | Boundary / implication |
|---|---|---|---|---|
| SaaS/tool | [SparkToro](https://sparktoro.com/) | Audience research across social networks, search/AI-tool usage, websites, keywords, media, and topics. | Adjacent substitute for discovery/channel intelligence. | It answers “where and who is an audience?” Base2026 answers “what did public expert sources say, with evidence?” Do not compete on audience-size breadth. |
| SaaS/tool | [Brandwatch Listen](https://www.brandwatch.com/products/listen/) | Enterprise social listening, conversation monitoring, sentiment, historical data, alerts, and many source types. | Adjacent substitute for monitoring. | Brandwatch optimizes mentions and market signals; Base2026 optimizes reviewed source retrieval and provenance. |
| SaaS/tool | [Feedly Market Intelligence](https://feedly.com/ai/models/market-intelligence) | AI-assisted collection, prioritization, trends, company/industry intelligence, and cited insight work over web/news/social sources. | Adjacent substitute for research aggregation. | Feedly is broad and enterprise-oriented; Base2026 can win on a narrow, open, creator-video evidence graph. |
| SaaS/tool | [HypeAuditor](https://hypeauditor.com/) | Influencer discovery, creator/audience metrics, engagement, fraud, campaign, and outreach intelligence. | Adjacent substitute for creator discovery. | Metrics and campaign ROI are not Base2026's evidence job. Do not add influencer scoring merely because the corpus has creators. |
| Publisher / trend intelligence | [Exploding Topics](https://explodingtopics.com/about) | Publishes and sells discovery of emerging topics, products, and categories from large-scale signals. | Indirect substitute for trend discovery. | It provides “what is growing?”; Base2026 provides “what source-backed perspectives exist?” Topic pages should show evidence and coverage, not trend certainty. |
| First-party publisher/tool | [TikTok Creative Center](https://ads.tiktok.com/help/article/creative-center?lang=en) and [Trends](https://ads.tiktok.com/resources/help/article/how-to-use-trends?lang=en) | Public trend, ad example, keyword, creative, and education views by region/industry. | Ecosystem source and discovery alternative. | It is a useful discovery reference and first-party publisher, not a public cross-creator evidence library. Do not mirror or scrape its interface. |
| Personal knowledge base | [Glasp](https://glasp.co/docs) | Video summarization, highlights, web/PDF capture, transcript-related tools, API/MCP options. | Substitute for an individual's capture/summarization workflow. | Glasp is user-owned knowledge; Base2026 is a public attributed corpus. Keep the public/provenance distinction clear. |
| Personal knowledge base | [Readwise Reader](https://readwise.io/read/) | Save and read articles, PDFs, RSS, YouTube, and other sources with notes/highlights/transcripts. | Substitute for private research capture. | Readwise optimizes personal reading; Base2026 optimizes public cross-source retrieval. Do not promise a private read-it-later product. |
| AI search / answer engine | [Perplexity](https://www.perplexity.ai/help-center/en/articles/10352895-how-does-perplexity-work) | Real-time web search and synthesized answers with citations to original sources. | Direct substitute for the “ask and cite” outcome. | It is broad, dynamic, and answer-first; Base2026 can be the cited specialist corpus that an answer engine discovers. Do not claim to replace it. |
| AI search / retrieval API | [Exa Search API](https://exa.ai/docs/reference/search) and [Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search) | Developer retrieval of web content, highlights, cleaned pages, and source-oriented results. | Infrastructure substitute / enabler. | They retrieve the open web; Base2026 maintains a bounded, reviewed source graph. API examples should show where Base2026 adds corpus value. |
| Video intelligence | [Tubular Labs](https://tubularlabs.com/products/) | Cross-platform social-video and creator discovery, measurement, categorization, audience behavior, and performance intelligence. | Closest corpus adjacency; generally enterprise/paid. | Tubular's job is performance and ROI across platforms. Base2026's job is source context, reviewed evidence, and citation. |
| Video intelligence | [Pentos](https://pentos.co/) | TikTok users, songs, hashtags, trends, competitor tracking, historical snapshots, and exports. | Adjacent TikTok trend/performance tool. | It measures what is trending; Base2026 maps what was said and how it is sourced. |
| Video intelligence | [Exolyt](https://exolyt.com/) | TikTok social listening, trends, account/video intelligence, competitor analysis, and campaign/content ideation. | Adjacent TikTok intelligence tool. | It is analytics/listening-first. Maintain a source-first evidence boundary rather than adding a dashboard clone. |
| Historical platform-specific lesson | [GummySearch pricing/closure notice](https://gummysearch.com/pricing/) | Reddit audience research and community/pain-point discovery (now closed according to its public notice). | Not an active competitor as of this research date. | Platform dependence and a single paid workflow are risks. Keep ingestion rights-aware and distribution diversified. |

### Competitive conclusion

The best comparison is not “Base2026 versus every SEO tool.” It is:

1. **Broad intelligence tools** provide scale, monitoring, audience, or performance metrics.
2. **Knowledge tools** provide private capture and summarization.
3. **AI search tools** provide broad answers and citations.
4. **Base2026** can own a narrow open layer: reviewed, attributed, source-linked expert-video evidence for SEO/GEO/AEO research.

The moat is therefore curation, provenance, public schema, and useful topic coverage. It is not raw video count, a generic AI score, or a claim of universal coverage.

## Search-intent clusters

No search-volume numbers were purchased or inferred. The clusters below are qualitative query hypotheses derived from the live product language, current topic labels, and the jobs above. Validate with Search Console and a small manual query log after the owner authorizes measurement.

| Cluster | Example query language | User intent | Best public page / artifact | Success signal | Guardrail |
|---|---|---|---|---|---|
| Find expert evidence | “find what SEO experts said in short videos”; “search TikTok expert videos”; “search video transcript by topic” | Discover whether a source library exists. | Home, workspace, one representative topic page | A visitor runs a query and opens a canonical source. | Say “public indexed corpus,” not “all TikTok” or “complete transcripts.” |
| Understand the category | “what is public-source intelligence”; “SEO GEO AEO research library”; “AI-search evidence database” | Learn what Base2026 is and whether it is credible. | Home, methodology, about, concise glossary block | Scroll/click to methodology or workspace. | Do not imply that GEO is a secret optimization discipline. |
| AI visibility and answer readiness | “AI visibility answer readiness”; “how to get cited in AI search”; “AI Overviews SEO evidence” | Learn tactics and inspect source-backed claims. | Topic pages, evidence maps, methodology | Canonical source clicks and citations to the topic page. | No guaranteed AI citations, ranking promises, or fake authority. |
| SEO implementation topics | “internal linking expert examples”; “on-page SEO evidence”; “technical SEO site architecture”; “schema SEO practitioner advice” | Apply a concrete tactic to a brief or audit. | Topic page with definition, coverage, dates, reviewed cards, source links | Topic page is useful without requiring a login. | Keep the page evidence-led; no thin keyword permutations. |
| Local/search operations | “Google Business Profile local SEO tactics”; “local SEO maintenance experts”; “answer-ready service page checklist” | Find operational patterns for a local or service business. | Existing strong topic pages and compact application notes | Repeat visits/source-page opens; no unsupported geography claim. | Separate public research from private client/agency execution; no city-page farm. |
| Compare and synthesize | “SEO expert opinions on internal linking”; “creator A versus creator B SEO”; “what do multiple experts agree on?” | Compare perspectives rather than consume one clip. | Compare/topic evidence map pages | Multiple creators and source links opened. | Only publish when coverage threshold is met; label disagreement and unknowns. |
| Freshness and monitoring | “latest SEO/GEO expert discussions”; “new TikTok SEO trends”; “what changed in AI search advice?” | Check recent evidence and changes over time. | Dated topic snapshot, changelog, release note | Repeat query log and dated source clicks. | Date every snapshot; do not market the corpus as real-time or comprehensive. |
| Developer / agent retrieval | “read-only SEO research API”; “JSONL source library for AI agents”; “MCP source evidence” | Integrate public records into a tool or agent. | API guide, API index, data dictionary, JSONL examples, GitHub | API/JSONL requests, repo forks, issue feedback. | Read-only and public-safe; future MCP is a roadmap item, not a live promise. |
| Trust, provenance, and rights | “how accurate are video transcripts”; “source attribution correction”; “remove my video from research database” | Verify representation and rights process. | Methodology, source policy, opt-out, correction flow | Rights/correction requests resolved and documented. | Never expose raw/private captions, media, QA logs, or private notes. |
| Alternative/evaluation | “Perplexity versus a source library”; “best free SEO research tool”; “open-source GEO research” | Compare workflows and decide whether to adopt. | Transparent comparison/methodology page; GitHub README | Qualified visitors reach API/workspace. | Compare jobs and evidence surfaces, not unsupported feature checklists. |

### Page construction rule

Prioritize a small set of useful topic pages rather than a page for every query. A candidate topic should meet the public data dictionary's strong-signal threshold of `source_count >= 5`, `creator_count >= 2`, and `public_insight_count >= 3`, then receive a human-readability check. Every page should state its definition, coverage, dates, source count, creator count, representative canonical links, and a short methodology/correction link.

## Free and unconventional distribution

The order below minimizes cost, account dependence, and rights risk.

### Keep and compound existing owned surfaces

- Make the home, workspace, methodology, API guide, policy, and static source/topic/creator/compare routes a coherent citation path.
- Keep `llms.txt`, `api-index.json`, `data-dictionary.json`, and public JSONL as a machine-readable contract. Describe them as agent/developer convenience, not a special Google ranking signal.
- Treat the GitHub repository as both documentation and distribution: README category statement, one reproducible public query, schema explanation, and dated release notes.
- Use short, source-linked “evidence packets” for strong topics: question, bounded answer, reviewed evidence cards, creator/date coverage, canonical sources, and method/correction links. A packet should be useful to a human who wants to cite it and to an agent that needs a stable page.

### Low-cost tests

- Publish a **small public-safe sample dataset** (metadata, reviewed short passages/cards, source URLs, topic IDs, dates, and license/boundary notes) as a versioned GitHub Release asset. Never include raw media, raw captions/ASR, private fields, credentials, logs, or unreviewed vault material.
- Add a query notebook or plain `curl` examples that reproduce a handful of topic/source lookups from the public JSONL/API. The notebook is a distribution artifact only after the sample and links pass the publication audit.
- Create a dedicated dataset landing page only if there is an actual versioned dataset to describe. Test [Google Dataset structured data](https://developers.google.com/search/docs/appearance/structured-data/dataset) with accurate visible fields; Google does not guarantee a rich result.
- Add public correction/rights issue templates in the repository. This is an unusual trust/distribution loop: source owners can improve the corpus without the product pretending to own their media.
- Publish dated manifest/changelog notes so external researchers can cite a release instead of a moving count.
- If an owner later approves one manual community post, lead with a reproducible public query or dataset example, not a generic launch announcement. One useful artifact is preferable to many promotional mentions.

### Holds requiring owner authority or a rights review

- Zenodo DOI or Hugging Face Dataset mirror: both can help discovery and versioning, but require an account, a reviewed export, a clear license, and a decision about immutability/version retention. Do not create an account or upload in this task.
- Bing Webmaster/IndexNow submission: [IndexNow](https://www.bing.com/indexnow/getstarted) can notify participating engines but does not guarantee crawl/indexing. Keep this owner-gated; no submission was made.
- Third-party launch directories, social posts, newsletters, or outreach: manual owner approval and channel-specific copy are required. No outreach was sent.
- Public open-ended AI answers: hold until answer provenance, hallucination, freshness, and abuse controls are specified. The current read-only evidence layer is safer.

### Kill/avoid

Do not create Wikipedia or other inauthentic mentions for ranking, mass-submit directories, scrape or mirror TikTok Creative Center, publish raw transcript dumps, or inflate coverage with templated city/niche pages. These tactics conflict with the public source policy and Google’s people-first guidance, and they would weaken the product’s trust boundary.

## KEEP / KILL / TEST / HOLD hypotheses

| Decision | Hypothesis | Evidence / rationale | Acceptance check |
|---|---|---|---|
| KEEP | Category language: “public-source intelligence for short-form expert-video evidence.” | Matches live home, methodology, API, about, and repository language. | A new visitor can explain the product in one sentence after the home/workspace path. |
| KEEP | Source-first trust: reviewed passage/card, original link, creator/date, correction/opt-out. | Live methodology and source policy make this the product’s distinctive contract. | Every promoted topic has source links, coverage, date, and policy/method links. |
| KEEP | Public agent surface: static JSONL, API index, data dictionary, `llms.txt`, read-only API. | Live public API page and files already expose the contract. | A developer can retrieve one record without credentials and trace it to a canonical page. |
| KEEP | Narrow high-signal topic coverage: AI visibility, SEO research/tooling, local SEO/GBP, WordPress/site SEO, internal linking, on-page/technical SEO, answer-ready service pages. | These labels and cards are visible in the current public export. | Pages meet source/creator/card threshold and have a dated, readable synthesis. |
| KILL | “GEO hacks,” guaranteed AI citations, AI ranking scores, or promises of getting named by an engine. | Google says core SEO and useful content still matter; engine output is unstable. | Remove guarantee language from page titles, metadata, and CTAs. |
| KILL | Generic SEO-suite, influencer analytics, or social-listening positioning. | Mature adjacent tools already own these jobs; they obscure Base2026’s evidence unit. | No feature or page is justified solely by similarity to a competitor. |
| KILL | Raw/full transcript marketplace or re-hosted video library. | Public policy excludes raw/private material and protects creator context. | Publication audit finds no raw captions, ASR, media, private notes, or unreviewed fields. |
| KILL | Thin query/city/niche page expansion. | The product does not have unique local evidence for arbitrary locations; scale would create a content farm. | New page requires real coverage threshold and editorial review. |
| KILL | Hardcoded or contradictory public counters. | Workspace card is stale relative to home/manifest. | One manifest hydrates all displayed public counts, or all surfaces state their snapshot date. |
| TEST | 10–15 high-signal topic evidence maps. | Existing public corpus has clustered SEO/GEO/AEO signals and cards. | Measure source clicks, repeat queries, and citation/referral observations; do not use page count alone. |
| TEST | GitHub Release with a small public-safe dataset/schema/query example. | GitHub Releases support versioned notes/assets; open-source distribution has no paid media cost. | Rights/export audit passes; an external user reproduces one lookup. |
| TEST | Dataset landing page with accurate Dataset JSON-LD. | Google documents Dataset structured data for organized collections. | Visible fields match the export; Search Console/validation records only, with no rich-result promise. |
| TEST | Dated public release/changelog and manifest diffs. | Moving counts otherwise undermine citations and comparisons. | Each release names date, scope, additions/removals, and boundary status. |
| TEST | Manual 10–20-query citation watch across Google AI features and cited answer engines. | Google recommends monitoring AI-feature performance; engines differ. | Log query, date, cited URL, page version, and confidence; no claim from one observation. |
| HOLD | Zenodo/Hugging Face mirror. | Useful discovery, but account/license/rights/immutability decisions are unresolved. | Owner approves license, export, versioning, account, and takedown process. |
| HOLD | IndexNow, sitemap resubmission, or authenticated search analytics changes. | These are external actions outside this research pass. | Owner explicitly authorizes the exact property/action and receipt is captured. |
| HOLD | Pricing, paid API, or enterprise monitoring. | Buyer willingness and usage evidence are not yet established. | Revisit after repeated public usage and a small set of validated jobs. |
| HOLD | Broad source-platform expansion. | More platforms increase extraction, rights, and consistency risk. | Add only after source-specific policy, quality, and coverage gates exist. |

## 90-day no-budget strategy

### Days 0–30: make the public evidence surface trustworthy

1. Reconcile the workspace stat card against the public manifest and home. Choose one machine-readable source of truth, render its snapshot date, and verify all public surfaces after the change.
2. Audit canonical links, redirects, titles, descriptions, robots, sitemap references, and the route family (`/workspace/`, `.html` documentation, source/topic/creator/compare templates). Do not submit anything externally in this pass.
3. Select 10–15 topics that meet the strong-signal threshold. For each, require a definition, source/creator/card counts, dates, two or more perspectives where available, three or more reviewed cards, canonical links, and a visible methodology/correction path.
4. Build a 20-query manual intent/citation baseline across find, tactic, compare, API, and trust queries. Record the page version and what evidence a visitor can reach; do not infer volume or ranking from this sample.
5. Baseline no-budget metrics: stale-counter rate, valid indexable topic/source pages, pages meeting coverage threshold, canonical source-link clicks (if already available), public API/JSONL requests (if already available), and correction response time.

### Days 31–60: turn openness into reproducible distribution

1. Prepare a public-safe, versioned sample dataset and schema/query example for a GitHub Release. Run the publication audit before release; exclude raw captions/ASR, media, private fields, logs, credentials, and unreviewed material.
2. Add a short API/JSONL quickstart with one reproducible lookup, one canonical source link, and one explanation of the public/private boundary.
3. Add or improve a dataset landing page only when a real versioned dataset exists. Test accurate Dataset JSON-LD and record validation; treat eligibility as a test, not a result guarantee.
4. Publish one dated changelog/manifest diff. Explain what changed in coverage and what did not; never silently merge incompatible counters.
5. Add rights/correction issue templates and link them from source policy and methodology.

### Days 61–90: learn demand and citations without paid acquisition

1. Run a weekly manual citation watch for 10–20 fixed queries in Google AI features and one or two cited answer engines. Log whether the citation points to a Base2026 page, an original source, or neither. Treat each observation as directional.
2. Improve only pages where the log shows a comprehension, provenance, freshness, or canonical-link problem. Keep summaries short, visible, and evidence-backed; do not generate pages for every query.
3. Publish a monthly public research/changelog note containing the query set, corpus date, coverage limits, corrections, and release links. This creates a citable artifact for people and agents.
4. If and only if the owner approves, make one manual community/developer post that demonstrates a reproducible public lookup. Do not mass-post, create accounts, or send outreach as part of this map.
5. Reassess buyer priority only after repeated usage signals: source/topic opens, repeat queries, API requests, GitHub reuse, correction quality, and direct user requests. Defer pricing and broad platform expansion until a job repeats.

### Weekly scorecard

Use a small, evidence-oriented scorecard rather than vanity traffic:

- public counters agree with the manifest (target: zero unexplained mismatch);
- number and freshness of pages meeting the coverage threshold;
- canonical source-link and evidence-card interactions, where existing measurement permits;
- reproducible public API/JSONL lookups and GitHub sample reuse;
- manual citation-watch observations with query/date/page version;
- correction/opt-out response time and unresolved rights issues;
- no public/private boundary violations or unreviewed material entering the export.

Do not report generic impressions, social followers, or a single AI citation as product-market proof. Do not use a citation-watch result to claim that Base2026 controls an external engine.

## Risks and stop conditions

| Risk | Stop condition | Safe response |
|---|---|---|
| Stale or contradictory public counts | Any page displays a materially different snapshot without date/context. | Pause new growth pages; reconcile to manifest and re-verify. |
| Rights or provenance uncertainty | A source cannot be traced to an allowed public URL or a correction/opt-out request is unresolved. | Hold the record/page; do not broaden distribution. |
| Thin coverage | Topic does not meet source/creator/card threshold or only one source supports a broad claim. | Keep unpublished/noindex or combine into a bounded index page. |
| AI citation overclaim | Copy implies guaranteed inclusion, ranking, or “optimization” by an external answer engine. | Rewrite as source-backed research and ordinary search clarity. |
| Platform extraction drift | A source platform changes access or attribution behavior. | Freeze affected ingestion/publication and mark coverage limitation. |
| Distribution pressure | A proposed channel requires an account, upload, external submit, or unsolicited message. | Hold for owner authorization and a specific rights/release plan. |

## Research receipts and source list

### Base2026 sources

- [Home](https://base2026.dev/)
- [Workspace](https://base2026.dev/workspace/)
- [Methodology](https://base2026.dev/methodology.html)
- [Roadmap](https://base2026.dev/roadmap.html)
- [API guide](https://base2026.dev/api.html)
- [About](https://base2026.dev/about.html)
- [Source policy](https://base2026.dev/source-policy.html)
- [Opt out](https://base2026.dev/opt-out.html)
- [`llms.txt`](https://base2026.dev/llms.txt)
- [Public data dictionary](https://base2026.dev/data-dictionary.json)
- [Public API index](https://base2026.dev/api-index.json)
- [Public manifest](https://base2026.dev/static/manifest.json)
- [GitHub repository](https://github.com/logic-crafts/base2026)

### Official search/distribution references

- [Google: AI features and your website](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- [Google: Dataset structured data](https://developers.google.com/search/docs/appearance/structured-data/dataset)
- [Bing: IndexNow](https://www.bing.com/indexnow/getstarted)
- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [Zenodo quickstart](https://help.zenodo.org/docs/get-started/quickstart/)
- [Hugging Face public datasets](https://huggingface.co/docs/hub/datasets-adding)

### Competitor references

- [SparkToro](https://sparktoro.com/)
- [Brandwatch Listen](https://www.brandwatch.com/products/listen/)
- [Feedly Market Intelligence](https://feedly.com/ai/models/market-intelligence)
- [Exploding Topics](https://explodingtopics.com/about)
- [TikTok Creative Center](https://ads.tiktok.com/help/article/creative-center?lang=en)
- [Tubular Labs](https://tubularlabs.com/products/)
- [Pentos](https://pentos.co/)
- [Exolyt](https://exolyt.com/)
- [HypeAuditor](https://hypeauditor.com/)
- [Glasp documentation](https://glasp.co/docs)
- [Readwise Reader](https://readwise.io/read/)
- [Perplexity: how it works](https://www.perplexity.ai/help-center/en/articles/10352895-how-does-perplexity-work)
- [Exa Search API](https://exa.ai/docs/reference/search)
- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [GummySearch closure/pricing notice](https://gummysearch.com/pricing/)

No external mutation was performed. This report is the only intended artifact from the research pass; product code, deployment state, accounts, sitemaps, outreach, and private source data were not touched.
