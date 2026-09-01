# Base2026 plugins and integrations

Base2026 is usable from agent clients through its public remote HTTP MCP
endpoint. The compatible setup is deliberately small: add one read-only
server, then let the client discover the six public tools. No API key, OAuth
secret, local daemon or private package is required. The endpoint is protected
by a Cloudflare per-edge-identity rate limit; it fails closed if that binding is
not configured, so this local candidate is not a release-ready live service.

## Codex

```bash
codex mcp add base2026 --url https://base2026.dev/api/mcp
```

This uses Codex's remote Streamable HTTP MCP configuration. The command changes
the local Codex configuration; inspect it before sharing a machine or project.

## Claude Code

```bash
claude mcp add --transport http base2026 https://base2026.dev/api/mcp
```

For a project-local Claude Code configuration, the equivalent `.mcp.json`
shape is:

```json
{
  "mcpServers": {
    "base2026": {
      "type": "http",
      "url": "https://base2026.dev/api/mcp"
    }
  }
}
```

Do not add tokens or secrets to this file. Base2026 is public and currently
does not accept an authentication header.

## What an agent can actually do

After discovery, an agent can search public sources, resolve one source,
inspect a public creator or topic, request a deterministic topic signal, and
read the current public manifest. It cannot publish, edit, remove, moderate,
download media, read raw transcripts, access private leads or call the private
pipeline.

## Repository-local skill surface

The repository keeps human-readable integration guidance in this page and the
machine-readable contracts in:

- `/api-index.json` - endpoint and protocol inventory;
- `/data-dictionary.json` - public field and privacy dictionary;
- `/llms.txt` - concise agent context;
- `/mcp.html` - MCP request examples and limits;
- `/static/manifest.json` - dated static release dimensions.

For clients that support repository-local instructions, the copyable
instruction-only skill is `docs/integrations/base2026-public-mcp/SKILL.md` and
its explicit non-marketplace manifest is
`docs/integrations/base2026-public-mcp/integration-manifest.json`. These files
contain no credentials and do not install or mutate a client configuration.

These are documentation and public data surfaces, not an official Codex or
Claude marketplace plugin. A client that does not support remote HTTP MCP can
still use the public JSONL files or the regular search API with the same
attribution and privacy rules.

## Citation and operating rules

Keep the original creator URL with any claim. Add a Base2026 source page when
one is returned. Record whether a number came from the dated static manifest or
from a live D1 response. Do not infer coverage, trend strength, or private
context from a bounded result.

Read the [free Base2026 API guide](api.html) for the search endpoint and the
[source policy](source-policy.html) for correction, removal and attribution.
