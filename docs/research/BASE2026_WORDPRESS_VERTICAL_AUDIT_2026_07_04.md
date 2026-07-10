# Base2026 WordPress vertical audit — 2026-07-04

Status: local/private planning note. No public Base2026 publishing, indexation, or outreach action was performed by this audit.

Verified at: 2026-07-04 15:16:31 Europe/Minsk.

## User question

Alex suspected that Base2026 is no longer only an SEO/GEO source base: a web-development layer already exists, and one creator appears to answer many WordPress questions. The requested outcome was to inspect the existing base and make the appropriate conclusions.

## Evidence checked

- Base2026 repo: `/Users/alexyarosh/Projects/base2026-migration/DW/base2026`
- Agency OS / Obsidian command center: `/Users/alexyarosh/Projects/ai-agency-obsidian-command-center`
- Public export files under `public-data/tiktok/`
- Private operational SQLite: `12_knowledge-base/indexes/kb.sqlite`
- Agency OS SQLite: `data/agency.sqlite`
- Existing staged taxonomy note: `docs/research/STAGED_SOURCE_CANDIDATES_2026_06_23.md`

## Findings

### 1. The project already has a web-development taxonomy lane

Agency OS already has a Base2026 Product task for this:

- `B26-8` / task `#38`: `B26-TAXONOMY-02: WebDevLog AI web-dev workflow category`
- Artifact: `docs/research/STAGED_SOURCE_CANDIDATES_2026_06_23.md`

That staged note already separates:

1. Marketer / GEO / AEO / AI-search creators
2. AI Marketing Agents & Skills
3. WebDevLog / AI-assisted web-development workflows
4. AI TikTok/social automation case studies

So the user hypothesis is correct: Base2026 is not purely an SEO bucket anymore. The separation has already started.

### 2. WordPress exists today, but it is scattered across SEO/CMS/web-dev topics

Public export counts from `public-data/tiktok/`:

| Dataset | Total rows | WordPress exact rows | WordPress/CMS broad rows | Web-dev broad rows | SEO/search rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| `source_records.jsonl` | 1,615 | 61 | 84 | 742 | 1,112 |
| `topics.jsonl` | 1,538 | 8 | 13 | 31 | 423 |

The system already generates WordPress-ish topics, for example:

- `wordpress-static-homepage-setup`
- `wordpress-plugin-loyalty`
- `wordpress-seo-plugin-capabilities`
- `wordpress-plugin-bloat`
- `wordpress-speed-monitoring`
- `wordpress-ai-workflow-risk`
- `cms-choice-seo`
- `cms-seo-readiness`

But there is no canonical top-level WordPress vertical/bucket yet. The signal is currently fragmented into individual topic names and mixed SEO/CMS/web-dev buckets.

### 3. `@iamdandavies` is a strong WordPress anchor creator

From private SQLite (`12_knowledge-base/indexes/kb.sqlite`):

- Creator exists as `tiktok-iamdandavies` / `@iamdandavies`.
- Current video rows: `35`.
- Title/URL matches for WordPress/web/CMS terms: `12`.
- Review/transcript state:
  - `19` transcribed/new
  - `3` transcribed/source_review_pass
  - `11` needs_source_review/needs_source_review
  - `2` needs_source_review/source_review_required_after_polish_qa

Public source examples already include repeated WordPress Q&A material from this creator:

- WordPress static homepage setup
- WordPress plugin loyalty
- out-of-date plugin risk
- contact form/plugin recommendations
- WordPress speed/cleanup
- WordPress vs Laravel/platform-choice discussion

Conclusion: `@iamdandavies` should not be treated as just another general SEO creator. He is the first obvious anchor for a dedicated WordPress insight lane.

### 4. `@webhivedigital` is a hybrid SEO + WordPress/web-dev source

From private SQLite:

- Creator exists as `tiktok-webhivedigital` / `@webhivedigital`.
- Current video rows: `1,020`.
- Title/URL matches for WordPress/web/CMS terms: `372`.
- Many old rows are intentionally out of scope, but there are still `183` transcribed/new rows and existing reviewed public WordPress plugin/SEO cards.

Public exact WordPress source examples include:

- WordPress plugin bloat
- WordPress SEO / plugin capabilities
- WordPress speed monitoring

Conclusion: `@webhivedigital` should remain hybrid: route SEO/search material to SEO/GEO lanes, and WordPress/plugin/CMS material to the new WordPress vertical.

## Decision

Add `WordPress / CMS implementation insights` as a separate Base2026 source/category vertical under the broader web-development layer.

This vertical should be private-first and source-backed. It should collect:

