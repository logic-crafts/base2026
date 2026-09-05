# Experiment Card — one SEO next step

**Mode:** `measured_input` / `planning_only`<br>
**Evidence status:** `OBSERVED_EXPORT` / `SYNTHETIC_WORKED` / `UNKNOWN`<br>
**Plain-language conclusion:** [one sentence first; state `planning_only` if baseline is missing]
**Decision question:** [Should this existing page be refreshed, left, merged, or held?]

## Scope lock

- Target URL: `[one URL]`
- URL audit status: `[not audited when the URL is a placeholder]`
- Property / country / device / search type: `[same values in every row]`
- Before period: `[equal complete dates]`
- After period: `[equal complete dates]`
- Exact query ledger: `[3–10 exact query IDs and strings]`
- Controls: `[at least two same-intent, similar-age URLs]`

## Evidence ledger

| Type | Source ID or URL | Exact observation/claim | Limitation |
| --- | --- | --- | --- |
| `export_observation` | `[GSC row/filter]` | `[copy value or observation]` | `[scope/missing data]` |
| `creator_claim` | `[public source URL]` | `[attribute the claim]` | `Not independent verification` |
| `official_fact` | `[primary documentation]` | `[state the documented fact]` | `[version/date scope]` |
| `inference` | `[this card]` | `[cautious interpretation]` | `[competing explanation]` |

## Diagnosis and experiment

- Signals: `demand / rank / CTR-intent / seasonality / mixed / unknown`
- Competing explanations: `[at least two]`
- Baseline equations: `CTR = clicks / impressions`; `relative change = (post - pre) / pre`; `position change = post - pre`.
- One substantive change set: `[sources/dates, answer/title/H1/description, useful procedure/data, relevant links; log technical/schema changes separately]`
- Readback: `[28 complete days; 8–12 weeks when volume allows]`
- Causal-evaluation hold: `[LOW_SAMPLE, CONFOUNDED, missing controls, or other explicit condition]`
- Observational advice: `[one simple bounded corrective step; fewer than two controls does not block this]`
- Next human action: `[one owner-reviewed step]`

Label the result `descriptive only` unless the same query/date/filter cohort,
controls, sample, and competing explanations support a narrower statement.
Never write `verified`, `best`, `won`, `lift`, or a causal claim from this card
alone.
