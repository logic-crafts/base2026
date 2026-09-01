---
name: base2026-public-mcp
description: Use the Base2026 public MCP endpoint for bounded, attributable short-form video evidence research.
---

# Base2026 public MCP

Use the remote MCP server at `https://base2026.dev/api/mcp` when a task needs
public short-form video evidence about SEO, GEO, AEO, AI search, local
visibility, schema, content or related topics.

## Tool routing

- Start with `search_sources` for a short query and a small `limit`.
- Use `get_source` to inspect bounded passages and applied evidence cards.
- Use `get_creator` or `get_topic` only with an exact public handle or topic ID.
- Use `get_topic_signal` for the deterministic evidence gate; do not call it a
  real-time trend score.
- Use `get_public_manifest` when a current public D1 dimension is needed.

## Evidence rules

Preserve the original creator source URL and any returned Base2026 source page.
Treat results as a bounded public corpus, not complete coverage or independent
verification of a creator claim. Distinguish live D1 counts from dated static
manifest counts.

## Privacy rules

This server is read-only. Never ask it for raw captions, raw ASR, full private
transcripts, media, credentials, private review packets, inbox data or pipeline
control state. Do not invent write, moderation, removal or publication tools.

The file is an instruction-only repository skill for clients that support local
agent guidance. It is not an official Codex or Claude marketplace plugin.
