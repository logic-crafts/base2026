# Base2026 DataForSEO positioning receipt — 2026-08-28

Status: completed, sanitized receipt
Locale: United States (`2840`), English (`en`)
SERP device: desktop / Windows / depth 10
Total observed task cost: **`$0.077`**

No credentials, account identity, balance or private account UI were read or
stored. Free location/language/status metadata and free task recovery calls are
not included in the paid total.

## Task ledger

| Endpoint | Task ID | Cost | Purpose |
|---|---|---:|---|
| `/v3/dataforseo_labs/google/keyword_overview/live` | `08281023-1882-0607-0000-f8cd3073ed94` | `$0.015` | Compare 40 category and problem-language hypotheses |
| `/v3/serp/google/organic/live/regular` | `08281023-1882-0121-0000-1013ba58f6e9` | `$0.002` | `video intelligence platform` intent |
| same | `08281025-1882-0121-0000-be2935e89c0f` | `$0.002` | `content intelligence platform` intent |
| same | `08281025-1882-0121-0000-4a6cbe3dcfb4` | `$0.002` | `tiktok search engine` intent |
| same | `08281025-1882-0121-0000-8ea020d14bc2` | `$0.002` | `ai video search` intent |
| same | `08281025-1882-0121-0000-67e271fcaa60` | `$0.002` | `ai search visibility tools` intent |
| same | `08281026-1882-0121-0000-7279d0e3884b` | `$0.002` | `tiktok research tool` intent |
| same | `08281026-1882-0121-0000-ca19bdc7edb7` | `$0.002` | `seo knowledge base` intent |
| `/v3/dataforseo_labs/google/serp_competitors/live` | `08281026-1882-0383-0000-6be9183c0c06` | `$0.024` | Candidate domains across seven shortlisted terms |
| `/v3/dataforseo_labs/google/keyword_ideas/live` | `08281026-1882-0400-0000-0e46a05be954` | `$0.024` | Adjacent problem language and long-tail discovery |

All paid task status codes were `20000`. One free ID-list preflight initially
used a future `datetime_to` and returned `40501`; it cost `$0`, was corrected,
and did not repeat a paid request. The live SERP endpoint accepted only the
first task from the initial multi-task body; the remaining six were then sent
once each as required by the endpoint. No paid task was duplicated.

## Keyword overview

The overview returned data for 25 of 40 hypotheses. Omitted terms are unknown,
not zero demand.

| Query | US volume | Main intent | Difficulty | Decision |
|---|---:|---|---:|---|
| `ai search visibility tools` | 1,000 | commercial | 59 | Adjacent market, not the current product category |
| `ai visibility platform` | 720 | commercial | 19 | Adjacent future comparison/measurement topic |
| `ai video search` | 260 | informational | 1 | Strong discovery-language wedge |
| `tiktok search engine` | 210 | informational | 24 | Useful problem framing, SERP is mostly “TikTok as search” |
| `content intelligence platform` | 110 | commercial | 0 | Closest software shelf, but broader than Base2026 |
| `video intelligence platform` | 70 | informational | 17 | Kill as primary label because live intent is surveillance/multimodal API |
| `tiktok research tool` | 30 | informational | 55 | Academic/product-research intent; use only with precise qualification |
| `video knowledge base` | 20 | informational | 0 | Accurate language but low measured demand |
| `seo knowledge base` | 40 | informational | 13 | SERP means SEO guides/help-center optimization, not Base2026 |

## Exact SERP decisions

- `video intelligence platform`: dominated by TwelveLabs, Google Video
  Intelligence, surveillance and enterprise analytics. **KILL** as homepage
  category.
- `content intelligence platform`: content marketing analytics and enterprise
  content lifecycle products. **TEST** only as secondary category language.
- `tiktok search engine`: dominated by commentary about TikTok itself as a
  search engine plus TikTok's own search. **TEST** as problem-led content, not
  a bare product claim.
- `ai video search`: multimodal moment search and video-finder tools including
  TwelveLabs and VidNavigator. **KEEP** as a comprehensible capability, with a
  qualifier that Base2026 searches a curated public evidence corpus.
- `ai search visibility tools`: brand-monitoring platforms and comparison
  lists. **HOLD** as an adjacent topic/collection; Base2026 does not currently
  track brand mentions across LLMs.
- `tiktok research tool`: TikTok Research API, academic tools and commerce
  analytics. **TEST** only for the narrower “search expert TikTok evidence”
  job.
- `seo knowledge base`: SEO guides and knowledge-base optimization. **KILL** as
  a standalone category.

## Competitive interpretation

The SERP Competitors task returned 131 candidate domains, but almost every top
domain ranked for only one seed. This is evidence that the query set spans
several fragmented markets, not proof that Base2026 has no competitors.

Commercially relevant candidates from exact SERPs and public product checks:

- TwelveLabs — multimodal video-search API for customer-owned archives;
- VidNavigator — cross-platform transcription, extraction and video-search API;
- WalloAI — online-video content intelligence for business research;
- BlendVision — enterprise video/knowledge intelligence and governed workflows;
- Deepgrip — uploaded-video archive intelligence, clips and analytics;
- AI visibility platforms such as Semrush, Profound and SE Ranking — adjacent
  alternatives for the SEO/GEO research budget, but not direct video-evidence
  products.

Base2026's defensible distinction is the combination: an open, free-to-search,
public evidence graph for curated expert short-form video; original-source and
creator attribution; indexable source/topic/creator pages; correction and
opt-out; public-safe API/data; and a Cloudflare-native receipt-gated pipeline.
Competitors generally analyze customer uploads, sell proprietary APIs, monitor
brands, or optimize content performance.

## Route implications

1. Homepage category: **open video research engine** / **searchable expert-video
   evidence**, not generic video intelligence.
2. Lead with the user job: search what experts said without scrolling feeds or
   losing the source.
3. Create useful source-backed collections around `AI video search`, TikTok
   search limitations, AI visibility tools and content intelligence only when
   Base2026 evidence genuinely supports the page.
4. Do not target downloader, login, profile search, reverse-video search or
   general TikTok troubleshooting terms returned by broad keyword ideas; their
   intent does not match the product.
5. Reconcile future content decisions against GSC/Bing data before another
   DataForSEO expansion packet.
