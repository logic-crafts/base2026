# Base2026 Template Migration Discovery — 2026-07-12

## Status

**Planning/research only.** This document does not authorize a production generator change, export replacement, deploy, reindex, indexing submission, commit, or push.

The accepted Source Detail V2 local pilot is the visual reference for the first family. It is a reference implementation, not yet the corpus renderer.

## What was verified locally

- The generated static tree contains **4,129 HTML files** at the current local output: 1,693 source pages, 1,163 topic pages, 1,163 compare pages, and 110 other static/product routes.
- `scripts/generate-public-pages.py` currently owns legacy source/topic/compare/creator generation and its own `page_shell`.
- `scripts/generate-info-pages.py` owns Markdown-derived information routes.
- `scripts/generate-ai-recommends-solutions.py` already uses `alex_v4_static_shell.apply_alex_v4_shell`, while its page body is still renderer-specific Python HTML.
- The accepted Source Detail V2 is isolated in `scripts/generate-base2026-source-detail-v2.py` with isolated CSS/JS and Playwright QA. It must be treated as the body/component reference, not copied manually into generated pages.
- Existing public-source contracts are non-negotiable: `normal_public_card` is indexable, `provenance_archive_noindex` is visible but `noindex` and excluded from normal discovery surfaces, and `future_private_backlog` has no public artifact and must remain 404.
- The current worktree was already dirty before this discovery: `docs/project-memory/CURRENT_HANDOFF.md` and `scripts/generate-ai-recommends-solutions.py`. This discovery must not overwrite or absorb those changes.

## Research conclusion

### Recommended: add a small, adapter-based rendering layer inside the existing Python build

Use **Jinja2 + strict Python view models + the existing Playwright QA capability**, introduced page-family by page-family. This is not a new site framework and does not replace the data pipeline.

Why:

1. Jinja template inheritance gives one document skeleton and explicit page-family blocks instead of repeated f-string shells. Its `StrictUndefined` mode fails a build when a required value is missing rather than silently emitting broken HTML.
2. Pydantic is already available in the local environment and can validate normalized view models before rendering. It should become a declared, pinned dependency only when implementation begins.
3. Playwright already supports screenshot assertions and parameterized projects. It should remain the single browser/visual test stack; no duplicate BackstopJS setup is needed.
4. A full Astro/Eleventy migration would change the build language, data adapters, templates, asset handling, and release pipeline at the same time. That is a replatform, not a safe visual migration.
5. Parsing/re-skinning already-generated HTML with DOM transforms, regex, or LLM rewriting is explicitly rejected. It loses semantic ownership, is difficult to make deterministic, and is unsafe for SEO/status contracts.

### Explicitly not recommended now

| Option | Decision | Reason |
| --- | --- | --- |
| Regex/DOM patch over `web/static/**/*.html` | Reject | Generated HTML is output, not a source of truth; fragile across 4k routes and cannot safely preserve contracts. |
| One giant replacement of `generate-public-pages.py` | Reject | Couples every route family and makes rollback/diagnosis impossible. |
| Astro/Eleventy full migration | Defer/reject for this scope | Useful tools, but a needless replatform while data and release contracts are live. |
| BackstopJS alongside Playwright | Reject | Playwright provides the needed screenshot gate; a second stack adds configuration and maintenance without closing a gap. |
| Hand edits of generated output | Reject | Non-reproducible and overwritten by the next build. |

## Target architecture

```text
canonical public JSONL / Markdown / approved static data
                   |
             family adapter
        (source, topic, compare, creator, docs, solution)
                   |
          strict PageViewModel validation
                   |
        shared shell + reusable components/macros
                   |
           family template (Jinja2)
                   |
     isolated candidate output tree + route manifest
                   |
  contract / SEO / resource / visual / interaction QA
```

### Responsibilities

| Layer | Owns | Must not own |
| --- | --- | --- |
| Adapters | Convert existing source data into a typed page-specific view model | HTML layout decisions or release actions |
| Contracts | Required data, status, canonical/robots, schema, H1/title rules | Styling |
| Shared shell | Header, footer, assets, metadata slots, body/main framing | Family-specific content semantics |
| Components/macros | Source identity, platform actions, breadcrumbs, cards, disclosures, section primitives | Route selection or raw data lookup |
| Family templates | The approved visual grammar for a page family | Direct file I/O or admission policy |
| Build CLI | Deterministic selection and output directories | Deploy/reindex/indexation |
| QA | Compare candidate output against baseline contracts and approved visual snapshots | Modify production artifacts |

### Proposed source layout (implementation target, not created yet)

```text
scripts/base2026_renderer/
  contracts.py            # Pydantic models and invariant validators
  registry.py             # page-family and route registry
  build.py                # deterministic CLI
  adapters/
    sources.py
    topics.py
    compare.py
    creators.py
    info_pages.py
    solutions.py
  templates/
    base.html
    families/source_detail.html
    families/topic.html
    families/compare.html
    families/creator.html
    components/*.html
  qa/
    capture_contracts.py
    check_contracts.py
    check_resources.py
    visual.spec.mjs
```

