# Base2026 / Alex zero-traffic command-center audit — 2026-07-01

Minsk time: 2026-07-01 18:37 +03

## Question

Alex asked why Base2026 + Alex commercial site still have near-zero traffic/leads while lower-quality automated content/blog projects can receive some organic traffic, and whether the issue is strategy, execution, or impatience.

## Short answer

The current state is not primarily a technical SEO failure. The site is crawlable, sitemaps are live, IndexNow has been used, and key pages return indexable canonical HTML.

The mismatch is strategic:

- Base2026 has a large proof/source layer, but proof pages are not the same as demand-capture pages.
- The market is moving toward instant `AI visibility checker / audit / score / competitor` offers, while our public funnel still reads partly like expert/service copy and a source library.
- We have created many SEO/indexation assets very recently; Google discovery/indexing lag is expected.
- Leads will not appear from SEO alone this fast. The acquisition loop needs a direct snapshot/outbound/vertical landing-page motion in parallel.

## Verified facts

### Hermes/model setup

- Default model confirmed/reset to `openai-codex` + `gpt-5.5`.
- `agent.reasoning_effort` confirmed/reset to `xhigh`.
- Current gateway session may still need a restart/new session for config-only changes to fully apply everywhere.

### Live crawl / sitemap facts

- `https://aggressorbulkit.online/robots.txt` returns 200 and lists both:
  - `https://aggressorbulkit.online/sitemap.xml`
  - `https://aggressorbulkit.online/knowledge/sitemap.xml`
- Main sitemap: 15 URLs.
- Base2026 sitemap index: 5 child sitemaps / 1,703 URLs.
- Base2026 URL family mix:
  - sources: 1,544
  - topics: 40
  - compare: 40
  - creators: 17
  - other hubs/info/money/resource pages: 62

### Existing growth/indexation work already done

From project-memory/evidence:

- 30 demand-led topic pages live from batches 1–3.
- AI Visibility Resource Hub live and linked.
- Money-page template deployed in Alex/Base2026 style.
- Priority crawl path deployed for 11 high-value pages.
- Bing full sitemap IndexNow submission: 1,703 live-gated eligible URLs, HTTP 200.
- Money/template IndexNow: 48 changed URLs, HTTP 200.
- Priority crawl path IndexNow: 11 URLs, HTTP 202.
- GSC post-hub recheck from 2026-06-28 showed 7/31 indexed and 24 not on Google — this is a discovery/indexing maturity issue, not proof of a broken site.

### Live commercial page facts

Core pages return 200, self-canonical, index/follow, one H1:

- `/` — title: `Free AI Visibility Snapshot | SEO, GEO & AEO`
- `/services/` — title: `SEO, GEO & AEO Services for AI Search Visibility`
- `/ai-visibility-audit/` — title: `Free AI Visibility Snapshot | AI Search Check`
- `/pricing/` — title: `AI Search Visibility Pricing | SEO, GEO & AEO Packages`
- `/knowledge/` — title: `Base2026 SEO, GEO & AEO Source Library`
- `/knowledge/ai-visibility-pages/` — title: `AI Visibility Lab | Base2026`

### Live issues found

- `www.aggressorbulkit.online` returns 200 instead of 301 redirecting to apex. Canonical points to apex, but host canonicalization should still be fixed.
- `/knowledge` without trailing slash returns 404 instead of 301 to `/knowledge/`.
- `/thank-you-ai-visibility-audit/` is in the main sitemap and appears indexable; likely should be `noindex` and removed from sitemap.
- Pricing page title promises pricing, but live DOM has 0 `$` price values. This can create trust/conversion friction.
- Pricing CTAs use `?intent=diagnostic|sprint|growth`, but live form inspection did not find clear intent capture handling. Paid-intent clicks may arrive as generic free snapshot leads.
- Terminology is still diluted in places: `Free AI Visibility Snapshot`, `AI search roadmap`, `AI visibility check`, `Check My Visibility`, `SEO/GEO/AEO`.
- Remaining copy snippets found:
  - homepage H1: `Get your free AI search roadmap without agency theater.`
  - about footer CTA: `Get My Free Roadmap`
- Commercial pages expose mostly `WebPage` JSON-LD; no stronger visible Service/Person/Organization/FAQ/Breadcrumb schema found in quick DOM audit.
- Money pages are visually/systemically consistent, but share repeated structure and may need more unique vertical proof/examples per page.

## External market scan

