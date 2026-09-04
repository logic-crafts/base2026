# Base2026 public tool activation measurement — decision receipt

Date: 2026-09-04
Status: reviewed local candidate; not deployed, pushed, merged, or connected to a remote D1/Analytics Engine dataset.

## Gap verified

The isolated candidate started from `origin/main` at `0341b8911`. The two
source runtimes dispatch `base2026:analytics` events, but the checked-in tool
templates had no listener or first-party sink. They also optionally pushed the
event name and properties into `window.dataLayer`, which was not bootstrapped
in either page and would have required an undisclosed third-party tag to do
anything.

The same gap was verified on the live site on 2026-09-04:

- `GET https://base2026.dev/tools/evidence-search/` returned HTTP 200. Its
  HTML referenced only `base2026-evidence-search.js`; it contained no
  `base2026:analytics`, `dataLayer`, `gtag`, `googletagmanager` or beacon
  listener/bootstrap marker.
- `GET https://base2026.dev/tools/source-diversity-check/` returned HTTP 200.
  Its HTML referenced only `base2026-source-diversity-check.js`; it contained
  the same absence of a listener/bootstrap/sink.
- The live JavaScript files contained the event dispatch and optional
  `dataLayer.push` code, proving emission without collection.
- `GET https://base2026.dev/api/analytics/event` returned HTTP 404 at
  2026-09-04 20:09:18 UTC. No live measurement write was attempted.

## Decision: Analytics Engine is the smallest justified sink

