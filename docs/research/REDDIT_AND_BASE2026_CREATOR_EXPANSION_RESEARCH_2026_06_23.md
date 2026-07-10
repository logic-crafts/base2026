# Reddit Search + Base2026 Creator Expansion Research — 2026-06-23

Status: research brief accepted by Alex; execution split into local staged queue + implementation tasks. Not yet an intake/import run.
Prepared for: Base2026 / Agency OS Research.
Timestamp: 2026-06-23 02:53 Minsk time.
Accepted: 2026-06-23 Telegram voice direction — PullPush + Arctic Shift approved; new categories should be staged locally first; TikTok/video sources must be text-transcript-suitable.

## Executive verdict

1. **Reddit comments are usable without API keys, but not through Reddit itself as the primary path.** Current direct `reddit.com/*.json` tests returned 403 from this machine. The practical no-key path is **PullPush for comment search** + **Arctic Shift for full/deep thread trees**.
2. **For Base2026 expansion, prioritize video-first marketing/GEO/AEO/local SEO creators first**, then add AI marketing agent/skill repositories as a new source category, then WebDevLog/AI web-development workflow sources.
3. **Do not immediately publish/import all new candidates.** Add them as staged pipeline candidates first, run discovery/check-only, then send only clean TikTok/video records through the existing Base2026 review/release gates.
4. **Recommended next execution slice:** add a small P1 batch of 8–10 marketing creators and 6–8 OSS/WebDevLog sources to a private intake queue, dry-run discovery/import, then review results before any public release.

## 1. Reddit comments: free/no-key research stack

### Recommended stack

- **Primary comment search:** PullPush
  - URL: https://pullpush.io/
  - Best for: keyword search across Reddit comments, filtering by subreddit/time/author/link.
- **Primary deep thread/tree extraction:** Arctic Shift
  - API docs/source: https://github.com/ArthurHeitmann/arctic_shift/tree/master/api
  - Base: https://arctic-shift.photon-reddit.com
  - Best for: full comment tree by `link_id`, deep branches, comment-rich threads.
- **Fallback only:** Reddit `.json`
  - Direct checks from current machine returned 403.
  - Even when accessible, depth is limited and `morechildren` expansion usually needs auth/OAuth.

### PullPush examples

Search comments by phrase:

```bash
curl "https://api.pullpush.io/reddit/search/comment/?q=chatgpt&subreddit=LocalLLaMA&size=100&sort=desc&sort_type=created_utc"
```

Search comments inside a specific thread:

```bash
curl "https://api.pullpush.io/reddit/search/comment/?link_id=6uey5x&size=100"
```

Search by date window:

```bash
curl "https://api.pullpush.io/reddit/search/comment/?q=%22battery%20life%22&subreddit=iphone&after=1704067200&before=1735689600&size=100"
```

Limits/risks:

- `size` is limited, paginate with `before/after`.
- Archive can lag fresh Reddit.
- Old Pushshift-derived archives may contain deleted/removed content; treat as privacy-sensitive.

### Arctic Shift examples

Search comments:

```bash
curl "https://arctic-shift.photon-reddit.com/api/comments/search?subreddit=LocalLLaMA&body=chatgpt&limit=100&fields=id,author,body,score,created_utc,link_id,parent_id"
```

Fetch all comments for a post:

```bash
curl "https://arctic-shift.photon-reddit.com/api/comments/search?link_id=t3_POSTID&limit=auto&fields=id,author,body,score,created_utc,parent_id"
```

Fetch deep comment tree:

```bash
curl "https://arctic-shift.photon-reddit.com/api/comments/tree?link_id=t3_POSTID&limit=25000&start_depth=50&start_breadth=999" -o reddit_thread_POSTID.json
```

Live check from worker:

- `comments/search?link_id=...` returned 200.
- `comments/tree?link_id=...&limit=9999&start_depth=50&start_breadth=999` returned 200 and ~3.3 MB JSON.

Limits/risks:

- No uptime/performance guarantees.
- Broad full-text searches can timeout; narrow by subreddit/date.
- Data can differ from live Reddit for fresh content.

### OSS/MCP candidates

- `pullpush-mcp`: https://github.com/jacklenzotti/pullpush-mcp
  - MCP wrapper for PullPush.
  - Candidate for Hermes MCP integration after quick audit.
