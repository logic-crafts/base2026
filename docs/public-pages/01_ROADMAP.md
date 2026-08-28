# Base2026 Roadmap

## Positioning

**Base2026 is an open public-source intelligence layer that turns short-form
expert videos into attributed, searchable evidence for SEO, GEO, AEO,
AI-search, and research workflows.**

It is not a video host, transcript dump, generic SEO suite, or social-listening
dashboard. The useful unit is a short public evidence card that preserves the
creator, original source, topic, date, and correction path.

## What is live

- The complete public product runs on Cloudflare at `base2026.dev`.
- Cloudflare Workers serves the site, read-only API, forms, and public search.
- Public D1 with FTS5 powers the search workspace without a browser API key.
- Public JSONL exports, a data dictionary, API index, `llms.txt`, source pages,
  topic pages, and creator pages provide human- and machine-readable access.
- The project is open source and documents its public/private boundary.
- A private Cloudflare pipeline discovers bounded public sources, captures
  eligible media, creates reviewed evidence, and automatically projects only
  a small sanitized public record into the public search layer.

Live counts change as the corpus grows. The public manifest and API are the
machine-readable sources for current data; dated roadmap snapshots are not.

## How the cloud workflow works

1. Cloudflare discovers candidate public videos from an approved creator list.
2. Private D1 rejects duplicates and records durable source and job state.
3. Bounded Browser Rendering and a restricted Container acquire eligible
   public media; private R2 stores temporary artifacts.
4. Workers AI transcribes and helps select short source-backed evidence.
5. Queues and Workflows move each job through retries, budgets, retention, and
   validation with durable receipts.
6. A strict automatic-publication policy permits only one to three sanitized
   excerpt cards to cross the private/public boundary.
7. A Cloudflare service binding sends that exact projection to the public
   Worker, which writes it to public D1 FTS5 and verifies the result.

Raw media, raw ASR, full private transcripts, credentials, logs, and private
review packets are never part of the public website or API.

## What is technically distinctive

- The runtime is cloud-native and does not depend on a development computer.
- D1 is the durable source of truth; Queues and Workflows are replay-safe
  transport and orchestration, not competing state stores.
- Public projection uses exact identities and receipts, so a retry cannot
  silently create a different public record.
- R2 artifacts have bounded retention and deletion receipts.
- The public database has no raw-media or private-packet schema.
- D1 FTS5 provides fast edge search without requiring a live LLM for every
  visitor query.
- Included Cloudflare services and hard software budgets keep the operating
  model practical for an open startup while failing closed at its limits.

## Current limitations

- The corpus is curated and bounded; it is not a complete copy of TikTok or the
  web.
- Platform access changes can pause discovery or acquisition.
- Automated transcription and evidence selection can be wrong; source links,
  correction, removal, and suppression paths remain essential.
- Public AI-generated answers are not live. The current product retrieves
  source-backed records and excerpts.
- Creator claims, public change history, richer usage analytics, and a stable
  public MCP interface remain unfinished.

# Development sequence

## Phase 1 — Public trust foundation

**Status:** Live

Methodology, source policy, privacy, source attribution, correction/removal,
open-source documentation, and the public/private boundary are live.

## Phase 2 — Cloud ingestion and evidence pipeline

**Status:** Live, monitored

Cloud discovery, bounded acquisition, private R2/D1 storage, Workers AI,
Queues, Workflows, automatic excerpt-card projection, retention, and receipts
are operational. Ongoing work focuses on source-platform resilience, quality,
and budget efficiency.

## Phase 3 — Indexable evidence graph

**Status:** Live, monitored

Search, source/topic/creator pages, canonical URLs, sitemaps, structured data,
internal links, static data, dynamic D1 projection pages, and read-only API
access are live. Google Search Console and Bing Webmaster Tools are connected.
Current work monitors discovery and keeps counters and projections synchronized.

## Phase 4 — Creator and rights controls

**Status:** In progress

Correction and removal paths are live. Creator claims, automated request
tracking, suppression receipts, and a public change log remain planned.

## Phase 5 — Developer and research distribution

**Status:** Live foundation, in progress

Public JSONL, data dictionary, API index, `llms.txt`, D1 search API, and GitHub
source are live. Next: versioned public-safe sample datasets, reproducible query
examples, release notes, and a read-only MCP contract.

## Phase 6 — Sustainable open product

**Status:** Research

Potential support, partnership, and premium research models will be tested only
after repeated public usage. They must preserve source attribution, correction
rights, transparent boundaries, and useful free access.

## Now

- Monitor Google Search Console and Bing Webmaster Tools for discovery and
  indexing changes.
- Keep public counters synchronized to dated D1/manifest dimensions.
- Publish a small set of strong source-backed topic evidence maps.
- Keep dynamic projection pages, canonicals and sitemaps release-tested.

## Next

- Versioned public-safe dataset sample and API quickstart.
- Dated corpus changelog and manifest diffs.
- Better creator/correction workflows.
- Read-only MCP tools for source, topic, creator, and comparison lookup.

## Later

- Citation-aware answer experiments with visible sources and strict limits.
- Carefully reviewed additional source platforms.
- Sustainability experiments driven by observed use, not speculative pricing.

# What this roadmap proves

The roadmap is a public sequence, not a promise of rankings, AI citations, or
universal coverage. Base2026 grows by making a narrow evidence corpus easier to
find, verify, cite, correct, and reuse.
