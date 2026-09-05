# Product Studio and Google login recovery — 2026-09-05

Status: Product Studio and the installable plugin are live. Google settings
are deployed, but the real browser round-trip is not yet confirmed. This is the current scoped
continuation of phase29, not a second strategy or a new office.

## Delivered source

- A `/tools/` landing page groups the three existing public tools, the free
  SEO Experiment Planner skill, MCP and the new WordPress companion.
- A pauseable blueprint/pixel factory explains four research stages. It is
  explicitly an illustration. Separate public inventory counters use only
  same-origin `/api/stats`; they are not queue activity, visitors or traffic.
  Hidden/offscreen/reduced-motion states stop unnecessary work.
- The WordPress Evidence Sidebar beta searches a short explicitly submitted
  topic through the existing public Evidence Brief v2 endpoint. It inserts an
  editable, attributed research note only on a separate click. No whole-post
  upload, paid AI, automatic publishing, title-as-quotation or forced backlink.
- `/tools/wordpress-evidence-sidebar/` is the product landing. The installable
  ZIP contains exactly the PHP entrypoint, editor JS, readme and GPL license.
  The builder regenerates this single download from reviewed source, never
  from an arbitrary repository/archive. Other ZIPs remain forbidden.

The existing header gains a Tools link and the home secondary CTA points to
the hub. Existing homepage/core CSS, search renderer, public data, founder,
footer, Worker source and private member implementation are preserved.

## Verification

- 69 focused Python release/UI/plugin tests; 6 executable Tools Studio JS tests.
- Worker typecheck, 645 Worker tests and 13 native member tests pass.
  After the release flag changed, its configuration-pinning assertion was
  updated to the deliberately enabled state; all 645 Worker tests were rerun
  successfully on that current config, including the 15 auth-routing tests.
- Disposable native WordPress 7.1 / PHP 8.5.8: plugin loads; authorized search
  returns five excerpt-bearing cards with original links; missing capability
  and invalid nonce both deny with403; a synthetic title-only result never
  becomes an excerpt. Editor insertion/route guards have executable JS tests.
- The retained production artifact's 4,281 source files were rehashed against
  their receipt with no mismatch. The tree-digest function now sorts paths
  consistently, removing a walk-order discrepancy without changing source data.
- Final source candidate v3 has4,286 served files,94,086,308 bytes and tree
  `f8fc68906f0224940d74de6c786025f6e2a4916395794cf4c22bf19f984140db`.
  Source tree is
  `bffcbbd3502daa38a6ca14282a456a0a9663e8447a66c133faec7ee0e7383405`.
- V3 passed the isolated four-public-data-file publication gate and
  target-bound Wrangler dry-run. An independent review rehashed every served
  file with zero mismatches. V2-to-V3 changes only the packaged readme.
- Actual WordPress editor search returned five cards. Insertion created two
  editable paragraphs with original attribution and no forced backlink.
  Save draft and full editor-reload persistence both passed on a disposable
  local WordPress site, not a client site.
- Hello Chrome desktop checks at1512px passed for both new landings with zero
  horizontal overflow. A current mobile-browser pass is not claimed.

## Live website release

Worker `ab2589fa-36a4-4bdb-985f-e66a383c8d6d` was deployed through the verified
target account with the exact V3 artifact, all four existing D1 bindings and
additive private auth secrets. Immediate previous version:
`3ecddaf3-f594-4b4a-91d4-fd409bd62e4a`. No DNS, mail or private-pipeline change.

Independent live readback passed: homepage, both new canonical/indexable
landings, health, stats, bounded five-result search and the preserved workspace.
The hub sitemap includes both new routes. The download is HTTP200 and
byte-identical to the reviewed19,096-byte ZIP, SHA256
`f588eddae0df5b91da4d70576b6cdec01d3a637b003ea076b9357cace6cb7e2a`.
Unauthenticated private collections/export deny with401; session and private
responses retain private/no-store and noindex/nofollow. Deployment is not proof
of indexing, directory acceptance or external adoption.

## Google and Cloudflare recovery

The existing Hello Chrome session was reused. Offliner remains a separate,
untouched session. Actual project-level Google OAuth permissions were repaired
for Hello without changing project/client identity, origin/callback, broad
organization permissions, DNS, mail or billing. Basic identity scopes only.

The original OAuth client was preserved. A new secret was prepared privately
without revoking the previous one. Target-account Wrangler authentication is
isolated from the legacy default login. Target AUTH_DB migrations and preserved
member rows were verified; target auth secrets were absent. The three required
secrets were deployed privately and are never committed. The production Worker
flag is now enabled for the real sign-in check. Missing prerequisites still
fail closed in code. No current owner password challenge has been observed.

The ordinary extension popup was dismissed; Hello and the existing second test
user were read back successfully. Google accepted the Hello account and consent
for basic name/email/profile, but the redirect then showed Chrome
`ERR_BLOCKED_BY_CLIENT`. Returning to My Research showed no authenticated
session; do not claim successful login or retry the callback blindly. The owner
was asked for a normal Hello-browser login check while other release work
continues. OAuth audience is still External/Testing, not public Production.
Do not switch profiles, disable security barriers, reconstruct browser tokens
or create another OAuth client. Ordinary interfering popups may be dismissed
through the supported, owner-authorized Computer Use flow.

## Concrete continuation

1. Resume the existing Hello My Research tab after the owner/browser redirect
   check; the test users and settings are already saved. Never recreate them.
2. Prove Google login, private save/revisit/export and logout denial. Publish
   the basic-identity OAuth audience only as part of the verified public launch.
3. Finish public-main source publication: the plugin landing's exact GitHub
   source path was404 during initial live QA, while its download already passed.
4. Submit only the real live new
   canonical URLs to discovery once; directory acceptance and traffic are
   separate. Do not replay the already-sent X skill announcement or pending MCP PR.
5. Reconcile AgencyOS tasks102 and114 through the existing CAS/idempotent
   reconciler. Task112 remains growth observation; task113 page check is not
   this plugin and is still a separate unfinished build.

Private exact receipts/credential locations belong in the existing operations
repository, not in this public handoff. One existing supervisor continues the
office; no additional scheduler or database was created.
