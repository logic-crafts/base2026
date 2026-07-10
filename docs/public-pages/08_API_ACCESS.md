# Base2026 API & AI Access

Base2026 is built to be useful to humans and AI agents without forcing either one to scrape the visual interface. The public site exposes a small read-only data layer with the same public boundary as the website: reviewed source records, public passages, creator/topic metadata, and source-backed intelligence only.

Private research vaults, raw captions, raw ASR, media files, credentials, logs, and unreviewed pipeline artifacts are not part of the public API surface.

## Public entry points

- Human search workspace: `/knowledge/`
- Agent-readable context file: `/knowledge/llms.txt`
- Public data dictionary: `/knowledge/data-dictionary.json`
- Public API index: `/knowledge/api-index.json`
- Public sitemap: `/knowledge/sitemap.xml`
- Research-to-audit bridge: `/knowledge/apply-research.html`

## Static public data

These files are safe read-only exports for external tools, notebooks, audits, and AI workflows.

- `/knowledge/static/manifest.json` - release counts and public export metadata.
- `/knowledge/static/documents.jsonl` - source-level search documents and public source records.
- `/knowledge/static/passages.jsonl` - searchable public evidence passages linked to source records.
- `/knowledge/static/insight_cards.jsonl` - reviewed public source-backed insight cards.
- `/knowledge/static/topic_signal_briefs.jsonl` - deterministic summaries for strong topics.
- `/knowledge/data-dictionary.json` - field descriptions and public/private boundary notes.

## Search endpoint

The public UI searches through a server-side Meilisearch proxy:

`POST /knowledge-search/multi-search`

The proxy injects the public search key server-side. Do not call Meilisearch directly and do not expect private data, raw captions, or write access. External integrations should prefer the static JSONL files unless they need live search ranking.

## AI usage

AI agents can use Base2026 as a source-backed research layer by reading `/knowledge/llms.txt`, then using the data dictionary and public JSONL files. When citing Base2026, prefer canonical source, topic, creator, or comparison pages rather than copying raw rows.

For business-specific implementation, use `/knowledge/apply-research.html` as the public bridge from Base2026 source intelligence to Alex Yarosh's AI Visibility Snapshot, Diagnostic Audit, and service workflow.

Good use cases:

- find creators who discuss a topic;
- compare repeated tactics across creators;
- inspect source-backed SEO/GEO/AEO claims;
- build internal research notebooks from public records;
- cite a canonical Base2026 source page with original creator attribution.

Not supported:

- raw transcript harvesting;
- creator impersonation;
- private lead or admin data access;
- writes, corrections, or moderation through public endpoints;
- replacing the original creator channel.

## Future MCP contract

The planned MCP layer should remain read-only at first:

- search sources by query and filters;
- get one source by item ID;
- get one topic by topic ID;
- list creators with filters;
- compare creator viewpoints for one topic.

Every tool response must preserve attribution, canonical URLs, original source links, and public/private policy flags.