- WordPress setup and admin workflows
- plugin selection, plugin bloat, plugin risk, and plugin loyalty
- themes/builders/CMS architecture when source-backed
- performance/speed/security/maintenance advice
- WordPress SEO plugin/capability discussions
- WooCommerce only when the source gives concrete implementation insight

Do **not** treat this as permission to publish bulk WordPress pages. Existing Base2026 gates still apply: reviewed source text, exact-evidence insight cards, no raw transcript dumps, no indexable singleton/thin topic pages, and no release until a specific promotion gate is passed.

## Recommended routing/taxonomy

| Layer | Purpose | Example values |
| --- | --- | --- |
| Platform | Where the source came from | `tiktok`, `youtube`, `github`, `blog` |
| Source type | Source shape | `creator_video`, `repo`, `blog_post`, `case_study` |
| Vertical | Product category | `seo`, `geo_ai_search`, `web_development`, `wordpress_cms` |
| Topic | Specific insight cluster | `wordpress-static-homepage-setup`, `wordpress-plugin-bloat`, `cms-choice-seo` |
| Creator role | How the creator should be interpreted | `wordpress_anchor`, `seo_wordpress_hybrid`, `webdev_workflow_source` |

Suggested creator mapping:

| Creator | Mapping | Notes |
| --- | --- | --- |
| `@iamdandavies` | `wordpress_anchor` | Main WordPress Q&A/tutorial signal; route WordPress questions here first. |
| `@webhivedigital` | `seo_wordpress_hybrid` | Strong SEO corpus plus useful WordPress/plugin/CMS examples. |
| `@tjrobertson52` | `webdev_cms_platform_risk` | Has CMS/WordPress/AI workflow topics, but not the primary WordPress anchor. |
| `@joshuamaraney` | `ai_web_search_hybrid` | Contains some WordPress term matches, but mostly AI/web/search governance style material. |

## Implementation backlog

1. Add canonical vertical alias mapping:
   - exact: `wordpress`, `woocommerce`, `elementor`, `gutenberg`, `wp`
   - broad/supporting: `plugin`, `theme`, `cms`, `homepage`, `contact form`, `builder`, `admin`, `speed`, `security`
2. Add a private WordPress collection/report page in the internal review layer before any public page.
3. Generate a reviewed WordPress insight queue from existing public-safe candidates, starting with `@iamdandavies` and `@webhivedigital`.
4. Keep `platform=tiktok` separate from `vertical=wordpress_cms`; do not confuse source platform with content category.
5. Only promote public WordPress pages/cards through the existing Base2026 evidence/indexation gate.

## Operational outcome

The appropriate conclusion is: **yes, Base2026 should now explicitly recognize WordPress as a separate category/vertical, nested under the web-development expansion rather than buried inside generic SEO.**

The next Agency OS task should be a scoped implementation task for `B26-TAXONOMY-03: WordPress / CMS implementation insights category`.

## 2026-07-04 card-batch execution addendum

Implemented a first private cards-only batch for the WordPress/CMS vertical:

- Card batch report: `docs/research/BASE2026_WORDPRESS_CMS_CARD_BATCH_2026_07_04.md`
- Review report: `docs/research/BASE2026_WORDPRESS_CMS_CARD_REVIEW_REPORT_2026_07_04.md`
- Candidate cards: `12`
- Evidence gate: `12/12` exact matches
- SQLite status after internal release: `12` new `insight_card_candidate` rows promoted to `reviewed`; `0` promoted to `approved`.
- Public/indexation status: held; no standalone WordPress pages, deployment, IndexNow, GSC/Bing indexing request, outreach, or source/transcript publication.

## 2026-07-04 webhive hybrid card-batch #2 addendum

Implemented a second private cards-only batch focused on `@webhivedigital` as the SEO/WordPress hybrid source:

- Card batch report: `docs/research/BASE2026_WORDPRESS_CMS_CARD_BATCH2_2026_07_04.md`
- Review report: `docs/research/BASE2026_WORDPRESS_CMS_CARD_BATCH2_REVIEW_REPORT_2026_07_04.md`
- Candidate cards: `12` total: `10` from `@webhivedigital`, `2` supplemental cards from `@iamdandavies`.
- Evidence gate: `12/12` exact matches.
- SQLite status after internal release: `12` new `insight_card_candidate` rows promoted to `reviewed`; `0` promoted to `approved`.
- Two-batch total: `24` private reviewed WordPress/CMS cards from the 2026-07-04 vertical work, with `0` public/approved promotion from these batches.
- Public/indexation status: held; no standalone WordPress pages, public export, deployment, IndexNow, GSC/Bing indexing request, outreach, source/transcript publication, staging, or commit.