- `reddit-comment-harvester`: https://github.com/wlyastn/reddit-comment-harvester
  - Uses public Reddit `.json`; weaker now because direct `.json` can 403.
- `hkay-dev/reddit-scraper`: https://github.com/hkay-dev/reddit-scraper
  - Also depends on visible public JSON; does not reliably expand `load more comments`.

### Compliance guardrails

- Use public content only.
- No login/cookie scraping for Reddit by default.
- No CAPTCHA bypass, residential proxies, or private subreddit scraping.
- Cache and throttle.
- Minimize usernames/PII in durable storage.
- For commercial or large-scale Reddit data usage, require legal/API review.

### Proposed Base2026/Hermes Reddit workflow

1. Use PullPush to discover candidate discussions.
2. Use Arctic Shift to fetch full thread trees for selected `link_id`s.
3. Flatten tree locally: `id`, `parent_id`, `depth`, `body`, `score`, `created_utc`, `author`, `link_id`.
4. Rank branches by depth, score, and keyword relevance.
5. Send only selected branches to LLM; do not dump entire comment trees into context.
6. Store source URLs and retrieval timestamp; keep raw comment dumps private unless explicitly cleared.

## 2. Base2026 marketer/GEO/AEO creator expansion

### P1: add to pipeline first

These should be the first human/creator targets for discovery/intake review because they are strongly relevant and have public video/interview/tutorial footprints.

1. **Aleyda Solis** — international SEO, AI search, SEOFOMO/Crawling Mondays  
   Source: https://www.aleydasolis.com/en/  
   Angle: international SEO, AI-search visibility, multilingual discovery.

2. **Lily Ray** — AI search, Google updates, GEO/AEO/LLMO  
   Sources: https://www.youtube.com/watch?v=2nJkT8zOzcM, https://www.youtube.com/watch?v=Df3EHdgm6zA  
   Angle: AI Overviews, entity/reputation, AI SEO reality checks.

3. **Michael King / iPullRank** — technical GEO, content engineering  
   Source: https://www.youtube.com/watch?v=TOjda22Zatw  
   Angle: semantic relevance, LLM mentions, technical content optimization.

4. **Rand Fishkin / SparkToro** — audience research, AI-search skepticism  
   Sources: https://www.youtube.com/watch?v=PVtDnOdmCLM, https://www.youtube.com/channel/UCgkXUGNLcEAZKy6KpdSycVQ  
   Angle: audience research for GEO, brand mentions, PR/YouTube/Reddit as AI-search inputs.

5. **Christopher S. Penn / Trust Insights** — AI for marketers  
   Source: https://www.youtube.com/watch?v=9Voy1fJyEt0  
   Angle: AI marketing strategy, GEO measurement, semantic search.

6. **Ethan Smith / Graphite** — AEO for SaaS/products  
   Source: https://www.youtube.com/watch?v=iT7kq-R3Gjc  
   Angle: answer engine optimization, product recommendations in ChatGPT/Claude/Gemini/Perplexity.

7. **Darren Shaw / Whitespark** — local SEO + TikTok/local search  
   Sources: https://whitespark.beehiiv.com/p/tiktok-local-seo-yes, https://www.youtube.com/watch?v=1awWMG1e5kY, https://www.tiktok.com/@darrenshawseo/video/7468348475449593093  
   Angle: GBP, local ranking factors, reviews, local video, TikTok/local search myths.  
   Note: already in Base2026; keep as anchor and refresh candidate.

8. **Joy Hawkins / Sterling Sky** — local SEO authority  
   Sources: https://ca.linkedin.com/in/joyhawkins, https://www.youtube.com/watch?v=pZ9HZu4qFWY  
   Angle: GBP troubleshooting, local rankings, reviews, multi-location SEO.

9. **Sarvesh Shrivastava** — India/global local SEO + AI workflows  
   Sources: https://sarveshshrivastava.com/, https://www.youtube.com/watch?v=CLL5Ep-LrhA  
   Angle: AI-powered local SEO systems, GBP, service business SEO.

10. **Caleb Ulku** — local SEO operations  
    Source: https://www.themarketingshow.com/people/caleb-ulku  
    Angle: repeatable local SEO operations, service businesses, rank maps.

