---
name: base2026-seo-experiment-planner
description: "Plan one useful SEO content-refresh next step with an optional GSC CSV and bounded Base2026 public evidence. Without analytics, start with practical planning-only checks; return one Experiment Card and measurement CSV, not fabricated keyword volume or publication actions."
metadata:
  scope: "public Base2026 skill"
  version: "1.0.0"
---

# Base2026 SEO experiment planner

Use this skill when an SEO practitioner has an existing page, a supplied Google
Search Console CSV, and a decision about whether to refresh, leave, merge, or
hold it. Produce one fixed-cohort experiment with one substantive change,
matched controls, and a later readback. This is not an article writer,
keyword-volume generator, ranking forecaster, or publishing agent.

Lead with a short plain-language conclusion. For a novice, show the three first
checks in the planning mode below before technical caveats. Never call a
placeholder URL audited or imply that a page was inspected when it was not.

## Inputs and output

Prefer a local GSC CSV or pasted export rows for one target URL, its page
intent, and the proposed user/business action. Capture property, country,
device, search type, period dates, and target/control roles when supplied.
Accept optional public Base2026 source IDs, topic IDs, or a suspected problem.
If no GSC baseline is supplied, continue in `planning_only` mode: return one
card with baseline, volume, and observed signals as `UNKNOWN`, list the exact
inputs still needed, and provide a change/control/readback plan without filling
results. Never request private transcripts, raw captions, credentials, contact
lists, client vaults, or hidden analytics exports.

Return exactly one `ExperimentCard` and one measurement CSV (or clearly marked
CSV block). With an export, the card includes the decision question and scope;
an exact 3–10 query cohort; equal pre/post periods; target plus at least two
same-intent controls; observed signals and competing explanations; a source
ledger; one substantive change; baseline/readback; stop/hold conditions; and
one next human action. Without an export, retain the structure but mark the
baseline, cohort, and measured signals `UNKNOWN` and call the card
`planning_only`, not measured or validated. Use the bundled schemas in
[`assets/measurement-template.csv`](assets/measurement-template.csv) and
[`assets/query-ledger.csv`](assets/query-ledger.csv).

Preserve supplied values as `OBSERVED_EXPORT`. Use `SYNTHETIC_WORKED` only for
an explicitly requested illustration. Missing values remain `UNKNOWN`, never
zero by inference.

## Planning-only first checks

When the CSV or page URL is missing, give useful planning advice immediately:

1. Confirm the real target URL and one-sentence search intent; a placeholder is
   a planning label, not an audited page.
2. Lock the exact query/date/property/country/device/search-type inputs that
   will be needed; baseline capture can happen later and must not gate simple
   corrective advice.
3. Check the obvious audience-facing change to test first (answer, title/H1,
   snippet fit, useful procedure, or relevant internal path) and state what
   evidence would change that recommendation.

Call the card `planning_only` with baseline and volume `UNKNOWN`, list the
missing inputs, and provide the bounded change/readback plan. `HOLD` means hold
causal/experiment evaluation; it does not mean the practitioner cannot receive
simple corrective advice. If fewer than two controls are available, label that
advice `OBSERVATIONAL_ONLY` and keep causal evaluation held rather than
refusing the plan.

## 1. Lock and inspect the export

Read the CSV locally; do not upload it. Confirm one target URL, two equal
complete periods, identical property/country/device/search-type filters, and
query-level rows. If only page totals exist, state that query demand cannot be
separated from page-level change. Recalculate `CTR = clicks / impressions`,
retain Search Console position as an aggregate signal, and do not silently
repair malformed dates, duplicates, or mixed scopes.

When the export is absent, do not stop at a refusal: use the bundled blank
schemas, set every baseline/volume/result field to `UNKNOWN`, list the missing
URL, query, date, filter, metric, and control inputs, and return a useful
planning-only card. Do not call that card a validated measured plan.

Create or preserve an exact-query ledger. Use the same query IDs and strings
for target and every control in both periods. Do not change the cohort after
seeing a decline. Search volume absent from the export is `UNKNOWN`; never
fabricate it from a keyword phrase.

