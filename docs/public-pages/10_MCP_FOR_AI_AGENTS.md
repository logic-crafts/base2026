# MCP for AI agents

Base2026 exposes a small public MCP server for AI agents that need attributable
short-form video evidence. It is free, no-key and read-only. The server wraps
the same public D1 search and projection tables as the website; it does not
open the private ingestion or review pipeline.

## Endpoint and transport

- MCP endpoint: `POST https://base2026.dev/api/mcp`
- Human guide: `https://base2026.dev/mcp`
- Transport: stateless Streamable HTTP with JSON responses.
- Current protocol negotiation: `2026-07-28` through `server/discover`.
- Compatibility: legacy `initialize` requests for supported 2025 protocol
  versions are accepted.
- Sessions: none. Server-sent events: none. DELETE: not supported.
- Authentication: none; the data is intentionally public.
- Abuse protection: the Worker uses the configured `MCP_RATE_LIMIT` binding at
  60 requests per minute per edge identity; if the binding is unavailable the
  route fails closed with `503` rather than serving an unprotected endpoint.

Modern clients should send `Content-Type: application/json`,
`MCP-Protocol-Version`, `Mcp-Method`, and the matching protocol metadata in
`params._meta`. A `tools/call` request also sends `Mcp-Name` matching
`params.name`. The endpoint validates these headers and rejects mismatches.

## Discover the server

```bash
curl -sS https://base2026.dev/api/mcp \
  -H 'content-type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  --data '{"jsonrpc":"2.0","id":"discover","method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
```

The response advertises a tools capability, protocol versions, server version,
cache guidance and the public-only instructions. `tools/list` returns the
deterministic tool schemas and read-only annotations.

## Tool set

| Tool | Arguments | Returns |
| --- | --- | --- |
| `search_sources` | `query`, optional `creator_handle`, `topic_id`, `platform`, `limit`, `offset` | Distinct public source summaries, bounded excerpts and attribution |
| `get_source` | `source_id` (also accepts an item, video or post alias) | Up to eight public passages and up to three applied evidence cards |
| `get_creator` | `handle` with or without `@` | Public creator metadata, topic counts and bounded source samples |
| `get_topic` | Exact `topic_id` | Public source/creator/insight counts and bounded samples |
| `get_topic_signal` | Exact `topic_id` | Deterministic evidence gate, not a trend ranking |
| `get_public_manifest` | No arguments | Current public D1 dimensions, endpoint links and policy flags |

## Call a tool

```bash
curl -sS https://base2026.dev/api/mcp \
  -H 'content-type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: search_sources' \
  --data '{"jsonrpc":"2.0","id":"search-1","method":"tools/call","params":{"name":"search_sources","arguments":{"query":"AI search","limit":5},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
```

Tool results contain both a text representation and `structuredContent`. Every
result carries a `public_boundary` object. When a source page is available,
the result preserves both the original source URL and the Base2026 canonical
page URL.

## Limits and errors

- MCP request bodies are capped at 64 KiB.
- The configured Cloudflare rate limit returns `429` with `Retry-After: 60`
  after the per-identity minute budget is exhausted.
- `search_sources` is bounded to 20 results and offset 1,000.
- Source lookup returns at most eight passages and three applied public cards.
- Creator and topic samples are bounded; counts are current D1 reads at call
  time, not a completeness claim about TikTok or the web.
- `get_topic_signal` reports `strong` only when source count is at least 5,
  creator count at least 2 and applied public insight count at least 3.
- Invalid JSON, unsupported versions, header mismatches, unknown methods and
  unsupported tools return structured JSON-RPC errors.

Agents should cite the original source URL and any returned Base2026 source
page. Do not present a bounded result as a real-time ranking, complete corpus,
full transcript or independent confirmation of the creator's claim. Every
production release verifies the rate-limit binding through Cloudflare version
readback and then exercises discovery and a bounded tool call against the live
endpoint.

## Privacy boundary

The handler reads only the public `DB` binding and never queries the Worker's
separate private bindings. It has no write tools, no raw captions or ASR, no
media access, no credentials, no inbox access and no publication actuator. See
the [source and content policy](source-policy.html) for correction and removal
boundaries.

For exact Codex and Claude Code commands, see [plugins and integrations](integrations.html).
