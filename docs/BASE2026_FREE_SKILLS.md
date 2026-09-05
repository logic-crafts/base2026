# Free Base2026 skills for useful SEO work

## SEO Experiment Planner

Turn a concrete SEO question and your own observations into one testable next
move. The skill helps your agent compare public source claims, check primary
guidance, preserve unknowns and produce an Experiment Card plus a measurement
worksheet. It is an open-source instruction-and-template pack, not another
hosted model or a promise of rankings.

No Search Console export yet? Ask for the first three checks in `planning_only`
mode. You still receive a useful next step; missing traffic, cause, and outcome
remain unknown. A placeholder URL is not presented as an inspected page.

**Try this task:** “This content page lost clicks. Help me distinguish demand,
CTR and ranking changes, choose a substantive refresh, and define how we will
measure it.” See the complete [synthetic worked example](examples/content-refresh-experiment.md),
[measurement CSV](examples/content-refresh-measurement.csv) and
[exact-query ledger](examples/content-refresh-queries.csv).

### Install the skill

Review [the skill files](../.agents/skills/base2026-seo-experiment-planner/SKILL.md)
before installing. From the project where you want to use it, choose your agent:

```bash
npx skills add offflinerpsy/base2026 --skill base2026-seo-experiment-planner --agent codex
npx skills add offflinerpsy/base2026 --skill base2026-seo-experiment-planner --agent claude-code
```

Run only the command for the client you use; do not install all repository
skills by default. The optional installer is the open-source
[Vercel Skills CLI](https://github.com/vercel-labs/skills). Its
[telemetry documentation](https://skills.sh/docs/cli) explains that installation
telemetry can be disabled with `DISABLE_TELEMETRY=1`.

Without an installer, copy the complete `base2026-seo-experiment-planner` folder
from `.agents/skills/` into your project's `.agents/skills/` for Codex or
`.claude/skills/` for Claude Code. Keep its resources together and do not
overwrite an existing skill of the same name without inspecting it first.

### Connect the optional source library

The pack can work from supplied exports and citations. To add Base2026 public
source retrieval, use its existing no-key read-only MCP server:

```bash
codex mcp add base2026 --url https://base2026.dev/api/mcp
claude mcp add --transport http base2026 https://base2026.dev/api/mcp
```

Use your client's normal configuration/reload workflow. Installing a skill does
not silently grant MCP access. Discovery and exact available tools are described
in the [public MCP guide](public-pages/10_MCP_FOR_AI_AGENTS.md).

### Ask for a result

In Codex:

> Use $base2026-seo-experiment-planner to plan one content-refresh experiment.
> Use the supplied page/query/date comparison. Keep missing volume and causal
> effects unknown. Return an Experiment Card and a CSV I can fill after the change.

In Claude Code, invoke `/base2026-seo-experiment-planner` with the same task or
ask for the skill by name. Provide only exports you are authorized to use.

The result should include the actual decision, competing explanations,
attributable sources, input/filter limitations, one bounded change, a baseline,
comparison, observation window and next decision. No site changes or publication
are authorized by the pack itself.

### What is free—and what this does not do

- The skill, templates and public Base2026 source lookups require no Base2026
  subscription or signup. The public API/MCP is bounded and rate-limited.
- You bring your own compatible AI agent. Its provider subscription, token
  charges or third-party data-service charges are separate.
- No keyword volume, ranking forecast, live site audit or AI-citation monitor
  is fabricated when the required service/data is unavailable.
- Private GSC exports stay in the authorized local task; they are not uploaded
  to Base2026. The MCP receives only deliberately selected non-sensitive public
  research queries/IDs, never a raw client export.
- A creator's excerpt is a claim with provenance, not independent validation.
  The Apache-2.0 license covers this code/instruction pack, not source creators'
  underlying content.

This is a community-distributed Agent Skills pack, not an official OpenAI or
Anthropic marketplace plugin. The [Agent Skills format](https://agentskills.io/specification)
is portable; client behavior and permissions remain client-specific.

Useful output or a reproducible bug is welcome through the repository's normal
feedback channel. Do not attach credentials, client exports or private source
data to a public issue. A new real task is more useful feedback than a review
written without using the product.