## 2. Retrieve bounded public evidence

Start with one or two short public search terms, such as `internal linking`.
If that returns zero, simplify to a broader one- or two-term query before
trying a distinct symptom or competing explanation. Count discovery and all
search/tool calls in a hard cap of five total public MCP requests. Call
`search_sources` with `limit <= 5`; use `get_source` only for returned exact
public IDs that materially support the card. Do not fan out across
creators/topics, and stop when one usable source-backed action is supported. A
no-result or missing field is `UNKNOWN`, not evidence that no source exists.
Read [`references/mcp.md`](references/mcp.md) before using the endpoint.

Classify every evidence item: `export_observation` (supplied GSC value),
`creator_claim` (attributed Base2026 passage/card), `official_fact` (named
primary documentation), `inference` (cautious interpretation), or `unknown`.
Creator/practitioner claims remain attributed; scores, cards, and repetition
do not make them facts. For Google platform rules or diagnostics, cite official
Google documentation when available.

## 3. Diagnose before proposing the change

Compare target and controls separately for clicks, impressions, CTR, position,
and any explicitly defined qualified action. Use:

```
relative change = (post - pre) / pre
position change = post - pre  # positive is numerically worse
```

List at least two competing explanations. A simultaneous impression and
position decline is mixed until query, seasonality, technical, and control
evidence narrows it. A stable trend proxy does not prove seasonality; a click
decline alone does not prove demand loss.

The change must be substantive and audience-led: update stale facts with linked
primary sources and dates; improve answer/title/H1/description for the fixed
cohort; remove filler; add a real procedure or approved-data table; and repair
relevant internal paths while retaining URL/canonical. Log content, link,
image, schema, and technical changes separately. Do not recommend a date-only
rewrite or word-count target as the experiment.

## 4. Readback and fences

Use a fixed post-period readback after 28 complete days, then 8–12 weeks when
volume allows; these are working cadences, not guarantees. Mark
`LOW_SAMPLE — descriptive only` below 100 cohort impressions or 20 clicks in
either period. Mark `CONFOUNDED — do not infer effect` for algorithm events,
migrations, outages, seasonality events, query/date/filter changes, control
edits, or other material overlap. Hold causal/experiment evaluation with fewer
than two usable controls or an unreconciled input, but provide simple
`OBSERVATIONAL_ONLY` corrective advice when it is safe and obvious. State what
would change the decision and the next human action. Never call a result
causal, verified, best, won, indexed, traffic, or lift without separate
evidence and readback.

## Safe boundary

Keep GSC rows local. Public MCP requests contain only short queries or exact
public IDs, never CSV contents, private URLs, notes, or client identifiers. Use
only the unauthenticated read-only Base2026 MCP; do not invent write, upload,
moderation, publication, analytics, or credential tools. DataForSEO is optional
only when an already-authorized connector or supplied result exists; never
purchase, spend, or fabricate volume/cost data, and keep it separate from GSC
and Base2026 evidence. Do not publish, deploy, submit, send, schedule, or emit
analytics events. Preserve attribution and rights limits; exclude raw captions,
full transcripts, media, private review text, and unreviewed claims.

## Resources

- [`references/mcp.md`](references/mcp.md): verified endpoint, discovery,
  tools, bounds, boundary, and citation rules.
- [`assets/blank-experiment.md`](assets/blank-experiment.md): compact card
  template for the human handoff.
- [`assets/measurement-template.csv`](assets/measurement-template.csv) and
  [`assets/query-ledger.csv`](assets/query-ledger.csv): bundled synthetic/blank
  schemas that work after standalone installation.
- Reuse the repository’s dependency-free
  [`public evidence workflow`](https://github.com/offflinerpsy/base2026/tree/main/examples/public-evidence-workflow)
  and its existing bounded `evidence_pack.py` for exact public IDs when a
  checkout is available; do not create or install a second Python MCP client.
