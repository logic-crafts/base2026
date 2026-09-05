# Base2026 public MCP reference

Use this reference only when the experiment needs bounded public source
research. The endpoint is a public, stateless, unauthenticated, read-only
Streamable HTTP JSON service. It is not a private corpus API, upload endpoint,
publisher, or truth/consensus engine.

## Verified endpoint and discovery

- Endpoint: `POST https://base2026.dev/api/mcp`
- Human guide: <https://base2026.dev/mcp>
- Protocol negotiation: `2026-07-28` via `server/discover` (legacy supported
  versions are documented by the public contract).
- Required request headers: `Content-Type: application/json`,
  `MCP-Protocol-Version`, `Mcp-Method`; `tools/call` also sends `Mcp-Name`.
- Include matching protocol metadata in `params._meta`.
- Authentication: none. Sessions and server-sent events are not needed.

Discovery is a read-only JSON-RPC request with method `server/discover`.
Confirm the response is complete and advertises the requested protocol before a
tool call. A discovery failure is a hold, not a reason to guess an endpoint or
retry broadly.

Use this exact modern discovery request. The protocol version is required in
both the header and `params._meta`; omitting the nested metadata can return
HTTP 400.

```bash
curl -sS https://base2026.dev/api/mcp \
  -H 'content-type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  --data '{"jsonrpc":"2.0","id":"discover","method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
```

## Tool routing

| Tool | Use in this skill |
| --- | --- |
| `search_sources` | Short intent/symptom/change queries; set `limit <= 5`. |
| `get_source` | Exact public IDs returned by search, only when a full bounded passage/card is needed. |
| `get_creator` | Avoid unless the user supplies an exact public handle and it materially resolves attribution. |
| `get_topic` | Avoid unless the user supplies an exact public topic ID and it materially resolves context. |
| `get_topic_signal` | Do not treat as trend or ranking data; use only for a named evidence gate. |
| `get_public_manifest` | Use only when a current public dimension is directly relevant; it is not demand evidence. |

The planner itself caps the whole retrieval at five public requests. It starts
with one or two short search terms and broadens only when a result is empty. A
`search_sources` response is bounded;
missing passages, cards, counts, or dates become explicit unknowns. Never fan
out into a corpus crawl.

Use this exact modern `tools/call` shape for the first short query. `Mcp-Name`
must match `params.name`, and the same nested protocol metadata is required.

```bash
curl -sS https://base2026.dev/api/mcp \
  -H 'content-type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: search_sources' \
  --data '{"jsonrpc":"2.0","id":"search-1","method":"tools/call","params":{"name":"search_sources","arguments":{"query":"internal linking","limit":5},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
```

## Public boundary and attribution

The public MCP exposes only reviewed public metadata, source links, bounded
passages, and applied public cards. It does not expose raw captions, raw ASR,
media, full private transcripts, credentials, inbox data, private review
packets, or write operations. Preserve both the original source URL and the
Base2026 source page URL when returned.

Report public passages/cards as attributed `creator_claim` evidence. A bounded
result is not complete coverage, independent confirmation, a real-time trend,
a ranking, a causal result, or permission to publish. Cite the original source
and any Base2026 page in the Experiment Card; keep missing fields as unknowns.

For a dependency-free repeatable fetch of exact public IDs, reuse the
repository’s [public evidence workflow](https://github.com/offflinerpsy/base2026/tree/main/examples/public-evidence-workflow).
It performs discovery, uses `get_source`, caps IDs at eight, and fails closed
on private-field or boundary drift. It is an existing repository example, not a
package to install or a replacement client to create.

The complete project contract is in the [public MCP integration skill](https://github.com/offflinerpsy/base2026/blob/main/docs/integrations/base2026-public-mcp/SKILL.md)
and the [public agent documentation](https://github.com/offflinerpsy/base2026/blob/main/docs/public-pages/10_MCP_FOR_AI_AGENTS.md).
