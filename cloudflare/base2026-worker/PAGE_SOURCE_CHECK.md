# Page Source Check v1

This is a free, no-signup **supplied HTML check**, available at
`/tools/page-readiness/` when its three assets are included in a release.
It is a security fallback for the proposed arbitrary-URL page check. It does
not retrieve or attest to the live page. The original live-URL acceptance
remains incomplete.

## Job and inventory

Evidence Search, Source Diversity Check and Source-backed Brief work over the
admitted Base2026 corpus. WordPress Evidence Sidebar inserts attributed research
into an editor. None checks the HTML of a user's own page. This independent
module helps someone identify a concrete source correction and compare a fresh
copy after editing, without accounts, D1, models or a new service.

The main input is pasted HTML or a local file. An optional HTTPS URL supplies
context for relative links/canonicals. It is not an instruction to fetch.
The editable fictional heating-page example has an empty title; the corrected
example adds a descriptive title. Its finding changes from Review to Observed.
The UI compares only the last successful result for the same URL context in
the current tab. A comparison does not prove a live-site change.

## API and deterministic result

`POST /api/page-readiness/v1`, `Content-Type: application/json`:

```json
{"url":"https://example.com/service","html":"<!doctype html><html><head><title>Service name</title></head><body><h1>Service name</h1></body></html>"}
```

`url` is optional. Only `url` and `html` are accepted. HTML is never returned as
markup. Success returns `mode: supplied_source`, timestamp, provenance, facts
and checks with `id`, `state`, `observation`, `why`, `action`, `recheck`.
States are Observed, Review or Unknown; there is no score or whole-page pass.

Checks cover title elements in the head, source H1 elements, named robots meta,
canonical URL syntax, HTTP(S) anchors and JSON-LD syntax. Native HTMLRewriter is
an inert streaming parser, not a browser or HTML conformance validator. Source
H1/link counts may include hidden or template content. Character entities in
text observations retain their source spelling. Metadata text display is
bounded and marked when shortened. Oversized directive attributes are rejected
rather than interpreted partially. JSON-LD contexts are not resolved; objects
and arrays that parse are not necessarily valid structured data. Other markup
attributes are only reported as detected. Missing JSON-LD is not a defect.

HTTP status, redirects, X-Robots-Tag, robots.txt, crawl eligibility and indexing
remain explicitly null/Unknown. URL-only input returns
`422 LIVE_FETCH_UNSUPPORTED` with useful source-copy instructions. Malformed,
oversized, complex or timed-out inputs remain Unknown. They never become a bad
SEO result. The endpoint is reusable JSON, but is not registered as an MCP tool.

## Network decision and limits

There are **zero target network requests and zero redirects**. The module does
not receive ASSETS, private bindings or databases. No DNS lookup, browser,
external proxy, downloaded image, remote script or LLM call is involved.

Workers' documented `resolveOverride` changes a hostname lookup only within
the caller's zone. It does not establish a general external HTTPS peer-IP pin.
A DNS preflight followed by normal `fetch()` would permit a DNS change between
validation and connection. Private-address blocking documented for TCP sockets
is not proof of an equivalent fetch contract. This implementation therefore
does not attempt an arbitrary-URL proxy.

- Request body: 320 KiB, enforced during streaming, including JSON escaping.
- HTML: 256 KiB UTF-8, complete input required.
- Deadline: five seconds over quota, input and analysis; browser abort at seven.
- Element bound: 8,000; repeated metadata/JSON-LD blocks: 40 per category.
- Displayed metadata text and directive attributes: 512 characters.
- URL context: HTTPS, standard port, no credentials, query or fragment, max
  2,048 characters. IP literals and local/reserved suffixes are rejected.
  This is input policy, not an assertion that a hostname resolves publicly.
- Existing `MCP_RATE_LIMIT` binding, separate `base2026:page-readiness:v1:`
  key prefix, existing 60 requests/minute configuration. Binding absence or
  error fails closed. No new quota binding or billable service.
- POST JSON only, same-origin browser requests, no permissive CORS, no-store
  JSON responses, no cookies, no analytics events, no source/URL application
  logs or persistence. Browser requests omit credentials and referrer. Do not
  enable request-body logging/tracing for this route during release.

A future live-URL version requires a separately reviewed egress mechanism that
enforces public-address policy at the actual connection, authenticates the
original HTTPS hostname and repeats this policy at every redirect. It also
needs total request/time/decoded-byte limits and a privacy review. Adding a
DNS denylist before native fetch is not sufficient evidence. Do not add a
proxy or new infrastructure as part of this source-only release.

Official references checked September 5, 2026:

- [Workers best practices](https://developers.cloudflare.com/workers/best-practices/workers-best-practices/)
- [Request and resolveOverride](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [HTMLRewriter and streamed text chunks](https://developers.cloudflare.com/workers/runtime-apis/html-rewriter/)
- [TCP socket restrictions](https://developers.cloudflare.com/workers/runtime-apis/tcp-sockets/)

## Verify and integrate

From `cloudflare/base2026-worker`:

```sh
npm ci --ignore-scripts
npx vitest run --config vitest.page-readiness.config.ts
npm run typecheck
npm test
```

From the repository root:

```sh
python3 -m pytest tests/test_build_base2026_cloudflare_release.py -q
python3 scripts/audit-publication-boundary.py --json
git diff --check
```

The real Workers tests cover before/after success, optional URL, base URL,
directives, absent/invalid JSON-LD, hostile source, zero fetch including unsafe
redirect destinations, private URL forms, malformed/non-HTML/oversized input,
rate limiting and stalled-body cancellation. Since there is no target fetch,
non-HTML/timeout refer to submitted input; they do not test a live remote server.

The router integration is one import and one exact API-route branch. The
existing startup builder adds exactly three assets: the tool HTML and its
scoped CSS/JS. Preserve the existing member build flag and retained production
artifact during integration. The hub, global navigation, sitemap, measurement
allowlists and current production configuration are intentionally outside this
change; the release owner coordinates discoverability separately. No generated
artifact, local database, screenshot or private receipt belongs in Git.

Before release, the release owner verifies the current account/bindings and
retained artifact; performs dry-run and member-safe release checks; then smoke
tests this route, adjacent tools and privacy on the actual deployment. A source
PR, local demo or test pass is not a production release or real-user activation.

## One-minute demonstration

1. Open the tool and choose **Load example source**. Explain that it is
   fictional supplied HTML and the tool will not visit example.com.
2. Choose **Check supplied source**. Show the empty-title observation and the
   concrete instruction to keep one descriptive, non-empty title in the head.
3. Choose **Load corrected example**, inspect/edit the descriptive title, then
   check again. Show the title change and the comparison message.
4. Point to the unchanged Unknown live-network finding. For a real page, make
   the change in its CMS and paste fresh source; verify live HTTP separately.

This demonstration can be reused in an existing distribution channel after
release. QA completion, publication, a visit and voluntary useful-user feedback
must be recorded as separate outcomes.