### P2: second wave / GEO diversity

- Kaleigh Moore — Creator AEO: https://www.kaleighmoore.com/blog/2026/6/18/creator-aeo
- Fernando Angulo / Semrush — Spanish/LATAM/global AI search: https://fernandoangulo.com/
- Victoria Olsina — Web3/Crypto/SaaS AI search: https://victoriaolsina.com/about-me/
- Chris Raulf — international SEO + GEO: https://chrisraulf.com/international-seo-consultant/
- Murat Ulusoy — technical GEO/entity engineering: https://www.muratulusoy.de/en/murat-ulusoy.html
- Jens Supan — global SEO + AI search: https://www.jenssupan.com/
- Tim Kahlert — Local SEO Bible: https://cy.linkedin.com/in/timkahlert
- Jeff Hassemer / Firestarter Forum — TikTok local discovery: https://firestarterforum.substack.com/p/49-of-your-customers-are-searching
- Sarah Mitchell / Crea8ive Solution — TikTok SEO for local service businesses: https://crea8ivesolution.net/tiktok-seo-strategy-for-local-service-businesses/
- Chad Wyatt — TikTok SEO/playbook: https://chad-wyatt.com/social-media/tiktok-seo/
- Kunal Kerkar / Kerkar Media — India AEO/schema: https://kerkarmedia.com/what-is-aeo-answer-engine-optimization/
- Austin Heaton — AEO consultant: https://www.austinheaton.com/blog/complete-guide-to-aeo-june-2026
- Marie Haynes — Google quality/AI-era SEO: https://www.youtube.com/watch?v=K0FVlM7Xmc0
- HubSpot Marketing channel — mainstream AEO education: https://www.youtube.com/watch?v=qT3M5WVafRQ
- Ahrefs channel — AI-search strategy roundtables: https://www.youtube.com/watch?v=RwKKLnyXCig

### Intake recommendation

Do not bulk-add all 25 at once. First run:

- P1 batch: Aleyda, Lily, Michael King, Rand/SparkToro, Christopher Penn, Ethan Smith, Joy Hawkins, Sarvesh, Caleb.
- Keep Darren Shaw as already-indexed anchor; use refresh only if needed.
- For each candidate, identify concrete public video/social source before adding to Base2026 private intake config.
- If no TikTok feed exists, route to `youtube/blog/interview candidate` backlog instead of forcing into TikTok pipeline.

## 3. New Base2026 category: AI Marketing Agents & Skills

### P0/P1 OSS sources

1. **coreyhaines31/marketingskills**  
   URL: https://github.com/coreyhaines31/marketingskills  
   Reported worker check: ~34.6k stars / 5.7k forks.  
   Why: canonical marketing skills for Claude Code, Codex, Cursor, Windsurf, Agent Skills. Covers CRO, copywriting, SEO, AI SEO/AEO/GEO/LLMO, analytics, programmatic SEO, schema.

2. **ericosiu/ai-marketing-skills**  
   URL: https://github.com/ericosiu/ai-marketing-skills  
   Reported worker check: ~2.7k stars / 567 forks.  
   Why: content ops, SEO ops, conversion ops, outbound engine, sales pipeline, experiments.

3. **zubair-trabzada/ai-marketing-claude**  
   URL: https://github.com/zubair-trabzada/ai-marketing-claude  
   Reported worker check: ~2.0k stars / 606 forks.  
   Why: Claude Code marketing suite, subagents, website audit, copy, email, ads, competitor analysis, PDF reports.

4. **aitytech/agentkits-marketing**  
   URL: https://github.com/aitytech/agentkits-marketing  
   Reported worker check: ~547 stars / 64 forks.  
   Why: marketing automation for Claude Code, Cursor, GitHub Copilot-compatible workflows.

5. **indranilbanerjee/digital-marketing-pro**  
   URL: https://github.com/indranilbanerjee/digital-marketing-pro  
   Reported worker check: ~150 stars / 40 forks.  
   Why: 158 skills, 25 specialist agents, compatibility claims for Claude Code, Codex, Cursor, Copilot CLI, Hermes Agent, OpenClaw.