| Option | Current official limits/cost | Fit for this gap | Decision |
| --- | --- | --- | --- |
| Existing public D1 | [Workers Free includes 5M rows read/day, 100k rows written/day and 5 GB total](https://developers.cloudflare.com/d1/platform/pricing/). Paid pricing starts after 25B rows read/month, 50M rows written/month and 5 GB storage; storage is $0.75/GB-month. Writes include inserts/updates/deletes and index writes. | Durable and queryable, but needs a public migration/table, retention/cleanup policy, write-quota handling, and mixes operational measurement with the public evidence database. That is a larger privacy and migration surface than the event itself. | Do not use. |
| Workers Analytics Engine | [Workers Free includes 100,000 data points/day and 10,000 read queries/day](https://developers.cloudflare.com/analytics/analytics-engine/pricing/). Paid includes 10M data points/month and 1M read queries/month, then $0.25/additional million data points and $1/additional million queries. Cloudflare currently says it is not billing and that pricing is advance notice for coming months. [Writes are non-blocking and the dataset is created on first write](https://developers.cloudflare.com/analytics/analytics-engine/get-started/); current retention is three months and each Worker invocation may write at most 250 points ([limits](https://developers.cloudflare.com/analytics/analytics-engine/limits/)). | Native custom-event sink, no SQL migration, no scheduler, no extra service, and the bounded public event volume is far below the included allocation. A fixed index and four small blobs keep the schema low-cardinality. | Choose this. |
| Cloudflare Web Analytics | [Free privacy-first page/performance analytics](https://developers.cloudflare.com/web-analytics/about/) uses the `/cdn-cgi/rum` beacon ([collection model](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/)). The [FAQ says custom events and custom integrations to the endpoint are not available](https://developers.cloudflare.com/web-analytics/faq/). | Useful for page/performance trends, but cannot receive the two tool activation event families or their coarse properties. It would not close the observed gap. | Do not use. |

Analytics Engine is therefore the only option that closes the concrete
collection gap without a D1 schema migration, retention scheduler or external
analytics service. The candidate adds one `ANALYTICS` binding with dataset
`base2026_activation_v1`. The dataset will be created by Cloudflare on its
first successful write after a separately authorized deployment; this local
candidate does not create it remotely.

## Privacy and abuse contract

The only accepted routes are:

- `/tools/evidence-search/`
- `/tools/source-diversity-check/`

The only accepted event names are:

`evidence_search_viewed`, `evidence_search_submitted`,
`evidence_search_results_returned`, `evidence_source_record_opened`,
`evidence_original_source_clicked`, `evidence_search_completed`,
`evidence_search_empty`, `evidence_search_partial`, `evidence_search_error`,
`source_check_run`, `source_check_completed`,
`source_check_decision_recorded`, and `source_check_card_copied`.

The Worker writes exactly one Analytics Engine point with:

- `blob1`: allowlisted event name;
- `blob2`: allowlisted tool route;
- `blob3`: server-generated UTC hour bucket (`YYYY-MM-DDTHH:00:00Z`);
- `blob4`: canonical JSON object containing only event-specific coarse enum
  properties;
- `double1`: `1` event count;
- `index1`: fixed `base2026:activation:v1`.

No client timestamp is accepted. Unknown top-level fields, routes, events,
properties, property values, controls, overlong values and bodies over 4 KiB
are rejected. The browser sender caps a page at 24 events, uses same-origin
`POST` with `credentials: omit`, `keepalive`, `referrerPolicy: no-referrer`,
and catches every fetch failure. There is no CORS response and no read API.

The existing `MCP_RATE_LIMIT` binding is reused with a separate
`base2026:activation:v1:` key prefix and its current 60 requests/60 seconds
configuration. Cloudflare's edge IP is used only as an ephemeral rate-limit
key; it is never copied into a data point or application log. Missing or
failed rate-limit/Analytics Engine bindings fail closed at the endpoint, while
an Analytics Engine write exception returns `204` so the product UI remains
fail-open. No cookies, local/session storage, fingerprinting, authentication,
member data, private pipeline state, raw query, record/source ID, note,
referrer, user-agent or IP is persisted by this slice. Counts are aggregate,
best-effort product signals and must not be treated as proof of a human action
or reported as unique visitors.

The public privacy template, public privacy source and analytics page now
describe this boundary. The language uses “when enabled” because the
candidate is not a live deployment receipt.

## Exact implementation delta

- Added `cloudflare/base2026-worker/src/analytics.ts` with same-origin request
  validation, strict allowlists, 4 KiB body bound, ephemeral rate limit,
  server-hour bucket and fail-open Analytics Engine write.
- Added `templates/base2026-activation-measurement.js`, a shared listener and
  bounded first-party sender; both tool templates load it before their tool
  runtime.
- Removed the tool runtimes' optional `window.dataLayer` pushes. Removed the
  Evidence Search raw record ID, source type, referrer classification and HTTP
  status bucket from emitted analytics properties. Source Diversity position
  and count properties now use the canonical coarse names/buckets.
- Added the `ANALYTICS` Analytics Engine binding to
  `cloudflare/base2026-worker/wrangler.jsonc` and the generated type contract.
  Reused `MCP_RATE_LIMIT`; no D1 migration or new service/scheduler was added.
- Routed `POST /api/analytics/event` through the existing public Worker.
- Added focused Worker, Python/build, privacy-copy and static-artifact tests.
- Updated `docs/public-pages/03_PRIVACY_POLICY.md`,
  `templates/base2026-privacy.html`, `web/static/analytics.html`,
  `docs/project-memory/DECISIONS.md`, `NEXT_ACTION.md` and this receipt.

## Verification

The local candidate passed the following gates before commit:

- `npm run typecheck` in `cloudflare/base2026-worker`;
- `npm test` — 638 Worker tests passed;
- focused Python/build/tool/measurement suite — 42 tests passed;
- full Python suite — 200 tests passed;
- release builder fixture — artifact file count increased from 58 to 59 and
  includes the shared measurement asset byte-for-byte;
- JavaScript syntax checks, `git diff --check`, and the publication-boundary
  audit;
- `npm run wrangler:dry-run` was attempted and correctly held because this
  clean source checkout has no generated release directory at the configured
  `output/cloudflare-migration/base2026-enrichment-retirement-20260831-v2`
  path; it made no remote or local release mutation;
- focused tests prove valid points contain no rate-limit IP, raw IDs/referrer
  fields are rejected, missing/rate-limited requests do not write, and a write
  failure returns `204`.

No deployment, remote binding readback, Analytics Engine write/read, D1
migration, public release build in the production output directory, push,
merge, PR or external publication was performed by this task.

## Deployment and rollback risks

Deployment must add the `ANALYTICS` binding and the shared static asset in one
reviewed Worker/static artifact. If the binding is absent, the endpoint returns
503 and the browser silently drops events. If the HTML and shared asset are
from different releases, events remain uncollected; verify both live tool HTML
documents after deployment. The first accepted point auto-creates the dataset,
which is an external state change and therefore remains outside this task.

Before deployment, re-run the release builder against the exact reviewed public
input, generated type/dry-run checks and the public-boundary audit. After an
explicit deployment approval, verify the two HTML script tags, send one
non-sensitive canary event, and read back only aggregate event dimensions in
Analytics Engine. Do not put event payloads, request headers or dashboard
exports into Git. A rollback is the previous Worker/static artifact; it needs
no D1 rollback. If the candidate is rejected, remove the route/binding/shared
asset as one source change and leave the existing tools' public behavior
unchanged.