Observed page/offer pattern in AI visibility/local AI search market:

- Competitors are not only publishing blogs; many push instant `AI visibility checker/audit/score` tools.
- Common promise: check ChatGPT/Gemini/Perplexity/Claude visibility, competitors, cited sources, and produce a score/report in 60 seconds to 3 minutes.
- Local SMB language is less `GEO/AEO` and more: `Does ChatGPT recommend my business or my competitor?`
- Strong vertical opportunities: dentists, roofers, HVAC, plumbers, lawyers, med spas, restoration, contractors.
- Market gap for Alex/Base2026: transparent evidence-backed audit with prompt logs, sources, and concrete fixes instead of generic score-only SaaS.

## Diagnosis: what we are doing wrong

1. We built too much proof infrastructure before the direct demand-capture surface was strong enough.
2. We treated indexation and internal linking as if they would quickly create leads. They will not, especially on a fresh domain/topic cluster.
3. The Base2026 sitemap is still heavily source-record dominated: 1,544 source pages vs 40 topic pages and 62 other hub/money/resource pages.
4. The offer is close, but not yet brutal/simple enough for local-business buyers.
5. We have not yet run the fast acquisition loop: specific vertical pages + sample report + mini-audit outreach + CTA/analytics validation.
6. Some technical/conversion hygiene remains unresolved: www redirect, `/knowledge` slash redirect, thank-you noindex, pricing trust, intent capture.

## Is Alex too early / impatient?

Partly yes, for Google organic traffic. Two weeks of build/indexation work is too early to expect stable organic traffic from a fresh architecture, especially when many URLs were deployed in the last few days.

But the impatience is strategically correct: waiting months for Google alone is not acceptable. The solution is not to panic or mass-publish weak pages; it is to run SEO and direct acquisition in parallel.

## Corrected 7–14 day action plan

### Phase 1 — Fix leaks immediately

- 301 `www` to apex.
- 301 `/knowledge` to `/knowledge/`.
- Set `/thank-you-ai-visibility-audit/` to `noindex` and remove from sitemap.
- Normalize remaining `roadmap` offer terminology where it conflicts with `Free AI Visibility Snapshot`.
- Make pricing page honest: either show actual prices/ranges or rename/position it as packages/engagement levels.
- Ensure `intent` query parameters are captured in the audit form/email/lead record.

### Phase 2 — Re-check actual webmaster state

Use Alex's logged-in Chrome:

- GSC Sitemaps: status/discovered for `/knowledge/sitemap.xml`.
- GSC URL Inspection sample sets:
  - 31 hub/demand URLs
  - 11 priority crawl-path URLs
  - 48 money/template URLs
- Bing Webmaster:
  - full 1,703 IndexNow processing
  - sitemap status
  - priority URL dashboard status

Classify URLs as indexed / discovered-not-indexed / crawled-not-indexed / unknown / impressions / clicks.

### Phase 3 — Turn offer into a tool/report, not just a page

- Public sample report: score, prompts tested, AI answers, competitors found, cited sources, priority fixes.
- Snapshot page fields: business name, website, category, city, competitors, email.
- Above-the-fold copy: `See whether ChatGPT, Perplexity and Gemini recommend your business — or your competitors.`
- Base2026 becomes proof/methodology behind the report, not the primary thing a local owner must understand.

### Phase 4 — Build 5–7 vertical local landing pages

Start with high-LTV verticals:

- dentists
- roofers
- HVAC
- plumbers
- lawyers
- med spas
- restoration/contractors

Each page should have:

- sample local prompts
- what AI checks
- concrete competitor/source examples
- CTA to Free AI Visibility Snapshot
- Base2026 proof/methodology bridge

### Phase 5 — Run non-public acquisition in parallel

- Pick 20 prospects from existing lead data / public search.
- Produce 5 personalized mini-snapshots first.
- Draft outreach only; send only after Alex approval.
- Track outcome in Agency OS/Plane.

## Recommended next move

Do not make another blind page batch yet.

Next concrete move:

1. Fix the small technical/conversion leaks.
2. Open GSC/Bing and capture fresh indexed/discovered/impression status.
3. Build one public sample AI Visibility Snapshot report page.
4. Build 3–5 vertical pages.
5. Prepare 5 outbound mini-snapshots, approval-gated.

## Operator status

- No deploy/edit was done in this audit except saving this report.
- No outreach was sent.
- No public posting/submission was done.
- Next public changes should go through the existing Base2026/Alex release/QA gates.