6. **BrianRWagner/ai-marketing-claude-code-skills**  
   URL: https://github.com/BrianRWagner/ai-marketing-claude-code-skills  
   Reported worker check: ~337 stars / 79 forks.  
   Why: marketing frameworks as executable skills.

7. **thatrebeccarae/claude-marketing**  
   URL: https://github.com/thatrebeccarae/claude-marketing  
   Why: DTC/ecommerce-oriented marketing ops: Klaviyo, Shopify, GA4, Looker Studio, paid media, SEO, CRO.

8. **thearnavrustagi/marketmenow**  
   URL: https://github.com/thearnavrustagi/marketmenow  
   Why: agentic outbound marketing automation, brand templates, Figma MCP, social publishing.

### Proposed taxonomy

- `ai-marketing-agents`
- `marketing-skills`
- `seo-aeo-geo`
- `cro-landing-pages`
- `content-ops`
- `copywriting-messaging`
- `paid-media`
- `email-lifecycle`
- `outbound-leadgen`
- `analytics-attribution`
- `multi-agent-marketing-teams`
- `agency-multibrand-ops`

## 4. New Base2026 category: WebDevLog / AI-assisted web development workflows

### P0/P1 OSS/index sources

1. **obra/superpowers**  
   URL: https://github.com/obra/superpowers  
   Why: agentic skills framework and SDLC methodology for Claude Code, Codex, Cursor, Gemini CLI, Copilot CLI, OpenCode.  
   Caveat: star count reported as extremely high by worker; verify star-history/adoption before treating stars as trust.

2. **wshobson/agents**  
   URL: https://github.com/wshobson/agents  
   Why: multi-harness marketplace of plugins/agents/skills/commands for Claude Code, Codex CLI, Cursor, OpenCode, Gemini CLI, Copilot.

3. **shinpr/claude-code-workflows**  
   URL: https://github.com/shinpr/claude-code-workflows  
   Why: requirements → design → implementation → quality workflows; useful for spec/design/test-aligned WebDevLog.

4. **upstash/context7**  
   URL: https://github.com/upstash/context7  
   Why: real-time library docs for AI code editors; key dependency in AI web-dev workflows.

5. **nexu-io/open-design**  
   URL: https://github.com/nexu-io/open-design  
   Why: local-first design/prototyping workflow for web/desktop/mobile prototypes; supports multiple coding agents.

6. **VoltAgent/awesome-agent-skills**  
   URL: https://github.com/VoltAgent/awesome-agent-skills  
   Why: discovery/index source for agent skills across Claude/Codex/Gemini/Cursor.

7. **hesreallyhim/awesome-claude-code**  
   URL: https://github.com/hesreallyhim/awesome-claude-code  
   Why: curated list of Claude Code skills, hooks, slash commands, orchestrators, plugins.

### Practical creator/blog/video sources

- Addy Osmani — My LLM coding workflow going into 2026: https://addyosmani.com/blog/ai-coding-workflow/
- Matt Lambert — Building projects with Claude Code: https://iammattl.com/blog/what-ive-learned-building-projects-with-claude-code
- Samanvya Tripathi — Shipping a feature in 45 minutes: https://samanvya.dev/blog/claude-code-feature-workflow
- Mikul Gohil — Claude Code workflows: https://www.mikul.me/blog/claude-code-workflows-ship-faster-ai-development
- Shawn Lin — Agent Plugins: https://blog.shdennlin.com/projects/agent-plugins/
- Elena Daehnhardt — How I Actually Use Claude Code: https://daehnhardt.com/blog/2026/06/15/claude-code/
- Chudi Nnorukam — Claude Code complete guide: https://chudi.dev/blog/claude-code-complete-guide
- LowCode Agency — Claude Code Agentic Workflows: https://www.lowcode.agency/blog/claude-code-agentic-workflows
- Owain Lewis — GitHub workflow with Codex + Claude Code: https://www.youtube.com/watch?v=zdeZGePZMuE
- Zen van Riel — Agentic Engineer Workflow: https://www.youtube.com/watch?v=ElYxdpYi4U0
- AI with Avthar — How I start every Claude Code project: https://www.youtube.com/watch?v=aQvpqlSiUIQ
- Eric Tech — Claude Code autonomous apps: https://www.youtube.com/watch?v=nX_bGyIOFM4
- Thomas Landgraf — Dynamic Workflows / SPECLAN: https://www.youtube.com/watch?v=-m3QJKoQCgU
- Patrick Ellis — Daily workflows from technical founders: https://www.youtube.com/watch?v=hOqgFNlbrYE

