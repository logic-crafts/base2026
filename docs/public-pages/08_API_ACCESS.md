# Base2026 API & AI Access

Base2026 exposes the same reviewed public evidence to people and software. The
public layer is read-only: source metadata, short evidence passages, public
cards, topics, attribution, and canonical links.

Raw captions, raw ASR, media, private review packets, credentials, logs, and
private pipeline state are not part of the public API.

## Public entry points

- Human search workspace: `/workspace/`
- Public dataset landing page: `/dataset`
- Agent-readable context: `/llms.txt`
- Public data dictionary: `/data-dictionary.json`
- Public API index: `/api-index.json`
- Static sitemap index: `/sitemap.xml`
- Current D1 projection sitemap: `/sitemap-dynamic.xml`
- Public source index: `/sources/`

## Static public data

- `/static/manifest.json` — dated release counts and public export metadata.
- `/static/documents.jsonl` — public source/search documents.
- `/static/passages.jsonl` — public evidence passages linked to sources.
- `/static/insight_cards.jsonl` — reviewed source-backed insight cards.
- `/static/topic_signal_briefs.jsonl` — summaries for strong public topics.

Static files are best for reproducible offline analysis. Their manifest date
must be retained when citing counts.

The public dataset landing page links these distributions to the live D1 layer,
source policy, machine-readable catalog, and a copy-ready API query.

## Live search endpoint

The public UI and compatible integrations use a read-only,
Meilisearch-compatible Cloudflare Worker endpoint backed by D1 FTS5:

`POST /api/search/multi-search`

No browser key is required. The endpoint provides public search and filters;
it has no write, moderation, raw-transcript, media, credential, or private-data
route.

Example:

```json
{
  "queries": [
    {
      "indexUid": "base2026_public_tiktok",
      "q": "AI search",
      "limit": 5
    }
  ]
}
```

## Indexable public projection

Eligible automatic D1 projections receive stable public source pages at:

`/sources/tiktok-video-{numeric_video_id}`

These pages show only sanitized public excerpt cards and attribution. The
original creator video remains the canonical source for the full content.

## Good uses

- find creators and sources discussing a topic;
- compare repeated tactics across public sources;
- inspect source-backed SEO, GEO, AEO, and AI-search claims;
- build a research notebook from public JSONL;
- link an answer to a stable Base2026 page and the original source.

## Not supported

- raw transcript harvesting or video re-hosting;
- creator impersonation;
- private lead, inbox, review, or administrative access;
- public writes, corrections, or moderation through the search endpoint;
- replacing the original creator channel.

## Read-only MCP contract in the current candidate

The candidate adds `POST /api/mcp`, a stateless JSON-RPC surface over public D1.
It supports the current MCP discovery and legacy `2025-11-25` initialization
compatibility, with bounded calls to:

- `search_sources` for public source/evidence lookup;
- `get_source` for one canonical source record;
- `get_creator` for creator metadata and linked public sources;
- `get_topic` for a topic and its public source summary;
- `get_topic_signal` for a deterministic public topic signal;
- `get_public_manifest` for dated public release dimensions.

The route has no sessions, SSE, writes, moderation, private bindings or
credentials. Responses preserve attribution, original source links, canonical
Base2026 URLs and public/private policy flags. Request bodies, arguments and
returned evidence are bounded; raw captions, raw ASR, full private transcripts,
media, inbox data and pipeline control state are never returned.

The route is source-complete in this candidate but is not a deployment receipt.
Use the [MCP guide](10_MCP_FOR_AI_AGENTS.md) and
[integration guide](11_PLUGINS_AND_INTEGRATIONS.md) after the worker, static,
browser and publication-boundary release gates pass.
