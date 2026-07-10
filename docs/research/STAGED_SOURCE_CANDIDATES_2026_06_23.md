# Staged Base2026 Source Candidates — 2026-06-23

Status: local/private staging queue; not a public Base2026 release artifact.
Source: Alex voice approval in Telegram + `REDDIT_AND_BASE2026_CREATOR_EXPANSION_RESEARCH_2026_06_23.md`.

## Owner decision captured

- Prior Reddit/creator expansion research brief is accepted as directionally correct.
- Implement Reddit comments lane as PullPush search + Arctic Shift deep thread/tree fetch.
- Add new source categories locally first; do not bulk-publish.
- For TikTok/short-form sources, prioritize videos that can be turned into coherent text transcripts: spoken explanations, captions/subtitles, interviews, walkthroughs.
- Reject/hold visual-only TikToks where the value is mostly screen text, gestures, UI montage, or music with little/no spoken content.

## Transcript suitability gate for TikTok/video candidates

A candidate can enter the private intake queue only if at least one source video passes:

- `spoken_density`: high enough that speech/audio carries the main idea.
- `caption_availability`: platform captions, extracted transcript, or reliable audio transcription path exists.
- `context_completeness`: transcript alone explains the concept without needing every visual frame.
- `technical_specificity`: includes concrete workflows, tools, commands, prompts, stack, or repeatable process.
- `public_safety`: public source; no login/cookie scraping/CAPTCHA bypass; no private/raw dumps published.

Suggested statuses:

- `candidate` — found but not checked.
- `transcript_check` — needs transcript extraction/manual check.
- `queue_private_intake` — good spoken-text candidate; can enter private intake/dry-run.
- `hold_visual_only` — useful visually, but bad for text knowledge base.
- `reject_low_signal` — generic/opinion/listicle with little reusable substance.

## Category 1: Marketer / GEO / AEO / AI-search creators

Purpose: human experts and marketer creators whose video/interview/tutorial material can feed Source Intelligence after transcript review.

Initial P1 queue from research brief:

- Aleyda Solis — international SEO, AI search, SEOFOMO/Crawling Mondays; platform check needed.
- Lily Ray — AI search / AI Overviews / Google updates; YouTube sources already known.
- Michael King / iPullRank — technical GEO/content engineering; YouTube source already known.
- Rand Fishkin / SparkToro — audience research and AI-search skepticism; YouTube/channel source known.
- Christopher S. Penn / Trust Insights — AI for marketers; YouTube source known.
- Ethan Smith / Graphite — AEO for SaaS/products; YouTube source known.
- Joy Hawkins / Sterling Sky — local SEO; YouTube/source check needed.
- Sarvesh Shrivastava — AI-powered local SEO systems; YouTube/source check needed.
- Caleb Ulku — local SEO operations; source check needed.
- Darren Shaw — already indexed anchor; refresh only if needed.

Fresh TikTok/search candidates to transcript-check:

- Will Francis — AI + Marketing: `https://www.tiktok.com/@willfrancis24/video/7436825414242209056`
  - Search snippet: spoken-looking AI SEO/ChatGPT/Perplexity/Google AI Overviews explainer.
  - Status: `transcript_check`.
- Jake / The Marketing Wizard: `https://www.tiktok.com/@thewizardmarketing/video/7507321725806185771`
  - Search snippet: Google AI mode changing SEO; likely useful if spoken explanation is present.
  - Status: `transcript_check`.
- Kate Smoothy / Webhive Digital: `https://www.tiktok.com/@webhivedigital/video/7444950668600692001`
  - Search snippet: AI tools for digital marketing/SEO with ChatGPT, Perplexity, Claude.
  - Status: `transcript_check`.
- Boss AI Automations: `https://www.tiktok.com/@boss_automations/video/7440931159543991584`
  - Search snippet: AI agent for marketing agencies.
  - Status: `transcript_check`; likely commercial/automation angle, verify substance.

## Category 2: AI Marketing Agents & Skills

Source type: GitHub repos / skill packs / agent kits, separated from human video creators.

Seed repos:

- `coreyhaines31/marketingskills`
- `ericosiu/ai-marketing-skills`
- `zubair-trabzada/ai-marketing-claude`
- `aitytech/agentkits-marketing`
- `indranilbanerjee/digital-marketing-pro`
- `BrianRWagner/ai-marketing-claude-code-skills`
- `thatrebeccarae/claude-marketing`
- `thearnavrustagi/marketmenow`

Metadata fields to collect:

- repo URL, license, stars/forks, last push, contributor activity
- compatible tools: Claude Code, Codex, Cursor, Copilot, Hermes, MCP, browser automation
- artifact types: skill, agent, slash command, prompt, workflow, integration
- marketing domains: SEO/AEO/GEO, CRO, copywriting, paid media, email, analytics, outbound, agency ops
- maturity/risk notes: star anomalies, abandoned repo, thin prompt pack, unsafe automation claims