### Proposed taxonomy

- `agentic-sdlc`
- `claude-code-plugins`
- `codex-skills`
- `cross-tool-agent-skills`
- `github-agent-workflows`
- `worktrees-parallel-agents`
- `spec-driven-development`
- `frontend-ai-design`
- `browser-testing-verification`
- `context-and-memory`
- `mcp-for-webdev`
- `wordpress-and-cms-ai-dev`
- `dev-workflow-creators`

## 5. Backlog: next concrete tasks

### B26-RESEARCH-01 — Reddit comment research adapter

Goal: make a safe no-key Reddit comment research lane for Hermes/Base2026.

Acceptance criteria:

- Small local script or skill wrapper for PullPush comment search.
- Small local script or skill wrapper for Arctic Shift comment tree fetch.
- Output format: JSONL with `thread_url`, `comment_id`, `parent_id`, `depth`, `score`, `created_utc`, `body`, `retrieved_at`, `source_api`.
- PII minimization option: hash or omit usernames by default.
- Rate limiting and cache folder.
- Document compliance guardrails.

### B26-PIPELINE-01 — staged P1 marketer creator expansion

Goal: add 8–10 P1 marketers as staged candidates, not public output.

Candidate set:

- Aleyda Solis
- Lily Ray
- Michael King/iPullRank
- Rand Fishkin/SparkToro
- Christopher Penn/Trust Insights
- Ethan Smith/Graphite
- Joy Hawkins/Sterling Sky
- Sarvesh Shrivastava
- Caleb Ulku
- Darren Shaw refresh only if needed

Acceptance criteria:

- Candidate source URLs verified.
- Platform type recorded: TikTok / YouTube / blog / newsletter / interview.
- Only candidates with compatible discoverable video feeds go into private intake config.
- Dry-run discovery/import before any apply.
- No public release until reviewed source text + Source Intelligence gates pass.

### B26-TAXONOMY-01 — add AI Marketing Agents & Skills category

Goal: create a category model and seed source list for agentic marketing skills/repos.

Seed repos:

- coreyhaines31/marketingskills
- ericosiu/ai-marketing-skills
- zubair-trabzada/ai-marketing-claude
- aitytech/agentkits-marketing
- indranilbanerjee/digital-marketing-pro
- BrianRWagner/ai-marketing-claude-code-skills
- thatrebeccarae/claude-marketing
- thearnavrustagi/marketmenow

Acceptance criteria:

- Repo metadata fields defined: stars/forks, pushed_at, license, compatibility, artifact types, maturity, risk notes.
- Star-history/anomaly caveat included.
- Category does not mix with human video creators; it is a separate source type.

### B26-TAXONOMY-02 — add WebDevLog / AI web-dev workflows category

Goal: track practical AI web-development workflows, not generic AI tool listicles.

Seed sources:

- Addy Osmani LLM coding workflow
- Matt Lambert Claude Code projects
- Samanvya Tripathi feature workflow
- Mikul Gohil Claude Code workflows
- Shawn Lin Agent Plugins
- Zen van Riel agentic engineer workflow
- AI with Avthar Claude Code setup
- Upstash Context7
- wshobson/agents
- obra/superpowers

Acceptance criteria:

- Fields for tools mentioned, commands/files, MCPs, GitHub workflow, worktrees, verification loops.
- Separate blog/video/source-code source types.
- Prioritize sources with concrete commands/workflows over generic opinion.

## 6. Do-not-do list

- Do not scrape Reddit through login/cookies/proxies as default.
- Do not store raw Reddit dumps or usernames in public repo.
- Do not bulk-import all creator candidates into public Base2026.
- Do not bypass existing Base2026 source-review/readiness/publication gates.
- Do not trust GitHub star counts alone; verify repo quality/activity before ranking.

## 7. Recommended immediate next step

Create a private staged candidate file for the P1 marketer batch and OSS/WebDevLog seed sources, then run only metadata/discovery dry-runs. After that, select the cleanest 3–5 sources for a first actual Base2026 intake/release pass.
