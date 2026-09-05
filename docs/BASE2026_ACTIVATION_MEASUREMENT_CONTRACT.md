# Base2026 activation measurement contract

Status: current implementation contract, 5 September 2026.

This document describes the small, first-party activation signal used by the
three public tools. It is a product-usage diagnostic, not an identity,
audience, attribution, or conversion system.

## Scope and request boundary

The browser may send `POST /api/analytics/event` from the same origin only for
these exact tool routes:

- `/tools/evidence-search/`
- `/tools/source-diversity-check/`
- `/tools/source-backed-brief/`

The request contains an allowlisted event name, the exact route, an event-
specific map of coarse enum properties, and an optional top-level `context`
object. Unknown top-level fields, context keys, values, route/event pairs, and
raw properties are rejected with HTTP 400. An omitted `context` is accepted
for backward compatibility and normalizes to `cohort: unattributed` and
`campaign: none`.

## Context dimensions

The browser reads only the following fixed URL tags. It does not send the raw
URL, query string, referrer, or tag text as an event field:

- `b26_campaign`: exactly one of `none`, `evidence_pulse`, `worked_example`,
  `agent_workflow`.
- `b26_qa=1`: an optional operator-QA marker.

After omitted members receive their defaults, the server accepts only this
normalized pair matrix:

| cohort | campaign |
| --- | --- |
| `unattributed` | `none` |
| `experiment` | `evidence_pulse`, `worked_example`, or `agent_workflow` |
| `operator_qa` | `none`, `evidence_pulse`, `worked_example`, or `agent_workflow` |

Thus `{}` and an omitted context both mean `unattributed/none`; an explicit
`operator_qa` may omit its campaign and default to `none`. A partial
`experiment` context without a named campaign, or a named campaign without an
explicit `experiment`/`operator_qa` cohort, is inconsistent and rejected.
Duplicate or unknown `b26_campaign` values cannot claim an experiment, and
duplicate or unknown `b26_qa` values cannot claim operator QA. The other fixed
dimension may still be recorded when it is independently valid; invalid
context supplied directly to the endpoint is rejected.

When a valid tag is present, the browser may propagate only the normalized
fixed tags on same-origin navigation between the three exact tool routes. It
clears both destination tag names before appending the source's valid tags,
so a one-tag source cannot inherit a stale opposing tag. Existing public ID
parameters and fragments are preserved; external links are not changed. Tags
are not persisted in cookies, local storage, session storage, a fingerprint,
or any other browser state.

## Analytics Engine point layout

The Worker writes one point to the existing dataset `base2026_activation_v1`
with fixed `index1 = base2026:activation:v1` and `double1 = 1`. Blob positions
are one-based in Analytics Engine SQL:

| Position | Meaning | Current value/boundary |
| --- | --- | --- |
| `blob1` | event | exact event name for the route |
| `blob2` | route | one of the three exact tool routes |
| `blob3` | time bucket | server-generated UTC hour, `YYYY-MM-DDTHH:00:00Z` |
| `blob4` | properties | canonical sorted JSON of coarse, event-specific enum properties |
| `blob5` | cohort | `unattributed`, `experiment`, or `operator_qa` |
| `blob6` | campaign | `none`, `evidence_pulse`, `worked_example`, or `agent_workflow` |

The original four blobs are stable. Points written before the context
extension may have no `blob5` or `blob6`; those rows are historical
`legacy_unknown`, not retroactively `unattributed/none`. Queries should test
for null explicitly and keep that group labeled rather than silently treating
it as a tagged or human cohort.

## Query guidance and limits

For a report that excludes explicit operator QA while retaining historical
unknown rows for a separately labeled comparison, the conceptual filter is:

```sql
WHERE index1 = 'base2026:activation:v1'
  AND (blob5 IS NULL OR blob5 <> 'operator_qa')
```

For current attributed rows only, require both dimensions to be present and
filter the accepted values, for example `blob5 IN ('unattributed',
'experiment')`. For a named experiment, filter both `blob5 = 'experiment'`
and the desired `blob6` value. Always report route and event dimensions with
the time bucket; do not add up unlike workflows as if they were one funnel.

These points are best-effort aggregate signals with no read API in the public
product. They cannot establish a unique visitor, a returning visitor, a human
request, consent identity, a session, a conversion, or the completeness of
traffic. In particular, “not operator QA” is not equivalent to “human” and
does not prove that all traffic was measured.

## Privacy boundary

The event body contains no user ID, IP address, authentication data, text,
raw query, raw URL, referrer, record ID, source ID, or browser fingerprint.
The edge may use an IP transiently for rate limiting, but it is not written to
the point or an application database. The measurement is first-party and
non-blocking; a failed write must not change tool behavior. See the [public
privacy policy](/privacy) for the visitor-facing notice.