## Category 3: WebDevLog / AI-assisted web-development workflows

Source type: practical blog/video/repo workflows for building websites/products with coding agents.

Seed sources from research brief:

- Addy Osmani — My LLM coding workflow going into 2026
- Matt Lambert — Building projects with Claude Code
- Samanvya Tripathi — Shipping a feature in 45 minutes
- Mikul Gohil — Claude Code workflows
- Shawn Lin — Agent Plugins
- Zen van Riel — Agentic Engineer Workflow
- AI with Avthar — Claude Code project setup
- Upstash Context7
- `wshobson/agents`
- `obra/superpowers`

Fresh spoken-video candidates to transcript-check:

- Sandy Lee / Claude Code social-media automation transcript: `https://sozai.app/transcript/automate-90-percent-social-media-claude-code/`
  - Already has transcript text in indexed page; good for text-first evaluation.
  - Status: `queue_private_intake` after source URL verification.
- Chris Raroque — updated Claude Code workflow tutorial: `https://www.youtube.com/watch?v=gNR3XI5Eb0k`
  - Search result includes detailed spoken transcript excerpt.
  - Status: `transcript_check`.
- Cole Medin — complete agentic coding workflow: `https://www.youtube.com/watch?v=goOZSXmrYQ4`
  - Search result includes workflow-heavy spoken transcript excerpt.
  - Status: `transcript_check`.
- Peter Yang / Kieran Klaassen — multiple AI agents with Claude Code: `https://www.youtube.com/watch?v=Z_iWe6dyGzs`
  - Search result includes practical multi-agent workflow transcript excerpt.
  - Status: `transcript_check`.

## Category 4: AI TikTok/social automation case studies

Use only if transcript has reusable process detail and does not imply unsafe auto-posting/spam.

Candidates:

- Lucas Barnes — How I'm Using Codex for TikTok Marketing: `https://www.youtube.com/watch?v=fyEORvqTgxs`
  - Search result includes transcript about Codex + Postiz + Cloudflare R2 + strategy docs + human posting review.
  - Status: `queue_private_intake` after source verification.
- Postiz — AI agent got 500K TikTok views: `https://www.youtube.com/watch?v=6_H-3cwIg1c`
  - Transcript exists in search result; short case study.
  - Status: `transcript_check`; likely promotional, verify independently.
- Koda — He built an AI agent. It runs his TikTok: `https://www.youtube.com/watch?v=Lvlk22j9JSM`
  - Transcript excerpt covers stack and hook formula.
  - Status: `transcript_check`; likely needs original source validation.
- Kachori Capitalists — AI UGC / 10 TikTok accounts: `https://www.youtube.com/watch?v=Nf4aRlB68q8`
  - Transcript excerpt has UGC pipeline discussion.
  - Status: `transcript_check`.

## Category 5: WordPress / CMS implementation insights

Source type: WordPress/CMS creator Q&A, tutorials, plugin/theme/admin workflows, and source-backed implementation advice. This is a child vertical under the broader web-development expansion, not a replacement for SEO/GEO.

Audit reference: `BASE2026_WORDPRESS_VERTICAL_AUDIT_2026_07_04.md`.

Initial creator mapping:

- `@iamdandavies` — `wordpress_anchor`; strong repeated WordPress Q&A/tutorial signal, including static homepage setup, plugin loyalty, plugin risk, contact forms, and WordPress-vs-framework discussions.
- `@webhivedigital` — `seo_wordpress_hybrid`; keep SEO/search material in SEO lanes, but route plugin/CMS/WordPress implementation material into this vertical.
- `@tjrobertson52` — `webdev_cms_platform_risk`; useful CMS/WordPress/AI workflow topics, but not the first WordPress anchor.
- `@joshuamaraney` — `ai_web_search_hybrid`; some WordPress term matches, mostly AI/search/web governance material.

Canonical vertical aliases to start with:

- Exact: `wordpress`, `woocommerce`, `elementor`, `gutenberg`, `wp`.
- Broad/supporting: `plugin`, `theme`, `cms`, `homepage`, `contact form`, `builder`, `admin`, `speed`, `security`.

Private-first gate:

- Collect into review/report queue before public promotion.
- Keep `platform=tiktok` separate from `vertical=wordpress_cms`.
- Do not publish bulk WordPress pages or singleton thin topic pages without the existing exact-evidence/indexation release gate.

## Next execution queue

1. Verify source URLs and platform type for P1 marketer batch.
2. For TikTok candidates, check whether TikTok exposes useful captions/transcripts or whether audio transcription is needed.
3. Move only text-rich candidates into private intake/dry-run.
4. Keep OSS repo categories separate from creator/video categories.
5. Build the private WordPress/CMS implementation insight queue from `@iamdandavies` and `@webhivedigital` before public promotion.
6. Do not publish to public Base2026 until existing source review and release gates pass.
