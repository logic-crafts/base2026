---
name: base2026-organic-growth
description: "Use for Base2026 organic-growth work: evidence maps, indexable page or tool decisions, Outreach-informed topic selection, public distribution receipts, or GSC/Bing measurement. Applies only to this repository's public Base2026 surface, not generic client SEO, private ingestion, or unapproved external mutation."
metadata:
  scope: project
  version: "1.0.0"
---

# Base2026 organic growth

Treat Base2026 as an open, source-first evidence library for short-form expert video. The objective is a small set of useful, citable discovery surfaces, not maximum URL count or generic AI-written content.

## Start from current state

1. Read `AGENTS.md` and the current project-memory contract; prefer live HTTP, Cloudflare, D1, GSC, and Bing receipts over dated claims.
2. Read `.agents/product-marketing.md`, `docs/project-memory/CURRENT_HANDOFF.md`, `docs/project-memory/BASE2026_SEO_GEO_GROWTH_MAP_2026_08_28.md`, `docs/schemas/PUBLIC_JSONL_SCHEMA.md`, and the canonical Cloudflare manual. For indexation work, also read `docs/project-memory/BASE2026_GSC_BING_PREFLIGHT_2026_08_28.md`.
3. Inspect the actual public-data, release, page, sitemap, and test paths before editing. Do not edit generated output as the primary fix.
4. Read [page eligibility](references/page-eligibility.md) for page, tool, and markup choices and [receipts and states](references/receipts-and-states.md) for Outreach, distribution, GSC/Bing, and AgencyOS.

## Project rules

- Index a page only when its public evidence, intent, unique utility, and technical gates pass. Weak records may remain searchable or noindex; corpus size is not page eligibility.
- Use `free`, `best`, `confirmed`, `verified`, `top`, `API`, `MCP`, `plugin`, `checker`, `examples`, or `template` only when the visible page or working tool supports that exact modifier. Bounded criteria and a dated comparison are required for “best/top”; a receipt or live readback is required for “confirmed/verified.” Never use modifiers as filler.
- A free tool must work with real public data, solve one adjacent job, produce a reproducible output, and have a live, mobile, accessible route before its landing page is claimed indexable.
- Preserve the public/private boundary: only reviewed public excerpts, cards, metadata, and source attribution may be public. Raw media, captions/ASR, private packets, contacts, credentials, logs, and unreviewed claims stay private. Evidence and Outreach are separate collections.
- Preserve the Base2026 visual and generator authority when public HTML changes. SEO, schema, and sitemap checks do not replace visual acceptance.
- External actions require exact owner scope and receipts. A draft, queued/scheduled, moderation, attempted, or HTTP-200 state is not publication, indexing, traffic, or backlink proof.
- Separate fact, inference, and experiment. Report exact status, proof location, blockers/holds, changed files, and one concrete next action. Never claim Google/Bing indexing or AI citation from submission alone.

## Routing

- Page/tool build or eligibility: read `references/page-eligibility.md`.
- Outreach, distribution, measurement, or AgencyOS: read `references/receipts-and-states.md`.
- If the task crosses into generator/CSS/HTML/deploy, carry the product visual and release gates; do not widen scope to private pipeline or broad distribution.