`alex_v4_static_shell.py` is a migration dependency: its verified header/footer behavior should be extracted behind the shared shell interface, not repeatedly applied as a post-render HTML transform forever.

## Machine-readable route manifest

Before changing a renderer, add a read-only inventory command that produces a versioned candidate manifest. One record per route should contain:

```json
{
  "route": "sources/tiktok-video-7657749901186583816.html",
  "page_family": "source_detail",
  "admission_state": "normal_public_card",
  "current_generator": "generate-public-pages.py",
  "target_template": "families/source_detail.html",
  "canonical": "https://aggressorbulkit.online/knowledge/sources/tiktok-video-7657749901186583816.html",
  "robots": "index,follow",
  "expected_status": 200,
  "fixture_class": ["normal", "long-content"],
  "contract_digest": "sha256:..."
}
```

The manifest is the control plane for batching, QA, diff reporting, and rollback. It is derived from existing data and output, never manually maintained as a second content database.

## Contract snapshot and migration rule

For each existing route, capture a compact semantic baseline **before** visual replacement:

- route, expected status, canonical, robots, title, meta description, H1;
- JSON-LD types and source/creator attribution fields where applicable;
- required links and asset paths;
- page-family-specific structural requirements;
- prohibited items: leaked private source data, archive membership in normal listings/search/sitemaps, and a public future route.

Migration acceptance means:

- **semantic contract stays equal** unless a route-specific approved exception is recorded;
- **visual system changes intentionally** to the accepted family template;
- new visual screenshots become the regression baseline only after Alex approves that family.

Do not pixel-compare old and new pages: the design is intentionally changing. Compare old versus new for data/SEO contracts, then compare new versus approved-new screenshots for future drift.

## Safe rollout order

| Batch | Family | Initial scale / state | Gate before moving on |
| --- | --- | --- | --- |
| 0 | Inventory and baseline contracts | All routes, read-only | Route manifest reconciles to generated corpus; no unknown family/status. |
| 1 | Source Detail V2 | normal + archive; future remains absent/404 | Data/SEO parity for full source family; selected visual + interaction fixtures pass. |
| 2 | Topic and Compare | Separate templates, not a source-detail clone | Indexability and topic/compare admission rules pass. |
| 3 | Creator and index/list surfaces | Preserve card/search contracts | List/card semantics and links pass; search is unchanged. |
| 4 | Info/solution/static pages | One family at a time | Markdown/static data contracts and schema pass. |
| 5 | Search workspace and filters | Separate workstream | Runtime filters, result cards, hash state and Meilisearch contracts pass. |

Search, filters and result cards are frozen during batches 1–4. They must not become incidental side effects of the source-detail migration.

## Deterministic build interface

The future CLI should support selection, isolated output and verification; it must not deploy:

```bash
python3 scripts/base2026-render.py inventory --out .planning/base2026-template-migration/routes.jsonl
python3 scripts/base2026-render.py build --family source_detail --manifest ... --out .planning/base2026-template-migration/site
python3 scripts/base2026-render.py check --baseline ... --candidate ... --family source_detail
python3 scripts/base2026-render.py build --route sources/<id>.html --out .planning/.../one-route
```

Required behavior:

- deterministic ordering and content hashes;
- `--dry-run`, `--check`, `--family`, `--route`, `--out` and explicit manifest paths;
- candidate output is never `web/static/` by default;
- no auto-deploy, reindex, sitemap submission or Git action;
- full output replacement only after a separately approved parity report;
- rollback is the unchanged legacy generator/output plus a release symlink switch, not a manual reverse edit.

## QA matrix

### Every route (fast, deterministic)

- manifest coverage and duplicate-route detection;
- expected `200` / `404` behavior;
- canonical, robots, title/meta, H1 count and JSON-LD contract;
- internal link/resource resolution;
- prohibited private/archive/future leakage checks;
- reproducible build hash/diff check.

### Representative fixtures (browser)

For each family: shortest, typical, long/stress, archive/noindex or other special state, missing optional field, and a route near path-depth boundaries. Test at 1440, 1280, 390 and 320 widths for:

- screenshot snapshots after explicit visual approval;
- horizontal overflow, console errors and failed network requests;
- keyboard focus order, visible focus, disclosure behavior and reduced motion;
- header/footer and platform-action behavior;
- no stale external runtime brand-mark dependency.

## External references consulted

- Jinja template inheritance and template model: https://jinja.palletsprojects.com/en/stable/templates/
- Jinja environment and undefined-value handling: https://jinja.palletsprojects.com/en/stable/api/
- Pydantic data validation models: https://docs.pydantic.dev/latest/concepts/models/
- Playwright visual snapshot assertions: https://playwright.dev/docs/test-snapshots
- Playwright parameterized tests/projects: https://playwright.dev/docs/test-parameterize
- BackstopJS (evaluated and not selected because it duplicates the Playwright role): https://github.com/garris/BackstopJS

## Exact next safe action

Implement only **Batch 0**: a read-only inventory/manifest generator and contract-capture report against the existing output/data. Do not touch `scripts/generate-public-pages.py`, do not integrate the V2 pilot, and do not regenerate or deploy the production tree until the inventory report is reviewed.
