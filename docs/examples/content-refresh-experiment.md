# Worked content-refresh experiment

This is a small, reusable SEO measurement packet. It turns one authorized
Search Console export into a refresh, leave, merge, or hold decision for one
existing URL. The worked values are `SYNTHETIC_WORKED`: they are not Base2026,
client, ranking, traffic, conversion, or causal results. The goal is a useful
human decision aid, not another generic article or a promise of lift.

## The filter lock

Start with the companion [exact-query ledger](content-refresh-queries.csv).
Each row is one exact query string in a fixed 3–10-query cohort. In a real run,
copy the strings from the authorized Search Console export; do not replace them
with a new keyword list after looking at the result. Use the same cohort ID,
property, country, device, search type, and two equal complete date periods for
the target and every comparison page. The measurement file has one row per
page-period and uses the same cohort label.

The ledger prevents spreadsheet drift: a page total from one date range or
device mix must not be compared with a different query set in the next period.
For a human consultant, that makes the handoff legible: the observed signal can
be described as demand/impression change, rank change, CTR/intent, seasonality,
mixed, or unknown, with the exact next action and readback date attached.

Synthetic exact-query example:

| Query ID | Exact query | Class | Before | After |
| --- | --- | --- | --- | --- |
| q01 | `internal linking strategy` | non-brand | 2026-05-01–05-28 | 2026-06-01–06-28 |
| q02 | `how to improve internal links` | non-brand | 2026-05-01–05-28 | 2026-06-01–06-28 |
| q03 | `internal link audit` | non-brand | 2026-05-01–05-28 | 2026-06-01–06-28 |
| q04 | `internal linking best practices` | non-brand | 2026-05-01–05-28 | 2026-06-01–06-28 |

## Measurement method

Export clicks, impressions, CTR, average position, and (if separately defined)
qualified actions. Record page age, canonical/index status, known sitewide
changes, content changes, and unknown values. Add at least two same-intent,
similar-age controls. Exclude or flag migrations, noindex periods, outages,
manual actions, algorithm events, seasonality events, and concurrent control
edits where known.

Use:

`CTR = clicks / impressions`

`relative change = (post - pre) / pre`

`position change = post - pre` (positive means a worse numerical position)

The synthetic target shows clicks 240 → 156, impressions 12,000 → 11,200,
CTR 2.00% → 1.39%, average position 6.8 → 8.4, and qualified actions 11 → 8.
The two synthetic controls remain roughly stable. That combination is a mixed
rank plus snippet/intent hypothesis; it is not proof of demand loss, seasonality,
or a causal effect. The worksheet calculates clicks −35.0%, impressions −6.7%,
CTR −0.61 percentage points, and position +1.6 (worse). A small cohort or
unresolved event should be labelled `LOW_SAMPLE — descriptive only` or
`CONFOUNDED — do not infer effect`.

## Substantive change and readback

If the decision is `REFRESH`, record one bounded change set: replace stale
facts/examples with linked primary sources and a dated note; rewrite the answer,
title, H1, and description for the fixed cohort; remove filler; add a procedure
or table from approved data; repair relevant internal paths; retain the URL and
canonical; and log content, links, images, schema, and technical changes
separately. Do not infer that a date-only rewrite is useful.

Repeat the same URL, exact queries, filters, controls, and period-length rule
after 28 complete days, then at 8–12 weeks when volume allows. Compare clicks,
impressions, CTR, position, and qualified actions separately. This is descriptive
readback, not an experiment with guaranteed attribution; record competing
explanations and stop or hold when the evidence is too small or confounded.

## Source limits and public demonstration draft

The packet retains the reviewed [Outreach finding
XGS-20260803-016](https://x.com/thinking_slow/status/2036398383267529081) only
as a source for the query-demand/usefulness-gap hypothesis and the need for a
substantive, source-backed update with matched controls. Its score and wording
do not prove a traffic or ranking outcome. Metric definitions and diagnostic
limits come from [Google Search Console metric definitions](https://support.google.com/webmasters/answer/7042828?hl=en),
[Google’s Search Console task guide](https://support.google.com/webmasters/answer/17010961?hl=en),
[Google’s traffic-drop debugging checklist](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops),
and [people-first content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content).
The existing [Base2026 content-freshness guide](https://base2026.dev/topics/content-freshness)
is a workflow aid, not outcome verification.

Native public demonstration draft — **DO NOT SEND**:

> Base2026 worked example: one page’s fixed Search Console cohort fell in
> clicks, but diagnosis needs impressions, position, CTR and seasonality—not a
> date-only rewrite. Try the free source search:
> https://base2026.dev/tools/evidence-search/?b26_campaign=worked_example
>
> — Alex Yarosh · Base2026. Synthetic example; not a client result or promise.

Use the [measurement CSV](content-refresh-measurement.csv) and [query CSV](content-refresh-queries.csv)
as a portable example. They contain no private paths, credentials, raw source
vault, or real client record.
